// react_app/src/pages/Login.jsx
import React, { useState, useEffect } from 'react';
import api, { getCsrfToken } from '../api/axios';
import { Link, useNavigate } from 'react-router-dom';

// Import Material UI components
import { 
  Container, 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Paper 
} from '@mui/material';

const Login = ({ isAuthenticated, setAuthenticated }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        getCsrfToken();
    }, []);

    useEffect(() => {
      if (isAuthenticated) {
        navigate('/chat');
      }
    }, [isAuthenticated, navigate]);

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await api.post('/auth/login', { email, password });
            setMessage(response.data.message);
    
            // Redirect to /chat after successful login
            if (response.status === 200) {
                setAuthenticated(true);
                navigate('/chat');
            }
        } catch (error) {
            setMessage(error.response?.data?.error || 'Login failed');
        }
    };

    return (
        <Container maxWidth="xs" sx={{ marginTop: 8 }}>
            <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                  Login
                </Typography>
                <Box 
                  component="form" 
                  onSubmit={handleLogin} 
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
                  <Button 
                    type="submit" 
                    variant="contained" 
                    color="primary" 
                    sx={{ mt: 2 }}
                  >
                    Login
                  </Button>
                </Box>
                {message && (
                  <Typography variant="body1" color="error" sx={{ mt: 2 }}>
                    {message}
                  </Typography>
                )}
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Don’t have an account? <Link to="/register">Create one</Link>
                </Typography>
            </Paper>
        </Container>
    );
};

export default Login;