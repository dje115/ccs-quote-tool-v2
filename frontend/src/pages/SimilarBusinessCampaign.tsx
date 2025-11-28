import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Autocomplete
} from '@mui/material';
import {
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Search as SearchIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { customerAPI } from '../services/api';

interface CampaignData {
  name: string;
  description: string;
  reference_company_name: string;
  postcode: string;
  distance_miles: number;
  max_results: number;
  prompt_type: string;
  company_size_category?: string;
}

interface Customer {
  id: string;
  company_name: string;
}

const SimilarBusinessCampaign: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const api = useApi();
  
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [campaignData, setCampaignData] = useState<CampaignData>({
    name: '',
    description: '',
    reference_company_name: '',
    postcode: '',
    distance_miles: 50,
    max_results: 20,
    prompt_type: 'similar_business',
    company_size_category: undefined
  });

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await customerAPI.list();
      setCustomers(response.data || []);
    } catch (err: any) {
      console.error('Failed to load customers:', err);
    }
  };

  const handleInputChange = (field: keyof CampaignData, value: any) => {
    setCampaignData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Validation
    if (!campaignData.reference_company_name.trim()) {
      setError('Please enter a company name to find similar businesses');
      setSubmitting(false);
      return;
    }

    if (!campaignData.postcode.trim()) {
      setError('Please enter a postcode for location-based search');
      setSubmitting(false);
      return;
    }

    try {
      // Build the campaign data - use reference company name in custom_prompt or description
      const campaignPayload = {
        name: campaignData.name || `Similar to ${campaignData.reference_company_name}`,
        description: campaignData.description || `Find businesses similar to ${campaignData.reference_company_name}`,
        sector_name: 'General Business', // Default sector
        postcode: campaignData.postcode,
        distance_miles: campaignData.distance_miles,
        max_results: campaignData.max_results,
        prompt_type: 'similar_business',
        custom_prompt: `Find businesses similar to ${campaignData.reference_company_name}. Look for companies with similar business activities, size, and market position.`,
        company_size_category: campaignData.company_size_category || undefined
      };

      const response = await api.post('/campaigns/', campaignPayload);
      setSuccess(true);
      
      // Redirect to campaigns list after a short delay
      setTimeout(() => {
        navigate('/campaigns');
      }, 2000);
      
    } catch (err: any) {
      console.error('Failed to create campaign:', err);
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <BusinessIcon sx={{ mr: 2, color: 'primary.main', fontSize: 32 }} />
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Similar Business Lookup
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Find businesses similar to a specific company
            </Typography>
          </Box>
        </Box>
        
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <InfoIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: 16 }} />
            Enter a company name and we'll find similar businesses based on industry, size, and business activities
          </Typography>
        </Alert>
      </Paper>

      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Campaign created successfully! Redirecting...
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Form */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Reference Company Name */}
            <Grid item xs={12}>
              <Autocomplete
                freeSolo
                options={customers}
                getOptionLabel={(option) => 
                  typeof option === 'string' ? option : option.company_name
                }
                inputValue={campaignData.reference_company_name}
                onInputChange={(event, newInputValue) => {
                  handleInputChange('reference_company_name', newInputValue);
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Reference Company Name"
                    required
                    helperText="Enter the company name you want to find similar businesses to"
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: <BusinessIcon sx={{ mr: 1, color: 'action.active' }} />
                    }}
                  />
                )}
              />
            </Grid>

            {/* Campaign Name */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Campaign Name"
                value={campaignData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder={`Similar to ${campaignData.reference_company_name || 'Company'}`}
                helperText="Optional - will auto-generate if left blank"
              />
            </Grid>

            {/* Postcode */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search Center Postcode"
                value={campaignData.postcode}
                onChange={(e) => handleInputChange('postcode', e.target.value.toUpperCase())}
                required
                placeholder="e.g., SW1A 1AA"
                helperText="UK postcode to search around"
                InputProps={{
                  startAdornment: <LocationIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />
            </Grid>

            {/* Distance */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Search Radius (miles)"
                value={campaignData.distance_miles}
                onChange={(e) => handleInputChange('distance_miles', parseInt(e.target.value) || 50)}
                inputProps={{ min: 5, max: 200 }}
                helperText="Search radius in miles (5-200)"
              />
            </Grid>

            {/* Max Results */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Maximum Results"
                value={campaignData.max_results}
                onChange={(e) => handleInputChange('max_results', parseInt(e.target.value) || 20)}
                inputProps={{ min: 5, max: 100 }}
                helperText="Maximum number of similar businesses to find (5-100)"
              />
            </Grid>

            {/* Company Size Filter */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Company Size Filter (Optional)"
                value={campaignData.company_size_category || ''}
                onChange={(e) => handleInputChange('company_size_category', e.target.value || undefined)}
                SelectProps={{
                  native: true
                }}
              >
                <option value="">All Sizes</option>
                <option value="Micro">Micro (1-9 employees)</option>
                <option value="Small">Small (10-49 employees)</option>
                <option value="Medium">Medium (50-249 employees)</option>
                <option value="Large">Large (250+ employees)</option>
              </TextField>
            </Grid>

            {/* Description */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Campaign Description (Optional)"
                value={campaignData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder={`Find businesses similar to ${campaignData.reference_company_name || 'the reference company'}`}
                helperText="Optional description for this campaign"
              />
            </Grid>

            {/* Submit Button */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Button
                  variant="outlined"
                  onClick={() => navigate('/campaigns')}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  size="large"
                  disabled={submitting || !campaignData.reference_company_name.trim() || !campaignData.postcode.trim()}
                  startIcon={submitting ? <CircularProgress size={20} /> : <SearchIcon />}
                >
                  {submitting ? 'Creating Campaign...' : 'Create Campaign'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default SimilarBusinessCampaign;

