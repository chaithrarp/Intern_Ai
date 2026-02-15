"""
Enhanced Intelligent Interruption Analyzer
===========================================

Multi-layer interruption detection system:

1. AUDIO LAYER: Pauses, hesitation, volume (from frontend AudioAnalyzer)
2. CONTENT LAYER: Rambling, vagueness, specificity (LLM-powered)
3. CONTEXT LAYER: Contradictions, off-topic, dodging (conversation-aware)
4. BEHAVIORAL LAYER: Filler words, uncertainty markers, confidence

This replaces the old rigid priority-based system with intelligent,
context-aware interruption decisions.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from models.interruption_models import InterruptionReason
from llm_service import get_llm_response
import re


# ============================================
# INTERRUPTION DECISION WEIGHTS
# ============================================

INTERRUPTION_SEVERITY = {
    # CRITICAL - Always interrupt on first detection
    "FALSE_CLAIM": {"weight": 100, "threshold": 1, "interruption_phrase": "Hold on - I need to stop you there."},
    "CONTRADICTION": {"weight": 95, "threshold": 1, "interruption_phrase": "Wait - that contradicts what you said earlier."},
    "COMPLETELY_OFF_TOPIC": {"weight": 90, "threshold": 1, "interruption_phrase": "Let me stop you - we're completely off track."},
    
    # HIGH SEVERITY - Warn once, interrupt on second occurrence
    "DODGING_QUESTION": {"weight": 85, "threshold": 2, "interruption_phrase": "I need to interrupt - you're not answering the question."},
    "EXCESSIVE_RAMBLING": {"weight": 80, "threshold": 2, "interruption_phrase": "I'm going to stop you there - please get to the point."},
    "EXCESSIVE_PAUSING": {"weight": 75, "threshold": 2, "interruption_phrase": "Let me help you focus - you seem to be struggling."},
    
    # MEDIUM SEVERITY - Warn twice, interrupt on third
    "VAGUE_ANSWER": {"weight": 70, "threshold": 3, "interruption_phrase": "Hold on - I need specific details, not generalizations."},
    "LACK_OF_SPECIFICS": {"weight": 65, "threshold": 3, "interruption_phrase": "Let me interrupt - give me concrete examples."},
    "HIGH_UNCERTAINTY": {"weight": 60, "threshold": 3, "interruption_phrase": "Stop for a moment - are you confident in this answer?"},
    
    # LOW SEVERITY - Warning only, never interrupt
    "MINOR_RAMBLING": {"weight": 30, "threshold": 999, "interruption_phrase": ""},
    "SPEAKING_TOO_LONG": {"weight": 25, "threshold": 999, "interruption_phrase": ""},
    "INCONSISTENT_DELIVERY": {"weight": 20, "threshold": 999, "interruption_phrase": ""},
}


# ============================================
# CONTENT ANALYSIS PATTERNS
# ============================================

# Filler word detection
FILLER_WORDS = [
    r'\b(um+|uh+|er+|ah+)\b',
    r'\b(like|you know|basically|actually|literally)\b',
    r'\b(sort of|kind of|i mean|i guess)\b',
    r'\b(well|so|anyway)\b'
]

# Uncertainty markers
UNCERTAINTY_MARKERS = [
    r'\b(i think|i believe|maybe|perhaps|possibly)\b',
    r'\b(probably|i guess|i suppose|not sure)\b',
    r'\b(might|could be|seems like)\b'
]

# Hedging phrases (indicate low confidence)
HEDGING_PHRASES = [
    r'\b(to be honest|in my opinion|from what i recall)\b',
    r'\b(if i remember correctly|i\'m not entirely sure)\b',
    r'\b(correct me if i\'m wrong)\b'
]


class EnhancedInterruptionAnalyzer:
    """
    Intelligent multi-layer interruption analyzer
    
    Combines:
    - Audio metrics (pauses, volume)
    - Content analysis (vagueness, rambling)
    - Contextual awareness (contradictions, relevance)
    - Behavioral patterns (confidence, coherence)
    """
    
    def __init__(self):
        self.session_warnings = {}  # Track warnings per session per issue type
        self.session_analysis_history = {}  # Store analysis results
        
        print("✅ Enhanced Interruption Analyzer initialized")
    
    
    def analyze_for_interruption(
        self,
        session_id: str,
        partial_transcript: str,
        audio_metrics: Dict,
        question_text: str,
        conversation_history: List[Dict],
        recording_duration: float
    ) -> Optional[Dict]:
        """
        MAIN FUNCTION: Analyze all layers and decide on interruption
        
        Args:
            session_id: Current session
            partial_transcript: What's been said so far (can be empty if no streaming STT)
            audio_metrics: From frontend AudioAnalyzer
            question_text: Question being answered
            conversation_history: Previous Q&As
            recording_duration: Seconds of recording
            
        Returns:
            Interruption decision dict or None
        """
        
        print(f"\n🔍 MULTI-LAYER INTERRUPTION ANALYSIS")
        print(f"   Session: {session_id}")
        print(f"   Duration: {recording_duration:.1f}s")
        print(f"   Transcript length: {len(partial_transcript)} chars")
        
        all_triggers = []
        
        # === LAYER 1: AUDIO ANALYSIS ===
        audio_triggers = self._analyze_audio_layer(audio_metrics, recording_duration)
        if audio_triggers:
            all_triggers.extend(audio_triggers)
            print(f"   🎤 Audio triggers: {[t['reason'] for t in audio_triggers]}")
        
        # === LAYER 2: CONTENT ANALYSIS ===
        if partial_transcript and len(partial_transcript) > 50:
            content_triggers = self._analyze_content_layer(
                partial_transcript,
                question_text,
                recording_duration
            )
            if content_triggers:
                all_triggers.extend(content_triggers)
                print(f"   💬 Content triggers: {[t['reason'] for t in content_triggers]}")
        
        # === LAYER 3: CONTEXT ANALYSIS ===
        if partial_transcript and conversation_history:
            context_triggers = self._analyze_context_layer(
                partial_transcript,
                question_text,
                conversation_history
            )
            if context_triggers:
                all_triggers.extend(context_triggers)
                print(f"   🧠 Context triggers: {[t['reason'] for t in context_triggers]}")
        
        # === LAYER 4: LLM-POWERED DEEP ANALYSIS ===
        if partial_transcript and len(partial_transcript) > 100:
            llm_triggers = self._analyze_llm_layer(
                partial_transcript,
                question_text,
                conversation_history
            )
            if llm_triggers:
                all_triggers.extend(llm_triggers)
                print(f"   🤖 LLM triggers: {[t['reason'] for t in llm_triggers]}")
        
        # === DECISION LOGIC ===
        if not all_triggers:
            return None
        
        # Sort by severity weight
        all_triggers.sort(key=lambda x: x.get('weight', 0), reverse=True)
        
        # Get highest priority trigger
        top_trigger = all_triggers[0]
        reason = top_trigger['reason']
        
        # Initialize warning tracking
        if session_id not in self.session_warnings:
            self.session_warnings[session_id] = {}
        
        # Get occurrence count
        occurrence_count = self.session_warnings[session_id].get(reason, 0) + 1
        self.session_warnings[session_id][reason] = occurrence_count
        
        # Get threshold for this issue
        severity_config = INTERRUPTION_SEVERITY.get(reason, {"weight": 50, "threshold": 2})
        threshold = severity_config['threshold']
        
        # Decide: warn or interrupt
        should_interrupt = occurrence_count >= threshold
        
        decision = {
            "should_interrupt": should_interrupt,
            "action": "interrupt" if should_interrupt else "warn",
            "reason": reason,
            "weight": top_trigger.get('weight', 50),
            "evidence": top_trigger.get('evidence', ''),
            "occurrence_count": occurrence_count,
            "threshold": threshold,
            "all_triggers": all_triggers,
            "interruption_phrase": severity_config.get('interruption_phrase', ''),
            "priority": self._calculate_priority(top_trigger['weight'])
        }
        
        if should_interrupt:
            print(f"\n🔥 INTERRUPTION TRIGGERED!")
            print(f"   Reason: {reason}")
            print(f"   Occurrences: {occurrence_count}/{threshold}")
            print(f"   Weight: {decision['weight']}")
        else:
            print(f"\n⚠️  WARNING ISSUED")
            print(f"   Reason: {reason}")
            print(f"   Occurrences: {occurrence_count}/{threshold}")
        
        return decision
    
    
    def _analyze_audio_layer(
        self,
        audio_metrics: Dict,
        recording_duration: float
    ) -> List[Dict]:
        """
        Analyze audio patterns from frontend AudioAnalyzer
        """
        triggers = []
        
        if not audio_metrics:
            return triggers
        
        detected_issues = audio_metrics.get('detected_issues', [])
        
        if not detected_issues:
            return triggers
        
        # Map frontend issue types to our severity system
        for issue in detected_issues:
            issue_type = issue.get('type', '')
            evidence = issue.get('evidence', '')
            
            # Map to our system
            if issue_type == 'EXCESSIVE_PAUSING':
                triggers.append({
                    "reason": "EXCESSIVE_PAUSING",
                    "weight": INTERRUPTION_SEVERITY['EXCESSIVE_PAUSING']['weight'],
                    "evidence": evidence,
                    "source": "audio"
                })
            
            elif issue_type == 'HIGH_HESITATION':
                triggers.append({
                    "reason": "HIGH_UNCERTAINTY",
                    "weight": INTERRUPTION_SEVERITY['HIGH_UNCERTAINTY']['weight'],
                    "evidence": evidence,
                    "source": "audio"
                })
            
            elif issue_type == 'SPEAKING_TOO_LONG':
                triggers.append({
                    "reason": "SPEAKING_TOO_LONG",
                    "weight": INTERRUPTION_SEVERITY['SPEAKING_TOO_LONG']['weight'],
                    "evidence": evidence,
                    "source": "audio"
                })
        
        return triggers
    
    
    def _analyze_content_layer(
        self,
        transcript: str,
        question_text: str,
        duration: float
    ) -> List[Dict]:
        """
        Analyze transcript content for rambling, vagueness, etc.
        """
        triggers = []
        
        # Normalize text
        text_lower = transcript.lower()
        words = text_lower.split()
        word_count = len(words)
        
        if word_count < 10:
            return triggers
        
        # === RAMBLING DETECTION ===
        
        # Count filler words
        filler_count = 0
        for pattern in FILLER_WORDS:
            filler_count += len(re.findall(pattern, text_lower))
        
        filler_ratio = filler_count / word_count if word_count > 0 else 0
        
        # Excessive filler words = rambling
        if filler_ratio > 0.15:  # >15% filler words
            triggers.append({
                "reason": "EXCESSIVE_RAMBLING",
                "weight": INTERRUPTION_SEVERITY['EXCESSIVE_RAMBLING']['weight'],
                "evidence": f"{filler_count} filler words in {word_count} words ({filler_ratio*100:.1f}%)",
                "source": "content"
            })
        
        elif filler_ratio > 0.08:  # 8-15% = minor rambling
            triggers.append({
                "reason": "MINOR_RAMBLING",
                "weight": INTERRUPTION_SEVERITY['MINOR_RAMBLING']['weight'],
                "evidence": f"Moderate use of filler words ({filler_ratio*100:.1f}%)",
                "source": "content"
            })
        
        # === UNCERTAINTY DETECTION ===
        
        uncertainty_count = 0
        for pattern in UNCERTAINTY_MARKERS + HEDGING_PHRASES:
            uncertainty_count += len(re.findall(pattern, text_lower))
        
        uncertainty_ratio = uncertainty_count / word_count if word_count > 0 else 0
        
        if uncertainty_ratio > 0.10:  # >10% uncertainty markers
            triggers.append({
                "reason": "HIGH_UNCERTAINTY",
                "weight": INTERRUPTION_SEVERITY['HIGH_UNCERTAINTY']['weight'],
                "evidence": f"{uncertainty_count} uncertainty markers - sounds very unsure",
                "source": "content"
            })
        
        # === VAGUENESS DETECTION ===
        
        # Check for concrete specifics (numbers, metrics, names)
        has_numbers = bool(re.search(r'\d+', transcript))
        has_metrics = bool(re.search(r'\d+\s*(ms|seconds|minutes|users|requests|percent|%)', text_lower))
        has_specifics = bool(re.search(r'\b(specifically|for example|such as)\b', text_lower))
        
        # Long answer without specifics = vague
        if word_count > 50 and not (has_numbers or has_metrics or has_specifics):
            triggers.append({
                "reason": "VAGUE_ANSWER",
                "weight": INTERRUPTION_SEVERITY['VAGUE_ANSWER']['weight'],
                "evidence": f"{word_count} words but no concrete examples, numbers, or metrics",
                "source": "content"
            })
        
        # === REPETITION DETECTION ===
        
        # Check for repeated phrases (indicates circular logic)
        sentences = re.split(r'[.!?]+', transcript)
        if len(sentences) >= 3:
            # Simple repetition check: find common 3-word phrases
            three_grams = []
            for i in range(len(words) - 2):
                three_grams.append(' '.join(words[i:i+3]))
            
            # Count duplicates
            unique_count = len(set(three_grams))
            total_count = len(three_grams)
            
            if total_count > 0:
                uniqueness_ratio = unique_count / total_count
                
                if uniqueness_ratio < 0.6:  # <60% unique = lots of repetition
                    triggers.append({
                        "reason": "EXCESSIVE_RAMBLING",
                        "weight": INTERRUPTION_SEVERITY['EXCESSIVE_RAMBLING']['weight'],
                        "evidence": f"Repetitive phrasing - only {uniqueness_ratio*100:.0f}% unique content",
                        "source": "content"
                    })
        
        return triggers
    
    
    def _analyze_context_layer(
        self,
        current_answer: str,
        question_text: str,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """
        Analyze answer in context of question and history
        """
        triggers = []
        
        # === QUESTION RELEVANCE ===
        
        # Extract key terms from question
        question_keywords = self._extract_keywords(question_text)
        answer_lower = current_answer.lower()
        
        # Count how many question keywords appear in answer
        keywords_found = sum(1 for kw in question_keywords if kw in answer_lower)
        relevance_ratio = keywords_found / len(question_keywords) if question_keywords else 1.0
        
        # If answer doesn't mention question topics = off-topic or dodging
        if len(current_answer.split()) > 30 and relevance_ratio < 0.3:
            triggers.append({
                "reason": "DODGING_QUESTION",
                "weight": INTERRUPTION_SEVERITY['DODGING_QUESTION']['weight'],
                "evidence": f"Answer doesn't address key topics from question",
                "source": "context"
            })
        
        # === CONTRADICTION DETECTION ===
        
        if conversation_history:
            # Simple contradiction check: look for opposite statements
            # This is a basic version - the LLM layer does deeper analysis
            
            for prev_qa in conversation_history[-3:]:  # Check last 3 answers
                prev_answer = prev_qa.get('answer', '').lower()
                
                # Look for direct contradictions (e.g., "yes" vs "no", "did" vs "didn't")
                current_lower = current_answer.lower()
                
                # Simple heuristic: if previous answer said "yes" and current says "no"
                # or vice versa about the same topic
                contradiction_patterns = [
                    (r'\byes\b', r'\bno\b'),
                    (r'\bdid\b', r'\bdidn\'t\b'),
                    (r'\bcan\b', r'\bcan\'t\b'),
                    (r'\bwill\b', r'\bwon\'t\b'),
                ]
                
                for pos_pattern, neg_pattern in contradiction_patterns:
                    if (re.search(pos_pattern, prev_answer) and re.search(neg_pattern, current_lower)) or \
                       (re.search(neg_pattern, prev_answer) and re.search(pos_pattern, current_lower)):
                        
                        # Check if talking about similar topics
                        prev_keywords = set(self._extract_keywords(prev_answer))
                        curr_keywords = set(self._extract_keywords(current_answer))
                        overlap = len(prev_keywords & curr_keywords)
                        
                        if overlap >= 2:  # At least 2 common keywords
                            triggers.append({
                                "reason": "CONTRADICTION",
                                "weight": INTERRUPTION_SEVERITY['CONTRADICTION']['weight'],
                                "evidence": f"Contradicts previous answer about similar topic",
                                "source": "context"
                            })
                            break
        
        return triggers
    
    
    def _analyze_llm_layer(
        self,
        transcript: str,
        question_text: str,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """
        Use LLM for deep semantic analysis
        
        This is expensive, so only call for longer answers
        """
        triggers = []
        
        try:
            # Build context from recent history
            history_context = ""
            if conversation_history:
                for qa in conversation_history[-2:]:
                    q = qa.get('question', '')[:100]
                    a = qa.get('answer', '')[:150]
                    history_context += f"Q: {q}\nA: {a}...\n\n"
            
            # Build analysis prompt
            messages = [
                {
                    "role": "system",
                    "content": f"""You are analyzing a candidate's answer in a job interview to detect issues.

QUESTION ASKED:
"{question_text}"

RECENT HISTORY:
{history_context if history_context else "No previous context"}

CANDIDATE'S CURRENT ANSWER:
"{transcript}"

Analyze the answer for the following issues. Respond in JSON format:

{{
  "is_off_topic": true/false,
  "is_dodging": true/false,
  "is_rambling": true/false,
  "is_vague": true/false,
  "contains_false_claim": true/false,
  "contradicts_history": true/false,
  "confidence_level": "high/medium/low",
  "explanation": "brief explanation of main issue if any"
}}

Be strict but fair. Only flag serious issues."""
                },
                {
                    "role": "user",
                    "content": "Analyze the answer."
                }
            ]
            
            # Get LLM analysis
            raw_response = get_llm_response(messages, temperature=0.2)
            
            # Parse JSON response
            import json
            
            # Clean response (remove markdown if present)
            clean_response = raw_response.strip()
            if clean_response.startswith('```'):
                clean_response = re.sub(r'```json\s*|\s*```', '', clean_response)
            
            analysis = json.loads(clean_response)
            
            # Convert LLM findings to triggers
            explanation = analysis.get('explanation', '')
            
            if analysis.get('contains_false_claim'):
                triggers.append({
                    "reason": "FALSE_CLAIM",
                    "weight": INTERRUPTION_SEVERITY['FALSE_CLAIM']['weight'],
                    "evidence": f"LLM detected false claim: {explanation}",
                    "source": "llm"
                })
            
            if analysis.get('contradicts_history'):
                triggers.append({
                    "reason": "CONTRADICTION",
                    "weight": INTERRUPTION_SEVERITY['CONTRADICTION']['weight'],
                    "evidence": f"LLM detected contradiction: {explanation}",
                    "source": "llm"
                })
            
            if analysis.get('is_dodging'):
                triggers.append({
                    "reason": "DODGING_QUESTION",
                    "weight": INTERRUPTION_SEVERITY['DODGING_QUESTION']['weight'],
                    "evidence": f"LLM detected question dodging: {explanation}",
                    "source": "llm"
                })
            
            if analysis.get('is_off_topic'):
                triggers.append({
                    "reason": "COMPLETELY_OFF_TOPIC",
                    "weight": INTERRUPTION_SEVERITY['COMPLETELY_OFF_TOPIC']['weight'],
                    "evidence": f"LLM detected off-topic response: {explanation}",
                    "source": "llm"
                })
            
            if analysis.get('is_rambling'):
                triggers.append({
                    "reason": "EXCESSIVE_RAMBLING",
                    "weight": INTERRUPTION_SEVERITY['EXCESSIVE_RAMBLING']['weight'],
                    "evidence": f"LLM detected rambling: {explanation}",
                    "source": "llm"
                })
            
            if analysis.get('is_vague'):
                triggers.append({
                    "reason": "LACK_OF_SPECIFICS",
                    "weight": INTERRUPTION_SEVERITY['LACK_OF_SPECIFICS']['weight'],
                    "evidence": f"LLM detected vagueness: {explanation}",
                    "source": "llm"
                })
        
        except Exception as e:
            print(f"   ⚠️ LLM layer failed: {str(e)}")
            # Don't fail the whole analysis if LLM fails
        
        return triggers
    
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'about', 'tell'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords[:10]  # Top 10 keywords
    
    
    def _calculate_priority(self, weight: int) -> int:
        """Convert weight to priority (1-10 scale)"""
        if weight >= 90:
            return 1  # Critical
        elif weight >= 80:
            return 3
        elif weight >= 70:
            return 5
        elif weight >= 60:
            return 7
        else:
            return 9  # Low
    
    
    def generate_interruption_phrase(self, reason: str) -> str:
        """Get interruption phrase for reason"""
        return INTERRUPTION_SEVERITY.get(reason, {}).get(
            'interruption_phrase',
            "Let me stop you for a moment."
        )
    
    
    def clear_session(self, session_id: str):
        """Clear session data when interview ends"""
        if session_id in self.session_warnings:
            del self.session_warnings[session_id]
        if session_id in self.session_analysis_history:
            del self.session_analysis_history[session_id]


# ============================================
# SINGLETON
# ============================================

_enhanced_analyzer = None

def get_enhanced_interruption_analyzer() -> EnhancedInterruptionAnalyzer:
    """Get singleton instance"""
    global _enhanced_analyzer
    if _enhanced_analyzer is None:
        _enhanced_analyzer = EnhancedInterruptionAnalyzer()
    return _enhanced_analyzer


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("ENHANCED INTERRUPTION ANALYZER TEST")
    print("=" * 70)
    
    analyzer = get_enhanced_interruption_analyzer()
    
    # Test 1: Rambling with filler words
    print("\n\nTEST 1: Rambling Answer")
    print("-" * 70)
    
    rambling_answer = """
    Um, so like, I think, you know, the database was, um, like, having some 
    issues, and, uh, basically what happened was, you know, we had, like, 
    a lot of, um, queries that were, sort of, kind of slow, and, uh, I guess 
    we, you know, tried to, like, optimize them, and, um, it sort of worked, 
    I think, maybe, you know, kind of improved things, like, a bit.
    """
    
    result = analyzer.analyze_for_interruption(
        session_id="test_001",
        partial_transcript=rambling_answer,
        audio_metrics={},
        question_text="How did you optimize the database?",
        conversation_history=[],
        recording_duration=25.0
    )
    
    if result:
        print(f"\nDecision: {result['action'].upper()}")
        print(f"Reason: {result['reason']}")
        print(f"Evidence: {result['evidence']}")
        print(f"Occurrences: {result['occurrence_count']}/{result['threshold']}")
    
    # Test 2: Vague answer without specifics
    print("\n\nTEST 2: Vague Answer")
    print("-" * 70)
    
    vague_answer = """
    We worked on the system and made it better. The performance improved and 
    users were happy. We used some technologies and frameworks to build it. 
    Everything went smoothly and the project was successful. The team was great 
    and we delivered on time.
    """
    
    result = analyzer.analyze_for_interruption(
        session_id="test_002",
        partial_transcript=vague_answer,
        audio_metrics={},
        question_text="Tell me about your microservices architecture",
        conversation_history=[],
        recording_duration=15.0
    )
    
    if result:
        print(f"\nDecision: {result['action'].upper()}")
        print(f"Reason: {result['reason']}")
        print(f"Evidence: {result['evidence']}")
    
    # Test 3: Excessive pausing (audio metric)
    print("\n\nTEST 3: Excessive Pausing")
    print("-" * 70)
    
    result = analyzer.analyze_for_interruption(
        session_id="test_003",
        partial_transcript="I worked on...",
        audio_metrics={
            'detected_issues': [
                {
                    'type': 'EXCESSIVE_PAUSING',
                    'severity': 'critical',
                    'evidence': '4 pauses over 3 seconds',
                    'priority': 3
                }
            ]
        },
        question_text="What was your role?",
        conversation_history=[],
        recording_duration=20.0
    )
    
    if result:
        print(f"\nDecision: {result['action'].upper()}")
        print(f"Reason: {result['reason']}")
        print(f"Evidence: {result['evidence']}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)