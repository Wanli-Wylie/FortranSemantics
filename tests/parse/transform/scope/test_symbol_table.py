from fparser.two.Fortran2003 import Type_Declaration_Stmt
from Fortran2.tasks.parse_fortran.etl.transform.scope.symbol_table import SymbolTableTransformer
from Fortran2.utils.get_parts import get_specification_part, get_subprogram_part
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from pathlib import Path
from fparser.two.Fortran2003 import Function_Subprogram


def create_type_declaration_from_string(decl_str: str) -> Type_Declaration_Stmt:
    code = insert_content_into_module(decls=decl_str, contains="")
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0]


def test_create_from_specification_part():
    src = """
subroutine my_sub()
  integer :: a
  real :: b
end subroutine my_sub
"""
    ast = parse_fortran_to_ast(src)
    sub_ast = ast.content[0]
    table = SymbolTableTransformer.from_subprogram(sub_ast)
    assert len(table) == 2
    assert "a" in table and "b" in table
    assert table["a"].type_declared == "INTEGER"
    assert table["b"].type_declared == "REAL"


def _get_module_ast(name: str):
    src = Path("example/basic") / name
    code = src.read_text()
    ast = parse_fortran_to_ast(code)
    return ast.children[0]


def test_symbol_table_from_ast_node():
    module_ast = _get_module_ast("vector_mod.f90")
    subprogram_asts = get_subprogram_part(module_ast)
    func_ast = [
        sp for sp in subprogram_asts if isinstance(sp, Function_Subprogram)
    ][0]

    table = SymbolTableTransformer.from_subprogram(func_ast)

    assert set(table.keys()) == {"a", "b"}
    assert table["a"].type_declared == "TYPE-VECTOR3_T"
    assert table["b"].type_declared == "TYPE-VECTOR3_T"
