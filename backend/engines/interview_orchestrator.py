"""
Interview Orchestrator - DEMO MODE FIX
=======================================

FIXES APPLIED:
1. ✅ Proper question number tracking (separate from phase questions)
2. ✅ HARD STOP at question 5 in demo mode
3. ✅ Follow-ups don't increment main question counter
4. ✅ Clear logging to debug question flow

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

from models.state_models import (
    SessionState,
    InterviewPhase,
    RoundType,
    DEFAULT_PHASE_CONFIGS
)
from models.evaluation_models import AnswerEvaluation
from engines.answer_analyzer import get_answer_analyzer
from llm_service import get_llm_response

# Import demo mode config
from config.evaluation_config import PHASE_TRANSITION_RULES


class InterviewOrchestrator:
    """
    Main orchestrator for interview flow
    
    FIXED: Proper question counting for demo mode
    """
    
    def __init__(self):
        self.analyzer = get_answer_analyzer()
        self.sessions = {}
        self.session_file = "active_sessions.json"
        
        self._load_sessions()
        
        # Calculate max questions from config
        self.max_total_questions = sum(
            config['max_questions'] 
            for config in PHASE_TRANSITION_RULES.values()
        )
        
        print("✅ Interview Orchestrator initialized")
        print(f"   📦 Loaded {len(self.sessions)} active session(s)")
        print(f"   🎯 Demo Mode: Max {self.max_total_questions} questions")
    
    def _load_sessions(self):
        """Load sessions from file"""
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
                        
                        # NEW: Track actual question number
                        state.config['actual_question_number'] = data.get('actual_question_number', 0)
                        state.config['followup_count'] = data.get('followup_count', 0)
                        
                        self.sessions[session_id] = state
                        print(f"   ✅ Restored session: {session_id}")
                    except Exception as e:
                        print(f"   ⚠️  Could not restore session {session_id}: {e}")
                        
        except Exception as e:
            print(f"   ⚠️  Could not load sessions file: {e}")
    
    def _save_sessions(self):
        """Save sessions to file"""
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
                    # NEW: Save question tracking
                    'actual_question_number': state.config.get('actual_question_number', 0),
                    'followup_count': state.config.get('followup_count', 0)
                }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"   ⚠️  Could not save sessions: {e}")
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if not session:
            print(f"   ❌ Session not found: {session_id}")
            print(f"   📋 Active sessions: {list(self.sessions.keys())}")
        
        return session
    
    
    def start_interview(
        self,
        session_id: str,
        round_type: str,
        resume_context: Optional[str] = None
    ) -> Dict:
        """
        Start a new interview session
        
        Returns:
            Dict with introduction, first question, and session setup
        """
        
        print(f"\n{'='*60}")
        print(f"🎯 STARTING {round_type.upper()} ROUND INTERVIEW")
        print(f"   Session: {session_id}")
        print(f"   Max Questions: {self.max_total_questions}")
        print(f"{'='*60}")
        
        # Initialize session state
        state = SessionState(
            session_id=session_id,
            resume_context=resume_context,
            resume_uploaded=resume_context is not None,
            current_phase=InterviewPhase.RESUME_DEEP_DIVE,
            current_round_type=self._parse_round_type(round_type)
        )
        
        # NEW: Initialize question tracking
        state.config["introduction_asked"] = False
        state.config["actual_question_number"] = 0  # Actual questions answered (not including followups)
        state.config["followup_count"] = 0  # Total followups asked
        
        # Store session
        self.sessions[session_id] = state
        self._save_sessions()
        
        # Generate introduction
        introduction = self._generate_introduction(round_type, resume_context)
        
        print(f"\n💬 Introduction: {introduction[:80]}...")
        
        # Generate first question (Q1)
        first_question = self._generate_question(
            state=state,
            round_type=round_type,
            resume_context=resume_context
        )
        
        # Update state with current question
        state.current_question_text = first_question["text"]
        state.current_question_id = "q_1"
        state.config["actual_question_number"] = 1  # This will be Q1
        
        # Save again with updated question
        self._save_sessions()
        
        return {
            "session_id": session_id,
            "round_type": round_type,
            "current_phase": state.current_phase.value,
            "introduction": introduction,
            "question": first_question,
            "question_number": 1,
            "total_questions_allowed": self.max_total_questions,
            "phase_info": self._get_phase_info(state.current_phase)
        }
    
    def _generate_introduction(self, round_type: str, resume_context: Optional[str]) -> str:
        """Generate personalized introduction/greeting"""
        
        intros = {
            "hr": [
                "Hello! I'm your AI interviewer for today's behavioral round. I'll be asking you about your past experiences and how you've handled various situations. Please use the STAR method: describe the Situation, Task, Action you took, and Results you achieved. Let's begin!",
                "Welcome to your HR interview! Today we'll explore your professional experiences and how you approach challenges. I'm looking for specific examples with measurable outcomes. Ready? Let's start!",
                "Hi there! I'll be conducting your behavioral interview today. I want to hear about real situations you've faced, the actions you took, and the results you achieved. Please be specific with examples. Shall we begin?"
            ],
            "technical": [
                "Hello! Welcome to your technical interview. I'll be assessing your understanding of computer science fundamentals, problem-solving skills, and technical depth. I'm looking for clear explanations of concepts, trade-off analysis, and consideration of edge cases. Let's get started!",
                "Hi! I'm here to evaluate your technical expertise. I'll ask questions about algorithms, data structures, and system concepts. Please explain your thought process, discuss time and space complexity, and mention any trade-offs. Ready to begin?",
                "Welcome to the technical round! I'll be testing your programming knowledge and problem-solving abilities. Focus on correctness, efficiency, and explaining WHY things work, not just WHAT they do. Let's dive in!"
            ],
            "system_design": [
                "Hello! This is your system design interview. I'll ask you to design scalable systems that handle millions of users. Focus on component architecture, bottleneck identification, and trade-offs between different approaches. Let's start designing!",
                "Welcome to the system design round! I want to see how you architect large-scale distributed systems. Think about scalability, reliability, and performance. Discuss your design choices and their trade-offs. Ready?",
                "Hi! I'll be your interviewer for system design. I'm looking for systematic thinking: requirements gathering, high-level design, component breakdown, and deep dives into critical parts. Let's build something!"
            ]
        }
        
        round_intros = intros.get(round_type, intros["technical"])
        intro = random.choice(round_intros)
        
        if resume_context:
            intro += " I see you've uploaded your resume, so I'll be asking you questions specifically about your background."
        
        intro += " But before that, let me ask you:"
        
        return intro
    
    
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
        Process answer, evaluate, and generate next question or complete interview
        
        FIXED: Proper question counting with hard stop at max questions
        """
        
        # Get actual question number for logging
        actual_q_num = state.config.get('actual_question_number', question_id)
        followup_count = state.config.get('followup_count', 0)
        
        print(f"\n{'='*60}")
        print(f"📝 PROCESSING ANSWER")
        print(f"   Question ID: Q{question_id}")
        print(f"   Actual Question Number: {actual_q_num}/{self.max_total_questions}")
        print(f"   Is Followup Answer: {is_followup_answer}")
        print(f"   Total Followups So Far: {followup_count}")
        print(f"   Phase: {state.current_phase.value}")
        print(f"   Questions in Phase: {state.questions_in_current_phase}")
        print(f"{'='*60}")
        
        # Step 1: Evaluate answer
        evaluation = self.analyzer.evaluate_answer(
            answer_text=answer_text,
            question_text=question_text,
            question_id=question_id,
            round_type=round_type,
            session_id=state.session_id,
            conversation_history=state.conversation_history,
            skip_claim_extraction=skip_claim_extraction
        )
        
        # Step 2: FIX - Increment question count ONLY for non-followup answers
        if not is_followup_answer:
            state.questions_in_current_phase += 1
            print(f"   ✅ New question answered")
            print(f"      Phase count: {state.questions_in_current_phase}")
        else:
            print(f"   🔁 Follow-up answer processed (not incrementing counters)")
        
        # Step 3: Update session state
        self._update_state_with_evaluation(state, evaluation, question_text, answer_text)
        
        # Initialize followup tracking flag
        if state.conversation_history:
            state.conversation_history[-1]['triggered_followup'] = False
            state.conversation_history[-1]['is_followup_answer'] = is_followup_answer
        
        # Step 4: Generate immediate feedback
        immediate_feedback = self._generate_immediate_feedback(evaluation)
        
        # ========================================
        # FIX: Check if we've hit max questions BEFORE followup check
        # ========================================
        if actual_q_num >= self.max_total_questions:
            print(f"\n🎉 INTERVIEW COMPLETED - Reached max questions ({self.max_total_questions})")
            print(f"   Total questions answered: {actual_q_num}")
            print(f"   Total followups: {followup_count}")
            
            return {
                "evaluation": evaluation.dict(),
                "immediate_feedback": immediate_feedback,
                "completed": True,
                "final_phase": True,
                "reason": f"Completed all {self.max_total_questions} questions"
            }
        
        # Step 5: Check for follow-up (only if we haven't hit max questions)
        needs_followup = self._should_ask_followup(
            evaluation, 
            answer_text, 
            state, 
            is_followup_answer,
            actual_q_num  # NEW: Pass current question number
        )
        
        if needs_followup:
            followup_q = self._generate_followup_question(
                evaluation, 
                question_text, 
                answer_text,
                state
            )
            
            if followup_q:
                print(f"\n🔍 Follow-up triggered: {evaluation.followup_reason or 'Low score/vague answer'}")
                
                # FIX: Mark followup and increment followup counter
                if state.conversation_history:
                    state.conversation_history[-1]['triggered_followup'] = True
                
                state.config['followup_count'] = state.config.get('followup_count', 0) + 1
                
                self._save_sessions()
                
                return {
                    "evaluation": evaluation.dict(),
                    "immediate_feedback": immediate_feedback,
                    "requires_followup": True,
                    "followup_question": followup_q,
                    "followup_reason": evaluation.followup_reason or "Answer needs clarification",
                    "completed": False,
                    "is_followup": True,
                    "question_number": actual_q_num,  # Don't increment
                    "total_questions_allowed": self.max_total_questions
                }
        
        # Step 6: Adjust difficulty
        state.difficulty_level = self._adjust_difficulty(
            state.difficulty_level,
            evaluation.difficulty_adjustment
        )
        
        # Step 7: Check phase transition
        phase_config = PHASE_TRANSITION_RULES.get(state.current_phase.value, {})
        force_transition_after = phase_config.get('force_transition_after', 999)
        
        print(f"\n📊 Phase Transition Check:")
        print(f"   Current phase: {state.current_phase.value}")
        print(f"   Questions in phase: {state.questions_in_current_phase}")
        print(f"   Force transition after: {force_transition_after}")
        
        if state.questions_in_current_phase >= force_transition_after:
            print(f"   ✅ Phase transition triggered (reached force_transition_after)")
            state.phases_completed.append(state.current_phase)
            state.current_phase = state.get_next_phase()
            state.questions_in_current_phase = 0
            self._save_sessions()
            
            print(f"   → New phase: {state.current_phase.value}")
            
            if state.current_phase == InterviewPhase.COMPLETED:
                print(f"\n🎉 INTERVIEW COMPLETED - All phases done!")
                return {
                    "evaluation": evaluation.dict(),
                    "immediate_feedback": immediate_feedback,
                    "completed": True,
                    "final_phase": True,
                    "reason": "Completed all phases"
                }
        
        # Step 8: Increment actual question number for NEXT question
        next_question_num = actual_q_num + 1
        state.config['actual_question_number'] = next_question_num
        
        print(f"\n🎲 Generating next question (Q{next_question_num})")
        
        # Step 9: Generate next question
        next_question = self._generate_question(
            state=state,
            round_type=round_type,
            resume_context=state.resume_context,
            previous_evaluation=evaluation
        )
        
        # Update state with new question
        state.current_question_text = next_question["text"]
        state.current_question_id = f"q_{next_question_num}"
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

    
    def _should_ask_followup(
        self, 
        evaluation: AnswerEvaluation, 
        answer_text: str,
        state: SessionState,
        is_followup_answer: bool = False,
        current_question_num: int = 0
    ) -> bool:
        """
        Determine if follow-up question is needed
        
        FIXED: Added question number check to prevent followups near the end
        """
        
        # NEW: Never followup if we're at or near max questions
        if current_question_num >= self.max_total_questions - 1:
            print(f"   ⏭️  Near end of interview (Q{current_question_num}/{self.max_total_questions}). No followups.")
            return False
        
        # RULE 1: Never follow-up a follow-up answer
        if is_followup_answer:
            print("   ⏭️  Current answer is a follow-up. Skipping further follow-ups.")
            return False

        # RULE 2: Never follow-up if we JUST triggered a follow-up
        if len(state.conversation_history) >= 1:
            last_qa = state.conversation_history[-1]
            if last_qa.get('triggered_followup', False):
                print("   ⏭️  Previous question had follow-up. Skipping to avoid consecutive follow-ups.")
                return False

        # RULE 3: Check max follow-ups (2 per session)
        followup_count = state.config.get('followup_count', 0)
        if followup_count >= 2:
            print(f"   ⏭️  Max follow-ups reached ({followup_count}/2). Skipping.")
            return False
        
        # RULE 4: Only follow-up for specific triggers
        
        # 1. If evaluator explicitly requested follow-up
        if evaluation.requires_followup:
            print(f"   🔍 Follow-up trigger: Evaluator requested")
            return True
        
        # 2. If score is very low
        if evaluation.overall_score < 55:
            print(f"   🔍 Follow-up trigger: Low score ({evaluation.overall_score}/100)")
            return True
        
        # 3. If answer is suspiciously short
        word_count = len(answer_text.split())
        if word_count < 30:
            print(f"   🔍 Follow-up trigger: Short answer ({word_count} words)")
            return True
        
        # 4. If there are red flags
        if len(evaluation.red_flags) > 0:
            print(f"   🔍 Follow-up trigger: Red flags detected ({len(evaluation.red_flags)})")
            return True
        
        # 5. If critical weaknesses detected
        critical_weaknesses = [
            "vague", "no specific", "missing details", 
            "unclear", "contradictory", "no metrics"
        ]
        for weakness in evaluation.weaknesses:
            if any(cw in weakness.lower() for cw in critical_weaknesses):
                print(f"   🔍 Follow-up trigger: Critical weakness - {weakness}")
                return True
        
        return False
    
    def _generate_followup_question(
        self,
        evaluation: AnswerEvaluation,
        original_question: str,
        answer_text: str,
        state: SessionState
    ) -> Optional[str]:
        """Generate smart follow-up question"""
        
        if evaluation.suggested_followup:
            return evaluation.suggested_followup
        
        weaknesses_str = "; ".join(evaluation.weaknesses[:2])
        
        prompt = [
            {
                "role": "system",
                "content": f"""You are an interviewer asking a brief follow-up question.

ORIGINAL QUESTION: {original_question}

CANDIDATE'S ANSWER: {answer_text[:300]}...

ISSUES DETECTED: {weaknesses_str}

Generate ONE short, direct follow-up question (1 sentence) that:
1. Asks for specific details they missed
2. Probes deeper into vague points
3. Requests concrete examples or metrics

Output ONLY the question, nothing else."""
            },
            {
                "role": "user",
                "content": "Generate the follow-up question."
            }
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
    
    
    def _generate_question(
        self,
        state: SessionState,
        round_type: str,
        resume_context: Optional[str] = None,
        previous_evaluation: Optional[AnswerEvaluation] = None
    ) -> Dict:
        """Generate next question based on state and round type"""
        
        print(f"\n🎲 Generating {round_type.upper()} question...")
        print(f"   Phase: {state.current_phase.value}")
        print(f"   Difficulty: {state.difficulty_level}/10")
        
        # Build prompt based on round type
        if round_type == "hr":
            prompt = self._build_hr_question_prompt(state, resume_context, previous_evaluation)
        elif round_type == "technical":
            prompt = self._build_technical_question_prompt(state, resume_context, previous_evaluation)
        elif round_type == "system_design":
            prompt = self._build_sysdesign_question_prompt(state, resume_context, previous_evaluation)
        else:
            prompt = self._build_technical_question_prompt(state, resume_context, previous_evaluation)
        
        # Get LLM response
        raw_question = get_llm_response(prompt, temperature=0.7)
        
        # Clean question
        question_text = self._clean_question(raw_question)
        
        print(f"   ✓ Generated: {question_text[:80]}...")
        
        return {
            "text": question_text,
            "round_type": round_type,
            "phase": state.current_phase.value,
            "difficulty": state.difficulty_level,
            "question_number": state.config.get('actual_question_number', len(state.conversation_history) + 1)
        }
    
    
    def _build_hr_question_prompt(
        self,
        state: SessionState,
        resume_context: Optional[str],
        previous_evaluation: Optional[AnswerEvaluation]
    ) -> List[Dict]:
        """Build prompt for HR round question"""
        
        system_prompt = f"""You are an expert HR interviewer conducting a behavioral interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

YOUR GOAL:
Ask ONE behavioral question that tests STAR method (Situation, Task, Action, Result).

PHASE-SPECIFIC FOCUS:
{self._get_phase_specific_guidance(state.current_phase, "hr")}

QUESTION REQUIREMENTS:
- Ask about specific experiences, not general approaches
- Encourage storytelling with concrete examples
- Probe for metrics and measurable outcomes
- Focus on ownership and decision-making

DIFFICULTY GUIDELINES:
{self._get_difficulty_guidance(state.difficulty_level, "hr")}

OUTPUT:
Just the question text, nothing else."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}...\n\nReference specific experiences from their resume."
        
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS ANSWER SCORE: {previous_evaluation.overall_score}/100"
            if previous_evaluation.overall_score < 60:
                system_prompt += "\nAdjust difficulty DOWN - ask a more straightforward question."
            elif previous_evaluation.overall_score > 80:
                system_prompt += "\nAdjust difficulty UP - ask a more challenging question."
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS ASKED:\n{history_context}\n\nDo NOT repeat similar questions. Specifically, the candidate has ALREADY introduced themselves. Ask a NEW behavioral question about their experience."
        else:
            system_prompt += "\n\nCRITICAL: This is the FIRST question. Ask the candidate to introduce themselves, their background, and their key strengths in a way that fits this HR/Behavioral round."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next behavioral interview question."}
        ]
        
        return messages
    
    
    def _build_technical_question_prompt(
        self,
        state: SessionState,
        resume_context: Optional[str],
        previous_evaluation: Optional[AnswerEvaluation]
    ) -> List[Dict]:
        """Build prompt for Technical round question"""
        
        system_prompt = f"""You are a senior software engineer conducting a technical interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

YOUR GOAL:
Ask ONE technical question that tests depth, accuracy, and problem-solving.

PHASE-SPECIFIC FOCUS:
{self._get_phase_specific_guidance(state.current_phase, "technical")}

QUESTION REQUIREMENTS:
- Test conceptual understanding (not just definitions)
- Probe for trade-offs and edge cases
- Encourage discussion of time/space complexity
- Ask about real-world application

DIFFICULTY GUIDELINES:
{self._get_difficulty_guidance(state.difficulty_level, "technical")}

OUTPUT:
Just the question text, nothing else."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}...\n\nAsk about technologies they claim to know."
        
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS ANSWER SCORE: {previous_evaluation.overall_score}/100"
            
            if previous_evaluation.weaknesses:
                system_prompt += f"\nWEAKNESSES DETECTED: {', '.join(previous_evaluation.weaknesses[:2])}"
                system_prompt += "\nProbe these weak areas with targeted questions."
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS:\n{history_context}\n\nAsk about different topics."
        else:
            system_prompt += "\n\nCRITICAL: This is the FIRST question. Ask the candidate to introduce themselves and their technical background/expertise in a way that fits this Technical round."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next technical interview question."}
        ]
        
        return messages
    
    
    def _build_sysdesign_question_prompt(
        self,
        state: SessionState,
        resume_context: Optional[str],
        previous_evaluation: Optional[AnswerEvaluation]
    ) -> List[Dict]:
        """Build prompt for System Design round question"""
        
        system_prompt = f"""You are a principal architect conducting a system design interview.

CURRENT PHASE: {state.current_phase.value}
DIFFICULTY LEVEL: {state.difficulty_level}/10
QUESTIONS ASKED: {len(state.conversation_history)}

YOUR GOAL:
Ask ONE system design question that tests architecture, scalability, and trade-offs.

PHASE-SPECIFIC FOCUS:
{self._get_phase_specific_guidance(state.current_phase, "system_design")}

QUESTION REQUIREMENTS:
- Ask about designing real-world systems
- Expect discussion of components (load balancer, cache, database, etc)
- Probe for bottleneck identification
- Test scalability thinking (millions of users)

DIFFICULTY GUIDELINES:
{self._get_difficulty_guidance(state.difficulty_level, "system_design")}

OUTPUT:
Just the question text, nothing else."""

        if resume_context:
            system_prompt += f"\n\nRESUME CONTEXT:\n{resume_context[:500]}...\n\nReference systems they've built."
        
        if previous_evaluation:
            system_prompt += f"\n\nPREVIOUS ANSWER SCORE: {previous_evaluation.overall_score}/100"
            
            if previous_evaluation.scores.get("technical_depth", 0) < 60:
                system_prompt += "\nStart with simpler systems (URL shortener, cache)."
            elif previous_evaluation.scores.get("technical_depth", 0) > 80:
                system_prompt += "\nAsk about complex distributed systems."
        
        history_context = self._build_history_context(state.conversation_history)
        if history_context:
            system_prompt += f"\n\nPREVIOUS QUESTIONS:\n{history_context}\n\nDesign different types of systems."
        else:
            system_prompt += "\n\nCRITICAL: This is the FIRST question. Ask the candidate to introduce themselves and their experience with building large-scale systems in a way that fits this System Design round."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the next system design question."}
        ]
        
        return messages
    
    
    def _get_phase_specific_guidance(self, phase: InterviewPhase, round_type: str) -> str:
        """Get guidance text for specific phase and round combination"""
        
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
                "hr": "Present HYPOTHETICAL real-world conflicts. Phrasing: 'Imagine you are in a situation where... what would you do?'. Focus on future actions and reasoning.",
                "technical": "Give debugging scenarios and edge cases to solve.",
                "system_design": "Present scaling challenges and ask for solutions."
            },
            InterviewPhase.STRESS_TESTING: {
                "hr": "Present HYPOTHETICAL high-pressure scenarios. Phrasing: 'Imagine you have a tight deadline and... how would you prioritize?'.",
                "technical": "Ask about optimization under constraints.",
                "system_design": "Design systems under extreme scale (billions of users)."
            },
            InterviewPhase.CLAIM_VERIFICATION: {
                "hr": "Follow up on vague claims from earlier answers.",
                "technical": "Probe deeper into technical claims that seemed suspicious.",
                "system_design": "Ask for specifics about scalability claims."
            },
            InterviewPhase.WRAP_UP: {
                "hr": "Final opportunity: 'What would you like us to know about you?'",
                "technical": "Final challenge: 'What's the hardest technical problem you've solved?'",
                "system_design": "Final design: 'Design your dream system with unlimited resources.'"
            }
        }
        
        return phase_guidance.get(phase, {}).get(round_type, "Ask a relevant question for this phase.")
    
    
    def _get_difficulty_guidance(self, difficulty_level: int, round_type: str) -> str:
        """Get difficulty-appropriate question guidance"""
        
        if difficulty_level <= 3:
            return "EASY: Ask straightforward questions with clear answers."
        elif difficulty_level <= 6:
            return "MEDIUM: Ask questions requiring trade-off analysis."
        else:
            return "HARD: Ask questions with multiple layers and edge cases."
    
    
    def _update_state_with_evaluation(
        self,
        state: SessionState,
        evaluation: AnswerEvaluation,
        question_text: str,
        answer_text: str
    ):
        """Update session state with new evaluation"""
        
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
            state.add_red_flag(
                flag_type="evaluation_flag",
                description=flag,
                question_id=str(evaluation.question_id)
            )
        
        state.update_activity()
    
    
    def _adjust_difficulty(self, current_level: int, adjustment: str) -> int:
        """Adjust difficulty level based on performance"""
        
        if adjustment == "increase":
            return min(10, current_level + 1)
        elif adjustment == "decrease":
            return max(1, current_level - 1)
        else:
            return current_level
    
    
    def _generate_immediate_feedback(self, evaluation: AnswerEvaluation) -> Dict:
        """Generate immediate feedback to show after answer"""
        
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
        """Build context string from conversation history"""
        
        if not history:
            return ""
        
        context_parts = []
        for i, item in enumerate(history[-3:], 1):
            q = item.get("question", "")
            context_parts.append(f"{i}. {q}")
        
        return "\n".join(context_parts)
    
    
    def _clean_question(self, raw_question: str) -> str:
        """Clean LLM-generated question"""
        
        question = raw_question.strip()
        question = question.replace("**", "").replace("*", "")
        
        prefixes = ["Question:", "Q:", "Next question:", "Here's the question:"]
        for prefix in prefixes:
            if question.startswith(prefix):
                question = question[len(prefix):].strip()
        
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        if question.startswith("'") and question.endswith("'"):
            question = question[1:-1]
        
        return question
    
    
    def _parse_round_type(self, round_type_str: str) -> RoundType:
        """Parse round type string to enum"""
        
        round_type_str = round_type_str.lower().strip()
        
        if "hr" in round_type_str or "behavioral" in round_type_str:
            return RoundType.HR
        elif "system" in round_type_str or "design" in round_type_str:
            return RoundType.SYSTEM_DESIGN
        else:
            return RoundType.TECHNICAL
    
    
    def _get_phase_info(self, phase: InterviewPhase) -> Dict:
        """Get phase information for frontend"""
        
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
    """Get singleton instance of interview orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InterviewOrchestrator()
    return _orchestrator_instance