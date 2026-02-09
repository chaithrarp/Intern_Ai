import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './UserMenu.css';

function UserMenu({ user, onLogout }) {
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to logout?')) {
      setIsOpen(false); // Close menu immediately
      await onLogout(); // Wait for logout to complete
    }
  };

  return (
    <div className="user-menu-container">
      <motion.button
        className="user-menu-button"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="user-avatar">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <span className="user-name">{user.username}</span>
        <motion.span 
          className="dropdown-arrow"
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          ▼
        </motion.span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="user-menu-dropdown"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <div className="user-info">
              <div className="user-avatar-large">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="user-details">
                <p className="user-username">{user.username}</p>
                <p className="user-email">{user.email}</p>
              </div>
            </div>

            <div className="menu-divider"></div>

            <motion.button
              className="logout-button"
              onClick={handleLogout}
              whileHover={{ backgroundColor: 'rgba(239, 68, 68, 0.2)' }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="logout-icon">🚪</span>
              Logout
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="menu-backdrop"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}

export default UserMenu;