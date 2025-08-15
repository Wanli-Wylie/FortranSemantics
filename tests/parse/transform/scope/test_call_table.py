import pytest
from tests.helpers import parse_fortran_to_ast
from Fortran2.tasks.parse_fortran.etl.transform.scope.call_table import CallTableTransformer
from Fortran2.tasks.parse_fortran.etl.transform.unit.calls import from_call_stmt
from Fortran2.data_models.fortran import SymbolReferenceRead


def _get_subprogram_ast():
    src = """
SUBROUTINE sub(a,b)
  INTEGER :: a,b
  CALL foo(a,b)
  CALL bar()
END SUBROUTINE sub
"""
    ast = parse_fortran_to_ast(src)
    return ast.content[0]


def test_call_table_from_subprogram():
    ast = _get_subprogram_ast()
    table = CallTableTransformer.from_subprogram(ast)
    names = [c.name for c in table]
    assert names == ["foo", "bar"]
    # current implementation does not resolve argument references
    assert table[0].actual_args == [
      SymbolReferenceRead(name='a', line=4, resolved_symbol=''), 
      SymbolReferenceRead(name='b', line=4, resolved_symbol='')]
    assert table[1].actual_args == []


def test_call_table_from_module_empty():
    src = """MODULE m
CONTAINS
  SUBROUTINE s
    CALL foo()
  END SUBROUTINE s
END MODULE m
"""
    ast = parse_fortran_to_ast(src)
    module_ast = ast.content[0]
    table = CallTableTransformer.from_module(module_ast)
    assert table == []
