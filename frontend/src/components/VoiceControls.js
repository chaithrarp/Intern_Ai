import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import voiceService from '../utils/voiceService';
import './VoiceControls.css';

function VoiceControls({ text, autoPlay = true, onSpeakingChange }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [hasSpoken, setHasSpoken] = useState(false);

  // Auto-play when text changes
  useEffect(() => {
    if (text && autoPlay && !hasSpoken) {
      handleSpeak();
      setHasSpoken(true);
    }
    
    // Cleanup: stop speaking when component unmounts or text changes
    return () => {
      voiceService.stop();
      setIsSpeaking(false);
    };
  }, [text]);

  // Reset hasSpoken when text changes
  useEffect(() => {
    setHasSpoken(false);
  }, [text]);

  const handleSpeak = async () => {
    if (!text) return;

    setIsSpeaking(true);
    if (onSpeakingChange) onSpeakingChange(true);

    try {
      await voiceService.speak(text);
    } catch (error) {
      console.error('Speech error:', error);
    } finally {
      setIsSpeaking(false);
      if (onSpeakingChange) onSpeakingChange(false);
    }
  };

  const handleStop = () => {
    voiceService.stop();
    setIsSpeaking(false);
    if (onSpeakingChange) onSpeakingChange(false);
  };

  const handleReplay = () => {
    handleSpeak();
  };

  return (
    <div className="voice-controls-minimal">
      {!isSpeaking ? (
        <motion.button
          className="voice-icon-btn"
          onClick={handleReplay}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          title="Listen to question"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
          </svg>
        </motion.button>
      ) : (
        <motion.button
          className="voice-icon-btn voice-speaking"
          onClick={handleStop}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          title="Stop speaking"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            strokeLinecap="round" 
            strokeLinejoin="round"
            className="sound-wave-icon"
          >
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" className="wave-1" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" className="wave-2" />
          </svg>
        </motion.button>
      )}
    </div>
  );
}

export default VoiceControls;