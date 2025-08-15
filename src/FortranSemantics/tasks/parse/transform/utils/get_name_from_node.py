import logging
from fparser.two.Fortran2003 import (
    Program_Stmt,
    Module_Stmt,
    Function_Stmt,
    Subroutine_Stmt,
    Main_Program,
    Module,
    Function_Subprogram,
    Subroutine_Subprogram,
    Use_Stmt,
    Derived_Type_Def,
    Function_Body,
    Subroutine_Body,
    Data_Component_Def_Stmt,
    Component_Decl_List,
    Component_Decl
)

logger = logging.getLogger(__name__)

def get_name_from_node(node):
    """
    Extract name from node. Uses different extraction strategies based on node type.
    
    Mainly handles the following cases:
    1. Program/Module/Function/Subroutine statement nodes
    2. Program/Module/Function/Subroutine program unit nodes
    3. Use statement nodes
    4. Other nodes with items attribute
    """
    try:
        # Handle statement-level nodes
        if isinstance(node, (Program_Stmt, Module_Stmt, Function_Stmt, Subroutine_Stmt)):
            # These statement nodes typically store the name in items[0]
            name = str(node.items[1])
            logger.debug(f"Extracted name '{name}' from statement node")
            return name
        
        # Handle program unit-level nodes
        elif isinstance(node, (Main_Program, Module, Function_Subprogram, Subroutine_Subprogram, Function_Body, Subroutine_Body)):
            # Program unit nodes typically store the name in the first child node (stmt)
            for child in node.children:
                if isinstance(child, (Program_Stmt, Module_Stmt, Function_Stmt, Subroutine_Stmt)):
                    return get_name_from_node(child)
        
        # Handle Use statements
        elif isinstance(node, Use_Stmt):
            # Module name in Use statements is typically in items[2]
            name = str(node.items[2])
            logger.debug(f"Extracted name '{name}' from USE statement")
            return name
        
        # Handle derived type definitions
        elif isinstance(node, Derived_Type_Def):
            name = str(node.children[0].items[1])
            logger.debug(f"Extracted name '{name}' from derived type definition")
            return name
        
        elif isinstance(node, Data_Component_Def_Stmt):
            
            if isinstance(node.items[2], Component_Decl_List):
                names = [str(item.items[0]) for item in node.items[2].items]
                logger.debug(f"Extracted names '{names}' from data component definition")
                return names
            elif isinstance(node.items[2], Component_Decl):
                
                raise ValueError(f"Unknown data component definition: {node.items[2]}")
        
        # Handle other nodes with items attribute
        elif hasattr(node, 'items') and node.items:
            # Iterate through items to find available names
            for item in node.items:
                # Check string attribute
                if hasattr(item, 'string'):
                    name = item.string
                    logger.debug(f"Extracted name '{name}' from node with string attribute")
                    return name
                # Check if it's a string
                elif isinstance(item, str):
                    name = item
                    logger.debug(f"Extracted name '{name}' from node with string attribute")
                    return name
                # Check name attribute
                elif hasattr(item, 'name'):
                    name = str(item.name)
                    logger.debug(f"Extracted name '{name}' from node with name attribute")
                    return name
        
        # If node has name attribute
        elif hasattr(node, 'name'):
            name = str(node.name)
            logger.debug(f"Extracted name '{name}' from node with name attribute")
            return name
        
        # If node has string attribute
        elif hasattr(node, 'string'):
            name = str(node.string)
            logger.debug(f"Extracted name '{name}' from node with string attribute")
            return name
        
        logger.debug(f"Extracted name '{name}' from node of type {type(node).__name__}")
        return name
    
    except Exception as e:
        logger.warning(f"Failed to extract name from node {type(node)}: {str(e)}")
        return "unnamed"