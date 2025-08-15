import enum
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base

# ─────────────────────────────────────────────
#  1. Enum Types
# ─────────────────────────────────────────────
class SubprogramType(str, enum.Enum):
    SUBROUTINE = "subroutine"
    FUNCTION = "function"


class SymbolReferenceType(str, enum.Enum):
    READ = "read"
    WRITE = "write"


class SubprogramSignatureDir(str, enum.Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"


# Can directly reuse `SubprogramType` as call type; if expansion needed, declare CallType enum separately
CallType = SubprogramType


# New enum for IO operations -- primarily open/close/read/write/print
class IOOperation(str, enum.Enum):
    OPEN = "open"
    CLOSE = "close"
    READ = "read"
    WRITE = "write"
    PRINT = "print"


# ─────────────────────────────────────────────
#  2. Core Entities
# ─────────────────────────────────────────────
class FortranModule(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # 已有关系
    subprograms: Mapped[List["FortranSubprogram"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
    derived_types: Mapped[List["FortranDerivedType"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )

    # 新增：以“我作为 source”/“我被 use”区分两条路径
    uses_as_source: Mapped[List["FortranUse"]] = relationship(
        back_populates="source_module",
        foreign_keys="FortranUse.source_module_id",
        cascade="all, delete-orphan",
    )
    uses_as_target: Mapped[List["FortranUse"]] = relationship(
        back_populates="target_module",
        foreign_keys="FortranUse.target_module_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<Module {self.name!r}>"


class FortranSubprogram(Base):
    """
    Fortran subprogram (function / procedure)

    * Unique key: module+name+type
    """

    __tablename__ = "subprograms"
    __table_args__ = (
        UniqueConstraint("module_id", "name", "type", name="uq_subprogram"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[SubprogramType] = mapped_column(
        Enum(SubprogramType), nullable=False
    )

    # ── relationships
    module: Mapped["FortranModule"] = relationship(back_populates="subprograms")
    
    uses: Mapped[List["FortranUse"]] = relationship(
        back_populates="source_subprogram",
        foreign_keys="FortranUse.source_subprogram_id",
        cascade="all, delete-orphan",
    )

    # Call graph: this subprogram → other subprograms
    calls_out: Mapped[List["FortranCall"]] = relationship(
        back_populates="caller",
        foreign_keys="FortranCall.caller_id",
        cascade="all, delete-orphan",
    )
    # Called by: other subprograms → this subprogram
    calls_in: Mapped[List["FortranCall"]] = relationship(
        back_populates="callee",
        foreign_keys="FortranCall.callee_id",
        cascade="all, delete-orphan",
    )

    symbols: Mapped[List["FortranSymbol"]] = relationship(
        back_populates="subprogram", cascade="all, delete-orphan"
    )
    symbol_refs: Mapped[List["FortranSymbolReference"]] = relationship(
        back_populates="subprogram", cascade="all, delete-orphan"
    )
    signatures: Mapped[List["FortranSubprogramSignature"]] = relationship(
        back_populates="subprogram", cascade="all, delete-orphan"
    )
    io_calls: Mapped[List["FortranIOCall"]] = relationship(
        back_populates="subprogram", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<Subprogram {self.fullname}>"

    # ── helper property
    @property
    def fullname(self) -> str:
        """module::name(type)"""
        return f"{self.module.name}::{self.name}({self.type})"


# ─────────────────────────────────────────────
#  3. Dependencies / Calls / Usage Relationships
# ─────────────────────────────────────────────
class FortranUse(Base):
    """
    USE <module> 语句。

    - 如果目标模块已纳入 modules 表 → 写 target_module_id，
      target_module_name 置 NULL。
    - 如果暂时未纳入 → target_module_id 置 NULL，
      直接把名字写入 target_module_name。
    """

    __tablename__ = "uses"
    __table_args__ = (
        # 至少要填一个：id 或 name
        CheckConstraint(
            "(target_module_id IS NOT NULL) OR (target_module_name IS NOT NULL)",
            name="ck_use_target_not_null",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ----------  源头 ----------
    source_module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    source_subprogram_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE")
    )

    # ----------  目标 ----------
    target_module_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("modules.id", ondelete="SET NULL"), nullable=True
    )
    target_module_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # ----------  relationships ----------
    source_module: Mapped["FortranModule"] = relationship(
        back_populates="uses_as_source",
        foreign_keys=[source_module_id],
    )
    target_module: Mapped[Optional["FortranModule"]] = relationship(
        back_populates="uses_as_target",
        foreign_keys=[target_module_id],
    )
    source_subprogram: Mapped[Optional["FortranSubprogram"]] = relationship(
        back_populates="uses",
        foreign_keys=[source_subprogram_id],
    )

    # ----------  helper ----------
    @property
    def target_display(self) -> str:
        """返回 `<模块对象.name>` 或备用字符串。"""
        return self.target_module.name if self.target_module else self.target_module_name

    def __repr__(self) -> str:  # noqa: D401
        return f"<USE {self.target_display}>"


class FortranCall(Base):
    """
    A call record: caller → callee (resolved / unresolved)

    If callee_id is null, indicates target subprogram not yet resolved.
    """

    __tablename__ = "calls"
    __table_args__ = (
        CheckConstraint(
            "(callee_id IS NOT NULL) OR (callee_name IS NOT NULL)",
            name="ck_call_callee_not_null",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caller_id: Mapped[int] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE"), nullable=False
    )
    callee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subprograms.id", ondelete="SET NULL")
    )
    callee_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    call_type: Mapped[CallType] = mapped_column(
        Enum(CallType), nullable=False
    )

    # ── relationships
    caller: Mapped["FortranSubprogram"] = relationship(
        back_populates="calls_out", foreign_keys=[caller_id]
    )
    callee: Mapped[Optional["FortranSubprogram"]] = relationship(
        back_populates="calls_in", foreign_keys=[callee_id]
    )

    def __repr__(self) -> str:  # noqa: D401
        tgt = self.callee.fullname if self.callee else "UNRESOLVED"
        return f"<Call {self.caller.fullname} → {tgt} @L{self.line}>"


# ─────────────────────────────────────────────
#  4. Symbol Table & References
# ─────────────────────────────────────────────
class FortranSymbol(Base):
    """Declaration location"""

    __tablename__ = "symbols"
    __table_args__ = (
        UniqueConstraint(
            "subprogram_id", "name", name="uq_symbol_in_subprogram"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subprogram_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE")
    )
    # If declared at module top level, can set subprogram_id = NULL, module passed through subprogram
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )

    # ── Fortran fields
    name: Mapped[str] = mapped_column(String, nullable=False)
    line_declared: Mapped[int] = mapped_column(Integer, nullable=False)
    type_declared: Mapped[str] = mapped_column(String, nullable=False)
    array_spec: Mapped[Optional[str]] = mapped_column(String)
    intent: Mapped[Optional[str]] = mapped_column(String)
    additional_keywords: Mapped[Optional[List[str]]] = mapped_column(
        MutableList.as_mutable(JSON)
    )
    initial_value: Mapped[Optional[str]] = mapped_column(String)

    # ── relationships
    subprogram: Mapped[Optional["FortranSubprogram"]] = relationship(
        back_populates="symbols"
    )
    module: Mapped["FortranModule"] = relationship()

    def __repr__(self) -> str:  # noqa: D401
        return f"<Symbol {self.name} @L{self.line_declared}>"


class FortranSymbolReference(Base):
    """Symbol reference (read / write / partial reference)"""

    __tablename__ = "symbol_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subprogram_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE")
    )
    symbol_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("symbols.id", ondelete="SET NULL")
    )
    is_part_ref: Mapped[bool] = mapped_column(Boolean, nullable=False)
    component_name: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(JSON)
    )

    # Snapshot fields
    name: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[SymbolReferenceType] = mapped_column(
        Enum(SymbolReferenceType), nullable=False
    )

    # ── relationships
    subprogram: Mapped[Optional["FortranSubprogram"]] = relationship(
        back_populates="symbol_refs"
    )
    symbol: Mapped[Optional["FortranSymbol"]] = relationship()

    def __repr__(self) -> str:  # noqa: D401
        return f"<SymbolRef {self.name}:{self.reference_type} @L{self.line}>"


# ─────────────────────────────────────────────
#  5. Subprogram Signatures
# ─────────────────────────────────────────────
class FortranSubprogramSignature(Base):
    __tablename__ = "subprogram_signatures"
    __table_args__ = (
        UniqueConstraint(
            "subprogram_id", "arg_name", name="uq_signature_arg"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subprogram_id: Mapped[int] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE"), nullable=False
    )

    arg_name: Mapped[str] = mapped_column(String, nullable=False)
    arg_type: Mapped[str] = mapped_column(String, nullable=False)
    arg_direction: Mapped[SubprogramSignatureDir] = mapped_column(
        Enum(SubprogramSignatureDir), nullable=False
    )
    result: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ── relationships
    subprogram: Mapped["FortranSubprogram"] = relationship(
        back_populates="signatures"
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<Signature {self.arg_name}:{self.arg_direction}>"


# ─────────────────────────────────────────────
#  6. Derived Types / Structures
# ─────────────────────────────────────────────
class FortranDerivedType(Base):
    """
    Fortran derived type (structure) and its components
    """

    __tablename__ = "derived_types"
    __table_args__ = (
        UniqueConstraint(
            "module_id", "name", "component_name", name="uq_derived_component"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    component_name: Mapped[str] = mapped_column(String, nullable=False)
    component_type: Mapped[str] = mapped_column(String, nullable=False)
    component_array_spec: Mapped[Optional[str]] = mapped_column(String)
    component_intent: Mapped[Optional[str]] = mapped_column(String)
    component_keywords: Mapped[Optional[List[str]]] = mapped_column(
        MutableList.as_mutable(JSON)
    )
    component_initial_value: Mapped[Optional[str]] = mapped_column(String)

    # ── relationships
    module: Mapped["FortranModule"] = relationship(back_populates="derived_types")

    def __repr__(self) -> str:  # noqa: D401
        return f"<DerivedType {self.name}%{self.component_name}>"


# ─────────────────────────────────────────────
#  7. IO Calls
# ─────────────────────────────────────────────
class FortranIOCall(Base):
    """Representation of an I/O related statement within a subprogram."""

    __tablename__ = "io_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subprogram_id: Mapped[int] = mapped_column(
        ForeignKey("subprograms.id", ondelete="CASCADE"), nullable=False
    )
    operation: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── relationships
    subprogram: Mapped["FortranSubprogram"] = relationship(
        back_populates="io_calls"
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<IOCall {self.operation} @L{self.line}>"