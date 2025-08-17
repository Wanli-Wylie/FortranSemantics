from fparser.two.Fortran2003 import Derived_Type_Def, Data_Component_Def_Stmt
from forge.tasks.parse.transform.unit.derived_type_definition import from_derived_type_definition
from tests.helpers import parse_fortran_to_ast, insert_content_into_module
from forge.data_models.fortran.attr_spec import DimKind

def create_derived_type_from_str(content: str) -> Derived_Type_Def:
    """Helper function to create derived type definition from a string"""
    code = insert_content_into_module(content)
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0]

def create_data_component_from_str(content: str) -> Data_Component_Def_Stmt:
    """Helper function to create data component definition from a string"""
    code = insert_content_into_module(content)
    ast = parse_fortran_to_ast(code)
    return ast.content[0].content[1].content[0]

# Tests for complete derived type definitions
def test_basic_derived_type():
    """Test processing of basic derived type definition"""
    content = """
    TYPE :: point
        REAL :: x, y
    END TYPE point
    """
    derived_type = create_derived_type_from_str(content)
    result = from_derived_type_definition(derived_type)
    
    assert result.name == "point"
    assert len(result.declared_components) == 2
    assert "x" in result.declared_components
    assert "y" in result.declared_components

def test_derived_type_with_components():
    """Test processing of derived type with various component types"""
    content = """
    TYPE :: employee
        CHARACTER(LEN=20) :: name
        INTEGER :: age
        REAL, DIMENSION(3) :: salary
        LOGICAL :: is_active
    END TYPE employee
    """
    derived_type = create_derived_type_from_str(content)
    result = from_derived_type_definition(derived_type)
    
    assert result.name == "employee"
    assert len(result.declared_components) == 4
    assert "name" in result.declared_components
    assert "age" in result.declared_components
    assert "salary" in result.declared_components
    assert "is_active" in result.declared_components

def test_derived_type_with_attributes():
    """Test processing of derived type with component attributes"""
    content = """
    TYPE :: matrix
        REAL, ALLOCATABLE :: data(:,:)
        INTEGER :: max_size = 100
        REAL, POINTER :: ptr_data(:)
    END TYPE matrix
    """
    derived_type = create_derived_type_from_str(content)
    result = from_derived_type_definition(derived_type)
    
    assert result.name == "matrix"
    assert len(result.declared_components) == 3
    assert "data" in result.declared_components
    assert "max_size" in result.declared_components
    assert "ptr_data" in result.declared_components

def test_derived_type_with_private_components():
    """Test processing of derived type with private components"""
    content = """
    TYPE :: bank_account
        PRIVATE
        REAL :: balance
        INTEGER :: account_number
    END TYPE bank_account
    """
    derived_type = create_derived_type_from_str(content)
    result = from_derived_type_definition(derived_type)
    
    assert result.name == "bank_account"
    assert len(result.declared_components) == 2
    assert "balance" in result.declared_components
    assert "account_number" in result.declared_components

# Tests for individual data components
def test_basic_data_component():
    """Test processing of basic data component definition"""
    content = """
    TYPE :: point
        REAL :: x
    END TYPE point
    """
    component = create_data_component_from_str(content)
    result = from_derived_type_definition(component)
    
    assert len(result.declared_components) == 1
    assert "x" in result.declared_components
    assert result.declared_components["x"].type_declared == "REAL"
    assert result.declared_components["x"].attributes.additional_keywords is None

def test_data_component_with_attributes():
    """Test processing of data component with attributes"""
    content = """
    TYPE :: matrix
        REAL, ALLOCATABLE :: data
    END TYPE matrix
    """
    component = create_data_component_from_str(content)
    result = from_derived_type_definition(component)
    
    assert len(result.declared_components) == 1
    assert "data" in result.declared_components
    assert result.declared_components["data"].type_declared == "REAL"
    assert result.declared_components["data"].attributes.additional_keywords == ["allocatable"]

def test_data_component_with_array():
    """Test processing of data component with array specification"""
    content = """
    TYPE :: vector
        REAL, DIMENSION(3), POINTER :: components
    END TYPE vector
    """
    component = create_data_component_from_str(content)
    result = from_derived_type_definition(component)
    
    assert len(result.declared_components) == 1
    assert "components" in result.declared_components
    assert result.declared_components["components"].type_declared == "REAL"
    assert result.declared_components["components"].attributes.array_spec.dimensions[0].kind == DimKind.explicit
    assert result.declared_components["components"].attributes.array_spec.dimensions[0].lower is None
    assert result.declared_components["components"].attributes.array_spec.dimensions[0].upper == "3"
    assert result.declared_components["components"].attributes.additional_keywords == ["pointer"]

def test_data_component_with_multiple_attributes():
    """Test processing of data component with multiple attributes"""
    content = """
    TYPE :: complex_data
        REAL, ALLOCATABLE, POINTER :: data(:,:)
    END TYPE complex_data
    """
    component = create_data_component_from_str(content)
    result = from_derived_type_definition(component)
    
    assert len(result.declared_components) == 1
    assert "data" in result.declared_components
    assert result.declared_components["data"].type_declared == "REAL"
    assert result.declared_components["data"].attributes.additional_keywords == ["allocatable", "pointer"]
    assert len(result.declared_components["data"].attributes.array_spec.dimensions) == 2
    assert result.declared_components["data"].attributes.array_spec.dimensions[0].kind == DimKind.deferred
    assert result.declared_components["data"].attributes.array_spec.dimensions[0].lower is None
    assert result.declared_components["data"].attributes.array_spec.dimensions[0].upper is None

def test_data_component_with_parameter():
    """Test processing of data component with parameter attribute"""
    content = """
    TYPE :: constants
        REAL :: pi = 3.14159
    END TYPE constants
    """
    component = create_data_component_from_str(content)
    result = from_derived_type_definition(component)
    
    assert len(result.declared_components) == 1
    assert "pi" in result.declared_components
    assert result.declared_components["pi"].type_declared == "REAL"
    assert result.declared_components["pi"].initial_value == "3.14159" 
