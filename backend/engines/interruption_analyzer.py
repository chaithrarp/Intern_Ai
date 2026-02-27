"""
Enhanced Intelligent Interruption Analyzer  v4
===============================================

KEY CHANGES FROM v3:
- Equal-chance selection: when multiple reasons fire, one is picked at RANDOM
  (no more hard priority ordering that always favours OFF_TOPIC)
- Per-question occurrence counter: resets each new question so thresholds
  are evaluated fresh every time
- "Struggling" composite signal: long pauses + fillers together can trigger
- Correct MAX_INTERRUPTIONS read from config (no more hardcoded 2)
- LLM layer fires at 120 chars (was 200) — catches shorter rambly answers
- Each interrupt reason carries a human-readable "display_reason" for the UI
- No threshold=999 special-casing: warn-only reasons are just excluded from
  the interrupt candidate pool (cleaner logic)

Interrupt reasons and what triggers them:
  FILLER_HEAVY         — >22% filler word density
  EXCESSIVE_RAMBLING   — high repetition OR very long with no structure
  COMPLETELY_OFF_TOPIC — answer shares <15% keyword overlap with question
  DODGING_QUESTION     — answer shares <25% keyword overlap (softer version)
  CONTRADICTION        — contradicts a previous answer on same topic
  VAGUE_EVASION        — 100+ words, zero numbers/examples/tech terms
  MANIPULATION_ATTEMPT — heavy corporate buzzwords / deflection phrases
  FALSE_CLAIM          — LLM flags a factual inconsistency with resume
  STRUGGLING           — composite: pauses + fillers + uncertainty together

Warn-only (never interrupt, just show yellow card):
  LONG_PAUSE, SPEAKING_TOO_LONG, MINOR_UNCERTAINTY
"""

import random
import re
from typing import Dict, List, Optional
from datetime import datetime

from llm_service import get_llm_response
import config


# ─────────────────────────────────────────────────────────────────────────────
# REASON CONFIG
# threshold = occurrences in THIS QUESTION before interrupt fires
# warn_only  = True means it can never become an interrupt
# ─────────────────────────────────────────────────────────────────────────────

REASON_CONFIG = {
    # ── Can interrupt ────────────────────────────────────────────────────────
    "FILLER_HEAVY": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Let me stop you — your answer has too many filler words. Take a breath and give me a clear, direct response.",
        "warn_phrase": "⚠️ Too many filler words — speak clearly.",
        "display_reason": "Seems like you're struggling to express yourself clearly",
        "icon": "💬",
    },
    "EXCESSIVE_RAMBLING": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "I'm going to stop you — you're rambling and going in circles. Get to the core of your answer.",
        "warn_phrase": "⚠️ You're rambling — focus on the key point.",
        "display_reason": "Seems like you're going off on tangents",
        "icon": "🌀",
    },
    "COMPLETELY_OFF_TOPIC": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Let me stop you — that's not what I asked. Please answer the actual question.",
        "warn_phrase": "⚠️ Stay focused on the question.",
        "display_reason": "Seems like you're going off-topic",
        "icon": "🎯",
    },
    "DODGING_QUESTION": {
        "threshold": 2,
        "warn_only": False,
        "phrase": "I need to stop you — you're not addressing what I asked. Let's try again.",
        "warn_phrase": "⚠️ Please address the question directly.",
        "display_reason": "Seems like you're avoiding the question",
        "icon": "❓",
    },
    "CONTRADICTION": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Hold on — that contradicts what you said earlier. Which is it?",
        "warn_phrase": "⚠️ This seems to contradict something you said earlier.",
        "display_reason": "Seems like you're contradicting yourself",
        "icon": "🔄",
    },
    "VAGUE_EVASION": {
        "threshold": 2,
        "warn_only": False,
        "phrase": "Let me stop you — I need specific, concrete answers. Not vague generalities.",
        "warn_phrase": "⚠️ Be more specific — avoid vague statements.",
        "display_reason": "Seems like you're not clear on the concept",
        "icon": "🔍",
    },
    "MANIPULATION_ATTEMPT": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Hold on — I'm not looking for corporate buzzwords. Give me a direct, honest answer.",
        "warn_phrase": "⚠️ Answer directly — avoid deflection.",
        "display_reason": "Seems like you're deflecting instead of answering",
        "icon": "🎭",
    },
    "FALSE_CLAIM": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Hold on — I need to stop you there. That doesn't match what's on your resume.",
        "warn_phrase": "⚠️ Be careful — that claim seems inconsistent with your background.",
        "display_reason": "Seems like that claim doesn't match your background",
        "icon": "📋",
    },
    "STRUGGLING": {
        "threshold": 1,
        "warn_only": False,
        "phrase": "Let me stop you — it seems like you're struggling with this. Take a moment to gather your thoughts and try again.",
        "warn_phrase": "⚠️ Take a breath — collect your thoughts.",
        "display_reason": "Seems like you're struggling with this question",
        "icon": "💭",
    },

    # ── Warn-only (never interrupt) ───────────────────────────────────────────
    "LONG_PAUSE": {
        "threshold": 999,
        "warn_only": True,
        "phrase": "",
        "warn_phrase": "⏸️ Long pause — collect your thoughts and continue.",
        "display_reason": "Long pause detected",
        "icon": "⏸️",
    },
    "SPEAKING_TOO_LONG": {
        "threshold": 999,
        "warn_only": True,
        "phrase": "",
        "warn_phrase": "⏱️ Wrap up your point — you've been speaking for a while.",
        "display_reason": "Speaking for too long",
        "icon": "⏱️",
    },
    "MINOR_UNCERTAINTY": {
        "threshold": 999,
        "warn_only": True,
        "phrase": "",
        "warn_phrase": "💡 Speak with more confidence.",
        "display_reason": "Sounds uncertain",
        "icon": "💡",
    },
}

# ── Pattern lists ──────────────────────────────────────────────────────────────
FILLER_PATTERNS = [
    r'\b(um+|uh+|er+|ah+|umm+|uhh+|hmm+)\b',
    r'\b(like|you know|basically|actually|literally|right)\b',
    r'\b(sort of|kind of|i mean|i guess|i think|you see)\b',
    r'\b(so yeah|and stuff|or whatever|and things like that|you know what i mean)\b',
]

UNCERTAINTY_PATTERNS = [
    r'\b(i think|i believe|maybe|perhaps|possibly|probably)\b',
    r'\b(i guess|i suppose|not sure|might be|could be|seems like)\b',
    r'\b(if i remember correctly|i\'m not entirely sure|correct me if i\'m wrong)\b',
]

MANIPULATION_PATTERNS = [
    r'\b(great question|excellent question|that\'s a fascinating)\b',
    r'\b(going forward|synergy|leverage|value add|circle back|touch base)\b',
    r'\b(at the end of the day|when all is said and done|the bottom line is)\b',
    r'\b(holistic approach|low-hanging fruit|move the needle|deep dive|bandwidth)\b',
]


class EnhancedInterruptionAnalyzer:
    """
    Multi-layer interruption analyzer with equal-chance random selection.

    Session state tracked:
      per_question_counts[session_id][question_id][reason] = int
        — resets each new question
      session_interruption_total[session_id] = int
        — total interrupts fired this session (used for max cap)
    """

    def __init__(self):
        # { session_id: { question_id: { reason: count } } }
        self.per_question_counts: Dict[str, Dict[int, Dict[str, int]]] = {}
        # session_id → total interrupts fired
        self.session_interruption_total: Dict[str, int] = {}
        print("✅ Enhanced Interruption Analyzer v4 initialized (equal-chance mode)")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _get_count(self, session_id: str, question_id: int, reason: str) -> int:
        return (
            self.per_question_counts
            .get(session_id, {})
            .get(question_id, {})
            .get(reason, 0)
        )

    def _increment_count(self, session_id: str, question_id: int, reason: str) -> int:
        self.per_question_counts.setdefault(session_id, {})
        self.per_question_counts[session_id].setdefault(question_id, {})
        old = self.per_question_counts[session_id][question_id].get(reason, 0)
        self.per_question_counts[session_id][question_id][reason] = old + 1
        return old + 1

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN ENTRY
    # ──────────────────────────────────────────────────────────────────────────
    def analyze_for_interruption(
        self,
        session_id: str,
        partial_transcript: str,
        audio_metrics: Dict,
        question_text: str,
        conversation_history: List[Dict],
        recording_duration: float,
        question_id: int = 0,
        current_interruption_count: int = 0,
    ) -> Optional[Dict]:

        max_interrupts = getattr(config, 'MAX_INTERRUPTIONS_PER_SESSION', 2)

        print(f"\n🔍 INTERRUPTION ANALYSIS | session={session_id} | q_id={question_id} | "
              f"duration={recording_duration:.1f}s | chars={len(partial_transcript)} | "
              f"interruptions_so_far={current_interruption_count}/{max_interrupts}")

        # ── Hard gates ─────────────────────────────────────────────────────────
        if question_id <= 0:
            print(f"   🛡️ Skipping — question_id={question_id} is intro/first question")
            return None

        if current_interruption_count >= max_interrupts:
            print(f"   🛡️ Skipping — max interruptions ({max_interrupts}) reached")
            return None

        min_time = getattr(config, 'MIN_INTERRUPTION_TIME', 12)
        if recording_duration < min_time:
            print(f"   ⏳ Too early ({recording_duration:.1f}s < {min_time}s)")
            return None

        all_detected: List[str] = []  # list of triggered reason names

        # === LAYER 1: AUDIO ===
        audio_reasons = self._audio_layer(audio_metrics, recording_duration)
        all_detected.extend(audio_reasons)

        # === LAYER 2: CONTENT ===
        if partial_transcript and len(partial_transcript) > 50:
            content_reasons = self._content_layer(partial_transcript, recording_duration)
            all_detected.extend(content_reasons)

        # === LAYER 3: CONTEXT ===
        if partial_transcript and len(partial_transcript) > 50:
            context_reasons = self._context_layer(partial_transcript, question_text, conversation_history)
            all_detected.extend(context_reasons)

        # === COMPOSITE: STRUGGLING ===
        # Fires if we have BOTH a pause/audio signal AND a filler/uncertainty signal
        has_audio_struggle = "LONG_PAUSE" in all_detected
        has_filler_struggle = any(r in all_detected for r in ("FILLER_HEAVY", "EXCESSIVE_RAMBLING", "MINOR_UNCERTAINTY"))
        if has_audio_struggle and has_filler_struggle:
            all_detected.append("STRUGGLING")
            print("   🧩 Composite STRUGGLING signal detected")

        # === LAYER 4: LLM (only when transcript is long enough and signals exist) ===
        interruptable_detected = [r for r in all_detected if not REASON_CONFIG.get(r, {}).get("warn_only", True)]
        if (partial_transcript
                and len(partial_transcript) >= 120
                and interruptable_detected):
            llm_reasons = self._llm_layer(partial_transcript, question_text, conversation_history)
            all_detected.extend(llm_reasons)

        if not all_detected:
            print("   ✅ No issues detected")
            return None

        # De-duplicate
        all_detected = list(dict.fromkeys(all_detected))
        print(f"   📋 All detected: {all_detected}")

        # ── Separate warn-only from interruptable ─────────────────────────────
        warn_only_reasons = [r for r in all_detected if REASON_CONFIG.get(r, {}).get("warn_only", False)]
        interruptable_reasons = [r for r in all_detected if not REASON_CONFIG.get(r, {}).get("warn_only", False)]

        # ── Decide: interrupt or warn? ─────────────────────────────────────────
        # For each interruptable reason, check if its per-question threshold is reached
        # Use RANDOM selection among eligible reasons — equal chance for all
        eligible_for_interrupt: List[str] = []
        for reason in interruptable_reasons:
            cfg = REASON_CONFIG.get(reason, {})
            count = self._increment_count(session_id, question_id, reason)
            threshold = cfg.get("threshold", 2)
            print(f"   🎰 {reason}: count={count}, threshold={threshold}")
            if count >= threshold:
                eligible_for_interrupt.append(reason)

        if eligible_for_interrupt:
            # EQUAL RANDOM SELECTION — no priority ordering
            chosen = random.choice(eligible_for_interrupt)
            cfg = REASON_CONFIG[chosen]
            print(f"   🔥 INTERRUPT chosen (random from {eligible_for_interrupt}): {chosen}")

            return {
                "should_interrupt": True,
                "action": "interrupt",
                "reason": chosen,
                "display_reason": cfg["display_reason"],
                "interruption_phrase": cfg["phrase"],
                "warn_phrase": cfg["warn_phrase"],
                "icon": cfg.get("icon", "⚠️"),
                "all_detected": all_detected,
            }

        # ── No interrupt threshold reached — pick best warn ───────────────────
        # Warn from interruptable reasons (they're more significant) or warn-only
        warn_candidates = interruptable_reasons if interruptable_reasons else warn_only_reasons
        if warn_candidates:
            # For warns we still pick randomly for equal exposure
            chosen_warn = random.choice(warn_candidates)
            cfg = REASON_CONFIG.get(chosen_warn, {})
            print(f"   ⚠️ WARN chosen (random from {warn_candidates}): {chosen_warn}")

            return {
                "should_interrupt": False,
                "action": "warn",
                "reason": chosen_warn,
                "display_reason": cfg.get("display_reason", chosen_warn),
                "warn_phrase": cfg.get("warn_phrase", "⚠️ Adjust your approach."),
                "icon": cfg.get("icon", "⚠️"),
                "all_detected": all_detected,
            }

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 1: AUDIO
    # ──────────────────────────────────────────────────────────────────────────
    def _audio_layer(self, audio_metrics: Dict, recording_duration: float) -> List[str]:
        reasons = []
        if not audio_metrics:
            return reasons

        for issue in audio_metrics.get('detected_issues', []):
            t = issue.get('type', '')
            if t == 'EXCESSIVE_PAUSING':
                reasons.append("LONG_PAUSE")
            elif t == 'SPEAKING_TOO_LONG':
                reasons.append("SPEAKING_TOO_LONG")

        # Duration-based speaking-too-long (fallback when no issue list)
        if recording_duration > 90 and "SPEAKING_TOO_LONG" not in reasons:
            reasons.append("SPEAKING_TOO_LONG")

        return reasons

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 2: CONTENT
    # ──────────────────────────────────────────────────────────────────────────
    def _content_layer(self, transcript: str, duration: float) -> List[str]:
        reasons = []
        text_lower = transcript.lower()
        words = text_lower.split()
        word_count = len(words)

        if word_count < 15:
            return reasons

        # ── Filler density ─────────────────────────────────────────────────────
        filler_count = sum(len(re.findall(p, text_lower)) for p in FILLER_PATTERNS)
        filler_ratio = filler_count / word_count

        if filler_ratio > 0.22:
            reasons.append("FILLER_HEAVY")
            print(f"   💬 FILLER_HEAVY: {filler_count}/{word_count} words ({filler_ratio*100:.1f}%)")
        elif filler_ratio > 0.15:
            # Moderate fillers count as rambling signal
            reasons.append("EXCESSIVE_RAMBLING")
            print(f"   💬 EXCESSIVE_RAMBLING (filler): {filler_ratio*100:.1f}%")

        # ── Repetition ─────────────────────────────────────────────────────────
        if word_count > 40:
            three_grams = [' '.join(words[i:i+3]) for i in range(len(words) - 2)]
            uniqueness = len(set(three_grams)) / len(three_grams) if three_grams else 1.0
            if uniqueness < 0.50:
                reasons.append("EXCESSIVE_RAMBLING")
                print(f"   🌀 EXCESSIVE_RAMBLING (repetition): uniqueness={uniqueness*100:.0f}%")

        # ── Manipulation / buzzwords ────────────────────────────────────────────
        manip_count = sum(len(re.findall(p, text_lower)) for p in MANIPULATION_PATTERNS)
        if manip_count >= 2 and word_count > 30:
            reasons.append("MANIPULATION_ATTEMPT")

        # ── Vagueness: long answer, zero substance ──────────────────────────────
        has_numbers   = bool(re.search(r'\d+', transcript))
        has_specifics = bool(re.search(r'\b(specifically|for example|for instance|such as|like when|in particular)\b', text_lower))
        has_tech      = bool(re.search(r'\b(api|database|server|cache|queue|algorithm|function|class|service|system|framework|library|tool)\b', text_lower))
        has_proper    = bool(re.search(r'\b[A-Z][a-z]{2,}\b', transcript))

        if word_count > 80 and not has_numbers and not has_specifics and not has_tech and not has_proper:
            reasons.append("VAGUE_EVASION")
            print(f"   🔍 VAGUE_EVASION: {word_count} words, no substance")

        # ── Uncertainty ─────────────────────────────────────────────────────────
        uncertainty_count = sum(len(re.findall(p, text_lower)) for p in UNCERTAINTY_PATTERNS)
        uncertainty_ratio = uncertainty_count / word_count
        if uncertainty_ratio > 0.16:
            reasons.append("MINOR_UNCERTAINTY")

        return reasons

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 3: CONTEXT
    # ──────────────────────────────────────────────────────────────────────────
    def _context_layer(
        self,
        current_answer: str,
        question_text: str,
        conversation_history: List[Dict],
    ) -> List[str]:
        reasons = []
        keywords = self._extract_keywords(question_text)
        answer_lower = current_answer.lower()
        word_count = len(current_answer.split())

        if keywords:
            found = sum(1 for kw in keywords if kw in answer_lower)
            relevance = found / len(keywords)

            if word_count > 40 and relevance < 0.15:
                reasons.append("COMPLETELY_OFF_TOPIC")
                print(f"   🎯 COMPLETELY_OFF_TOPIC: relevance={relevance*100:.0f}%")
            elif word_count > 60 and relevance < 0.25:
                reasons.append("DODGING_QUESTION")
                print(f"   ❓ DODGING_QUESTION: relevance={relevance*100:.0f}%")

        # ── Simple contradiction ────────────────────────────────────────────────
        if conversation_history:
            current_lower = current_answer.lower()
            contradiction_pairs = [
                (r'\byes\b', r'\bno\b'),
                (r'\bdid\b', r'\bdidn\'t\b'),
                (r'\bcan\b', r"\bcan't\b"),
                (r'\bwill\b', r"\bwon't\b"),
                (r'\bhave\b', r"\bhaven't\b"),
                (r'\balways\b', r'\bnever\b'),
            ]
            for prev_qa in conversation_history[-3:]:
                prev = prev_qa.get('answer', '').lower()
                prev_kw = set(self._extract_keywords(prev))
                curr_kw = set(self._extract_keywords(current_answer))
                if len(prev_kw & curr_kw) >= 3:
                    for pos_pat, neg_pat in contradiction_pairs:
                        if (re.search(pos_pat, prev) and re.search(neg_pat, current_lower)) or \
                           (re.search(neg_pat, prev) and re.search(pos_pat, current_lower)):
                            reasons.append("CONTRADICTION")
                            break

        return reasons

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 4: LLM
    # ──────────────────────────────────────────────────────────────────────────
    def _llm_layer(
        self,
        transcript: str,
        question_text: str,
        conversation_history: List[Dict],
    ) -> List[str]:
        reasons = []
        try:
            import json
            history_ctx = ""
            for qa in conversation_history[-2:]:
                history_ctx += f"Q: {qa.get('question','')[:100]}\nA: {qa.get('answer','')[:150]}\n\n"

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a strict interview evaluator. Analyze the candidate's answer.\n\n"
                        f"QUESTION ASKED: \"{question_text}\"\n\n"
                        f"PRIOR CONTEXT:\n{history_ctx or 'None'}\n\n"
                        f"CANDIDATE ANSWER: \"{transcript}\"\n\n"
                        "Respond ONLY with this JSON (no markdown, no commentary):\n"
                        "{\n"
                        "  \"is_off_topic\": false,\n"
                        "  \"is_dodging\": false,\n"
                        "  \"is_rambling_fillers\": false,\n"
                        "  \"is_vague_evasion\": false,\n"
                        "  \"contains_false_claim\": false,\n"
                        "  \"contradicts_history\": false,\n"
                        "  \"is_manipulative\": false,\n"
                        "  \"answer_quality\": \"good|acceptable|poor\",\n"
                        "  \"explanation\": \"one sentence max\"\n"
                        "}\n\n"
                        "RULES: Only flag OBVIOUS violations. "
                        "If answer_quality is good or acceptable, ALL flags must be false."
                    )
                },
                {"role": "user", "content": "Analyze."}
            ]

            raw = get_llm_response(messages, temperature=0.1)
            clean = raw.strip()
            if clean.startswith('```'):
                clean = re.sub(r'```json\s*|\s*```', '', clean)
            analysis = json.loads(clean)

            if analysis.get('answer_quality') in ('good', 'acceptable'):
                print(f"   🤖 LLM: quality={analysis['answer_quality']} — suppressing all LLM flags")
                return []

            flag_map = {
                'is_off_topic':        'COMPLETELY_OFF_TOPIC',
                'is_dodging':          'DODGING_QUESTION',
                'is_rambling_fillers': 'FILLER_HEAVY',
                'is_vague_evasion':    'VAGUE_EVASION',
                'contradicts_history': 'CONTRADICTION',
                'is_manipulative':     'MANIPULATION_ATTEMPT',
                'contains_false_claim':'FALSE_CLAIM',
            }
            for flag, reason in flag_map.items():
                if analysis.get(flag):
                    reasons.append(reason)
                    print(f"   🤖 LLM flagged: {reason}")

        except Exception as e:
            print(f"   ⚠️ LLM layer failed (non-fatal): {e}")

        return reasons

    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────────
    def _extract_keywords(self, text: str) -> List[str]:
        stop = {
            'the','a','an','and','or','but','in','on','at','to','for','of','with',
            'by','from','as','is','was','are','were','be','have','has','had','do',
            'does','did','will','would','could','should','may','might','can','this',
            'that','these','those','i','you','he','she','it','we','they','me','him',
            'her','us','them','what','which','who','when','where','why','how','about',
            'tell','your','my','our','their','its','yourself','describe','explain',
            'talk','share','give','example','please',
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stop and len(w) > 3][:15]

    def generate_interruption_phrase(self, reason: str) -> str:
        return REASON_CONFIG.get(reason, {}).get("phrase", "Let me stop you for a moment.")

    def generate_warn_phrase(self, reason: str) -> str:
        return REASON_CONFIG.get(reason, {}).get("warn_phrase", "⚠️ Consider adjusting your approach.")

    def get_display_reason(self, reason: str) -> str:
        return REASON_CONFIG.get(reason, {}).get("display_reason", reason.replace("_", " ").title())

    def clear_session(self, session_id: str):
        self.per_question_counts.pop(session_id, None)
        self.session_interruption_total.pop(session_id, None)
        print(f"🧹 Cleared interruption state for session {session_id}")


# ── Singleton ──────────────────────────────────────────────────────────────────
_analyzer_instance = None

def get_interruption_analyzer():
    return get_enhanced_interruption_analyzer()

def get_enhanced_interruption_analyzer() -> EnhancedInterruptionAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = EnhancedInterruptionAnalyzer()
    return _analyzer_instance