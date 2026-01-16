
import asyncio
import traceback
from datetime import datetime
from sqlmodel import Session, select, create_engine
from backend.app.database import init_db
from backend.app.models.sql import StoredGPO, StoredSetting
from backend.app.models.gpo import PolicyState, GPOInfo, PolicySetting, AnalysisResult, SeverityLevel
from backend.app.analyzers.conflict_detector import detect_conflicts
from backend.app.analyzers.duplicate_detector import detect_duplicates
from backend.app.analyzers.improvement_engine import generate_improvements

# Connect to the actual DB
engine = create_engine("sqlite:///data/gpo_analysis.db")

def debug_analysis_logic():
    print("--- Debugging Analysis Logic ---")
    with Session(engine) as session:
        # 1. Fetch all GPO IDs to mimic user selection
        gpos = session.exec(select(StoredGPO)).all()
        if not gpos:
            print("No GPOs in DB to test.")
            return

        gpo_ids = [g.id for g in gpos]
        print(f"Testing analysis with GPO IDs: {gpo_ids}")
        
        # 2. Reproduction of start_analysis code
        try:
            selected_gpos = []
            selected_settings = []
            
            for gid in gpo_ids:
                sgpo = session.get(StoredGPO, gid)
                if sgpo:
                    print(f"Converting GPO: {sgpo.name}")
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
                    print(f"  - Found {len(ssettings)} settings")
                    
                    for ss in ssettings:
                        # DEBUG: detailed setting conversion
                        try:
                            # Verify Enum mapping
                            state_val = PolicyState(ss.state) if ss.state else PolicyState.NOT_CONFIGURED
                            
                            selected_settings.append(PolicySetting(
                                gpo_id=ss.gpo_id,
                                gpo_name=ss.gpo_name,
                                category=ss.category,
                                name=ss.name,
                                state=state_val,
                                value=ss.value,
                                registry_path=ss.registry_path,
                                registry_value=ss.registry_value,
                                scope=ss.scope
                            ))
                        except Exception as e:
                            print(f"ERROR converting setting {ss.name}: {e}")
                            raise e

            print("Run Analysis...")
            conflicts = detect_conflicts(selected_gpos, selected_settings)
            print(f"Conflicts: {len(conflicts)}")
            
            duplicates = detect_duplicates(selected_gpos, selected_settings)
            print(f"Duplicates: {len(duplicates)}")
            
            improvements = generate_improvements(selected_gpos, selected_settings)
            print(f"Improvements: {len(improvements)}")
            
            # Construct Result
            print("Constructing AnalysisResult...")
            result = AnalysisResult(
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
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0
            )
            print("Success!")
            
        except Exception as e:
            print("\n!!! CRASH DETECTED !!!")
            traceback.print_exc()

if __name__ == "__main__":
    debug_analysis_logic()
