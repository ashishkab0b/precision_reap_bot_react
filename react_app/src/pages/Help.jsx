// react_app/src/pages/Help.jsx
import React from "react";
import { Container, Typography, Box } from "@mui/material";

function Help() {
  return (
    <Container maxWidth="md" sx={{ mt: 4, backgroundColor: "background.paper", p: 4, borderRadius: 2, boxShadow: 3 }}>
      <Box>
        <Typography variant="h4" gutterBottom sx={{ color: "text.primary" }}>
          Welcome to Reappraise.it: A Free Cognitive Reappraisal AI Helper
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Negative emotions can be incredibly useful—they serve as signals, letting us know what’s going wrong or right in our world and highlighting the things we truly care about. They can motivate us to take action, solve problems, and protect what matters most. But sometimes, negative emotions stick around longer than they need to or get in the way of our goals. In those moments, we have the power to take steps to change how we feel.
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          One particularly adaptive way to change our emotions is called <strong>cognitive reappraisal</strong>. Decades of research have shown that reappraisal—i.e., rethinking a situation to view it from a different, more helpful perspective—can help to transform people's emotional experience for the better and achieve greater well-being. It’s not about ignoring problems or denying reality; it’s about finding new ways to view challenges that reduce distress and help us respond in healthier, more constructive ways.
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Research has found that people who use reappraisal more often tend to enjoy:
        </Typography>
        <ul>
          <li><Typography variant="body1">Better psychological well-being.</Typography></li>
          <li><Typography variant="body1">Improved physical health.</Typography></li>
          <li><Typography variant="body1">Stronger relationships.</Typography></li>
          <li><Typography variant="body1">Better cognitive functioning.</Typography></li>
          <li><Typography variant="body1">The list goes on...</Typography></li>
        </ul>
        <Typography variant="body1" sx={{ mb: 2 }}>
          In my own research, I’ve seen firsthand how powerful reappraisal can be. I’ve conducted many studies where participants were guided to reappraise their challenges and the feedback has been overwhelmingly positive. People often share how this simple yet powerful tool helped them see their problems in a new light and feel better equipped to handle them.
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          The positive feedback in my own research from participants inspired me to make this process accessible to everyone. Whether you’re navigating a tough situation, feeling stuck, or just looking for a way to better manage your emotions, this tool is here to guide you through rethinking and reframing your perspective.
        </Typography>
      </Box>
    </Container>
  );
}

export default Help;