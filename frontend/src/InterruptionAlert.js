import React, { useEffect, useRef } from 'react';
import voiceService from './utils/voiceService';
import { motion, AnimatePresence } from 'framer-motion';
import './InterruptionAlert.css';

function InterruptionAlert({ interruption, onAcknowledge }) {
  const hasSpokenRef = useRef(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!interruption) return;
    if (hasSpokenRef.current) return;
    hasSpokenRef.current = true;

    timerRef.current = setTimeout(() => {
      const textToSpeak = `${interruption.interruption_phrase} ${interruption.followup_question}`;
      console.log('🔊 Speaking:', textToSpeak.substring(0, 60));
      voiceService.speak(textToSpeak)
        .then(() => console.log('✅ Interruption audio done'))
        .catch(err => console.error('❌ Voice error:', err));
    }, 1500);

    // NO cleanup — removing return() so re-renders don't cancel the timer

  }, [interruption]);

  if (!interruption) return null;

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
          initial={{ scale: 0.8, y: -50, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          exit={{ scale: 0.8, y: 50, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
          <motion.div
            className="interruption-icon"
            animate={{ rotate: [0, -10, 10, -10, 0] }}
            transition={{ duration: 0.5, repeat: 2 }}
          >
            ⚡
          </motion.div>

          <motion.div className="interruption-phrase" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            {interruption.interruption_phrase}
          </motion.div>

          <motion.div className="interruption-question" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <p className="question-label">Quick Follow-up:</p>
            <p className="question-text">{interruption.followup_question}</p>
          </motion.div>

          <motion.button
            className="btn-acknowledge"
            onClick={(e) => { e.stopPropagation(); voiceService.stop(); onAcknowledge(); }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Got it - Let me answer
          </motion.button>

          <motion.div className="pressure-badge" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            <span className="pressure-icon">🔥</span>
            <span className="pressure-text">Pressure Mode</span>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default InterruptionAlert;