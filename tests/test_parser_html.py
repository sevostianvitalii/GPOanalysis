"""
Test for GPO HTML Parser.

Tests the ability to parse Microsoft Get-GPOReport HTML format.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, '/home/user/git/GPOanalysis')

from backend.app.parsers.gpo_parser import GPOParser
from backend.app.models.gpo import PolicyState
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_html_parser():
    """Test parsing the sample GPO HTML file."""
    sample_file = Path('/home/user/git/GPOanalysis/tests/sample_gpo.htm')
    
    if not sample_file.exists():
        logger.error(f"Sample file not found: {sample_file}")
        return False
    
    parser = GPOParser()
    gpos, settings = parser.parse_file(sample_file)
    
    logger.info(f"GPOs found: {len(gpos)}")
    logger.info(f"Settings found: {len(settings)}")
    
    # Verify GPO metadata was extracted
    if len(gpos) == 0:
        logger.error("FAIL: No GPOs found")
        return False
    
    gpo = gpos[0]
    logger.info(f"GPO Name: {gpo.name}")
    logger.info(f"GPO Domain: {gpo.domain}")
    logger.info(f"GPO ID: {gpo.id}")
    
    # Verify settings were extracted
    if len(settings) == 0:
        logger.error("FAIL: No settings found")
        return False
    
    # Count settings by scope
    computer_settings = [s for s in settings if s.scope == "Computer"]
    user_settings = [s for s in settings if s.scope == "User"]
    
    logger.info(f"Computer settings: {len(computer_settings)}")
    logger.info(f"User settings: {len(user_settings)}")
    
    # Verify we got enabled settings (password settings have values)
    enabled_settings = [s for s in settings if s.state == PolicyState.ENABLED]
    logger.info(f"Enabled settings: {len(enabled_settings)}")
    
    # List some settings for verification
    logger.info("\nSample settings found:")
    for s in settings[:10]:
        logger.info(f"  - {s.name}: {s.state.value} (value: {s.value})")
    
    # Checks
    passed = True
    
    # Check GPO name matched title
    if "SEC-Baseline-Computer" not in gpo.name:
        logger.warning(f"GPO name mismatch, expected 'SEC-Baseline-Computer', got '{gpo.name}'")
    
    # Check we found expected settings
    setting_names = [s.name for s in settings]
    
    expected_settings = [
        "Minimum password length",
        "Maximum password age",
        "Account lockout threshold"
    ]
    
    for expected in expected_settings:
        if expected not in setting_names:
            logger.warning(f"Expected setting not found: {expected}")
            passed = False
    
    if passed:
        logger.info("\n✓ All tests passed!")
    else:
        logger.error("\n✗ Some tests failed")
    
    return passed


def test_state_extraction():
    """Test the state extraction from combined values."""
    parser = GPOParser()
    
    test_cases = [
        ("Enabled", PolicyState.ENABLED, None),
        ("Disabled", PolicyState.DISABLED, None),
        ("Not Configured", PolicyState.NOT_CONFIGURED, None),
        ("8 characters", PolicyState.ENABLED, "8 characters"),
        ("90 days", PolicyState.ENABLED, "90 days"),
        ("24 passwords remembered", PolicyState.ENABLED, "24 passwords remembered"),
    ]
    
    all_passed = True
    for value_text, expected_state, expected_value in test_cases:
        state, value = parser._extract_state_from_value(value_text)
        if state != expected_state:
            logger.error(f"FAIL: '{value_text}' -> state {state}, expected {expected_state}")
            all_passed = False
        elif value != expected_value:
            logger.error(f"FAIL: '{value_text}' -> value '{value}', expected '{expected_value}'")
            all_passed = False
        else:
            logger.info(f"OK: '{value_text}' -> {state.value}, '{value}'")
    
    return all_passed


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Testing State Extraction")
    logger.info("=" * 60)
    test_state_extraction()
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing HTML Parser")
    logger.info("=" * 60)
    test_html_parser()
