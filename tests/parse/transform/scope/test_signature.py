from forge.tasks.parse.extract import extract_from_fortran_string, pickup_module_ast
from forge.tasks.parse.transform.scope.signature import SignatureTransformer, FormalParameter

def _get_first_subprogram(src: str):
    ast = extract_from_fortran_string(src)
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
        "a": FormalParameter(name="a", type="INTEGER"),
        "b": FormalParameter(name="b", type="INTEGER"),
        "c": FormalParameter(name="c", type="INTEGER"),
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
        "a": FormalParameter(name="a", type="INTEGER"),
        "b": FormalParameter(name="b", type="INTEGER"),
        "c": FormalParameter(name="c", type="INTEGER"),
    }
    assert result_var == FormalParameter(name="func", type="INTEGER")
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
        "a": FormalParameter(name="a", type="INTEGER"),
        "b": FormalParameter(name="b", type="INTEGER"),
        "c": FormalParameter(name="c", type="INTEGER")
    }
    assert result_var == FormalParameter(name="d", type="INTEGER")
    assert signature.result_var_same_as_name is False
