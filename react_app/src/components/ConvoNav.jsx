import React, { useState, useEffect } from "react";
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  Button,
  IconButton,
  Tooltip,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import api from "../api/axios";

const ConvoNav = ({ onConvoSelect, refreshConvoNav }) => {
  const [convos, setConvos] = useState([]);

  // Fetch conversations function
  const fetchConversations = async () => {
    try {
      const response = await api.get("/chat/get_conversations");
      if (response.status === 200) {
        setConvos(response.data);
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    }
  };

  // Fetch conversations initially
  useEffect(() => {
    fetchConversations();
  }, []);

  // Trigger refresh on `refreshConvoNav` change
  useEffect(() => {
    if (refreshConvoNav) {
      fetchConversations();
    }
  }, [refreshConvoNav]);

  const handleNewChat = async () => {
    try {
      const response = await api.post("/chat/new_chat");
      if (response.status === 200 && response.data.convo_id) {
        const newConvo = {
          id: response.data.convo_id,
          label: `Conversation ${response.data.convo_id}`,
        };
        setConvos((prev) => [newConvo, ...prev]);
        if (onConvoSelect) {
          onConvoSelect(newConvo.id);
        }
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };

  const handleConvoClick = (convoId) => {
    if (onConvoSelect) {
      onConvoSelect(convoId);
    }
  };

  const handleDeleteConvo = async (convoId) => {
    try {
      const response = await api.delete(`/chat/delete_conversation/${convoId}`);
      if (response.status === 200) {
        setConvos((prev) => prev.filter((convo) => convo.id !== convoId));
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };


  return (
    <Box
      sx={{
        width: { xs: "100%", sm: "250px" },
        borderRight: "1px solid #ccc",
        p: 1,
        flexShrink: 0,
        bgcolor: "#f9f9f9",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* New Chat Button */}
      <Box sx={{ mb: 2, textAlign: "center" }}>
        <Button variant="contained" onClick={handleNewChat}>
          New Chat
        </Button>
      </Box>

      {/* Scrollable List of Conversations */}
      <Box sx={{ flex: 1, overflowY: "auto" }}>
        <List>
          {convos.map((convo) => (
            <React.Fragment key={convo.id}>
              <ListItemButton
                onClick={() => handleConvoClick(convo.id)}
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  "&:hover .delete-icon": {
                    visibility: "visible", // Make the delete icon visible on hover
                  },
                }}
              >
                {/* Conversation Label */}
                <ListItemText primary={convo.label} />

                {/* Delete Icon */}
                <Tooltip title="Delete" arrow>
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent triggering the conversation click
                      handleDeleteConvo(convo.id);
                    }}
                    className="delete-icon" // Add a class for hover targeting
                    sx={{
                      visibility: "hidden", // Initially hidden
                      transition: "visibility 0.2s ease-in-out",
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </ListItemButton>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </Box>
    </Box>
  );
};

export default ConvoNav;