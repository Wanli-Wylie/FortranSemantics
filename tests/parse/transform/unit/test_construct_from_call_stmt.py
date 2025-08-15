from tests.helpers import parse_fortran_to_ast
from FortranSemantics.tasks.parse.transform.unit.reference_entry import from_call_stmt
from FortranSemantics.data_models.fortran import (
    SymbolReferenceRead,
)


def create_call_stmt_from_code(stmt: str):
    """Helper to parse one CALL statement."""
    code = f"""
module test_mod
contains
  subroutine func(x, y)
    integer :: x, y
  end subroutine func
  subroutine test_subroutine
    {stmt}
  end subroutine test_subroutine
end module test_mod
"""
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[2].content[1].content[0]


def test_simple_function_call():
    stmt = create_call_stmt_from_code("call func(x, y)")
    result = from_call_stmt(stmt)
    names = {ref.name for ref in result}
    assert names == {"x", "y"}
    for ref in result:
        assert isinstance(ref, SymbolReferenceRead)


def test_function_call_with_array():
    stmt = create_call_stmt_from_code("call func(arr(i), x)")
    result = from_call_stmt(stmt)
    names = {ref.name for ref in result}
    assert names == {"arr", "i", "x"}


def test_function_call_with_structure():
    stmt = create_call_stmt_from_code("call func(struct%field, x)")
    result = from_call_stmt(stmt)
    names = {ref.name for ref in result}
    assert names == {"struct", "x"}


def test_empty_call_stmt():
    stmt = create_call_stmt_from_code("call func()")
    result = from_call_stmt(stmt)
    assert len(result) == 0

