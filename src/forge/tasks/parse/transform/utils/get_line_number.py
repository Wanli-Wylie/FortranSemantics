from .is_iterable import is_iterable

def get_line_number(ast_node: object) -> int:
    """
    Get the line number of an AST node.
    """
    current_node = ast_node
    while current_node:
        if hasattr(current_node, 'item') and hasattr(current_node.item, 'span'):
            return current_node.item.span[0]
        else:
            if is_iterable(current_node):
                current_node = current_node.children[0]
            else:
                current_node = None
        
    return -1
