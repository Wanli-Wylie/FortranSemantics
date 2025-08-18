from fparser.two.Fortran2003 import Component_Decl, Data_Component_Def_Stmt, Derived_Type_Def, Component_Decl_List
from fpyevolve_core.models.fortran.attr_spec import AttrSpec
from fpyevolve_core.models.fortran import FortranDeclaredComponent, FortranDerivedTypeDefinition
from ..attrs.process_array_spec import process_array_spec
from ..attrs.process_type_spec import process_type_spec
from ..attrs.process_attr_specs import process_attr_specs
from ..utils import get_line_number, get_name_from_node, get_component_part

def from_component_decl(component_decl: Component_Decl, line_no: int, type_name: str, attrs: AttrSpec) -> FortranDeclaredComponent:
    """
    Create a DeclaredComponent instance from a Fortran component declaration node.
    
    This function processes a Fortran component declaration node from the AST and extracts
    all relevant information to create a DeclaredComponent instance.
    
    Args:
        component_decl (Component_Decl): The Fortran AST node representing
                                                       the component declaration.
        line_no (int): The line number where the declaration occurs.
        type_name (str): The Fortran type name of the component.
        attrs (AttrSpec): An AttrSpec object containing attributes associated with the declaration.
            
    Returns:
        DeclaredComponent: A new instance containing the processed component information.
    """
    name, dimension_spec, char_length, initial_value = component_decl.items
    
    # Create a copy of attrs to avoid modifying the original
    attrs_dict = attrs.model_dump()
    
    # Process array dimensions if present and not already in attributes
    if dimension_spec and not attrs.array_spec:
        attrs_dict['array_spec'] = process_array_spec(dimension_spec)
    
    # Process initial value if present
    if initial_value:
        initial_value = str(initial_value.string.replace("=", "")).strip()
    else:
        initial_value = None
        
    return FortranDeclaredComponent(
        name=str(name), 
        line_declared=line_no, 
        type_declared=type_name, 
        attributes=AttrSpec(**attrs_dict), 
        initial_value=initial_value
    )

def from_data_component_def_stmt(data_component_def_stmt: Data_Component_Def_Stmt) -> dict[str, FortranDeclaredComponent]:
    """
    Create a dictionary of DeclaredComponent instances from a Fortran data component definition statement.
    
    This function processes a Fortran data component definition statement from the AST and creates
    a dictionary mapping component names to their corresponding DeclaredComponent instances.
    
    Args:
        data_component_def_stmt (Data_Component_Def_Stmt): The Fortran AST node
                                                                         representing the data component
                                                                         definition statement.
            
    Returns:
        dict[str, DeclaredComponent]: A dictionary mapping component names to their
                                        corresponding DeclaredComponent instances.
                                        
    Raises:
        ValueError: If the component declaration type is unexpected.
    """
    line_no = get_line_number(data_component_def_stmt)
    
    # Extract type specification, attribute specifications, and component declarations
    type_spec, attr_specs, component_decls = data_component_def_stmt.items
    
    # Process the type specification
    type_spec_result = process_type_spec(type_spec)
    
    # Process attribute specifications if present
    if attr_specs:
        attrs = process_attr_specs(attr_specs)
    else:
        attrs = AttrSpec()
    
    # Process single component declaration
    if isinstance(component_decls, Component_Decl):
        component = from_component_decl(component_decls, line_no, type_spec_result, attrs)
        return {component.name: component}
    # Process multiple component declarations
    elif isinstance(component_decls, Component_Decl_List):
        components = {}
        for component_decl in component_decls.items:
            component = from_component_decl(component_decl, line_no, type_spec_result, attrs)
            components[component.name] = component
        return components
    else:
        raise ValueError(f"Unexpected component declaration type: {type(component_decls)}")

def from_derived_type_definition(derived_type_def_ast: Derived_Type_Def) -> FortranDerivedTypeDefinition:
    """
    Create a DerivedTypeDefinition instance from a Fortran derived type definition AST node.
    
    This function processes a Fortran derived type definition node from the AST and creates
    a DerivedTypeDefinition instance containing all its components.
    
    Args:
        derived_type_def_ast (Derived_Type_Def): The Fortran AST node
                                                               representing the derived type
                                                               definition.
            
    Returns:
        DerivedTypeDefinition: A new instance containing the processed derived type
                                        definition information.
    """
    name = get_name_from_node(derived_type_def_ast)
    declared_components = {}
    
    # Get the component part of the derived type definition
    component_part = get_component_part(derived_type_def_ast)
    
    # Process each component in the derived type
    for component in component_part.content:
        if isinstance(component, Data_Component_Def_Stmt):
            components = from_data_component_def_stmt(component)
            declared_components.update(components)
    
    return FortranDerivedTypeDefinition(name=name, declared_components=declared_components)