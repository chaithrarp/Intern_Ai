import React, { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import Interview from './Interview';
import SoundToggle from './components/SoundToggle';
import './App.css';

function App() {
  const [showInterview, setShowInterview] = useState(false);

  const handleStartInterview = () => {
    setShowInterview(true);
  };

  return (
    <div className="App">
      {!showInterview ? (
        <WelcomeScreen onStart={handleStartInterview} />
      ) : (
        <Interview />
      )}
      
      {/* PHASE 8: Sound Toggle */}
      <SoundToggle />
    </div>
  );
}

export default App;