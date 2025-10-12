import React, { useState, useEffect } from 'react';
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
  IconButton,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  FormControlLabel,
  Checkbox,
  Divider
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Campaign as CampaignIcon,
  LocationOn as LocationIcon,
  Settings as SettingsIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

interface PromptType {
  value: string;
  label: string;
  description: string;
}

const CampaignCreate: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [promptTypes, setPromptTypes] = useState<PromptType[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_type: 'it_msp_expansion',
    postcode: '',
    distance_miles: 20,
    max_results: 50,
    custom_prompt: '',
    exclude_duplicates: true,
    include_existing_customers: false
  });

  useEffect(() => {
    loadPromptTypes();
  }, []);

  const loadPromptTypes = async () => {
    try {
      const response = await campaignAPI.getPromptTypes();
      setPromptTypes(response.data);
    } catch (err) {
      console.error('Error loading prompt types:', err);
      // Use fallback prompt types
      setPromptTypes([
        { value: 'it_msp_expansion', label: 'IT/MSP Expansion', description: 'Find IT/MSP businesses' },
        { value: 'education', label: 'Education Sector', description: 'Schools and educational institutions' },
        { value: 'healthcare', label: 'Healthcare', description: 'Healthcare facilities' },
        { value: 'manufacturing', label: 'Manufacturing', description: 'Manufacturing companies' },
        { value: 'retail_office', label: 'Retail & Office', description: 'Retail and office businesses' }
      ]);
    }
  };

  const handleChange = (field: string) => (e: any) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({ ...formData, [field]: value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await campaignAPI.create(formData);
      navigate('/campaigns');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const selectedPrompt = promptTypes.find(p => p.value === formData.prompt_type);

  return (
    <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/campaigns')} sx={{ mr: 1 }}>
          <BackIcon />
        </IconButton>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <CampaignIcon sx={{ color: 'white', fontSize: 28 }} />
        </Box>
        <Typography variant="h4" component="h1" fontWeight="600">
          Create Lead Generation Campaign
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Left Column - Campaign Details */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3, borderRadius: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon color="primary" /> Campaign Details
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <TextField
                fullWidth
                required
                label="Campaign Name"
                value={formData.name}
                onChange={handleChange('name')}
                placeholder="e.g., IT MSPs in Leicester - Q3 2024"
                helperText="Choose a descriptive name for your campaign"
                sx={{ mb: 3 }}
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={handleChange('description')}
                placeholder="Optional description of your campaign goals..."
                helperText="Optional description of what you're looking for"
              />
            </Paper>

            {/* AI Search Prompts */}
            <Paper sx={{ p: 3, borderRadius: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                🤖 AI Search Prompts
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Choose a search prompt:
              </Typography>

              <Grid container spacing={2}>
                {promptTypes.map((prompt) => (
                  <Grid item xs={12} sm={6} key={prompt.value}>
                    <Card
                      sx={{
                        borderRadius: 2,
                        border: formData.prompt_type === prompt.value ? '2px solid #667eea' : '1px solid #e0e0e0',
                        transition: 'all 0.2s',
                        '&:hover': { boxShadow: 3 }
                      }}
                    >
                      <CardActionArea onClick={() => setFormData({ ...formData, prompt_type: prompt.value })}>
                        <CardContent>
                          <Typography variant="subtitle1" fontWeight="600" gutterBottom>
                            {prompt.label}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {prompt.description}
                          </Typography>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>

            {/* Search Criteria */}
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocationIcon color="primary" /> Search Criteria
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    required
                    label="Postcode"
                    value={formData.postcode}
                    onChange={handleChange('postcode')}
                    placeholder="e.g., LE17 5NJ"
                    helperText="Center point for your search"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Distance (miles)</InputLabel>
                    <Select
                      value={formData.distance_miles}
                      onChange={handleChange('distance_miles')}
                      label="Distance (miles)"
                    >
                      <MenuItem value={10}>10 miles</MenuItem>
                      <MenuItem value={15}>15 miles</MenuItem>
                      <MenuItem value={20}>20 miles</MenuItem>
                      <MenuItem value={30}>30 miles</MenuItem>
                      <MenuItem value={50}>50 miles</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Maximum Results</InputLabel>
                    <Select
                      value={formData.max_results}
                      onChange={handleChange('max_results')}
                      label="Maximum Results"
                    >
                      <MenuItem value={20}>20 leads</MenuItem>
                      <MenuItem value={50}>50 leads</MenuItem>
                      <MenuItem value={100}>100 leads</MenuItem>
                      <MenuItem value={250}>250 leads</MenuItem>
                      <MenuItem value={500}>500 leads</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Paper>

            {/* Campaign Settings */}
            <Paper sx={{ p: 3, borderRadius: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SettingsIcon color="primary" /> Campaign Settings
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.exclude_duplicates}
                    onChange={handleChange('exclude_duplicates')}
                  />
                }
                label="Exclude duplicate companies (recommended)"
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4, mb: 2 }}>
                Automatically filter out companies already in your system
              </Typography>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.include_existing_customers}
                    onChange={handleChange('include_existing_customers')}
                  />
                }
                label="Include existing customers in results"
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4 }}>
                Show companies you already work with (not recommended)
              </Typography>
            </Paper>
          </Grid>

          {/* Right Column - Campaign Preview */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, borderRadius: 3, position: 'sticky', top: 20 }}>
              <Typography variant="h6" gutterBottom fontWeight="600">
                📊 Campaign Preview
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Search Area:</strong>
                </Typography>
                <Typography variant="body1">
                  {formData.postcode || 'Enter postcode'} (±{formData.distance_miles} miles)
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Target Results:</strong>
                </Typography>
                <Typography variant="body1">
                  Up to {formData.max_results} leads
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Search Type:</strong>
                </Typography>
                <Chip
                  label={selectedPrompt?.label || 'Select a prompt'}
                  color="primary"
                  size="small"
                  sx={{ mt: 0.5 }}
                />
              </Box>

              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>How it works:</strong>
                </Typography>
                <Typography variant="caption" component="div">
                  1. AI will search for businesses matching your criteria<br />
                  2. Each business will be verified and analyzed<br />
                  3. Leads will be scored based on fit and potential<br />
                  4. Duplicates will be automatically filtered<br />
                  <br />
                  This process typically takes 5-15 minutes depending on the number of results.
                </Typography>
              </Alert>

              <Box sx={{ mt: 3 }}>
                <Button
                  fullWidth
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    textTransform: 'none',
                    fontSize: '16px',
                    fontWeight: 600,
                    mb: 1,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                    }
                  }}
                >
                  {loading ? '🚀 Creating Campaign...' : '🚀 Start Campaign'}
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => navigate('/campaigns')}
                  disabled={loading}
                  sx={{ borderRadius: 2, textTransform: 'none' }}
                >
                  Cancel
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </form>
    </Container>
  );
};

export default CampaignCreate;
