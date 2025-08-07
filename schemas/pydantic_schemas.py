from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Condition(BaseModel):
    name: str
    description: str

class Medication(BaseModel):
    name: str
    description: str

class UrgentFlag(BaseModel):
    condition: str
    explanation: str

# class RecommendedCare(BaseModel):
#     self_care: List[str] = Field(..., alias="self-care")
#     medications: List[Medication]
#     lifestyle: List[str]

class RecommendedCare(BaseModel):
    self_care: List[str] = Field(default_factory=list, alias="self-care")
    medications: Optional[List[Medication]] = Field(default_factory=list)
    lifestyle: Optional[List[str]] = Field(default_factory=list)

class DoctorResponse(BaseModel):
    summary: str
    confidence_level: Literal["low", "medium", "high"]
    possible_conditions: List[Condition]
    recommended_care: RecommendedCare
    urgent_flags: List[UrgentFlag]
    disclaimer: str
    model_config = {
        "extra": "allow"  # Allow unknown keys from LLM output
    }

class DoctorResponseWrapped(BaseModel):
    response: DoctorResponse
