# =============================================================================
# GPO Improvement Engine - Suggests best practices and optimizations
# =============================================================================

import uuid
import re
import logging
from collections import defaultdict

from backend.app.models.gpo import (
    GPOInfo, PolicySetting, ImprovementSuggestion, ImprovementCategory, 
    SeverityLevel, PolicyState
)

logger = logging.getLogger(__name__)


class ImprovementEngine:
    """
    Analyzes GPOs and suggests improvements based on best practices.
    
    Suggestion categories:
    - Consolidation: Merge related GPOs
    - Security: Apply security hardening
    - Performance: Optimize GPO processing
    - Naming: Follow naming conventions
    - Organization: Better OU structure
    - Cleanup: Remove unused settings/GPOs
    """
    
    def __init__(self, gpos: list[GPOInfo], settings: list[PolicySetting]):
        self.gpos = gpos
        self.settings = settings
        self.settings_by_gpo: dict[str, list[PolicySetting]] = defaultdict(list)
        self._index_settings()
    
    def _index_settings(self) -> None:
        """Index settings by GPO."""
        for setting in self.settings:
            self.settings_by_gpo[setting.gpo_id].append(setting)
    
    def generate_suggestions(self) -> list[ImprovementSuggestion]:
        """Generate all improvement suggestions."""
        suggestions = []
        
        suggestions.extend(self._check_naming_conventions())
        suggestions.extend(self._check_empty_or_small_gpos())
        suggestions.extend(self._check_unused_sections())
        suggestions.extend(self._check_consolidation_opportunities())
        suggestions.extend(self._check_security_recommendations())
        
        logger.info(f"Improvement engine complete: {len(suggestions)} suggestion(s) generated")
        return suggestions
    
    def _check_naming_conventions(self) -> list[ImprovementSuggestion]:
        """Check GPO naming conventions."""
        suggestions = []
        
        # Patterns for good naming
        good_patterns = [
            r'^[A-Z]{2,4}[-_]',  # Prefix like "SEC-", "APP_"
            r'[-_](Computer|User)s?[-_]',  # Scope indicator
            r'[-_](Policy|Settings?)$',  # Suffix
        ]
        
        for gpo in self.gpos:
            issues = []
            name = gpo.name
            
            # Check for generic names
            generic_names = ['new group policy object', 'gpo', 'test', 'policy', 'temp']
            if name.lower() in generic_names:
                issues.append("Uses a generic/default name")
            
            # Check length
            if len(name) < 5:
                issues.append("Name is too short to be descriptive")
            elif len(name) > 64:
                issues.append("Name is excessively long")
            
            # Check for spaces (some orgs prefer underscores/dashes)
            # Not adding as an issue since spaces are valid
            
            # Check if no good patterns match
            if not any(re.search(p, name) for p in good_patterns):
                issues.append("Doesn't follow common naming conventions (prefix-scope-purpose)")
            
            if issues:
                suggestions.append(ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    category=ImprovementCategory.NAMING,
                    severity=SeverityLevel.LOW,
                    title=f"Improve naming for '{gpo.name}'",
                    description=f"Issues found: {'; '.join(issues)}",
                    affected_gpos=[gpo.name],
                    action=(
                        "Rename the GPO to follow a consistent naming convention. "
                        "Recommended format: 'PREFIX-SCOPE-Purpose' "
                        "(e.g., 'SEC-Computer-BitLocker' or 'APP-User-Office365')"
                    ),
                    estimated_impact="Improved manageability and easier troubleshooting"
                ))
        
        return suggestions
    
    def _check_empty_or_small_gpos(self) -> list[ImprovementSuggestion]:
        """Check for empty or very small GPOs."""
        suggestions = []
        
        for gpo in self.gpos:
            settings = self.settings_by_gpo.get(gpo.id, [])
            configured_settings = [s for s in settings if s.state != PolicyState.NOT_CONFIGURED]
            
            if len(configured_settings) == 0:
                suggestions.append(ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    category=ImprovementCategory.CLEANUP,
                    severity=SeverityLevel.MEDIUM,
                    title=f"Empty GPO: '{gpo.name}'",
                    description="This GPO has no configured settings.",
                    affected_gpos=[gpo.name],
                    action="Delete this GPO if it's not needed, or add settings if it was created for future use.",
                    estimated_impact="Reduced GPO processing overhead and cleaner management"
                ))
            elif len(configured_settings) <= 2:
                suggestions.append(ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    category=ImprovementCategory.CONSOLIDATION,
                    severity=SeverityLevel.LOW,
                    title=f"Consider consolidating '{gpo.name}'",
                    description=f"This GPO only has {len(configured_settings)} configured setting(s).",
                    affected_gpos=[gpo.name],
                    action="Consider merging these settings into a related GPO to reduce the total number of GPOs.",
                    estimated_impact="Simpler GPO structure and faster policy processing"
                ))
        
        return suggestions
    
    def _check_unused_sections(self) -> list[ImprovementSuggestion]:
        """Check for GPOs with unused Computer or User configuration sections."""
        suggestions = []
        
        for gpo in self.gpos:
            settings = self.settings_by_gpo.get(gpo.id, [])
            
            computer_settings = [s for s in settings if s.scope == "Computer" and s.state != PolicyState.NOT_CONFIGURED]
            user_settings = [s for s in settings if s.scope == "User" and s.state != PolicyState.NOT_CONFIGURED]
            
            # Only suggest if there are some settings but one section is completely empty
            if settings and (computer_settings or user_settings):
                if not computer_settings and user_settings and gpo.computer_enabled:
                    suggestions.append(ImprovementSuggestion(
                        id=str(uuid.uuid4()),
                        category=ImprovementCategory.PERFORMANCE,
                        severity=SeverityLevel.LOW,
                        title=f"Disable unused Computer Configuration in '{gpo.name}'",
                        description="This GPO only has User Configuration settings but Computer Configuration is enabled.",
                        affected_gpos=[gpo.name],
                        action="Disable the Computer Configuration section to speed up computer startup.",
                        estimated_impact="Faster computer startup (GPO processing is skipped for this section)"
                    ))
                elif not user_settings and computer_settings and gpo.user_enabled:
                    suggestions.append(ImprovementSuggestion(
                        id=str(uuid.uuid4()),
                        category=ImprovementCategory.PERFORMANCE,
                        severity=SeverityLevel.LOW,
                        title=f"Disable unused User Configuration in '{gpo.name}'",
                        description="This GPO only has Computer Configuration settings but User Configuration is enabled.",
                        affected_gpos=[gpo.name],
                        action="Disable the User Configuration section to speed up user logon.",
                        estimated_impact="Faster user logon (GPO processing is skipped for this section)"
                    ))
        
        return suggestions
    
    def _check_consolidation_opportunities(self) -> list[ImprovementSuggestion]:
        """Check for GPOs that could be consolidated."""
        suggestions = []
        
        # Group GPOs by similar naming patterns
        gpo_groups = defaultdict(list)
        
        for gpo in self.gpos:
            # Extract common prefix (first word or before first separator)
            name_parts = re.split(r'[-_\s]', gpo.name)
            if name_parts:
                prefix = name_parts[0].upper()
                gpo_groups[prefix].append(gpo)
        
        # Find groups with multiple small GPOs
        for prefix, group_gpos in gpo_groups.items():
            if len(group_gpos) >= 3:
                total_settings = sum(
                    len([s for s in self.settings_by_gpo.get(g.id, []) 
                         if s.state != PolicyState.NOT_CONFIGURED])
                    for g in group_gpos
                )
                
                # If many GPOs with few settings total
                if total_settings < len(group_gpos) * 10:  # Average <10 settings per GPO
                    suggestions.append(ImprovementSuggestion(
                        id=str(uuid.uuid4()),
                        category=ImprovementCategory.CONSOLIDATION,
                        severity=SeverityLevel.MEDIUM,
                        title=f"Consolidate '{prefix}' GPO group",
                        description=(
                            f"Found {len(group_gpos)} GPOs with similar naming prefix '{prefix}' "
                            f"containing a total of {total_settings} settings."
                        ),
                        affected_gpos=[g.name for g in group_gpos],
                        action=(
                            f"Consider consolidating these {len(group_gpos)} GPOs into fewer, "
                            f"more comprehensive policies to simplify management."
                        ),
                        estimated_impact="Reduced complexity, faster troubleshooting, fewer GPOs to manage"
                    ))
        
        return suggestions
    
    def _check_security_recommendations(self) -> list[ImprovementSuggestion]:
        """Check for security best practice recommendations."""
        suggestions = []
        
        # Collect all security-related settings
        security_keywords = [
            'password', 'lockout', 'audit', 'encryption', 'firewall',
            'bitlocker', 'defender', 'uac', 'credential', 'trust'
        ]
        
        security_settings = []
        for setting in self.settings:
            name_lower = setting.name.lower()
            category_lower = setting.category.lower()
            
            if any(kw in name_lower or kw in category_lower for kw in security_keywords):
                security_settings.append(setting)
        
        # Check if security settings are scattered across many GPOs
        security_gpos = set(s.gpo_id for s in security_settings)
        
        if len(security_gpos) > 3 and len(security_settings) > 5:
            gpo_names = list(set(s.gpo_name for s in security_settings))
            suggestions.append(ImprovementSuggestion(
                id=str(uuid.uuid4()),
                category=ImprovementCategory.SECURITY,
                severity=SeverityLevel.MEDIUM,
                title="Consolidate security settings",
                description=(
                    f"Security-related settings are spread across {len(security_gpos)} GPOs. "
                    f"This can make security auditing and compliance checks more difficult."
                ),
                affected_gpos=gpo_names,
                action=(
                    "Consider creating dedicated security GPOs (e.g., 'SEC-Baseline-Computer', "
                    "'SEC-Baseline-User') to centralize security settings for easier auditing."
                ),
                estimated_impact="Easier security audits, better compliance tracking, clearer security posture"
            ))
        
        return suggestions


def generate_improvements(gpos: list[GPOInfo], settings: list[PolicySetting]) -> list[ImprovementSuggestion]:
    """Convenience function for generating improvements."""
    engine = ImprovementEngine(gpos, settings)
    return engine.generate_suggestions()
