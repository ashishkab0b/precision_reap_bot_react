// theme.jsx

import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#475693", // Dark blue
    },
    secondary: {
      main: "#FF6B35", // A bright accent color
    },
    background: {
      default: "#F3F2FC", // Subtle background
      paper: "#FFFFFF",
    },
    text: {
      primary: "#1E1E1E", 
      secondary: "#475693",
    },
    chatbot: {
      botBg: "#E4E2FF",
      botText: "#1E1E1E",
      userBg: "#475693",
      userText: "#FFFFFF",
    },
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: "'Open Sans', sans-serif",
    h4: {
      fontWeight: 700,
      letterSpacing: "0.03em",
    },
    body1: {
      fontSize: "1rem",
      lineHeight: 1.6,
    },
  },
  components: {
    // Example overrides
    MuiListItemText: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "8px 12px",
          margin: "4px 0",
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          marginBottom: "1rem", // Spacing under each TextField
        },
      },
    },
  },
});

export default theme;