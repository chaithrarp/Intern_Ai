import React, { useState, useEffect } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import ResumeUpload from './components/ResumeUpload';
import Interview from './Interview';
import Login from './components/Login';
import Register from './components/Register';
import SoundToggle from './components/SoundToggle';
import UserMenu from './components/UserMenu';
import SessionHistory from './components/SessionHistory';
import './App.css';

function App() {
  const [showInterview, setShowInterview] = useState(false);
  const [showResumeUpload, setShowResumeUpload] = useState(false);
  const [showHistory, setShowHistory] = useState(false);         // ← NEW
  const [resumeData, setResumeData] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authView, setAuthView] = useState('login');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        try {
          const response = await fetch('http://localhost:8000/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          if (response.ok) {
            const userData = await response.json();
            setCurrentUser(userData);
            setIsAuthenticated(true);
          } else {
            localStorage.removeItem('token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('user');
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
          localStorage.removeItem('token_type');
          localStorage.removeItem('user');
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const handleLoginSuccess = (userData) => {
    setCurrentUser(userData);
    setIsAuthenticated(true);
  };

  const handleRegisterSuccess = (userData) => {
    setCurrentUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('token');
    try {
      if (token) {
        await fetch('http://localhost:8000/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setCurrentUser(null);
      setShowInterview(false);
      setShowResumeUpload(false);
      setShowHistory(false);
      setResumeData(null);
    }
  };

  const handleStartInterview = () => {
    setShowHistory(false);
    setShowResumeUpload(true);
  };

  const handleResumeUploaded = (data) => {
    setResumeData(data);
    setShowResumeUpload(false);
    setShowInterview(true);
  };

  const handleSkipResume = () => {
    setResumeData(null);
    setShowResumeUpload(false);
    setShowInterview(true);
  };

  const handleBackToWelcome = () => {
    setShowInterview(false);
    setShowResumeUpload(false);
    setShowHistory(false);
    setResumeData(null);
  };

  // ← NEW: called from FeedbackScreen "View History" button
  const handleViewHistory = () => {
    setShowInterview(false);
    setShowResumeUpload(false);
    setShowHistory(true);
  };

  if (loading) {
    return (
      <div className="App loading-app">
        <div className="loading-spinner">
          <div className="spinner-orb">🤖</div>
          <p>Loading InternAI...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {!isAuthenticated && (
        <>
          {authView === 'login' ? (
            <Login onLoginSuccess={handleLoginSuccess} onSwitchToRegister={() => setAuthView('register')} />
          ) : (
            <Register onRegisterSuccess={handleRegisterSuccess} onSwitchToLogin={() => setAuthView('login')} />
          )}
        </>
      )}

      {isAuthenticated && (
        <>
          <UserMenu user={currentUser} onLogout={handleLogout} />

          {!showInterview && !showResumeUpload && !showHistory && (
            <WelcomeScreen onStart={handleStartInterview} user={currentUser} />
          )}

          {showResumeUpload && (
            <ResumeUpload onResumeUploaded={handleResumeUploaded} onSkip={handleSkipResume} />
          )}

          {showInterview && (
            <Interview
              resumeData={resumeData}
              onBack={handleBackToWelcome}
              onViewHistory={handleViewHistory}   // ← NEW: passed down
            />
          )}

          {/* ← NEW: Session History view */}
          {showHistory && (
            <SessionHistory
              onBack={handleBackToWelcome}
              onStartNew={handleStartInterview}
            />
          )}

          <SoundToggle />
        </>
      )}
    </div>
  );
}

export default App;