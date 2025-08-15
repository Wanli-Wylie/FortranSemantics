from fparser.two.Fortran2003 import Execution_Part, Subroutine_Subprogram, Function_Subprogram

def get_execution_part(ast_node: Subroutine_Subprogram | Function_Subprogram) -> Execution_Part:
    for child in ast_node.children:
        if isinstance(child, Execution_Part):
            return child
    return None