"""
Claim Analyzer
==============

Analyzes extracted claims to:
- Prioritize which claims to verify first
- Detect red flags and suspicious patterns
- Categorize claims by risk level
- Generate claim verification strategy
"""

from typing import List, Dict, Optional
from models.interview_models import ExtractedClaim, ClaimType, ClaimVerifiability
from config.evaluation_config import CLAIM_PRIORITY_RULES, RED_FLAG_PATTERNS


# ============================================
# CLAIM ANALYZER CLASS
# ============================================

class ClaimAnalyzer:
    """
    Analyzes claims for verification priority and red flags
    
    Usage:
        analyzer = ClaimAnalyzer()
        
        # Prioritize claims for verification
        priority_claims = analyzer.prioritize_claims(all_claims)
        
        # Detect red flags
        red_flags = analyzer.detect_red_flags(claim)
        
        # Generate verification strategy
        strategy = analyzer.generate_verification_strategy(claims)
    """
    
    def __init__(self):
        self.priority_rules = CLAIM_PRIORITY_RULES
        self.red_flag_patterns = RED_FLAG_PATTERNS
    
    
    def prioritize_claims(
        self,
        claims: List[ExtractedClaim],
        max_claims: int = 3
    ) -> List[ExtractedClaim]:
        """
        Prioritize which claims to verify first
        
        Considers:
        - Claim priority score
        - Red flags
        - Verifiability status
        - Claim type importance
        
        Args:
            claims: List of extracted claims
            max_claims: Maximum number to return
        
        Returns:
            Top priority claims sorted by importance
        """
        
        print(f"\n📊 Prioritizing {len(claims)} claims...")
        
        # Filter to only unverified claims
        unverified = [c for c in claims if c.requires_verification and not c.verification_result]
        
        if not unverified:
            print("   No claims require verification")
            return []
        
        # Calculate adjusted priority scores
        scored_claims = []
        
        for claim in unverified:
            adjusted_score = self._calculate_adjusted_priority(claim)
            scored_claims.append((claim, adjusted_score))
            
            print(f"   - {claim.claim_text[:50]}... (score: {adjusted_score})")
        
        # Sort by adjusted score (highest first)
        scored_claims.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N claims
        top_claims = [claim for claim, score in scored_claims[:max_claims]]
        
        print(f"\n✓ Top {len(top_claims)} priority claims selected")
        
        return top_claims
    
    
    def _calculate_adjusted_priority(self, claim: ExtractedClaim) -> float:
        """
        Calculate adjusted priority score for a claim
        
        Base priority + modifiers for:
        - Red flags (+20)
        - Contradictory (+30)
        - Suspicious (+15)
        - Vague (+10)
        - Claim type importance
        
        Returns:
            Adjusted priority score (higher = more important)
        """
        
        score = float(claim.priority)
        
        # Red flag bonus
        if claim.red_flags:
            score += 20
        
        # Verifiability modifiers
        if claim.verifiability == ClaimVerifiability.CONTRADICTORY:
            score += 30  # CRITICAL - always verify contradictions
        elif claim.verifiability == ClaimVerifiability.SUSPICIOUS:
            score += 15
        elif claim.verifiability == ClaimVerifiability.VAGUE:
            score += 10
        
        # Claim type importance (from config)
        type_bonus = {
            ClaimType.METRIC: 5,              # Metrics are important
            ClaimType.PROJECT_SCALE: 5,       # Scale claims often exaggerated
            ClaimType.ARCHITECTURE_DECISION: 4,
            ClaimType.TECHNICAL_ACHIEVEMENT: 3,
            ClaimType.TOOL_EXPERTISE: 2,
            ClaimType.ROLE_RESPONSIBILITY: 2,
            ClaimType.PROBLEM_SOLVED: 1
        }
        
        score += type_bonus.get(claim.claim_type, 0)
        
        return score
    
    
    def detect_red_flags(self, claim: ExtractedClaim) -> List[str]:
        """
        Detect red flags in a claim
        
        Checks for:
        - Unrealistic metrics
        - Vague optimizations without details
        - Responsibility inflation
        - Technology buzzwords without depth
        
        Args:
            claim: Claim to analyze
        
        Returns:
            List of red flag descriptions
        """
        
        red_flags = []
        claim_text_lower = claim.claim_text.lower()
        
        # Check for unrealistic metrics
        if claim.claim_type == ClaimType.METRIC:
            if self._is_unrealistic_metric(claim.claim_text):
                red_flags.append(
                    f"Unrealistic metric without supporting details: {claim.claim_text}"
                )
        
        # Check for vague optimizations
        vague_keywords = ["optimized", "improved", "enhanced", "better", "faster"]
        has_vague_keyword = any(kw in claim_text_lower for kw in vague_keywords)
        
        if has_vague_keyword:
            # Check if they provided specifics
            specific_indicators = [
                "by", "%", "from", "to", "seconds", "milliseconds",
                "requests", "users", "bytes", "mb", "gb"
            ]
            has_specifics = any(ind in claim_text_lower for ind in specific_indicators)
            
            if not has_specifics:
                red_flags.append(
                    "Vague optimization claim without specific metrics or techniques"
                )
        
        # Check for responsibility inflation
        if claim.claim_type == ClaimType.ROLE_RESPONSIBILITY:
            inflation_patterns = [
                ("intern", ["led", "owned", "architected"]),
                ("junior", ["led team", "owned product", "made all decisions"]),
                ("engineer", ["single-handedly", "solely responsible"])
            ]
            
            for role_keyword, inflated_terms in inflation_patterns:
                if role_keyword in claim_text_lower:
                    if any(term in claim_text_lower for term in inflated_terms):
                        red_flags.append(
                            f"Possible responsibility inflation: {role_keyword} claiming '{inflated_terms}'"
                        )
        
        # Check for technology buzzwords without context
        buzzwords = ["ai", "machine learning", "ml", "blockchain", "quantum"]
        has_buzzword = any(bw in claim_text_lower for bw in buzzwords)
        
        if has_buzzword and claim.claim_type == ClaimType.TOOL_EXPERTISE:
            # Check if they mentioned specifics
            depth_indicators = [
                "algorithm", "model", "trained", "dataset", "accuracy",
                "precision", "recall", "implementation", "framework"
            ]
            has_depth = any(ind in claim_text_lower for ind in depth_indicators)
            
            if not has_depth:
                red_flags.append(
                    "Technology buzzword mentioned without technical depth"
                )
        
        return red_flags
    
    
    def generate_verification_strategy(
        self,
        claims: List[ExtractedClaim]
    ) -> Dict:
        """
        Generate strategy for verifying claims
        
        Returns:
            {
                "high_priority": [claims],
                "medium_priority": [claims],
                "low_priority": [claims],
                "total_verification_questions": int,
                "recommended_approach": str
            }
        """
        
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for claim in claims:
            if not claim.requires_verification:
                continue
            
            adjusted_score = self._calculate_adjusted_priority(claim)
            
            if adjusted_score >= 15:
                high_priority.append(claim)
            elif adjusted_score >= 10:
                medium_priority.append(claim)
            else:
                low_priority.append(claim)
        
        # Count total verification questions needed
        total_questions = sum(
            len(c.verification_questions) 
            for c in high_priority + medium_priority + low_priority
        )
        
        # Determine recommended approach
        if len(high_priority) >= 3:
            approach = "Focus on high-priority claims - multiple critical issues detected"
        elif len(high_priority) > 0:
            approach = "Verify high-priority claims first, then proceed to medium priority"
        elif len(medium_priority) > 0:
            approach = "No critical issues - verify medium priority claims"
        else:
            approach = "No significant claims require verification"
        
        return {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "total_verification_questions": total_questions,
            "recommended_approach": approach,
            "summary": {
                "total_claims": len(claims),
                "requires_verification": len(high_priority) + len(medium_priority) + len(low_priority),
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority),
                "low_priority_count": len(low_priority)
            }
        }
    
    
    def categorize_claims_by_risk(
        self,
        claims: List[ExtractedClaim]
    ) -> Dict[str, List[ExtractedClaim]]:
        """
        Categorize claims by risk level
        
        Returns:
            {
                "critical": [contradictions, false claims],
                "high": [suspicious, unrealistic],
                "medium": [vague],
                "low": [verifiable, no red flags]
            }
        """
        
        categorized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for claim in claims:
            # Critical: Contradictions
            if claim.verifiability == ClaimVerifiability.CONTRADICTORY:
                categorized["critical"].append(claim)
            
            # High: Suspicious or has red flags
            elif claim.verifiability == ClaimVerifiability.SUSPICIOUS or claim.red_flags:
                categorized["high"].append(claim)
            
            # Medium: Vague
            elif claim.verifiability == ClaimVerifiability.VAGUE:
                categorized["medium"].append(claim)
            
            # Low: Verifiable without issues
            else:
                categorized["low"].append(claim)
        
        return categorized
    
    
    def _is_unrealistic_metric(self, claim_text: str) -> bool:
        """
        Check if a metric claim seems unrealistic
        
        Examples of unrealistic claims:
        - "100% uptime" without HA explanation
        - "10 million requests" from single server
        - "Zero bugs" in production
        """
        
        claim_lower = claim_text.lower()
        
        # 100% or perfect claims
        perfect_patterns = ["100%", "perfect", "zero bugs", "no downtime", "flawless"]
        if any(pattern in claim_lower for pattern in perfect_patterns):
            # Check if they explain how they achieved perfection
            explanation_indicators = [
                "redundancy", "failover", "distributed", "replicated",
                "load balanced", "multiple", "backup"
            ]
            has_explanation = any(ind in claim_lower for ind in explanation_indicators)
            
            if not has_explanation:
                return True  # Unrealistic - no explanation
        
        # Extreme scale without infrastructure mention
        scale_keywords = ["million", "billion", "thousands", "enterprise"]
        has_scale = any(kw in claim_lower for kw in scale_keywords)
        
        if has_scale:
            infrastructure_indicators = [
                "server", "cache", "distributed", "cluster", "node",
                "instance", "kubernetes", "docker", "cloud", "aws", "gcp"
            ]
            has_infrastructure = any(ind in claim_lower for ind in infrastructure_indicators)
            
            if not has_infrastructure:
                return True  # Unrealistic - scale without infrastructure
        
        return False
    
    
    def get_claim_summary(self, claims: List[ExtractedClaim]) -> Dict:
        """
        Generate summary statistics for claims
        
        Returns:
            Dictionary with claim statistics
        """
        
        return {
            "total_claims": len(claims),
            "by_type": {
                claim_type.value: len([
                    c for c in claims if c.claim_type == claim_type
                ])
                for claim_type in ClaimType
            },
            "by_verifiability": {
                verif.value: len([
                    c for c in claims if c.verifiability == verif
                ])
                for verif in ClaimVerifiability
            },
            "requires_verification": len([
                c for c in claims if c.requires_verification
            ]),
            "with_red_flags": len([
                c for c in claims if c.red_flags
            ]),
            "average_priority": (
                sum(c.priority for c in claims) / len(claims)
                if claims else 0
            )
        }


# ============================================
# STANDALONE TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("CLAIM ANALYZER TEST")
    print("=" * 60)
    
    # Create test claims
    from datetime import datetime
    
    test_claims = [
        ExtractedClaim(
            claim_id="claim_1",
            claim_text="I optimized the system",
            claim_type=ClaimType.TECHNICAL_ACHIEVEMENT,
            source_question_id="q1",
            source_answer_id="a1",
            session_id="test",
            verifiability=ClaimVerifiability.VAGUE,
            requires_verification=True,
            verification_questions=["What specifically did you optimize?"],
            priority=8,
            red_flags=["Vague optimization without metrics"]
        ),
        ExtractedClaim(
            claim_id="claim_2",
            claim_text="Handled 10 million requests per day",
            claim_type=ClaimType.PROJECT_SCALE,
            source_question_id="q1",
            source_answer_id="a1",
            session_id="test",
            verifiability=ClaimVerifiability.VERIFIABLE,
            requires_verification=True,
            verification_questions=["What caching strategy?", "What database?"],
            priority=9,
            red_flags=[]
        ),
        ExtractedClaim(
            claim_id="claim_3",
            claim_text="I used machine learning",
            claim_type=ClaimType.TOOL_EXPERTISE,
            source_question_id="q1",
            source_answer_id="a1",
            session_id="test",
            verifiability=ClaimVerifiability.VAGUE,
            requires_verification=True,
            verification_questions=["What ML algorithm?"],
            priority=6,
            red_flags=["Technology buzzword without depth"]
        )
    ]
    
    analyzer = ClaimAnalyzer()
    
    # Test prioritization
    print("\n1. Testing Prioritization:")
    priority_claims = analyzer.prioritize_claims(test_claims, max_claims=2)
    
    # Test verification strategy
    print("\n2. Testing Verification Strategy:")
    strategy = analyzer.generate_verification_strategy(test_claims)
    print(f"   High priority: {len(strategy['high_priority'])}")
    print(f"   Medium priority: {len(strategy['medium_priority'])}")
    print(f"   Approach: {strategy['recommended_approach']}")
    
    # Test categorization
    print("\n3. Testing Risk Categorization:")
    categorized = analyzer.categorize_claims_by_risk(test_claims)
    for risk_level, claims in categorized.items():
        print(f"   {risk_level}: {len(claims)} claims")
    
    # Test summary
    print("\n4. Testing Summary:")
    summary = analyzer.get_claim_summary(test_claims)
    print(f"   Total claims: {summary['total_claims']}")
    print(f"   Require verification: {summary['requires_verification']}")
    print(f"   With red flags: {summary['with_red_flags']}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)