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

    def __init__(self):
        self.strategies = {
            "FALSE_CLAIM":          self._generate_false_claim_followup,
            "CONTRADICTION":        self._generate_contradiction_followup,
            "DODGING_QUESTION":     self._generate_dodging_followup,
            "EXCESSIVE_RAMBLING":   self._generate_rambling_followup,
            "FILLER_HEAVY":         self._generate_rambling_followup,
            "VAGUE_ANSWER":         self._generate_vague_followup,
            "VAGUE_EVASION":        self._generate_vague_followup,
            "LACK_OF_SPECIFICS":    self._generate_specifics_followup,
            "COMPLETELY_OFF_TOPIC": self._generate_offtopic_followup,
            "EXCESSIVE_PAUSING":    self._generate_pausing_followup,
            "STRUGGLING":           self._generate_pausing_followup,
            "HIGH_UNCERTAINTY":     self._generate_uncertainty_followup,
            "MINOR_UNCERTAINTY":    self._generate_uncertainty_followup,
            "MANIPULATION_ATTEMPT": self._generate_dodging_followup,
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
        print(f"\n💡 Generating follow-up for: {interruption_reason}")

        strategy_func = self.strategies.get(
            interruption_reason,
            self._generate_generic_followup
        )

        followup = strategy_func(
            partial_answer=partial_answer,
            original_question=original_question,
            conversation_history=conversation_history,
            evidence=evidence
        )

        print(f"   ✓ Generated: {followup[:80]}...")
        return followup

    # ── Strategies ────────────────────────────────────────────────────────────

    def _generate_false_claim_followup(self, partial_answer, original_question,
                                        conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a technical interviewer who just detected a false or incorrect claim.\n\n"
                    f"ORIGINAL QUESTION:\n\"{original_question}\"\n\n"
                    f"WHAT THEY SAID:\n\"{partial_answer}\"\n\n"
                    f"ISSUE DETECTED:\n{evidence}\n\n"
                    "Generate ONE sharp follow-up question that points out the inaccuracy "
                    "and asks them to clarify. 1 sentence max. "
                    "Output ONLY the question with NO preamble, NO intro phrase, NO 'here is' prefix."
                )
            },
            {"role": "user", "content": "Generate the follow-up question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_contradiction_followup(self, partial_answer, original_question,
                                          conversation_history, evidence):
        history_context = self._build_history_snippet(conversation_history, limit=2)
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer who detected a contradiction.\n\n"
                    f"RECENT CONVERSATION:\n{history_context}\n\n"
                    f"CURRENT QUESTION:\n\"{original_question}\"\n\n"
                    f"WHAT THEY JUST SAID:\n\"{partial_answer}\"\n\n"
                    "Generate ONE question highlighting the contradiction and asking them "
                    "to clarify which statement is correct. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_dodging_followup(self, partial_answer, original_question,
                                    conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer. The candidate is avoiding answering directly.\n\n"
                    f"YOU ASKED:\n\"{original_question}\"\n\n"
                    f"THEY SAID:\n\"{partial_answer}\"\n\n"
                    "Generate ONE redirect question that brings them back to the actual question "
                    "and is specific about what you want to know. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_rambling_followup(self, partial_answer, original_question,
                                     conversation_history, evidence):
        import re
        numbers = re.findall(r'\d+', partial_answer)
        tech_terms = re.findall(
            r'\b(database|api|server|cache|redis|postgres|mongodb|kubernetes)\b',
            partial_answer.lower()
        )
        focus_point = ""
        if numbers:
            focus_point = f"They mentioned {numbers[0]}. "
        elif tech_terms:
            focus_point = f"They mentioned {tech_terms[0]}. "

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer. The candidate is rambling.\n\n"
                    f"ORIGINAL QUESTION:\n\"{original_question}\"\n\n"
                    f"THEY'VE BEEN SAYING:\n\"{partial_answer[:200]}...\"\n\n"
                    f"{focus_point}"
                    "Generate ONE focused question asking them to get to the point "
                    "and focus on ONE specific aspect. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_vague_followup(self, partial_answer, original_question,
                                  conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer. The candidate is being too vague.\n\n"
                    f"QUESTION:\n\"{original_question}\"\n\n"
                    f"THEIR VAGUE ANSWER:\n\"{partial_answer}\"\n\n"
                    "Generate ONE question demanding a concrete example, number, or specific tool. "
                    "1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_specifics_followup(self, partial_answer, original_question,
                                      conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer demanding concrete details.\n\n"
                    f"QUESTION:\n\"{original_question}\"\n\n"
                    f"THEIR ANSWER SO FAR:\n\"{partial_answer}\"\n\n"
                    "Generate ONE sharp question demanding exact numbers, specific tool names, "
                    "or measurable outcomes. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_offtopic_followup(self, partial_answer, original_question,
                                     conversation_history, evidence):
        """
        FIX: Previously hardcoded a preamble phrase causing duplication with
        the interruption phrase shown in the UI. Now uses LLM to return a
        clean redirect question only.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer. The candidate went completely off-topic.\n\n"
                    f"ORIGINAL QUESTION:\n\"{original_question}\"\n\n"
                    f"WHAT THEY SAID INSTEAD:\n\"{partial_answer}\"\n\n"
                    "Generate ONE direct question that redirects them to answer the original question. "
                    "Be specific about exactly what you need from them. 1-2 sentences max. "
                    "IMPORTANT: Output ONLY the question itself. "
                    "Do NOT start with 'That\\'s not what I asked', 'Let me be specific', "
                    "or any other preamble — the interviewer already said that. "
                    "Just ask the redirected question directly."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_pausing_followup(self, partial_answer, original_question,
                                    conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"The candidate is struggling or pausing too much.\n\n"
                    f"QUESTION:\n\"{original_question}\"\n\n"
                    f"WHAT THEY'VE MANAGED TO SAY:\n\"{partial_answer}\"\n\n"
                    "Generate ONE simpler, more specific version of the question "
                    "that focuses on just ONE aspect to help them. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_uncertainty_followup(self, partial_answer, original_question,
                                        conversation_history, evidence):
        messages = [
            {
                "role": "system",
                "content": (
                    f"The candidate sounds very uncertain.\n\n"
                    f"QUESTION:\n\"{original_question}\"\n\n"
                    f"THEIR UNCERTAIN ANSWER:\n\"{partial_answer}\"\n\n"
                    "Generate ONE question asking if they're confident in what they said "
                    "or would like to reconsider. 1 sentence max. "
                    "Output ONLY the question with NO preamble."
                )
            },
            {"role": "user", "content": "Generate the question."}
        ]
        return self._call_llm_and_clean(messages)

    def _generate_generic_followup(self, partial_answer, original_question,
                                    conversation_history, evidence):
        return "Can you clarify what you meant and be more specific?"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _call_llm_and_clean(self, messages: List[Dict]) -> str:
        try:
            raw_response = get_llm_response(messages, temperature=0.7)
            question = raw_response.strip()

            # Remove markdown
            question = question.replace("**", "").replace("*", "")

            # Remove common LLM preamble prefixes
            prefixes = [
                "Question:", "Q:", "Follow-up:", "Here's the question:",
                "Follow-up question:", "I would ask:", "Here is the question:",
                "Here is a follow-up question:", "Sure,", "Certainly,",
                "That's not what I asked.", "Let me be specific:",
                "That's not what I asked. Let me be specific:",
            ]
            for prefix in prefixes:
                if question.lower().startswith(prefix.lower()):
                    question = question[len(prefix):].strip()

            # Remove surrounding quotes
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            if question.startswith("'") and question.endswith("'"):
                question = question[1:-1]

            # Ensure ends with question mark
            if not question.endswith('?'):
                question += '?'

            return question

        except Exception as e:
            print(f"❌ LLM call failed: {str(e)}")
            return "Can you clarify what you just said?"

    def _build_history_snippet(self, conversation_history: List[Dict], limit: int = 2) -> str:
        if not conversation_history:
            return "No previous context."
        recent = conversation_history[-limit:]
        parts = []
        for i, item in enumerate(recent, 1):
            q = item.get('question', '')[:80]
            a = item.get('answer', '')[:100]
            parts.append(f"{i}. Q: {q}\n   A: {a}...")
        return "\n".join(parts)


# ── Singleton ──────────────────────────────────────────────────────────────────

_generator_instance = None

def get_followup_generator() -> FollowUpGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = FollowUpGenerator()
    return _generator_instance