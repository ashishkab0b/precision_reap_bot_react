import React, { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  FormControl, 
  MenuItem, 
  Select, 
  InputLabel, 
  RadioGroup, 
  FormControlLabel, 
  Radio,
  TextField
} from '@mui/material';

/**
 * @param {boolean} open       - Whether the dialog is open
 * @param {function} onClose   - Called when user clicks "close" or outside
 * @param {function} onSubmit  - Called when user saves; pass formData back up
 */
export default function UserProfileDialog({ open, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    age: '',
    gender: '',
    research_consent: 'yes', // Default to "yes"
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = () => {
    if (formData.research_consent === '') {
      alert("You must select an option for research consent.");
      return;
    }
    // Pass formData upward
    onSubmit(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="user-profile-dialog">
      <DialogTitle id="user-profile-dialog">Research Consent</DialogTitle>
      <DialogContent>
        {/* Age Input */}
        <FormControl fullWidth margin="normal">
          <TextField
            label="Age"
            name="age"
            type="text"
            value={formData.age}
            onChange={handleChange}
            placeholder="Enter your age"
            inputProps={{
              inputMode: 'numeric', // Mobile-friendly numeric keyboard
              pattern: '[0-9]*', // Numeric input only
            }}
          />
        </FormControl>

        {/* Gender Dropdown */}
        <FormControl fullWidth margin="normal">
          <InputLabel id="gender-label">Gender</InputLabel>
          <Select
            labelId="gender-label"
            name="gender"
            value={formData.gender}
            onChange={handleChange}
          >
            <MenuItem value="">Select your gender</MenuItem>
            <MenuItem value="Female">Female</MenuItem>
            <MenuItem value="Male">Male</MenuItem>
            <MenuItem value="Non-binary/Other">Non-binary/Other</MenuItem>
          </Select>
        </FormControl>

        {/* Research Consent Radio Buttons */}
        <FormControl component="fieldset" margin="normal" fullWidth>
          <RadioGroup
            name="research_consent"
            value={formData.research_consent}
            onChange={handleChange}
          >
            <FormControlLabel
              value="yes"
              control={<Radio />}
              label="I consent to have my data anonymized and used for academic research."
            />
            <FormControlLabel
              value="no"
              control={<Radio />}
              label="I do not consent to have my data used for academic research."
            />
          </RadioGroup>
        </FormControl>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} color="secondary">
          Close
        </Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}