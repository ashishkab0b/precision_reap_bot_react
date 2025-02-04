// react_app/src/components/inputs/RankingInput.jsx

import React, { useState, useEffect } from "react";
import {
  Box,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
  Typography,
} from "@mui/material";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";

/**
 * @param {object} props
 * @param {string[]} props.items - The list of text blocks to rank.
 * @param {string|number} props.questionId - Identifier to reset state when question changes.
 * @param {function} props.onSubmit - Callback to pass the final ranking up. 
 *        Receives two args: (rankingArray, "ranking") plus extra optional metadata.
 * 
 * Usage:
 *  <RankingInput
 *    items={["Option A", "Option B", "Option C"]}
 *    questionId="q1"
 *    onSubmit={(ranking, inputType, metadata) => {
 *      console.log("Final ranking:", ranking); // Example output: [2, 0, 1]
 *    }}
 *  />
 */
const RankingInput = ({ 
  items = [], 
  questionId, 
  onSubmit 
}) => {
  // The ranking state is now an array of indices corresponding to the items.
  const [ranking, setRanking] = useState(() => items.map((_, i) => i));
  const [isDisabled, setIsDisabled] = useState(false);

  // Reset ranking when question or items change.
  useEffect(() => {
    setRanking(items.map((_, i) => i));
    setIsDisabled(false);
  }, [items, questionId]);

  // Move the index at position 'index' up by 1.
  const moveItemUp = (index) => {
    if (index === 0 || isDisabled) return; // Can't move the first item up.
    const newRanking = [...ranking];
    [newRanking[index - 1], newRanking[index]] = [newRanking[index], newRanking[index - 1]];
    setRanking(newRanking);
  };

  // Move the index at position 'index' down by 1.
  const moveItemDown = (index) => {
    if (index === ranking.length - 1 || isDisabled) return; // Can't move the last item down.
    const newRanking = [...ranking];
    [newRanking[index + 1], newRanking[index]] = [newRanking[index], newRanking[index + 1]];
    setRanking(newRanking);
  };

  // Handle submission of the final order.
  const handleSubmit = () => {
    setIsDisabled(true);
    // The submitted ranking is now an array of indices.
    onSubmit(ranking, "ranking", { questionId });
  };

  return (
    <Box
      sx={{
        // Center only the ranking input content.
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        p: 2,
      }}
    >
      <Typography variant="body1" gutterBottom>
        Please rank the following reframings by clicking the arrows on the right side.
        Please place the most preferred option at the top and the least preferred at the bottom.
      </Typography>

      <List
        sx={{
          width: "100%",
          maxWidth: 800,
          backgroundColor: "#f9f9f9",
          borderRadius: 1,
          boxShadow: 1,
        }}
      >
        {ranking.map((itemIndex, position) => (
          <ListItem
            key={itemIndex}
            sx={{
              border: "1px solid #ccc", // Border around each item.
              mb: 1,
              borderRadius: 1,
            }}
            secondaryAction={
              <Box sx={{ display: "flex", flexDirection: "column" }}>
                <IconButton
                  size="small"
                  onClick={() => moveItemUp(position)}
                  disabled={isDisabled}
                >
                  <KeyboardArrowUpIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => moveItemDown(position)}
                  disabled={isDisabled}
                >
                  <KeyboardArrowDownIcon />
                </IconButton>
              </Box>
            }
          >
            <ListItemText primary={items[itemIndex]} />
          </ListItem>
        ))}
      </List>

      <Button 
        variant="contained" 
        onClick={handleSubmit} 
        sx={{ mt: 2 }}
        disabled={isDisabled}
      >
        Submit Ranking
      </Button>
    </Box>
  );
};

export default RankingInput;