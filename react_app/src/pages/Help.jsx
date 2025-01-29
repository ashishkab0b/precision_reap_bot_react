// react_app/src/pages/Help.jsx

import React from "react";
import { Container, Typography, Box, Link, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

function Help() {

  const navigate = useNavigate();
  const handleStartChat = () => {
    navigate("/chat", { state: { newChat: true } });
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, backgroundColor: "background.paper", p: 4, borderRadius: 2, boxShadow: 3 }}>
      <Box>
        <Typography variant="h4" gutterBottom sx={{ color: "text.primary" }}>
          Welcome to Reappraise.it: A Free Cognitive Reappraisal AI Helper
        </Typography>

        <Typography variant="body1" sx={{ mb: 2 }}>
          This is a chatbot that guides you through the process of cognitive reappraisal, a powerful emotion regulation strategy that can help you feel better when you’re feeling down.
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Negative emotions can be incredibly useful—they serve as signals, letting us know what’s going wrong or right in our world and highlighting the things we truly care about. They can motivate us to take action, solve problems, and protect what matters most. But sometimes, negative emotions stick around longer than they need to or get in the way of our goals. <Box component="span" sx={{ fontStyle: 'italic', fontWeight: 'bold'}}>In those moments, we have the power to take steps to change how we feel.</Box>
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          One particularly adaptive way to change our emotions is called <strong>cognitive reappraisal</strong>. Decades of research have shown that reappraisal—i.e., rethinking a situation to view it from a different, more helpful perspective—can help to transform people's emotional experience and achieve greater well-being. It’s not about ignoring problems or denying reality; it’s about finding new ways to view challenges that reduce distress and help us respond in healthier, more constructive ways.
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ color: "text.primary" }}>
          Why Reappraise?
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Research has found that people who use reappraisal more often tend to enjoy:
        </Typography>
        
        <Typography variant="body1" component="div" sx={{ mb: 2 }}>
          <ul>
            <li>Better psychological well-being.</li>
            <li>Improved physical health.</li>
            <li>Stronger relationships.</li>
            <li>Better cognitive functioning.</li>
            <li>The list goes on...</li>
          </ul>
        </Typography>
        
        <Typography variant="h5" gutterBottom sx={{ color: "text.primary" }}>
          Should I ALWAYS reappraise when I feel bad?
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          This is a great question and understanding when someone should or should not use reappraisal is an active area of research with plenty more to learn. We do know that in general, increasing the frequency with which people reappraise tends to do good things for them. However, there are a few things to keep in mind.
          </Typography>
         
          <ul>
            <li>Negative emotions can be important signals that we need to address a problem in our environment. You do not want your reappraisal to prevent you from taking actions to make things better in your environment.</li>
            <li>Reappraisal can be hard and it can be taxing. (Though, like any skill, it gets easier with practice.) If you are feeling strong and overwhelming negative emotions, you may want to give yourself a bit of time and space before attempting to reappraise. You can think of it like this: reappraisal is an investment of upfront effort for long-term relief—but if you don't have the resources to give that upfront effort, it may be worth waiting until you do.</li>
            <li>
              <Box component="span" sx={{ fontWeight: 'bold' }}>
                Remember, there is nothing wrong with feeling negative emotions! It is only when negative emotions interfere with our valued goals that they should be regulated.
              </Box>
            </li>
          </ul>

          <Typography variant="body1" sx={{ mb: 2 }}>
          It’s important to use reappraisal in conjunction with other strategies and to be mindful of when it’s appropriate to use it.
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ color: "text.primary" }}>
          What is this app NOT for?
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          This app is NOT a substitute for professional mental health care from a human. If you are struggling with your mental health, please seek help from a mental health professional. This app is not designed to diagnose or treat any mental health condition. It is simply a tool to help you practice cognitive reappraisal, a skill that can be helpful for many people.
        </Typography>
        <Typography variant="h6" gutterBottom sx={{ color: "text.primary" }}>
          Crisis Resources
        </Typography>
        <Typography variant="body1" component="div" sx={{ mb: 2 }}>
          If you are in crisis or experiencing thoughts of harming yourself or others, this app is not the appropriate resource. Instead, here are some resources that can help:
          <ul>
            <li><Typography variant="body1"><Link href="https://www.crisistextline.org">Crisis Text Line</Link> – Free, 24/7 text-based support for people in crisis</Typography></li>
            <li><Typography variant="body1"><Link href="https://988lifeline.org">988 Suicide and Crisis Lifeline</Link> – Free, confidential support in the U.S. for people in distress</Typography></li>
            <li><Typography variant="body1"><Link href="https://befrienders.org">Befrienders Worldwide</Link> - Free, global support network for individuals in crisis</Typography></li>
          </ul>
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ color: "text.primary" }}>
          Who made this site and why?
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          I am a PhD student at Stanford studying reappraisal as the topic of my dissertation (<Link href="https://ashish.mehta.fyi/?s=prbr">website</Link>). In my own research, I’ve seen firsthand how powerful reappraisal can be. I’ve conducted many studies where participants were guided to reappraise their challenges. Even though the studies were designed to test particular research questions and not simply to help people feel better, I consistently received overwhelmingly positive feedback. People often shared how profoundly helpful the study was with something they had been really struggling with. The positive feedback from participants in my research projects inspired me to make this process accessible to everyone. 
        </Typography>
        <Typography variant="h5" gutterBottom sx={{ color: "text.primary" }}>
          How do I get started?
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Just click this button!
        </Typography>
        
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleStartChat}
        >
          Start Chat
        </Button>
      </Box>
    </Container>
  );
}

export default Help;