import React, { useEffect, useRef } from "react";
import MessageItem from "./MessageItem";
import { List } from "@mui/material";

const MessageList = ({ messages }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom each time messages change
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <List>
      {messages
        .filter((message) => {
          console.log("message", message);
          // Ensure message and content are valid
          if (!message || typeof message.content === "undefined" || message.content === null) {
            return false;
          }

          // Convert content to string and check if it's non-empty after trimming
          const content = String(message.content).trim();
          return content.length > 0;
        })
        .map((message) => (
          <MessageItem key={message.msgId || Date.now()} message={message} />
        ))}
      {/* This div will be our anchor to scroll to. */}
      <div ref={bottomRef} />
    </List>
  );
};

export default MessageList;