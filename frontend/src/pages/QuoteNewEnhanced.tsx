import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Container, Box, Typography, Button, Paper } from '@mui/material';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import QuoteBuilderWizard from '../components/QuoteBuilderWizard';

const QuoteNewEnhanced: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const customerIdParam = searchParams.get('customer');

  const handleComplete = (quoteId: string) => {
    navigate(`/quotes/${quoteId}`);
  };

  const handleCancel = () => {
    navigate('/quotes');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={handleCancel}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Create New Quote (AI-Powered)
        </Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <QuoteBuilderWizard
          onComplete={handleComplete}
          onCancel={handleCancel}
          initialCustomerId={customerIdParam || undefined}
        />
      </Paper>
    </Container>
  );
};

export default QuoteNewEnhanced;

