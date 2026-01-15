# =============================================================================
# CSV Exporter - Export GPO analysis results to CSV format
# =============================================================================

import csv
import io
import logging
from datetime import datetime

from backend.app.models.gpo import AnalysisResult

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export analysis results to CSV format."""
    
    def __init__(self, result: AnalysisResult):
        self.result = result
    
    def export_all(self) -> dict[str, str]:
        """
        Export all analysis data to multiple CSV files.
        
        Returns:
            Dictionary mapping filename to CSV content
        """
        return {
            "gpos.csv": self._export_gpos(),
            "settings.csv": self._export_settings(),
            "conflicts.csv": self._export_conflicts(),
            "duplicates.csv": self._export_duplicates(),
            "improvements.csv": self._export_improvements(),
            "summary.csv": self._export_summary(),
        }
    
    def export_summary(self) -> str:
        """Export only summary information."""
        return self._export_summary()
    
    def export_conflicts(self) -> str:
        """Export only conflicts."""
        return self._export_conflicts()
    
    def export_all_combined(self) -> str:
        """Export all data in a single CSV with section headers."""
        output = io.StringIO()
        
        # Summary section
        output.write("=== GPO ANALYSIS SUMMARY ===\n")
        output.write(self._export_summary())
        output.write("\n")
        
        # GPOs section
        output.write("=== GROUP POLICY OBJECTS ===\n")
        output.write(self._export_gpos())
        output.write("\n")
        
        # Conflicts section
        output.write("=== CONFLICTS ===\n")
        output.write(self._export_conflicts())
        output.write("\n")
        
        # Duplicates section
        output.write("=== DUPLICATES ===\n")
        output.write(self._export_duplicates())
        output.write("\n")
        
        # Improvements section
        output.write("=== IMPROVEMENT SUGGESTIONS ===\n")
        output.write(self._export_improvements())
        
        return output.getvalue()
    
    def _export_gpos(self) -> str:
        """Export GPO list to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "GPO Name", "ID", "Domain", "Created", "Modified", 
            "Owner", "Computer Enabled", "User Enabled", "Source File"
        ])
        
        # Data
        for gpo in self.result.gpos:
            writer.writerow([
                gpo.name,
                gpo.id,
                gpo.domain or "",
                gpo.created.isoformat() if gpo.created else "",
                gpo.modified.isoformat() if gpo.modified else "",
                gpo.owner or "",
                "Yes" if gpo.computer_enabled else "No",
                "Yes" if gpo.user_enabled else "No",
                gpo.source_file
            ])
        
        return output.getvalue()
    
    def _export_settings(self) -> str:
        """Export all settings to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "GPO Name", "Scope", "Category", "Setting Name", 
            "State", "Value", "Registry Path", "Registry Value"
        ])
        
        # Data
        for setting in self.result.settings:
            writer.writerow([
                setting.gpo_name,
                setting.scope,
                setting.category,
                setting.name,
                setting.state.value,
                setting.value or "",
                setting.registry_path or "",
                setting.registry_value or ""
            ])
        
        return output.getvalue()
    
    def _export_conflicts(self) -> str:
        """Export conflicts to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Severity", "Setting Name", "Category", "Registry Path",
            "Conflicting GPOs", "Winning GPO", "Description", "Recommendation"
        ])
        
        # Data
        for conflict in self.result.conflicts:
            gpo_list = ", ".join(set(p.gpo_name for p in conflict.conflicting_policies))
            writer.writerow([
                conflict.severity.value.upper(),
                conflict.setting_name,
                conflict.category,
                conflict.registry_path or "",
                gpo_list,
                conflict.winning_gpo or "",
                conflict.description,
                conflict.recommendation
            ])
        
        return output.getvalue()
    
    def _export_duplicates(self) -> str:
        """Export duplicates to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Severity", "Setting Name", "Category", 
            "Affected GPOs", "Description", "Recommendation"
        ])
        
        # Data
        for duplicate in self.result.duplicates:
            writer.writerow([
                duplicate.severity.value.upper(),
                duplicate.setting_name,
                duplicate.category,
                ", ".join(duplicate.affected_gpos),
                duplicate.description,
                duplicate.recommendation
            ])
        
        return output.getvalue()
    
    def _export_improvements(self) -> str:
        """Export improvement suggestions to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Severity", "Category", "Title", 
            "Affected GPOs", "Description", "Action", "Estimated Impact"
        ])
        
        # Data
        for improvement in self.result.improvements:
            writer.writerow([
                improvement.severity.value.upper(),
                improvement.category.value,
                improvement.title,
                ", ".join(improvement.affected_gpos),
                improvement.description,
                improvement.action,
                improvement.estimated_impact
            ])
        
        return output.getvalue()
    
    def _export_summary(self) -> str:
        """Export summary statistics to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Analysis Date", self.result.analyzed_at.isoformat()])
        writer.writerow(["Total GPOs", self.result.gpo_count])
        writer.writerow(["Total Settings", self.result.setting_count])
        writer.writerow(["Conflicts Found", self.result.conflict_count])
        writer.writerow(["Duplicates Found", self.result.duplicate_count])
        writer.writerow(["Improvement Suggestions", self.result.improvement_count])
        writer.writerow(["Critical Issues", self.result.critical_issues])
        writer.writerow(["High Priority Issues", self.result.high_issues])
        writer.writerow(["Medium Priority Issues", self.result.medium_issues])
        writer.writerow(["Low Priority Issues", self.result.low_issues])
        
        return output.getvalue()


def export_to_csv(result: AnalysisResult, combined: bool = True) -> str | dict[str, str]:
    """
    Convenience function for CSV export.
    
    Args:
        result: Analysis result to export
        combined: If True, return single combined CSV; otherwise return dict of CSVs
    """
    exporter = CSVExporter(result)
    if combined:
        return exporter.export_all_combined()
    return exporter.export_all()
