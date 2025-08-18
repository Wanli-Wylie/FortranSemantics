from fparser.two.Fortran2003 import (
    Explicit_Shape_Spec,
    Deferred_Shape_Spec,
    Assumed_Shape_Spec,
    Array_Spec
)
from typing import List
from fpyevolve_core.models.fortran.attr_spec import DimensionSpec, DimKind, ArraySpec

def process_array_spec(array_spec: Array_Spec) -> ArraySpec:
    """Process array specification and return dimension information list"""
    dimensions: List[DimensionSpec] = []
    if not array_spec or not hasattr(array_spec, 'items'):
        return ArraySpec(dimensions=dimensions)
        
    for item in array_spec.items:
        if isinstance(item, Explicit_Shape_Spec):
            # Process explicit shape array, e.g. dimension(1:10, 2:20)
            dim_info = DimensionSpec(
                kind=DimKind.explicit,
                lower=str(item.items[0]) if item.items[0] else None,
                upper=str(item.items[1]) if item.items[1] else None
            )
            dimensions.append(dim_info)
        elif isinstance(item, Deferred_Shape_Spec):
            # Process deferred shape array, e.g. dimension(:)
            dim_info = DimensionSpec(
                kind=DimKind.deferred,
                lower=None,
                upper=None
            )
            dimensions.append(dim_info)
        elif isinstance(item, Assumed_Shape_Spec):
            # Process assumed shape array, e.g. dimension(*)
            dim_info = DimensionSpec(
                kind=DimKind.assumed,
                lower=None,
                upper=None
            )
            dimensions.append(dim_info)
            
    return ArraySpec(dimensions=dimensions) 