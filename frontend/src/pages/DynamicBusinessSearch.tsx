import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  Tooltip,
  Alert,
  CircularProgress,
  Divider,
  FormControlLabel,
  Switch,
  InputAdornment,
  Fade,
  Autocomplete
} from '@mui/material';
import {
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Search as SearchIcon,
  Info as InfoIcon,
  Language as LanguageIcon,
  Public as PublicIcon,
  Speed as SpeedIcon,
  GpsFixed as TargetIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';

interface Sector {
  id: number;
  sector_name: string;
  prompt_ready_replacement_line: string;
  example_keywords: string;
  example_companies: string;
}

interface CampaignData {
  name: string;
  description: string;
  sector_name: string;
  postcode: string;
  distance_miles: number;
  max_results: number;
  prompt_type: string;
  custom_prompt: string;
  company_size_category?: string;
}

const CampaignCreate: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const api = useApi();
  
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [sectorSearch, setSectorSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [campaignData, setCampaignData] = useState<CampaignData>({
    name: '',
    description: '',
    sector_name: '',
    postcode: '',
    distance_miles: 50,
    max_results: 20,
    prompt_type: 'sector_search',
    custom_prompt: ''
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  // Enhanced filtering with better search logic
  const filteredSectors = useMemo(() => {
    if (!sectors) return [];
    
    // If no search term, show all sectors
    if (!sectorSearch.trim()) return sectors;
    
    const searchTerm = sectorSearch.toLowerCase().trim();
    
    return sectors.filter(sector => {
      const name = sector.sector_name.toLowerCase();
      const description = sector.prompt_ready_replacement_line?.toLowerCase() || '';
      const keywords = sector.example_keywords?.toLowerCase() || '';
      
      // Prioritize exact name matches, then description, then keywords
      const nameMatch = name.includes(searchTerm);
      const descriptionMatch = description.includes(searchTerm);
      const keywordMatch = keywords.includes(searchTerm);
      
      // Also check for word-starts-with matches for better UX
      const nameWordMatch = name.split(' ').some(word => word.startsWith(searchTerm));
      const descriptionWordMatch = description.split(' ').some(word => word.startsWith(searchTerm));
      
      return nameMatch || descriptionMatch || keywordMatch || nameWordMatch || descriptionWordMatch;
    });
  }, [sectors, sectorSearch]);

  // Get selected sector details
  const selectedSector = sectors?.find(s => s.sector_name === campaignData.sector_name);

  useEffect(() => {
    loadSectors();
  }, []);

  const loadSectors = async () => {
    setLoading(true);
    try {
      console.log('­ƒöä Loading sectors...');
      const response = await api.get('/sectors/');
      console.log('Ô£à Sectors loaded:', response);
      console.log('­ƒôè Number of sectors:', response?.length);
      setSectors(response);
    } catch (err: any) {
      console.error('ÔØî Failed to load sectors:', err);
      console.error('ÔØî Error details:', err.response?.data);
      setError(t('campaigns.loadSectorsError', 'Failed to load sectors'));
    } finally {
      setLoading(false);
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

    try {
      const response = await api.post('/campaigns/', campaignData);
      setSuccess(true);
      
      // Redirect to campaigns list after a short delay
      setTimeout(() => {
        navigate('/campaigns');
      }, 2000);
      
    } catch (err: any) {
      console.error('Failed to create campaign:', err);
      setError(err.response?.data?.detail || t('campaigns.createError', 'Failed to create campaign'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <BusinessIcon sx={{ mr: 2, color: 'primary.main', fontSize: 32 }} />
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {t('campaigns.createNewCampaign', 'Create New Campaign')}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {t('campaigns.createDescription', 'Generate high-quality leads using AI-powered business discovery')}
            </Typography>
          </Box>
        </Box>
        
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <LanguageIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: 16 }} />
            {t('campaigns.multilingualNote', 'This campaign will automatically adapt to your business profile and target the most relevant sectors')}
          </Typography>
        </Alert>
      </Paper>
      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {t('campaigns.createSuccess', 'Campaign created successfully! Redirecting...')}
        </Alert>
      )}
      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      {/* Action Buttons - Always at Top */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" gap={2} justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {t('campaigns.quickActions', 'Quick Actions')}
          </Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              onClick={() => navigate('/campaigns')}
              disabled={submitting}
              startIcon={<BusinessIcon />}
            >
              {t('campaigns.viewAll', 'View All Campaigns')}
            </Button>
            <Button
              variant="contained"
              onClick={() => {
                // Auto-fill form with smart defaults
                handleInputChange('name', `Campaign ${new Date().toLocaleDateString()}`);
                handleInputChange('postcode', 'LE1 6RP');
                handleInputChange('distance_miles', 30);
                handleInputChange('max_results', 20);
              }}
              startIcon={<SpeedIcon />}
            >
              {t('campaigns.quickSetup', 'Quick Setup')}
            </Button>
          </Box>
        </Box>
      </Paper>
      <Grid container spacing={3}>
        {/* Main Form */}
        <Grid
          size={{
            xs: 12,
            lg: 8
          }}>
          <Paper elevation={2} sx={{ p: 3 }}>
            {/* Form Header with Action Buttons */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">
                {t('campaigns.basicInformation', 'Basic Information')}
              </Typography>
              <Box display="flex" gap={1}>
                <Tooltip title={t('campaigns.resetForm', 'Reset form to defaults')}>
                  <span>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => {
                        setCampaignData({
                          name: '',
                          description: '',
                          sector_name: '',
                          postcode: '',
                          distance_miles: 50,
                          max_results: 20,
                          prompt_type: 'sector_search',
                          custom_prompt: '',
                          company_size_category: undefined
                        });
                      }}
                    >
                      {t('common.reset', 'Reset')}
                    </Button>
                  </span>
                </Tooltip>
                <Tooltip title={t('campaigns.saveDraft', 'Save as draft')}>
                  <span>
                    <Button
                      size="small"
                      variant="outlined"
                      disabled={!campaignData.name}
                    >
                      {t('common.draft', 'Draft')}
                    </Button>
                  </span>
                </Tooltip>
              </Box>
            </Box>
            
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                {/* Target Sector - Moved to Top for Better UX */}
                <Grid size={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    {t('campaigns.targetSector', 'Target Sector')}
                  </Typography>
                  
                  {/* Search Box for Sectors */}
                  <TextField
                    fullWidth
                    placeholder={t('campaigns.searchSectors', 'Search sectors... (e.g., "IT", "Healthcare", "Manufacturing")')}
                    value={sectorSearch}
                    onChange={(e) => setSectorSearch(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                      endAdornment: sectorSearch && (
                        <InputAdornment position="end">
                          <Button
                            size="small"
                            onClick={() => setSectorSearch('')}
                            sx={{ minWidth: 'auto', p: 0.5 }}
                          >
                            Ô£ò
                          </Button>
                        </InputAdornment>
                      ),
                    }}
                    sx={{ mb: 2 }}
                  />
                  
                  {/* Filtered Sector Selection */}
                  <FormControl fullWidth required>
                    <InputLabel>
                      <Box display="flex" alignItems="center">
                        <PublicIcon sx={{ mr: 1 }} />
                        {t('campaigns.selectSector', 'Select Sector')}
                      </Box>
                    </InputLabel>
                    <Select
                      value={campaignData.sector_name || ''}
                      onChange={(e) => handleInputChange('sector_name', e.target.value)}
                      label={t('campaigns.selectSector', 'Select Sector')}
                      MenuProps={{
                        PaperProps: {
                          style: {
                            maxHeight: 500, // Increased height for better browsing
                          },
                        },
                      }}
                    >
                      {filteredSectors.length === 0 ? (
                        <MenuItem disabled>
                          <Typography variant="body2" color="text.secondary">
                            {sectorSearch ? `No sectors found matching "${sectorSearch}"` : 'No sectors available'}
                          </Typography>
                        </MenuItem>
                      ) : (
                        filteredSectors.map((sector) => (
                          <MenuItem key={sector.id} value={sector.sector_name}>
                            <Box sx={{ width: '100%' }}>
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {sector.sector_name}
                              </Typography>
                              {sector.prompt_ready_replacement_line && (
                                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                                  {sector.prompt_ready_replacement_line.length > 100 
                                    ? `${sector.prompt_ready_replacement_line.substring(0, 100)}...`
                                    : sector.prompt_ready_replacement_line
                                  }
                                </Typography>
                              )}
                              {sector.example_keywords && (
                                <Typography variant="caption" color="primary.main" display="block" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                                  Keywords: {sector.example_keywords}
                                </Typography>
                              )}
                            </Box>
                          </MenuItem>
                        ))
                      )}
                    </Select>
                  </FormControl>
                  
                  {/* Sector Count and Quick Filters */}
                  <Box display="flex" justifyContent="space-between" alignItems="center" mt={1} mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="caption" color="text.secondary">
                        {sectorSearch ? `${filteredSectors.length} of ${sectors?.length || 0} sectors` : `All ${sectors?.length || 0} sectors`}
                      </Typography>
                      {sectorSearch && (
                        <Fade in={true}>
                          <Typography variant="caption" color="primary.main">
                            (filtered by "{sectorSearch}")
                          </Typography>
                        </Fade>
                      )}
                    </Box>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {['IT', 'Healthcare', 'Manufacturing', 'Retail', 'Finance', 'Technology', 'Services'].map((filter) => (
                        <Chip
                          key={filter}
                          label={filter}
                          size="small"
                          variant={sectorSearch === filter ? "filled" : "outlined"}
                          color={sectorSearch === filter ? "primary" : "default"}
                          onClick={() => setSectorSearch(filter)}
                          sx={{ 
                            cursor: 'pointer',
                            '&:hover': {
                              backgroundColor: sectorSearch === filter ? 'primary.dark' : 'action.hover'
                            }
                          }}
                        />
                      ))}
                      {sectorSearch && (
                        <Chip
                          label="Show All"
                          size="small"
                          variant="outlined"
                          color="secondary"
                          onClick={() => setSectorSearch('')}
                          sx={{ 
                            cursor: 'pointer',
                            '&:hover': {
                              backgroundColor: 'secondary.light'
                            }
                          }}
                        />
                      )}
                    </Box>
                  </Box>
                  
                  {selectedSector && (
                    <Box mt={2}>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          <strong>{t('campaigns.selectedSector', 'Selected Sector')}:</strong> {selectedSector.sector_name}
                        </Typography>
                        {selectedSector.prompt_ready_replacement_line && (
                          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                            {selectedSector.prompt_ready_replacement_line}
                          </Typography>
                        )}
                      </Alert>
                    </Box>
                  )}
                </Grid>

                {/* Campaign Name */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <TextField
                    fullWidth
                    label={t('campaigns.campaignName', 'Campaign Name')}
                    value={campaignData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    required
                    helperText={t('campaigns.campaignNameHelp', 'Give your campaign a descriptive name')}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <BusinessIcon color="action" />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>

                {/* Max Results */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <TextField
                    fullWidth
                    type="number"
                    label={t('campaigns.maxResults', 'Maximum Results')}
                    value={campaignData.max_results}
                    onChange={(e) => handleInputChange('max_results', parseInt(e.target.value))}
                    required
                    inputProps={{ min: 5, max: 100 }}
                    helperText={t('campaigns.maxResultsHelp', 'Number of leads to generate (5-100)')}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <TargetIcon color="action" />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>

                {/* Location */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <TextField
                    fullWidth
                    label={t('campaigns.postcode', 'Postcode')}
                    value={campaignData.postcode}
                    onChange={(e) => handleInputChange('postcode', e.target.value)}
                    required
                    placeholder="LE1 6RP"
                    helperText={t('campaigns.postcodeHelp', 'UK postcode for location-based search')}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <LocationIcon color="action" />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>

                {/* Distance */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <TextField
                    fullWidth
                    type="number"
                    label={t('campaigns.distance', 'Search Distance')}
                    value={campaignData.distance_miles}
                    onChange={(e) => handleInputChange('distance_miles', parseInt(e.target.value))}
                    required
                    inputProps={{ min: 5, max: 200 }}
                    helperText={t('campaigns.distanceHelp', 'Search radius in miles (5-200)')}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SpeedIcon color="action" />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>

                {/* Company Size Category */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <FormControl fullWidth>
                    <InputLabel>Company Size (Optional)</InputLabel>
                    <Select
                      value={campaignData.company_size_category || ''}
                      onChange={(e) => handleInputChange('company_size_category', e.target.value || undefined)}
                      label="Company Size (Optional)"
                    >
                      <MenuItem value="">
                        <em>Any Size</em>
                      </MenuItem>
                      <MenuItem value="Micro">Micro (0-9 employees)</MenuItem>
                      <MenuItem value="Small">Small (10-49 employees)</MenuItem>
                      <MenuItem value="Medium">Medium (50-249 employees)</MenuItem>
                      <MenuItem value="Large">Large (250+ employees)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {/* Submit Buttons - Move to Top */}
                <Grid size={12}>
                  <Divider sx={{ my: 2 }} />
                  <Box display="flex" gap={2} justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/campaigns')}
                      disabled={submitting}
                    >
                      {t('common.cancel', 'Cancel')}
                    </Button>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={submitting || !campaignData.name || !campaignData.sector_name}
                      startIcon={submitting ? <CircularProgress size={20} /> : <SearchIcon />}
                      size="large"
                    >
                      {submitting ? t('campaigns.creating', 'Creating...') : t('campaigns.createCampaign', 'Create Campaign')}
                    </Button>
                  </Box>
                </Grid>


                {/* Description */}
                <Grid size={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label={t('campaigns.description', 'Description')}
                    value={campaignData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    helperText={t('campaigns.descriptionHelp', 'Optional description for this campaign')}
                  />
                </Grid>

                {/* Advanced Options */}
                <Grid size={12}>
                  <Divider sx={{ my: 2 }} />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showAdvanced}
                        onChange={(e) => setShowAdvanced(e.target.checked)}
                      />
                    }
                    label={
                      <Box display="flex" alignItems="center">
                        <Typography variant="body1">
                          {t('campaigns.advancedOptions', 'Advanced Options')}
                        </Typography>
                        <Tooltip title={t('campaigns.advancedOptionsTooltip', 'Configure additional campaign parameters')}>
                          <InfoIcon sx={{ ml: 1, fontSize: 16, color: 'action.active' }} />
                        </Tooltip>
                      </Box>
                    }
                  />
                </Grid>

                {showAdvanced && (
                  <>
                    <Grid
                      size={{
                        xs: 12,
                        md: 6
                      }}>
                      <FormControl fullWidth>
                        <InputLabel>{t('campaigns.promptType', 'Prompt Type')}</InputLabel>
                        <Select
                          value={campaignData.prompt_type}
                          onChange={(e) => handleInputChange('prompt_type', e.target.value)}
                          label={t('campaigns.promptType', 'Prompt Type')}
                        >
                          <MenuItem value="sector_search">
                            <Box>
                              <Typography variant="body1">{t('campaigns.sectorSearch', 'Sector Search')}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {t('campaigns.sectorSearchDesc', 'Find businesses in specific sector')}
                              </Typography>
                            </Box>
                          </MenuItem>
                          <MenuItem value="custom_search">
                            <Box>
                              <Typography variant="body1">{t('campaigns.customSearch', 'Custom Search')}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {t('campaigns.customSearchDesc', 'Use custom search criteria')}
                              </Typography>
                            </Box>
                          </MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    {campaignData.prompt_type === 'custom_search' && (
                      <Grid size={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={4}
                          label={t('campaigns.customPrompt', 'Custom Search Prompt')}
                          value={campaignData.custom_prompt}
                          onChange={(e) => handleInputChange('custom_prompt', e.target.value)}
                          helperText={t('campaigns.customPromptHelp', 'Describe what type of businesses you want to find')}
                          placeholder={t('campaigns.customPromptPlaceholder', 'e.g., Find IT companies that could benefit from our cabling services...')}
                        />
                      </Grid>
                    )}

                    {/* Deduplication Options */}
                    <Grid size={12}>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        ­ƒÜ½ {t('campaigns.deduplicationOptions', 'Deduplication Options')}
                      </Typography>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="caption" display="block">
                          <strong>{t('campaigns.preventDuplicateLeads', 'Prevent duplicate leads')}</strong> by checking against existing data
                        </Typography>
                      </Alert>
                      
                      <Grid container spacing={2}>
                        <Grid
                          size={{
                            xs: 12,
                            md: 6
                          }}>
                          <FormControlLabel
                            control={<Switch defaultChecked color="primary" />}
                            label={t('campaigns.checkExistingCustomers', 'Check Existing Customers')}
                            labelPlacement="end"
                          />
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('campaigns.skipBusinessesInCrm', 'Skip businesses already in CRM')}
                          </Typography>
                        </Grid>
                        
                        <Grid
                          size={{
                            xs: 12,
                            md: 6
                          }}>
                          <FormControlLabel
                            control={<Switch defaultChecked color="primary" />}
                            label={t('campaigns.checkExistingLeads', 'Check Existing Leads')}
                            labelPlacement="end"
                          />
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('campaigns.skipBusinessesInLeads', 'Skip businesses already in leads database')}
                          </Typography>
                        </Grid>
                        
                        <Grid
                          size={{
                            xs: 12,
                            md: 6
                          }}>
                          <FormControlLabel
                            control={<Switch defaultChecked={false} color="primary" />}
                            label={t('campaigns.checkCompanyNames', 'Check Company Names')}
                            labelPlacement="end"
                          />
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('campaigns.skipSimilarNames', 'Skip similar company names (fuzzy matching)')}
                          </Typography>
                        </Grid>
                        
                        <Grid
                          size={{
                            xs: 12,
                            md: 6
                          }}>
                          <FormControlLabel
                            control={<Switch defaultChecked color="primary" />}
                            label={t('campaigns.checkEmailAddresses', 'Check Email Addresses')}
                            labelPlacement="end"
                          />
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('campaigns.skipKnownEmails', 'Skip businesses with known email addresses')}
                          </Typography>
                        </Grid>
                        
                        <Grid
                          size={{
                            xs: 12,
                            md: 6
                          }}>
                          <FormControlLabel
                            control={<Switch defaultChecked={false} color="primary" />}
                            label={t('campaigns.checkPhoneNumbers', 'Check Phone Numbers')}
                            labelPlacement="end"
                          />
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('campaigns.skipKnownPhones', 'Skip businesses with known phone numbers')}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Grid>
                  </>
                )}
              </Grid>
            </form>
          </Paper>
        </Grid>

        {/* Info Panel */}
        <Grid
          size={{
            xs: 12,
            lg: 4
          }}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('campaigns.howItWorks', 'How It Works')}
            </Typography>
            
            <Box mb={3}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SearchIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">
                      {t('campaigns.step1', '1. AI Web Search')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('campaigns.step1Desc', 'Our AI searches the web for real UK businesses in your target sector and location')}
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            <Box mb={3}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <PublicIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">
                      {t('campaigns.step2', '2. Data Verification')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('campaigns.step2Desc', 'Each business is verified using Google Maps and Companies House for accuracy')}
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            <Box mb={3}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <BusinessIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">
                      {t('campaigns.step3', '3. AI Analysis')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('campaigns.step3Desc', 'Comprehensive analysis including telesales summaries and business intelligence')}
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            {selectedSector && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  {t('campaigns.sectorInfo', 'Sector Information')}
                </Typography>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {t('campaigns.exampleKeywords', 'Example Keywords:')}
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {selectedSector.example_keywords.split('\n').slice(0, 5).map((keyword, index) => (
                      <Chip
                        key={index}
                        label={keyword.replace('ÔÇó', '').trim()}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
                
                {selectedSector.example_companies && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {t('campaigns.exampleCompanies', 'Example Companies:')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      {selectedSector.example_companies.substring(0, 200)}...
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CampaignCreate;
