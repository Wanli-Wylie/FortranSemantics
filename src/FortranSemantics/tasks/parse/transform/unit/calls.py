"""Construct :class:`SubroutineCall` domain objects from AST nodes."""

from .....data_models.fortran import SubroutineCall, SymbolReferenceRead
from fparser.two.Fortran2003 import Call_Stmt

from .reference_entry import from_expression
from ..utils import get_line_number, get_name_from_node


def from_call_stmt(call_stmt: Call_Stmt) -> SubroutineCall:
    """Create a :class:`SubroutineCall` from a ``Call_Stmt`` node."""

    line_no = get_line_number(call_stmt)

    if call_stmt is None:
        return SubroutineCall(
            name="",
            line=-1,
            resolved_subroutine="",
            formal_args=[],
            actual_args=[],
        )

    sub_name, arg_list = call_stmt.items
    name = get_name_from_node(sub_name)

    actual_args: list[SymbolReferenceRead] = []
    if arg_list:
        for arg in arg_list.items:
            # ``from_expression`` returns a list but each argument should be
            # treated independently. Only READ references are expected here.
            expr_refs = from_expression(arg, line_no, access="read")
            for ref in expr_refs:
                if isinstance(ref, SymbolReferenceRead):
                    actual_args.append(ref)

    return SubroutineCall(
        name=name,
        line=line_no,
        resolved_subroutine="",
        actual_args=actual_args,
    )
