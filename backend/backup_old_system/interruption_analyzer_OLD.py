"""
Interruption Analyzer - Intelligent Interruption Decision Engine
Analyzes audio patterns and content to decide when to interrupt
"""

from typing import Dict, List, Optional, Tuple
from models.interruption_models import InterruptionReason
import json

# ============================================
# INTERRUPTION PRIORITY MAPPING
# ============================================

INTERRUPTION_PRIORITIES = {
    # CRITICAL - Interrupt immediately (1-3)
    InterruptionReason.FALSE_CLAIM: 1,
    InterruptionReason.CONTRADICTION: 2,
    InterruptionReason.EXCESSIVE_PAUSING: 3,
    
    # HIGH - Warn once, then interrupt (4-6)
    InterruptionReason.OFF_TOPIC: 4,
    InterruptionReason.DODGING_QUESTION: 5,
    InterruptionReason.RAMBLING: 6,
    
    # MEDIUM - Warn twice, then interrupt (7-9)
    InterruptionReason.VAGUE_CLAIM: 7,
    InterruptionReason.LACK_OF_SPECIFICS: 8,
    InterruptionReason.UNCERTAINTY: 9,
    
    # LOW - Warning only (10)
    InterruptionReason.SPEAKING_TOO_LONG: 10
}

class InterruptionAnalyzer:
    """
    Analyzes real-time audio patterns to detect interruption triggers
    """
    
    def __init__(self):
        self.warning_history = {}  # Track warnings per session
    
    def analyze_audio_patterns(
        self,
        audio_report: Dict,
        session_id: str
    ) -> Optional[Dict]:
        """
        Analyze audio patterns from frontend analyzer
        
        Args:
            audio_report: Report from frontend AudioAnalyzer.getAnalysisReport()
            session_id: Current session ID
            
        Returns:
            Interruption trigger data or None
        """
        
        if not audio_report or 'detected_issues' not in audio_report:
            return None
        
        detected_issues = audio_report['detected_issues']
        
        if not detected_issues:
            return None
        
        # Sort issues by priority (lowest number = highest priority)
        sorted_issues = sorted(detected_issues, key=lambda x: x['priority'])
        
        # Get highest priority issue
        top_issue = sorted_issues[0]
        issue_type = top_issue['type']
        priority = top_issue['priority']
        
        # Initialize warning history for session if needed
        if session_id not in self.warning_history:
            self.warning_history[session_id] = {}
        
        # Track warnings for this issue type
        warning_count = self.warning_history[session_id].get(issue_type, 0)
        
        # Decision logic based on priority
        should_interrupt = False
        action = "warn"
        
        if priority <= 3:
            # CRITICAL - Interrupt immediately
            should_interrupt = True
            action = "interrupt"
        
        elif priority <= 6:
            # HIGH - Warn once, then interrupt
            if warning_count >= 1:
                should_interrupt = True
                action = "interrupt"
            else:
                action = "warn"
        
        elif priority <= 9:
            # MEDIUM - Warn twice, then interrupt
            if warning_count >= 2:
                should_interrupt = True
                action = "interrupt"
            else:
                action = "warn"
        
        else:
            # LOW - Warning only, never interrupt
            action = "warn"
        
        # Update warning history
        self.warning_history[session_id][issue_type] = warning_count + 1
        
        return {
            "should_interrupt": should_interrupt,
            "action": action,
            "reason": issue_type,
            "priority": priority,
            "severity": top_issue['severity'],
            "evidence": top_issue['evidence'],
            "warning_count": warning_count + 1,
            "all_issues": sorted_issues
        }
    
    def should_interrupt_based_on_content(
        self,
        partial_transcript: str,
        question_text: str,
        conversation_history: List[Dict],
        session_id: str
    ) -> Optional[Dict]:
        """
        Analyze transcript content for interruption triggers
        (Used when partial transcript is available via streaming STT)
        
        Args:
            partial_transcript: What user has said so far
            question_text: The question being answered
            conversation_history: Previous Q&A pairs
            session_id: Current session
            
        Returns:
            Interruption trigger data or None
        """
        
        # This will be implemented when streaming STT is added
        # For now, content analysis happens post-recording
        
        return None
    
    def generate_warning_message(self, issue_type: str, evidence: str) -> str:
        """
        Generate user-friendly warning message
        
        Args:
            issue_type: Type of issue detected
            evidence: Evidence for the issue
            
        Returns:
            Warning message string
        """
        
        warning_messages = {
            "EXCESSIVE_PAUSING": "You're taking long pauses - try to speak more fluidly",
            "HIGH_HESITATION": "You seem hesitant - take a breath and organize your thoughts",
            "LOW_CONFIDENCE": "Speak with more confidence - project your voice",
            "INCONSISTENT_DELIVERY": "Try to maintain a steady speaking pace",
            "SPEAKING_TOO_LONG": "Keep your answer concise - wrap up your point",
            "RAMBLING": "Focus on the question - avoid filler words",
            "OFF_TOPIC": "Stay focused on the question asked",
            "DODGING_QUESTION": "Address the question directly",
            "VAGUE_CLAIM": "Be more specific - give concrete examples",
            "LACK_OF_SPECIFICS": "Provide specific details and metrics"
        }
        
        base_message = warning_messages.get(issue_type, "Consider adjusting your approach")
        
        return f"{base_message}"
    
    def generate_interruption_phrase(self, reason: str) -> str:
        """
        Generate interruption phrase based on reason
        
        Args:
            reason: Interruption reason
            
        Returns:
            Interruption phrase
        """
        
        phrases = {
            "EXCESSIVE_PAUSING": "Let me stop you there - you seem to be struggling. Let me ask you something more specific.",
            "HIGH_HESITATION": "Hold on - let me help you focus. ",
            "RAMBLING": "I'm going to cut you off there - you're losing the thread.",
            "OFF_TOPIC": "Wait - that's not answering my question.",
            "DODGING_QUESTION": "Hold on - I need you to address the actual question.",
            "VAGUE_CLAIM": "Let me stop you there - I need specifics.",
            "SPEAKING_TOO_LONG": "I need to interrupt - let's get to the point.",
            "FALSE_CLAIM": "Stop right there - I need to clarify something.",
            "CONTRADICTION": "Hold on - that contradicts what you said earlier."
        }
        
        return phrases.get(reason, "Let me stop you for a moment.")
    
    def clear_session_warnings(self, session_id: str):
        """
        Clear warning history for a session (call when session ends)
        """
        if session_id in self.warning_history:
            del self.warning_history[session_id]

# ============================================
# SINGLETON INSTANCE
# ============================================

_analyzer_instance = None

def get_interruption_analyzer() -> InterruptionAnalyzer:
    """
    Get singleton instance of interruption analyzer
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = InterruptionAnalyzer()
    return _analyzer_instance

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("INTERRUPTION ANALYZER TEST")
    print("=" * 60)
    
    analyzer = get_interruption_analyzer()
    
    # Test 1: Excessive pausing (critical - should interrupt immediately)
    print("\n1. Test: Excessive pausing")
    audio_report = {
        "recording_duration": 15.0,
        "excessive_pause_count": 3,
        "detected_issues": [
            {
                "type": "EXCESSIVE_PAUSING",
                "severity": "critical",
                "evidence": "3 pauses over 3 seconds",
                "priority": 3
            }
        ]
    }
    
    result = analyzer.analyze_audio_patterns(audio_report, "test_session_1")
    print(f"   Should interrupt: {result['should_interrupt']}")
    print(f"   Action: {result['action']}")
    print(f"   Reason: {result['reason']}")
    print(f"   Evidence: {result['evidence']}")
    
    # Test 2: Speaking too long (low priority - warn only)
    print("\n2. Test: Speaking too long")
    audio_report = {
        "recording_duration": 95.0,
        "detected_issues": [
            {
                "type": "SPEAKING_TOO_LONG",
                "severity": "medium",
                "evidence": "Speaking for 95 seconds",
                "priority": 10
            }
        ]
    }
    
    result = analyzer.analyze_audio_patterns(audio_report, "test_session_2")
    print(f"   Should interrupt: {result['should_interrupt']}")
    print(f"   Action: {result['action']}")
    print(f"   Reason: {result['reason']}")
    
    # Test 3: Rambling - first time (warn), second time (interrupt)
    print("\n3. Test: Rambling progression")
    audio_report = {
        "recording_duration": 20.0,
        "detected_issues": [
            {
                "type": "HIGH_HESITATION",
                "severity": "high",
                "evidence": "45% of time spent pausing",
                "priority": 5
            }
        ]
    }
    
    # First occurrence
    result1 = analyzer.analyze_audio_patterns(audio_report, "test_session_3")
    print(f"   First time - Action: {result1['action']} (warning count: {result1['warning_count']})")
    
    # Second occurrence
    result2 = analyzer.analyze_audio_patterns(audio_report, "test_session_3")
    print(f"   Second time - Action: {result2['action']} (warning count: {result2['warning_count']})")
    
    # Test 4: Generate warning messages
    print("\n4. Test: Warning messages")
    for issue_type in ["EXCESSIVE_PAUSING", "RAMBLING", "SPEAKING_TOO_LONG"]:
        message = analyzer.generate_warning_message(issue_type, "test evidence")
        print(f"   {issue_type}: '{message}'")
    
    print("\n✅ Interruption analyzer test complete!")