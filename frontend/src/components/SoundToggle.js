import React, { useState } from 'react';
import { motion } from 'framer-motion';
import soundEffects from '../utils/soundEffects';
import './SoundToggle.css';

function SoundToggle() {
  const [soundEnabled, setSoundEnabled] = useState(true);

  const toggleSound = () => {
    const newState = !soundEnabled;
    setSoundEnabled(newState);
    soundEffects.setEnabled(newState);
    
    // Play notification to confirm (if enabling)
    if (newState) {
      soundEffects.playNotification();
    }
  };

  return (
    <motion.button
      className={`sound-toggle ${soundEnabled ? 'enabled' : 'disabled'}`}
      onClick={toggleSound}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      title={soundEnabled ? 'Mute sounds' : 'Enable sounds'}
    >
      {soundEnabled ? '🔊' : '🔇'}
    </motion.button>
  );
}

export default SoundToggle;