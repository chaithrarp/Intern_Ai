import React, { useState } from 'react';
import { motion } from 'framer-motion';
import AIInterviewer from './AIInterviewer';
import './WelcomeScreen.css';

function WelcomeScreen({ onStart }) {
  const [isHovering, setIsHovering] = useState(false);

  return (
    <motion.div 
      className="welcome-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.2 }}
    >
      {/* Animated background */}
      <div className="welcome-background"></div>
      <div className="glow-orbs"></div>

      {/* Content */}
      <div className="welcome-content">
        
        {/* Pre-title */}
        <motion.div
          className="pre-title"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          <span className="line"></span>
          <span className="text">AI-POWERED INTERVIEW TRAINING</span>
          <span className="line"></span>
        </motion.div>

        {/* Main Title with 3D effect */}
        <motion.h1 
          className="welcome-title"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 1, type: 'spring' }}
        >
          <span className="title-word">Intern</span>
          <span className="title-word accent">AI</span>
        </motion.h1>

        {/* AI Particle Cloud */}
        <motion.div
          className="ai-container"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.7, duration: 1.2, type: 'spring' }}
        >
          <AIInterviewer state="idle" />
        </motion.div>

        {/* Tagline */}
        <motion.p 
          className="welcome-tagline"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
        >
          Master performance under <span className="highlight">pressure</span>
        </motion.p>

        {/* Start Button */}
        <motion.button
          className="welcome-button"
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.8 }}
          whileHover={{ 
            scale: 1.08,
            boxShadow: '0 0 60px rgba(0, 240, 255, 0.8)',
          }}
          whileTap={{ scale: 0.95 }}
          onClick={onStart}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
        >
          <span className="button-glow"></span>
          <span className="button-text">Begin Interview</span>
          <motion.span 
            className="button-arrow"
            animate={{ x: isHovering ? 8 : 0 }}
            transition={{ duration: 0.3 }}
          >
            →
          </motion.span>
        </motion.button>

      </div>

      {/* Floating particles background */}
      <div className="floating-dots">
        {[...Array(30)].map((_, i) => (
          <div 
            key={i} 
            className="dot"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${8 + Math.random() * 12}s`,
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}

export default WelcomeScreen;