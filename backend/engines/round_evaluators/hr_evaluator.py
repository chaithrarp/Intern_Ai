"""
HR Round Evaluator - FIXED VERSION
===================================

CHANGES:
- Added fallback mechanism to ensure all 5 dimensions are always present
- Prevents Pydantic validation errors when LLM doesn't return all dimensions
"""

from typing import Dict, List
from models.evaluation_models import AnswerEvaluation, EvaluationScore
from llm_service import get_llm_response


class HRRoundEvaluator:
    """
    Evaluates HR/behavioral interview answers
    """
    
    def __init__(self):
        self.round_type = "hr"
    
    def evaluate(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        conversation_history: List[Dict] = None
    ) -> AnswerEvaluation:
        """
        Evaluate an HR round answer
        
        Args:
            answer_text: The candidate's answer
            question_text: The question asked
            question_id: Question ID
            conversation_history: Previous Q&A pairs
            
        Returns:
            AnswerEvaluation object with scores and feedback
        """
        
        print(f"\n📊 HR Evaluator: Analyzing answer to Q{question_id}...")
        
        # Build evaluation prompt
        prompt = self._build_hr_evaluation_prompt(
            answer_text,
            question_text,
            conversation_history or []
        )
        
        # Get LLM evaluation
        raw_response = get_llm_response(prompt, temperature=0.3)
        
        # Parse response into structured scores
        evaluation = self._parse_hr_evaluation(
            raw_response,
            question_id
        )
        
        return evaluation
    
    def _build_hr_evaluation_prompt(
        self,
        answer: str,
        question: str,
        history: List[Dict]
    ) -> List[Dict]:
        """
        Build LLM prompt for HR evaluation
        """
        
        system_prompt = """You are an expert HR interviewer evaluating a behavioral interview answer.

Your task: Evaluate the answer across 5 dimensions and provide specific feedback.

EVALUATION CRITERIA:

1. **Technical Depth (0-100)**: 
   - For HR round, this measures depth of understanding about their role/project
   - Did they explain what they actually did?
   - Do they understand the technical context?

2. **Concept Accuracy (0-100)**:
   - Are their claims accurate and verifiable?
   - No false claims or exaggerations?
   - Consistent with previous answers?

3. **Structured Thinking (0-100)** - MOST IMPORTANT FOR HR:
   - STAR method: Situation, Task, Action, Result
   - Situation: Did they set context clearly?
   - Task: Did they explain what needed to be done?
   - Action: Did they describe specific actions they took?
   - Result: Did they share measurable outcomes?
   - Logical flow and organization

4. **Communication Clarity (0-100)**:
   - Concise and to the point?
   - Minimal filler words ("um", "like", "you know")
   - Easy to follow?

5. **Confidence & Consistency (0-100)**:
   - Confident delivery (no excessive hesitation)?
   - Consistent with previous statements?
   - Ownership vs deflection?

RED FLAGS TO DETECT:
- Blaming others instead of taking ownership
- No specific examples (all vague generalizations)
- No measurable results ("we improved things" without numbers)
- Inconsistent with previous answers
- Taking credit for team work without acknowledging team

OUTPUT FORMAT (plain text, parseable):
```
TECHNICAL_DEPTH: [0-100]
TECHNICAL_DEPTH_EVIDENCE: [one sentence]
TECHNICAL_DEPTH_IMPROVEMENT: [one sentence or NONE]

CONCEPT_ACCURACY: [0-100]
CONCEPT_ACCURACY_EVIDENCE: [one sentence]
CONCEPT_ACCURACY_IMPROVEMENT: [one sentence or NONE]

STRUCTURED_THINKING: [0-100]
STRUCTURED_THINKING_EVIDENCE: [one sentence]
STRUCTURED_THINKING_IMPROVEMENT: [one sentence or NONE]

COMMUNICATION_CLARITY: [0-100]
COMMUNICATION_CLARITY_EVIDENCE: [one sentence]
COMMUNICATION_CLARITY_IMPROVEMENT: [one sentence or NONE]

CONFIDENCE_CONSISTENCY: [0-100]
CONFIDENCE_CONSISTENCY_EVIDENCE: [one sentence]
CONFIDENCE_CONSISTENCY_IMPROVEMENT: [one sentence or NONE]

STRENGTHS: [2-3 specific strengths, separated by |]
WEAKNESSES: [2-3 specific weaknesses, separated by |]
RED_FLAGS: [any critical issues, separated by | or NONE]

REQUIRES_FOLLOWUP: [YES or NO]
FOLLOWUP_REASON: [reason or NONE]
SUGGESTED_FOLLOWUP: [question or NONE]

DIFFICULTY_ADJUSTMENT: [decrease, maintain, or increase]
```

Be harsh but fair. This is training, not encouragement."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Question: "{question}"

Answer: "{answer}"

Evaluate this HR/behavioral answer. Focus on STAR method adherence and specific examples."""}
        ]
        
        return messages
    
    def _parse_hr_evaluation(
        self,
        raw_output: str,
        question_id: int
    ) -> AnswerEvaluation:
        """
        Parse LLM output into AnswerEvaluation object
        
        FIXED: Now ensures all required dimensions are present
        """
        
        lines = raw_output.strip().split('\n')
        scores = {}
        score_details = []
        strengths = []
        weaknesses = []
        red_flags = []
        requires_followup = False
        followup_reason = None
        suggested_followup = None
        difficulty_adjustment = "maintain"
        
        current_dimension = None
        dimension_score = 0
        dimension_evidence = ""
        dimension_improvement = ""
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('```'):
                continue
            
            # Parse dimension scores
            if line.startswith('TECHNICAL_DEPTH:'):
                current_dimension = 'technical_depth'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except:
                    scores[current_dimension] = 0
                
            elif line.startswith('TECHNICAL_DEPTH_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip()
                
            elif line.startswith('TECHNICAL_DEPTH_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip()
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='technical_depth',
                        score=scores.get('technical_depth', 0),
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='technical_depth',
                        score=scores.get('technical_depth', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Repeat for other dimensions
            elif line.startswith('CONCEPT_ACCURACY:'):
                current_dimension = 'concept_accuracy'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except:
                    scores[current_dimension] = 0
                
            elif line.startswith('CONCEPT_ACCURACY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip()
                
            elif line.startswith('CONCEPT_ACCURACY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip()
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='concept_accuracy',
                        score=scores.get('concept_accuracy', 0),
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='concept_accuracy',
                        score=scores.get('concept_accuracy', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            elif line.startswith('STRUCTURED_THINKING:'):
                current_dimension = 'structured_thinking'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except:
                    scores[current_dimension] = 0
                
            elif line.startswith('STRUCTURED_THINKING_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip()
                
            elif line.startswith('STRUCTURED_THINKING_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip()
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='structured_thinking',
                        score=scores.get('structured_thinking', 0),
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='structured_thinking',
                        score=scores.get('structured_thinking', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            elif line.startswith('COMMUNICATION_CLARITY:'):
                current_dimension = 'communication_clarity'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except:
                    scores[current_dimension] = 0
                
            elif line.startswith('COMMUNICATION_CLARITY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip()
                
            elif line.startswith('COMMUNICATION_CLARITY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip()
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='communication_clarity',
                        score=scores.get('communication_clarity', 0),
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='communication_clarity',
                        score=scores.get('communication_clarity', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            elif line.startswith('CONFIDENCE_CONSISTENCY:'):
                current_dimension = 'confidence_consistency'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except:
                    scores[current_dimension] = 0
                
            elif line.startswith('CONFIDENCE_CONSISTENCY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip()
                
            elif line.startswith('CONFIDENCE_CONSISTENCY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip()
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='confidence_consistency',
                        score=scores.get('confidence_consistency', 0),
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='confidence_consistency',
                        score=scores.get('confidence_consistency', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Parse feedback
            elif line.startswith('STRENGTHS:'):
                strengths_text = line.split(':', 1)[1].strip()
                strengths = [s.strip() for s in strengths_text.split('|') if s.strip()]
                
            elif line.startswith('WEAKNESSES:'):
                weaknesses_text = line.split(':', 1)[1].strip()
                weaknesses = [w.strip() for w in weaknesses_text.split('|') if w.strip()]
                
            elif line.startswith('RED_FLAGS:'):
                red_flags_text = line.split(':', 1)[1].strip()
                if red_flags_text != 'NONE':
                    red_flags = [r.strip() for r in red_flags_text.split('|') if r.strip()]
            
            # Parse follow-up
            elif line.startswith('REQUIRES_FOLLOWUP:'):
                requires_followup = 'YES' in line.upper()
                
            elif line.startswith('FOLLOWUP_REASON:'):
                reason_text = line.split(':', 1)[1].strip()
                if reason_text != 'NONE':
                    followup_reason = reason_text
                    
            elif line.startswith('SUGGESTED_FOLLOWUP:'):
                followup_text = line.split(':', 1)[1].strip()
                if followup_text != 'NONE':
                    suggested_followup = followup_text
            
            # Parse difficulty
            elif line.startswith('DIFFICULTY_ADJUSTMENT:'):
                difficulty_adjustment = line.split(':')[1].strip().lower()
        
        # === CRITICAL FIX: Ensure all required dimensions are present ===
        required_dimensions = [
            'technical_depth',
            'concept_accuracy',
            'structured_thinking',
            'communication_clarity',
            'confidence_consistency'
        ]
        
        # Add missing dimensions with default score of 0
        for dim in required_dimensions:
            if dim not in scores:
                print(f"   ⚠️  Missing dimension '{dim}' - using default score 0")
                scores[dim] = 0
                score_details.append(EvaluationScore(
                    dimension=dim,
                    score=0,
                    evidence="No evaluation data available from LLM response",
                    improvement="Unable to assess - LLM did not return this dimension"
                ))
        
        # Calculate overall score (weighted average)
        from models.evaluation_models import ScoringThresholds
        overall_score = ScoringThresholds.calculate_weighted_score(scores)
        
        # Create evaluation object
        evaluation = AnswerEvaluation(
            question_id=question_id,
            round_type="hr",
            scores=scores,
            score_details=score_details,
            overall_score=overall_score,
            strengths=strengths if strengths else ["No strengths identified"],
            weaknesses=weaknesses if weaknesses else ["No weaknesses identified"],
            red_flags=red_flags,
            requires_followup=requires_followup,
            followup_reason=followup_reason,
            suggested_followup=suggested_followup,
            difficulty_adjustment=difficulty_adjustment
        )
        
        print(f"   ✅ HR Evaluation complete: Overall {overall_score}/100")
        print(f"      Structured Thinking: {scores.get('structured_thinking', 0)}/100 (KEY FOR HR)")
        
        return evaluation