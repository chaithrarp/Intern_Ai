import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './PersonaSelector.css';

function PersonaSelector({ onPersonaSelected, onBack }) {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPersonas();
  }, []);

  const fetchPersonas = async () => {
    try {
      const response = await fetch('http://localhost:8000/personas/list');
      const data = await response.json();
      
      if (data.success) {
        // Convert personas object to array
        const personasArray = Object.keys(data.personas).map(key => ({
          id: key,
          ...data.personas[key]
        }));
        setPersonas(personasArray);
      }
    } catch (error) {
      console.error('Error fetching personas:', error);
      // Fallback personas
      setPersonas([
        {
          id: 'friendly_coach',
          name: 'Friendly Coach',
          emoji: '🟢',
          description: 'Supportive and encouraging - perfect for practice',
          interruption_probability: 0.20
        },
        {
          id: 'standard_professional',
          name: 'Standard Professional',
          emoji: '🟡',
          description: 'Realistic interview simulation - balanced pressure',
          interruption_probability: 0.50
        },
        {
          id: 'aggressive_challenger',
          name: 'Aggressive Challenger',
          emoji: '🔴',
          description: 'High-pressure stress test - maximum difficulty',
          interruption_probability: 0.80
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPersona = (personaId) => {
    setSelectedPersona(personaId);
  };

  const handleStartInterview = () => {
    if (selectedPersona) {
      onPersonaSelected(selectedPersona);
    }
  };

  const getDifficultyLabel = (probability) => {
    if (probability <= 0.3) return { text: 'BEGINNER', color: '#10b981' };
    if (probability <= 0.6) return { text: 'INTERMEDIATE', color: '#f59e0b' };
    return { text: 'EXPERT', color: '#ef4444' };
  };

  if (loading) {
    return (
      <div className="persona-selector-container">
        <div className="loading-personas">
          <div className="spinner"></div>
          <p>Loading interviewer personas...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      className="persona-selector-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="persona-selector-content">
        
        {/* Header */}
        <motion.div 
          className="persona-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1>🎭 Choose Your Interviewer</h1>
          <p className="persona-subtitle">
            Select the pressure level that matches your preparation goals
          </p>
        </motion.div>

        {/* Persona Cards */}
        <motion.div 
          className="personas-grid"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {personas.map((persona, index) => {
            const difficulty = getDifficultyLabel(persona.interruption_probability);
            const isSelected = selectedPersona === persona.id;

            return (
              <motion.div
                key={persona.id}
                className={`persona-card ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectPersona(persona.id)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + (index * 0.1) }}
                whileHover={{ scale: 1.03, y: -5 }}
                whileTap={{ scale: 0.98 }}
              >
                {/* Selection Indicator */}
                {isSelected && (
                  <motion.div 
                    className="selected-badge"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                  >
                    ✓
                  </motion.div>
                )}

                {/* Persona Emoji */}
                <div className="persona-emoji">{persona.emoji}</div>

                {/* Persona Name */}
                <h3 className="persona-name">{persona.name}</h3>

                {/* Description */}
                <p className="persona-description">{persona.description}</p>

                {/* Difficulty Badge */}
                <div 
                  className="difficulty-badge"
                  style={{ backgroundColor: difficulty.color }}
                >
                  {difficulty.text}
                </div>

                {/* Interruption Probability */}
                <div className="persona-stats">
                  <div className="stat-item">
                    <span className="stat-label">Interruption Rate:</span>
                    <span className="stat-value">{Math.round(persona.interruption_probability * 100)}%</span>
                  </div>
                  
                  {/* Visual bar */}
                  <div className="probability-bar">
                    <div 
                      className="probability-fill"
                      style={{ 
                        width: `${persona.interruption_probability * 100}%`,
                        backgroundColor: difficulty.color
                      }}
                    />
                  </div>
                </div>

                {/* Persona Traits */}
                <div className="persona-traits">
                  {persona.id === 'friendly_coach' && (
                    <>
                      <span className="trait">✓ Encouraging</span>
                      <span className="trait">✓ Patient</span>
                      <span className="trait">✓ Constructive</span>
                    </>
                  )}
                  {persona.id === 'standard_professional' && (
                    <>
                      <span className="trait">✓ Balanced</span>
                      <span className="trait">✓ Realistic</span>
                      <span className="trait">✓ Professional</span>
                    </>
                  )}
                  {persona.id === 'aggressive_challenger' && (
                    <>
                      <span className="trait">✓ Demanding</span>
                      <span className="trait">✓ Sharp</span>
                      <span className="trait">✓ Intense</span>
                    </>
                  )}
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Action Buttons */}
        <motion.div 
          className="persona-actions"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <button className="btn-back" onClick={onBack}>
            ← Back
          </button>
          
          <button 
            className="btn-start-interview"
            onClick={handleStartInterview}
            disabled={!selectedPersona}
          >
            {selectedPersona 
              ? `Start Interview with ${personas.find(p => p.id === selectedPersona)?.name}`
              : 'Select a Persona First'
            }
          </button>
        </motion.div>

        {/* Tips */}
        <motion.div 
          className="persona-tips"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0 }}
        >
          <h4>💡 Quick Tips:</h4>
          <ul>
            <li><strong>Friendly Coach:</strong> Best for first-time practice and building confidence</li>
            <li><strong>Standard Professional:</strong> Realistic simulation of typical interviews</li>
            <li><strong>Aggressive Challenger:</strong> Stress test for experienced candidates</li>
          </ul>
        </motion.div>

      </div>
    </motion.div>
  );
}

export default PersonaSelector;