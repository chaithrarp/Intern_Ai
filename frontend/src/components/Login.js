import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './Auth.css';

function Login({ onLoginSuccess, onSwitchToRegister }) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Save token to localStorage
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('token_type', data.token_type);
        
        // Fetch user info
        const userResponse = await fetch('http://localhost:8000/auth/me', {
          headers: {
            'Authorization': `Bearer ${data.access_token}`,
          },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          localStorage.setItem('user', JSON.stringify(userData));
          onLoginSuccess(userData);
        }
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Failed to connect to server. Is the backend running?');
      console.error('Login error:', err);
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
          Welcome Back
        </motion.h2>

        <motion.p 
          className="auth-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          Sign in to continue your interview training
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

        {/* Login Form */}
        <motion.form 
          className="auth-form"
          onSubmit={handleSubmit}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <div className="form-group">
            <label htmlFor="username">Username or Email</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Enter your username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
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
                Signing in...
                <span className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </span>
              </span>
            ) : (
              'Sign In'
            )}
          </motion.button>
        </motion.form>

        {/* Switch to Register */}
        <motion.div 
          className="auth-switch"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <p>
            Don't have an account?{' '}
            <button 
              onClick={onSwitchToRegister}
              className="switch-button"
            >
              Create one
            </button>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}

export default Login;