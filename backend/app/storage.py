# =============================================================================
# GPO Analysis Tool - Analysis Storage
# =============================================================================
# File-based storage for saving and loading GPO analysis results

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.app.models.gpo import AnalysisResult

logger = logging.getLogger(__name__)

# Storage directory configuration
BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "data" / "analyses"


def ensure_storage_dir():
    """Ensure the storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize a name to be safe for use as a filename."""
    # Replace unsafe characters with underscores
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, '_')
    # Limit length
    return name[:100].strip()


def save_analysis(analysis: AnalysisResult, name: str) -> dict:
    """
    Save an analysis result to a JSON file.
    
    Args:
        analysis: The analysis result to save
        name: Human-readable name for the saved analysis
        
    Returns:
        Dictionary with save result info
    """
    ensure_storage_dir()
    
    # Create a safe filename
    safe_name = sanitize_filename(name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{safe_name}_{timestamp}.json"
    filepath = STORAGE_DIR / filename
    
    # Convert to JSON-serializable format
    analysis_dict = analysis.model_dump(mode='json')
    
    # Add metadata
    save_data = {
        "name": name,
        "saved_at": datetime.now().isoformat(),
        "analysis": analysis_dict
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, default=str)
        
        logger.info(f"Saved analysis '{name}' to {filepath}")
        
        return {
            "success": True,
            "filename": filename,
            "path": str(filepath),
            "name": name
        }
    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def load_analysis(filename: str) -> Optional[AnalysisResult]:
    """
    Load a saved analysis from a JSON file.
    
    Args:
        filename: Name of the file to load (without path)
        
    Returns:
        AnalysisResult object or None if loading fails
    """
    filepath = STORAGE_DIR / filename
    
    if not filepath.exists():
        logger.error(f"Analysis file not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        analysis_dict = save_data.get("analysis", save_data)
        analysis = AnalysisResult.model_validate(analysis_dict)
        
        logger.info(f"Loaded analysis from {filepath}")
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to load analysis from {filepath}: {e}")
        return None


def list_saved_analyses() -> list[dict]:
    """
    List all saved analyses.
    
    Returns:
        List of dictionaries with analysis metadata
    """
    ensure_storage_dir()
    
    analyses = []
    
    for filepath in sorted(STORAGE_DIR.glob("*.json"), reverse=True):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Get metadata
            name = save_data.get("name", filepath.stem)
            saved_at = save_data.get("saved_at", "")
            
            # Get analysis summary
            analysis = save_data.get("analysis", {})
            
            analyses.append({
                "filename": filepath.name,
                "name": name,
                "saved_at": saved_at,
                "gpo_count": analysis.get("gpo_count", 0),
                "setting_count": analysis.get("setting_count", 0),
                "conflict_count": analysis.get("conflict_count", 0),
                "duplicate_count": analysis.get("duplicate_count", 0),
                "improvement_count": analysis.get("improvement_count", 0),
            })
            
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            analyses.append({
                "filename": filepath.name,
                "name": filepath.stem,
                "error": str(e)
            })
    
    return analyses


def delete_saved_analysis(filename: str) -> dict:
    """
    Delete a saved analysis file.
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Dictionary with deletion result
    """
    filepath = STORAGE_DIR / filename
    
    if not filepath.exists():
        return {
            "success": False,
            "error": "File not found"
        }
    
    try:
        filepath.unlink()
        logger.info(f"Deleted saved analysis: {filepath}")
        return {
            "success": True,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to delete {filepath}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
