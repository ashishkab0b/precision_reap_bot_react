import React, { useState, useEffect, useRef } from "react";
import { Box, TextField, Button } from "@mui/material";

const TextInput = ({ onSubmit, botMsgId }) => {
  const [value, setValue] = useState("");
  const [isDisabled, setIsDisabled] = useState(false); // State to disable input
  const inputRef = useRef(null); // Ref for the input field

  // Ensure that the input is enabled and cleared when the bot message changes
  useEffect(() => {
    setValue("");
    setIsDisabled(false);

    // Focus on the input field after a short delay (short delay is a hack to fix a bug where it wasn't focusing on input)
    const timer = setTimeout(() => {
      inputRef.current?.focus();
    }, 50);

    return () => clearTimeout(timer);
  }, [botMsgId]);

  const handleSend = () => {
    if (value.trim() !== "") {
      onSubmit(value, "text", {});
      setValue("");
      setIsDisabled(true); // Disable input after submission
    }
  };  
  
  // Listen for Enter key
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();  // Prevents form submission if inside a form
      handleSend();
    }
  };

  return (
    <Box sx={{ display: "flex", gap: 1 }}>
      <TextField
        inputRef={inputRef}
        variant="outlined"
        fullWidth
        size="small"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type your message"
        onKeyDown={handleKeyDown}
        disabled={isDisabled} // Disable TextField when isDisabled is true
        autoFocus  // does this mean i can get rid of all the logic earlier??
      />
      <Button 
      variant="contained" 
      onClick={handleSend}
      disabled={isDisabled}
      >
        Send
      </Button>
    </Box>
  );
};

export default TextInput;