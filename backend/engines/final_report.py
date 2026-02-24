"""
Final Report Generator
======================

Generates comprehensive final report at end of interview.
"""

from typing import Dict, List, Optional
from datetime import datetime

from models.evaluation_models import (
    FinalReport,
    SkillAssessment,
    SessionEvaluation
)
from models.state_models import SessionState, RoundType
from llm_service import get_llm_response


class FinalReportGenerator:

    def __init__(self):
        pass

    def generate_report(
        self,
        session: SessionState,
        session_eval: Optional[SessionEvaluation] = None   # ← optional, kept for compat
    ) -> FinalReport:
        """Generate final report for completed session."""

        print(f"\n{'='*60}")
        print(f"📊 GENERATING FINAL REPORT")
        print(f"   Session: {session.session_id}")
        print(f"   Questions: {len(session.conversation_history)}")
        print(f"{'='*60}")

        final_scores = session.calculate_average_scores()
        overall_score = int(sum(final_scores.values()) / len(final_scores)) if final_scores else 0

        overall_assessment = self._generate_overall_assessment(session, overall_score)
        skill_assessments  = self._generate_skill_assessments(session)
        strong_areas, improvement_areas = self._identify_areas(session, final_scores)
        critical_mistakes  = self._extract_critical_mistakes(session)
        detailed_feedback  = self._generate_detailed_feedback(session)
        round_breakdown    = self._generate_round_breakdown(session)
        recommended_topics = self._generate_recommendations(session, improvement_areas)
        interruption_summary = self._generate_interruption_summary(session)
        claim_report       = self._generate_claim_report(session)
        next_steps         = self._generate_next_steps(improvement_areas, critical_mistakes)
        difficulty_reached = self._determine_difficulty_reached(session)

        duration = (
            (session.completed_at - session.started_at).total_seconds()
            if session.completed_at else 0
        )

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

        print(f"✅ Final report generated — Overall: {overall_score}/100")
        return report

    # ── Helpers ──────────────────────────────────────────────────

    def _generate_overall_assessment(self, session: SessionState, overall_score: int) -> str:
        final_scores = session.average_scores
        if not final_scores:
            return "Interview completed."
        top_dim  = max(final_scores.items(), key=lambda x: x[1])
        weak_dim = min(final_scores.items(), key=lambda x: x[1])
        top_name  = top_dim[0].replace("_", " ").title()
        weak_name = weak_dim[0].replace("_", " ").title()

        if overall_score >= 85:
            return f"Excellent performance overall. Strong {top_name}, minor improvements needed in {weak_name}."
        elif overall_score >= 70:
            return f"Good performance with strong {top_name}, but needs work on {weak_name}."
        elif overall_score >= 50:
            return f"Average performance. Focus on improving {weak_name} while maintaining {top_name}."
        else:
            return f"Needs significant improvement, especially in {weak_name}. {top_name} shows some potential."

    def _generate_skill_assessments(self, session: SessionState) -> List[SkillAssessment]:
        assessments = []
        for dimension, scores in session.skill_scores.items():
            if not scores:
                continue
            avg_score = int(sum(scores) / len(scores))
            if avg_score >= 85:   proficiency = "expert"
            elif avg_score >= 70: proficiency = "advanced"
            elif avg_score >= 50: proficiency = "intermediate"
            else:                 proficiency = "beginner"

            evidence = self._extract_evidence_for_skill(session, dimension)
            assessments.append(SkillAssessment(
                skill_name=dimension.replace("_", " ").title(),
                proficiency_level=proficiency,
                evidence=evidence,
                score=avg_score
            ))
        return assessments

    def _extract_evidence_for_skill(self, session: SessionState, dimension: str) -> List[str]:
        evidence = []
        for qa in session.conversation_history:
            eval_data    = qa.get("evaluation", {})
            score_details = eval_data.get("score_details", [])
            for detail in score_details:
                if detail.get("dimension") == dimension:
                    ev = detail.get("evidence")
                    if ev and ev not in evidence:
                        evidence.append(ev)
                    if len(evidence) >= 3:
                        return evidence
        return evidence[:3]

    def _identify_areas(self, session: SessionState, final_scores: Dict[str, float]):
        strong_areas = []
        improvement_areas = []
        for dimension, score in final_scores.items():
            name = dimension.replace("_", " ").title()
            if score >= 75:
                strong_areas.append(name)
            elif score < 60:
                improvement_areas.append(name)

        for phase in session.phases_completed:
            phase_avg  = session.get_phase_average_score(phase)
            phase_name = phase.value.replace("_", " ").title()
            if phase_avg >= 75 and phase_name not in strong_areas:
                strong_areas.append(f"{phase_name} Phase")
            elif phase_avg < 60 and phase_name not in improvement_areas:
                improvement_areas.append(f"{phase_name} Phase")

        return strong_areas, improvement_areas

    def _extract_critical_mistakes(self, session: SessionState) -> List[Dict[str, str]]:
        mistakes = []
        for flag in session.red_flags:
            mistakes.append({
                "mistake": flag["description"],
                "question": f"Q{flag['question_id']}",
                "impact": "Critical accuracy issue"
            })
        for qa in session.conversation_history:
            eval_data     = qa.get("evaluation", {})
            overall_score = eval_data.get("overall_score", 0)
            if overall_score < 50:
                weaknesses = eval_data.get("weaknesses", [])
                if weaknesses:
                    mistakes.append({
                        "mistake": weaknesses[0],
                        "question": f"Q{qa.get('question_id', '?')}",
                        "impact": f"Low score: {overall_score}/100"
                    })
        return mistakes[:5]

    def _generate_detailed_feedback(self, session: SessionState) -> Dict[str, List[str]]:
        feedback = {
            "technical_depth": [], "concept_accuracy": [],
            "structured_thinking": [], "communication": [], "confidence": []
        }
        for qa in session.conversation_history:
            eval_data = qa.get("evaluation", {})
            for strength in eval_data.get("strengths", [])[:2]:
                key  = self._categorize_feedback(strength)
                text = f"✅ {strength}"
                if text not in feedback.get(key, []):
                    feedback[key].append(text)
            for weakness in eval_data.get("weaknesses", [])[:2]:
                key  = self._categorize_feedback(weakness)
                text = f"❌ {weakness}"
                if text not in feedback.get(key, []):
                    feedback[key].append(text)
        for key in feedback:
            feedback[key] = feedback[key][:5]
        return feedback

    def _categorize_feedback(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["technical", "depth", "detail", "architecture"]):
            return "technical_depth"
        if any(w in t for w in ["accurate", "correct", "wrong", "error", "mistake"]):
            return "concept_accuracy"
        if any(w in t for w in ["structure", "star", "organized", "logical"]):
            return "structured_thinking"
        if any(w in t for w in ["clear", "filler", "rambling", "concise", "explain"]):
            return "communication"
        return "confidence"

    def _generate_round_breakdown(self, session: SessionState) -> Dict[str, Dict]:
        breakdown = {}
        rounds = {"hr": [], "technical": [], "system_design": []}
        for qa in session.conversation_history:
            rt = qa.get("round_type")
            if rt in rounds:
                rounds[rt].append(qa)
        for round_type, questions in rounds.items():
            if not questions:
                continue
            scores    = [q.get("evaluation", {}).get("overall_score", 0) for q in questions]
            avg_score = int(sum(scores) / len(scores)) if scores else 0
            strengths, weaknesses = [], []
            for q in questions:
                e = q.get("evaluation", {})
                strengths.extend(e.get("strengths", []))
                weaknesses.extend(e.get("weaknesses", []))
            breakdown[round_type] = {
                "score": avg_score,
                "questions_asked": len(questions),
                "strengths":  list(set(strengths))[:3],
                "weaknesses": list(set(weaknesses))[:3]
            }
        return breakdown

    def _generate_recommendations(self, session: SessionState, improvement_areas: List[str]) -> List[str]:
        recs = []
        rec_map = {
            "Technical Depth":       "Study system design patterns and practice explaining technical concepts in detail",
            "Concept Accuracy":      "Review fundamental CS concepts and verify your understanding with practice problems",
            "Structured Thinking":   "Practice the STAR method with specific examples and measurable outcomes",
            "Communication Clarity": "Record yourself answering questions and work on reducing filler words",
            "Confidence & Consistency": "Practice mock interviews to build confidence and maintain consistency"
        }
        for area in improvement_areas:
            if area in rec_map:
                recs.append(rec_map[area])
        if session.red_flags:
            recs.append("Verify all claims before interviews — inconsistencies were detected in this session")
        if session.total_interruptions > 2:
            recs.append("Work on staying concise and on-topic to avoid interruptions")
        return recs[:5]

    def _generate_interruption_summary(self, session: SessionState) -> Dict:
        if not session.interruptions:
            return {
                "total_interruptions": 0,
                "primary_trigger": "none",
                "recovery_quality": "n/a",
                "notes": "No interruptions during interview"
            }
        triggers = {}
        for intr in session.interruptions:
            reason = intr.get("reason", "unknown")
            triggers[reason] = triggers.get(reason, 0) + 1
        primary = max(triggers.items(), key=lambda x: x[1])[0] if triggers else "unknown"
        return {
            "total_interruptions": session.total_interruptions,
            "primary_trigger": primary,
            "recovery_quality": "good" if session.total_interruptions <= 2 else "needs_work",
            "trigger_breakdown": triggers,
            "notes": f"Most common trigger: {primary.replace('_', ' ')}. Focus on staying concise and accurate."
        }

    def _generate_claim_report(self, session: SessionState) -> Dict:
        total   = len(session.extracted_claims)
        unverif = session.unverified_claims
        verif   = session.verified_claims
        red     = [f["description"] for f in session.red_flags if f.get("type") == "claim"]
        return {
            "total_claims": total,
            "verified": len(verif),
            "unverified": unverif[:3],
            "red_flags": red[:3]
        }

    def _generate_next_steps(self, improvement_areas: List[str], critical_mistakes: List[Dict]) -> List[str]:
        steps = []
        if "Communication Clarity" in improvement_areas:
            steps.append("Record 3 practice answers and count filler words — aim for <2 per minute")
        if "Structured Thinking" in improvement_areas:
            steps.append("Prepare 5 STAR stories with specific metrics before your next interview")
        if "Technical Depth" in improvement_areas:
            steps.append("Practice explaining 3 complex technical concepts to a non-technical friend")
        if critical_mistakes:
            steps.append("Review and verify all claims from your resume before interviews")
        steps.append("Take at least 2 more mock interviews focusing on your weak areas")
        return steps[:5]

    def _determine_difficulty_reached(self, session: SessionState) -> str:
        difficulties = ["easy", "medium", "hard"]
        max_difficulty = "easy"
        for qa in session.conversation_history:
            d = qa.get("difficulty", "medium")
            if d in difficulties and difficulties.index(d) > difficulties.index(max_difficulty):
                max_difficulty = d
        return max_difficulty


# ── Singleton ────────────────────────────────────────────────

_report_generator = None

def get_final_report_generator() -> FinalReportGenerator:
    global _report_generator
    if _report_generator is None:
        _report_generator = FinalReportGenerator()
    return _report_generator

get_report_generator = get_final_report_generator