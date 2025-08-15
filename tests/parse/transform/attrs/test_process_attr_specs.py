import pytest
from fparser.two.Fortran2003 import (
    Attr_Spec_List
)
from Fortran2.tasks.parse_fortran.etl.transform.attrs.process_attr_specs import process_attr_specs
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from Fortran2.data_models.fortran.attr_spec import DimKind

def create_attr_spec_from_declaration(decl_str: str) -> Attr_Spec_List:
    """Helper function to create attribute specification from a declaration string"""
    # Create a minimal program with the declaration
    code = insert_content_into_module(decl_str)
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0].items[1]

def test_basic_attr_specs():
    """Test processing of basic attribute specifications"""
    # Test with single attribute
    attr_spec = create_attr_spec_from_declaration("integer, allocatable :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "allocatable" in result.additional_keywords

    # Test with multiple attributes
    attr_spec = create_attr_spec_from_declaration("integer, allocatable, save :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "allocatable" in result.additional_keywords
    assert "save" in result.additional_keywords

def test_dimension_attr_spec():
    """Test processing of dimension attribute specifications"""
    # Test with single dimension
    attr_spec = create_attr_spec_from_declaration("integer, dimension(1:10) :: arr")
    result = process_attr_specs(attr_spec)
    assert result.array_spec is not None
    assert len(result.array_spec.dimensions) == 1
    assert result.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.array_spec.dimensions[0].lower == '1'
    assert result.array_spec.dimensions[0].upper == '10'

    # Test with multiple dimensions
    attr_spec = create_attr_spec_from_declaration("real, dimension(1:10, 2:20) :: arr")
    result = process_attr_specs(attr_spec)
    assert result.array_spec is not None
    assert len(result.array_spec.dimensions) == 2
    assert result.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.array_spec.dimensions[0].lower == '1'
    assert result.array_spec.dimensions[0].upper == '10'
    assert result.array_spec.dimensions[1].kind == DimKind.explicit
    assert result.array_spec.dimensions[1].lower == '2'
    assert result.array_spec.dimensions[1].upper == '20'

def test_intent_attr_spec():
    """Test processing of intent attribute specifications"""
    # Test with intent(in)
    attr_spec = create_attr_spec_from_declaration("integer, intent(in) :: var")
    result = process_attr_specs(attr_spec)
    assert result.intent == 'in'

    # Test with intent(out)
    attr_spec = create_attr_spec_from_declaration("real, intent(out) :: var")
    result = process_attr_specs(attr_spec)
    assert result.intent == 'out'

    # Test with intent(inout)
    attr_spec = create_attr_spec_from_declaration("integer, intent(inout) :: var")
    result = process_attr_specs(attr_spec)
    assert result.intent == 'inout'

def test_combined_attr_specs():
    """Test processing of combined attribute specifications"""
    # Test with dimension and intent
    attr_spec = create_attr_spec_from_declaration("integer, dimension(1:10), intent(in) :: arr")
    result = process_attr_specs(attr_spec)
    assert result.array_spec is not None
    assert len(result.array_spec.dimensions) == 1
    assert result.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.array_spec.dimensions[0].lower == '1'
    assert result.array_spec.dimensions[0].upper == '10'
    assert result.intent == 'in'

    # Test with multiple attributes including allocatable
    attr_spec = create_attr_spec_from_declaration("real, allocatable, dimension(:), intent(out) :: arr")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "allocatable" in result.additional_keywords
    assert result.array_spec is not None
    assert len(result.array_spec.dimensions) == 1
    assert result.array_spec.dimensions[0].kind == DimKind.assumed
    assert result.array_spec.dimensions[0].lower is None
    assert result.array_spec.dimensions[0].upper is None
    assert result.intent == 'out'

def test_special_attr_specs():
    """Test processing of special attribute specifications"""
    # Test with parameter attribute
    attr_spec = create_attr_spec_from_declaration("integer, parameter :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "parameter" in result.additional_keywords

    # Test with target attribute
    attr_spec = create_attr_spec_from_declaration("real, target :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "target" in result.additional_keywords

    # Test with pointer attribute
    attr_spec = create_attr_spec_from_declaration("integer, pointer :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "pointer" in result.additional_keywords

    # Test with volatile attribute
    attr_spec = create_attr_spec_from_declaration("real, volatile :: var")
    result = process_attr_specs(attr_spec)
    assert result.additional_keywords is not None
    assert "volatile" in result.additional_keywords
