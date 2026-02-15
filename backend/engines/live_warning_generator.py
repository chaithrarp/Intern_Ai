"""
Live Warning Generator
Generates non-interrupting warnings during recording
"""

from typing import Dict, Optional, List
from datetime import datetime

class LiveWarningGenerator:
    """
    Generates live warnings without interrupting the user
    """
    
    def __init__(self):
        self.warning_cooldowns = {}  # Prevent spam
        self.COOLDOWN_SECONDS = 10  # Min 10s between same warning type
    
    def should_show_warning(
        self,
        issue_type: str,
        session_id: str
    ) -> bool:
        """
        Check if warning should be shown (respects cooldown)
        
        Args:
            issue_type: Type of issue
            session_id: Current session
            
        Returns:
            True if warning should be shown
        """
        
        key = f"{session_id}_{issue_type}"
        
        if key not in self.warning_cooldowns:
            # First warning of this type
            self.warning_cooldowns[key] = datetime.now()
            return True
        
        # Check cooldown
        last_warning_time = self.warning_cooldowns[key]
        elapsed = (datetime.now() - last_warning_time).total_seconds()
        
        if elapsed >= self.COOLDOWN_SECONDS:
            self.warning_cooldowns[key] = datetime.now()
            return True
        
        return False
    
    def generate_warning(
        self,
        analysis_result: Dict,
        session_id: str
    ) -> Optional[Dict]:
        """
        Generate warning data for frontend
        
        Args:
            analysis_result: Result from InterruptionAnalyzer
            session_id: Current session
            
        Returns:
            Warning data or None
        """
        
        if not analysis_result:
            return None
        
        # Only generate warnings if action is "warn" (not interrupt)
        if analysis_result.get('action') != 'warn':
            return None
        
        issue_type = analysis_result.get('reason')
        
        # Check cooldown
        if not self.should_show_warning(issue_type, session_id):
            return None
        
        # Generate warning message
        warning_message = self._get_warning_message(issue_type)
        warning_icon = self._get_warning_icon(issue_type)
        warning_color = self._get_warning_color(analysis_result.get('severity', 'low'))
        
        return {
            "type": "live_warning",
            "issue_type": issue_type,
            "message": warning_message,
            "icon": warning_icon,
            "color": warning_color,
            "severity": analysis_result.get('severity'),
            "evidence": analysis_result.get('evidence'),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_warning_message(self, issue_type: str) -> str:
        """
        Get user-friendly warning message
        """
        
        messages = {
            "EXCESSIVE_PAUSING": "You're taking long pauses",
            "HIGH_HESITATION": "Try to speak more fluently",
            "LOW_CONFIDENCE": "Speak with more confidence",
            "INCONSISTENT_DELIVERY": "Maintain steady pace",
            "SPEAKING_TOO_LONG": "Wrap up your point",
            "RAMBLING": "Reduce filler words",
            "OFF_TOPIC": "Stay focused on the question",
            "DODGING_QUESTION": "Address the question directly",
            "VAGUE_CLAIM": "Be more specific",
            "LACK_OF_SPECIFICS": "Give concrete examples"
        }
        
        return messages.get(issue_type, "Consider adjusting your approach")
    
    def _get_warning_icon(self, issue_type: str) -> str:
        """
        Get icon for warning type
        """
        
        icons = {
            "EXCESSIVE_PAUSING": "⏸️",
            "HIGH_HESITATION": "🤔",
            "LOW_CONFIDENCE": "📢",
            "INCONSISTENT_DELIVERY": "📊",
            "SPEAKING_TOO_LONG": "⏱️",
            "RAMBLING": "💬",
            "OFF_TOPIC": "🎯",
            "DODGING_QUESTION": "❓",
            "VAGUE_CLAIM": "🔍",
            "LACK_OF_SPECIFICS": "📝"
        }
        
        return icons.get(issue_type, "⚠️")
    
    def _get_warning_color(self, severity: str) -> str:
        """
        Get color for warning severity
        """
        
        colors = {
            "critical": "#ff4444",  # Red
            "high": "#ff9800",      # Orange
            "medium": "#ffc107",    # Yellow
            "low": "#4caf50"        # Green
        }
        
        return colors.get(severity, "#ffc107")
    
    def clear_session_warnings(self, session_id: str):
        """
        Clear warning cooldowns for a session
        """
        keys_to_remove = [k for k in self.warning_cooldowns.keys() if k.startswith(f"{session_id}_")]
        for key in keys_to_remove:
            del self.warning_cooldowns[key]

# ============================================
# SINGLETON INSTANCE
# ============================================

_warning_generator_instance = None

def get_warning_generator() -> LiveWarningGenerator:
    """
    Get singleton instance of warning generator
    """
    global _warning_generator_instance
    if _warning_generator_instance is None:
        _warning_generator_instance = LiveWarningGenerator()
    return _warning_generator_instance

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("LIVE WARNING GENERATOR TEST")
    print("=" * 60)
    
    generator = get_warning_generator()
    
    # Test 1: Generate warning
    print("\n1. Test: Generate warning for excessive pausing")
    analysis_result = {
        "action": "warn",
        "reason": "EXCESSIVE_PAUSING",
        "severity": "critical",
        "evidence": "3 pauses over 3 seconds"
    }
    
    warning = generator.generate_warning(analysis_result, "test_session")
    if warning:
        print(f"   Message: {warning['message']}")
        print(f"   Icon: {warning['icon']}")
        print(f"   Color: {warning['color']}")
        print(f"   Severity: {warning['severity']}")
    
    # Test 2: Cooldown (should not show second warning immediately)
    print("\n2. Test: Cooldown - same warning immediately")
    warning2 = generator.generate_warning(analysis_result, "test_session")
    print(f"   Warning shown: {warning2 is not None}")
    
    # Test 3: Different warning type (should show)
    print("\n3. Test: Different warning type")
    analysis_result2 = {
        "action": "warn",
        "reason": "SPEAKING_TOO_LONG",
        "severity": "medium",
        "evidence": "Speaking for 95 seconds"
    }
    
    warning3 = generator.generate_warning(analysis_result2, "test_session")
    if warning3:
        print(f"   Message: {warning3['message']}")
        print(f"   Warning shown: True")
    
    # Test 4: No warning for interrupt action
    print("\n4. Test: No warning for interrupt action")
    analysis_result3 = {
        "action": "interrupt",
        "reason": "FALSE_CLAIM",
        "severity": "critical"
    }
    
    warning4 = generator.generate_warning(analysis_result3, "test_session")
    print(f"   Warning shown: {warning4 is not None} (should be False)")
    
    print("\n✅ Live warning generator test complete!")