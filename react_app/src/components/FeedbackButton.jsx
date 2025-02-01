import React, { useState } from 'react';

function FeedbackButton() {
  const [showModal, setShowModal] = useState(false);
  const [feedback, setFeedback] = useState('');

  const openModal = () => setShowModal(true);
  const closeModal = () => setShowModal(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback }),
      });

      if (!response.ok) {
        // Handle error
        console.error('Error submitting feedback');
      } else {
        // Optionally show a success message
        console.log('Feedback submitted successfully!');
      }
    } catch (error) {
      console.error('An error occurred:', error);
    }

    // Reset the form and close the modal
    setFeedback('');
    setShowModal(false);
  };

  return (
    <div>
      {/* Floating or sticky button */}
      <button 
        onClick={openModal}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 999
        }}
      >
        Feedback
      </button>

      {/* Modal (only renders if showModal is true) */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div
            style={{
              backgroundColor: '#fff',
              padding: '2rem',
              borderRadius: '8px',
              width: '300px'
            }}
          >
            <h3>Send us your feedback</h3>
            <form onSubmit={handleSubmit}>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={5}
                style={{ width: '100%' }}
                placeholder="Share your thoughts..."
              />
              <div style={{ marginTop: '1rem' }}>
                <button type="submit">Submit</button>
                <button type="button" onClick={closeModal} style={{ marginLeft: '1rem' }}>
                  Close
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default FeedbackButton;