import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './LiveWarning.css';

const SEVERITY_LABELS = {
  critical: '🚨 Critical Warning',
  high:     '⚠️ Warning',
  medium:   '⚡ Heads Up',
  low:      '💡 Tip',
};

function LiveWarning({ warning }) {
  if (!warning) return null;

  const severity = warning.severity || 'medium';

  return (
    <AnimatePresence>
      <motion.div
        className="live-warning-container"
        key="live-warning"
        initial={{ opacity: 0, x: 60, scale: 0.88 }}
        animate={{ opacity: 1, x: 0,  scale: 1    }}
        exit={{    opacity: 0, x: 60, scale: 0.88 }}
        transition={{ type: 'spring', stiffness: 320, damping: 26 }}
      >
        <div className={`live-warning live-warning-${severity}`}>

          {/* Icon */}
          <motion.span
            className="warning-icon"
            animate={{ rotate: [0, -12, 12, -6, 0] }}
            transition={{ duration: 0.55, delay: 0.1 }}
          >
            {warning.icon || (severity === 'critical' ? '🚨' : severity === 'high' ? '⚠️' : '⚡')}
          </motion.span>

          {/* Text block */}
          <div className="warning-content">
            <span className="warning-label">
              {SEVERITY_LABELS[severity] || '⚠️ Warning'}
            </span>
            <motion.span
              className="warning-message"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.12 }}
            >
              {warning.message}
            </motion.span>
          </div>

          {/* Bottom progress/severity bar */}
          <motion.div
            className="warning-severity-bar"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            style={{ backgroundColor: warning.color || '#eab308' }}
          />
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default LiveWarning;