# =============================================================================
# GPO Analysis Tool - API Routes
# =============================================================================

import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
import io
from sqlmodel import Session, select

from backend.app.models.gpo import (
    AnalysisResult, UploadResponse, GPOInfo, PolicySetting,
    ConflictReport, DuplicateReport, ImprovementSuggestion,
    SeverityLevel, ExportFormat
)
from backend.app.models.sql import StoredGPO, StoredSetting
from backend.app.database import get_session, init_db
from backend.app.parsers.gpo_parser import GPOParser
from backend.app.analyzers.conflict_detector import detect_conflicts
from backend.app.analyzers.duplicate_detector import detect_duplicates
from backend.app.analyzers.improvement_engine import generate_improvements
from backend.app.exporters.csv_exporter import export_to_csv
from backend.app.exporters.pdf_exporter import export_to_pdf
from backend.app.exporters.action_generator import ActionGenerator
from backend.app.storage import (
    save_analysis, load_analysis, list_saved_analyses, delete_saved_analysis
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["GPO Analysis"])

# In-memory storage for the current analysis session (Backward Compatibility)
# This mimics the old behavior where the user sees the result of what they just uploaded
_current_analysis: Optional[AnalysisResult] = None
_uploaded_files: list[dict] = []
_current_session_gpo_ids: list[str] = [] # IDs of GPOs in current "session"


# =============================================================================
# File Upload Endpoints
# =============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_gpo_files(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload one or more GPO export files for analysis.
    Files are parsed and stored in the database.
    
    Supported formats:
    - HTML/HTM (Get-GPOReport -ReportType HTML)
    - XML (Get-GPOReport -ReportType XML, gpresult /X)
    """
    global _current_analysis, _uploaded_files, _current_session_gpo_ids
    
    # Clear any previous analysis to ensure clean state
    # NOTE: In v3, we might want to allow appending, but for now we follow old behavior
    # of "New Upload = New Analysis Session" unless we add an "Append" flag.
    # To keep strict back-compat, we reset session.
    _current_analysis = None
    _uploaded_files = []
    _current_session_gpo_ids = []
    
    # Create new parser instance for this upload
    parser = GPOParser()
    all_gpos: list[GPOInfo] = []
    all_settings: list[PolicySetting] = []
    errors: list[str] = []
    
    for file in files:
        try:
            try:
                content = await file.read()
                
                # Detect encoding from BOM or heuristics (same logic as parse_file)
                encoding = 'utf-8'
                
                # Check for BOM markers
                if content[:2] == b'\xff\xfe':
                    encoding = 'utf-16-le'
                    logger.debug(f"Detected UTF-16LE encoding (BOM) for {file.filename}")
                elif content[:2] == b'\xfe\xff':
                    encoding = 'utf-16-be'
                    logger.debug(f"Detected UTF-16BE encoding (BOM) for {file.filename}")
                elif content[:3] == b'\xef\xbb\xbf':
                    encoding = 'utf-8'
                    logger.debug(f"Detected UTF-8 encoding (BOM) for {file.filename}")
                else:
                    # No BOM, try to detect from content (check for UTF-16 pattern)
                    if len(content) > 100:
                        null_count = content[:100].count(b'\x00')
                        if null_count > 20:  # Likely UTF-16
                            encoding = 'utf-16-le'
                            logger.debug(f"Detected UTF-16LE encoding (heuristic) for {file.filename}")
                
                try:
                    content_str = content.decode(encoding)
                except Exception as e:
                    logger.warning(f"Failed to decode {file.filename} with {encoding}, falling back to UTF-8: {e}")
                    content_str = content.decode('utf-8', errors='replace')
                
                gpos, settings = parser.parse_content(
                    content_str, 
                    file.filename or "unknown",
                    file.content_type or ""
                )
                
                # --- DB PERSISTENCE START ---
                for gpo in gpos:
                    # Convert to SQL Model
                    # Check if exists first to avoid Primary Key error or overwrite
                    existing_gpo = session.get(StoredGPO, gpo.id)
                    if existing_gpo:
                        # Update? For now, we overwrite metadata but careful with settings
                        # Simpler: Delete old and re-insert is often easier for full replace
                        session.delete(existing_gpo)
                        session.commit()
                    
                    stored_gpo = StoredGPO(
                        id=gpo.id,
                        name=gpo.name,
                        domain=gpo.domain,
                        created=gpo.created,
                        modified=gpo.modified,
                        owner=gpo.owner,
                        computer_enabled=gpo.computer_enabled,
                        user_enabled=gpo.user_enabled,
                        source_file=gpo.source_file,
                        links=[l.model_dump() for l in gpo.links] # Use setter logic if needed, but direct links_data assign via dict works
                    )
                    # Manually handle links setter if property not working in constructor directly (Pydantic/SQLModel quirk)
                    stored_gpo.links = gpo.links 
                    
                    session.add(stored_gpo)
                    
                    # Store Settings
                    # Filter settings for this GPO (parser returns flat list for file, but they have gpo_id)
                    gpo_settings = [s for s in settings if s.gpo_id == gpo.id]
                    for s in gpo_settings:
                        stored_setting = StoredSetting(
                            gpo_id=gpo.id,
                            gpo_name=gpo.name,
                            category=s.category,
                            name=s.name,
                            state=s.state.value,
                            value=s.value,
                            registry_path=s.registry_path,
                            registry_value=s.registry_value,
                            scope=s.scope
                        )
                        session.add(stored_setting)
                    
                    _current_session_gpo_ids.append(gpo.id)

                session.commit()
                # --- DB PERSISTENCE END ---
                
                all_gpos.extend(gpos)
                all_settings.extend(settings)
                
                _uploaded_files.append({
                    "filename": file.filename,
                    "size": len(content),
                    "gpos_found": len(gpos),
                    "settings_found": len(settings)
                })
                
                logger.info(f"Processed file '{file.filename}': {len(gpos)} GPO(s), {len(settings)} setting(s)")
            finally:
                await file.close()
            
        except Exception as e:
            error_msg = f"Error processing '{file.filename}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    if not all_gpos:
        return UploadResponse(
            success=False,
            message="No GPOs could be extracted from the uploaded files.",
            files_processed=len(files),
            gpos_found=0,
            errors=errors
        )
    
    # Run analysis
    conflicts = detect_conflicts(all_gpos, all_settings)
    duplicates = detect_duplicates(all_gpos, all_settings)
    improvements = generate_improvements(all_gpos, all_settings)
    
    # Calculate severity counts
    all_issues = conflicts + duplicates + [
        type('obj', (object,), {'severity': s.severity})() for s in improvements
    ]
    
    critical_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.CRITICAL)
    high_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.HIGH)
    medium_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.MEDIUM)
    low_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.LOW)
    
    # Store analysis result
    _current_analysis = AnalysisResult(
        analyzed_at=datetime.now(),
        gpo_count=len(all_gpos),
        setting_count=len(all_settings),
        gpos=all_gpos,
        settings=all_settings,
        conflicts=conflicts,
        duplicates=duplicates,
        improvements=improvements,
        conflict_count=len(conflicts),
        duplicate_count=len(duplicates),
        improvement_count=len(improvements),
        critical_issues=critical_count,
        high_issues=high_count,
        medium_issues=medium_count,
        low_issues=low_count
    )
    
    return UploadResponse(
        success=True,
        message=f"Successfully analyzed {len(all_gpos)} GPO(s) with {len(all_settings)} setting(s).",
        files_processed=len(files),
        gpos_found=len(all_gpos),
        errors=errors
    )


@router.delete("/upload")
async def clear_analysis():
    """Clear current analysis and uploaded files."""
    global _current_analysis, _uploaded_files
    _current_analysis = None
    _uploaded_files = []
    logger.info("Analysis cleared, ready for new upload")
    return {"message": "Analysis cleared", "success": True}


# =============================================================================
# Analysis Results Endpoints
# =============================================================================

@router.get("/analysis", response_model=Optional[AnalysisResult])
async def get_analysis():
    """Get the current analysis result."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available. Upload GPO files first.")
    return _current_analysis


@router.get("/gpos", response_model=list[GPOInfo])
async def get_gpos():
    """Get list of analyzed GPOs."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    return _current_analysis.gpos


@router.get("/settings", response_model=list[PolicySetting])
async def get_settings(
    gpo_id: Optional[str] = Query(None, description="Filter by GPO ID"),
    scope: Optional[str] = Query(None, description="Filter by scope (Computer/User)"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)")
):
    """Get list of policy settings with optional filtering."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    settings = _current_analysis.settings
    
    if gpo_id:
        settings = [s for s in settings if s.gpo_id == gpo_id]
    if scope:
        settings = [s for s in settings if s.scope.lower() == scope.lower()]
    if category:
        settings = [s for s in settings if category.lower() in s.category.lower()]
    
    return settings


@router.get("/conflicts", response_model=list[ConflictReport])
async def get_conflicts(
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity")
):
    """Get conflict reports."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    conflicts = _current_analysis.conflicts
    
    if severity:
        conflicts = [c for c in conflicts if c.severity == severity]
    
    return conflicts


@router.get("/duplicates", response_model=list[DuplicateReport])
async def get_duplicates(
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity")
):
    """Get duplicate reports."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    duplicates = _current_analysis.duplicates
    
    if severity:
        duplicates = [d for d in duplicates if d.severity == severity]
    
    return duplicates


@router.get("/improvements", response_model=list[ImprovementSuggestion])
async def get_improvements(
    category: Optional[str] = Query(None, description="Filter by improvement category")
):
    """Get improvement suggestions."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    improvements = _current_analysis.improvements
    
    if category:
        improvements = [i for i in improvements if i.category.value == category]
    
    return improvements


@router.get("/generate-fix/{suggestion_id}")
async def generate_fix(suggestion_id: str):
    """Generate a PowerShell fix script for a suggestion."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    # Find the suggestion
    suggestion = next((i for i in _current_analysis.improvements if i.id == suggestion_id), None)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found.")
        
    script_content = ActionGenerator.generate_fix_script(suggestion)
    
    filename = f"fix_{suggestion_id}.ps1"
    
    return StreamingResponse(
        io.StringIO(script_content),
        media_type="application/powershell",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/generate-consolidation/{suggestion_id}")
async def generate_consolidation(suggestion_id: str):
    """Generate a PowerShell script to consolidate GPOs."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    # Find the suggestion
    suggestion = next((i for i in _current_analysis.improvements if i.id == suggestion_id), None)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found.")
    
    if suggestion.category != "consolidation":
        raise HTTPException(status_code=400, detail="This manual action is only for consolidation suggestions.")
        
    # Derive name from suggestion title or default
    # Title format: "Consolidate '{prefix}' GPO group" or "Consolidate GPOs for '{cat}'"
    new_name = "Consolidated-GPO"
    if "Consolidate '" in suggestion.title:
        # crude extraction
        try:
            part = suggestion.title.split("'")[1]
            new_name = f"Policy-{part}-Consolidated"
        except:
            pass
            
    script_content = ActionGenerator.generate_consolidation_script(new_name, suggestion.affected_gpos)
    
    filename = f"consolidate_{suggestion_id}.ps1"
    
    return StreamingResponse(
        io.StringIO(script_content),
        media_type="application/powershell",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# =============================================================================
# Export Endpoints
# =============================================================================

@router.get("/export/csv")
async def export_csv():
    """Export analysis results to CSV."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    # Use a copy to prevent state corruption
    from copy import deepcopy
    analysis_copy = deepcopy(_current_analysis)
    csv_content = export_to_csv(analysis_copy, combined=True)
    
    filename = f"gpo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/pdf")
async def export_pdf():
    """Export analysis results to PDF."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    try:
        # Use a copy to prevent state corruption
        from copy import deepcopy
        analysis_copy = deepcopy(_current_analysis)
        pdf_content = export_to_pdf(analysis_copy)
        
        filename = f"gpo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/export/policy")
async def export_policy():
    """Export recommended policy settings as PowerShell GPO script."""
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available.")
    
    try:
        from backend.app.exporters.policy_exporter import export_recommended_policy
        from copy import deepcopy
        
        # Use a copy to prevent state corruption
        analysis_copy = deepcopy(_current_analysis)
        policy_content = export_recommended_policy(analysis_copy)
        
        filename = f"gpo_recommended_policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ps1"
        
        return StreamingResponse(
            io.StringIO(policy_content),
            media_type="application/powershell",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Policy export error: {e}")
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")


# =============================================================================
# Statistics Endpoint
# =============================================================================

@router.get("/stats")
async def get_statistics():
    """Get analysis statistics and summary."""
    if not _current_analysis:
        return {
            "has_analysis": False,
            "uploaded_files": len(_uploaded_files),
            "files": _uploaded_files
        }
    
    return {
        "has_analysis": True,
        "analyzed_at": _current_analysis.analyzed_at.isoformat(),
        "gpo_count": _current_analysis.gpo_count,
        "setting_count": _current_analysis.setting_count,
        "conflict_count": _current_analysis.conflict_count,
        "duplicate_count": _current_analysis.duplicate_count,
        "improvement_count": _current_analysis.improvement_count,
        "issues": {
            "critical": _current_analysis.critical_issues,
            "high": _current_analysis.high_issues,
            "medium": _current_analysis.medium_issues,
            "low": _current_analysis.low_issues
        },
        "uploaded_files": _uploaded_files
    }


# =============================================================================
# Analysis Storage Endpoints
# =============================================================================

@router.post("/analysis/save")
async def save_current_analysis(name: str = Query(..., description="Name for the saved analysis")):
    """Save the current analysis with a given name."""
    global _current_analysis
    
    if not _current_analysis:
        raise HTTPException(status_code=404, detail="No analysis available to save.")
    
    result = save_analysis(_current_analysis, name)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to save analysis"))
    
    return result


@router.get("/analysis/saved")
async def get_saved_analyses():
    """Get list of all saved analyses."""
    return list_saved_analyses()


@router.get("/analysis/load/{filename}")
async def load_saved_analysis(filename: str):
    """Load a previously saved analysis."""
    global _current_analysis, _uploaded_files
    
    analysis = load_analysis(filename)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or failed to load.")
    
    _current_analysis = analysis
    _uploaded_files = []  # Clear uploaded files list (loaded from save)
    
    return {
        "success": True,
        "message": f"Loaded analysis with {analysis.gpo_count} GPOs",
        "gpo_count": analysis.gpo_count,
        "setting_count": analysis.setting_count
    }


@router.delete("/analysis/saved/{filename}")
async def delete_analysis(filename: str):
    """Delete a saved analysis."""
    result = delete_saved_analysis(filename)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to delete analysis"))
    
    return result


# =============================================================================
# Library & Object Analysis Endpoints (v3)
# =============================================================================

@router.get("/library", response_model=List[dict])
async def get_gpo_library(session: Session = Depends(get_session)):
    """List all GPOs stored in the database."""
    gpos = session.exec(select(StoredGPO)).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "domain": g.domain,
            "modified": g.modified,
            "gpo_guid": g.id, 
            "link_count": len(g.links) if g.links else 0,
            "source": g.source_file
        }
        for g in gpos
    ]

@router.post("/analysis/start", response_model=AnalysisResult)
async def start_analysis(
    gpo_ids: List[str],
    session: Session = Depends(get_session)
):
    """
    Start a new analysis session with specific GPOs from the library.
    """
    global _current_analysis, _current_session_gpo_ids
    
    # Fetch selected GPOs
    selected_gpos = []
    selected_settings = []
    
    for gid in gpo_ids:
        sgpo = session.get(StoredGPO, gid)
        if sgpo:
            gpo_info = GPOInfo(
                id=sgpo.id,
                name=sgpo.name,
                domain=sgpo.domain,
                created=sgpo.created,
                modified=sgpo.modified,
                owner=sgpo.owner,
                computer_enabled=sgpo.computer_enabled,
                user_enabled=sgpo.user_enabled,
                source_file=sgpo.source_file,
                links=[l.model_dump() for l in sgpo.links]
            )
            selected_gpos.append(gpo_info)
            
            ssettings = session.exec(select(StoredSetting).where(StoredSetting.gpo_id == gid)).all()
            for ss in ssettings:
                selected_settings.append(PolicySetting(
                    gpo_id=ss.gpo_id,
                    gpo_name=ss.gpo_name,
                    category=ss.category,
                    name=ss.name,
                    state=PolicyState(ss.state) if ss.state else PolicyState.NOT_CONFIGURED,
                    value=ss.value,
                    registry_path=ss.registry_path,
                    registry_value=ss.registry_value,
                    scope=ss.scope
                ))

    if not selected_gpos:
        raise HTTPException(status_code=404, detail="No valid GPOs found for the provided IDs.")

    # Run Analysis
    conflicts = detect_conflicts(selected_gpos, selected_settings)
    duplicates = detect_duplicates(selected_gpos, selected_settings)
    improvements = generate_improvements(selected_gpos, selected_settings)
    
     # Calculate severity counts
    critical_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.CRITICAL)
    high_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.HIGH)
    medium_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.MEDIUM)
    low_count = sum(1 for i in conflicts + duplicates if i.severity == SeverityLevel.LOW)
    
    # Update global state
    _current_session_gpo_ids = gpo_ids
    _current_analysis = AnalysisResult(
        analyzed_at=datetime.now(),
        gpo_count=len(selected_gpos),
        setting_count=len(selected_settings),
        gpos=selected_gpos,
        settings=selected_settings,
        conflicts=conflicts,
        duplicates=duplicates,
        improvements=improvements,
        conflict_count=len(conflicts),
        duplicate_count=len(duplicates),
        improvement_count=len(improvements),
        critical_issues=critical_count,
        high_issues=high_count,
        medium_issues=medium_count,
        low_issues=low_count
    )
    
    return _current_analysis


@router.get("/analysis/object")
async def analyze_object(
    query: str = Query(..., description="Computer Name, User Name, or OU DN"),
    type: str = Query("auto", description="auto, computer, user, ou"),
    session: Session = Depends(get_session)
):
    """
    Find policies applied to a specific object.
    1. Direct Match: Check if we have a gpresult for object.
    2. Link Match: Check if any GPO is linked to the provided OU.
    """
    results = {
        "query": query,
        "match_type": "none",
        "applied_gpos": [],
        "effective_settings": []
    }
    
    stmt = select(StoredGPO).where(StoredGPO.source_file.contains(query) | StoredGPO.name.contains(query))
    direct_matches = session.exec(stmt).all()
    
    if direct_matches:
        results["match_type"] = "report_match"
        results["matches"] = [{"id": g.id, "name": g.name, "source": g.source_file} for g in direct_matches]
        for match in direct_matches:
            results["applied_gpos"].append({
                "id": match.id,
                "name": match.name,
                "reason": "Direct Report Match"
            })
            
    if "dc=" in query.lower() or "ou=" in query.lower():
        all_gpos = session.exec(select(StoredGPO)).all()
        start_node = query.lower().strip()
        
        for gpo in all_gpos:
            for link in gpo.links:
                if link.location.lower() == start_node and link.enabled:
                    results["applied_gpos"].append({
                        "id": gpo.id,
                        "name": gpo.name,
                        "location": link.location,
                        "enforced": link.enforced,
                        "reason": f"Linked to {link.location}"
                    })
        
        if results["applied_gpos"] and results["match_type"] == "none":
            results["match_type"] = "link_match"

    return results

@router.get("/export/object")
async def export_object_analysis(
    query: str,
    format: ExportFormat = ExportFormat.CSV,
    session: Session = Depends(get_session)
):
    """Export the object analysis results."""
    analysis_data = await analyze_object(query, "auto", session)
    
    if format == ExportFormat.CSV:
        output = io.StringIO()
        output.write("GPO Name,Reason,Location,Enforced\n")
        for gpo in analysis_data["applied_gpos"]:
            output.write(f"{gpo['name']},{gpo.get('reason','')},{gpo.get('location','')},{gpo.get('enforced','')}\n")
        
        filename = f"object_analysis_{query}.csv"
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        return {"error": "PDF export for object analysis not yet implemented"}
