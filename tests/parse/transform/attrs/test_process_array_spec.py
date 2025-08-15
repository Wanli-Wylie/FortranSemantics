from fparser.two.Fortran2003 import (
    Array_Spec,
    Type_Declaration_Stmt,
    Entity_Decl,
    Program
)
from FortranSemantics.tasks.parse.transform.attrs.process_array_spec import process_array_spec
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from FortranSemantics.data_models.fortran.attr_spec import DimKind

def create_array_spec_from_declaration(decl_str: str) -> Array_Spec:
    """Helper function to create array spec from a declaration string"""
    # Create a minimal program with the declaration
    code = insert_content_into_module(decl_str)
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0].items[2].items[0].items[1]

def test_explicit_shape_array():
    """Test processing of explicit shape array specifications"""
    # Test with single dimension
    array_spec = create_array_spec_from_declaration("integer :: arr(1:10)")
    result = process_array_spec(array_spec)
    assert len(result.dimensions) == 1
    assert result.dimensions[0].kind == DimKind.explicit
    assert result.dimensions[0].lower == '1'
    assert result.dimensions[0].upper == '10'
    

    # Test with multiple dimensions
    array_spec = create_array_spec_from_declaration("integer :: arr(1:10, 2:20)")
    result = process_array_spec(array_spec)
    assert len(result.dimensions) == 2
    assert result.dimensions[0].kind == DimKind.explicit
    assert result.dimensions[0].lower == '1'
    assert result.dimensions[0].upper == '10'
    
    assert result.dimensions[1].kind == 'explicit'
    assert result.dimensions[1].lower == '2'
    assert result.dimensions[1].upper == '20'

def test_assumed_shape_array():
    """Test processing of deferred shape array specifications"""
    
    array_spec = create_array_spec_from_declaration("integer :: arr(:)")
    result = process_array_spec(array_spec)
    assert len(result.dimensions) == 1
    assert result.dimensions[0].kind == DimKind.assumed
    assert result.dimensions[0].lower is None
    assert result.dimensions[0].upper is None

    # Test with multiple dimensions
    array_spec = create_array_spec_from_declaration("integer :: arr(:,:)")
    result = process_array_spec(array_spec)
    assert len(result.dimensions) == 2
    assert result.dimensions[0].kind == DimKind.assumed
    assert result.dimensions[0].lower is None
    assert result.dimensions[0].upper is None
    
    assert result.dimensions[1].kind == DimKind.assumed
    assert result.dimensions[1].lower is None
    assert result.dimensions[1].upper is None

# def test_deferred_shape_array():
#     """Test processing of assumed shape array specifications"""
#     array_spec = create_array_spec_from_declaration("integer, allocatable :: arr(:)")
#     result = process_array_spec(array_spec)
#     assert len(result) == 1
#     assert result[0] == {
#         'type': 'deferred',
#         'lower': None,
#         'upper': None
#     }

#     # Test with multiple dimensions
#     array_spec = create_array_spec_from_declaration("integer, allocatable :: arr(:,:)")
    
#     result = process_array_spec(array_spec)
#     assert len(result) == 2
#     assert result[0] == {
#         'type': 'deferred',
#         'lower': None,
#         'upper': None
#     }
#     assert result[1] == {
#         'type': 'deferred',
#         'lower': None,
#         'upper': None
#     }

# def test_mixed_array_types():
#     """Test processing of mixed array specification types"""
#     array_spec = create_array_spec_from_declaration("integer :: arr(1:10, :, :)")
#     result = process_array_spec(array_spec)
#     assert len(result) == 3
#     assert result[0] == {
#         'type': 'explicit',
#         'lower': '1',
#         'upper': '10'
#     }
#     assert result[1] == {
#         'type': 'assumed',
#         'lower': None,
#         'upper': None
#     }
#     assert result[2] == {
#         'type': 'assumed',
#         'lower': None,
#         'upper': None
#     }
