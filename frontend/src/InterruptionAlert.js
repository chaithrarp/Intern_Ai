import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './InterruptionAlert.css';

function InterruptionAlert({ interruption, onAcknowledge }) {
  if (!interruption) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="interruption-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onAcknowledge}
      >
        <motion.div
          className="interruption-alert"
          initial={{ scale: 0.8, y: -50, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          exit={{ scale: 0.8, y: 50, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
          {/* Alert Icon */}
          <motion.div
            className="interruption-icon"
            initial={{ rotate: 0 }}
            animate={{ rotate: [0, -10, 10, -10, 0] }}
            transition={{ duration: 0.5, repeat: 2 }}
          >
            ⚡
          </motion.div>

          {/* Interruption Phrase */}
          <motion.div
            className="interruption-phrase"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {interruption.interruption_phrase}
          </motion.div>

          {/* Follow-up Question */}
          <motion.div
            className="interruption-question"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <p className="question-label">Quick Follow-up:</p>
            <p className="question-text">{interruption.followup_question}</p>
          </motion.div>

          {/* Acknowledge Button */}
          <motion.button
            className="btn-acknowledge"
            onClick={onAcknowledge}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Got it - Let me answer
          </motion.button>

          {/* Pressure Indicator */}
          <motion.div
            className="pressure-badge"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <span className="pressure-icon">🔥</span>
            <span className="pressure-text">Pressure Mode</span>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default InterruptionAlert;