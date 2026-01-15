
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append('/home/user/git/GPOanalysis')

from backend.app.models.gpo import AnalysisResult, GPOInfo, PolicySetting, SeverityLevel
from backend.app.exporters.csv_exporter import export_to_csv
from backend.app.exporters.pdf_exporter import export_to_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dummy_data():
    return AnalysisResult(
        gpo_count=1,
        setting_count=1,
        gpos=[GPOInfo(
            id="123", name="Test GPO", source_file="test.xml", 
            created=datetime.now(), modified=datetime.now()
        )],
        settings=[PolicySetting(
            gpo_id="123", gpo_name="Test GPO", category="Security", 
            name="Test Setting", value="Enabled"
        )],
        conflicts=[],
        duplicates=[],
        improvements=[]
    )

def test_csv():
    logger.info("Testing CSV Export...")
    try:
        data = create_dummy_data()
        csv_out = export_to_csv(data)
        if len(csv_out) > 0:
            logger.info("CSV Export Success")
        else:
            logger.error("CSV output empty")
    except Exception as e:
        logger.error(f"CSV Export Failed: {e}")
        import traceback
        traceback.print_exc()

def test_pdf():
    logger.info("Testing PDF Export...")
    try:
        data = create_dummy_data()
        pdf_out = export_to_pdf(data)
        if len(pdf_out) > 0:
            logger.info("PDF Export Success")
        else:
            logger.error("PDF output empty")
    except Exception as e:
        logger.error(f"PDF Export Failed: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    test_csv()
    test_pdf()
