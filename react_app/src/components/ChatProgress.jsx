// src/components/ChatProgress.jsx

import React from "react";
import { Stepper, Step, StepLabel } from "@mui/material";

const steps = [
  "Issue Interview",
  "Rate Issue",
  "Generate Reappraisal",
  "Rate Reappraisal #1",
  "Refine Reappraisal",
  "Rate Reappraisal #2",
  "Complete",
];

  const stateToStepIndex = {
    issue_interview: 0,
    rate_issue: 1,
    generate_reap: 2,
    rate_reap_1: 3,
    refine_reap: 4,
    rate_reap_2: 5,
    complete: 6,
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