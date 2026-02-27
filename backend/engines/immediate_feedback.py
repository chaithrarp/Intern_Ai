"""
Immediate Feedback Generator
=============================

Generates quick, conversational feedback shown right after each answer.

CHANGED: Now produces message-based feedback — e.g.:
  "Your answer lacked technical depth — you didn't discuss trade-offs or complexity."
  "You paused frequently and used filler words, which reduced clarity."

Instead of just returning a score number.
"""

from typing import Dict, List
from models.evaluation_models import AnswerEvaluation


class ImmediateFeedbackGenerator:
    """
    Generates immediate post-answer feedback as conversational messages.
    """

    def __init__(self):
        pass

    def generate_feedback(
        self,
        evaluation: AnswerEvaluation,
        round_type: str
    ) -> Dict:
        """
        Generate immediate feedback as human-readable messages.

        Returns:
            Dictionary with:
              - overall_score
              - performance_level
              - emoji
              - headline: one-line summary ("Strong technical answer")
              - messages: list of specific conversational observations
              - key_strength: best thing they did (string)
              - key_weakness: main thing to fix (string)
              - red_flags: list of hard issues
              - encouragement: closing line
        """

        print(f"\n💬 Generating immediate feedback (score={evaluation.overall_score})...")

        performance_level = self._get_performance_level(evaluation.overall_score)
        emoji = self._get_emoji(evaluation.overall_score)
        headline = self._get_headline(evaluation.overall_score, round_type)

        # Build specific observation messages
        messages = self._build_observation_messages(evaluation, round_type)

        key_strength = evaluation.strengths[0] if evaluation.strengths else None
        key_weakness = evaluation.weaknesses[0] if evaluation.weaknesses else None

        encouragement = self._get_encouragement(evaluation.overall_score, round_type)

        feedback = {
            "overall_score": evaluation.overall_score,
            "performance_level": performance_level,
            "emoji": emoji,
            "headline": headline,
            "messages": messages,           # ← NEW: list of specific observations
            "key_strength": key_strength,
            "key_weakness": key_weakness,
            "red_flags": evaluation.red_flags[:2] if evaluation.red_flags else [],
            "has_critical_issues": len(evaluation.red_flags) > 0,
            "encouragement": encouragement,
            # Legacy fields kept for backward compatibility
            "overall_assessment": performance_level,
            "strengths": [{"text": s, "icon": "✅"} for s in (evaluation.strengths or [])[:2]],
            "improvements": self._build_improvement_list(evaluation),
        }

        print(f"   ✅ Feedback generated: {headline}")
        return feedback

    # ──────────────────────────────────────────────────────────────
    # CORE MESSAGE BUILDER
    # ──────────────────────────────────────────────────────────────

    def _build_observation_messages(self, evaluation: AnswerEvaluation, round_type: str) -> List[str]:
        """
        Build a list of specific, conversational observations based on
        the score breakdown and detected issues.

        Examples:
          "You lacked technical depth — no mention of time complexity or trade-offs."
          "Your answer was well-structured and used specific examples."
          "You contradicted an earlier answer about your team size."
        """
        messages = []
        scores = evaluation.scores or {}

        # ── Dimension-specific messages ──────────────────────────
        tech_depth = scores.get("technical_depth", -1)
        concept_acc = scores.get("concept_accuracy", -1)
        structured = scores.get("structured_thinking", -1)
        clarity = scores.get("communication_clarity", -1)
        confidence = scores.get("confidence_consistency", -1)

        # Technical depth
        if tech_depth >= 0:
            if tech_depth >= 80:
                messages.append("Your answer showed strong technical depth with specific details.")
            elif tech_depth >= 60:
                messages.append("Decent technical depth, but you could go deeper on trade-offs or edge cases.")
            elif tech_depth >= 40:
                if round_type == "technical":
                    messages.append("Your answer lacked technical depth — try to discuss complexity, trade-offs, or concrete implementation details.")
                elif round_type == "system_design":
                    messages.append("The architecture answer was surface-level — mention specific components, bottlenecks, or scaling strategies.")
                else:
                    messages.append("Add more specific details to strengthen your answer.")
            else:
                if round_type == "technical":
                    messages.append("Very limited technical depth — core concepts were missing or incorrect.")
                else:
                    messages.append("The answer was too brief and lacked supporting details.")

        # Concept accuracy
        if concept_acc >= 0:
            if concept_acc < 50:
                messages.append("Some concepts were inaccurate or misused — review the fundamentals here.")
            elif concept_acc >= 85:
                messages.append("Concepts were accurate and well-applied.")

        # Structured thinking
        if structured >= 0:
            if round_type == "hr" and structured < 55:
                messages.append("Your answer didn't follow the STAR format clearly — try to structure as Situation → Task → Action → Result.")
            elif round_type in ("technical", "system_design") and structured < 55:
                messages.append("Your answer jumped around — try to structure your thinking before diving into details.")
            elif structured >= 80:
                messages.append("Well-structured and easy to follow.")

        # Communication clarity
        if clarity >= 0:
            if clarity < 50:
                messages.append("Your answer was hard to follow — aim for shorter sentences and clearer transitions.")
            elif clarity >= 80:
                messages.append("Communicated clearly and concisely.")

        # Confidence/consistency
        if confidence >= 0:
            if confidence < 45:
                messages.append("You seemed uncertain — avoid excessive hedging like 'I think maybe' or 'I'm not sure but'.")
            elif confidence >= 80:
                messages.append("Answered with confidence and consistency.")

        # ── Red flag messages ─────────────────────────────────────
        for flag in (evaluation.red_flags or [])[:2]:
            if "contradiction" in flag.lower():
                messages.append(f"⚠️ Contradiction detected: {flag}")
            elif "suspicious" in flag.lower() or "false claim" in flag.lower():
                messages.append(f"⚠️ Unverified claim: {flag}")

        # ── Positive reinforcement if doing well ──────────────────
        if evaluation.overall_score >= 80 and not messages:
            messages.append("Solid all-round answer — strong depth, clarity, and accuracy.")

        # Fallback
        if not messages:
            if evaluation.overall_score >= 70:
                messages.append("Good answer overall. Small improvements to depth will push you further.")
            elif evaluation.overall_score >= 50:
                messages.append("Average answer. Focus on being more specific and structured.")
            else:
                messages.append("This answer needs work. Review the key concepts and try to give concrete examples.")

        return messages[:3]  # Cap at 3 messages to keep the popup clean

    def _build_improvement_list(self, evaluation: AnswerEvaluation) -> List[Dict]:
        """Build improvements list (legacy format for compatibility)"""
        improvements = []
        for detail in (evaluation.score_details or []):
            if detail.improvement and len(improvements) < 2:
                improvements.append({
                    "dimension": self._format_dimension_name(detail.dimension),
                    "suggestion": detail.improvement,
                    "icon": "💡"
                })
        if len(improvements) < 2 and evaluation.weaknesses:
            for weakness in evaluation.weaknesses[:2]:
                if len(improvements) >= 2:
                    break
                improvements.append({
                    "dimension": "General",
                    "suggestion": weakness,
                    "icon": "💡"
                })
        return improvements

    # ──────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────

    def _get_performance_level(self, score: int) -> str:
        if score >= 85: return "Excellent"
        if score >= 70: return "Good"
        if score >= 50: return "Average"
        return "Needs Improvement"

    def _get_emoji(self, score: int) -> str:
        if score >= 85: return "🌟"
        if score >= 70: return "👍"
        if score >= 50: return "🤔"
        return "📚"

    def _get_headline(self, score: int, round_type: str) -> str:
        """One-line summary tailored to round type and score"""
        round_labels = {
            "hr": "behavioral answer",
            "technical": "technical answer",
            "system_design": "design answer"
        }
        label = round_labels.get(round_type, "answer")

        if score >= 85:
            return f"Excellent {label}"
        if score >= 70:
            return f"Good {label} — minor gaps to address"
        if score >= 50:
            return f"Average {label} — several areas to improve"
        return f"Weak {label} — key concepts were missing"

    def _get_encouragement(self, score: int, round_type: str) -> str:
        if score >= 85:
            return "Keep this up — you're performing at a strong level."
        if score >= 70:
            return "Good foundation. Address the gaps above to reach the next level."
        if score >= 50:
            return "You're on the right track. Be more specific and structured."
        return "Review the feedback carefully — focus on the biggest gap first."

    def _format_dimension_name(self, dimension: str) -> str:
        name_map = {
            "technical_depth": "Technical Depth",
            "concept_accuracy": "Concept Accuracy",
            "structured_thinking": "Structured Thinking",
            "communication_clarity": "Communication Clarity",
            "confidence_consistency": "Confidence & Consistency",
            "general": "General"
        }
        return name_map.get(dimension, dimension.replace("_", " ").title())


# ============================================
# SINGLETON
# ============================================

_feedback_generator = None

def get_immediate_feedback_generator() -> ImmediateFeedbackGenerator:
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = ImmediateFeedbackGenerator()
    return _feedback_generator