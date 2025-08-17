from tests.helpers import parse_fortran_to_ast
from forge.tasks.parse.transform.unit.reference_entry import from_expression, from_designator
from forge.data_models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite
)


def _build_module(code_snippet: str) -> str:
    """Embed a code snippet inside a syntactically correct Fortran module.

    The helper adds:
      * a derived type `mytype` so we can reference `struct%field`
      * a subroutine `subroutine_test` that declares needed scalars, arrays and
        derived‐type variables.
      * `IMPLICIT NONE` to force explicit typing.
    """
    return f"""
MODULE test_mod
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
    """Parse *one* executable statement embedded in a minimal module.

    Returns the *first* executable statement node so that its children can be
    inspected by the reference extractor.
    """
    src = _build_module(code_snippet)
    ast = parse_fortran_to_ast(src)
    # Path: Module -> CONTAINS block (index 1) -> first content item -> body stmt[0]
    return ast.content[0].content[2].content[1].content[2].content[0]


###############################################################################
#  Unit‑tests
###############################################################################

def test_scalar_reference_designator():
    """Scalar variable reads and writes are recognised correctly."""
    expr = _extract_first_stmt("arg1 = arg2")
    refs = from_designator(expr.children[0], line_no=1)

    assert len(refs) == 1
    assert refs[0].name == "arg1"
    assert refs[0].line == 1
    assert isinstance(refs[0], SymbolReferenceWrite)
    
def test_scalar_reference_expression():
    """Scalar variable reads and writes are recognised correctly."""
    expr = _extract_first_stmt("arg1 = arg2")
    refs = from_expression(expr.children[2], line_no=1)

    assert len(refs) == 1
    assert refs[0].name == "arg2"
    assert refs[0].line == 1
    assert isinstance(refs[0], SymbolReferenceRead)


def test_array_reference_read_write():
    """Array name and sub‑scripts are both returned as references."""
    # Read
    expr = _extract_first_stmt("arg1 = arr(i)")
    refs = from_expression(expr.children[2], line_no=1)
    names = {r.name for r in refs}
    assert names == {"arr", "i"}

    # Write
    expr = _extract_first_stmt("arr(i) = x")
    refs = from_designator(expr.children[0], line_no=1)
    names = {r.name for r in refs}
    # `arr` is written, index `i` is read
    assert "arr" in names and "i" in names
    for r in refs:
        if r.name == "arr":
            assert isinstance(r, SymbolReferenceWrite)
        else:
            assert isinstance(r, SymbolReferenceRead)


def test_nested_structure_reference():
    """Only the top‑level structure variable is reported."""
    # Read
    expr = _extract_first_stmt("x = struct%field")
    refs = from_expression(expr.children[2], line_no=1)
    assert {r.name for r in refs} == {"struct"}

    # Write
    expr = _extract_first_stmt("struct%field = x")
    refs = from_designator(expr.children[0], line_no=1)
    assert {r.name for r in refs} == {"struct"}


def test_function_call_reference():
    """Actual arguments of user functions are treated as READ references."""
    
    # Full Fortran module including a dummy function so the parser accepts the call
    src = """
MODULE test_mod
  IMPLICIT NONE
CONTAINS
  INTEGER FUNCTION func(a, b)
    INTEGER :: a, b
    func = a + b
  END FUNCTION func

  SUBROUTINE sub(arg1, arg2)
    INTEGER :: x, arg1, arg2
    x = func(arg1 + arg2 * 2, arg2)
  END SUBROUTINE sub
END MODULE test_mod
"""
    ast = parse_fortran_to_ast(src)
    # Navigate to: Module -> CONTAINS -> SUB sub -> body (assignment is third stmt)
    expr = ast.content[0].content[2].content[2].content[2].content[0]

    refs = from_expression(expr.children[2], line_no=1)
    assert {r.name for r in refs} == {"arg1", "arg2", "func"}


def test_parenthesis_expression():
    """Expressions inside parentheses are processed correctly."""

    expr = _extract_first_stmt("arg1 = (arg2)")
    refs = from_expression(expr.children[2], line_no=1)

    assert len(refs) == 1
    assert refs[0].name == "arg2"
    assert isinstance(refs[0], SymbolReferenceRead)

