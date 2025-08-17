from fparser.two.Fortran2003 import Specification_Part, Module, Subroutine_Subprogram, Function_Subprogram


def get_specification_part(ast_node: Module | Subroutine_Subprogram | Function_Subprogram) -> Specification_Part:
    for child in ast_node.children:
        if isinstance(child, Specification_Part):
            return child
    return None