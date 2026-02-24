"""
Interview Orchestrator - WITH QUESTION PRE-FETCHING
=====================================================

KEY OPTIMIZATION:
- Next question is generated in a background thread IMMEDIATELY after answer evaluation
- By the time the user finishes reading feedback and clicks "Next", the question is ready
- Eliminates the 5-8 second Ollama wait between feedback and next question

DEMO MODE FLOW:
- Q0: Introduction (not counted)
- Q1-Q2: Resume questions (questions_in_current_phase = 2)
- Q3-Q5: Round-specific questions (questions_in_current_phase = 3)
- Total: EXACTLY 5 questions
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import json
import os
import threading  # ← KEY: for background pre-fetching

from models.state_models import (
    SessionState,
    InterviewPhase,
    RoundType,
    DEFAULT_PHASE_CONFIGS
)
from models.evaluation_models import AnswerEvaluation
from engines.answer_analyzer import get_answer_analyzer
from llm_service import get_llm_response

from config.evaluation_config import PHASE_TRANSITION_RULES


class InterviewOrchestrator:
    """
    Main orchestrator for interview flow.
    
    OPTIMIZED: Pre-fetches next question in background thread while user reads feedback.
    """
    
    def __init__(self):
        self.analyzer = get_answer_analyzer()
        self.sessions = {}
        self.session_file = "active_sessions.json"
        
        # ── PRE-FETCH CACHE ──────────────────────────────────────────
        # Stores {session_id: {"question": {...}, "ready": bool, "thread": Thread}}
        self._question_cache: Dict[str, Dict] = {}
        self._cache_lock = threading.Lock()
        # ────────────────────────────────────────────────────────────
        
        self._load_sessions()
        
        self.max_total_questions = sum(
            config['max_questions'] 
            for config in PHASE_TRANSITION_RULES.values()
        )
        
        print("✅ Interview Orchestrator initialized (with question pre-fetching)")
        print(f"   📦 Loaded {len(self.sessions)} active session(s)")
        print(f"   🎯 Demo Mode: Max {self.max_total_questions} questions")
    
    # ============================================================
    # PRE-FETCH: Background question generation
    # ============================================================

    def _prefetch_next_question(
        self,
        session_id: str,
        state: SessionState,
        round_type: str,
        evaluation: AnswerEvaluation
    ):
        """
        Kick off background thread to pre-generate the next question.
        Stores result in self._question_cache[session_id].
        """
        # Mark slot as "generating"
        with self._cache_lock:
            self._question_cache[session_id] = {"ready": False, "question": None}

        def _generate():
            try:
                print(f"   🔄 [PRE-FETCH] Generating next question in background for {session_id}...")
                question = self._generate_question(
                    state=state,
                    round_type=round_type,
                    resume_context=state.resume_context,
                    previous_evaluation=evaluation
                )
                with self._cache_lock:
                    self._question_cache[session_id] = {"ready": True, "question": question}
                print(f"   ✅ [PRE-FETCH] Question ready for {session_id}: {question['text'][:60]}...")
            except Exception as e:
                print(f"   ❌ [PRE-FETCH] Failed for {session_id}: {e}")
                with self._cache_lock:
                    self._question_cache[session_id] = {"ready": True, "question": None}  # unblock

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

    def _get_prefetched_question(self, session_id: str, timeout: float = 12.0) -> Optional[Dict]:
        """
        Wait (up to timeout seconds) for the pre-fetched question to be ready.
        Returns the question dict or None if it failed.
        """
        import time
        waited = 0.0
        interval = 0.15  # poll every 150ms

        while waited < timeout:
            with self._cache_lock:
                cached = self._question_cache.get(session_id)
            if cached and cached.get("ready"):
                with self._cache_lock:
                    del self._question_cache[session_id]  # consume it
                return cached.get("question")
            time.sleep(interval)
            waited += interval

        print(f"   ⚠️  [PRE-FETCH] Timeout waiting for pre-fetched question ({session_id})")
        with self._cache_lock:
            self._question_cache.pop(session_id, None)
        return None

    def _clear_prefetch(self, session_id: str):
        """Discard any cached question for this session (e.g. follow-up overrides it)."""
        with self._cache_lock:
            self._question_cache.pop(session_id, None)

    # ============================================================
    # SESSION PERSISTENCE
    # ============================================================
    
    def _load_sessions(self):
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    
            for session_id, data in session_data.items():
                try:
                    state = SessionState(
                        session_id=session_id,
                        resume_context=data.get('resume_context'),
                        resume_uploaded=data.get('resume_uploaded', False),
                        current_phase=InterviewPhase(data.get('current_phase', 'resume_deep_dive')),
                        current_round_type=RoundType(data.get('current_round_type', 'technical'))
                    )
                    state.current_question_text = data.get('current_question_text')
                    state.current_question_id = data.get('current_question_id')
                    state.difficulty_level = data.get('difficulty_level', 5)
                    state.questions_in_current_phase = data.get('questions_in_current_phase', 0)
                    state.conversation_history = data.get('conversation_history', [])
                    state.overall_score_progression = data.get('overall_score_progression', [])
                    state.total_interruptions = data.get('total_interruptions', 0)
                    state.config['actual_question_number'] = data.get('actual_question_number', 0)
                    state.config['followup_count'] = data.get('followup_count', 0)
                    self.sessions[session_id] = state
                    print(f"   ✅ Restored session: {session_id}")
                except Exception as e:
                    print(f"   ⚠️  Could not restore session {session_id}: {e}")
        except Exception as e:
            print(f"   ⚠️  Could not load sessions file: {e}")
    
    def _save_sessions(self):
        try:
            session_data = {}
            for session_id, state in self.sessions.items():
                session_data[session_id] = {
                    'session_id': session_id,
                    'resume_context': state.resume_context,
                    'resume_uploaded': state.resume_uploaded,
                    'current_phase': state.current_phase.value,
                    'current_round_type': state.current_round_type.value,
                    'current_question_text': state.current_question_text,
                    'current_question_id': state.current_question_id,
                    'difficulty_level': state.difficulty_level,
                    'questions_in_current_phase': state.questions_in_current_phase,
                    'conversation_history': state.conversation_history,
                    'overall_score_progression': state.overall_score_progression,
                    'total_interruptions': state.total_interruptions,
                    'started_at': state.started_at.isoformat() if state.started_at else None,
                    'actual_question_number': state.config.get('actual_question_number', 0),
                    'followup_count': state.config.get('followup_count', 0)
                }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"   ⚠️  Could not save sessions: {e}")
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        session = self.sessions.get(session_id)
        if not session:
            print(f"   ❌ Session not found: {session_id}")
        return session
    
    # ============================================================
    # START INTERVIEW
    # ============================================================
    
    def start_interview(
        self,
        session_id: str,
        round_type: str,
        resume_context: Optional[str] = None
    ) -> Dict:
        print(f"\n{'='*60}")
        print(f"🎯 STARTING {round_type.upper()} ROUND INTERVIEW")
        print(f"   Session: {session_id}")
        print(f"{'='*60}")
        
        state = SessionState(
            session_id=session_id,
            resume_context=resume_context,
            resume_uploaded=resume_context is not None,
            current_phase=InterviewPhase.RESUME_DEEP_DIVE,
            current_round_type=self._parse_round_type(round_type)
        )
        
        state.config["introduction_asked"] = False
        state.config["actual_question_number"] = 0
        state.config["followup_count"] = 0
        
        self.sessions[session_id] = state
        self._save_sessions()
        
        introduction = self._generate_introduction(round_type, resume_context)

        # Q0: "introduce yourself" — not counted in the 5 scored questions
        intro_question = {
            "text": "Tell me a bit about yourself — who you are, what you've been working on, and what brings you here today.",
            "round_type": round_type,
            "phase": state.current_phase.value,
            "difficulty": 1,
            "question_number": 0,
            "is_intro": True
        }

        state.current_question_text = intro_question["text"]
        state.current_question_id = "q_0"
        state.config["actual_question_number"] = 0
        self._save_sessions()

        return {
            "session_id": session_id,
            "round_type": round_type,
            "current_phase": state.current_phase.value,
            "introduction": introduction,
            "question": intro_question,
            "question_number": 0,
            "total_questions_allowed": self.max_total_questions,
            "phase_info": self._get_phase_info(state.current_phase)
        }
    
    # ============================================================
    # PROCESS ANSWER — MAIN OPTIMIZED METHOD
    # ============================================================

    def process_answer(
        self,
        state: SessionState,
        question_id: int,
        question_text: str,
        answer_text: str,
        round_type: str,
        skip_claim_extraction: bool = False,
        is_followup_answer: bool = False
    ) -> Dict:
        """
        OPTIMIZED: Evaluate answer, then kick off next-question generation
        in the background before returning. When frontend eventually asks
        for the next question it's already (or nearly) ready.
        """
        actual_q_num = state.config.get('actual_question_number', question_id)
        followup_count = state.config.get('followup_count', 0)
        session_id = state.session_id
        
        print(f"\n{'='*60}")
        print(f"📝 PROCESSING ANSWER Q{question_id} ({actual_q_num}/{self.max_total_questions})")
        print(f"{'='*60}")
        
        # ── Step 1: Evaluate answer ────────────────────────────────
        evaluation = self.analyzer.evaluate_answer(
            answer_text=answer_text,
            question_text=question_text,
            question_id=question_id,
            round_type=round_type,
            session_id=session_id,
            conversation_history=state.conversation_history,
            skip_claim_extraction=skip_claim_extraction
        )
        
        # ── Step 2: Update counters ────────────────────────────────
        if not is_followup_answer:
            state.questions_in_current_phase += 1
        
        self._update_state_with_evaluation(state, evaluation, question_text, answer_text)
        
        if state.conversation_history:
            state.conversation_history[-1]['triggered_followup'] = False
            state.conversation_history[-1]['is_followup_answer'] = is_followup_answer
        
        # ── Step 3: Immediate feedback ─────────────────────────────
        immediate_feedback = self._generate_immediate_feedback(evaluation)
        
        # ── Step 4: Hard stop check ────────────────────────────────
        if actual_q_num >= self.max_total_questions:
            print(f"🎉 INTERVIEW COMPLETED — reached max questions ({self.max_total_questions})")
            return {
                "evaluation": evaluation.dict(),
                "immediate_feedback": immediate_feedback,
                "completed": True,
                "final_phase": True,
                "reason": f"Completed all {self.max_total_questions} questions"
            }
        
        # ── Step 5: Follow-up check ────────────────────────────────
        needs_followup = self._should_ask_followup(
            evaluation, answer_text, state, is_followup_answer, actual_q_num
        )
        
        if needs_followup:
            followup_q = self._generate_followup_question(
                evaluation, question_text, answer_text, state
            )
            if followup_q:
                print(f"🔍 Follow-up triggered")
                if state.conversation_history:
                    state.conversation_history[-1]['triggered_followup'] = True
                state.config['followup_count'] = followup_count + 1
                
                # ⚡ Pre-fetch the question AFTER the followup while user answers it
                self._prefetch_next_question(session_id, state, round_type, evaluation)
                
                self._save_sessions()
                return {
                    "evaluation": evaluation.dict(),
                    "immediate_feedback": immediate_feedback,
                    "requires_followup": True,
                    "followup_question": followup_q,
                    "followup_reason": evaluation.followup_reason or "Answer needs clarification",
                    "completed": False,
                    "is_followup": True,
                    "question_number": actual_q_num,
                    "total_questions_allowed": self.max_total_questions
                }
        
        # ── Step 6: Phase transition ───────────────────────────────
        state.difficulty_level = self._adjust_difficulty(
            state.difficulty_level, evaluation.difficulty_adjustment
        )
        
        phase_config = PHASE_TRANSITION_RULES.get(state.current_phase.value, {})
        force_transition_after = phase_config.get('force_transition_after', 999)
        
        if state.questions_in_current_phase >= force_transition_after:
            state.phases_completed.append(state.current_phase)
            state.current_phase = state.get_next_phase()
            state.questions_in_current_phase = 0
            print(f"→ Phase transition: {state.current_phase.value}")
            
            if state.current_phase == InterviewPhase.COMPLETED:
                print("🎉 INTERVIEW COMPLETED — all phases done")
                return {
                    "evaluation": evaluation.dict(),
                    "immediate_feedback": immediate_feedback,
                    "completed": True,
                    "final_phase": True,
                    "reason": "Completed all phases"
                }
        
        # ── Step 7: Increment question counter ────────────────────
        next_question_num = actual_q_num + 1
        state.config['actual_question_number'] = next_question_num
        
        # ── Step 8: ⚡ START BACKGROUND QUESTION GENERATION ────────
        # This is the key optimization: we kick this off NOW, before returning,
        # so the question is ready while the user reads their feedback.
        self._prefetch_next_question(session_id, state, round_type, evaluation)
        
        self._save_sessions()
        
        # ── Step 9: Return immediately (question generates in background) ─
        # The frontend will call /interview/next-question to retrieve it.
        # But for backward compatibility we ALSO wait here (with a short timeout)
        # and include the question if it's already done.
        next_question = self._get_prefetched_question(session_id, timeout=8.0)
        
        if next_question is None:
            # Fallback: generate synchronously (should rarely happen)
            print("   ⚠️  Pre-fetch timed out, generating synchronously")
            next_question = self._generate_question(
                state=state,
                round_type=round_type,
                resume_context=state.resume_context,
                previous_evaluation=evaluation
            )
        
        state.current_question_text = next_question["text"]
        state.current_question_id = f"q_{next_question_num}"
        next_question["question_number"] = next_question_num
        self._save_sessions()
        
        return {
            "evaluation": evaluation.dict(),
            "immediate_feedback": immediate_feedback,
            "next_question": next_question,
            "question_number": next_question_num,
            "total_questions_allowed": self.max_total_questions,
            "current_phase": state.current_phase.value,
            "phase_info": self._get_phase_info(state.current_phase),
            "difficulty_level": state.difficulty_level,
            "completed": False
        }

    # ============================================================
    # QUESTION GENERATION
    # ============================================================
    
    def _generate_question(
        self,
        state: SessionState,
        round_type: str,
        resume_context: Optional[str] = None,
        previous_evaluation: Optional[AnswerEvaluation] = None
    ) -> Dict:
        print(f"🎲 Generating {round_type.upper()} question (phase={state.current_phase.value}, diff={state.difficulty_level})...")
        
        if round_type == "hr":
            prompt = self._build_hr_question_prompt(state, resume_context, previous_evaluation)
        elif round_type == "technical":
            prompt = self._build_technical_question_prompt(state, resume_context, previous_evaluation)
        elif round_type == "system_design":
            prompt = self._build_sysdesign_question_prompt(state, resume_context, previous_evaluation)
        else:
            prompt = self._build_technical_question_prompt(state, resume_context, previous_evaluation)
        
        raw_question = get_llm_response(prompt, temperature=0.7)
        question_text = self._clean_question(raw_question)
        
        print(f"   ✓ Generated: {question_text[:80]}...")
        
        return {
            "text": question_text,
            "round_type": round_type,
            "phase": state.current_phase.value,
            "difficulty": state.difficulty_level,
            "question_number": state.config.get('actual_question_number', len(state.conversation_history) + 1)
        }

    def _should_ask_followup(
        self, 
        evaluation: AnswerEvaluation, 
        answer_text: str,
        state: SessionState,
        is_followup_answer: bool = False,
        current_question_num: int = 0
    ) -> bool:
        if current_question_num >= self.max_total_questions - 1:
            return False
        if is_followup_answer:
            return False
        if len(state.conversation_history) >= 1:
            last_qa = state.conversation_history[-1]
            if last_qa.get('triggered_followup', False):
                return False
        followup_count = state.config.get('followup_count', 0)
        if followup_count >= 2:
            return False
        if evaluation.requires_followup:
            print("   🔍 Follow-up trigger: Evaluator requested")
            return True
        if evaluation.overall_score < 55:
            print(f"   🔍 Follow-up trigger: Low score ({evaluation.overall_score})")
            return True
        if len(answer_text.split()) < 30:
            print(f"   🔍 Follow-up trigger: Short answer")
            return True
        if len(evaluation.red_flags) > 0:
            print(f"   🔍 Follow-up trigger: Red flags")
            return True
        critical_weaknesses = ["vague", "no specific", "missing details", "unclear", "contradictory", "no metrics"]
        for weakness in evaluation.weaknesses:
            if any(cw in weakness.lower() for cw in critical_weaknesses):
                print(f"   🔍 Follow-up trigger: Critical weakness")
                return True
        return False
    
    def _generate_followup_question(
        self,
        evaluation: AnswerEvaluation,
        original_question: str,
        answer_text: str,
        state: SessionState
    ) -> Optional[str]:
        if evaluation.suggested_followup:
            return evaluation.suggested_followup
        
        weaknesses_str = "; ".join(evaluation.weaknesses[:2])
        prompt = [
            {
                "role": "system",
                "content": f"""You are an interviewer asking a brief follow-up question.

ORIGINAL QUESTION: {original_question}
CANDIDATE'S ANSWER: {answer_text[:300]}
ISSUES DETECTED: {weaknesses_str}

Generate ONE short, direct follow-up question (1 sentence) that asks for specific details they missed.
Output ONLY the question, nothing else."""
            },
            {"role": "user", "content": "Generate the follow-up question."}
        ]
        
        try:
            response = get_llm_response(prompt, temperature=0.7)
            question = response.strip().replace("**", "").replace("*", "")
            for prefix in ["Question:", "Q:", "Follow-up:"]:
                if question.startswith(prefix):
                    question = question[len(prefix):].strip()
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            return question
        except Exception as e:
            print(f"   ⚠️  Could not generate follow-up: {e}")
            return "Can you elaborate on that with more specific details?"
    
    # ============================================================
    # PROMPT BUILDERS
    # ============================================================
    
    def _generate_introduction(self, round_type: str, resume_context: Optional[str]) -> str:
        intros = {
            "hr": [
                "Hello! I'm your AI interviewer for today's behavioral round. I'll be asking you about your past experiences and how you've handled various situations. Let's begin!",
                "Welcome to your HR interview! Today we'll explore your professional experiences and how you approach challenges. Ready? Let's start!",
            ],
            "technical": [
                "Hello! Welcome to your technical interview. I'll be assessing your understanding of computer science fundamentals, problem-solving skills, and technical depth. Let's get started!",
                "Hi! I'm here to evaluate your technical expertise. I'll ask questions about algorithms, data structures, and system concepts. Ready to begin?",
            ],
            "system_design": [
                "Hello! This is your system design interview. I'll ask you to design scalable systems. Focus on component architecture, bottleneck identification, and trade-offs. Let's start!",
                "Welcome to the system design round! I want to see how you architect large-scale distributed systems. Think about scalability, reliability, and performance. Ready?",
            ]
        }
        round_intros = intros.get(round_type, intros["technical"])
        intro = random.choice(round_intros)
        if resume_context:
            intro += " I can see you've uploaded your resume, so I'll be tailoring questions to your background."
        intro += " But first — tell me a bit about yourself."
        return intro

    def _build_hr_question_prompt(self, state, resume_context, previous_evaluation):
        system_prompt = f"""You are an expert HR interviewer conducting a behavioral interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

Ask ONE behavioral question testing STAR method (Situation, Task, Action, Result).

PHASE FOCUS: {self._get_phase_specific_guidance(state.current_phase, "hr")}
DIFFICULTY: {self._get_difficulty_guidance(state.difficulty_level, "hr")}

OUTPUT RULES:
- Output ONLY the question itself, nothing else.
- Do NOT explain what you are doing.
- Do NOT say 'Based on your resume' or 'As you mentioned'.
- Start directly with the question words."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}\n\nUse this context to personalize the question but do NOT reference the resume in your output."
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS SCORE: {previous_evaluation.overall_score}/100"
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS (do NOT repeat):\n{history_context}"
        else:
            system_prompt += "\n\nCRITICAL: First question — ask the candidate to introduce themselves and their background."
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next behavioral interview question."}
        ]
    
    def _build_technical_question_prompt(self, state, resume_context, previous_evaluation):
        system_prompt = f"""You are a senior software engineer conducting a technical interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

Ask ONE technical question testing depth, accuracy, and problem-solving.

PHASE FOCUS: {self._get_phase_specific_guidance(state.current_phase, "technical")}
DIFFICULTY: {self._get_difficulty_guidance(state.difficulty_level, "technical")}

OUTPUT RULES:
- Output ONLY the question itself, nothing else.
- Do NOT explain what you are doing.
- Do NOT say 'Based on your resume' or 'As you mentioned'.
- Start directly with the question words."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}\n\nUse this context to personalize the question but do NOT reference the resume in your output."
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS SCORE: {previous_evaluation.overall_score}/100"
            if previous_evaluation.weaknesses:
                system_prompt += f"\nWEAKNESSES: {', '.join(previous_evaluation.weaknesses[:2])}"
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS (do NOT repeat):\n{history_context}"
        else:
            system_prompt += "\n\nCRITICAL: First question — ask the candidate to introduce themselves and their technical background."
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next technical interview question."}
        ]
    
    def _build_sysdesign_question_prompt(self, state, resume_context, previous_evaluation):
        system_prompt = f"""You are a principal architect conducting a system design interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

Ask ONE system design question testing architecture, scalability, and trade-offs.

PHASE FOCUS: {self._get_phase_specific_guidance(state.current_phase, "system_design")}
DIFFICULTY: {self._get_difficulty_guidance(state.difficulty_level, "system_design")}

OUTPUT RULES:
- Output ONLY the question itself, nothing else.
- Do NOT explain what you are doing.
- Do NOT say 'Based on your resume' or 'As you mentioned'.
- Start directly with the question words."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}\n\nUse this context to personalize the question but do NOT reference the resume in your output."
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS SCORE: {previous_evaluation.overall_score}/100"
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS (do NOT repeat):\n{history_context}"
        else:
            system_prompt += "\n\nCRITICAL: First question — ask the candidate to introduce themselves and their experience with large-scale systems."
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next system design question."}
        ]

    # ============================================================
    # HELPERS
    # ============================================================
    
    def _get_phase_specific_guidance(self, phase: InterviewPhase, round_type: str) -> str:
        phase_guidance = {
            InterviewPhase.RESUME_DEEP_DIVE: {
                "hr": "Verify claims from resume. Ask about specific projects and achievements.",
                "technical": "Test technologies listed on resume. Ask for code examples.",
                "system_design": "Ask about architecture of systems they claim to have built."
            },
            InterviewPhase.CORE_SKILL_ASSESSMENT: {
                "hr": "Test fundamental soft skills: communication, teamwork, problem-solving.",
                "technical": "Test core CS concepts: data structures, algorithms, complexity.",
                "system_design": "Test fundamental architecture patterns: caching, load balancing, databases."
            },
            InterviewPhase.SCENARIO_SOLVING: {
                "hr": "Present HYPOTHETICAL real-world conflicts. Phrasing: 'Imagine you are in a situation where...'",
                "technical": "Give debugging scenarios and edge cases to solve.",
                "system_design": "Present scaling challenges and ask for solutions."
            },
            InterviewPhase.STRESS_TESTING: {
                "hr": "Present HYPOTHETICAL high-pressure scenarios.",
                "technical": "Ask about optimization under constraints.",
                "system_design": "Design systems under extreme scale (billions of users)."
            },
            InterviewPhase.CLAIM_VERIFICATION: {
                "hr": "Follow up on vague claims from earlier answers.",
                "technical": "Probe deeper into technical claims that seemed suspicious.",
                "system_design": "Ask for specifics about scalability claims."
            },
            InterviewPhase.WRAP_UP: {
                "hr": "Final: 'What would you like us to know about you?'",
                "technical": "Final: 'What's the hardest technical problem you've solved?'",
                "system_design": "Final: 'Design your dream system with unlimited resources.'"
            }
        }
        return phase_guidance.get(phase, {}).get(round_type, "Ask a relevant question for this phase.")
    
    def _get_difficulty_guidance(self, difficulty_level: int, round_type: str) -> str:
        if difficulty_level <= 3:
            return "EASY: Ask straightforward questions with clear answers."
        elif difficulty_level <= 6:
            return "MEDIUM: Ask questions requiring trade-off analysis."
        else:
            return "HARD: Ask questions with multiple layers and edge cases."
    
    def _update_state_with_evaluation(self, state, evaluation, question_text, answer_text):
        state.add_answer_scores(evaluation.scores)
        state.calculate_average_scores()
        state.conversation_history.append({
            "question_id": evaluation.question_id,
            "question": question_text,
            "answer": answer_text,
            "evaluation": evaluation.dict(),
            "phase": state.current_phase.value,
            "timestamp": datetime.now().isoformat()
        })
        state.overall_score_progression.append(evaluation.overall_score)
        for flag in evaluation.red_flags:
            state.add_red_flag("evaluation_flag", flag, str(evaluation.question_id))
        state.update_activity()
    
    def _adjust_difficulty(self, current_level: int, adjustment: str) -> int:
        if adjustment == "increase":
            return min(10, current_level + 1)
        elif adjustment == "decrease":
            return max(1, current_level - 1)
        return current_level
    
    def _generate_immediate_feedback(self, evaluation: AnswerEvaluation) -> Dict:
        from models.evaluation_models import ScoringThresholds
        performance_level = ScoringThresholds.get_performance_level(evaluation.overall_score)
        key_strength = evaluation.strengths[0] if evaluation.strengths else "Good effort"
        key_weakness = evaluation.weaknesses[0] if evaluation.weaknesses else None
        if evaluation.overall_score >= 85:
            emoji = "🌟"
        elif evaluation.overall_score >= 70:
            emoji = "👍"
        elif evaluation.overall_score >= 50:
            emoji = "🤔"
        else:
            emoji = "📚"
        return {
            "overall_score": evaluation.overall_score,
            "performance_level": performance_level,
            "emoji": emoji,
            "key_strength": key_strength,
            "key_weakness": key_weakness,
            "red_flags": evaluation.red_flags[:1] if evaluation.red_flags else []
        }
    
    def _build_history_context(self, history: List[Dict]) -> str:
        if not history:
            return ""
        context_parts = []
        for i, item in enumerate(history[-3:], 1):
            q = item.get("question", "")
            context_parts.append(f"{i}. {q}")
        return "\n".join(context_parts)
    
    def _clean_question(self, raw_question: str) -> str:
        import re as _re
        question = raw_question.strip().replace("**", "").replace("*", "")

        preamble_prefixes = [
            "Question:", "Q:", "Next question:", "Here's the question:",
            "Here is the next question:", "Here is a question:",
            "Sure!", "Sure,", "Certainly!", "Certainly,",
            "Of course!", "Of course,", "Absolutely!",
            "Based on", "As you have", "As per", "Given that",
            "Referring to", "According to", "Since you",
            "I see that", "I notice that", "Looking at",
            "From your resume", "From the resume",
            "As referenced", "As you referenced",
        ]
        changed = True
        while changed:
            changed = False
            for prefix in preamble_prefixes:
                if question.lower().startswith(prefix.lower()):
                    question = question[len(prefix):].strip().lstrip(",:").strip()
                    changed = True

        # Jump past "...interview question: 'actual question'"
        colon_match = _re.search(r"(?i)\bquestion\s*:", question)
        if colon_match:
            question = question[colon_match.end():].strip()

        # Strip surrounding quotes (up to 3 layers)
        for _ in range(3):
            if len(question) > 2:
                if question.startswith('"') and question.endswith('"'):
                    question = question[1:-1].strip()
                if question.startswith("'") and question.endswith("'"):
                    question = question[1:-1].strip()

        return question.strip()
    
    def _parse_round_type(self, round_type_str: str) -> RoundType:
        round_type_str = round_type_str.lower().strip()
        if "hr" in round_type_str or "behavioral" in round_type_str:
            return RoundType.HR
        elif "system" in round_type_str or "design" in round_type_str:
            return RoundType.SYSTEM_DESIGN
        return RoundType.TECHNICAL
    
    def _get_phase_info(self, phase: InterviewPhase) -> Dict:
        config = DEFAULT_PHASE_CONFIGS.get(phase)
        if not config:
            return {}
        return {
            "phase": phase.value,
            "description": config.description,
            "min_questions": config.min_questions,
            "max_questions": config.max_questions,
            "difficulty": config.base_difficulty
        }


# Singleton
_orchestrator_instance = None

def get_interview_orchestrator() -> InterviewOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InterviewOrchestrator()
    return _orchestrator_instance