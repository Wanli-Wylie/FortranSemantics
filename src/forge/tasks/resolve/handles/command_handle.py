from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query
from fpyevolve_core.keys.fortran import ModuleKey, SubprogramKey, ModuleDeclKey, SubprogramDeclKey
from fpyevolve_core.models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
    SubroutineCall,
    FunctionCall,
    FortranDeclaredEntity,
)
from fpyevolve_core.db.schema.fortrans import (
    FortranSymbolReference, 
    FortranCall,
    FortranSubprogram,
    FortranModule,
    FortranSymbol,
    SymbolReferenceType,
    SubprogramType
)

class CommandHandle:
    """SQLite-backed implementation of symbol reference update."""

    def __init__(self, session: Session) -> None:
        if session is None:
            raise ValueError("Session cannot be None")
        self.session = session

    def _host_filter(self, query: Query, host: ModuleKey | SubprogramKey):
        
        if isinstance(host, SubprogramKey):
            # For subprogram-level references, join with subprogram and filter by subprogram
            query = query.join(
                FortranSubprogram, 
                FortranSymbolReference.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, 
                FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == host.module_name,
                FortranSubprogram.name == host.subprogram_name,
                FortranSubprogram.type == host.subprogram_type,
            )
        else:
            # For module-level references, join with subprogram and filter by module
            query = query.join(
                FortranSubprogram, 
                FortranSymbolReference.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, 
                FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == host.module_name,
                FortranSymbolReference.subprogram_id.is_(None)
            )
        return query

    def update_symbol_reference(
        self,
        host: SubprogramKey | ModuleKey,
        ref: SymbolReferenceRead | SymbolReferenceWrite,
        resolved: SubprogramDeclKey | ModuleDeclKey | None,
    ) -> None:
        # Build the query to find the records to update
        
        q = self.session.query(FortranSymbolReference)
        q = self._host_filter(q, host)
        q = q.filter(
            FortranSymbolReference.name == ref.name,
            FortranSymbolReference.line == ref.line,
            FortranSymbolReference.reference_type == SymbolReferenceType(ref.reference_type),
        )
        
        # Get the IDs of records to update
        record_ids = [record.id for record in q.all()]
        
        if not record_ids:
            return
        
        # Update the symbol_id to point to the resolved symbol
        if isinstance(resolved, SubprogramDeclKey):
            resolved_symbol = self.session.query(FortranSymbol).join(
                FortranSubprogram, FortranSymbol.subprogram_id == FortranSubprogram.id
            ).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == resolved.module_name,
                FortranSubprogram.name == resolved.subprogram_name,
                FortranSubprogram.type == resolved.subprogram_type,
                FortranSymbol.name == resolved.declaration_name,
            ).first()
        elif isinstance(resolved, ModuleDeclKey):
            resolved_symbol = self.session.query(FortranSymbol).join(
                FortranModule, FortranSymbol.module_id == FortranModule.id
            ).filter(
                FortranModule.name == resolved.module_name,
                FortranSymbol.name == ref.name
            ).first()
        else:
            return
        
        if resolved_symbol:
            self.session.query(FortranSymbolReference).filter(
                FortranSymbolReference.id.in_(record_ids)
            ).update({FortranSymbolReference.symbol_id: resolved_symbol.id})
        
        self.session.commit()

    def update_resolved_call_reference(
        self,
        host: SubprogramKey,
        call: SubroutineCall,
        resolved: SubprogramKey | None,
    ) -> None:
        # Find the caller subprogram
        caller = self.session.query(FortranSubprogram).join(
            FortranModule, FortranSubprogram.module_id == FortranModule.id
        ).filter(
            FortranModule.name == host.module_name,
            FortranSubprogram.name == host.subprogram_name,
            FortranSubprogram.type == host.subprogram_type,
        ).first()
        
        if not caller:
            return
            
        # Find the call record
        q = self.session.query(FortranCall).filter(
            FortranCall.caller_id == caller.id,
            FortranCall.line == call.line,
            FortranCall.call_type == SubprogramType.SUBROUTINE,
        )
        
        # Update the callee_id to point to the resolved subprogram
        if resolved:
            # Find the resolved subprogram
            callee = self.session.query(FortranSubprogram).join(
                FortranModule, FortranSubprogram.module_id == FortranModule.id
            ).filter(
                FortranModule.name == resolved.module_name,
                FortranSubprogram.name == resolved.subprogram_name,
                FortranSubprogram.type == resolved.subprogram_type,
            ).first()
            
            if callee:
                q.update({FortranCall.callee_id: callee.id})
        else:
            q.update({FortranCall.callee_id: None})
            
        self.session.commit()

    def update_resolved_part_ref(
        self,
        host: SubprogramKey | ModuleKey,
        part_ref: SymbolReferenceRead | SymbolReferenceWrite,
        resolved: SymbolReferenceRead | FunctionCall,
    ) -> None:
        # Build the query to find the records to update
        q = self.session.query(FortranSymbolReference)
        q = self._host_filter(q, host)
        q = q.filter(
            FortranSymbolReference.name == part_ref.name,
            FortranSymbolReference.line == part_ref.line,
            FortranSymbolReference.is_part_ref == True,
        )
        
        # Get the IDs of records to update
        record_ids = [record.id for record in q.all()]
        
        if not record_ids:
            return
        
        if isinstance(resolved, SymbolReferenceRead):

            # Find the resolved symbol and update symbol_id
            if resolved.resolved_symbol:
                resolved_symbol = (
                    self.session.query(FortranSymbol)
                    .join(FortranSubprogram, FortranSymbol.subprogram_id == FortranSubprogram.id)
                    .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
                    .filter(FortranSymbol.name == resolved.resolved_symbol)
                    .first()
                )

                if resolved_symbol:
                    self.session.query(FortranSymbolReference).filter(
                        FortranSymbolReference.id.in_(record_ids)
                    ).update({FortranSymbolReference.symbol_id: resolved_symbol.id})
            self.session.commit()
        else:  # FunctionCall
            # If this is a function call, delete the part_ref record
            self.session.query(FortranSymbolReference).filter(
                FortranSymbolReference.id.in_(record_ids)
            ).delete(synchronize_session=False)
            self.session.commit()

    def add_function_call(self, host: SubprogramKey, call: FunctionCall) -> None:
        caller = (
            self.session.query(FortranSubprogram)
            .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
            .filter(
                FortranModule.name == host.module_name,
                FortranSubprogram.name == host.subprogram_name,
                FortranSubprogram.type == host.subprogram_type,
            )
            .first()
        )
        if not caller:
            return

        callee_id = None
        if call.resolved_function:
            try:
                key = SubprogramKey.from_string(call.resolved_function)
            except ValueError:
                key = None
            if key:
                callee = (
                    self.session.query(FortranSubprogram)
                    .join(FortranModule, FortranSubprogram.module_id == FortranModule.id)
                    .filter(
                        FortranModule.name == key.module_name,
                        FortranSubprogram.name == key.subprogram_name,
                        FortranSubprogram.type == key.subprogram_type,
                    )
                    .first()
                )
                if callee:
                    callee_id = callee.id

        row = FortranCall(
            caller_id=caller.id,
            callee_id=callee_id,
            callee_name=None if callee_id else call.name,
            line=call.line,
            call_type=SubprogramType.FUNCTION,
        )
        self.session.add(row)
        self.session.commit()

    def remove_part_ref(self, host: SubprogramKey | ModuleKey, part_ref: SymbolReferenceRead | SymbolReferenceWrite) -> None:
        q = self.session.query(FortranSymbolReference.id)
        q = self._host_filter(q, host)
        q = q.filter(
            FortranSymbolReference.name == part_ref.name,
            FortranSymbolReference.line == part_ref.line,
            FortranSymbolReference.is_part_ref == True,
        )
        target_ids = [row.id for row in q]      # 先拿到主键列表

        if target_ids:
            (self.session.query(FortranSymbolReference)
                .filter(FortranSymbolReference.id.in_(target_ids))
                .delete(synchronize_session=False))
            self.session.commit()

    def add_symbol(self, host: SubprogramKey, symbol: FortranDeclaredEntity) -> None:
        module_row = self.session.query(FortranModule).filter_by(name=host.module_name).one()
        sp_row = (
            self.session.query(FortranSubprogram)
            .filter(
                FortranSubprogram.module_id == module_row.id,
                FortranSubprogram.name == host.subprogram_name,
                FortranSubprogram.type == host.subprogram_type,
            )
            .one()
        )
        row = FortranSymbol(
            module_id=module_row.id,
            subprogram_id=sp_row.id,
            name=symbol.name,
            line_declared=symbol.line_declared,
            type_declared=symbol.type_declared,
            array_spec=symbol.attributes.array_spec.model_dump_json() if symbol.attributes.array_spec else None,
            intent=symbol.attributes.intent,
            additional_keywords=(
                symbol.attributes.additional_keywords
                if symbol.attributes.additional_keywords and len(symbol.attributes.additional_keywords) > 0
                else None
            ),
            initial_value=symbol.initial_value,
        )
        self.session.add(row)
        self.session.commit()