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
  const [showHistory, setShowHistory] = useState(false);
  const [resumeData, setResumeData] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authView, setAuthView] = useState('login');
  const [loading, setLoading] = useState(true);

  // ── Track where user came from before going to History ──────────────────
  // 'welcome' | 'interview' (interview includes the feedback screen at the end)
  const [historyReturnTo, setHistoryReturnTo] = useState('welcome');

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

  // ── View History — remember where we came from ───────────────────────────
  // Called from FeedbackScreen (inside Interview) → return to interview/feedback
  const handleViewHistoryFromInterview = () => {
    setHistoryReturnTo('interview');
    setShowHistory(true);
    // Don't setShowInterview(false) — keep it true so back returns to it
  };

  // Called from WelcomeScreen (if you add a history button there) → return to welcome
  const handleViewHistoryFromWelcome = () => {
    setHistoryReturnTo('welcome');
    setShowInterview(false);
    setShowHistory(true);
  };

  // ── History back button — goes to correct previous screen ───────────────
  const handleHistoryBack = () => {
    setShowHistory(false);
    if (historyReturnTo === 'interview') {
      // Return to the interview/feedback screen (showInterview is still true)
      // Nothing else to set — Interview component is still mounted showing FeedbackScreen
    } else {
      // Return to welcome
      setShowInterview(false);
      setShowResumeUpload(false);
      setResumeData(null);
    }
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

          {/* Welcome screen — hidden when interview/history is showing */}
          {!showInterview && !showResumeUpload && !showHistory && (
            <WelcomeScreen
              onStart={handleStartInterview}
              user={currentUser}
              onViewHistory={handleViewHistoryFromWelcome}  // optional: add history button to welcome
            />
          )}

          {showResumeUpload && (
            <ResumeUpload
              onResumeUploaded={handleResumeUploaded}
              onSkip={handleSkipResume}
            />
          )}

          {/* Interview — stays mounted even when history is open (so feedback screen is preserved) */}
          {showInterview && !showHistory && (
            <Interview
              resumeData={resumeData}
              onBack={handleBackToWelcome}
              onViewHistory={handleViewHistoryFromInterview}
            />
          )}

          {/* History — shown on top, back button goes to correct page */}
          {showHistory && (
            <SessionHistory
              onBack={handleHistoryBack}
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