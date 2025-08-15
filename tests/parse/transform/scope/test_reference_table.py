from FortranSemantics.tasks.parse.transform.scope.reference_table import ReferenceTableTransformer
from FortranSemantics.data_models.fortran import SymbolReferenceRead, SymbolReferenceWrite
from tests.helpers import parse_fortran_to_ast


def _get_sub_ast(body: str):
    src = f"""subroutine my_sub()
  integer :: arg1, arg2, arr(10), i
  type :: mytype
     integer :: field
  end type mytype
  type(mytype) :: struct
  {body}
end subroutine my_sub
"""
    ast = parse_fortran_to_ast(src)
    return ast.content[0]


def test_reference_table_from_subprogram():
    sub_ast = _get_sub_ast("arg1 = arg2")
    stmt = sub_ast.content[2].content[0]
    line_no = stmt.item.span[0]

    refs = ReferenceTableTransformer.from_subprogram(sub_ast)
    mapping = {r.name: r for r in refs}

    assert isinstance(mapping["arg1"], SymbolReferenceWrite)
    assert isinstance(mapping["arg2"], SymbolReferenceRead)

    for ref in refs:
        assert ref.line == line_no
        assert ref.is_part_ref is False
        assert ref.component_name is None


def test_reference_table_complex_stmt():
    sub_ast = _get_sub_ast("arr(i) = arg1 + struct%field")
    stmt = sub_ast.content[2].content[0]
    line_no = stmt.item.span[0]

    refs = ReferenceTableTransformer.from_subprogram(sub_ast)
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
    assert mapping["struct"].component_name == ["field"]

    for ref in refs:
        assert ref.line == line_no

