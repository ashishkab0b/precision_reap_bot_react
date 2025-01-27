// react_app/src/pages/Register.jsx
import React, { useState, useEffect } from 'react';
import api, { getCsrfToken } from '../api/axios';
import { Link, useNavigate } from 'react-router-dom';

import { 
  Container, 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Paper 
} from '@mui/material';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    
    const navigate = useNavigate();

    useEffect(() => {
        getCsrfToken();
    }, []);

    const handleRegister = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            setMessage('Passwords do not match');
            return;
        }
        try {
            const response = await api.post('/auth/register', { email, password });
            setMessage(response.data.message);
    
            // ✅ Redirect to /chat after successful registration
            if (response.status === 201) {
                // navigate('/login');
            }
        } catch (error) {
            setMessage(error.response?.data?.error || 'Registration failed');
        }
    };

    return (
        <Container maxWidth="xs" sx={{ marginTop: 8 }}>
            <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                  Register
                </Typography>
                <Box
                  component="form"
                  onSubmit={handleRegister}
                  sx={{ display: 'flex', flexDirection: 'column' }}
                >
                  <TextField
                    label="Email"
                    variant="outlined"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                  <TextField
                    label="Password"
                    variant="outlined"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <TextField
                    label="Confirm Password"
                    variant="outlined"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                  <Button 
                    type="submit" 
                    variant="contained" 
                    color="primary" 
                    sx={{ mt: 2 }}
                  >
                    Register
                  </Button>
                </Box>
                {message && (
                  <Typography variant="body1" color="error" sx={{ mt: 2 }}>
                    {message}
                  </Typography>
                )}
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Already have an account? <Link to="/login">Log in here</Link>
                </Typography>
            </Paper>
        </Container>
    );
};

export default Register;