import React, { useState, useEffect } from 'react';
import api, { getCsrfToken } from '../api/axios';
import { useNavigate } from 'react-router-dom';

import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper
} from '@mui/material';

const Auth = ({ isAuthenticated, setAuthenticated }) => {
  const navigate = useNavigate();

  const [step, setStep] = useState('email'); // 'email' | 'login' | 'register'
  const [isRegistered, setIsRegistered] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Make sure we have a CSRF token if needed
    getCsrfToken();
  }, []);

  useEffect(() => {
    // If user is already logged in, navigate away
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  // 1) Step to check if email is in DB
  const handleCheckEmail = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!email) return;

    try {
      const response = await api.post('/auth/check_email', { email });
      if (response.data.exists) {
        // Email is registered -> show login UI
        setIsRegistered(true);
        setStep('login');
      } else {
        // Email is NOT registered -> show register UI
        setIsRegistered(false);
        setStep('register');
      }
    } catch (error) {
      setMessage(error.response?.data?.error || 'Error checking email');
    }
  };

  // 2) Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await api.post('/auth/login', { email, password });
      if (response.status === 200) {
        setAuthenticated(true);
        navigate('/chat');
      }
    } catch (error) {
      setMessage(error.response?.data?.error || 'Login failed');
    }
  };

  // 3) Handle register
  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage('');

    if (password !== confirmPassword) {
      setMessage('Passwords do not match');
      return;
    }

    try {
      const response = await api.post('/auth/register', { email, password });
      if (response.status === 201) {
        // After register, you can decide to:
        // - auto-login the user 
        //   OR
        // - direct them to login 
        //   OR
        // - show them a success message
        // For example, let's just log them in for a seamless experience:
        await handleLogin(e); // re-use handleLogin, or do a fresh login call
      }
    } catch (error) {
      setMessage(error.response?.data?.error || 'Registration failed');
    }
  };

  return (
    <Container maxWidth="xs" sx={{ marginTop: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {step === 'email' && (
          <>
            <Typography variant="h4" component="h1" gutterBottom>
              Welcome
            </Typography>
            <Typography variant="body1" gutterBottom>
              Enter your email to continue
            </Typography>
            <Box
              component="form"
              onSubmit={handleCheckEmail}
              sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}
            >
              <TextField
                label="Email"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Button type="submit" variant="contained" color="primary">
                Continue
              </Button>
            </Box>
          </>
        )}

        {step === 'login' && (
          <>
            <Typography variant="h4" component="h1" gutterBottom>
              Login
            </Typography>
            <Box
              component="form"
              onSubmit={handleLogin}
              sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}
            >
              <TextField
                label="Email"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled // We've already captured email
              />
              <TextField
                label="Password"
                type="password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Button type="submit" variant="contained" color="primary">
                Login
              </Button>
              <Button 
                variant="text" 
                onClick={() => {
                  // in case user typed wrong email, allow them to go back
                  setStep('email'); 
                  setPassword('');
                }}
              >
                Go Back
              </Button>
            </Box>
          </>
        )}

        {step === 'register' && (
          <>
            <Typography variant="h4" component="h1" gutterBottom>
              Register
            </Typography>
            <Box
              component="form"
              onSubmit={handleRegister}
              sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}
            >
              <TextField
                label="Email"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled // We've already captured email
              />
              <TextField
                label="Password"
                type="password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <TextField
                label="Confirm Password"
                type="password"
                variant="outlined"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              <Button type="submit" variant="contained" color="primary">
                Register
              </Button>
              <Button 
                variant="text" 
                onClick={() => {
                  // go back if user messed up email
                  setStep('email');
                  setPassword('');
                  setConfirmPassword('');
                }}
              >
                Go Back
              </Button>
            </Box>
          </>
        )}

        {message && (
          <Typography variant="body1" color="error" sx={{ mt: 2 }}>
            {message}
          </Typography>
        )}
      </Paper>
    </Container>
  );
};

export default Auth;