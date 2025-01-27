import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { getCsrfToken } from '../api/axios';  // Import the Axios instance

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);  // Prevent flickering

  // Helper function to check if user profile is complete
  function isProfileComplete(userData) {
    if (!userData) return false;
    return (
      userData.age !== null &&
      userData.gender !== null &&
      userData.research_consent !== null
    );
  }

  // Fetch current user from Flask backend
  const getUserInfo = async () => {
    try {
      const response = await api.get('/user/get_user_data');
      return response.data;
    } catch (error) {
      return null;
    }
  };

  // Public method to refresh user info
  const refreshUser = async () => {
    await getCsrfToken();  // Ensure CSRF token is set for secure requests
    const userData = await getUserInfo();
    setUser(userData);
  };

  // Fetch user data on component mount
  useEffect(() => {
    const fetchUser = async () => {
      await refreshUser();
      setLoading(false);
    };
    fetchUser();
  }, []);

  // Handle login
  const login = async (username, password) => {
    try {
      await getCsrfToken();
      const response = await api.post('/auth/login', { username, password });
      // After login, refresh user data
      await refreshUser();
      return { success: true, message: response.data.message };
    } catch (error) {
      return { success: false, message: error.response?.data?.error || 'Login failed' };
    }
  };

  // Handle logout
  const logout = async () => {
    try {
      await api.post('/auth/logout');
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isProfileComplete: isProfileComplete(user),
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}