# =============================================================================
# GPO Duplicate Detector - Identifies duplicate and redundant policies
# =============================================================================

import uuid
import logging
from collections import defaultdict

from backend.app.models.gpo import (
    GPOInfo, PolicySetting, DuplicateReport, SeverityLevel, PolicyState
)

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detects duplicate and redundant policy settings across GPOs.
    
    Types of duplicates detected:
    1. Identical settings: Same policy with same value in multiple GPOs
    2. Redundant GPOs: GPO that is a complete subset of another GPO
    """
    
    def __init__(self, gpos: list[GPOInfo], settings: list[PolicySetting]):
        self.gpos = {gpo.id: gpo for gpo in gpos}
        self.settings = settings
        self.settings_by_gpo: dict[str, list[PolicySetting]] = defaultdict(list)
        self._index_settings()
    
    def _index_settings(self) -> None:
        """Index settings by GPO for quick lookup."""
        for setting in self.settings:
            self.settings_by_gpo[setting.gpo_id].append(setting)
    
    def detect_duplicates(self) -> list[DuplicateReport]:
        """Run duplicate detection and return list of duplicates."""
        duplicates = []
        
        # Detect identical settings across GPOs
        duplicates.extend(self._detect_identical_settings())
        
        # Detect redundant GPOs (subset of another)
        duplicates.extend(self._detect_redundant_gpos())
        
        logger.info(f"Duplicate detection complete: {len(duplicates)} duplicate(s) found")
        return duplicates
    
    def _detect_identical_settings(self) -> list[DuplicateReport]:
        """Find identical policy settings across different GPOs."""
        duplicates = []
        
        # Group settings by their signature (category + name + state + value)
        setting_signatures = defaultdict(list)
        
        for setting in self.settings:
            if setting.state == PolicyState.NOT_CONFIGURED:
                continue
            
            # Create a signature for this setting
            signature = (
                setting.scope,
                setting.category,
                setting.name,
                setting.state,
                setting.value or ""
            )
            setting_signatures[signature].append(setting)
        
        # Find signatures that appear in multiple GPOs
        for signature, settings in setting_signatures.items():
            unique_gpos = set(s.gpo_id for s in settings)
            
            if len(unique_gpos) < 2:
                continue
            
            # This is a duplicate
            duplicate = DuplicateReport(
                id=str(uuid.uuid4()),
                severity=SeverityLevel.LOW,
                setting_name=settings[0].name,
                category=settings[0].category,
                affected_gpos=[s.gpo_name for s in settings],
                duplicate_settings=settings,
                description=self._generate_description(settings),
                recommendation=self._generate_recommendation(settings)
            )
            duplicates.append(duplicate)
        
        return duplicates
    
    def _detect_redundant_gpos(self) -> list[DuplicateReport]:
        """Find GPOs that are complete subsets of other GPOs."""
        duplicates = []
        
        # Build setting sets for each GPO
        gpo_setting_sets: dict[str, set] = {}
        
        for gpo_id, settings in self.settings_by_gpo.items():
            setting_set = set()
            for s in settings:
                if s.state != PolicyState.NOT_CONFIGURED:
                    sig = (s.scope, s.category, s.name, s.state, s.value or "")
                    setting_set.add(sig)
            gpo_setting_sets[gpo_id] = setting_set
        
        # Check for subset relationships
        checked_pairs = set()
        
        for gpo_id_a, set_a in gpo_setting_sets.items():
            if not set_a:  # Skip empty GPOs
                continue
                
            for gpo_id_b, set_b in gpo_setting_sets.items():
                if gpo_id_a == gpo_id_b:
                    continue
                
                pair = tuple(sorted([gpo_id_a, gpo_id_b]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                if not set_b:
                    continue
                
                # Check if A is subset of B
                if set_a < set_b:  # Proper subset
                    gpo_a = self.gpos[gpo_id_a]
                    gpo_b = self.gpos[gpo_id_b]
                    
                    duplicate = DuplicateReport(
                        id=str(uuid.uuid4()),
                        severity=SeverityLevel.MEDIUM,
                        setting_name=f"[All settings in {gpo_a.name}]",
                        category="GPO Redundancy",
                        affected_gpos=[gpo_a.name, gpo_b.name],
                        duplicate_settings=[],
                        description=(
                            f"GPO '{gpo_a.name}' is redundant - all its {len(set_a)} settings "
                            f"are already defined in '{gpo_b.name}' (which has {len(set_b)} settings)."
                        ),
                        recommendation=(
                            f"Consider removing GPO '{gpo_a.name}' as all its settings are already "
                            f"covered by '{gpo_b.name}'. Verify that link locations are compatible "
                            f"before removal."
                        )
                    )
                    duplicates.append(duplicate)
        
        return duplicates
    
    def _generate_description(self, settings: list[PolicySetting]) -> str:
        """Generate human-readable duplicate description."""
        gpo_names = list(set(s.gpo_name for s in settings))
        setting_name = settings[0].name
        value_str = f" (value: {settings[0].value})" if settings[0].value else ""
        
        return (
            f"Policy '{setting_name}'{value_str} is configured identically in "
            f"{len(gpo_names)} GPOs: {', '.join(gpo_names)}"
        )
    
    def _generate_recommendation(self, settings: list[PolicySetting]) -> str:
        """Generate recommendation for resolving the duplicate."""
        gpo_names = list(set(s.gpo_name for s in settings))
        
        if len(gpo_names) == 2:
            return (
                f"This setting is duplicated. Consider removing it from one of the GPOs "
                f"or consolidating '{gpo_names[0]}' and '{gpo_names[1]}' into a single GPO."
            )
        else:
            return (
                f"This setting is defined in {len(gpo_names)} GPOs. Consider consolidating "
                f"these policies into fewer GPOs to simplify management."
            )


def detect_duplicates(gpos: list[GPOInfo], settings: list[PolicySetting]) -> list[DuplicateReport]:
    """Convenience function for duplicate detection."""
    detector = DuplicateDetector(gpos, settings)
    return detector.detect_duplicates()
