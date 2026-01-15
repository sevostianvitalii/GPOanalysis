from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from backend.app.models.gpo import SeverityLevel

class RuleCategory(str, Enum):
    """Categories for best practice rules."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STABILITY = "stability"
    OPERATION = "operation"

class BestPracticeRule(BaseModel):
    """
    Defines a best practice rule for GPO settings.
    """
    id: str = Field(..., description="Unique rule identifier (e.g., 'SEC-001')")
    name: str = Field(..., description="Short descriptive name")
    description: str = Field(..., description="Detailed explanation of the rule")
    category: RuleCategory = Field(default=RuleCategory.OPERATION)
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    
    # Matching criteria
    setting_name: Optional[str] = Field(None, description="Exact setting name to match")
    registry_path: Optional[str] = Field(None, description="Registry path to match")
    registry_value: Optional[str] = Field(None, description="Registry value name to match")
    
    # logic
    recommended_value: Any = Field(..., description="The recommended value")
    operator: str = Field(default="equals", description="Comparison operator: equals, not_equals, greater_than, less_than, contains")
    
    rationale: str = Field(default="", description="Why this recommendation exists")
    reference_url: Optional[str] = Field(None, description="Link to Microsoft docs or benchmarks")
