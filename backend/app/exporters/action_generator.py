import logging
from backend.app.models.gpo import ImprovementSuggestion, GPOInfo

logger = logging.getLogger(__name__)

class ActionGenerator:
    """Generates deployable artifacts (scripts) from suggestions."""
    
    @staticmethod
    def generate_fix_script(suggestion: ImprovementSuggestion) -> str:
        """Generate a PowerShell script to apply the suggested fix."""
        
        script = [
            "# =============================================================================",
            f"# GPO Analysis Tool - Fix Script",
            f"# Suggestion: {suggestion.title}",
            f"# Severity: {suggestion.severity.value.upper()}",
            "# =============================================================================",
            "",
            "Import-Module GroupPolicy",
            "",
            f"Write-Host 'Applying fix for: {suggestion.title}'",
            ""
        ]
        
        # Determine strictness of script based on category
        # For now, we generate generic instructions or placeholder commands
        # because mapping every setting to a precise Registry/GPO cmd is complex.
        
        if suggestion.affected_gpos:
            for gpo_name in suggestion.affected_gpos:
                script.append(f"# Target GPO: {gpo_name}")
                script.append(f"# Manual Action Required: {suggestion.action}")
                
                # If we had precise registry mapping in the rule, we could generate:
                # Set-GPRegistryValue -Name "{gpo_name}" -Key "HKLM\..." -ValueName "..." -Type ... -Value ...
                
                script.append(f"Write-Warning 'Automatic remediation not yet fully implemented for this setting type.'")
                script.append(f"Write-Host 'Please open GPO: {gpo_name} and perform: {suggestion.action}'")
                script.append("")
        
        return "\n".join(script)

    @staticmethod
    def generate_consolidation_script(new_gpo_name: str, source_gpos: list[str]) -> str:
        """Generate script to consolidate multiple GPOs into one."""
        
        script = [
            "# =============================================================================",
            f"# GPO Analysis Tool - Consolidation Script",
            f"# Target GPO: {new_gpo_name}",
            f"# Source GPOs: {', '.join(source_gpos)}",
            "# =============================================================================",
            "",
            "Import-Module GroupPolicy",
            "",
            f"$TargetGPO = '{new_gpo_name}'",
            f"$SourceGPOs = @({', '.join([repr(s) for s in source_gpos])})",
            "",
            "# 1. Create new GPO",
            "Write-Host \"Creating new GPO: $TargetGPO\"",
            "New-GPO -Name $TargetGPO -Comment \"Consolidated by GPO Analysis Tool\"",
            "",
            "# 2. Copy settings (Conceptual - requires backup/import)",
            "foreach ($Source in $SourceGPOs) {",
            "    Write-Host \"Migrating settings from $Source to $TargetGPO...\"",
            "    # Note: True setting migration requires Backup-GPO + Import-GPO",
            "    # This script is a template for the admin.",
            "    Write-Host \"[ACTION REQUIRED] Please manually copy settings or use GPO backups to import into $TargetGPO\"",
            "}",
            "",
            "Write-Host \"Consolidation structure created. Please verify settings before linking.\""
        ]
        
        return "\n".join(script)
