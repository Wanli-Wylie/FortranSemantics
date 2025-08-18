from fparser.common.readfortran import FortranStringReader
from fparser.two.parser import ParserFactory
from fparser.two.utils import FortranSyntaxError
import logging
import time
from fparser.two.Fortran2003 import Module, Subroutine_Subprogram, Function_Subprogram, Program

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
BASE_DELAY = 0.1  # Base delay in seconds
MAX_DELAY = 2.0   # Maximum delay in seconds

def extract_from_fortran_string(
        fortran_string: str,
        lowering: bool = True
    ) -> Module | Subroutine_Subprogram | Function_Subprogram | Program | None:
    """Parse a Fortran program (given as a string) and return its AST.

    Args:
        fortran_string:   Fortran source code.
        lowering:         Whether to convert to lowercase before parsing.
    Returns:
        Module, Subroutine_Subprogram, Function_Subprogram, or Program on success; None on failure.
    """
    logger.info(
        "Processing Fortran string (len=%d)...",
        len(fortran_string)
    )

    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            if lowering:
                fortran_string = fortran_string.lower()
            
            reader = FortranStringReader(fortran_string)
            parser = ParserFactory().create()
            ast = parser(reader)

            if attempt > 0:
                logger.info("Successfully parsed Fortran code on attempt %d", attempt + 1)
            
            return ast

        except FortranSyntaxError as exc:
            last_exception = exc
            logger.warning("Syntax error in Fortran code (attempt %d/%d): %s", 
                         attempt + 1, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES - 1:
                logger.error("Final attempt failed with syntax error: %s", exc)
                return None
                
        except Exception as exc:
            last_exception = exc
            logger.warning("Error processing Fortran code (attempt %d/%d): %s", 
                         attempt + 1, MAX_RETRIES, exc)
            
            # Don't retry on certain types of errors that won't be fixed by retrying
            if isinstance(exc, (ValueError, TypeError, AttributeError)):
                logger.error("Non-retryable error encountered: %s", exc)
                return None
            
            if attempt == MAX_RETRIES - 1:
                logger.error("Final attempt failed with error: %s", exc)
                return None
        
        # Calculate delay with exponential backoff
        if attempt < MAX_RETRIES - 1:
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
            logger.info("Retrying in %.2f seconds...", delay)
            time.sleep(delay)
    
    logger.error("Failed to parse Fortran code after %d attempts. Last error: %s", 
                MAX_RETRIES, last_exception)
    return None

def pickup_module_ast(ast: Program) -> Module:
    """Extract the first module from a program AST.
    
    Args:
        ast: The program AST to extract from.
        
    Returns:
        The first module found in the AST.
        
    Raises:
        IndexError: If no children are found in the AST.
        AttributeError: If the AST doesn't have a children attribute.
    """
    if not hasattr(ast, 'children') or not ast.children:
        raise ValueError("AST has no children to extract from")
    
    return ast.children[0]