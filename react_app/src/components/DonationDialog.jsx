import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
} from '@mui/material';

function DonationDialog({ open, onClose }) {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Thank you for using Reappraise.it!</DialogTitle>
            <DialogContent dividers>
                <Typography component="p">
                Hi! I’m a graduate student passionate about making mental health tools accessible and effective. 
                If you find this bot helpful and want to support its development, 
                feel free to leave a donation. 
                Every bit helps, but no pressure—I’m just glad you’re here! 🩵
                </Typography>

                <Box
                    mt={2}
                    display="flex"
                    justifyContent="center"
                >
                    <stripe-buy-button
                        buy-button-id="buy_btn_1QdCKmGAf1R453AQH8vl4nwX"
                        publishable-key="pk_live_51QdBvMGAf1R453AQL9xskuy6XyHKbYORN3I4AV1KhsDuvGnNRR6QV3CsIiZ2rbnRBg65F34PEii9esiviIOSEt2n00Xi1lwmqe"
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                {/* "Skip" button just closes the dialog */}
                <Button onClick={onClose} variant="contained" color="secondary">
                    Skip
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default DonationDialog;