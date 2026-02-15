"""
Intelligent Follow-Up Question Generator
=========================================

Generates contextual, sharp follow-up questions after interruptions.

The follow-up should:
1. Reference what the candidate just said
2. Probe the specific weakness detected
3. Be brief and direct (1 sentence)
4. Maintain professional but firm tone
5. Push for specifics, not generalities
"""

from typing import Dict, List, Optional
from llm_service import get_llm_response


class FollowUpGenerator:
    """
    Generates intelligent follow-up questions post-interruption
    
    Each interruption reason gets a specific follow-up strategy.
    """
    
    def __init__(self):
        # Define follow-up strategies per interruption reason
        self.strategies = {
            "FALSE_CLAIM": self._generate_false_claim_followup,
            "CONTRADICTION": self._generate_contradiction_followup,
            "DODGING_QUESTION": self._generate_dodging_followup,
            "EXCESSIVE_RAMBLING": self._generate_rambling_followup,
            "VAGUE_ANSWER": self._generate_vague_followup,
            "LACK_OF_SPECIFICS": self._generate_specifics_followup,
            "COMPLETELY_OFF_TOPIC": self._generate_offtopic_followup,
            "EXCESSIVE_PAUSING": self._generate_pausing_followup,
            "HIGH_UNCERTAINTY": self._generate_uncertainty_followup,
        }
        
        print("✅ Follow-Up Generator initialized")
    
    
    def generate_followup(
        self,
        interruption_reason: str,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str = ""
    ) -> str:
        """
        Generate follow-up question based on interruption reason
        
        Args:
            interruption_reason: Why we interrupted
            partial_answer: What they said before interruption
            original_question: The question they were answering
            conversation_history: Previous Q&As
            evidence: Specific evidence for the interruption
            
        Returns:
            Follow-up question string
        """
        
        print(f"\n💡 Generating follow-up for: {interruption_reason}")
        
        # Get appropriate strategy
        strategy_func = self.strategies.get(
            interruption_reason,
            self._generate_generic_followup
        )
        
        # Generate follow-up
        followup = strategy_func(
            partial_answer=partial_answer,
            original_question=original_question,
            conversation_history=conversation_history,
            evidence=evidence
        )
        
        print(f"   ✓ Generated: {followup[:80]}...")
        
        return followup
    
    
    def _generate_false_claim_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for false technical claim"""
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a technical interviewer who just detected a false or incorrect claim.

ORIGINAL QUESTION:
"{original_question}"

WHAT THEY SAID:
"{partial_answer}"

ISSUE DETECTED:
{evidence}

Generate ONE sharp, direct follow-up question that:
1. Points out the specific inaccuracy
2. Asks them to clarify or correct their statement
3. Is 1 sentence maximum
4. Maintains professional but firm tone

Example: "That's not quite right - Redis is not a relational database. Can you clarify what you meant?"

Output ONLY the question, nothing else."""
            },
            {
                "role": "user",
                "content": "Generate the follow-up question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_contradiction_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for contradiction with previous answer"""
        
        # Get recent history context
        history_context = self._build_history_snippet(conversation_history, limit=2)
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an interviewer who detected a contradiction.

RECENT CONVERSATION:
{history_context}

CURRENT QUESTION:
"{original_question}"

WHAT THEY JUST SAID:
"{partial_answer}"

ISSUE:
This contradicts something they said earlier.

Generate ONE direct question that:
1. Highlights the contradiction
2. Asks them to clarify which statement is correct
3. Is brief and firm

Example: "Wait - earlier you said you led the team, but now you're saying you assisted. Which was it?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_dodging_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up when candidate is dodging the question"""
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an interviewer. The candidate is avoiding answering your question directly.

YOU ASKED:
"{original_question}"

THEY SAID:
"{partial_answer}"

ISSUE:
They're not directly answering what you asked.

Generate ONE redirect question that:
1. Brings them back to the actual question
2. Is specific about what you want to know
3. Is direct and firm

Example: "Let me stop you - I asked about your PERSONAL role, not the team's. What did YOU specifically do?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_rambling_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for excessive rambling"""
        
        # Extract a potential specific detail to focus on
        words = partial_answer.split()
        
        # Look for something concrete to anchor on
        import re
        numbers = re.findall(r'\d+', partial_answer)
        tech_terms = re.findall(r'\b(database|api|server|cache|redis|postgres|mongodb|kubernetes)\b', 
                                partial_answer.lower())
        
        focus_point = ""
        if numbers:
            focus_point = f"You mentioned {numbers[0]}. "
        elif tech_terms:
            focus_point = f"You mentioned {tech_terms[0]}. "
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an interviewer. The candidate is rambling and needs to focus.

ORIGINAL QUESTION:
"{original_question}"

THEY'VE BEEN SAYING:
"{partial_answer[:200]}..."

{focus_point}

Generate ONE focused question that:
1. Asks them to get to the point
2. Focuses on ONE specific aspect
3. Demands brevity

Example: "Let me stop you - just tell me the RESULT in one sentence."

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_vague_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for vague answer lacking specifics"""
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an interviewer. The candidate is being too vague and general.

QUESTION:
"{original_question}"

THEIR VAGUE ANSWER:
"{partial_answer}"

Generate ONE demand for specifics:
1. Ask for concrete examples
2. Ask for numbers/metrics
3. Ask for specific technologies/tools
4. Be direct

Example: "That's too general - give me a specific metric. How much did performance improve?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_specifics_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up demanding concrete details"""
        
        # Similar to vague but more aggressive
        messages = [
            {
                "role": "system",
                "content": f"""You are an interviewer demanding concrete details.

QUESTION:
"{original_question}"

THEIR ANSWER SO FAR:
"{partial_answer}"

Generate ONE sharp question demanding specifics:
1. Ask for exact numbers
2. Ask for specific names (tools, frameworks, etc.)
3. Ask for measurable outcomes
4. Be firm and direct

Example: "I need specifics - what EXACT tool did you use and what were the NUMBERS?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_offtopic_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up when completely off-topic"""
        
        # Very direct redirect
        return f"That's not what I asked. Let me be specific: {original_question}"
    
    
    def _generate_pausing_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for excessive pausing/struggling"""
        
        messages = [
            {
                "role": "system",
                "content": f"""The candidate is struggling with long pauses.

QUESTION:
"{original_question}"

WHAT THEY'VE MANAGED TO SAY:
"{partial_answer}"

Generate ONE simpler, more specific question to help them:
1. Break down the original question into something easier
2. Focus on just ONE aspect
3. Make it a yes/no or concrete question

Example: "Let me help you focus - did you personally write the code for this, yes or no?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_uncertainty_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Follow-up for high uncertainty/lack of confidence"""
        
        messages = [
            {
                "role": "system",
                "content": f"""The candidate sounds very uncertain and lacks confidence.

QUESTION:
"{original_question}"

THEIR UNCERTAIN ANSWER:
"{partial_answer}"

Generate ONE question that:
1. Asks if they're confident in what they just said
2. Gives them a chance to reconsider
3. Is direct but not harsh

Example: "You sound unsure - are you confident in that answer, or would you like to reconsider?"

Output ONLY the question."""
            },
            {
                "role": "user",
                "content": "Generate the question."
            }
        ]
        
        return self._call_llm_and_clean(messages)
    
    
    def _generate_generic_followup(
        self,
        partial_answer: str,
        original_question: str,
        conversation_history: List[Dict],
        evidence: str
    ) -> str:
        """Generic follow-up for unknown interruption type"""
        
        return f"Let me stop you there. Can you clarify what you meant by that?"
    
    
    def _call_llm_and_clean(self, messages: List[Dict]) -> str:
        """Call LLM and clean up the response"""
        
        try:
            raw_response = get_llm_response(messages, temperature=0.7)
            
            # Clean response
            question = raw_response.strip()
            
            # Remove markdown
            question = question.replace("**", "").replace("*", "")
            
            # Remove common prefixes
            prefixes = [
                "Question:", "Q:", "Follow-up:", "Here's the question:",
                "Follow-up question:", "I would ask:"
            ]
            for prefix in prefixes:
                if question.lower().startswith(prefix.lower()):
                    question = question[len(prefix):].strip()
            
            # Remove quotes
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            if question.startswith("'") and question.endswith("'"):
                question = question[1:-1]
            
            # Ensure it's a question
            if not question.endswith('?'):
                question += '?'
            
            return question
        
        except Exception as e:
            print(f"❌ LLM call failed: {str(e)}")
            return "Can you clarify what you just said?"
    
    
    def _build_history_snippet(
        self,
        conversation_history: List[Dict],
        limit: int = 2
    ) -> str:
        """Build brief context from conversation history"""
        
        if not conversation_history:
            return "No previous context."
        
        recent = conversation_history[-limit:]
        
        snippet_parts = []
        for i, item in enumerate(recent, 1):
            q = item.get('question', '')[:80]
            a = item.get('answer', '')[:100]
            snippet_parts.append(f"{i}. Q: {q}\n   A: {a}...")
        
        return "\n".join(snippet_parts)


# ============================================
# SINGLETON
# ============================================

_generator_instance = None

def get_followup_generator() -> FollowUpGenerator:
    """Get singleton instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = FollowUpGenerator()
    return _generator_instance


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("FOLLOW-UP GENERATOR TEST")
    print("=" * 70)
    
    generator = get_followup_generator()
    
    # Test 1: Rambling
    print("\n\nTEST 1: Rambling Answer")
    print("-" * 70)
    
    rambling_answer = """
    Um, so like, we had this issue with the database, and, uh, basically
    what happened was that we tried a bunch of things, you know, and some
    of them worked and some didn't, and eventually we got it sorted out...
    """
    
    followup = generator.generate_followup(
        interruption_reason="EXCESSIVE_RAMBLING",
        partial_answer=rambling_answer,
        original_question="How did you optimize the database queries?",
        conversation_history=[],
        evidence="Too many filler words"
    )
    
    print(f"\nFollow-up: {followup}")
    
    # Test 2: Vague Answer
    print("\n\nTEST 2: Vague Answer")
    print("-" * 70)
    
    vague_answer = """
    We improved the system performance significantly. The users were very
    happy with the results. We used best practices and modern technologies.
    """
    
    followup = generator.generate_followup(
        interruption_reason="VAGUE_ANSWER",
        partial_answer=vague_answer,
        original_question="What caching strategy did you implement?",
        conversation_history=[],
        evidence="No concrete metrics or specifics"
    )
    
    print(f"\nFollow-up: {followup}")
    
    # Test 3: Dodging Question
    print("\n\nTEST 3: Dodging Question")
    print("-" * 70)
    
    dodging_answer = """
    Well, the team worked really hard on this project. Everyone contributed
    in different ways. It was a collaborative effort with good communication.
    """
    
    followup = generator.generate_followup(
        interruption_reason="DODGING_QUESTION",
        partial_answer=dodging_answer,
        original_question="What was YOUR specific contribution to the project?",
        conversation_history=[],
        evidence="Not answering the personal role question"
    )
    
    print(f"\nFollow-up: {followup}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)