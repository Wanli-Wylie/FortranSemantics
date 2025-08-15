import pytest
from fparser.two.Fortran2003 import Intrinsic_Type_Spec, Declaration_Type_Spec
from Fortran2.tasks.parse_fortran.etl.transform.attrs.process_type_spec import process_type_spec

def test_intrinsic_type_spec():
    """Test processing of intrinsic type specifications"""
    # Test basic intrinsic types
    assert process_type_spec(Intrinsic_Type_Spec("INTEGER")) == "INTEGER"
    assert process_type_spec(Intrinsic_Type_Spec("REAL")) == "REAL"
    assert process_type_spec(Intrinsic_Type_Spec("CHARACTER")) == "CHARACTER"
    assert process_type_spec(Intrinsic_Type_Spec("LOGICAL")) == "LOGICAL"
    assert process_type_spec(Intrinsic_Type_Spec("COMPLEX")) == "COMPLEX"
    
    # Test case insensitivity (should be converted to uppercase)
    assert process_type_spec(Intrinsic_Type_Spec("integer")) == "INTEGER"
    assert process_type_spec(Intrinsic_Type_Spec("Real")) == "REAL"

# def test_declaration_type_spec():
#     """Test processing of declaration type specifications"""
#     # Test basic type declarations
    
    
    
#     type_spec = Declaration_Type_Spec("TYPE(my_type)")
#     assert process_type_spec(type_spec) == "TYPE-MY_TYPE"


def test_unknown_type_spec():
    """Test handling of unknown type specifications"""
    # Test with None
    assert process_type_spec(None) == "UNKNOWN"
    
    # Test with string
    assert process_type_spec("some_type") == "UNKNOWN"
    
    # Test with integer
    assert process_type_spec(42) == "UNKNOWN"
