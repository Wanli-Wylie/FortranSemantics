from fparser.two.Fortran2003 import (
    Intrinsic_Type_Spec,
    Declaration_Type_Spec
)
def process_type_spec(type_spec: Intrinsic_Type_Spec | Declaration_Type_Spec) -> str:
    """Process type specifier and return type name"""
    if isinstance(type_spec, Intrinsic_Type_Spec):
        return str(type_spec).upper()
    elif isinstance(type_spec, Declaration_Type_Spec):
        # The first item is the plain "TYPE" keyword, the second item is the type name
        return f"TYPE-{str(type_spec.items[1]).upper()}"
    else:
        return "UNKNOWN"
