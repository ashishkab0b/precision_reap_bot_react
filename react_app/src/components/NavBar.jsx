// react_app/src/components/NavBar.jsx
import React from "react";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { Link } from "react-router-dom";
import { useDonationDialog } from "../contexts/DonationDialogContext";
import api from "../api/axios";


function NavBar({ isAuthenticated, setAuthenticated }) {
  // This function can handle logging out (e.g., clearing session/cookies)
  const handleLogout = () => {
    // Call the logout API
    api.post("/auth/logout");
    setAuthenticated(false);
  };

  const { openDonationDialog } = useDonationDialog();
  const handleOpenDonation = () => {
    openDonationDialog();
  };

  return (
    <AppBar position="static">
      <Toolbar>
        {/* Logo / Name on the left */}
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          <Link
            to="/"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            Reappraise.it
          </Link>
        </Typography>

        {/* Right side menu items */}
        {isAuthenticated && (
          <Button component={Link} to="/chat" color="inherit">
            Chat
          </Button>
        )}
        <Button component={Link} to="/help" color="inherit">
          What is this app?
        </Button>
        <Button color="inherit" onClick={handleOpenDonation}>
            Donate
        </Button>

        {isAuthenticated ? (
          <Button onClick={handleLogout} color="inherit">
            Logout
          </Button>
        ) : (
          <>
            {/* <Button component={Link} to="/login" color="inherit">
              Login
            </Button>
            <Button component={Link} to="/register" color="inherit">
              Register
            </Button> */}
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}

export default NavBar;