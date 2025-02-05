// react_app/src/pages/Chatbot.jsx

import React, { useRef, useState, useEffect } from "react";
import { Box, Typography } from "@mui/material";
import MessageList from "../components/MessageList";
import ResponseFactory from "../components/ResponseFactory";
import ChatProgress from "../components/ChatProgress";
import api from "../api/axios";
import { useSearchParams } from "react-router-dom";


const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [convoState, setConvoState] = useState([]);
  const [convoId, setConvoId] = useState(null);
  const [error, setError] = useState(null);
  const hasAttemptedStart = useRef(false); // Track if we already tried starting a conversation

  const [searchParams, setSearchParams] = useSearchParams();
  const pidParam = searchParams.get("pid");
  const codeParam = searchParams.get("code");

  //
  // ---------------------------------------
  // Conversation management
  // ---------------------------------------
  //

  // Function to start a new conversation
  const startNewConversation = async (pid) => {
    if (hasAttemptedStart.current) return; // Prevent infinite retry loops
    hasAttemptedStart.current = true; // Mark as attempted
  
    try {
      const response = await api.post("/chat/new_chat", { pid: pid });
  
      if (response.status === 201) {
        setConvoId(response.data.convoId);
        setConvoState(response.data.state);
        setSearchParams({ pid: pidParam, code: response.data.code });
        setMessages(response.data.messages);
      }
    } catch (error) {
      console.error("Error starting new conversation:", error);
    }
  };

  const fetchConversation = async (pid, code) => {
    try {
        const response = await api.get("/chat/get_conversation", {
            params: { pid, code },
        });
        if (response.status === 200) {
          if (response.data.exists === true) {
            setConvoId(response.data.convoId);
            setConvoState(response.data.state);
            setMessages(response.data.messages);
          } else {
            await startNewConversation(pid);
          }
        }
    } catch (error) {
        console.error("Error fetching conversation:", error);
    }
};

  //
  // ---------------------------------------
  // Check PID and Code on initial render
  // ---------------------------------------
  //
  useEffect(() => {
    // 1) If there is no pid, show an error
    if (!pidParam) {
      setError("Error: No participant ID (pid) was provided in the URL. Please contact the researcher.");
      return;
    }

    // 2) If there is no code, start a new conversation
    if (!codeParam) {
      console.log('No code found, starting new conversation');
      startNewConversation(pidParam);
    } else {
      // 3) If there is a code, fetch existing conversation
      //    If it's invalid, startNewConversation will be called in catch
      fetchConversation(pidParam, codeParam);
    }
  }, [pidParam, codeParam]); // re-run if params change

  //
  // ---------------------------------------
  // Chat functionality
  // ---------------------------------------
  //

  // The last assistant message determines the next input type
  const lastBotMessage = messages
    .slice()
    .reverse()
    .find((msg) => msg.role === "assistant");

  const handleUserResponse = async (
    content,
    responseType = "text",
    options = null
  ) => {
    // Ensure a conversation is selected
    if (!convoId) {
      console.error("No conversation selected.");
      return;
    }

    // Build user message object
    const userMessage = {
      msgId: Date.now(), // Temporary ID until server assigns one
      convoId: convoId,
      convoState: convoState,
      content: content,
      role: "user",
      responseType: responseType,
      options: options,
    };

    // Optimistically update UI with the user's message
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setIsLoading(true);

    try {
      // Send the user message to the server
      const response = await api.post("/chat/send_message", {
        convoId: convoId,
        convoState: convoState,
        content: content,
        responseType: responseType,
        options: options,
      });

      if ((response.status === 200 || response.status === 201) && response.data) {
        // Construct the bot's message from the response
        const botMessages = [
          {
            msgId: response.data.msgId || Date.now() + Math.random(),
            role: "assistant",
            convoId: response.data.convoId,
            convoState: response.data.convoState,
            content: response.data.content,
            responseType: response.data.responseType,
            options: response.data.options,
          },
        ];

        // Update the conversation state
        setConvoState(response.data.convoState);

        // Append the bot's message
        setMessages((prevMessages) => [...prevMessages, ...botMessages]);
      }
    } catch (error) {
      console.error(`Error sending ${responseType} response:`, error);
    } finally {
      // Stop loading
      setIsLoading(false);
    }
  };

  //
  // ---------------------------------------
  // Rendering
  // ---------------------------------------
  //

  if (error) {
    // If there's an error (e.g. no pid), show it and don't render the chatbot
    return (
      <Box
        sx={{
          display: "flex",
          height: "100vh",
          alignItems: "center",
          justifyContent: "center",
          p: 2,
        }}
      >
        <Typography variant="h6" color="error">
          {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",       // Center the chat area horizontally
        alignItems: "stretch",
        width: "100%",
        height: "100vh",
        overflow: "hidden", // or "auto", if needed
      }}
    >
      {/* Outer container to cap max width */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          maxWidth: "900px",  // Adjust to your preference (could be 800px, 900px, etc.)
          p: 2,               // padding
        }}
      >
        {/* Render the progress at the top */}
        <ChatProgress currentState={convoState} />
  
        <Box
          sx={{
            border: (theme) => `1px solid ${theme.palette.divider}`,
            maxHeight: "calc(100% - 200px)",
            borderRadius: 1,
            p: 2,
            mb: 2,
            flex: 1,
            overflowY: "auto",
          }}
        >
          <MessageList messages={messages} />
        </Box>
  
        {isLoading && (
          <Typography variant="body2" sx={{ mb: 2 }}>
            Bot is thinking...
          </Typography>
        )}
  
        {lastBotMessage && (
          <ResponseFactory
            responseType={lastBotMessage.responseType}
            options={lastBotMessage.options}
            botMsgId={lastBotMessage.msgId}
            onSubmit={(content) =>
              handleUserResponse(
                content,
                lastBotMessage.responseType,
                lastBotMessage.options
              )
            }
          />
        )}
      </Box>
    </Box>
  );
};

export default Chatbot;