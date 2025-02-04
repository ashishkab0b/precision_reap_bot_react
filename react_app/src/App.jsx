// react_app/src/App.jsx

import React, { useState, useEffect } from "react";
import { ThemeProvider } from "@mui/material/styles";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import theme from "./theme";
import Chatbot from "./pages/Chatbot";


function App() {

  // const [loading, setLoading] = useState(true);

  // if (loading) {
  //   return <div>Loading...</div>;  // Prevents premature rendering
  // }
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Chatbot />} />
          {/* Redirect unknown routes */}
          <Route path="*" element={<Chatbot />} />
          </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;