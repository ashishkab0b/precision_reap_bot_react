// react_app/src/App.jsx

import React, { useState, useEffect } from "react";
import { ThemeProvider } from "@mui/material/styles";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navigate } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import theme from "./theme";

import NavBar from "./components/NavBar";
import api from "./api/axios";
import Chatbot from "./pages/Chatbot";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Auth from "./pages/Auth";
import Help from "./pages/Help";
import PrivateRoute from "./components/PrivateRoute";
import { DonationDialogProvider } from "./contexts/DonationDialogContext";

function App() {

  const [isAuthenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.get('/auth/current_user');
        if (response.status === 200) {
          setAuthenticated(true);
        }
      } catch (error) {
        setAuthenticated(false);
      } finally {
        setLoading(false);  // ✅ Mark as loaded
      }
    };
    checkAuth();
  }, []);

  if (loading) {
    return <div>Loading...</div>;  // ✅ Prevents premature rendering
  }
  
  return (
    <DonationDialogProvider>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
      {/* Pass down isAuthenticated (and a setter if needed) */}
        <NavBar isAuthenticated={isAuthenticated} setAuthenticated={setAuthenticated} />
        
        <Routes>
          <Route path="/" element={<Auth isAuthenticated={isAuthenticated} setAuthenticated={setAuthenticated} />} />
          {/* <Route 
            path="/login" 
            element={<Login 
              isAuthenticated={isAuthenticated} 
              setAuthenticated={setAuthenticated} 
            />} 
          />
          <Route path="/register" element={<Register />} /> */}
          <Route path="/help" element={<Help />} />
          
          {/* Protected Routes */}
          <Route element={<PrivateRoute isAuthenticated={isAuthenticated} />}>
            <Route path="/chat" element={<Chatbot />} />
          </Route>
          
          {/* Redirect unknown routes */}
          <Route
            path="*"
            element={
              isAuthenticated ? (
                <Navigate to="/chat" replace />
              ) : (
                <Navigate to="/" replace />
                )}/>
          
          
          </Routes>
      </Router>
    </ThemeProvider>
    </DonationDialogProvider>
  );
}

export default App;