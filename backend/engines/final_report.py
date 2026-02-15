"""
Final Report Generator
======================

Generates comprehensive final report at end of interview.

Creates:
- Overall performance summary
- Dimension breakdown (for radar chart)
- Skill heatmap
- Specific mistakes with evidence
- Recommended focus topics
- Next steps
"""

from typing import Dict, List
from datetime import datetime

from models.evaluation_models import (
    FinalReport,
    SkillAssessment,
    SessionEvaluation
)
from models.state_models import SessionState, RoundType
from llm_service import get_llm_response


class FinalReportGenerator:
    """
    Generates comprehensive final interview report
    """
    
    def __init__(self):
        pass
    
    def generate_report(
        self,
        session: SessionState
    ) -> FinalReport:
        """
        Generate final report for completed session
        
        Args:
            session: Completed SessionState object
        
        Returns:
            FinalReport object
        """
        
        print(f"\n{'='*60}")
        print(f"📊 GENERATING FINAL REPORT")
        print(f"   Session: {session.session_id}")
        print(f"   Questions: {len(session.conversation_history)}")
        print(f"{'='*60}")
        
        # Calculate final scores
        final_scores = session.calculate_average_scores()
        
        # Calculate overall score
        from models.evaluation_models import ScoringThresholds
        overall_score = int(sum(final_scores.values()) / len(final_scores))
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            session, overall_score
        )
        
        # Generate skill assessments
        skill_assessments = self._generate_skill_assessments(session)
        
        # Identify strong and weak areas
        strong_areas, improvement_areas = self._identify_areas(session, final_scores)
        
        # Extract critical mistakes
        critical_mistakes = self._extract_critical_mistakes(session)
        
        # Generate detailed feedback by dimension
        detailed_feedback = self._generate_detailed_feedback(session)
        
        # Generate round breakdown
        round_breakdown = self._generate_round_breakdown(session)
        
        # Generate recommended topics
        recommended_topics = self._generate_recommendations(
            session, improvement_areas
        )
        
        # Generate interruption summary
        interruption_summary = self._generate_interruption_summary(session)
        
        # Generate claim report
        claim_report = self._generate_claim_report(session)
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            improvement_areas, critical_mistakes
        )
        
        # Determine difficulty reached
        difficulty_reached = self._determine_difficulty_reached(session)
        
        # Calculate duration
        duration = (session.completed_at - session.started_at).total_seconds() if session.completed_at else 0
        
        # Build final report
        report = FinalReport(
            session_id=session.session_id,
            overall_score=overall_score,
            overall_assessment=overall_assessment,
            dimension_scores={k: int(v) for k, v in final_scores.items()},
            skill_assessments=skill_assessments,
            strong_areas=strong_areas,
            improvement_areas=improvement_areas,
            critical_mistakes=critical_mistakes,
            detailed_feedback=detailed_feedback,
            round_breakdown=round_breakdown,
            recommended_topics=recommended_topics,
            interruption_summary=interruption_summary,
            claim_report=claim_report,
            next_steps=next_steps,
            interview_duration=duration,
            questions_asked=len(session.conversation_history),
            phases_completed=[p.value for p in session.phases_completed],
            difficulty_reached=difficulty_reached
        )
        
        print(f"\n✅ Final report generated")
        print(f"   Overall Score: {overall_score}/100")
        print(f"   Strong Areas: {len(strong_areas)}")
        print(f"   Improvement Areas: {len(improvement_areas)}")
        
        return report
    
    
    def _generate_overall_assessment(
        self,
        session: SessionState,
        overall_score: int
    ) -> str:
        """Generate one-sentence overall assessment"""
        
        # Get top strength and weakness
        final_scores = session.average_scores
        
        top_dimension = max(final_scores.items(), key=lambda x: x[1])
        weak_dimension = min(final_scores.items(), key=lambda x: x[1])
        
        top_name = top_dimension[0].replace("_", " ").title()
        weak_name = weak_dimension[0].replace("_", " ").title()
        
        if overall_score >= 85:
            return f"Excellent performance overall. Strong {top_name}, minor improvements needed in {weak_name}."
        elif overall_score >= 70:
            return f"Good performance with strong {top_name}, but needs work on {weak_name}."
        elif overall_score >= 50:
            return f"Average performance. Focus on improving {weak_name} while maintaining {top_name}."
        else:
            return f"Needs significant improvement, especially in {weak_name}. {top_name} shows some potential."
    
    
    def _generate_skill_assessments(
        self,
        session: SessionState
    ) -> List[SkillAssessment]:
        """Generate skill assessments for heatmap"""
        
        assessments = []
        
        for dimension, scores in session.skill_scores.items():
            if not scores:
                continue
            
            avg_score = int(sum(scores) / len(scores))
            
            # Determine proficiency level
            if avg_score >= 85:
                proficiency = "expert"
            elif avg_score >= 70:
                proficiency = "advanced"
            elif avg_score >= 50:
                proficiency = "intermediate"
            else:
                proficiency = "beginner"
            
            # Extract evidence from conversation
            evidence = self._extract_evidence_for_skill(
                session, dimension
            )
            
            assessments.append(SkillAssessment(
                skill_name=dimension.replace("_", " ").title(),
                proficiency_level=proficiency,
                evidence=evidence,
                score=avg_score
            ))
        
        return assessments
    
    
    def _extract_evidence_for_skill(
        self,
        session: SessionState,
        dimension: str
    ) -> List[str]:
        """Extract evidence quotes for a skill"""
        
        evidence = []
        
        for qa in session.conversation_history:
            eval_data = qa.get("evaluation", {})
            score_details = eval_data.get("score_details", [])
            
            for detail in score_details:
                if detail.get("dimension") == dimension:
                    evidence_text = detail.get("evidence")
                    if evidence_text and evidence_text not in evidence:
                        evidence.append(evidence_text)
                    
                    if len(evidence) >= 3:
                        return evidence
        
        return evidence[:3]
    
    
    def _identify_areas(
        self,
        session: SessionState,
        final_scores: Dict[str, float]
    ) -> tuple:
        """Identify strong areas and improvement areas"""
        
        strong_areas = []
        improvement_areas = []
        
        for dimension, score in final_scores.items():
            name = dimension.replace("_", " ").title()
            
            if score >= 75:
                strong_areas.append(name)
            elif score < 60:
                improvement_areas.append(name)
        
        # Add phase-specific insights
        for phase in session.phases_completed:
            phase_avg = session.get_phase_average_score(phase)
            phase_name = phase.value.replace("_", " ").title()
            
            if phase_avg >= 75 and phase_name not in strong_areas:
                strong_areas.append(f"{phase_name} Phase")
            elif phase_avg < 60 and phase_name not in improvement_areas:
                improvement_areas.append(f"{phase_name} Phase")
        
        return strong_areas, improvement_areas
    
    
    def _extract_critical_mistakes(
        self,
        session: SessionState
    ) -> List[Dict[str, str]]:
        """Extract specific mistakes with evidence"""
        
        mistakes = []
        
        # From red flags
        for flag in session.red_flags:
            mistakes.append({
                "mistake": flag["description"],
                "question": f"Q{flag['question_id']}",
                "impact": "Critical accuracy issue"
            })
        
        # From low-scoring answers
        for qa in session.conversation_history:
            eval_data = qa.get("evaluation", {})
            overall_score = eval_data.get("overall_score", 0)
            
            if overall_score < 50:
                weaknesses = eval_data.get("weaknesses", [])
                if weaknesses:
                    mistakes.append({
                        "mistake": weaknesses[0],
                        "question": f"Q{qa['question_id']}",
                        "impact": f"Low score: {overall_score}/100"
                    })
        
        return mistakes[:5]  # Top 5 mistakes
    
    
    def _generate_detailed_feedback(
        self,
        session: SessionState
    ) -> Dict[str, List[str]]:
        """Generate detailed feedback by category"""
        
        feedback = {
            "technical_depth": [],
            "concept_accuracy": [],
            "structured_thinking": [],
            "communication": [],
            "confidence": []
        }
        
        # Aggregate feedback from all evaluations
        for qa in session.conversation_history:
            eval_data = qa.get("evaluation", {})
            
            # Add strengths
            for strength in eval_data.get("strengths", [])[:2]:
                feedback_key = self._categorize_feedback(strength)
                feedback_text = f"✅ {strength}"
                if feedback_text not in feedback.get(feedback_key, []):
                    feedback[feedback_key].append(feedback_text)
            
            # Add weaknesses
            for weakness in eval_data.get("weaknesses", [])[:2]:
                feedback_key = self._categorize_feedback(weakness)
                feedback_text = f"❌ {weakness}"
                if feedback_text not in feedback.get(feedback_key, []):
                    feedback[feedback_key].append(feedback_text)
        
        # Limit to 5 items per category
        for key in feedback:
            feedback[key] = feedback[key][:5]
        
        return feedback
    
    
    def _categorize_feedback(self, text: str) -> str:
        """Categorize feedback into appropriate dimension"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["technical", "depth", "detail", "architecture", "system"]):
            return "technical_depth"
        elif any(word in text_lower for word in ["accurate", "correct", "wrong", "error", "mistake"]):
            return "concept_accuracy"
        elif any(word in text_lower for word in ["structure", "star", "organized", "logical"]):
            return "structured_thinking"
        elif any(word in text_lower for word in ["clear", "filler", "rambling", "concise", "explain"]):
            return "communication"
        else:
            return "confidence"
    
    
    def _generate_round_breakdown(
        self,
        session: SessionState
    ) -> Dict[str, Dict]:
        """Generate performance breakdown by round"""
        
        breakdown = {}
        
        # Group by round type
        rounds = {
            "hr": [],
            "technical": [],
            "system_design": []
        }
        
        for qa in session.conversation_history:
            round_type = qa.get("round_type")
            if round_type in rounds:
                rounds[round_type].append(qa)
        
        # Calculate stats for each round
        for round_type, questions in rounds.items():
            if not questions:
                continue
            
            scores = [q.get("evaluation", {}).get("overall_score", 0) for q in questions]
            avg_score = int(sum(scores) / len(scores)) if scores else 0
            
            # Collect strengths and weaknesses
            strengths = []
            weaknesses = []
            
            for q in questions:
                eval_data = q.get("evaluation", {})
                strengths.extend(eval_data.get("strengths", []))
                weaknesses.extend(eval_data.get("weaknesses", []))
            
            # Deduplicate and limit
            strengths = list(set(strengths))[:3]
            weaknesses = list(set(weaknesses))[:3]
            
            breakdown[round_type] = {
                "score": avg_score,
                "questions_asked": len(questions),
                "strengths": strengths,
                "weaknesses": weaknesses
            }
        
        return breakdown
    
    
    def _generate_recommendations(
        self,
        session: SessionState,
        improvement_areas: List[str]
    ) -> List[str]:
        """Generate specific study/practice recommendations"""
        
        recommendations = []
        
        # Based on improvement areas
        recommendation_map = {
            "Technical Depth": "Study system design patterns and practice explaining technical concepts in detail",
            "Concept Accuracy": "Review fundamental CS concepts and verify your understanding with practice problems",
            "Structured Thinking": "Practice the STAR method with specific examples and measurable outcomes",
            "Communication Clarity": "Record yourself answering and work on reducing filler words",
            "Confidence & Consistency": "Practice mock interviews to build confidence and maintain consistency"
        }
        
        for area in improvement_areas:
            if area in recommendation_map:
                recommendations.append(recommendation_map[area])
        
        # Based on red flags
        if session.red_flags:
            recommendations.append("Verify all claims before interviews - inconsistencies were detected")
        
        # Based on interruptions
        if session.total_interruptions > 2:
            recommendations.append("Work on staying concise and on-topic to avoid interruptions")
        
        return recommendations[:5]
    
    
    def _generate_interruption_summary(
        self,
        session: SessionState
    ) -> Dict:
        """Generate interruption analysis summary"""
        
        if not session.interruptions:
            return {
                "total_interruptions": 0,
                "primary_trigger": "none",
                "recovery_quality": "n/a",
                "notes": "No interruptions during interview"
            }
        
        # Count triggers
        triggers = {}
        for interrupt in session.interruptions:
            reason = interrupt.get("reason", "unknown")
            triggers[reason] = triggers.get(reason, 0) + 1
        
        primary_trigger = max(triggers.items(), key=lambda x: x[1])[0] if triggers else "unknown"
        
        # Assess recovery quality (simplified)
        recovery_quality = "good" if session.total_interruptions <= 2 else "needs_work"
        
        return {
            "total_interruptions": session.total_interruptions,
            "primary_trigger": primary_trigger,
            "recovery_quality": recovery_quality,
            "trigger_breakdown": triggers,
            "notes": f"Most common trigger: {primary_trigger}. Focus on staying concise and accurate."
        }
    
    
    def _generate_claim_report(
        self,
        session: SessionState
    ) -> Dict:
        """Generate claim verification report"""
        
        total_claims = len(session.extracted_claims)
        unverified = session.unverified_claims
        verified = session.verified_claims
        red_flags = [flag for flag in session.red_flags if flag.get("type") == "claim"]
        
        return {
            "total_claims": total_claims,
            "verified": len(verified),
            "unverified": unverified[:3],  # Show top 3
            "red_flags": [flag["description"] for flag in red_flags[:3]]
        }
    
    
    def _generate_next_steps(
        self,
        improvement_areas: List[str],
        critical_mistakes: List[Dict]
    ) -> List[str]:
        """Generate actionable next steps"""
        
        steps = []
        
        # Based on improvement areas
        if "Communication Clarity" in improvement_areas:
            steps.append("Record 3 practice answers and count filler words - aim for <2 per minute")
        
        if "Structured Thinking" in improvement_areas:
            steps.append("Prepare 5 STAR stories with specific metrics before your next interview")
        
        if "Technical Depth" in improvement_areas:
            steps.append("Practice explaining 3 complex technical concepts to a non-technical friend")
        
        # Based on mistakes
        if critical_mistakes:
            steps.append("Review and verify all claims from your resume before interviews")
        
        # General steps
        steps.append("Take at least 2 more mock interviews focusing on your weak areas")
        steps.append("Join interview practice communities for peer feedback")
        
        return steps[:5]
    
    
    def _determine_difficulty_reached(
        self,
        session: SessionState
    ) -> str:
        """Determine highest difficulty level reached"""
        
        difficulties = ["easy", "medium", "hard"]
        max_difficulty = "easy"
        
        for qa in session.conversation_history:
            # Check if difficulty info is stored (may not be in all QAs)
            difficulty = qa.get("difficulty", "medium")
            if difficulty in difficulties:
                if difficulties.index(difficulty) > difficulties.index(max_difficulty):
                    max_difficulty = difficulty
        
        return max_difficulty


# ============================================
# SINGLETON INSTANCE
# ============================================

_report_generator = None

def get_final_report_generator() -> FinalReportGenerator:
    """Get singleton instance"""
    global _report_generator
    if _report_generator is None:
        _report_generator = FinalReportGenerator()
    return _report_generator


# Alias for backward compatibility
get_report_generator = get_final_report_generator


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("FINAL REPORT GENERATOR TEST")
    print("=" * 60)
    
    from models.state_models import SessionState, InterviewPhase, RoundType
    
    # Create test session
    test_session = SessionState(
        session_id="test_001",
        current_phase=InterviewPhase.COMPLETED,
        phases_completed=[
            InterviewPhase.RESUME_DEEP_DIVE,
            InterviewPhase.CORE_SKILL_ASSESSMENT
        ]
    )
    
    # Add mock conversation history
    test_session.conversation_history = [
        {
            "question_id": 1,
            "question": "Test question",
            "answer": "Test answer",
            "round_type": "hr",
            "evaluation": {
                "overall_score": 75,
                "strengths": ["Good structure", "Specific examples"],
                "weaknesses": ["Lacked metrics"],
                "score_details": []
            }
        }
    ]
    
    # Add scores
    test_session.skill_scores = {
        "technical_depth": [70, 75, 80],
        "concept_accuracy": [75, 78, 82],
        "structured_thinking": [80, 82, 85],
        "communication_clarity": [68, 70, 72],
        "confidence_consistency": [65, 68, 70]
    }
    
    test_session.calculate_average_scores()
    test_session.completed_at = datetime.now()
    
    generator = get_final_report_generator()
    report = generator.generate_report(test_session)
    
    print(f"\n📊 Generated Report:")
    print(f"   Overall Score: {report.overall_score}/100")
    print(f"   Assessment: {report.overall_assessment}")
    print(f"   Strong Areas: {', '.join(report.strong_areas)}")
    print(f"   Improvement Areas: {', '.join(report.improvement_areas)}")
    print(f"   Recommendations: {len(report.recommended_topics)}")
    
    print("\n" + "=" * 60)