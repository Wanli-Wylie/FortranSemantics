import pytest
from tests.helpers import parse_fortran_to_ast
from Fortran2.tasks.parse_fortran.etl.transform.unit.reference_entry import from_designator
from Fortran2.data_models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite
)


def _build_module(code_snippet: str) -> str:
    return f"""MODULE test_mod
  IMPLICIT NONE
  TYPE :: mytype
     INTEGER :: field
  END TYPE mytype
CONTAINS
  SUBROUTINE subroutine_test(arg1, arg2)
    INTEGER :: arg1, arg2
    INTEGER :: arr(10), i, j, x
    TYPE(mytype) :: struct
{code_snippet}
  END SUBROUTINE subroutine_test
END MODULE test_mod
"""


def _extract_first_stmt(code_snippet: str):
    src = _build_module(code_snippet)
    ast = parse_fortran_to_ast(src)
    return ast.content[0].content[2].content[1].content[2].content[0]


def test_simple_variable_designator():
    stmt = _extract_first_stmt("arg1 = arg2")
    refs = from_designator(stmt.children[0], line_no=1)
    assert len(refs) == 1
    assert refs[0].name == "arg1"
    assert isinstance(refs[0], SymbolReferenceWrite)


def test_array_designator():
    stmt = _extract_first_stmt("arr(i) = x")
    refs = from_designator(stmt.children[0], line_no=1)
    mapping = {r.name: type(r) for r in refs}
    assert mapping == {
        "arr": SymbolReferenceWrite,
        "i": SymbolReferenceRead,
    }


def test_structure_designator():
    stmt = _extract_first_stmt("struct%field = x")
    refs = from_designator(stmt.children[0], line_no=1)
    assert len(refs) == 1
    assert refs[0].name == "struct"
    assert isinstance(refs[0], SymbolReferenceWrite)
