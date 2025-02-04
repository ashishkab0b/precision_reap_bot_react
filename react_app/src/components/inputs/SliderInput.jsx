// SliderInput.jsx

import React, { useState, useEffect } from "react";
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

    // If the user moves the slider for the first time
    if (!hasInteracted) {
      setHasInteracted(true);
    }
    setSliderValue(newValue);
  };

  // Handle submission
  const handleSend = () => {
    // If still null (no default + no interaction), do nothing (or show error)
    if (sliderValue === null) {
      return; 
    }
    // Disable everything
    setIsDisabled(true);

    // Pass sliderValue back up
    onSubmit(sliderValue, "slider", {
      min,
      max,
      step,
      defaultValue,
      questionId,
    });
  };

  return (
    <Box>
      <Typography gutterBottom>
        Select a value between {min} and {max} by clicking and dragging along the slider below:
      </Typography>

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
        // If sliderValue is null, fallback to min just to satisfy controlled value,
        // but we hide the thumb/track visually (see sx) until interaction.
        value={sliderValue ?? min}
        onChange={handleSliderChange}
        valueLabelDisplay="auto"       // Bring back numeric labels on hover/drag
        disabled={isDisabled}          // Disable after submit
        sx={{
          // Hide the thumb if there's no defaultValue and user hasn't interacted
          "& .MuiSlider-thumb": {
            visibility:
              sliderValue !== null || hasInteracted
                ? "visible"
                : "hidden",
          },
          // Hide the filled track if there's no defaultValue and user hasn't interacted
          "& .MuiSlider-track": {
            opacity:
              sliderValue !== null || hasInteracted
                ? 1
                : 0,
          },
        }}
      />

      <Button
        variant="contained"
        onClick={handleSend}
        sx={{ mt: 2 }}
        // If there's no default and user hasn't moved slider, keep button disabled.
        disabled={(!hasInteracted && sliderValue === null) || isDisabled}
      >
        Submit
      </Button>
    </Box>
  );
};

export default SliderInput;