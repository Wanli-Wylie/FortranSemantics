from tests.helpers import parse_fortran_to_ast
from Fortran2.tasks.parse_fortran.etl.transform.scope.io_table import IOTableTransformer


def _get_subprogram_ast():
    src = """
SUBROUTINE io_sub(a)
  INTEGER :: a
  OPEN(UNIT=10, FILE='foo.txt')
  READ(10,*) a
  WRITE(10,*) a
  PRINT *, a
  CALL MPI_SEND(a, 1, MPI_INTEGER, 0, 0, MPI_COMM_WORLD, ierr)
END SUBROUTINE io_sub
"""
    ast = parse_fortran_to_ast(src)
    return ast.content[0]


def test_io_table_from_subprogram():
    ast = _get_subprogram_ast()
    table = IOTableTransformer.from_subprogram(ast)
    ops = [c.operation for c in table]
    assert ops == ["open", "read", "write", "print", "mpi_send"]


def test_io_table_from_module_empty():
    src = """MODULE m
CONTAINS
  SUBROUTINE s
    CALL foo()
  END SUBROUTINE s
END MODULE m
"""
    ast = parse_fortran_to_ast(src)
    module_ast = ast.content[0]
    table = IOTableTransformer.from_module(module_ast)
    assert table == []
