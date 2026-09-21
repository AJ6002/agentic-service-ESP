from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    source_field: str = Field(..., description="Raw field name in domain data source")
    canonical_field: str = Field(..., description="Target canonical field name")
    data_type: str = Field("float", description="Data type of the field")
    unit: str = Field("", description="Unit of measurement")
    conversion_rule: Optional[str] = Field(None, description="Optional conversion formula or rule")
    valid_range: Optional[List[float]] = Field(None, description="Optional min and max valid range [min, max]")
    is_required: bool = Field(True, description="Whether this field is mandatory for diagnosis")


class MappingConfig(BaseModel):
    domain_id: str = Field(..., description="Domain identifier for the mapping configuration")
    field_mappings: Union[List[FieldMapping], Dict[str, Any]] = Field(
        ..., description="List or dictionary of field mappings from raw to canonical concepts"
    )

    def get_mappings_list(self) -> List[FieldMapping]:
        """Normalize field_mappings into a list of FieldMapping objects regardless of input format."""
        if isinstance(self.field_mappings, list):
            return [
                item if isinstance(item, FieldMapping) else FieldMapping(**item)
                for item in self.field_mappings
            ]
        elif isinstance(self.field_mappings, dict):
            res = []
            for src, tgt in self.field_mappings.items():
                if isinstance(tgt, str):
                    res.append(FieldMapping(source_field=src, canonical_field=tgt))
                elif isinstance(tgt, dict):
                    res.append(FieldMapping(source_field=src, **tgt))
            return res
        return []
