import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import voiceService from './utils/voiceService';
import './InterruptionAlert.css';

/**
 * InterruptionAlert v2
 *
 * Changes:
 * - Shows display_reason as natural language (e.g. "Seems like you're struggling")
 * - Correct interruption_count / max_interruptions counter
 * - Icon from server response
 * - Speaks phrase + follow-up automatically
 */
function InterruptionAlert({ interruption, onAcknowledge }) {
  useEffect(() => {
    if (!interruption) return;

    const phrase = interruption.interruption_phrase || "Let me stop you there.";
    const followup = interruption.followup_question || '';

    const speakSequence = async () => {
      try {
        await voiceService.speak(phrase);
        if (followup) {
          await new Promise(r => setTimeout(r, 450));
          await voiceService.speak(followup);
        }
      } catch (e) {
        console.error('Voice error in interruption alert:', e);
      }
    };

    speakSequence();
    return () => voiceService.stop();
  }, [interruption]);

  if (!interruption) return null;

  const count     = interruption.interruption_count ?? '?';
  const max       = interruption.max_interruptions ?? 2;
  // Prefer the human-readable display_reason; fall back to mapping the raw reason
  const displayReason = interruption.display_reason || _fallbackLabel(interruption.reason);
  const icon      = interruption.icon || '✋';

  return (
    <AnimatePresence>
      <motion.div
        className="interruption-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="interruption-alert"
          initial={{ scale: 0.85, y: -40, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          exit={{ scale: 0.85, y: 40, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 280, damping: 22 }}
        >
          {/* Header row */}
          <div className="interruption-header">
            <motion.span
              className="interruption-icon"
              animate={{ rotate: [0, -12, 12, -8, 0] }}
              transition={{ duration: 0.5, repeat: 1 }}
            >
              {icon}
            </motion.span>
            <div className="interruption-header-text">
            </div>
          </div>

          {/* Natural-language reason badge */}
          {displayReason && (
            <div className="interruption-reason-badge">
              {displayReason}
            </div>
          )}

          {/* What the interviewer said */}
          <motion.div
            className="interruption-phrase"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <span className="phrase-quote-mark">"</span>
            {interruption.interruption_phrase || "Let me stop you there."}
            <span className="phrase-quote-mark">"</span>
          </motion.div>

          {/* Follow-up question */}
          {interruption.followup_question && (
            <motion.div
              className="interruption-question"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <p className="question-label">New question for you:</p>
              <p className="question-text">{interruption.followup_question}</p>
            </motion.div>
          )}

          {/* Acknowledge button */}
          <motion.button
            className="btn-acknowledge"
            onClick={onAcknowledge}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
          >
            Got it — I'll answer this
          </motion.button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

/** Fallback if display_reason not sent from server */
function _fallbackLabel(reason) {
  const map = {
    EXCESSIVE_RAMBLING:   'Seems like you\'re going off on tangents',
    DODGING_QUESTION:     'Seems like you\'re avoiding the question',
    FILLER_HEAVY:         'Seems like you\'re struggling to express yourself',
    CONTRADICTION:        'Seems like you\'re contradicting yourself',
    FALSE_CLAIM:          'Seems like that claim doesn\'t match your background',
    COMPLETELY_OFF_TOPIC: 'Seems like you\'re going off-topic',
    VAGUE_EVASION:        'Seems like you\'re not clear on the concept',
    STRUGGLING:           'Seems like you\'re struggling with this question',
    MANIPULATION_ATTEMPT: 'Seems like you\'re deflecting instead of answering',
  };
  return map[reason] || (reason ? reason.replace(/_/g, ' ') : '');
}

export default InterruptionAlert;