from pathlib import Path
from fparser.common.readfortran import FortranStringReader
from fparser.two.parser import ParserFactory
from fparser.two.Fortran2003 import Base, Program, Module

def parse_fortran_to_ast(fortran_code: str) -> Base | Program:
    """
    Parse a Fortran program string into an Abstract Syntax Tree (AST).
    
    Args:
        fortran_code (str): The Fortran program code as a string
        
    Returns:
        The parsed AST object
        
    Raises:
        FortranSyntaxError: If the Fortran code is invalid
    """
    # Create a reader for the Fortran code
    reader = FortranStringReader(fortran_code)
    
    # Create a parser for Fortran 2008 standard
    parser = ParserFactory().create(std="f2003")
    
    # Parse the code and return the AST
    ast = parser(reader)
    if ast is None:
        raise ValueError("Failed to parse Fortran code")
    return ast

def insert_content_into_module(decls: str = "", contains: str = "") -> str:
    """
    Insert a list of declarations into a module
    """
    template = f'''
MODULE TEST
    {decls}
CONTAINS
    {contains}
END MODULE TEST
'''
    return template


def get_module_ast(filename: str):
    path = Path("example/basic") / filename
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    program_ast = parse_fortran_to_ast(src)
    return program_ast.children[0]

def get_all_f90_files():
    return list(Path("example/basic").glob("*.f90"))

def get_example_project_dependency_graph():
    from Fortran2.infrastructure.etl.load.to_memory import load_to_memory
    _, dependency_graph = load_to_memory(get_all_f90_files())
    return dependency_graph