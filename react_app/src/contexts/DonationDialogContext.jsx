// src/context/DonationDialogContext.jsx

import React, { createContext, useState, useContext } from 'react';
import DonationDialog from '../components/DonationDialog';

const DonationDialogContext = createContext();

export const useDonationDialog = () => {
    return useContext(DonationDialogContext);
};

export const DonationDialogProvider = ({ children }) => {
    const [open, setOpen] = useState(false);

    const openDonationDialog = () => setOpen(true);
    const closeDonationDialog = () => setOpen(false);

    return (
        <DonationDialogContext.Provider value={{ openDonationDialog, closeDonationDialog }}>
            {children}
            <DonationDialog open={open} onClose={closeDonationDialog} />
        </DonationDialogContext.Provider>
    );
};

