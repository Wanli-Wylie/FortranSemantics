from fparser.two.Fortran2003 import (
    Entity_Decl
)
from forge.tasks.parse.transform.unit.declared_entity import from_entity_decl
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from forge.data_models.fortran.attr_spec import DimKind, AttrSpec

def create_entity_decl_from_declaration(decl_str: str) -> Entity_Decl:
    """Helper function to create entity declaration from a declaration string"""
    # Create a minimal program with the declaration
    code = insert_content_into_module(decl_str)
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0].items[2].items[0]

def test_basic_entity_declaration():
    """Test processing of basic entity declarations"""
    # Test simple variable declaration
    entity_decl = create_entity_decl_from_declaration("integer :: var")
    result = from_entity_decl(entity_decl, line_no=1, type_name="INTEGER", attrs=AttrSpec())
    assert result.name == "var"
    assert result.type_declared == "INTEGER"
    assert result.line_declared == 1
    assert result.initial_value is None
    assert not hasattr(result, 'dimensions')

def test_entity_with_initialization():
    """Test processing of entity declarations with initialization"""
    # Test with simple initialization
    entity_decl = create_entity_decl_from_declaration("integer :: var = 42")
    result = from_entity_decl(entity_decl, line_no=1, type_name="INTEGER", attrs=AttrSpec())
    assert result.name == "var"
    assert result.initial_value == "42"

    # Test with expression initialization
    entity_decl = create_entity_decl_from_declaration("real :: var = 3.14 * 2")
    result = from_entity_decl(entity_decl, line_no=1, type_name="REAL", attrs=AttrSpec())
    assert result.name == "var"
    assert result.initial_value == "3.14 * 2"

def test_entity_with_dimensions():
    """Test processing of entity declarations with array dimensions"""
    # Test with explicit shape array
    entity_decl = create_entity_decl_from_declaration("integer :: arr(1:10)")
    result = from_entity_decl(entity_decl, line_no=1, type_name="INTEGER", attrs=AttrSpec())
    assert result.name == "arr"

    # Test with multiple dimensions
    entity_decl = create_entity_decl_from_declaration("real :: arr(1:10, 2:20)")
    result = from_entity_decl(entity_decl, line_no=1, type_name="REAL", attrs=AttrSpec())
    assert result.name == "arr"
    assert result.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.attributes.array_spec.dimensions[0].lower == '1'
    assert result.attributes.array_spec.dimensions[0].upper == '10'
    assert result.attributes.array_spec.dimensions[1].kind == DimKind.explicit
    assert result.attributes.array_spec.dimensions[1].lower == '2'
    assert result.attributes.array_spec.dimensions[1].upper == '20'


def test_entity_with_combined_attributes():
    """Test processing of entity declarations with multiple attributes"""
    # Test with dimensions and intent
    entity_decl = create_entity_decl_from_declaration("integer :: arr(1:10)")
    result = from_entity_decl(entity_decl, line_no=1, type_name="INTEGER", attrs=AttrSpec())
    assert result.name == "arr"
    assert result.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.attributes.array_spec.dimensions[0].lower == '1'
    assert result.attributes.array_spec.dimensions[0].upper == '10'

    # Test with dimensions, intent and initialization
    entity_decl = create_entity_decl_from_declaration("real :: arr(1:10) = 0.0")
    result = from_entity_decl(entity_decl, line_no=1, type_name="REAL", attrs=AttrSpec())
    assert result.name == "arr"
    assert result.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.attributes.array_spec.dimensions[0].lower == '1'
    assert result.attributes.array_spec.dimensions[0].upper == '10'
    assert result.initial_value == "0.0" 
