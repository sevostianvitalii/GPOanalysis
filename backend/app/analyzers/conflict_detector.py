# =============================================================================
# GPO Conflict Detector - Identifies conflicting policy settings
# =============================================================================

import uuid
import logging
from collections import defaultdict
from typing import Optional

from backend.app.models.gpo import (
    GPOInfo, PolicySetting, ConflictReport, SeverityLevel, PolicyState
)

logger = logging.getLogger(__name__)


class ConflictDetector:
    """
    Detects conflicts between GPO settings.
    
    Types of conflicts detected:
    1. Same registry path with different values across GPOs
    2. Contradicting Enable/Disable on same policy
    3. Overlapping security settings with different configurations
    """
    
    def __init__(self, gpos: list[GPOInfo], settings: list[PolicySetting]):
        self.gpos = {gpo.id: gpo for gpo in gpos}
        self.settings = settings
        self.gpo_precedence: dict[str, int] = {}
        self._build_precedence_map()
    
    def _build_precedence_map(self) -> None:
        """Build GPO precedence based on modification date (newer = higher priority as fallback)."""
        sorted_gpos = sorted(
            self.gpos.values(), 
            key=lambda g: g.modified or g.created or 0, 
            reverse=True
        )
        for i, gpo in enumerate(sorted_gpos):
            self.gpo_precedence[gpo.id] = i
    
    def detect_conflicts(self) -> list[ConflictReport]:
        """Run conflict detection and return list of conflicts."""
        conflicts = []
        
        # Group settings by their identifier (registry path or category+name)
        setting_groups = self._group_settings()
        
        for key, group_settings in setting_groups.items():
            if len(group_settings) < 2:
                continue
            
            # Check for value conflicts
            conflict = self._check_group_conflict(key, group_settings)
            if conflict:
                conflicts.append(conflict)
        
        logger.info(f"Conflict detection complete: {len(conflicts)} conflict(s) found")
        return conflicts
    
    def _group_settings(self) -> dict[str, list[PolicySetting]]:
        """Group settings by their unique identifier."""
        groups = defaultdict(list)
        
        for setting in self.settings:
            # Only consider configured settings
            if setting.state == PolicyState.NOT_CONFIGURED:
                continue
            
            # Create unique key for the setting
            if setting.registry_path and setting.registry_value:
                key = f"REG:{setting.registry_path}\\{setting.registry_value}"
            else:
                # Use category + name as key
                key = f"{setting.scope}:{setting.category}:{setting.name}"
            
            groups[key].append(setting)
        
        return groups
    
    def _check_group_conflict(self, key: str, settings: list[PolicySetting]) -> Optional[ConflictReport]:
        """Check if a group of settings has conflicts."""
        # Get unique values/states
        unique_configs = set()
        for s in settings:
            config = (s.state, s.value)
            unique_configs.add(config)
        
        # No conflict if all settings have the same configuration
        if len(unique_configs) == 1:
            return None
        
        # Determine severity based on conflict type
        severity = self._determine_severity(settings)
        
        # Find winning GPO based on precedence
        winning_setting = min(settings, key=lambda s: self.gpo_precedence.get(s.gpo_id, 999))
        
        # Generate description and recommendation
        description = self._generate_description(settings)
        recommendation = self._generate_recommendation(settings, winning_setting)
        
        return ConflictReport(
            id=str(uuid.uuid4()),
            severity=severity,
            setting_name=settings[0].name,
            category=settings[0].category,
            registry_path=settings[0].registry_path,
            conflicting_policies=settings,
            winning_gpo=winning_setting.gpo_name,
            description=description,
            recommendation=recommendation
        )
    
    def _determine_severity(self, settings: list[PolicySetting]) -> SeverityLevel:
        """Determine conflict severity based on setting characteristics."""
        category_lower = settings[0].category.lower()
        name_lower = settings[0].name.lower()
        
        # Security-related settings are higher severity
        security_keywords = [
            'security', 'password', 'authentication', 'audit', 'firewall',
            'encryption', 'account', 'logon', 'credential', 'bitlocker',
            'defender', 'antivirus', 'uac', 'admin'
        ]
        
        if any(kw in category_lower or kw in name_lower for kw in security_keywords):
            return SeverityLevel.HIGH
        
        # Check for Enable vs Disable conflicts (more severe than just value differences)
        states = {s.state for s in settings}
        if PolicyState.ENABLED in states and PolicyState.DISABLED in states:
            return SeverityLevel.HIGH
        
        # Network and system settings are medium severity
        system_keywords = ['network', 'system', 'service', 'driver', 'update', 'install']
        if any(kw in category_lower or kw in name_lower for kw in system_keywords):
            return SeverityLevel.MEDIUM
        
        return SeverityLevel.LOW
    
    def _generate_description(self, settings: list[PolicySetting]) -> str:
        """Generate human-readable conflict description."""
        gpo_names = list(set(s.gpo_name for s in settings))
        setting_name = settings[0].name
        
        # Describe the conflict
        config_descriptions = []
        for s in settings:
            state_str = s.state.value
            value_str = f" ({s.value})" if s.value else ""
            config_descriptions.append(f"'{s.gpo_name}' sets {state_str}{value_str}")
        
        return (
            f"Policy '{setting_name}' has conflicting configurations across "
            f"{len(gpo_names)} GPO(s): " + "; ".join(config_descriptions)
        )
    
    def _generate_recommendation(self, settings: list[PolicySetting], winning: PolicySetting) -> str:
        """Generate recommendation for resolving the conflict."""
        other_gpos = [s.gpo_name for s in settings if s.gpo_id != winning.gpo_id]
        
        return (
            f"The setting from '{winning.gpo_name}' will take effect. "
            f"Consider removing or reconfiguring this setting in: {', '.join(other_gpos)}. "
            f"Alternatively, consolidate these GPOs to avoid confusion."
        )


def detect_conflicts(gpos: list[GPOInfo], settings: list[PolicySetting]) -> list[ConflictReport]:
    """Convenience function for conflict detection."""
    detector = ConflictDetector(gpos, settings)
    return detector.detect_conflicts()
