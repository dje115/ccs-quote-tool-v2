import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  IconButton
} from '@mui/material';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const CampaignCreate: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_type: 'it_msp_expansion',
    postcode: '',
    distance_miles: 20,
    max_results: 100,
    custom_prompt: ''
  });

  const handleChange = (field: string) => (e: any) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await campaignAPI.create(formData);
      navigate(`/campaigns/${response.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/campaigns')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          Create Lead Generation Campaign
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                label="Campaign Name"
                value={formData.name}
                onChange={handleChange('name')}
                helperText="Give your campaign a descriptive name"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={handleChange('description')}
                helperText="Optional description of what you're looking for"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Campaign Type</InputLabel>
                <Select
                  value={formData.prompt_type}
                  onChange={handleChange('prompt_type')}
                  label="Campaign Type"
                >
                  <MenuItem value="it_msp_expansion">IT/MSP Expansion</MenuItem>
                  <MenuItem value="new_business">New Business</MenuItem>
                  <MenuItem value="competitor_analysis">Competitor Analysis</MenuItem>
                  <MenuItem value="custom">Custom Prompt</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Postcode"
                value={formData.postcode}
                onChange={handleChange('postcode')}
                helperText="UK postcode for location search"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Distance (miles)"
                value={formData.distance_miles}
                onChange={handleChange('distance_miles')}
                inputProps={{ min: 1, max: 100 }}
                helperText="Search radius from postcode"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Max Results"
                value={formData.max_results}
                onChange={handleChange('max_results')}
                inputProps={{ min: 10, max: 500 }}
                helperText="Maximum leads to generate"
              />
            </Grid>

            {formData.prompt_type === 'custom' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  label="Custom Prompt"
                  value={formData.custom_prompt}
                  onChange={handleChange('custom_prompt')}
                  helperText="Describe exactly what type of businesses you're looking for"
                  required
                />
              </Grid>
            )}

            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="body2">
                  <strong>How it works:</strong>
                  <br />
                  1. AI will search for businesses matching your criteria
                  <br />
                  2. Each business will be verified and analyzed
                  <br />
                  3. Leads will be scored based on fit and potential
                  <br />
                  4. Duplicates will be automatically filtered
                  <br />
                  <br />
                  This process typically takes 5-15 minutes depending on the number of results.
                </Typography>
              </Alert>
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/campaigns')}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                >
                  {loading ? 'Creating Campaign...' : 'Start Campaign'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  );
};

export default CampaignCreate;

