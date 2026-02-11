import React, { useState, useEffect } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import ResumeUpload from './components/ResumeUpload';
import Interview from './Interview';
import Login from './components/Login';
import Register from './components/Register';
import SoundToggle from './components/SoundToggle';
import UserMenu from './components/UserMenu';
import './App.css';

function App() {
  const [showInterview, setShowInterview] = useState(false);
  const [showResumeUpload, setShowResumeUpload] = useState(false);
  const [resumeData, setResumeData] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authView, setAuthView] = useState('login'); // 'login' or 'register'
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in (on app load)
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');

      if (token && savedUser) {
        try {
          // Verify token is still valid
          const response = await fetch('http://localhost:8000/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const userData = await response.json();
            setCurrentUser(userData);
            setIsAuthenticated(true);
          } else {
            // Token is invalid, clear storage
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
      // Call logout endpoint to validate session end
      if (token) {
        const response = await fetch('http://localhost:8000/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          console.warn('Logout endpoint returned status:', response.status);
        }
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local storage regardless of endpoint response
      localStorage.removeItem('token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('user');

      // Reset state
      setIsAuthenticated(false);
      setCurrentUser(null);
      setShowInterview(false);
      setShowResumeUpload(false);
      setResumeData(null);
    }
  };

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

  const handleBackToWelcome = () => {
    setShowInterview(false);
    setShowResumeUpload(false);
    setResumeData(null);
  };

  // Loading screen
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
      {/* Authentication Views */}
      {!isAuthenticated && (
        <>
          {authView === 'login' ? (
            <Login 
              onLoginSuccess={handleLoginSuccess}
              onSwitchToRegister={() => setAuthView('register')}
            />
          ) : (
            <Register 
              onRegisterSuccess={handleRegisterSuccess}
              onSwitchToLogin={() => setAuthView('login')}
            />
          )}
        </>
      )}

      {/* Main Application (After Login) */}
      {isAuthenticated && (
        <>
          {/* User Menu (Top Right) */}
          <UserMenu 
            user={currentUser}
            onLogout={handleLogout}
          />

          {/* Show Welcome, Resume Upload, or Interview */}
          {!showInterview && !showResumeUpload && (
            <WelcomeScreen 
              onStart={handleStartInterview}
              user={currentUser}
            />
          )}
          
          {showResumeUpload && (
            <ResumeUpload 
              onResumeUploaded={handleResumeUploaded}
              onSkip={handleSkipResume}
            />
          )}
          
          {showInterview && (
            <Interview 
              resumeData={resumeData}
              onBack={handleBackToWelcome}
            />
          )}

          {/* Sound Toggle */}
          <SoundToggle />
        </>
      )}
    </div>
  );
}

export default App;