import React from "react";
import { ListItem, ListItemText } from "@mui/material";

const MessageItem = ({ message }) => {
  const isBot = message.role === "assistant";

  return (
    <ListItem
      sx={{
        justifyContent: isBot ? "flex-start" : "flex-end",
      }}
    >
      {isBot ? (
        <ListItemText
          primary={
            <div
              dangerouslySetInnerHTML={{ __html: message.content }}
            />
          }
          sx={{
            bgcolor: (theme) =>
              theme.palette.chatbot.botBg,
            color: (theme) =>
              theme.palette.chatbot.botText,
            borderRadius: (theme) => theme.shape.borderRadius,
            px: 3,
            py: 1,
          }}
        />
      ) : (
        <ListItemText
          primary={message.content}
          sx={{
            bgcolor: (theme) =>
              theme.palette.chatbot.userBg,
            color: (theme) =>
              theme.palette.chatbot.userText,
            borderRadius: (theme) => theme.shape.borderRadius,
            px: 3,
            py: 1,
          }}
        />
      )}
    </ListItem>
  );
};

export default MessageItem;