from fparser.two.Fortran2003 import Entity_Decl, Type_Declaration_Stmt, Entity_Decl_List
from fpyevolve_core.models.fortran.attr_spec import AttrSpec
from fpyevolve_core.models.fortran import FortranDeclaredEntity
from ..attrs.process_array_spec import process_array_spec
from ..attrs.process_type_spec import process_type_spec
from ..attrs.process_attr_specs import process_attr_specs
from ..utils import get_line_number

def from_entity_decl(entity_decl: Entity_Decl, line_no: int, type_name: str, attrs: AttrSpec) -> FortranDeclaredEntity:
    """
    Create a DeclaredEntity instance from a Fortran AST node.
        
    This method processes a Fortran entity declaration node from the AST and extracts
    all relevant information to create a DeclaredEntity instance.
        
    Args:
        entity_decl (Entity_Decl): The Fortran AST node representing the entity declaration.
        line_no (int): The line number where the declaration occurs.
        type_name (str): The Fortran type name of the variable.
        attrs (dict): A dictionary of attributes associated with the declaration.
            
    Returns:
        DeclaredEntity: A new instance containing the processed declaration information.
    """
    name, dimension_spec, char_length, initial_value = entity_decl.items
        
    name = str(name)
        
    # Process array dimensions if present and not already in attributes
    if dimension_spec and not attrs.array_spec:
        attrs.array_spec = process_array_spec(dimension_spec)
        
    # Process initial value if present
    if initial_value:
        initial_value = str(initial_value.string.replace("=", "")).strip()
    else:
        initial_value = None
        
    return FortranDeclaredEntity(
        name=name,
        line_declared=line_no,
        type_declared=type_name,
        attributes=attrs,
        initial_value=initial_value,
    )

def from_type_declaration_stmt(type_declaration_stmt: Type_Declaration_Stmt) -> dict[str, FortranDeclaredEntity]:
    """
    Create a dict[str, DeclaredEntity] from a Fortran type declaration statement.
    
    This method processes a Fortran type declaration statement from the AST and creates
    a container containing all variable declarations from that statement.
    
    Args:
        type_declaration_stmt (Type_Declaration_Stmt): The Fortran AST node
        representing the type declaration.
    
    Returns:
        dict[str, DeclaredEntity]: A new dict containing all variable declarations
                                from the type declaration statement.
                                
    Raises:
        ValueError: If the entity declaration type is unexpected.
    """
    # Get the line number where the declaration occurs
    line_no = get_line_number(type_declaration_stmt)
    
    # Extract type specification, attribute specifications, and entity declarations
    type_spec, attr_specs, entity_decls = type_declaration_stmt.items
    
    # Process the type specification
    type_spec = process_type_spec(type_spec)
    
    # Process attribute specifications if present
    if attr_specs:
        attrs = process_attr_specs(attr_specs)
    else:
        attrs = AttrSpec()
    
    # Create a new container for the declarations
    entities = {}
    
    # Process single entity declaration
    if isinstance(entity_decls, Entity_Decl):
        entity = from_entity_decl(entity_decls, line_no, type_spec, attrs)
        entities.update({entity.name: entity})
    # Process multiple entity declarations
    elif isinstance(entity_decls, Entity_Decl_List):
        for entity_decl in entity_decls.items:
            entity = from_entity_decl(entity_decl, line_no, type_spec, attrs)
            entities.update({entity.name: entity})
    else:
        raise ValueError(f"Unexpected entity declaration type: {type(entity_decls)}")
    
    return entities
