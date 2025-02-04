// src/components/ChatProgress.jsx

import React from "react";
import { Stepper, Step, StepLabel } from "@mui/material";

const steps = [
  "Issue Interview",
  "Rate Issue",
  "Rate Values",
  "Rank Reframings",
  "Rate Reframings",
  "Complete",
];

  const stateToStepIndex = {
    issue_interview: 0,
    rate_issue: 1,
    rate_values: 2,
    rank_reaps: 3,
    rate_reaps: 4,
    complete: 5,
  };

export default function ChatProgress({ currentState }) {
  // If currentState is not in the map, fallback to 0 or -1.
  const activeStep = stateToStepIndex[currentState] ?? 0;

  return (
    <Stepper activeStep={activeStep} alternativeLabel>
      {steps.map((label, index) => (
        <Step key={label}>
          <StepLabel>{label}</StepLabel>
        </Step>
      ))}
    </Stepper>
  );
}