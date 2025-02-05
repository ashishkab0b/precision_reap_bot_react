// SliderInput.jsx

import React, { useState, useEffect, useCallback } from "react";
import { Box, Slider, Button, Typography } from "@mui/material";
import Grid from "@mui/material/Grid";

const SliderInput = ({
  min = 0,
  max = 100,
  step = 1,
  defaultValue = null, // If null => no thumb visible initially
  labels = ["Not at all", "Slightly", "Moderately", "Very much", "Extremely"],
  questionId,
  onSubmit,
}) => {
  // Internal states
  const [sliderValue, setSliderValue] = useState(null);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);

  // On mount or when question changes, reset
  useEffect(() => {
    if (defaultValue !== null) {
      // If there's a real default, show it right away
      setSliderValue(defaultValue);
      setHasInteracted(true);
    } else {
      // Otherwise, start truly blank
      setSliderValue(null);
      setHasInteracted(false);
    }
    setIsDisabled(false);
  }, [questionId, defaultValue]);

  // Handle user movement of the slider
  const handleSliderChange = (_, newValue) => {
    // If disabled, ignore changes
    if (isDisabled) return;

    if (!hasInteracted) {
      setHasInteracted(true);
    }
    setSliderValue(newValue);
  };

  // Submission logic
  const handleSend = useCallback(() => {
    // If it's still null (no default + no interaction), do nothing
    if (sliderValue === null || isDisabled) {
      return;
    }
    // Disable after submission
    setIsDisabled(true);

    // Pass the selected value back up
    onSubmit(sliderValue, "slider", {
      min,
      max,
      step,
      defaultValue,
      questionId,
    });
  }, [sliderValue, isDisabled, onSubmit, min, max, step, defaultValue, questionId]);

  // Global key listener for Enter
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Enter") {
        handleSend();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSend]);

  return (
    <Box>
      <Grid container justifyContent="space-between" sx={{ mb: 2 }}>
        {labels.map((label, index) => (
          <Grid key={index}>
            <Typography variant="caption">{label}</Typography>
          </Grid>
        ))}
      </Grid>

      <Slider
        min={min}
        max={max}
        step={step}
        // Use min as a fallback for the controlled component,
        // but visually hide the thumb/track until user interacts or has a default value.
        value={sliderValue ?? min}
        onChange={handleSliderChange}
        valueLabelDisplay="auto"
        disabled={isDisabled}
        sx={{
          "& .MuiSlider-thumb": {
            visibility: sliderValue !== null || hasInteracted ? "visible" : "hidden",
          },
          "& .MuiSlider-track": {
            opacity: sliderValue !== null || hasInteracted ? 1 : 0,
          },
        }}
      />

      <Button
        variant="contained"
        onClick={handleSend}
        sx={{ mt: 2 }}
        disabled={(!hasInteracted && sliderValue === null) || isDisabled}
      >
        Submit
      </Button>
    </Box>
  );
};

export default SliderInput;