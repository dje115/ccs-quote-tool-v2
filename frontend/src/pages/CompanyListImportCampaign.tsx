import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Alert,
  Grid,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  AutoAwesome as QuickSetupIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const CompanyListImportCampaign: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as any;
  
  const [campaignName, setCampaignName] = useState('');
  const [description, setDescription] = useState('');
  const [companies, setCompanies] = useState<string[]>(state?.companies || []);
  const [newCompanyInput, setNewCompanyInput] = useState('');
  const [excludeDuplicates, setExcludeDuplicates] = useState(true);
  const [includeExisting, setIncludeExisting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [pasteDialogOpen, setPasteDialogOpen] = useState(false);
  const [pasteContent, setPasteContent] = useState('');

  const handleAddCompany = () => {
    const trimmed = newCompanyInput.trim();
    if (trimmed && !companies.includes(trimmed)) {
      setCompanies([...companies, trimmed]);
      setNewCompanyInput('');
    }
  };

  const handleRemoveCompany = (index: number) => {
    setCompanies(companies.filter((_, i) => i !== index));
  };

  const handlePasteCompanies = () => {
    const newCompanies = pasteContent
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !companies.includes(line));
    
    setCompanies([...companies, ...newCompanies]);
    setPasteContent('');
    setPasteDialogOpen(false);
  };

  const handleQuickSetup = () => {
    const now = new Date();
    const dateTime = now.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    
    let campaignName = '';
    
    // Check if we have source data from CRM record
    if (state?.source) {
      // Extract the customer name from source like "Competitors of Acme Corp"
      let customerName = state.source;
      if (customerName.includes('Competitors of ')) {
        customerName = customerName.replace('Competitors of ', '');
      }
      campaignName = `${customerName} - ${dateTime}`;
    } else if (state?.customerName) {
      // Direct customer name passed
      campaignName = `${state.customerName} - ${dateTime}`;
    } else {
      // Manual entry - just use "List"
      campaignName = `List - ${dateTime}`;
    }
    
    setCampaignName(campaignName);
  };

  const handleCreateCampaign = async () => {
    setError(null);

    // Validation
    if (!campaignName.trim()) {
      setError('Campaign name is required');
      return;
    }

    if (companies.length === 0) {
      setError('Please add at least one company');
      return;
    }

    try {
      setLoading(true);

      const campaignData = {
        name: campaignName,
        description: description || `Company list import campaign with ${companies.length} companies`,
        prompt_type: 'company_list',
        company_names: companies,
        exclude_duplicates: excludeDuplicates,
        include_existing_customers: includeExisting
      };

      const response = await campaignAPI.create(campaignData);
      
      setSuccess(true);
      setTimeout(() => {
        navigate(`/campaigns/${response.data.id}`);
      }, 1500);
    } catch (err: any) {
      console.error('Error creating campaign:', err);
      
      // Handle validation errors from FastAPI
      if (err.response?.status === 422 && err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Multiple validation errors
          const errorMessages = detail.map((error: any) => 
            `${error.loc ? error.loc.join('.') : 'field'}: ${error.msg}`
          );
          setError(`Validation failed: ${errorMessages.join(', ')}`);
        } else {
          // Single error message
          setError(detail);
        }
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to create campaign');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <Button
          variant="text"
          startIcon={<BackIcon />}
          onClick={() => navigate('/campaigns/create')}
        >
          Back
        </Button>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight="700" color="primary">
            Company List Import
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Import companies from CRM records or competitor lists
          </Typography>
        </Box>
      </Box>

      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Campaign created successfully! Redirecting...
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Form */}
        <Grid
          size={{
            xs: 12,
            md: 8
          }}>
          <Paper sx={{ p: 3 }}>
            {/* Campaign Details */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Campaign Details
              </Typography>
              
              {/* Campaign Name with Quick Setup */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  label="Campaign Name"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="e.g., Competitor Analysis - Q4 2025"
                  disabled={loading}
                />
                <Button
                  variant="outlined"
                  startIcon={<QuickSetupIcon />}
                  onClick={handleQuickSetup}
                  disabled={loading}
                  sx={{ whiteSpace: 'nowrap', minWidth: 140, flexShrink: 0 }}
                  title="Auto-generate campaign name with source and timestamp"
                >
                  Quick Setup
                </Button>
              </Box>
              <TextField
                fullWidth
                label="Description (Optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add notes about this campaign..."
                multiline
                rows={3}
                disabled={loading}
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Company List */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Company List
              </Typography>
              
              {/* Add Company Input */}
              <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                <TextField
                  fullWidth
                  label="Company Name"
                  value={newCompanyInput}
                  onChange={(e) => setNewCompanyInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddCompany();
                    }
                  }}
                  placeholder="Enter company name and press Enter"
                  disabled={loading}
                />
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddCompany}
                  disabled={loading || !newCompanyInput.trim()}
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  Add
                </Button>
              </Box>

              {/* Paste Button */}
              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                onClick={() => setPasteDialogOpen(true)}
                disabled={loading}
                sx={{ mb: 2 }}
              >
                Paste Company List
              </Button>

              {/* Company List Display */}
              {companies.length > 0 && (
                <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto', mb: 2 }}>
                  <List>
                    {companies.map((company, index) => (
                      <Box key={index}>
                        <ListItem
                          secondaryAction={
                            <IconButton
                              edge="end"
                              aria-label="delete"
                              onClick={() => handleRemoveCompany(index)}
                              disabled={loading}
                            >
                              <DeleteIcon />
                            </IconButton>
                          }
                        >
                          <CheckCircleIcon sx={{ mr: 2, color: 'success.main' }} />
                          <ListItemText primary={company} />
                        </ListItem>
                        {index < companies.length - 1 && <Divider />}
                      </Box>
                    ))}
                  </List>
                </Paper>
              )}

              <Alert severity="info">
                {companies.length} compan{companies.length === 1 ? 'y' : 'ies'} added to campaign
              </Alert>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Campaign Settings */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Campaign Settings
              </Typography>
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={excludeDuplicates}
                    onChange={(e) => setExcludeDuplicates(e.target.checked)}
                    disabled={loading}
                  />
                }
                label="Exclude duplicates (skip companies already in system)"
              />
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeExisting}
                    onChange={(e) => setIncludeExisting(e.target.checked)}
                    disabled={loading}
                  />
                }
                label="Include existing customers in analysis"
              />
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/campaigns/create')}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                onClick={handleCreateCampaign}
                disabled={loading || !campaignName.trim() || companies.length === 0}
              >
                {loading ? 'Creating...' : 'Create Campaign'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Info Panel */}
        <Grid
          size={{
            xs: 12,
            md: 4
          }}>
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
              ℹ️ How It Works
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                1. Add Companies
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Add company names individually or paste a list
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                2. Configure Settings
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Choose whether to exclude duplicates and include existing customers
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                3. Create Campaign
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI will analyze each company and create leads
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              💡 Tips
            </Typography>
            <ul style={{ paddingLeft: 20, margin: 0 }}>
              <li>
                <Typography variant="body2" color="text.secondary">
                  Use company names that are exact or close matches
                </Typography>
              </li>
              <li>
                <Typography variant="body2" color="text.secondary">
                  Paste lists with one company per line
                </Typography>
              </li>
              <li>
                <Typography variant="body2" color="text.secondary">
                  Duplicates are automatically detected and removed
                </Typography>
              </li>
            </ul>
          </Paper>
        </Grid>
      </Grid>

      {/* Paste Dialog */}
      <Dialog open={pasteDialogOpen} onClose={() => setPasteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Paste Company List</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Paste one company name per line:
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={6}
            value={pasteContent}
            onChange={(e) => setPasteContent(e.target.value)}
            placeholder="Company A&#10;Company B&#10;Company C"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasteDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handlePasteCompanies}
            disabled={!pasteContent.trim()}
          >
            Add Companies
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CompanyListImportCampaign;
