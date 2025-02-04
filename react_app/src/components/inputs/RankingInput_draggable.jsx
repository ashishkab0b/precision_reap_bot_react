// react_app/src/components/inputs/RankingInput.jsx

import React, { useState, useEffect } from "react";
import {
  Box,
  List,
  ListItem,
  ListItemText,
  Button,
  Typography,
  IconButton,
} from "@mui/material";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

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
 *      console.log("Final ranking:", ranking);
 *    }}
 *  />
 */
const RankingInput = ({ 
  items = [], 
  questionId, 
  onSubmit 
}) => {
  const [ranking, setRanking] = useState(items);
  const [isDisabled, setIsDisabled] = useState(false);

  // Reset ranking when question or items change
  useEffect(() => {
    setRanking(items);
    setIsDisabled(false);
  }, [items, questionId]);

  // Helper function to reorder the list after a drag
  const reorder = (list, startIndex, endIndex) => {
    const result = Array.from(list);
    const [removed] = result.splice(startIndex, 1);
    result.splice(endIndex, 0, removed);
    return result;
  };

  // Handle drag end event
  const onDragEnd = (result) => {
    if (!result.destination) {
      return;
    }
    const newRanking = reorder(ranking, result.source.index, result.destination.index);
    setRanking(newRanking);
  };

  // Handle submission of final order
  const handleSubmit = () => {
    setIsDisabled(true);
    onSubmit(ranking, "ranking", { questionId });
  };

  return (
    <Box>
      <Typography gutterBottom>
        Please rank the following items by dragging them into your preferred order:
      </Typography>

      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="rankingList">
          {(provided) => (
            <List
              ref={provided.innerRef}
              {...provided.droppableProps}
              sx={{ maxWidth: 800, backgroundColor: "#f9f9f9", borderRadius: 1, padding: 0 }}
            >
              {ranking.map((item, index) => (
                <Draggable
                  key={`${item}-${index}`} // ensure unique key if items might be duplicated
                  draggableId={`${item}-${index}`}
                  index={index}
                >
                  {(provided, snapshot) => (
                    <ListItem
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      sx={{
                        backgroundColor: snapshot.isDragging ? "#e0e0e0" : "inherit",
                        borderBottom: "1px solid #ddd",
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      {/* Drag Handle */}
                      <IconButton
                        {...provided.dragHandleProps}
                        sx={{ cursor: "grab", mr: 1 }}
                        disabled={isDisabled}
                      >
                        <DragIndicatorIcon />
                      </IconButton>
                      <ListItemText primary={item} />
                    </ListItem>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </List>
          )}
        </Droppable>
      </DragDropContext>

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