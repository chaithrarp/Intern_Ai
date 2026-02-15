"""
Interruption Prompts
===================

Prompt templates for the intelligent interruption system
"""

# ============================================
# INTERRUPTION REASON PROMPTS
# ============================================

INTERRUPTION_PROMPTS = {
    "FALSE_CLAIM": {
        "phrase": "Hold on. I think there's an issue with what you just said.",
        "priority": 1,
        "severity": "critical"
    },
    "CONTRADICTION": {
        "phrase": "Wait - that contradicts what you said earlier. Can you clarify?",
        "priority": 2,
        "severity": "critical"
    },
    "EXCESSIVE_PAUSING": {
        "phrase": "Let me stop you there. You seem to be struggling with this question.",
        "priority": 3,
        "severity": "critical"
    },
    "OFF_TOPIC": {
        "phrase": "Hold on - we're getting off track. Let me refocus.",
        "priority": 4,
        "severity": "high"
    },
    "DODGING_QUESTION": {
        "phrase": "Let me interrupt. You're not answering the question I asked.",
        "priority": 5,
        "severity": "high"
    },
    "RAMBLING": {
        "phrase": "I'm going to stop you. Please get to the point.",
        "priority": 6,
        "severity": "high"
    },
    "VAGUE_CLAIM": {
        "phrase": "Hold on. I need more specific details, not generalizations.",
        "priority": 7,
        "severity": "medium"
    },
    "LACK_OF_SPECIFICS": {
        "phrase": "Wait. I need concrete examples, not abstract concepts.",
        "priority": 8,
        "severity": "medium"
    },
    "UNCERTAINTY": {
        "phrase": "Let me stop you. You sound uncertain - are you confident in this answer?",
        "priority": 9,
        "severity": "medium"
    },
    "SPEAKING_TOO_LONG": {
        "phrase": "I need to interrupt here. Please wrap up your point.",
        "priority": 10,
        "severity": "low"
    }
}

# ============================================
# WARNING MESSAGE TEMPLATES
# ============================================

WARNING_MESSAGES = {
    "EXCESSIVE_PAUSING": {
        "message": "You're taking long pauses",
        "icon": "⏸️",
        "color": "#ff4444",
        "severity": "critical"
    },
    "RAMBLING": {
        "message": "Wrap up your point",
        "icon": "🎯",
        "color": "#ff9800",
        "severity": "high"
    },
    "SPEAKING_TOO_LONG": {
        "message": "Keep it concise",
        "icon": "⏱️",
        "color": "#ffeb3b",
        "severity": "low"
    },
    "VAGUE_ANSWER": {
        "message": "Be more specific",
        "icon": "🎯",
        "color": "#ff9800",
        "severity": "high"
    },
    "LACK_OF_SPECIFICS": {
        "message": "Need concrete examples",
        "icon": "📋",
        "color": "#ff9800",
        "severity": "medium"
    }
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_interruption_phrase(reason):
    """Get the interruption phrase for a given reason"""
    return INTERRUPTION_PROMPTS.get(reason, {}).get("phrase", "Let me interrupt.")

def get_warning_config(reason):
    """Get the warning configuration for a given reason"""
    return WARNING_MESSAGES.get(reason, {
        "message": "Pay attention",
        "icon": "⚠️",
        "color": "#ff9800",
        "severity": "medium"
    })

def get_priority(reason):
    """Get the priority level for a given reason"""
    return INTERRUPTION_PROMPTS.get(reason, {}).get("priority", 99)

def get_severity(reason):
    """Get the severity level for a given reason"""
    return INTERRUPTION_PROMPTS.get(reason, {}).get("severity", "low")