"""
Technical Round Evaluator - FIXED VERSION
==========================================

CHANGES:
- Added fallback mechanism to ensure all 5 dimensions are always present
- Prevents Pydantic validation errors when LLM doesn't return all dimensions
- Added try-except blocks around score parsing
"""

from typing import Dict, List
from models.evaluation_models import AnswerEvaluation, EvaluationScore, ScoringThresholds
from llm_service import get_llm_response


class TechnicalRoundEvaluator:
    """
    Evaluates technical interview answers
    """
    
    def __init__(self):
        self.round_type = "technical"
    
    def evaluate(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        conversation_history: List[Dict] = None
    ) -> AnswerEvaluation:
        """
        Evaluate a technical round answer
        
        Args:
            answer_text: The candidate's answer
            question_text: The question asked
            question_id: Question ID
            conversation_history: Previous Q&A pairs
            
        Returns:
            AnswerEvaluation object with scores and feedback
        """
        
        print(f"\n📊 Technical Evaluator: Analyzing answer to Q{question_id}...")
        
        # Build evaluation prompt
        prompt = self._build_technical_evaluation_prompt(
            answer_text,
            question_text,
            conversation_history or []
        )
        
        # Get LLM evaluation
        raw_response = get_llm_response(prompt, temperature=0.3)
        
        # Parse response into structured scores
        evaluation = self._parse_technical_evaluation(
            raw_response,
            question_id
        )
        
        return evaluation
    
    def _build_technical_evaluation_prompt(
        self,
        answer: str,
        question: str,
        history: List[Dict]
    ) -> List[Dict]:
        """
        Build LLM prompt for technical evaluation
        """
        
        system_prompt = """You are an expert senior engineer evaluating a technical interview answer.

Your task: Evaluate the answer across 5 dimensions with TECHNICAL FOCUS.

EVALUATION CRITERIA:

1. **Technical Depth (0-100)** - MOST IMPORTANT FOR TECHNICAL:
   - Deep understanding of concepts (not surface level)
   - Explains WHY things work, not just WHAT
   - Discusses internals/implementation details
   - Shows hands-on experience

2. **Concept Accuracy (0-100)** - CRITICAL:
   - Are technical statements correct?
   - No fundamental misunderstandings?
   - Uses terminology correctly?
   - No false claims about how things work?

3. **Structured Thinking (0-100)**:
   - Organized explanation (not scattered)
   - Logical problem-solving approach
   - Breaks down complex problems
   - Systematic reasoning

4. **Communication Clarity (0-100)**:
   - Explains complex topics clearly
   - Minimal jargon without explanation
   - Concise technical communication

5. **Confidence & Consistency (0-100)**:
   - Confident in technical knowledge
   - Consistent with previous answers
   - Admits when unsure (vs making things up)

TECHNICAL RED FLAGS:
- Fundamental concept errors (e.g., "hash maps are O(n) lookup")
- Buzzword dropping without understanding
- No mention of trade-offs (everything is "best practice")
- No edge case consideration
- Unrealistic claims ("this solution works for everything")
- Vague optimizations ("I made it faster" without specifics)

WHAT TO LOOK FOR:
✅ Discusses time/space complexity
✅ Mentions trade-offs and alternatives
✅ Considers edge cases
✅ Explains with examples
✅ Shows debugging/troubleshooting thinking
✅ Admits limitations of approach

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

STRENGTHS: [2-3 specific technical strengths, separated by |]
WEAKNESSES: [2-3 specific technical gaps, separated by |]
RED_FLAGS: [any critical technical errors, separated by | or NONE]

REQUIRES_FOLLOWUP: [YES or NO]
FOLLOWUP_REASON: [reason or NONE]
SUGGESTED_FOLLOWUP: [probing technical question or NONE]

DIFFICULTY_ADJUSTMENT: [decrease, maintain, or increase]
```

Be technically rigorous. Flag incorrect concepts immediately."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Question: "{question}"

Answer: "{answer}"

Evaluate this technical answer. Focus on correctness, depth, and trade-off analysis."""}
        ]
        
        return messages
    
    def _parse_technical_evaluation(
        self,
        raw_output: str,
        question_id: int
    ) -> AnswerEvaluation:
        """
        Parse LLM output into AnswerEvaluation object
        
        FIXED: Now ensures all required dimensions are present with proper error handling
        """
        
        # CRITICAL FIX: Remove markdown formatting before parsing
        raw_output = raw_output.replace('**', '').replace('*', '')
        
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
                    print(f"   ⚠️  Could not parse TECHNICAL_DEPTH score, using default 0")
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
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='technical_depth',
                        score=scores.get('technical_depth', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Parse CONCEPT_ACCURACY
            elif line.startswith('CONCEPT_ACCURACY:'):
                current_dimension = 'concept_accuracy'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    print(f"   ⚠️  Could not parse CONCEPT_ACCURACY score, using default 0")
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
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='concept_accuracy',
                        score=scores.get('concept_accuracy', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Parse STRUCTURED_THINKING
            elif line.startswith('STRUCTURED_THINKING:'):
                current_dimension = 'structured_thinking'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    print(f"   ⚠️  Could not parse STRUCTURED_THINKING score, using default 0")
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
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='structured_thinking',
                        score=scores.get('structured_thinking', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Parse COMMUNICATION_CLARITY
            elif line.startswith('COMMUNICATION_CLARITY:'):
                current_dimension = 'communication_clarity'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    print(f"   ⚠️  Could not parse COMMUNICATION_CLARITY score, using default 0")
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
                        evidence=dimension_evidence or "No evidence provided",
                        improvement=dimension_improvement
                    ))
                else:
                    score_details.append(EvaluationScore(
                        dimension='communication_clarity',
                        score=scores.get('communication_clarity', 0),
                        evidence=dimension_evidence or "No evidence provided"
                    ))
            
            # Parse CONFIDENCE_CONSISTENCY
            elif line.startswith('CONFIDENCE_CONSISTENCY:'):
                current_dimension = 'confidence_consistency'
                try:
                    dimension_score = int(line.split(':')[1].strip())
                    scores[current_dimension] = dimension_score
                except (ValueError, IndexError):
                    print(f"   ⚠️  Could not parse CONFIDENCE_CONSISTENCY score, using default 0")
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
                # Only add to score_details if not already there
                if not any(sd.dimension == dim for sd in score_details):
                    score_details.append(EvaluationScore(
                        dimension=dim,
                        score=0,
                        evidence="No evaluation data available from LLM response",
                        improvement="Unable to assess - LLM did not return this dimension"
                    ))
        
        # Calculate overall score (weighted average)
        overall_score = ScoringThresholds.calculate_weighted_score(scores)
        
        # Ensure we have at least some feedback
        if not strengths:
            strengths = ["Provided an answer"]
        if not weaknesses:
            weaknesses = ["Could provide more depth"]
        
        # Create evaluation object
        evaluation = AnswerEvaluation(
            question_id=question_id,
            round_type="technical",
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
        
        print(f"   ✅ Technical Evaluation complete: Overall {overall_score}/100")
        print(f"      Technical Depth: {scores.get('technical_depth', 0)}/100 (KEY FOR TECHNICAL)")
        print(f"      Concept Accuracy: {scores.get('concept_accuracy', 0)}/100 (CRITICAL)")
        
        return evaluation


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("TECHNICAL ROUND EVALUATOR TEST")
    print("=" * 60)
    
    evaluator = TechnicalRoundEvaluator()
    
    # Test answer with good technical depth
    test_answer = """
    A hash map uses a hash function to compute an index into an array of buckets.
    The time complexity for average case lookup is O(1) because we can directly 
    access the bucket using the hash value.
    
    However, in the worst case with many collisions, it degrades to O(n) if we're 
    using chaining and all elements hash to the same bucket. That's why choosing 
    a good hash function is critical.
    
    There's a trade-off between memory and performance - a larger array reduces 
    collisions but uses more space. Most implementations use a load factor of 
    around 0.75 to balance this.
    
    For edge cases, we need to handle null keys, resize the array when load 
    factor is exceeded, and ensure the hash function distributes values evenly.
    """
    
    test_question = "Explain how a hash map works and discuss its time complexity."
    
    evaluation = evaluator.evaluate(
        answer_text=test_answer,
        question_text=test_question,
        question_id=1
    )
    
    print(f"\n📊 Results:")
    print(f"   Overall Score: {evaluation.overall_score}/100")
    print(f"\n   Dimension Scores:")
    for dim, score in evaluation.scores.items():
        print(f"   - {dim}: {score}/100")
    
    print(f"\n   Strengths:")
    for strength in evaluation.strengths:
        print(f"   ✅ {strength}")
    
    print(f"\n   Weaknesses:")
    for weakness in evaluation.weaknesses:
        print(f"   ⚠️ {weakness}")
    
    if evaluation.red_flags:
        print(f"\n   Red Flags:")
        for flag in evaluation.red_flags:
            print(f"   🚨 {flag}")
    
    print("\n" + "=" * 60)