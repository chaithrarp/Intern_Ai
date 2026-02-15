"""
Engines Module
==============

Contains all analysis and orchestration engines for the interview system.
"""

# Import only what exists, skip what doesn't
import importlib.util
import sys
from pathlib import Path

engines_dir = Path(__file__).parent


def safe_import(module_name, *names):
    """Safely import names from a module, return None if not found"""
    try:
        module = importlib.import_module(f'.{module_name}', package='engines')
        result = {}
        for name in names:
            result[name] = getattr(module, name, None)
        return result
    except (ImportError, AttributeError) as e:
        print(f"⚠️  Optional import failed: {module_name}.{names} - {e}")
        return {name: None for name in names}


# Core orchestration
try:
    from .interview_orchestrator import InterviewOrchestrator, get_interview_orchestrator
except ImportError as e:
    print(f"⚠️  Could not import interview_orchestrator: {e}")
    InterviewOrchestrator = None
    get_interview_orchestrator = None

# Answer analysis
try:
    from .answer_analyzer import AnswerAnalyzer, get_answer_analyzer
except ImportError as e:
    print(f"⚠️  Could not import answer_analyzer: {e}")
    AnswerAnalyzer = None
    get_answer_analyzer = None

try:
    from .claim_extractor import ClaimExtractor
except ImportError as e:
    print(f"⚠️  Could not import claim_extractor: {e}")
    ClaimExtractor = None

try:
    from .claim_analyzer import ClaimAnalyzer
except ImportError:
    ClaimAnalyzer = None

# Immediate feedback
try:
    from .immediate_feedback import ImmediateFeedbackGenerator, get_immediate_feedback_generator
except ImportError as e:
    print(f"⚠️  Could not import immediate_feedback: {e}")
    ImmediateFeedbackGenerator = None
    get_immediate_feedback_generator = None

# Final report - make it optional
try:
    from .final_report import get_report_generator
except ImportError:
    print(f"⚠️  Could not import get_report_generator from final_report (optional)")
    get_report_generator = None

# Interruption analyzer - use the renamed one
try:
    from .interruption_analyzer import (
        EnhancedInterruptionAnalyzer,
        get_enhanced_interruption_analyzer
    )
    # Create aliases for backward compatibility
    InterruptionAnalyzer = EnhancedInterruptionAnalyzer
    get_interruption_analyzer = get_enhanced_interruption_analyzer
except ImportError as e:
    print(f"❌ Could not import interruption_analyzer: {e}")
    InterruptionAnalyzer = None
    get_interruption_analyzer = None
    EnhancedInterruptionAnalyzer = None
    get_enhanced_interruption_analyzer = None

# Follow-up generator
try:
    from .followup_generator import FollowUpGenerator, get_followup_generator
except ImportError:
    print(f"⚠️  Could not import followup_generator (optional)")
    FollowUpGenerator = None
    get_followup_generator = None

# Warning system
try:
    from .live_warning_generator import get_warning_generator
except ImportError:
    get_warning_generator = None

# Decision engine
try:
    from .interruption_decision import get_interruption_decision_engine
except ImportError:
    get_interruption_decision_engine = None


# Export what's available
__all__ = [
    # Orchestration
    'InterviewOrchestrator',
    'get_interview_orchestrator',
    
    # Analysis
    'AnswerAnalyzer',
    'get_answer_analyzer',
    'ClaimExtractor',
    'ClaimAnalyzer',
    
    # Feedback
    'ImmediateFeedbackGenerator',
    'get_immediate_feedback_generator',
    'get_report_generator',
    
    # Interruptions
    'InterruptionAnalyzer',
    'get_interruption_analyzer',
    'EnhancedInterruptionAnalyzer',
    'get_enhanced_interruption_analyzer',
    
    # Follow-ups
    'FollowUpGenerator',
    'get_followup_generator',
    
    # Warnings
    'get_warning_generator',
]