# =============================================================================
# GPO Analysis Tool - Pydantic Models
# =============================================================================

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Severity levels for conflicts and recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PolicyState(str, Enum):
    """Policy configuration state."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


class GPOLink(BaseModel):
    """Represents a GPO link to an OU/Site/Domain."""
    location: str = Field(..., description="Distinguished Name of linked container")
    enabled: bool = Field(default=True)
    enforced: bool = Field(default=False)
    order: int = Field(default=0, description="Link order (lower = higher priority)")


class GPOInfo(BaseModel):
    """Basic GPO metadata extracted from reports."""
    id: str = Field(..., description="Unique identifier (usually GUID)")
    name: str = Field(..., description="Display name of the GPO")
    domain: Optional[str] = Field(default=None)
    created: Optional[datetime] = Field(default=None)
    modified: Optional[datetime] = Field(default=None)
    owner: Optional[str] = Field(default=None)
    links: list[GPOLink] = Field(default_factory=list)
    computer_enabled: bool = Field(default=True)
    user_enabled: bool = Field(default=True)
    source_file: str = Field(..., description="Original source file path")


class PolicySetting(BaseModel):
    """Individual policy setting within a GPO."""
    gpo_id: str = Field(..., description="Parent GPO identifier")
    gpo_name: str = Field(..., description="Parent GPO name")
    category: str = Field(..., description="Policy category path")
    name: str = Field(..., description="Policy setting name")
    state: PolicyState = Field(default=PolicyState.NOT_CONFIGURED)
    value: Optional[str] = Field(default=None, description="Configured value if applicable")
    registry_path: Optional[str] = Field(default=None, description="Associated registry key")
    registry_value: Optional[str] = Field(default=None, description="Registry value name")
    scope: str = Field(default="Computer", description="Computer or User configuration")


class ConflictReport(BaseModel):
    """Report of conflicting settings between GPOs."""
    id: str = Field(..., description="Unique conflict identifier")
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    setting_name: str = Field(..., description="Name of the conflicting setting")
    category: str = Field(..., description="Policy category")
    registry_path: Optional[str] = Field(default=None)
    
    conflicting_policies: list[PolicySetting] = Field(
        ..., description="List of policies with conflicting values"
    )
    
    winning_gpo: Optional[str] = Field(
        default=None, 
        description="GPO that would win based on precedence"
    )
    
    description: str = Field(
        default="", 
        description="Human-readable explanation of the conflict"
    )
    
    recommendation: str = Field(
        default="", 
        description="Suggested resolution"
    )


class DuplicateReport(BaseModel):
    """Report of duplicate/redundant policies."""
    id: str = Field(..., description="Unique duplicate identifier")
    severity: SeverityLevel = Field(default=SeverityLevel.LOW)
    setting_name: str = Field(..., description="Name of the duplicated setting")
    category: str = Field(..., description="Policy category")
    
    affected_gpos: list[str] = Field(
        ..., description="List of GPO names with identical settings"
    )
    
    duplicate_settings: list[PolicySetting] = Field(
        ..., description="The duplicate policy settings"
    )
    
    description: str = Field(default="")
    recommendation: str = Field(default="")


class ImprovementCategory(str, Enum):
    """Categories for improvement suggestions."""
    CONSOLIDATION = "consolidation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NAMING = "naming"
    ORGANIZATION = "organization"
    CLEANUP = "cleanup"


class ImprovementSuggestion(BaseModel):
    """Recommendation for GPO improvement."""
    id: str = Field(..., description="Unique suggestion identifier")
    category: ImprovementCategory
    severity: SeverityLevel = Field(default=SeverityLevel.INFO)
    title: str = Field(..., description="Short title of the suggestion")
    description: str = Field(..., description="Detailed explanation")
    affected_gpos: list[str] = Field(default_factory=list)
    action: str = Field(..., description="Recommended action to take")
    estimated_impact: str = Field(default="", description="Expected benefit from implementing")


class AnalysisResult(BaseModel):
    """Complete analysis result for a set of GPOs."""
    analyzed_at: datetime = Field(default_factory=datetime.now)
    gpo_count: int = Field(default=0)
    setting_count: int = Field(default=0)
    
    gpos: list[GPOInfo] = Field(default_factory=list)
    settings: list[PolicySetting] = Field(default_factory=list)
    conflicts: list[ConflictReport] = Field(default_factory=list)
    duplicates: list[DuplicateReport] = Field(default_factory=list)
    improvements: list[ImprovementSuggestion] = Field(default_factory=list)
    
    # Summary statistics
    conflict_count: int = Field(default=0)
    duplicate_count: int = Field(default=0)
    improvement_count: int = Field(default=0)
    
    critical_issues: int = Field(default=0)
    high_issues: int = Field(default=0)
    medium_issues: int = Field(default=0)
    low_issues: int = Field(default=0)


class UploadResponse(BaseModel):
    """Response after uploading GPO files."""
    success: bool
    message: str
    files_processed: int = Field(default=0)
    gpos_found: int = Field(default=0)
    errors: list[str] = Field(default_factory=list)


class ExportFormat(str, Enum):
    """Available export formats."""
    CSV = "csv"
    PDF = "pdf"
