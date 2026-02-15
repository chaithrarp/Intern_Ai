"""
Immediate Feedback Generator
=============================

Generates quick, actionable feedback shown right after each answer.

This is NOT the final report - it's immediate guidance shown after transcription.
"""

from typing import Dict, List
from models.evaluation_models import AnswerEvaluation


class ImmediateFeedbackGenerator:
    """
    Generates immediate post-answer feedback
    
    Shows:
    - Quick score summary
    - Top 2 strengths
    - Top 2 improvements
    - Any red flags
    """
    
    def __init__(self):
        pass
    
    def generate_feedback(
        self,
        evaluation: AnswerEvaluation,
        round_type: str
    ) -> Dict:
        """
        Generate immediate feedback from evaluation
        
        Args:
            evaluation: AnswerEvaluation object
            round_type: Which round (hr, technical, system_design)
        
        Returns:
            Dictionary with feedback data for UI
        """
        
        print(f"\n💬 Generating immediate feedback...")
        
        # Overall assessment
        overall_assessment = self._get_overall_assessment(evaluation.overall_score)
        
        # Key dimension for this round
        key_dimension = self._get_key_dimension(round_type)
        key_score = evaluation.scores.get(key_dimension, 0)
        
        # Top strengths (limit to 2)
        strengths = evaluation.strengths[:2] if len(evaluation.strengths) >= 2 else evaluation.strengths
        
        # Top improvements (limit to 2)
        improvements = []
        for detail in evaluation.score_details:
            if detail.improvement and len(improvements) < 2:
                improvements.append({
                    "dimension": detail.dimension,
                    "suggestion": detail.improvement
                })
        
        # Add generic improvements if less than 2
        if len(improvements) < 2 and evaluation.weaknesses:
            for weakness in evaluation.weaknesses[:2]:
                if len(improvements) >= 2:
                    break
                improvements.append({
                    "dimension": "general",
                    "suggestion": weakness
                })
        
        # Red flags
        has_red_flags = len(evaluation.red_flags) > 0
        
        # Build feedback object
        feedback = {
            "overall_score": evaluation.overall_score,
            "overall_assessment": overall_assessment,
            "key_dimension": {
                "name": self._format_dimension_name(key_dimension),
                "score": key_score,
                "importance": f"Critical for {round_type.upper()} round"
            },
            "strengths": [
                {"text": s, "icon": "✅"} for s in strengths
            ],
            "improvements": [
                {
                    "dimension": self._format_dimension_name(imp["dimension"]),
                    "suggestion": imp["suggestion"],
                    "icon": "💡"
                }
                for imp in improvements
            ],
            "red_flags": [
                {"text": flag, "icon": "🚨"} for flag in evaluation.red_flags
            ] if has_red_flags else [],
            "has_critical_issues": has_red_flags,
            "encouragement": self._get_encouragement(evaluation.overall_score, round_type)
        }
        
        print(f"   ✅ Feedback generated: {overall_assessment}")
        
        return feedback
    
    
    def _get_overall_assessment(self, score: int) -> str:
        """Get overall assessment text"""
        if score >= 85:
            return "Excellent Answer"
        elif score >= 70:
            return "Good Answer"
        elif score >= 50:
            return "Average Answer"
        else:
            return "Needs Improvement"
    
    
    def _get_key_dimension(self, round_type: str) -> str:
        """Get the most important dimension for this round"""
        key_dimensions = {
            "hr": "structured_thinking",  # STAR method
            "technical": "technical_depth",  # Deep understanding
            "system_design": "technical_depth"  # Architecture thinking
        }
        return key_dimensions.get(round_type, "technical_depth")
    
    
    def _format_dimension_name(self, dimension: str) -> str:
        """Format dimension name for display"""
        name_map = {
            "technical_depth": "Technical Depth",
            "concept_accuracy": "Concept Accuracy",
            "structured_thinking": "Structured Thinking",
            "communication_clarity": "Communication Clarity",
            "confidence_consistency": "Confidence & Consistency",
            "general": "General"
        }
        return name_map.get(dimension, dimension.replace("_", " ").title())
    
    
    def _get_encouragement(self, score: int, round_type: str) -> str:
        """Get encouraging message based on score"""
        
        if score >= 85:
            messages = [
                "Outstanding! You're demonstrating strong skills.",
                "Excellent work! Keep this level of detail.",
                "Great answer! You're showing deep understanding."
            ]
        elif score >= 70:
            messages = [
                "Good job! A few tweaks will make it even better.",
                "Solid answer. Focus on the improvements noted.",
                "Nice work! Small refinements will boost your score."
            ]
        elif score >= 50:
            messages = [
                "Decent start. Work on the areas highlighted above.",
                "You're on the right track. Address the key improvements.",
                "Not bad. Focus on the feedback to improve further."
            ]
        else:
            messages = [
                "Let's work on this together. Review the suggestions carefully.",
                "This needs improvement. Focus on the critical points above.",
                "Keep trying. Pay attention to the feedback provided."
            ]
        
        import random
        return random.choice(messages)


# ============================================
# SINGLETON INSTANCE
# ============================================

_feedback_generator = None

def get_immediate_feedback_generator() -> ImmediateFeedbackGenerator:
    """Get singleton instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = ImmediateFeedbackGenerator()
    return _feedback_generator


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("IMMEDIATE FEEDBACK GENERATOR TEST")
    print("=" * 60)
    
    from models.evaluation_models import AnswerEvaluation, EvaluationScore
    
    # Test evaluation
    test_eval = AnswerEvaluation(
        question_id=1,
        round_type="technical",
        scores={
            "technical_depth": 82,
            "concept_accuracy": 78,
            "structured_thinking": 75,
            "communication_clarity": 70,
            "confidence_consistency": 72
        },
        score_details=[
            EvaluationScore(
                dimension="technical_depth",
                score=82,
                evidence="Explained caching strategies in detail",
                improvement="Could discuss cache invalidation patterns"
            ),
            EvaluationScore(
                dimension="concept_accuracy",
                score=78,
                evidence="Correct understanding of Redis",
                improvement=None
            )
        ],
        overall_score=76,
        strengths=[
            "Detailed explanation of Redis internals",
            "Mentioned trade-offs between different caching strategies",
            "Good use of concrete examples"
        ],
        weaknesses=[
            "Didn't discuss cache invalidation",
            "Could elaborate on memory management"
        ],
        red_flags=[],
        requires_followup=False,
        difficulty_adjustment="increase"
    )
    
    generator = get_immediate_feedback_generator()
    feedback = generator.generate_feedback(test_eval, "technical")
    
    print(f"\n📊 Generated Feedback:")
    print(f"\n   Overall: {feedback['overall_assessment']} ({feedback['overall_score']}/100)")
    
    print(f"\n   Key Dimension:")
    print(f"   - {feedback['key_dimension']['name']}: {feedback['key_dimension']['score']}/100")
    
    print(f"\n   Strengths:")
    for strength in feedback['strengths']:
        print(f"   {strength['icon']} {strength['text']}")
    
    print(f"\n   Improvements:")
    for imp in feedback['improvements']:
        print(f"   {imp['icon']} [{imp['dimension']}] {imp['suggestion']}")
    
    print(f"\n   {feedback['encouragement']}")
    
    print("\n" + "=" * 60)