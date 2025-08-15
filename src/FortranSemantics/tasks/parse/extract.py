from fparser.common.readfortran import FortranStringReader
from fparser.two.parser import ParserFactory
from fparser.two.utils import FortranSyntaxError
import logging
from fparser.two.Fortran2003 import Module, Subroutine_Subprogram, Function_Subprogram, Program

logger = logging.getLogger(__name__)

def extract_from_fortran_string(
        fortran_string: str,
        lowering: bool = True
    ) -> Module | Subroutine_Subprogram | Function_Subprogram | Program | None:
    """Parse a Fortran program (given as a string) and return its AST.

    Args:
        fortran_string:   Fortran source code.
    Returns:
        Module on success; None on failure.
    """
    logger.info(
        "Processing Fortran string (len=%d)...",
    )

    try:
        if lowering:
            fortran_string = fortran_string.lower()
        reader = FortranStringReader(fortran_string)
        parser = ParserFactory().create()
        ast = parser(reader)

        return ast

    except FortranSyntaxError as exc:
        logger.error("Syntax error in Fortran code: %s", exc)
        return None
    except Exception as exc:
        logger.error("Error processing Fortran code: %s", exc)
        return None

def pickup_module_ast(ast: Program) -> Module:
    return ast.children[0]