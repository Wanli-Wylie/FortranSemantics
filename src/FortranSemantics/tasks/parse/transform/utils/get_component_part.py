from fparser.two.Fortran2003 import Derived_Type_Def, Component_Part

def get_component_part(derived_type_def_ast: Derived_Type_Def) -> Component_Part:
    for child in derived_type_def_ast.children:
        if isinstance(child, Component_Part):
            return child
    return None