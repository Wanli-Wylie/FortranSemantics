from fparser.two.Fortran2003 import Subroutine_Subprogram, Function_Subprogram, Subroutine_Stmt, Function_Stmt, Module
from fpyevolve_core.models.fortran import Signature, FormalParameter, FortranDeclaredEntity
from ..utils import get_specification_part
from .symbol_table import SymbolTableTransformer
from .base import BaseTableTransformer

class SignatureTransformer(BaseTableTransformer):
    @staticmethod
    def from_module(module: Module) -> Signature:
        raise ValueError("Signature table is not supported for module")
    
    @staticmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> Signature:
        """
        Create a Signature instance from a Fortran subprogram.
        
        Args:
            subprogram (Subroutine_Subprogram | Function_Subprogram): The Fortran subprogram AST node.
            
        Returns:
            Signature: A signature containing the input and output parameters of the subprogram.
        """
        if isinstance(subprogram, Module):
            return Signature(inputs={}, output=None)
        
        stmt: Subroutine_Stmt | Function_Stmt = get_stmt(subprogram)
        
        sym_tab: dict[str, FortranDeclaredEntity] = SymbolTableTransformer.from_subprogram(subprogram)
        
        prefix, func_name, dummy_arg_list, suffix = stmt.items
        if dummy_arg_list is None:
            arg_names = []
        else:
            arg_names = [str(arg) for arg in dummy_arg_list.items]
        has_result_clause = suffix is not None
        if has_result_clause:
            result_name = str(subprogram.content[0].items[3].items[0])
        else:
            result_name = str(func_name)
            
        args: list[FormalParameter] = []
        for name in arg_names:
            decl = sym_tab.get(name)    
            arg_type = decl.type_declared if decl is not None else ""
            args.append(FormalParameter(name=name, type=arg_type))
        inputs = {arg.name: arg for arg in args}
            
        if isinstance(subprogram, Function_Subprogram):
            result_decl = sym_tab.get(result_name)
            if result_decl is not None:
                result_type = result_decl.type_declared
            elif prefix is not None:
                result_type = str(prefix.items[0])
            else:
                raise ValueError(f"No result variable found in {subprogram}")
            result_entry = FormalParameter(name=result_name, type=result_type)
            return Signature(
                inputs=inputs,
                output=result_entry,
                result_var_same_as_name=not has_result_clause,
            )
        else:
            return Signature(inputs=inputs, output=None)

def get_stmt(ast_node: Subroutine_Subprogram | Function_Subprogram) -> Subroutine_Stmt | Function_Stmt:
    """Get the statement node from a subprogram AST node.
    
    Parameters
    ----------
    ast_node:
        ``Subroutine_Subprogram`` or ``Function_Subprogram`` AST node.
        
    Returns
    -------
    Subroutine_Stmt | Function_Stmt
        The statement node containing the subprogram declaration.
        
    Raises
    ------
    ValueError
        If no statement node is found.
    """
    for stmt in ast_node.content:
        if isinstance(stmt, (Subroutine_Stmt, Function_Stmt)):
            return stmt
    raise ValueError(f"No statement node found in {ast_node}")
