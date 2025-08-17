from tests.helpers import parse_fortran_to_ast
from forge.tasks.parse.transform.unit.reference_entry import from_assignment_stmt
from forge.data_models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
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


def test_simple_assignment():
    stmt = _extract_first_stmt("arg1 = arg2")
    line_no = stmt.item.span[0]
    refs = from_assignment_stmt(stmt)

    # Both lhs and rhs are captured with appropriate access types
    mapping = {r.name: type(r) for r in refs}
    assert mapping == {
        "arg1": SymbolReferenceWrite,
        "arg2": SymbolReferenceRead,
    }

    # New reference objects expose extra metadata
    for ref in refs:
        assert ref.line == line_no
        assert ref.component_name is None
        assert ref.is_part_ref is False


def test_complex_assignment():
    stmt = _extract_first_stmt("arr(i) = arg1 + struct%field")
    line_no = stmt.item.span[0]
    refs = from_assignment_stmt(stmt)
    mapping = {r.name: r for r in refs}

    assert isinstance(mapping["arr"], SymbolReferenceWrite)
    assert mapping["arr"].is_part_ref
    assert mapping["arr"].component_name is None

    assert isinstance(mapping["i"], SymbolReferenceRead)
    assert mapping["i"].is_part_ref is False
    assert mapping["i"].component_name is None

    assert isinstance(mapping["arg1"], SymbolReferenceRead)
    assert mapping["arg1"].is_part_ref is False
    assert mapping["arg1"].component_name is None

    assert isinstance(mapping["struct"], SymbolReferenceRead)
    assert mapping["struct"].is_part_ref is False
    assert mapping["struct"].component_name == ["field"]

    for ref in refs:
        assert ref.line == line_no

