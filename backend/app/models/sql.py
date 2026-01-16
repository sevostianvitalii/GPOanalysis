# =============================================================================
# GPO Analysis Tool - SQL Models
# =============================================================================

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON
from pydantic import BaseModel

class GPOLink(BaseModel):
    """Represents a GPO link to an OU/Site/Domain. Stored as JSON."""
    location: str
    enabled: bool = True
    enforced: bool = False
    order: int = 0

class StoredGPO(SQLModel, table=True):
    """Database model for a Group Policy Object."""
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    domain: Optional[str] = Field(default=None, index=True)
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    owner: Optional[str] = None
    computer_enabled: bool = True
    user_enabled: bool = True
    source_file: str
    
    # Store links as JSON since it's a list of somewhat complex objects
    # and we don't strictly need to query *inside* the link structure purely by SQL often yet
    links_data: List[dict] = Field(default=[], sa_type=JSON)

    # Relationships
    settings: List["StoredSetting"] = Relationship(back_populates="gpo", sa_relationship_kwargs={"cascade": "all, delete"})

    @property
    def links(self) -> List[GPOLink]:
        """Deserialize links_data to Pydantic models."""
        return [GPOLink(**link) for link in self.links_data]

    @links.setter
    def links(self, value: List[GPOLink]):
        """Serialize Pydantic models to dicts for storage."""
        self.links_data = [link.model_dump() for link in value]


class StoredSetting(SQLModel, table=True):
    """Database model for a Policy Setting."""
    id: Optional[int] = Field(default=None, primary_key=True)
    gpo_id: str = Field(foreign_key="storedgpo.id", index=True)
    
    # Metadata
    gpo_name: str # Redundant but useful for fast display without join
    category: str = Field(index=True)
    name: str = Field(index=True)
    
    # State
    state: str # Enabled, Disabled, Not Configured
    value: Optional[str] = None
    registry_path: Optional[str] = None
    registry_value: Optional[str] = None
    scope: str = Field(index=True) # Computer or User

    # Relationships
    gpo: StoredGPO = Relationship(back_populates="settings")
