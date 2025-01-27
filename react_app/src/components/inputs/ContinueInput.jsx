import React from "react";
import { Box, Button } from "@mui/material";
import { useState } from "react";

const ContinueInput = ({ onSubmit }) => {

  const [isDisabled, setIsDisabled] = useState(false); 

  const handleContinue = () => {
    onSubmit(null, null, null);
    setIsDisabled(true);
  };

  return (
    <Box sx={{ display: "flex", justifyContent: "center" }}>
      <Button 
      variant="contained" 
      onClick={handleContinue}
      disabled={isDisabled}
      >
        Continue
      </Button>
    </Box>
  );
};

export default ContinueInput;