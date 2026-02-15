"""
System Design Round Evaluator - FIXED VERSION
==============================================

CHANGES:
- Added fallback mechanism to ensure all 5 dimensions are always present  
- Prevents Pydantic validation errors when LLM doesn't return all dimensions
- Added try-except blocks around score parsing
"""

from typing import Dict, List
from models.evaluation_models import AnswerEvaluation, EvaluationScore, ScoringThresholds
from llm_service import get_llm_response


class SystemDesignEvaluator:
    """
    Evaluates system design interview answers
    """
    
    def __init__(self):
        self.round_type = "system_design"
    
    def evaluate(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        conversation_history: List[Dict] = None
    ) -> AnswerEvaluation:
        """
        Evaluate a system design round answer
        """
        
        print(f"\n📊 System Design Evaluator: Analyzing answer to Q{question_id}...")
        
        # Build evaluation prompt
        prompt = self._build_sysdesign_evaluation_prompt(
            answer_text,
            question_text,
            conversation_history or []
        )
        
        # Get LLM evaluation
        raw_response = get_llm_response(prompt, temperature=0.3)
        
        # Parse response into structured scores
        evaluation = self._parse_sysdesign_evaluation(
            raw_response,
            question_id
        )
        
        return evaluation
    
    def _build_sysdesign_evaluation_prompt(
        self,
        answer: str,
        question: str,
        history: List[Dict]
    ) -> List[Dict]:
        """
        Build LLM prompt for system design evaluation
        """
        
        system_prompt = """You are an expert system architect evaluating a system design interview answer.

Your task: Evaluate the answer across 5 dimensions with ARCHITECTURE FOCUS.

EVALUATION CRITERIA:

1. **Technical Depth (0-100)** - MOST IMPORTANT FOR SYSTEM DESIGN:
   - Scalability thinking (horizontal vs vertical)
   - Component architecture (load balancers, caching, databases, queues)
   - Data flow understanding
   - Infrastructure awareness (CDN, distributed systems)
   - Handles millions/billions of users thinking

2. **Concept Accuracy (0-100)**:
   - Correct understanding of distributed systems concepts
   - Accurate capacity estimations
   - Realistic architecture choices
   - No fundamental misunderstandings about how systems scale

3. **Structured Thinking (0-100)** - CRITICAL:
   - Systematic approach (requirements → architecture → deep dive)
   - Breaks down problem into components
   - Identifies bottlenecks methodically
   - Considers failure scenarios
   - Clear component boundaries

4. **Communication Clarity (0-100)**:
   - Explains architecture clearly
   - Uses diagrams/visual thinking (mentions boxes, arrows, flows)
   - Makes trade-offs explicit

5. **Confidence & Consistency (0-100)**:
   - Confident in design decisions
   - Justifies choices with reasoning
   - Consistent architecture throughout

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

STRENGTHS: [2-3 specific system design strengths, separated by |]
WEAKNESSES: [2-3 specific architecture gaps, separated by |]
RED_FLAGS: [any critical design flaws, separated by | or NONE]

REQUIRES_FOLLOWUP: [YES or NO]
FOLLOWUP_REASON: [reason or NONE]
SUGGESTED_FOLLOWUP: [probing architecture question or NONE]

DIFFICULTY_ADJUSTMENT: [decrease, maintain, or increase]
```

Be architecturally rigorous. This is senior-level evaluation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Question: "{question}"

Answer: "{answer}"

Evaluate this system design answer. Focus on scalability, architecture, and bottleneck awareness."""}
        ]
        
        return messages
    
    def _parse_sysdesign_evaluation(
        self,
        raw_output: str,
        question_id: int
    ) -> AnswerEvaluation:
        """
        Parse LLM output into AnswerEvaluation object
        
        FIXED: Now ensures all required dimensions are present with proper error handling
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
            
            # Parse TECHNICAL_DEPTH
            if line.startswith('TECHNICAL_DEPTH:'):
                current_dimension = 'technical_depth'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    scores[current_dimension] = 0
                    dimension_score = 0
                
            elif line.startswith('TECHNICAL_DEPTH_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
                
            elif line.startswith('TECHNICAL_DEPTH_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip() if ':' in line else ""
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='technical_depth',
                        score=scores.get('technical_depth', 0),
                        evidence=dimension_evidence or "No evidence",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='technical_depth',
                        score=scores.get('technical_depth', 0),
                        evidence=dimension_evidence or "No evidence"
                    ))
            
            # Parse CONCEPT_ACCURACY
            elif line.startswith('CONCEPT_ACCURACY:'):
                current_dimension = 'concept_accuracy'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    scores[current_dimension] = 0
                    dimension_score = 0
                
            elif line.startswith('CONCEPT_ACCURACY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
                
            elif line.startswith('CONCEPT_ACCURACY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip() if ':' in line else ""
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='concept_accuracy',
                        score=scores.get('concept_accuracy', 0),
                        evidence=dimension_evidence or "No evidence",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='concept_accuracy',
                        score=scores.get('concept_accuracy', 0),
                        evidence=dimension_evidence or "No evidence"
                    ))
            
            # Parse STRUCTURED_THINKING
            elif line.startswith('STRUCTURED_THINKING:'):
                current_dimension = 'structured_thinking'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    scores[current_dimension] = 0
                    dimension_score = 0
                
            elif line.startswith('STRUCTURED_THINKING_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
                
            elif line.startswith('STRUCTURED_THINKING_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip() if ':' in line else ""
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='structured_thinking',
                        score=scores.get('structured_thinking', 0),
                        evidence=dimension_evidence or "No evidence",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='structured_thinking',
                        score=scores.get('structured_thinking', 0),
                        evidence=dimension_evidence or "No evidence"
                    ))
            
            # Parse COMMUNICATION_CLARITY
            elif line.startswith('COMMUNICATION_CLARITY:'):
                current_dimension = 'communication_clarity'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    scores[current_dimension] = 0
                    dimension_score = 0
                
            elif line.startswith('COMMUNICATION_CLARITY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
                
            elif line.startswith('COMMUNICATION_CLARITY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip() if ':' in line else ""
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='communication_clarity',
                        score=scores.get('communication_clarity', 0),
                        evidence=dimension_evidence or "No evidence",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='communication_clarity',
                        score=scores.get('communication_clarity', 0),
                        evidence=dimension_evidence or "No evidence"
                    ))
            
            # Parse CONFIDENCE_CONSISTENCY
            elif line.startswith('CONFIDENCE_CONSISTENCY:'):
                current_dimension = 'confidence_consistency'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    scores[current_dimension] = 0
                    dimension_score = 0
                
            elif line.startswith('CONFIDENCE_CONSISTENCY_EVIDENCE:'):
                dimension_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
                
            elif line.startswith('CONFIDENCE_CONSISTENCY_IMPROVEMENT:'):
                dimension_improvement = line.split(':', 1)[1].strip() if ':' in line else ""
                if dimension_improvement and dimension_improvement != 'NONE':
                    score_details.append(EvaluationScore(
                        dimension='confidence_consistency',
                        score=scores.get('confidence_consistency', 0),
                        evidence=dimension_evidence or "No evidence",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='confidence_consistency',
                        score=scores.get('confidence_consistency', 0),
                        evidence=dimension_evidence or "No evidence"
                    ))
            
            # Parse feedback
            elif line.startswith('STRENGTHS:'):
                strengths_text = line.split(':', 1)[1].strip() if ':' in line else ""
                strengths = [s.strip() for s in strengths_text.split('|') if s.strip()]
                
            elif line.startswith('WEAKNESSES:'):
                weaknesses_text = line.split(':', 1)[1].strip() if ':' in line else ""
                weaknesses = [w.strip() for w in weaknesses_text.split('|') if w.strip()]
                
            elif line.startswith('RED_FLAGS:'):
                red_flags_text = line.split(':', 1)[1].strip() if ':' in line else ""
                if red_flags_text and red_flags_text != 'NONE':
                    red_flags = [r.strip() for r in red_flags_text.split('|') if r.strip()]
            
            # Parse follow-up
            elif line.startswith('REQUIRES_FOLLOWUP:'):
                requires_followup = 'YES' in line.upper()
                
            elif line.startswith('FOLLOWUP_REASON:'):
                reason_text = line.split(':', 1)[1].strip() if ':' in line else ""
                if reason_text and reason_text != 'NONE':
                    followup_reason = reason_text
                    
            elif line.startswith('SUGGESTED_FOLLOWUP:'):
                followup_text = line.split(':', 1)[1].strip() if ':' in line else ""
                if followup_text and followup_text != 'NONE':
                    suggested_followup = followup_text
            
            # Parse difficulty
            elif line.startswith('DIFFICULTY_ADJUSTMENT:'):
                try:
                    difficulty_adjustment = line.split(':')[1].strip().lower()
                    if difficulty_adjustment not in ['decrease', 'maintain', 'increase']:
                        difficulty_adjustment = 'maintain'
                except (IndexError, AttributeError):
                    difficulty_adjustment = 'maintain'
        
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
                if not any(sd.dimension == dim for sd in score_details):
                    score_details.append(EvaluationScore(
                        dimension=dim,
                        score=0,
                        evidence="No evaluation data from LLM",
                        improvement="Unable to assess"
                    ))
        
        # Calculate overall score
        overall_score = ScoringThresholds.calculate_weighted_score(scores)
        
        # Ensure feedback exists
        if not strengths:
            strengths = ["Provided an answer"]
        if not weaknesses:
            weaknesses = ["Could provide more depth"]
        
        # Create evaluation object
        evaluation = AnswerEvaluation(
            question_id=question_id,
            round_type="system_design",
            scores=scores,
            score_details=score_details,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            red_flags=red_flags,
            requires_followup=requires_followup,
            followup_reason=followup_reason,
            suggested_followup=suggested_followup,
            difficulty_adjustment=difficulty_adjustment
        )
        
        print(f"   ✅ System Design Evaluation complete: Overall {overall_score}/100")
        print(f"      Technical Depth: {scores.get('technical_depth', 0)}/100 (SCALABILITY)")
        print(f"      Structured Thinking: {scores.get('structured_thinking', 0)}/100 (ARCHITECTURE)")
        
        return evaluation