# =============================================================================
# Policy Exporter - Export recommended policy as deployable PowerShell GPO script
# =============================================================================

import io
import logging
from datetime import datetime
from typing import Optional

from backend.app.models.gpo import AnalysisResult, ImprovementSuggestion, ImprovementCategory

logger = logging.getLogger(__name__)


class PolicyExporter:
    """
    Generates deployable GPO policy scripts from analysis recommendations.
    
    Creates PowerShell scripts that can be used to apply best practice
    settings identified during analysis.
    """
    
    def __init__(self, result: AnalysisResult):
        self.result = result
    
    def export_recommended_policy(self) -> str:
        """
        Generate a PowerShell script containing all recommended policy changes.
        
        Returns:
            PowerShell script content as string
        """
        output = io.StringIO()
        
        # Script header
        output.write("# =============================================================================\n")
        output.write("# GPO Analysis Tool - Recommended Policy Script\n")
        output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("# =============================================================================\n")
        output.write("#\n")
        output.write("# This script contains recommended GPO settings based on best practices.\n")
        output.write("# Review each section carefully before applying to your environment.\n")
        output.write("#\n")
        output.write("# USAGE:\n")
        output.write("#   1. Review the settings below\n")
        output.write("#   2. Modify GPO_NAME to match your target GPO\n")
        output.write("#   3. Run in an elevated PowerShell session with RSAT installed\n")
        output.write("#\n")
        output.write("# =============================================================================\n\n")
        
        # Configuration section
        output.write("#Requires -Modules GroupPolicy\n\n")
        output.write("# Configuration - modify these values\n")
        output.write('$GPO_NAME = "YOUR-GPO-NAME"  # Replace with your target GPO name\n')
        output.write('$DOMAIN = $env:USERDNSDOMAIN  # Or specify manually\n\n')
        
        # Safety prompt
        output.write("# Safety check\n")
        output.write('$confirm = Read-Host "This script will modify GPO settings. Type YES to continue"\n')
        output.write('if ($confirm -ne "YES") {\n')
        output.write('    Write-Host "Aborted by user." -ForegroundColor Yellow\n')
        output.write("    exit\n")
        output.write("}\n\n")
        
        # Initialize counters
        output.write("# Initialize\n")
        output.write("$successCount = 0\n")
        output.write("$errorCount = 0\n")
        output.write('Write-Host "Applying recommended policy settings..." -ForegroundColor Cyan\n\n')
        
        # Get security and performance improvements
        security_improvements = [
            i for i in self.result.improvements 
            if i.category in [ImprovementCategory.SECURITY, ImprovementCategory.PERFORMANCE]
        ]
        
        if not security_improvements:
            output.write("# No security or performance improvements to apply.\n")
            output.write('Write-Host "No recommended settings found." -ForegroundColor Yellow\n')
        else:
            output.write(f"# {len(security_improvements)} recommended setting(s) to apply\n\n")
            
            for i, improvement in enumerate(security_improvements, 1):
                output.write(f"# -----------------------------------------------------------------------------\n")
                output.write(f"# [{i}] {improvement.title}\n")
                output.write(f"# Severity: {improvement.severity.value.upper()}\n")
                if improvement.reference_url:
                    output.write(f"# Reference: {improvement.reference_url}\n")
                output.write(f"# Description: {improvement.description[:100]}...\n" if len(improvement.description) > 100 else f"# Description: {improvement.description}\n")
                output.write(f"# -----------------------------------------------------------------------------\n")
                
                # Generate setting-specific commands
                self._write_setting_command(output, improvement)
                output.write("\n")
        
        # Summary section
        output.write("\n# =============================================================================\n")
        output.write("# Summary\n")
        output.write("# =============================================================================\n")
        output.write('Write-Host ""`n')
        output.write('Write-Host "Policy application complete." -ForegroundColor Green\n')
        output.write('Write-Host "Successfully applied: $successCount setting(s)"\n')
        output.write('Write-Host "Errors encountered: $errorCount"\n')
        output.write('Write-Host ""`n')
        output.write('Write-Host "IMPORTANT: Review the GPO in Group Policy Management Console to verify changes." -ForegroundColor Yellow\n')
        
        return output.getvalue()
    
    def _write_setting_command(self, output: io.StringIO, improvement: ImprovementSuggestion) -> None:
        """Write PowerShell command for a specific improvement."""
        
        # Extract setting info from title/description
        # Format varies, but we try to extract key info
        title_lower = improvement.title.lower()
        
        output.write("try {\n")
        
        # Check for known setting patterns
        if "password length" in title_lower:
            output.write('    # Setting: Minimum Password Length\n')
            output.write('    # This requires domain-level password policy changes\n')
            output.write('    Write-Host "  Setting minimum password length..." -NoNewline\n')
            output.write('    # Manual action required - use Active Directory Administrative Center\n')
            output.write('    # or Set-ADDefaultDomainPasswordPolicy cmdlet\n')
            output.write('    Write-Host " [MANUAL ACTION REQUIRED]" -ForegroundColor Yellow\n')
            
        elif "lockout" in title_lower:
            output.write('    # Setting: Account Lockout Policy\n')
            output.write('    Write-Host "  Configuring account lockout policy..." -NoNewline\n')
            output.write('    # Manual action required - use Active Directory Administrative Center\n')
            output.write('    Write-Host " [MANUAL ACTION REQUIRED]" -ForegroundColor Yellow\n')
            
        elif "password age" in title_lower:
            output.write('    # Setting: Maximum Password Age\n')
            output.write('    Write-Host "  Setting maximum password age..." -NoNewline\n')
            output.write('    # Manual action required - domain password policy\n')
            output.write('    Write-Host " [MANUAL ACTION REQUIRED]" -ForegroundColor Yellow\n')
            
        elif "admin" in title_lower and "account" in title_lower:
            output.write('    # Setting: Administrator Account Status\n')
            output.write('    Write-Host "  Configuring administrator account..." -NoNewline\n')
            output.write('    # Set via: Computer Configuration > Windows Settings > Security Settings > Local Policies > Security Options\n')
            output.write('    Set-GPRegistryValue -Name $GPO_NAME -Key "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" `\n')
            output.write('        -ValueName "EnableLUA" -Type DWord -Value 1 -ErrorAction Stop\n')
            output.write('    Write-Host " [OK]" -ForegroundColor Green\n')
            output.write('    $successCount++\n')
            
        else:
            # Generic handler for unknown settings
            output.write(f'    # Setting: {improvement.title}\n')
            output.write(f'    Write-Host "  Applying: {improvement.title[:50]}..." -NoNewline\n')
            output.write('    # This setting requires manual configuration\n')
            output.write(f'    # Action: {improvement.action[:80]}...\n' if len(improvement.action) > 80 else f'    # Action: {improvement.action}\n')
            output.write('    Write-Host " [MANUAL ACTION REQUIRED]" -ForegroundColor Yellow\n')
        
        output.write("}\n")
        output.write("catch {\n")
        output.write(f'    Write-Host " [ERROR]" -ForegroundColor Red\n')
        output.write('    Write-Host "    $_" -ForegroundColor Red\n')
        output.write('    $errorCount++\n')
        output.write("}\n")


def export_recommended_policy(result: AnalysisResult) -> str:
    """
    Convenience function for exporting recommended policy.
    
    Args:
        result: Analysis result to export
        
    Returns:
        PowerShell script content
    """
    exporter = PolicyExporter(result)
    return exporter.export_recommended_policy()
