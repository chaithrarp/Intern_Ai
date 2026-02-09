/**
 * API Utility for Authenticated Requests
 * 
 * This file provides helper functions to make authenticated API calls
 * to the InternAI backend with automatic token handling.
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Get authentication headers
 * @returns {Object} Headers object with Authorization if token exists
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

/**
 * Make an authenticated GET request
 * @param {string} endpoint - API endpoint (e.g., '/users/sessions')
 * @returns {Promise<Object>} Response data
 */
export const apiGet = async (endpoint) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (response.status === 401) {
      // Token expired or invalid
      handleUnauthorized();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    console.error(`API GET ${endpoint} failed:`, error);
    throw error;
  }
};

/**
 * Make an authenticated POST request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body data
 * @returns {Promise<Object>} Response data
 */
export const apiPost = async (endpoint, data = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (response.status === 401) {
      handleUnauthorized();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    console.error(`API POST ${endpoint} failed:`, error);
    throw error;
  }
};

/**
 * Make an authenticated POST request with FormData (for file uploads)
 * @param {string} endpoint - API endpoint
 * @param {FormData} formData - FormData object
 * @returns {Promise<Object>} Response data
 */
export const apiPostFormData = async (endpoint, formData) => {
  try {
    const token = localStorage.getItem('token');
    const headers = {};

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Don't set Content-Type for FormData - browser will set it automatically

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: formData,
    });

    if (response.status === 401) {
      handleUnauthorized();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    console.error(`API POST FormData ${endpoint} failed:`, error);
    throw error;
  }
};

/**
 * Handle unauthorized access (401)
 * Clear tokens and redirect to login
 */
const handleUnauthorized = () => {
  console.warn('Session expired or unauthorized. Logging out...');
  
  // Clear authentication data
  localStorage.removeItem('token');
  localStorage.removeItem('token_type');
  localStorage.removeItem('user');

  // Reload the app (will show login screen)
  window.location.reload();
};

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

/**
 * Get current user from localStorage
 * @returns {Object|null} User object or null
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (error) {
      console.error('Failed to parse user data:', error);
      return null;
    }
  }
  return null;
};

/**
 * Logout user
 * Clear all authentication data
 */
export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('token_type');
  localStorage.removeItem('user');
  window.location.reload();
};

// Export API base URL for direct use
export { API_BASE_URL };

/**
 * USAGE EXAMPLES:
 * 
 * // Get user's sessions
 * const sessions = await apiGet('/users/sessions?limit=10');
 * 
 * // Start an interview
 * const interview = await apiPost('/interview/start-with-persona?persona=friendly_coach');
 * 
 * // Submit an answer
 * const result = await apiPost('/interview/answer?session_id=session_123', {
 *   question_id: 1,
 *   answer_text: 'My answer...',
 *   was_interrupted: false,
 *   recording_duration: 15.5
 * });
 * 
 * // Upload audio file
 * const formData = new FormData();
 * formData.append('audio_file', audioBlob, 'recording.webm');
 * const result = await apiPostFormData(
 *   '/interview/upload-audio?session_id=session_123&question_id=1',
 *   formData
 * );
 */