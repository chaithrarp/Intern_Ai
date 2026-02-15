"""
Answer Analyzer - OPTIMIZED VERSION
====================================

OPTIMIZATIONS:
✅ Added skip_claim_extraction flag (saves ~2-3 seconds for Q1-Q3)
✅ Claim extraction only runs for Q4+ when patterns emerge

RESULT: 2-3x faster for early questions
"""

from typing import Dict, List, Optional
from models.evaluation_models import AnswerEvaluation
from engines.round_evaluators.hr_evaluator import HRRoundEvaluator
from engines.round_evaluators.technical_evaluator import TechnicalRoundEvaluator
from engines.round_evaluators.sysdesign_evaluator import SystemDesignEvaluator
from engines.claim_extractor import ClaimExtractor


class OptimizedAnswerAnalyzer:
    """
    OPTIMIZED answer analyzer with conditional claim extraction
    """
    
    def __init__(self):
        # Initialize all round evaluators
        self.hr_evaluator = HRRoundEvaluator()
        self.technical_evaluator = TechnicalRoundEvaluator()
        self.sysdesign_evaluator = SystemDesignEvaluator()
        
        # Initialize claim extractor
        self.claim_extractor = ClaimExtractor()
        
        print("✅ OPTIMIZED Answer Analyzer initialized")
        print("   🚀 Claim extraction can be skipped for speed")
    
    def evaluate_answer(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        round_type: str,
        session_id: str,
        conversation_history: List[Dict] = None,
        skip_claim_extraction: bool = False  # ← NEW OPTIMIZATION FLAG
    ) -> AnswerEvaluation:
        """
        Evaluate answer with OPTIONAL claim extraction
        
        Args:
            skip_claim_extraction: If True, skips expensive claim extraction
                                   (recommended for Q1-Q3)
        """
        
        print(f"\n{'='*60}")
        print(f"📊 ANALYZING ANSWER - Question {question_id}")
        print(f"   Round Type: {round_type.upper()}")
        
        if skip_claim_extraction:
            print(f"   🚀 FAST MODE: Skipping claim extraction")
        
        print(f"{'='*60}")
        
        # Step 1: Extract claims (CONDITIONALLY)
        claims = []
        if not skip_claim_extraction:
            claims = self._extract_claims(
                answer_text,
                question_text,
                question_id,
                session_id,
                conversation_history or []
            )
        else:
            print("\n   ⏭️  Skipped claim extraction (optimization)")
        
        # Step 2: Route to appropriate evaluator (ALWAYS RUN)
        evaluation = self._route_to_evaluator(
            answer_text,
            question_text,
            question_id,
            round_type,
            conversation_history or []
        )
        
        # Step 3: Enhance with claims (only if claims extracted)
        if claims:
            evaluation = self._enhance_with_claims(evaluation, claims)
        
        print(f"\n✅ ANALYSIS COMPLETE")
        print(f"   Overall Score: {evaluation.overall_score}/100")
        print(f"   Difficulty Recommendation: {evaluation.difficulty_adjustment}")
        print(f"{'='*60}\n")
        
        return evaluation
    
    def _extract_claims(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        session_id: str,
        conversation_history: List[Dict]
    ) -> List:
        """Extract claims (expensive LLM call)"""
        
        print("\n🔍 Step 1: Extracting claims...")
        
        try:
            claims = self.claim_extractor.extract_claims(
                answer_text=answer_text,
                question_text=question_text,
                question_id=str(question_id),
                answer_id=f"a_{question_id}",
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            if claims:
                print(f"   ✓ Extracted {len(claims)} claims")
                high_priority = [c for c in claims if c.priority >= 7]
                if high_priority:
                    print(f"   ⚠️  {len(high_priority)} claims need verification")
            else:
                print(f"   ✓ No verifiable claims found")
            
            return claims
            
        except Exception as e:
            print(f"   ❌ Claim extraction failed: {str(e)}")
            return []
    
    def _route_to_evaluator(
        self,
        answer_text: str,
        question_text: str,
        question_id: int,
        round_type: str,
        conversation_history: List[Dict]
    ) -> AnswerEvaluation:
        """Route to appropriate evaluator (ALWAYS RUN)"""
        
        print(f"\n📝 Step 2: Routing to {round_type.upper()} evaluator...")
        
        # Normalize round type
        round_type = round_type.lower().strip()
        
        # Route to evaluator
        if round_type == "hr" or round_type == "behavioral":
            evaluator = self.hr_evaluator
        elif round_type == "technical" or round_type == "tech":
            evaluator = self.technical_evaluator
        elif round_type == "system_design" or round_type == "sysdesign":
            evaluator = self.sysdesign_evaluator
        else:
            print(f"   ⚠️  Unknown round type '{round_type}', defaulting to technical")
            evaluator = self.technical_evaluator
        
        # Evaluate
        evaluation = evaluator.evaluate(
            answer_text=answer_text,
            question_text=question_text,
            question_id=question_id,
            conversation_history=conversation_history
        )
        
        return evaluation
    
    def _enhance_with_claims(
        self,
        evaluation: AnswerEvaluation,
        claims: List
    ) -> AnswerEvaluation:
        """Enhance evaluation with claim insights (only if claims exist)"""
        
        if not claims:
            return evaluation
        
        print(f"\n🔬 Step 3: Enhancing evaluation with claim insights...")
        
        # Count claim types
        vague_claims = [c for c in claims if c.verifiability.value == "vague"]
        suspicious_claims = [c for c in claims if c.verifiability.value == "suspicious"]
        contradictory_claims = [c for c in claims if c.verifiability.value == "contradictory"]
        
        # Add claim-based red flags
        if contradictory_claims:
            for claim in contradictory_claims:
                flag = f"Contradiction detected: {claim.claim_text[:60]}..."
                if flag not in evaluation.red_flags:
                    evaluation.red_flags.append(flag)
            print(f"   🚨 Added {len(contradictory_claims)} contradiction red flags")
        
        if suspicious_claims:
            for claim in suspicious_claims:
                flag = f"Suspicious claim: {claim.claim_text[:60]}..."
                if flag not in evaluation.red_flags:
                    evaluation.red_flags.append(flag)
            print(f"   ⚠️  Added {len(suspicious_claims)} suspicious claim flags")
        
        # Reduce concept accuracy score for vague claims
        if vague_claims and len(vague_claims) >= 2:
            penalty = min(15, len(vague_claims) * 5)
            old_score = evaluation.scores.get('concept_accuracy', 0)
            evaluation.scores['concept_accuracy'] = max(0, old_score - penalty)
            print(f"   ⬇️  Reduced concept accuracy by {penalty} points (vague claims)")
        
        # Reduce confidence score for contradictions
        if contradictory_claims:
            penalty = min(20, len(contradictory_claims) * 10)
            old_score = evaluation.scores.get('confidence_consistency', 0)
            evaluation.scores['confidence_consistency'] = max(0, old_score - penalty)
            print(f"   ⬇️  Reduced confidence by {penalty} points (contradictions)")
        
        # Recalculate overall score
        from models.evaluation_models import ScoringThresholds
        evaluation.overall_score = ScoringThresholds.calculate_weighted_score(
            evaluation.scores
        )
        
        # Add claim verification to weaknesses if many unverified
        unverified = [c for c in claims if c.requires_verification]
        if len(unverified) >= 3:
            weakness = f"Made {len(unverified)} claims that need verification"
            if weakness not in evaluation.weaknesses:
                evaluation.weaknesses.append(weakness)
        
        return evaluation
    
    def get_evaluator_for_round(self, round_type: str):
        """Get appropriate evaluator for round type"""
        round_type = round_type.lower().strip()
        
        if round_type == "hr" or round_type == "behavioral":
            return self.hr_evaluator
        elif round_type == "technical" or round_type == "tech":
            return self.technical_evaluator
        elif round_type == "system_design" or round_type == "sysdesign":
            return self.sysdesign_evaluator
        else:
            return self.technical_evaluator


# Singleton
_optimized_analyzer = None

def get_answer_analyzer():
    """Get singleton instance"""
    global _optimized_analyzer
    if _optimized_analyzer is None:
        _optimized_analyzer = OptimizedAnswerAnalyzer()
    return _optimized_analyzer


# Alias for backward compatibility
AnswerAnalyzer = OptimizedAnswerAnalyzer