# =============================================================================
# PDF Exporter - Export GPO analysis results to PDF format
# =============================================================================

import io
import logging
from datetime import datetime

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from backend.app.models.gpo import AnalysisResult, SeverityLevel

logger = logging.getLogger(__name__)


class PDFExporter:
    """Export analysis results to professional PDF report."""
    
    def __init__(self, result: AnalysisResult):
        self.result = result
        self.font_config = FontConfiguration()
    
    def export(self) -> bytes:
        """Generate PDF report and return as bytes."""
        html_content = self._generate_html()
        css_content = self._get_css()
        
        html = HTML(string=html_content)
        css = CSS(string=css_content, font_config=self.font_config)
        
        pdf_bytes = html.write_pdf(stylesheets=[css], font_config=self.font_config)
        
        logger.info("PDF report generated successfully")
        return pdf_bytes
    
    def _generate_html(self) -> str:
        """Generate HTML content for the PDF."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GPO Analysis Report</title>
</head>
<body>
    {self._render_cover_page()}
    {self._render_executive_summary()}
    {self._render_gpo_inventory()}
    {self._render_conflicts()}
    {self._render_duplicates()}
    {self._render_improvements()}
</body>
</html>
"""
    
    def _render_cover_page(self) -> str:
        """Render cover page."""
        return f"""
<div class="cover-page">
    <div class="cover-content">
        <h1 class="cover-title">Group Policy Object<br>Analysis Report</h1>
        <div class="cover-date">{self.result.analyzed_at.strftime('%B %d, %Y')}</div>
        <div class="cover-stats">
            <div class="cover-stat">
                <span class="stat-value">{self.result.gpo_count}</span>
                <span class="stat-label">GPOs Analyzed</span>
            </div>
            <div class="cover-stat">
                <span class="stat-value">{self.result.conflict_count}</span>
                <span class="stat-label">Conflicts Found</span>
            </div>
            <div class="cover-stat">
                <span class="stat-value">{self.result.improvement_count}</span>
                <span class="stat-label">Suggestions</span>
            </div>
        </div>
    </div>
</div>
"""
    
    def _render_executive_summary(self) -> str:
        """Render executive summary section."""
        # Calculate health score
        total_issues = (
            self.result.critical_issues * 10 +
            self.result.high_issues * 5 +
            self.result.medium_issues * 2 +
            self.result.low_issues
        )
        health_score = max(0, 100 - (total_issues * 2))
        health_class = "good" if health_score >= 80 else "warning" if health_score >= 50 else "critical"
        
        return f"""
<div class="page-break"></div>
<section class="section">
    <h2>Executive Summary</h2>
    
    <div class="summary-grid">
        <div class="summary-card">
            <h3>Overall Health Score</h3>
            <div class="health-score {health_class}">{health_score}%</div>
        </div>
        
        <div class="summary-card">
            <h3>Analysis Overview</h3>
            <table class="summary-table">
                <tr><td>GPOs Analyzed</td><td><strong>{self.result.gpo_count}</strong></td></tr>
                <tr><td>Total Settings</td><td><strong>{self.result.setting_count}</strong></td></tr>
                <tr><td>Conflicts Detected</td><td><strong>{self.result.conflict_count}</strong></td></tr>
                <tr><td>Duplicates Found</td><td><strong>{self.result.duplicate_count}</strong></td></tr>
                <tr><td>Improvement Suggestions</td><td><strong>{self.result.improvement_count}</strong></td></tr>
            </table>
        </div>
        
        <div class="summary-card">
            <h3>Issue Breakdown</h3>
            <table class="summary-table">
                <tr><td><span class="badge critical">Critical</span></td><td>{self.result.critical_issues}</td></tr>
                <tr><td><span class="badge high">High</span></td><td>{self.result.high_issues}</td></tr>
                <tr><td><span class="badge medium">Medium</span></td><td>{self.result.medium_issues}</td></tr>
                <tr><td><span class="badge low">Low</span></td><td>{self.result.low_issues}</td></tr>
            </table>
        </div>
    </div>
</section>
"""
    
    def _render_gpo_inventory(self) -> str:
        """Render GPO inventory section."""
        if not self.result.gpos:
            return ""
        
        rows = ""
        for gpo in self.result.gpos[:20]:  # Limit to 20 for PDF
            rows += f"""
<tr>
    <td>{gpo.name}</td>
    <td>{gpo.domain or 'N/A'}</td>
    <td>{gpo.modified.strftime('%Y-%m-%d') if gpo.modified else 'N/A'}</td>
</tr>
"""
        
        remaining = len(self.result.gpos) - 20
        if remaining > 0:
            rows += f'<tr><td colspan="3" class="more-items">... and {remaining} more GPOs</td></tr>'
        
        return f"""
<div class="page-break"></div>
<section class="section">
    <h2>GPO Inventory</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>GPO Name</th>
                <th>Domain</th>
                <th>Last Modified</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</section>
"""
    
    def _render_conflicts(self) -> str:
        """Render conflicts section."""
        if not self.result.conflicts:
            return """
<div class="page-break"></div>
<section class="section">
    <h2>Conflicts</h2>
    <p class="no-issues">✓ No conflicts detected. Your GPO configurations are consistent.</p>
</section>
"""
        
        rows = ""
        for conflict in self.result.conflicts[:15]:  # Limit for PDF
            severity_class = conflict.severity.value
            gpo_list = ", ".join(set(p.gpo_name for p in conflict.conflicting_policies[:3]))
            if len(conflict.conflicting_policies) > 3:
                gpo_list += f" (+{len(conflict.conflicting_policies) - 3} more)"
            
            rows += f"""
<tr>
    <td><span class="badge {severity_class}">{conflict.severity.value.upper()}</span></td>
    <td>{conflict.setting_name}</td>
    <td>{gpo_list}</td>
    <td>{conflict.winning_gpo or 'N/A'}</td>
</tr>
"""
        
        return f"""
<div class="page-break"></div>
<section class="section">
    <h2>Conflicts ({self.result.conflict_count} total)</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>Severity</th>
                <th>Setting</th>
                <th>Conflicting GPOs</th>
                <th>Winner</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</section>
"""
    
    def _render_duplicates(self) -> str:
        """Render duplicates section."""
        if not self.result.duplicates:
            return """
<div class="page-break"></div>
<section class="section">
    <h2>Duplicates</h2>
    <p class="no-issues">✓ No duplicate settings detected.</p>
</section>
"""
        
        rows = ""
        for dup in self.result.duplicates[:15]:
            gpo_list = ", ".join(dup.affected_gpos[:3])
            if len(dup.affected_gpos) > 3:
                gpo_list += f" (+{len(dup.affected_gpos) - 3} more)"
            
            rows += f"""
<tr>
    <td><span class="badge {dup.severity.value}">{dup.severity.value.upper()}</span></td>
    <td>{dup.setting_name}</td>
    <td>{gpo_list}</td>
</tr>
"""
        
        return f"""
<div class="page-break"></div>
<section class="section">
    <h2>Duplicates ({self.result.duplicate_count} total)</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>Severity</th>
                <th>Setting</th>
                <th>Affected GPOs</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</section>
"""
    
    def _render_improvements(self) -> str:
        """Render improvement suggestions section."""
        if not self.result.improvements:
            return """
<div class="page-break"></div>
<section class="section">
    <h2>Improvement Suggestions</h2>
    <p class="no-issues">✓ No improvement suggestions - your GPO structure follows best practices!</p>
</section>
"""
        
        items = ""
        for improvement in self.result.improvements[:10]:
            items += f"""
<div class="improvement-card">
    <div class="improvement-header">
        <span class="badge {improvement.severity.value}">{improvement.severity.value.upper()}</span>
        <span class="improvement-category">{improvement.category.value.upper()}</span>
    </div>
    <h4>{improvement.title}</h4>
    <p class="improvement-desc">{improvement.description}</p>
    <p class="improvement-action"><strong>Action:</strong> {improvement.action}</p>
</div>
"""
        
        return f"""
<div class="page-break"></div>
<section class="section">
    <h2>Improvement Suggestions ({self.result.improvement_count} total)</h2>
    {items}
</section>
"""
    
    def _get_css(self) -> str:
        """Return CSS styles for the PDF."""
        return """
@page {
    size: A4;
    margin: 2cm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10px;
        color: #666;
    }
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 11px;
    line-height: 1.5;
    color: #333;
}

.page-break {
    page-break-before: always;
}

/* Cover Page */
.cover-page {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #1a365d 0%, #2563eb 100%);
    color: white;
    text-align: center;
}

.cover-title {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 20px;
}

.cover-date {
    font-size: 16px;
    opacity: 0.9;
    margin-bottom: 40px;
}

.cover-stats {
    display: flex;
    justify-content: center;
    gap: 40px;
}

.cover-stat {
    text-align: center;
}

.stat-value {
    display: block;
    font-size: 48px;
    font-weight: 700;
}

.stat-label {
    font-size: 12px;
    opacity: 0.8;
}

/* Sections */
.section {
    padding: 20px 0;
}

.section h2 {
    font-size: 20px;
    color: #1a365d;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

/* Summary */
.summary-grid {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

.summary-card {
    flex: 1;
    min-width: 150px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

.summary-card h3 {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 10px;
}

.health-score {
    font-size: 32px;
    font-weight: 700;
    text-align: center;
}

.health-score.good { color: #22c55e; }
.health-score.warning { color: #f59e0b; }
.health-score.critical { color: #ef4444; }

.summary-table {
    width: 100%;
}

.summary-table td {
    padding: 4px 0;
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.data-table th,
.data-table td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
}

.data-table th {
    background: #f1f5f9;
    font-weight: 600;
    color: #475569;
}

.data-table tbody tr:nth-child(even) {
    background: #f8fafc;
}

.more-items {
    text-align: center;
    font-style: italic;
    color: #64748b;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}

.badge.critical { background: #fef2f2; color: #dc2626; }
.badge.high { background: #fff7ed; color: #ea580c; }
.badge.medium { background: #fffbeb; color: #d97706; }
.badge.low { background: #f0fdf4; color: #16a34a; }
.badge.info { background: #eff6ff; color: #2563eb; }

/* Improvements */
.improvement-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
}

.improvement-header {
    margin-bottom: 10px;
}

.improvement-category {
    margin-left: 10px;
    font-size: 10px;
    color: #64748b;
}

.improvement-card h4 {
    font-size: 13px;
    margin-bottom: 8px;
}

.improvement-desc {
    color: #475569;
    margin-bottom: 8px;
}

.improvement-action {
    font-size: 10px;
    background: #f1f5f9;
    padding: 8px;
    border-radius: 4px;
}

.no-issues {
    text-align: center;
    padding: 30px;
    background: #f0fdf4;
    color: #16a34a;
    border-radius: 8px;
    border: 1px solid #bbf7d0;
}
"""


def export_to_pdf(result: AnalysisResult) -> bytes:
    """Convenience function for PDF export."""
    exporter = PDFExporter(result)
    return exporter.export()
