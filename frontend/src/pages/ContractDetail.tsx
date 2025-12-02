import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Chip,
  Grid,
  Divider,
  Alert
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Description as DescriptionIcon,
  Receipt as ReceiptIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { contractAPI, quoteAPI } from '../services/api';

const ContractDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [contract, setContract] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generatingQuote, setGeneratingQuote] = useState(false);
  const [associatedQuote, setAssociatedQuote] = useState<any>(null);

  useEffect(() => {
    if (id) {
      loadContract();
      checkAssociatedQuote();
    }
  }, [id]);

  const loadContract = async () => {
    try {
      setLoading(true);
      const response = await contractAPI.get(id!);
      setContract(response.data);
    } catch (error) {
      console.error('Error loading contract:', error);
      alert('Failed to load contract');
    } finally {
      setLoading(false);
    }
  };

  const checkAssociatedQuote = async () => {
    try {
      const response = await contractAPI.getAssociatedQuote(id!);
      if (response.data?.quote) {
        setAssociatedQuote(response.data.quote);
      }
    } catch (error) {
      // No associated quote - that's fine
      console.log('No associated quote found');
    }
  };

  const handleGenerateQuote = async () => {
    if (!window.confirm('Generate a quote from this contract? This will create a new quote with all contract details.')) {
      return;
    }

    setGeneratingQuote(true);
    try {
      const response = await contractAPI.generateQuoteFromContract(id!);
      if (response.data?.quote_id) {
        alert('Quote generated successfully!');
        navigate(`/quotes/${response.data.quote_id}`);
      } else {
        throw new Error('Failed to generate quote');
      }
    } catch (error: any) {
      console.error('Error generating quote:', error);
      alert(error.response?.data?.detail || 'Failed to generate quote from contract');
    } finally {
      setGeneratingQuote(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'draft':
        return 'default';
      case 'pending_signature':
        return 'warning';
      case 'expired':
        return 'error';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Typography>Loading contract...</Typography>
      </Container>
    );
  }

  if (!contract) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Alert severity="error">Contract not found</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/contracts')}>
          Back
        </Button>
        <Typography variant="h4">{contract.contract_name}</Typography>
        <Chip
          label={contract.status.replace('_', ' ')}
          color={getStatusColor(contract.status) as any}
        />
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>Contract Content</Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                p: 2,
                bgcolor: 'grey.50',
                borderRadius: 1,
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                maxHeight: '600px',
                overflow: 'auto'
              }}
            >
              {contract.contract_content || 'No content available'}
            </Box>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Contract Details</Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">Contract Number</Typography>
              <Typography variant="body1" fontWeight="medium">{contract.contract_number}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">Type</Typography>
              <Typography variant="body1">{contract.contract_type}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">Status</Typography>
              <Chip
                label={contract.status.replace('_', ' ')}
                size="small"
                color={getStatusColor(contract.status) as any}
                sx={{ mt: 0.5 }}
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">Start Date</Typography>
              <Typography variant="body1">
                {new Date(contract.start_date).toLocaleDateString()}
              </Typography>
            </Box>

            {contract.end_date && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">End Date</Typography>
                <Typography variant="body1">
                  {new Date(contract.end_date).toLocaleDateString()}
                </Typography>
              </Box>
            )}

            {contract.annual_value && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">Annual Value</Typography>
                <Typography variant="body1" fontWeight="medium">
                  £{contract.annual_value.toLocaleString()}
                </Typography>
              </Box>
            )}

            {contract.monthly_value && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">Monthly Value</Typography>
                <Typography variant="body1" fontWeight="medium">
                  £{contract.monthly_value.toLocaleString()}
                </Typography>
              </Box>
            )}

            {contract.opportunity_id && (
              <Box sx={{ mb: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  onClick={() => navigate(`/opportunities/${contract.opportunity_id}`)}
                >
                  View Opportunity
                </Button>
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Contract-to-Quote Integration */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Generate Quote
              </Typography>
              {associatedQuote ? (
                <Box>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    Quote already exists
                  </Alert>
                  <Button
                    variant="contained"
                    size="small"
                    fullWidth
                    startIcon={<ReceiptIcon />}
                    onClick={() => navigate(`/quotes/${associatedQuote.id}`)}
                  >
                    View Quote
                  </Button>
                </Box>
              ) : (
                <Button
                  variant="contained"
                  size="small"
                  fullWidth
                  startIcon={<ReceiptIcon />}
                  onClick={handleGenerateQuote}
                  disabled={generatingQuote}
                >
                  {generatingQuote ? 'Generating...' : 'Generate Quote from Contract'}
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ContractDetail;

