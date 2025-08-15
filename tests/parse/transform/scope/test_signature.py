from Fortran2.utils.process_fortran_string import fortran_string_to_ast, pickup_module_ast
from Fortran2.tasks.parse_fortran.etl.transform.scope.signature import SignatureTransformer, FormalParameter

def _get_first_subprogram(src: str):
    ast = fortran_string_to_ast(src)
    module_ast = pickup_module_ast(ast)
    # the parser returns ast of the subroutine/function as the first child
    return module_ast


def test_inspect_subroutine_signature_simple():
    src = """
SUBROUTINE SUBR(A, B, C)
    INTEGER :: A, B, C
END SUBROUTINE SUBR
"""
    ast = _get_first_subprogram(src)
    signature = SignatureTransformer.from_subprogram(ast)
    args = signature.inputs
    assert args == {
        "A": FormalParameter(name="A", type="INTEGER"),
        "B": FormalParameter(name="B", type="INTEGER"),
        "C": FormalParameter(name="C", type="INTEGER"),
    }
    assert signature.result_var_same_as_name is None


def test_inspect_function_signature_without_result():
    src = """
INTEGER FUNCTION FUNC(A, B, C)
    INTEGER :: A, B, C
END FUNCTION FUNC
"""
    ast = _get_first_subprogram(src)
    signature = SignatureTransformer.from_subprogram(ast)
    args = signature.inputs
    result_var = signature.output
    assert args == {
        "A": FormalParameter(name="A", type="INTEGER"),
        "B": FormalParameter(name="B", type="INTEGER"),
        "C": FormalParameter(name="C", type="INTEGER"),
    }
    assert result_var == FormalParameter(name="FUNC", type="INTEGER")
    assert signature.result_var_same_as_name is True


def test_inspect_function_signature_with_result():
    src = """
INTEGER FUNCTION FUNC(A, B, C) RESULT(D)
    INTEGER :: A, B, C
    INTEGER :: D
END FUNCTION FUNC
"""
    ast = _get_first_subprogram(src)
    signature = SignatureTransformer.from_subprogram(ast)
    args = signature.inputs
    result_var = signature.output
    assert args == {
        "A": FormalParameter(name="A", type="INTEGER"),
        "B": FormalParameter(name="B", type="INTEGER"),
        "C": FormalParameter(name="C", type="INTEGER")
    }
    assert result_var == FormalParameter(name="D", type="INTEGER")
    assert signature.result_var_same_as_name is False
