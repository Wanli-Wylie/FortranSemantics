import pytest
from fparser.two.Fortran2003 import (
    Type_Declaration_Stmt,
    Program
)
from FortranSemantics.tasks.parse.transform.unit.declared_entity import from_type_declaration_stmt
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from FortranSemantics.data_models.fortran.attr_spec import DimKind

def create_type_declaration_from_string(decl_str: str) -> Type_Declaration_Stmt:
    """Helper function to create type declaration statement from a declaration string"""
    # Create a minimal program with the declaration
    code = insert_content_into_module(decls=decl_str, contains="")
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0]

def test_basic_type_declaration():
    """Test processing of basic type declarations"""
    # Test simple variable declaration
    type_decl = create_type_declaration_from_string("integer :: var")
    result = from_type_declaration_stmt(type_decl)
    assert len(result) == 1
    var = result['var']
    assert var.name == "var"
    assert var.type_declared == "INTEGER"
    assert var.line_declared == 3
    assert var.initial_value is None
    assert not hasattr(var, 'array_spec')

    # Test multiple variables in one declaration
    type_decl = create_type_declaration_from_string("real :: var1, var2, var3")
    result = from_type_declaration_stmt(type_decl)
    assert len(result) == 3
    assert all(name in result for name in ['var1', 'var2', 'var3'])
    for var in result.values():
        assert var.type_declared == "REAL"
        assert var.line_declared == 3

def test_type_declaration_with_attributes():
    """Test processing of type declarations with attributes"""
    # Test with allocatable attribute
    type_decl = create_type_declaration_from_string("integer, allocatable :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert "allocatable" in var.attributes.additional_keywords

    # Test with multiple attributes
    type_decl = create_type_declaration_from_string("real, allocatable, save :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert "allocatable" in var.attributes.additional_keywords
    assert "save" in var.attributes.additional_keywords

def test_type_declaration_with_dimensions():
    """Test processing of type declarations with array dimensions"""
    # Test with single dimension
    type_decl = create_type_declaration_from_string("integer, dimension(1:10) :: arr")
    result = from_type_declaration_stmt(type_decl)
    var = result['arr']
    assert var.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert var.attributes.array_spec.dimensions[0].lower == '1'
    assert var.attributes.array_spec.dimensions[0].upper == '10'

    # Test with multiple dimensions
    type_decl = create_type_declaration_from_string("real, dimension(1:10, 2:20) :: arr")
    result = from_type_declaration_stmt(type_decl)
    var = result['arr']
    assert var.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert var.attributes.array_spec.dimensions[0].lower == '1'
    assert var.attributes.array_spec.dimensions[0].upper == '10'
    assert var.attributes.array_spec.dimensions[1].kind == DimKind.explicit
    assert var.attributes.array_spec.dimensions[1].lower == '2'
    assert var.attributes.array_spec.dimensions[1].upper == '20'

def test_type_declaration_with_intent():
    """Test processing of type declarations with intent"""
    # Test with intent(in)
    type_decl = create_type_declaration_from_string("integer, intent(in) :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert var.attributes.intent == 'in'

    # Test with intent(out)
    type_decl = create_type_declaration_from_string("real, intent(out) :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert var.attributes.intent == 'out'

def test_type_declaration_with_initialization():
    """Test processing of type declarations with initialization"""
    # Test with simple initialization
    type_decl = create_type_declaration_from_string("integer :: var = 42")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert var.initial_value == "42"

    # Test with expression initialization
    type_decl = create_type_declaration_from_string("real :: var = 3.14 * 2")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert var.initial_value == "3.14 * 2"

def test_complex_type_declaration():
    """Test processing of complex type declarations with multiple attributes"""
    # Test with dimensions, intent and initialization
    type_decl = create_type_declaration_from_string("real, dimension(1:10), intent(in) :: arr = 0.0")
    result = from_type_declaration_stmt(type_decl)
    var = result['arr']
    assert var.attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert var.attributes.array_spec.dimensions[0].lower == '1'
    assert var.attributes.array_spec.dimensions[0].upper == '10'
    assert var.attributes.intent == 'in'
    assert var.initial_value == "0.0"

    # Test with allocatable array and intent
    type_decl = create_type_declaration_from_string("real, allocatable, dimension(:), intent(out) :: arr")
    result = from_type_declaration_stmt(type_decl)
    var = result['arr']
    assert "allocatable" in var.attributes.additional_keywords
    assert var.attributes.intent == 'out'
    assert var.attributes.array_spec.dimensions[0].kind == DimKind.assumed
    assert var.attributes.array_spec.dimensions[0].lower is None
    assert var.attributes.array_spec.dimensions[0].upper is None

def test_special_type_declarations():
    """Test processing of special type declarations"""
    # Test with parameter attribute
    type_decl = create_type_declaration_from_string("integer, parameter :: var = 42")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert "parameter" in var.attributes.additional_keywords
    assert var.initial_value == "42"

    # Test with pointer attribute
    type_decl = create_type_declaration_from_string("real, pointer :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert "pointer" in var.attributes.additional_keywords

    # Test with target attribute
    type_decl = create_type_declaration_from_string("integer, target :: var")
    result = from_type_declaration_stmt(type_decl)
    var = result['var']
    assert "target" in var.attributes.additional_keywords
