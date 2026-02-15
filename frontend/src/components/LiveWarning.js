import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './LiveWarning.css';

/**
 * LiveWarning - Floating non-interrupting warning component
 * Shows real-time feedback during recording without interrupting
 */
function LiveWarning({ warning }) {
  if (!warning) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="live-warning-container"
        initial={{ opacity: 0, y: -20, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.9 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <motion.div
          className={`live-warning live-warning-${warning.severity || 'medium'}`}
          initial={{ x: -10 }}
          animate={{ x: 0 }}
        >
          {/* Warning Icon */}
          <motion.span
            className="warning-icon"
            initial={{ rotate: 0 }}
            animate={{ rotate: [0, -10, 10, 0] }}
            transition={{ duration: 0.5, repeat: 1 }}
          >
            {warning.icon || '⚠️'}
          </motion.span>

          {/* Warning Message */}
          <motion.span
            className="warning-message"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            {warning.message}
          </motion.span>

          {/* Severity Indicator */}
          <motion.div
            className="warning-severity-bar"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.3 }}
            style={{
              backgroundColor: warning.color || '#ffc107'
            }}
          />
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default LiveWarning;