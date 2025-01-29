// react_app/src/pages/Chatbot.jsx

import React, { useState, useEffect } from "react";
import { Box, Typography, Button } from "@mui/material";
import ConvoNav from "../components/ConvoNav";
import MessageList from "../components/MessageList";
import ResponseFactory from "../components/ResponseFactory";
import ChatProgress from "../components/ChatProgress";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";
import UserProfileDialog from "../components/UserProfileDialog";
import { useLocation, useNavigate } from "react-router-dom";

const Chatbot = () => {
  const [refreshConvoNav, setRefreshConvoNav] = useState(false);
  const [selectedConvoId, setSelectedConvoId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConvoState, setSelectedConvoState] = useState([]);
  
  // Check if the user is coming from the Help page with request to start a new chat
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    if (location.state?.newChat) {
      handleNewChat();
      navigate("/chat", { replace: true });  // Clear the state
    }
  }, [location.state]);


  // Bring in user info and helper from AuthContext
  const { user, isAuthenticated, isProfileComplete, refreshUser } = useAuth();
  
  // For controlling whether we show the user info form
  const [showUserInfoDialog, setShowUserInfoDialog] = useState(false);


  // Warn before leaving the page if a conversation is in progress
  useEffect(() => {
    const handleBeforeUnload = (event) => {
      if (selectedConvoId && selectedConvoState.some((state) => !state.completed)) {
        event.preventDefault();
        event.returnValue =
          "You have an active conversation. Are you sure you want to leave?";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [selectedConvoId, selectedConvoState]);

  // ---------------------------------------
  // 1. Function to fetch messages by convo
  // ---------------------------------------
  const fetchMessages = async (convoId) => {
    try {
      const response = await api.get("/chat/get_messages", {
        params: { conversation_id: convoId },
      });
      if (response.status === 200) {
        const fetchedMessages = response.data.map((msg) => ({
          msg_id: msg.msg_id,
          convo_id: msg.convo_id,
          content: msg.content,
          role: msg.role,
          responseType: msg.response_type,
          options: msg.options,
        }));
        setMessages(fetchedMessages);
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const fetchConversation = async (convoId) => {
    try {
      const response = await api.get("/chat/get_conversation", {
        params: { conversation_id: convoId },
      });
      if (response.status === 200) {
        const fetchedConvo = {
          convo_id: response.data.convo_id,
          user_id: response.data.user_id,
          state: response.data.state,
          label: response.data.oneline_summary,
          ephemeral: response.data.ephemeral,
          last_active_at: response.data.last_active_at,
        };
        setSelectedConvoState(fetchedConvo.state);
        console.log("fetchedConvo", fetchedConvo);
      }
    } catch (error) {
      console.error("Error fetching conversation:", error);
    }
  };

  // ---------------------------------------
  // 2. Handler to set selected conversation
  // ---------------------------------------
  const handleConvoSelect = (convoId) => {
    setSelectedConvoId(convoId);
    fetchMessages(convoId);
    fetchConversation(convoId);
  };

  // The last assistant message determines the next input type
  const lastBotMessage = messages
    .slice()
    .reverse()
    .find((msg) => msg.role === "assistant");

  // ---------------------------------------
  // 2a. Actually create a new conversation
  // ---------------------------------------
  const createNewConversation = async () => {
    try {
      const response = await api.post("/chat/new_chat");
      if (response.status === 200 && response.data.convo_id) {
        const newConvoId = response.data.convo_id;
        handleConvoSelect(newConvoId); // Immediately select the new chat
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };

  // Called when user clicks "Start a New Chat"
  // If the user profile is incomplete, show the info dialog first
  const handleNewChat = () => {
    if (!isProfileComplete) {
      setShowUserInfoDialog(true);
    } else {
      createNewConversation();
    }
  };

  // ---------------------------------------
  // 3. Handles user input
  // ---------------------------------------
  const handleUserResponse = async (
    content,
    responseType = "text",
    options = null,
  ) => {
    // Ensure a conversation is selected
    if (!selectedConvoId) {
      console.error("No conversation selected.");
      return;
    }

    // User message object
    const userMessage = {
      msg_id: Date.now(), // Temporary ID until server assigns one
      convo_id: selectedConvoId,
      convo_state: selectedConvoState,
      content: content,
      role: "user",
      responseType: responseType,
      options: options,
    };

    // Optimistically update UI with the user's message
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    // Start loading
    setIsLoading(true);

    try {
      // Send the message to the Flask endpoint
      const response = await api.post("/chat/send_message", {
        conversation_id: selectedConvoId,
        convo_state: selectedConvoState,
        content: content,
        response_type: responseType,
        options: options,
      });

      if ((response.status === 200 || response.status === 201) && response.data) {
        // Wrap the single bot object in an array
        const botMessages = [{
          msg_id: response.data.msg_id || Date.now() + Math.random(),
          role: "assistant",
          convo_id: response.data.convo_id,
          convo_state: response.data.convo_state,
          content: response.data.content,
          responseType: response.data.response_type,
          options: response.data.options,
        }];

        // Update the conversation state
        setSelectedConvoState(response.data.convo_state);

        // Append the bot's message
        setMessages((prevMessages) => [...prevMessages, ...botMessages]);

        if (botMessages.length + messages.length >= 3) {
          setRefreshConvoNav(true);
          setTimeout(() => setRefreshConvoNav(false), 500); // Reset after triggering refresh
        }
      }
    } catch (error) {
      console.error(`Error sending ${responseType} response:`, error);
    } finally {
      // Stop loading
      setIsLoading(false);
    }
  };

  // ---------------------------------------
  // 4. Handle user profile submission
  // ---------------------------------------
  const handleUserInfoSubmit = async (formData) => {
    try {
      // Send to the backend
      await api.post("/user/update_user", formData);
      // Refresh local user data
      await refreshUser();
      // Close the dialog
      setShowUserInfoDialog(false);
      // Now create the new conversation
      createNewConversation();
    } catch (err) {
      console.error("Error updating user profile:", err);
    }
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <ConvoNav onConvoSelect={handleConvoSelect} refreshConvoNav={refreshConvoNav} />

      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", p: 2 }}>
        {selectedConvoId ? ( // <-- Conditional rendering for selected chat
          <>
            {/* Render the progress at the top */}
            <ChatProgress currentState={selectedConvoState} />

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
                botMsgId={lastBotMessage.msg_id}
                onSubmit={(content) =>
                  handleUserResponse(
                    content,
                    lastBotMessage.responseType,
                    lastBotMessage.options
                  )
                }
              />
            )}
          </>
        ) : (
          // ---------------------------------------
          //  button when no chat is selected
          // ---------------------------------------
          <Box
            sx={{
              flex: 1,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Button
              variant="contained"
              onClick={handleNewChat}
              sx={{ fontSize: "1.2rem", padding: "1rem 2rem" }}
            >
              Start a New Chat
            </Button>
          </Box>
        )}
      </Box>

      {/* Popup for user profile if incomplete */}
      <UserProfileDialog
        open={showUserInfoDialog}
        onClose={() => setShowUserInfoDialog(false)}
        onSubmit={handleUserInfoSubmit}
        initialData={user} 
      />
    </Box>
  );
};

export default Chatbot;