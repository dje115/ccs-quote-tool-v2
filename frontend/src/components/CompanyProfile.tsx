import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Divider,
  Chip,
  Stack,
  Paper,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Save as SaveIcon,
  Business as BusinessIcon,
  Add as AddIcon,
  Psychology as AiIcon,
  Language as WebsiteIcon,
  Phone as PhoneIcon,
  Inventory as ProductIcon,
  EmojiObjects as IdeaIcon,
  TrendingUp as TrendingIcon,
  Campaign as CampaignIcon,
  Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon,
  AutoAwesome as SparkleIcon
} from '@mui/icons-material';
import { settingsAPI } from '../services/api';

interface ProfileData {
  company_name: string;
  company_address: string;
  company_phone_numbers: string[];
  company_email_addresses: Array<{email: string, is_default: boolean}>;
  company_contact_names: Array<{name: string, is_default: boolean}>;
  company_description: string;
  company_websites: string[];
  products_services: string[];
  unique_selling_points: string[];
  target_markets: string[];
  sales_methodology: string;
  elevator_pitch: string;
  logo_url: string;
  logo_text: string;
  use_text_logo: boolean;
  website_keywords: Record<string, string[]>;
}

const CompanyProfile: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [autoFilling, setAutoFilling] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisDate, setAnalysisDate] = useState<string | null>(null);
  const [autoFillResults, setAutoFillResults] = useState<any>(null);

  const [profile, setProfile] = useState<ProfileData>({
    company_name: '',
    company_address: '',
    company_phone_numbers: [],
    company_email_addresses: [],
    company_contact_names: [],
    company_description: '',
    company_websites: [],
    products_services: [],
    unique_selling_points: [],
    target_markets: [],
    sales_methodology: '',
    elevator_pitch: '',
    logo_url: '',
    logo_text: '',
    use_text_logo: false,
    website_keywords: {}
  });

  // Input fields
  const [newWebsite, setNewWebsite] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newProduct, setNewProduct] = useState('');
  const [newUSP, setNewUSP] = useState('');
  const [newMarket, setNewMarket] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await settingsAPI.get('/company-profile');
      const data = response.data;
      
      setProfile({
        company_name: data.company_name || '',
        company_address: data.company_address || '',
        company_phone_numbers: Array.isArray(data.company_phone_numbers) ? data.company_phone_numbers : [],
        company_email_addresses: Array.isArray(data.company_email_addresses) ? data.company_email_addresses : [],
        company_contact_names: Array.isArray(data.company_contact_names) ? data.company_contact_names : [],
        company_description: data.company_description || '',
        company_websites: Array.isArray(data.company_websites) ? data.company_websites : [],
        products_services: Array.isArray(data.products_services) ? data.products_services : [],
        unique_selling_points: Array.isArray(data.unique_selling_points) ? data.unique_selling_points : [],
        target_markets: Array.isArray(data.target_markets) ? data.target_markets : [],
        sales_methodology: data.sales_methodology || '',
        elevator_pitch: data.elevator_pitch || '',
        logo_url: data.logo_url || '',
        logo_text: data.logo_text || '',
        use_text_logo: data.use_text_logo || false,
        website_keywords: data.website_keywords || {}
      });
      
      setAnalysis(data.company_analysis);
      setAnalysisDate(data.company_analysis_date);
    } catch (err: any) {
      console.error('Failed to load profile:', err);
      setError('Failed to load company profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeCompany = async () => {
    console.log('[handleAnalyzeCompany] Starting company analysis...');
    try {
      setAnalyzing(true);
      setError('');
      
      console.log('[handleAnalyzeCompany] Calling API endpoint /company-profile/analyze');
      const response = await settingsAPI.post('/company-profile/analyze');
      console.log('[handleAnalyzeCompany] API response received:', response.data);
      
      if (response.data.success) {
        setSuccess('AI analysis completed successfully!');
        setAnalysis(response.data.analysis);
        setAnalysisDate(response.data.analysis_date);
        console.log('[handleAnalyzeCompany] Analysis data set:', response.data.analysis);
      setTimeout(() => setSuccess(''), 3000);
      } else {
        console.warn('[handleAnalyzeCompany] API returned success=false');
        setError('Analysis completed but returned no data');
      }
    } catch (err: any) {
      console.error('[handleAnalyzeCompany] Error:', err);
      console.error('[handleAnalyzeCompany] Error details:', err.response?.data || err.message);
      setError(err.response?.data?.detail || 'Failed to analyze company profile. Please ensure your OpenAI API key is configured.');
    } finally {
      setAnalyzing(false);
      console.log('[handleAnalyzeCompany] Analysis complete, analyzing=false');
    }
  };

  const handleAutoFill = async () => {
    try {
      setAutoFilling(true);
      setError('');
      
      if (!profile.company_name) {
        setError('Please enter your company name first');
        setAutoFilling(false);
        return;
      }
      
      if (!profile.company_websites || profile.company_websites.length === 0) {
        setError('Please add at least one company website for AI to analyze');
        setAutoFilling(false);
        return;
      }
      
      const response = await settingsAPI.post('/company-profile/auto-fill');
      const apiResponse = response.data;
      const data = apiResponse.data; // The nested data object
      
      console.log('AI Auto-Fill Response:', apiResponse);
      console.log('AI Data:', data);
      
      // Store the full auto-fill results INCLUDING the data
      setAutoFillResults({
        confidence_score: apiResponse.confidence_score || 0,
        sources: apiResponse.sources || [],
        keywords: data.keywords || [],
        linkedin_url: data.linkedin_url,
        social_media_links: data.social_media_links || {},
        // Store the NEW data from AI (don't apply to profile yet)
        ai_data: {
          company_description: data.company_description || '',
          products_services: data.products_services || [],
          unique_selling_points: data.unique_selling_points || [],
          target_markets: data.target_markets || [],
          sales_methodology: data.sales_methodology || '',
          elevator_pitch: data.elevator_pitch || '',
          company_phone_numbers: data.company_phone_numbers || [],
          company_email_addresses: data.company_email_addresses || [],
          company_address: data.company_address || '',
          website_keywords: data.website_keywords || {}
        }
      });
      
      setSuccess(`AI auto-fill completed with ${apiResponse.confidence_score}% confidence! Review the suggested data below. Changes are NOT saved yet - you can accept, merge, or discard each section individually.`);
      setTimeout(() => setSuccess(''), 8000);
    } catch (err: any) {
      console.error('Failed to auto-fill:', err);
      setError('Failed to auto-fill profile. Please ensure your OpenAI API key is configured and you have added your company website.');
    } finally {
      setAutoFilling(false);
    }
  };

  const applySectionSuggestion = (field: string, action: 'replace' | 'merge' | 'discard') => {
    if (!autoFillResults || !autoFillResults.ai_data) return;
    
    const aiData = autoFillResults.ai_data;
    
    setProfile(prev => {
      if (action === 'discard') {
        // Keep existing data, do nothing
        return prev;
      } else if (action === 'replace') {
        // Replace with AI data
        return {
          ...prev,
          [field]: aiData[field as keyof typeof aiData]
        };
      } else if (action === 'merge') {
        // Merge arrays or replace strings
        const currentValue = prev[field as keyof typeof prev];
        const aiValue = aiData[field as keyof typeof aiData];
        
        if (Array.isArray(currentValue) && Array.isArray(aiValue)) {
          // Merge arrays, remove duplicates
          return {
            ...prev,
            [field]: [...new Set([...currentValue, ...aiValue])]
          };
        } else if (typeof currentValue === 'object' && typeof aiValue === 'object') {
          // Merge objects (like website_keywords)
          return {
            ...prev,
            [field]: { ...currentValue, ...aiValue }
          };
        } else {
          // For strings, replace (merge doesn't make sense)
          return {
            ...prev,
            [field]: aiValue || currentValue
          };
        }
      }
      return prev;
    });
    
    setSuccess(`Updated ${field.replace(/_/g, ' ')}! Remember to click "Save Company Profile" to persist changes.`);
    setTimeout(() => setSuccess(''), 3000);
  };

  const applyAllSuggestions = (action: 'replace' | 'merge') => {
    if (!autoFillResults || !autoFillResults.ai_data) return;
    
    const aiData = autoFillResults.ai_data;
    
    if (action === 'replace') {
      setProfile(prev => ({
        ...prev,
        company_description: aiData.company_description || prev.company_description,
        products_services: aiData.products_services || [],
        unique_selling_points: aiData.unique_selling_points || [],
        target_markets: aiData.target_markets || [],
        sales_methodology: aiData.sales_methodology || prev.sales_methodology,
        elevator_pitch: aiData.elevator_pitch || prev.elevator_pitch,
        company_phone_numbers: aiData.company_phone_numbers || prev.company_phone_numbers,
        company_email_addresses: aiData.company_email_addresses || prev.company_email_addresses,
        company_address: aiData.company_address || prev.company_address,
        website_keywords: aiData.website_keywords || prev.website_keywords
      }));
      setSuccess('All AI suggestions applied! Click "Save Company Profile" to save changes.');
    } else if (action === 'merge') {
      setProfile(prev => ({
        ...prev,
        company_description: aiData.company_description || prev.company_description,
        products_services: [...new Set([...prev.products_services, ...(aiData.products_services || [])])],
        unique_selling_points: [...new Set([...prev.unique_selling_points, ...(aiData.unique_selling_points || [])])],
        target_markets: [...new Set([...prev.target_markets, ...(aiData.target_markets || [])])],
        sales_methodology: aiData.sales_methodology || prev.sales_methodology,
        elevator_pitch: aiData.elevator_pitch || prev.elevator_pitch,
        company_phone_numbers: [...new Set([...prev.company_phone_numbers, ...(aiData.company_phone_numbers || [])])],
        company_email_addresses: [...prev.company_email_addresses, ...(aiData.company_email_addresses || [])],
        company_address: aiData.company_address || prev.company_address,
        website_keywords: { ...prev.website_keywords, ...aiData.website_keywords }
      }));
      setSuccess('All AI suggestions merged! Click "Save Company Profile" to save changes.');
    }
    
    setAutoFillResults(null);
    setTimeout(() => setSuccess(''), 5000);
  };

  const discardAllSuggestions = () => {
    setAutoFillResults(null);
    setSuccess('AI suggestions discarded.');
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      setError('');
      await settingsAPI.put('/company-profile', profile);
      setSuccess('Profile saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to save profile:', err);
      setError('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const addWebsite = () => {
    if (newWebsite.trim()) {
      let url = newWebsite.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
      }
      setProfile(prev => ({
        ...prev,
        company_websites: [...prev.company_websites, url]
      }));
      setNewWebsite('');
    }
  };

  const removeWebsite = (index: number) => {
    setProfile(prev => ({
      ...prev,
      company_websites: prev.company_websites.filter((_, i) => i !== index)
    }));
  };

  const addPhone = () => {
    if (newPhone.trim()) {
      setProfile(prev => ({
        ...prev,
        company_phone_numbers: [...prev.company_phone_numbers, newPhone.trim()]
      }));
      setNewPhone('');
    }
  };

  const removePhone = (index: number) => {
    setProfile(prev => ({
      ...prev,
      company_phone_numbers: prev.company_phone_numbers.filter((_, i) => i !== index)
    }));
  };

  const addProduct = () => {
    if (newProduct.trim()) {
      setProfile(prev => ({
        ...prev,
        products_services: [...prev.products_services, newProduct.trim()]
      }));
      setNewProduct('');
    }
  };

  const removeProduct = (index: number) => {
    setProfile(prev => ({
      ...prev,
      products_services: prev.products_services.filter((_, i) => i !== index)
    }));
  };

  const addUSP = () => {
    if (newUSP.trim()) {
      setProfile(prev => ({
        ...prev,
        unique_selling_points: [...prev.unique_selling_points, newUSP.trim()]
      }));
      setNewUSP('');
    }
  };

  const removeUSP = (index: number) => {
    setProfile(prev => ({
      ...prev,
      unique_selling_points: prev.unique_selling_points.filter((_, i) => i !== index)
    }));
  };

  const addMarket = () => {
    if (newMarket.trim()) {
      setProfile(prev => ({
        ...prev,
        target_markets: [...prev.target_markets, newMarket.trim()]
      }));
      setNewMarket('');
    }
  };

  const removeMarket = (index: number) => {
    setProfile(prev => ({
      ...prev,
      target_markets: prev.target_markets.filter((_, i) => i !== index)
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* AI Tools Section - Prominent at top */}
        <Grid item xs={12}>
          <Paper 
            elevation={3} 
            sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              p: 3,
              borderRadius: 2
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SparkleIcon sx={{ fontSize: 32, mr: 1 }} />
              <Typography variant="h5" fontWeight="bold">
                AI-Powered Profile Assistant
        </Typography>
      </Box>
            <Typography variant="body1" sx={{ mb: 3, opacity: 0.95 }}>
              Let AI analyze your website and automatically generate your company profile data
            </Typography>
            <Button
              variant="contained"
              size="large"
              sx={{ 
                bgcolor: 'white', 
                color: 'primary.main',
                fontWeight: 'bold',
                '&:hover': { bgcolor: 'grey.100' }
              }}
              startIcon={autoFilling ? <CircularProgress size={20} /> : <SparkleIcon />}
              onClick={handleAutoFill}
              disabled={autoFilling}
            >
              {autoFilling ? 'Analyzing Website...' : 'AI AUTO-FILL PROFILE'}
            </Button>
          </Paper>
        </Grid>

        {/* AI Auto-Fill Results */}
        {autoFillResults && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: '#e8f5e9', borderLeft: 4, borderColor: 'success.main' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SparkleIcon color="success" />
                  AI Auto-Fill Results
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  Confidence Score: <Chip label={`${autoFillResults.confidence_score}%`} color="success" size="small" />
                </Typography>
                
                <Divider sx={{ my: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      Data Sources Used:
                    </Typography>
                    <Stack spacing={0.5}>
                      {autoFillResults.sources && Array.isArray(autoFillResults.sources) && autoFillResults.sources.map((source: string, idx: number) => (
                        <Typography key={idx} variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          • {source}
                        </Typography>
                      ))}
                      {(!autoFillResults.sources || !Array.isArray(autoFillResults.sources) || autoFillResults.sources.length === 0) && (
                        <Typography variant="body2" color="text.secondary" fontStyle="italic">
                          No sources information available
                        </Typography>
                      )}
                    </Stack>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      Social Media & Other Sources:
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {autoFillResults.linkedin_url && (
                        <Chip 
                          label="LinkedIn"
                          icon={<WebsiteIcon />}
                          component="a"
                          href={autoFillResults.linkedin_url}
                          target="_blank"
                          clickable
                          color="primary"
                          variant="filled"
                          size="medium"
                        />
                      )}
                      {autoFillResults.social_media_links && Object.entries(autoFillResults.social_media_links).map(([platform, url]: [string, any]) => (
                        <Chip 
                          key={platform}
                          label={platform.charAt(0).toUpperCase() + platform.slice(1)}
                          icon={<WebsiteIcon />}
                          component="a"
                          href={url}
                          target="_blank"
                          clickable
                          color="secondary"
                          variant="filled"
                          size="medium"
                        />
                      ))}
                      {(!autoFillResults.linkedin_url && (!autoFillResults.social_media_links || Object.keys(autoFillResults.social_media_links).length === 0)) && (
                        <Typography variant="body2" color="text.secondary" fontStyle="italic">
                          No social media links found on website
                        </Typography>
                      )}
                    </Stack>
                  </Grid>
                  
                  {autoFillResults.keywords && Array.isArray(autoFillResults.keywords) && autoFillResults.keywords.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Extracted SEO/Marketing Keywords ({autoFillResults.keywords.length}):
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {autoFillResults.keywords.map((keyword: string, idx: number) => (
                          <Chip key={idx} label={keyword} size="small" color="info" variant="outlined" />
                        ))}
                      </Stack>
                    </Grid>
                  )}
                </Grid>
                
                <Divider sx={{ my: 3 }} />
                
                {/* Section-by-Section Comparison */}
                {autoFillResults.ai_data && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom color="primary" sx={{ mb: 3 }}>
                      🔄 Review AI Suggestions (Section by Section)
                    </Typography>

                    {/* Global Actions */}
                    <Alert severity="info" sx={{ mb: 3 }}>
                      <Typography variant="body2" fontWeight="bold" gutterBottom>
                        Quick Actions - Apply to ALL Sections:
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        <Button 
                          size="small" 
                          variant="contained" 
                          color="primary"
                          onClick={() => applyAllSuggestions('replace')}
                        >
                          Replace All
                        </Button>
                        <Button 
                          size="small" 
                          variant="contained" 
                          color="success"
                          onClick={() => applyAllSuggestions('merge')}
                        >
                          Merge All
                        </Button>
                        <Button 
                          size="small" 
                          variant="outlined" 
                          color="error"
                          onClick={discardAllSuggestions}
                        >
                          Discard All
                        </Button>
                      </Stack>
        </Alert>

                    {/* Company Description */}
                    {autoFillResults.ai_data.company_description && (
                      <Paper elevation={2} sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: 'warning.main' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          📝 Company Description
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="text.secondary" fontWeight="bold">
                              CURRENT:
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, minHeight: 80 }}>
                              <Typography variant="body2">
                                {profile.company_description || <em style={{ color: '#999' }}>No description yet</em>}
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="primary" fontWeight="bold">
                              AI SUGGESTED:
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 1, minHeight: 80 }}>
                              <Typography variant="body2">
                                {autoFillResults.ai_data.company_description}
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                          <Button size="small" variant="contained" onClick={() => applySectionSuggestion('company_description', 'replace')}>
                            Use AI Version
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => applySectionSuggestion('company_description', 'discard')}>
                            Keep Current
                          </Button>
                        </Stack>
                      </Paper>
                    )}

                    {/* Products & Services */}
                    {autoFillResults.ai_data.products_services && autoFillResults.ai_data.products_services.length > 0 && (
                      <Paper elevation={2} sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: 'info.main' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          📦 Products & Services
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="text.secondary" fontWeight="bold">
                              CURRENT ({profile.products_services.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, minHeight: 80 }}>
                              {profile.products_services.length > 0 ? (
                                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                  {profile.products_services.map((item, idx) => (
                                    <Chip key={idx} label={item} size="small" />
                                  ))}
                                </Stack>
                              ) : (
                                <em style={{ color: '#999' }}>No products/services listed</em>
                              )}
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="primary" fontWeight="bold">
                              AI SUGGESTED ({autoFillResults.ai_data.products_services.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 1, minHeight: 80 }}>
                              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                {autoFillResults.ai_data.products_services.map((item: string, idx: number) => (
                                  <Chip key={idx} label={item} size="small" color="primary" variant="outlined" />
                                ))}
                              </Stack>
                            </Box>
                          </Grid>
                        </Grid>
                        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                          <Button size="small" variant="contained" onClick={() => applySectionSuggestion('products_services', 'replace')}>
                            Replace
                          </Button>
                          <Button size="small" variant="contained" color="success" onClick={() => applySectionSuggestion('products_services', 'merge')}>
                            Merge (Add New)
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => applySectionSuggestion('products_services', 'discard')}>
                            Keep Current
                          </Button>
                        </Stack>
                      </Paper>
                    )}

                    {/* Unique Selling Points */}
                    {autoFillResults.ai_data.unique_selling_points && autoFillResults.ai_data.unique_selling_points.length > 0 && (
                      <Paper elevation={2} sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: 'success.main' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          ⭐ Unique Selling Points
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="text.secondary" fontWeight="bold">
                              CURRENT ({profile.unique_selling_points.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, minHeight: 80 }}>
                              {profile.unique_selling_points.length > 0 ? (
                                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                  {profile.unique_selling_points.map((item, idx) => (
                                    <Chip key={idx} label={item} size="small" />
                                  ))}
                                </Stack>
                              ) : (
                                <em style={{ color: '#999' }}>No USPs listed</em>
                              )}
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="primary" fontWeight="bold">
                              AI SUGGESTED ({autoFillResults.ai_data.unique_selling_points.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#e8f5e9', borderRadius: 1, minHeight: 80 }}>
                              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                {autoFillResults.ai_data.unique_selling_points.map((item: string, idx: number) => (
                                  <Chip key={idx} label={item} size="small" color="success" variant="outlined" />
                                ))}
                              </Stack>
                            </Box>
                          </Grid>
                        </Grid>
                        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                          <Button size="small" variant="contained" onClick={() => applySectionSuggestion('unique_selling_points', 'replace')}>
                            Replace
                          </Button>
                          <Button size="small" variant="contained" color="success" onClick={() => applySectionSuggestion('unique_selling_points', 'merge')}>
                            Merge (Add New)
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => applySectionSuggestion('unique_selling_points', 'discard')}>
                            Keep Current
                          </Button>
                        </Stack>
                      </Paper>
                    )}

                    {/* Target Markets */}
                    {autoFillResults.ai_data.target_markets && autoFillResults.ai_data.target_markets.length > 0 && (
                      <Paper elevation={2} sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: 'secondary.main' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          🎯 Target Markets
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="text.secondary" fontWeight="bold">
                              CURRENT ({profile.target_markets.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, minHeight: 80 }}>
                              {profile.target_markets.length > 0 ? (
                                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                  {profile.target_markets.map((item, idx) => (
                                    <Chip key={idx} label={item} size="small" />
                                  ))}
                                </Stack>
                              ) : (
                                <em style={{ color: '#999' }}>No target markets listed</em>
                              )}
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="primary" fontWeight="bold">
                              AI SUGGESTED ({autoFillResults.ai_data.target_markets.length}):
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f3e5f5', borderRadius: 1, minHeight: 80 }}>
                              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                {autoFillResults.ai_data.target_markets.map((item: string, idx: number) => (
                                  <Chip key={idx} label={item} size="small" color="secondary" variant="outlined" />
                                ))}
                              </Stack>
                            </Box>
                          </Grid>
                        </Grid>
                        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                          <Button size="small" variant="contained" onClick={() => applySectionSuggestion('target_markets', 'replace')}>
                            Replace
                          </Button>
                          <Button size="small" variant="contained" color="success" onClick={() => applySectionSuggestion('target_markets', 'merge')}>
                            Merge (Add New)
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => applySectionSuggestion('target_markets', 'discard')}>
                            Keep Current
                          </Button>
                        </Stack>
                      </Paper>
                    )}

                    {/* Elevator Pitch */}
                    {autoFillResults.ai_data.elevator_pitch && (
                      <Paper elevation={2} sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: 'error.main' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          💼 Elevator Pitch
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="text.secondary" fontWeight="bold">
                              CURRENT:
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, minHeight: 80 }}>
                              <Typography variant="body2">
                                {profile.elevator_pitch || <em style={{ color: '#999' }}>No elevator pitch yet</em>}
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="caption" color="primary" fontWeight="bold">
                              AI SUGGESTED:
                            </Typography>
                            <Box sx={{ p: 2, bgcolor: '#ffebee', borderRadius: 1, minHeight: 80 }}>
                              <Typography variant="body2">
                                {autoFillResults.ai_data.elevator_pitch}
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                          <Button size="small" variant="contained" onClick={() => applySectionSuggestion('elevator_pitch', 'replace')}>
                            Use AI Version
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => applySectionSuggestion('elevator_pitch', 'discard')}>
                            Keep Current
                          </Button>
                        </Stack>
                      </Paper>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* AI Analysis Results */}
        {analysis && typeof analysis === 'object' && (
          <Grid item xs={12}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: '#e8f5e9' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AssessmentIcon color="success" />
                  <Typography variant="h6" fontWeight="bold" color="success.main">
                    AI Business Intelligence
                  </Typography>
                  <Chip 
                    label={analysisDate ? new Date(analysisDate).toLocaleDateString() : 'Recent'}
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
      <Grid container spacing={3}>
                  {analysis.business_model && typeof analysis.business_model === 'string' && (
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: '#fafafa' }}>
                        <Typography variant="subtitle1" fontWeight="bold" color="primary" gutterBottom>
                          Business Model
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {String(analysis.business_model)}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                  {analysis.competitive_position && typeof analysis.competitive_position === 'string' && (
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: '#fafafa' }}>
                        <Typography variant="subtitle1" fontWeight="bold" color="primary" gutterBottom>
                          Competitive Position
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {String(analysis.competitive_position)}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                  {analysis.ideal_customer_profile && typeof analysis.ideal_customer_profile === 'string' && (
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: '#fafafa' }}>
                        <Typography variant="subtitle1" fontWeight="bold" color="primary" gutterBottom>
                          Ideal Customer Profile
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {String(analysis.ideal_customer_profile)}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                  {analysis.sales_approach && typeof analysis.sales_approach === 'string' && (
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: '#fafafa' }}>
                        <Typography variant="subtitle1" fontWeight="bold" color="primary" gutterBottom>
                          Recommended Sales Approach
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {String(analysis.sales_approach)}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {/* Company Overview Section */}
        <Grid item xs={12}>
          <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                <BusinessIcon color="primary" />
            Company Overview
              </Typography>
          <Divider sx={{ mb: 3 }} />
        </Grid>
              
        {/* Company Description */}
                <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary">
                About Your Company
              </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    value={profile.company_description}
                    onChange={(e) => setProfile({ ...profile, company_description: e.target.value })}
                placeholder="Describe your company, what you do, and who you serve..."
                sx={{ mt: 1 }}
                variant="outlined"
                  />
            </CardContent>
          </Card>
                </Grid>
                
        {/* Contact Information Section */}
                <Grid item xs={12}>
          <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <WebsiteIcon color="primary" />
            Contact Information
          </Typography>
        </Grid>

        {/* Company Websites */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WebsiteIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">
                  Company Websites
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <TextField
                    fullWidth
                  size="small"
                  placeholder="www.example.com"
                  value={newWebsite}
                  onChange={(e) => setNewWebsite(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addWebsite()}
                />
                <Tooltip title="Add Website">
                  <Button variant="contained" onClick={addWebsite} disabled={!newWebsite.trim()}>
                    <AddIcon />
                  </Button>
                </Tooltip>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {profile.company_websites.map((website, index) => (
                  <Box key={index}>
                    <Chip
                      label={website}
                      onDelete={() => removeWebsite(index)}
                      color="primary"
                      variant="outlined"
                      clickable
                      onClick={() => window.open(website, '_blank')}
                    />
                    {profile.website_keywords && profile.website_keywords[website] && profile.website_keywords[website].length > 0 && (
                      <Box sx={{ mt: 1, ml: 1 }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Keywords for this site:
                        </Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                          {profile.website_keywords[website].slice(0, 5).map((keyword: string, kidx: number) => (
                            <Chip key={kidx} label={keyword} size="small" color="info" variant="filled" sx={{ height: 20, fontSize: '0.7rem' }} />
                          ))}
                          {profile.website_keywords[website].length > 5 && (
                            <Chip label={`+${profile.website_keywords[website].length - 5} more`} size="small" color="default" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                          )}
                        </Stack>
                      </Box>
                    )}
                  </Box>
                ))}
                {profile.company_websites.length === 0 && (
                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                    No websites added yet
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
                </Grid>
                
        {/* Phone Numbers */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PhoneIcon color="secondary" sx={{ mr: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">
                  Phone Numbers
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <TextField
                    fullWidth
                  size="small"
                  placeholder="+44 1234 567890"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addPhone()}
                />
                <Tooltip title="Add Phone">
                  <Button variant="contained" color="secondary" onClick={addPhone} disabled={!newPhone.trim()}>
                    <AddIcon />
                  </Button>
                </Tooltip>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {profile.company_phone_numbers.map((phone, index) => (
                  <Chip
                    key={index}
                    label={phone}
                    onDelete={() => removePhone(index)}
                    color="secondary"
                    variant="outlined"
                  />
                ))}
                {profile.company_phone_numbers.length === 0 && (
                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                    No phone numbers added yet
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
                </Grid>
                
        {/* Company Address */}
                <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Company Address
              </Typography>
                  <TextField
                    fullWidth
                multiline
                rows={2}
                value={profile.company_address}
                onChange={(e) => setProfile({ ...profile, company_address: e.target.value })}
                placeholder="Enter your company address"
                variant="outlined"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Business Intelligence Section */}
        <Grid item xs={12}>
          <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <TrendingIcon color="primary" />
            Business Intelligence
          </Typography>
        </Grid>

        {/* Products & Services */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ProductIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">
                Products & Services
              </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Add a product or service"
                  value={newProduct}
                  onChange={(e) => setNewProduct(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addProduct()}
                />
                <Button variant="contained" color="info" onClick={addProduct} disabled={!newProduct.trim()}>
                  <AddIcon />
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {profile.products_services.map((product, index) => (
                  <Chip
                    key={index}
                    label={product}
                    onDelete={() => removeProduct(index)}
                    color="info"
                    variant="filled"
                  />
                ))}
                {profile.products_services.length === 0 && (
                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                    No products or services added yet
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Unique Selling Points */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <IdeaIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">
                  Unique Selling Points
              </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="What makes you different?"
                  value={newUSP}
                  onChange={(e) => setNewUSP(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addUSP()}
                />
                <Button variant="contained" color="success" onClick={addUSP} disabled={!newUSP.trim()}>
                  <AddIcon />
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {profile.unique_selling_points.map((usp, index) => (
                  <Chip
                    key={index}
                    label={usp}
                    onDelete={() => removeUSP(index)}
                    color="success"
                    variant="filled"
                  />
                ))}
                {profile.unique_selling_points.length === 0 && (
                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                    No USPs added yet
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Target Markets */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CampaignIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">
                Target Markets
              </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Add target industry or sector"
                  value={newMarket}
                  onChange={(e) => setNewMarket(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addMarket()}
                />
                <Button variant="contained" color="warning" onClick={addMarket} disabled={!newMarket.trim()}>
                  <AddIcon />
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {profile.target_markets.map((market, index) => (
                  <Chip
                    key={index}
                    label={market}
                    onDelete={() => removeMarket(index)}
                    color="warning"
                    variant="filled"
                  />
                ))}
                {profile.target_markets.length === 0 && (
                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                    No target markets added yet
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Sales Strategy Section */}
        <Grid item xs={12}>
          <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <CampaignIcon color="primary" />
            Sales Strategy
          </Typography>
        </Grid>

        {/* Sales Methodology */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
                Sales Methodology
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Describe your sales process, approach, and methodologies
              </Typography>
              <TextField
            fullWidth
                multiline
                rows={3}
                value={profile.sales_methodology}
                onChange={(e) => setProfile({ ...profile, sales_methodology: e.target.value })}
                placeholder="e.g., Consultative selling, SPIN, Challenger, Solution selling..."
                variant="outlined"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Elevator Pitch */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
                Elevator Pitch
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Your 30-second pitch - what do you do and why should customers care?
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={profile.elevator_pitch}
                onChange={(e) => setProfile({ ...profile, elevator_pitch: e.target.value })}
                placeholder="In 30 seconds, what makes your company special?"
                variant="outlined"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button - Sticky at bottom */}
          <Grid item xs={12}>
          <Paper 
            elevation={4} 
            sx={{ 
              p: 2, 
              mt: 3,
              position: 'sticky',
              bottom: 16,
              bgcolor: 'background.paper',
              borderRadius: 2
            }}
          >
              <Button
                variant="contained"
              color="primary"
                size="large"
              startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              onClick={handleSaveProfile}
              disabled={saving}
              fullWidth
              sx={{ 
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 'bold'
              }}
            >
              {saving ? 'Saving Profile...' : 'Save Company Profile'}
              </Button>
          </Paper>
        </Grid>
          </Grid>
    </Box>
  );
};

export default CompanyProfile;
