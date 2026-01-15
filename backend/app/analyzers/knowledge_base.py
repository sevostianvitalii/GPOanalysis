import json
import logging
from pathlib import Path
from typing import Optional, Any

from backend.app.models.knowledge import BestPracticeRule

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """
    Loads and provides access to GPO best practice rules.
    """
    
    def __init__(self, rules_path: Optional[Path] = None):
        self.rules: list[BestPracticeRule] = []
        if rules_path:
            self.load_rules(rules_path)
        else:
            # Default to local data directory
            default_path = Path(__file__).parent.parent / "data" / "baselines.json"
            if default_path.exists():
                self.load_rules(default_path)
    
    def load_rules(self, path: Path) -> None:
        """Load rules from a JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rules = [BestPracticeRule(**rule) for rule in data]
            logger.info(f"Loaded {len(self.rules)} best practice rules from {path}")
        except Exception as e:
            logger.error(f"Failed to load knowledge base rules from {path}: {e}")
            self.rules = []
    
    def get_rules_for_setting(self, setting_name: str) -> list[BestPracticeRule]:
        """Find rules applicable to a specific setting name."""
        return [
            r for r in self.rules 
            if r.setting_name and r.setting_name.lower() in setting_name.lower()
        ]
    
    def evaluate(self, value: Any, rule: BestPracticeRule) -> bool:
        """
        Evaluate a value against a rule.
        Returns True if the value COMPLIES with the rule, False otherwise.
        """
        if rule.recommended_value is None:
            return True
            
        try:
            # Handle numeric comparisons
            if isinstance(rule.recommended_value, (int, float)):
                try:
                    actual_val = float(str(value)) # Try to cast setting value (often string) to float
                    Rec_val = float(rule.recommended_value)
                except ValueError:
                    # If value is not a number (e.g. "Enabled"), numeric comparison fails
                    return False
                
                if rule.operator == "greater_than_or_equal":
                    return actual_val >= Rec_val
                elif rule.operator == "less_than_or_equal":
                    return actual_val <= Rec_val
                elif rule.operator == "equals":
                    return actual_val == Rec_val
            
            # String comparisons
            str_val = str(value).lower()
            rec_val = str(rule.recommended_value).lower()
            
            if rule.operator == "equals":
                return str_val == rec_val
            elif rule.operator == "contains":
                return rec_val in str_val
                
        except Exception as e:
            logger.warning(f"Error evaluating rule {rule.id} against value {value}: {e}")
            
        return False
