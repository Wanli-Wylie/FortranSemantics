from typing import Iterable

def is_iterable(obj):
    if hasattr(obj, 'children') and isinstance(obj.children, Iterable):
        if len(obj.children) > 0:
            return True
    return False

