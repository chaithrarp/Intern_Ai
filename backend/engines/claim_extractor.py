"""
Claim Extractor Engine
======================

Extracts verifiable claims from candidate answers using LLM.

Key Features:
- Extracts all types of claims (technical, metrics, tools, etc)
- Categorizes by verifiability (verifiable, vague, suspicious, contradictory)
- Generates verification questions
- Detects contradictions with previous answers
- Prioritizes claims for verification
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid

# Import your existing LLM service
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import get_llm_response

# Import new models and prompts
from models.interview_models import (
    ExtractedClaim,
    ClaimType,
    ClaimVerifiability
)

from prompt_templates.claim_prompts import (
    build_claim_extraction_prompt,
    build_contradiction_check_prompt,
    parse_claim_extraction_output,
    parse_contradiction_output
)

from config.evaluation_config import CLAIM_PRIORITY_RULES


# ============================================
# CLAIM EXTRACTOR CLASS
# ============================================

class ClaimExtractor:
    """
    Extracts and analyzes claims from candidate answers
    
    Usage:
        extractor = ClaimExtractor()
        
        claims = extractor.extract_claims(
            answer_text="I optimized database to handle 10M requests",
            question_text="Tell me about your database work",
            question_id="q_003",
            answer_id="a_003",
            session_id="session_001",
            conversation_history=[...]
        )
    """
    
    def __init__(self):
        self.extracted_claims = []  # Store all extracted claims
    
    
    def extract_claims(
        self,
        answer_text: str,
        question_text: str,
        question_id: str,
        answer_id: str,
        session_id: str,
        conversation_history: List[Dict] = None
    ) -> List[ExtractedClaim]:
        """
        Extract all claims from an answer
        
        Args:
            answer_text: The candidate's answer
            question_text: The question they were answering
            question_id: Question identifier
            answer_id: Answer identifier
            session_id: Session identifier
            conversation_history: Previous Q&A for contradiction detection
        
        Returns:
            List of ExtractedClaim objects
        """
        
        print(f"\n🔍 Extracting claims from answer to Q{question_id}...")
        
        try:
            # Step 1: Extract claims using LLM
            claims_data = self._extract_claims_with_llm(
                answer_text,
                question_text,
                conversation_history or []
            )
            
            if not claims_data:
                print("   No claims found in this answer")
                return []
            
            print(f"   Found {len(claims_data)} potential claims")
            
            # Step 2: Check for contradictions
            contradiction_info = None
            if conversation_history:
                contradiction_info = self._check_contradictions(
                    answer_text,
                    conversation_history
                )
            
            # Step 3: Convert to ExtractedClaim objects
            extracted_claims = []
            
            for i, claim_data in enumerate(claims_data, 1):
                claim_id = f"claim_{session_id}_{answer_id}_{i}"
                
                # Determine if this claim is contradictory
                is_contradictory = (
                    contradiction_info and 
                    contradiction_info.get("contradiction_found", False)
                )
                
                # Override verifiability if contradiction detected
                verifiability = claim_data.get("verifiability", "verifiable")
                if is_contradictory:
                    verifiability = "contradictory"
                
                # Build red flags
                red_flags = claim_data.get("red_flags", [])
                if is_contradictory and contradiction_info:
                    red_flags.append(
                        f"CONTRADICTION: {contradiction_info.get('explanation', 'Contradicts previous answer')}"
                    )
                
                # Create ExtractedClaim object
                claim = ExtractedClaim(
                    claim_id=claim_id,
                    claim_text=claim_data["claim_text"],
                    claim_type=self._parse_claim_type(claim_data["claim_type"]),
                    source_question_id=question_id,
                    source_answer_id=answer_id,
                    session_id=session_id,
                    verifiability=self._parse_verifiability(verifiability),
                    requires_verification=self._should_verify_claim(
                        claim_data,
                        verifiability
                    ),
                    verification_questions=claim_data.get("verification_questions", []),
                    priority=claim_data.get("priority", 5),
                    red_flags=red_flags
                )
                
                extracted_claims.append(claim)
                
                print(f"   ✓ Claim {i}: {claim.claim_text[:50]}...")
                print(f"     Type: {claim.claim_type.value}, Priority: {claim.priority}")
                
                if claim.requires_verification:
                    print(f"     ⚠️ Requires verification")
            
            # Store for reference
            self.extracted_claims.extend(extracted_claims)
            
            return extracted_claims
        
        except Exception as e:
            print(f"❌ Error extracting claims: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    
    def _extract_claims_with_llm(
        self,
        answer_text: str,
        question_text: str,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """
        Use LLM to extract claims from answer
        
        Returns:
            List of claim dictionaries
        """
        
        try:
            # Build prompt
            messages = build_claim_extraction_prompt(
                answer_text=answer_text,
                question_text=question_text,
                conversation_history=conversation_history
            )
            
            # Call LLM
            raw_response = get_llm_response(messages, temperature=0.3)
            
            # Parse response
            claims = parse_claim_extraction_output(raw_response)
            
            return claims
        
        except Exception as e:
            print(f"Error in LLM claim extraction: {str(e)}")
            return []
    
    
    def _check_contradictions(
        self,
        current_answer: str,
        conversation_history: List[Dict]
    ) -> Optional[Dict]:
        """
        Check if current answer contradicts previous statements
        
        Returns:
            Dictionary with contradiction info or None
        """
        
        try:
            # Build prompt
            messages = build_contradiction_check_prompt(
                current_answer=current_answer,
                conversation_history=conversation_history
            )
            
            # Call LLM
            raw_response = get_llm_response(messages, temperature=0.2)
            
            # Parse response
            contradiction_info = parse_contradiction_output(raw_response)
            
            if contradiction_info.get("contradiction_found"):
                print(f"   🚨 CONTRADICTION DETECTED!")
                print(f"      Previous: {contradiction_info.get('previous_statement', '')[:60]}...")
                print(f"      Current: {contradiction_info.get('current_statement', '')[:60]}...")
            
            return contradiction_info
        
        except Exception as e:
            print(f"Error checking contradictions: {str(e)}")
            return None
    
    
    def _parse_claim_type(self, type_str: str) -> ClaimType:
        """Convert string to ClaimType enum"""
        type_map = {
            "technical_achievement": ClaimType.TECHNICAL_ACHIEVEMENT,
            "metric": ClaimType.METRIC,
            "tool_expertise": ClaimType.TOOL_EXPERTISE,
            "role_responsibility": ClaimType.ROLE_RESPONSIBILITY,
            "project_scale": ClaimType.PROJECT_SCALE,
            "problem_solved": ClaimType.PROBLEM_SOLVED,
            "architecture_decision": ClaimType.ARCHITECTURE_DECISION
        }
        
        return type_map.get(type_str.lower(), ClaimType.TECHNICAL_ACHIEVEMENT)
    
    
    def _parse_verifiability(self, verif_str: str) -> ClaimVerifiability:
        """Convert string to ClaimVerifiability enum"""
        verif_map = {
            "verifiable": ClaimVerifiability.VERIFIABLE,
            "vague": ClaimVerifiability.VAGUE,
            "suspicious": ClaimVerifiability.SUSPICIOUS,
            "contradictory": ClaimVerifiability.CONTRADICTORY
        }
        
        return verif_map.get(verif_str.lower(), ClaimVerifiability.VERIFIABLE)
    
    
    def _should_verify_claim(
        self,
        claim_data: Dict,
        verifiability: str
    ) -> bool:
        """
        Determine if claim needs verification
        
        Verify if:
        - Priority >= 7 (high priority)
        - Verifiability is vague/suspicious/contradictory
        - Has red flags
        """
        
        priority = claim_data.get("priority", 5)
        red_flags = claim_data.get("red_flags", [])
        
        # Always verify contradictions
        if verifiability == "contradictory":
            return True
        
        # Verify high priority claims
        if priority >= 7:
            return True
        
        # Verify suspicious/vague claims
        if verifiability in ["suspicious", "vague"]:
            return True
        
        # Verify if has red flags
        if red_flags:
            return True
        
        return False
    
    
    def get_unverified_claims(
        self,
        session_id: str,
        min_priority: int = 7
    ) -> List[ExtractedClaim]:
        """
        Get all unverified claims for a session
        
        Args:
            session_id: Session to filter by
            min_priority: Only return claims with priority >= this
        
        Returns:
            List of unverified claims sorted by priority
        """
        
        unverified = [
            claim for claim in self.extracted_claims
            if claim.session_id == session_id
            and claim.requires_verification
            and claim.verification_result is None  # Not yet verified
            and claim.priority >= min_priority
        ]
        
        # Sort by priority (highest first)
        unverified.sort(key=lambda c: c.priority, reverse=True)
        
        return unverified
    
    
    def get_claims_by_type(
        self,
        session_id: str,
        claim_type: ClaimType
    ) -> List[ExtractedClaim]:
        """Get all claims of a specific type for a session"""
        
        return [
            claim for claim in self.extracted_claims
            if claim.session_id == session_id
            and claim.claim_type == claim_type
        ]
    
    
    def get_red_flag_claims(self, session_id: str) -> List[ExtractedClaim]:
        """Get all claims with red flags for a session"""
        
        return [
            claim for claim in self.extracted_claims
            if claim.session_id == session_id
            and len(claim.red_flags) > 0
        ]
    
    
    def mark_claim_verified(
        self,
        claim_id: str,
        verification_result: Dict
    ):
        """
        Mark a claim as verified with result
        
        Args:
            claim_id: Claim to mark
            verification_result: Verification data (from ClaimVerification model)
        """
        
        for claim in self.extracted_claims:
            if claim.claim_id == claim_id:
                claim.verification_result = verification_result
                claim.verified_at = datetime.now()
                print(f"✓ Marked claim verified: {claim.claim_text[:50]}...")
                break


# ============================================
# STANDALONE TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("CLAIM EXTRACTOR TEST")
    print("=" * 60)
    
    extractor = ClaimExtractor()
    
    # Test answer with multiple claims
    test_answer = """
    I led a team of 5 engineers to build a distributed system that handles 
    10 million requests per day. We used microservices architecture with 
    Redis caching and achieved 99.9% uptime. I personally optimized the 
    database queries which reduced latency by 50%.
    """
    
    test_question = "Tell me about your most significant project."
    
    # Extract claims
    claims = extractor.extract_claims(
        answer_text=test_answer,
        question_text=test_question,
        question_id="test_q1",
        answer_id="test_a1",
        session_id="test_session",
        conversation_history=[]
    )
    
    print(f"\n✅ Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"\n{i}. {claim.claim_text}")
        print(f"   Type: {claim.claim_type.value}")
        print(f"   Priority: {claim.priority}/10")
        print(f"   Requires verification: {claim.requires_verification}")
        if claim.verification_questions:
            print(f"   Verification questions:")
            for q in claim.verification_questions:
                print(f"     - {q}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)