from fparser.two.Fortran2003 import (
    Attr_Spec_List,
    Dimension_Attr_Spec, 
    Dimension_Component_Attr_Spec,
    Intent_Attr_Spec, 
)
from .process_array_spec import process_array_spec
from .....data_models.fortran.attr_spec import AttrSpec

def process_attr_specs(attr_specs: Attr_Spec_List) -> AttrSpec:
    """Process attribute specification list and return attribute dictionary"""
    attrs = {}

    if not attr_specs or not hasattr(attr_specs, 'items'):
        return AttrSpec(**attrs)
        
    for item in attr_specs.items:
        if isinstance(item, (Dimension_Attr_Spec, Dimension_Component_Attr_Spec)):
            array_spec = item.items[1]
            dimensions = process_array_spec(array_spec)
            if dimensions:
                attrs['array_spec'] = dimensions
        elif isinstance(item, Intent_Attr_Spec):
            # Process INTENT attribute
            intent_spec = str(item.items[1]).lower()
            attrs['intent'] = intent_spec
        else:
            if attrs.get('additional_keywords') is None:
                attrs['additional_keywords'] = []
            attrs['additional_keywords'].append(str(item).lower())
    
    if attrs.get('additional_keywords') is None:
        attrs['additional_keywords'] = []
            
    return AttrSpec(**attrs)
