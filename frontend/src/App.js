import React, { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import Interview from './Interview'; 
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
    </div>
  );
}

export default App;
