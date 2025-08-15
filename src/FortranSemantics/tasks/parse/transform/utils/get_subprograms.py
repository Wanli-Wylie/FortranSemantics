from fparser.two.Fortran2003 import Module, Subroutine_Subprogram, Function_Subprogram, Module_Subprogram_Part


def get_subprogram_part(ast_node: Module) -> list[Subroutine_Subprogram | Function_Subprogram]:
    subprogram_part = None
    subprogram_contents = []
    
    for child in ast_node.children:
        if isinstance(child, Module_Subprogram_Part):
            subprogram_part = child
            break
        
    if not subprogram_part:
        return []
    
    for child in subprogram_part.children:
        if isinstance(child, (Subroutine_Subprogram, Function_Subprogram)):
            subprogram_contents.append(child)
    
    return subprogram_contents