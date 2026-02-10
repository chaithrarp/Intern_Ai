import React, { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import ResumeUpload from './components/ResumeUpload';
import Interview from './Interview';
import SoundToggle from './components/SoundToggle';
import './App.css';

function App() {
  const [showInterview, setShowInterview] = useState(false);
  const [showResumeUpload, setShowResumeUpload] = useState(false);
  const [resumeData, setResumeData] = useState(null);

  const handleStartInterview = () => {
    // Show resume upload screen instead of going directly to interview
    setShowResumeUpload(true);
  };

  const handleResumeUploaded = (data) => {
    // Resume was uploaded successfully
    setResumeData(data);
    setShowResumeUpload(false);
    setShowInterview(true);
  };

  const handleSkipResume = () => {
    // User chose to skip resume upload
    setResumeData(null);
    setShowResumeUpload(false);
    setShowInterview(true);
  };

  return (
    <div className="App">
      {!showInterview && !showResumeUpload && (
        <WelcomeScreen onStart={handleStartInterview} />
      )}
      
      {showResumeUpload && (
        <ResumeUpload 
          onResumeUploaded={handleResumeUploaded}
          onSkip={handleSkipResume}
        />
      )}
      
      {showInterview && (
        <Interview resumeData={resumeData} />
      )}
      
      {/* PHASE 8: Sound Toggle */}
      <SoundToggle />
    </div>
  );
}

export default App;