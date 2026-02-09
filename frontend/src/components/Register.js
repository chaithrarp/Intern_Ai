import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './Auth.css';

function Register({ onRegisterSuccess, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name || null
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        
        // Automatically log in after successful registration
        setTimeout(async () => {
          try {
            const loginResponse = await fetch('http://localhost:8000/auth/login', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                username: formData.username,
                password: formData.password
              }),
            });

            const loginData = await loginResponse.json();

            if (loginResponse.ok) {
              localStorage.setItem('token', loginData.access_token);
              localStorage.setItem('token_type', loginData.token_type);
              
              const userResponse = await fetch('http://localhost:8000/auth/me', {
                headers: {
                  'Authorization': `Bearer ${loginData.access_token}`,
                },
              });

              if (userResponse.ok) {
                const userData = await userResponse.json();
                localStorage.setItem('user', JSON.stringify(userData));
                onRegisterSuccess(userData);
              }
            }
          } catch (err) {
            console.error('Auto-login error:', err);
            onSwitchToLogin();
          }
        }, 1500);
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Failed to connect to server. Is the backend running?');
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-background"></div>
        <div className="glow-orbs"></div>
        
        <motion.div 
          className="auth-card success-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <motion.div 
            className="success-icon"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            ✓
          </motion.div>
          <h2>Account Created!</h2>
          <p>Welcome to InternAI. Logging you in...</p>
          <div className="loading-dots">
            <span>●</span><span>●</span><span>●</span>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-background"></div>
      <div className="glow-orbs"></div>

      <motion.div 
        className="auth-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Logo */}
        <motion.div 
          className="auth-logo"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <h1 className="logo-text">
            <span className="logo-word">Intern</span>
            <span className="logo-word accent">AI</span>
          </h1>
        </motion.div>

        {/* Title */}
        <motion.h2 
          className="auth-title"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          Create Account
        </motion.h2>

        <motion.p 
          className="auth-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          Start your interview training journey
        </motion.p>

        {/* Error Message */}
        {error && (
          <motion.div 
            className="error-message"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            ⚠️ {error}
          </motion.div>
        )}

        {/* Registration Form */}
        <motion.form 
          className="auth-form"
          onSubmit={handleSubmit}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <div className="form-group">
            <label htmlFor="username">Username *</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Choose a username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="your.email@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="full_name">Full Name (Optional)</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="John Doe"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="At least 6 characters"
              minLength={6}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password *</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              placeholder="Re-enter your password"
            />
          </div>

          <motion.button 
            type="submit" 
            className="auth-button"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? (
              <span className="loading-text">
                Creating account...
                <span className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </span>
              </span>
            ) : (
              'Create Account'
            )}
          </motion.button>
        </motion.form>

        {/* Switch to Login */}
        <motion.div 
          className="auth-switch"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <p>
            Already have an account?{' '}
            <button 
              onClick={onSwitchToLogin}
              className="switch-button"
            >
              Sign in
            </button>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}

export default Register;