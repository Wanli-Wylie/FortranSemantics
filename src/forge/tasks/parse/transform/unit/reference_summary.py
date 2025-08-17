

def parse_resolved_symbol(resolved_symbol: str) -> str:
    """
    Parse the resolved symbol from a string.
    """
    return resolved_symbol.split(".")[-1]