import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Business as BusinessIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface CustomerFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (customer: any) => void;
  customer?: any;
}

interface AIAnalysis {
  company_overview?: string;
  industry_analysis?: string;
  size_assessment?: string;
  growth_potential?: string;
  it_needs_assessment?: string;
  lead_score?: number;
  decision_makers?: string[];
  competitive_advantages?: string[];
  risk_factors?: string[];
  recommended_approach?: string;
  next_steps?: string[];
  opportunities?: string[];
  urgency?: string;
  budget_estimate?: string;
  timeline?: string;
}

const CustomerForm: React.FC<CustomerFormProps> = ({ open, onClose, onSave, customer }) => {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    website: '',
    company_name: '',
    company_number: '',
    industry: '',
    description: ''
  });
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searching, setSearching] = useState(false);

  // Simplified - just basic info, AI analysis happens AFTER customer is created
  const steps = ['Customer Information'];

  useEffect(() => {
    if (customer) {
      setFormData({
        name: customer.name || '',
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
        website: customer.website || '',
        company_name: customer.company_name || '',
        company_number: customer.company_number || '',
        industry: customer.industry || '',
        description: customer.description || ''
      });
    }
  }, [customer]);

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const searchCompany = async () => {
    if (!formData.company_name.trim()) {
      setError('Please enter a company name to search');
      return;
    }

    setSearching(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/ai-analysis/analyze-company', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          company_name: formData.company_name,
          company_number: formData.company_number || undefined
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze company');
      }

      const result = await response.json();
      
      if (result.success && result.analysis) {
        setAiAnalysis(result.analysis);
        
        // Auto-fill form with AI insights
        if (result.analysis.industry_analysis) {
          setFormData(prev => ({
            ...prev,
            industry: result.analysis.industry_analysis
          }));
        }
        
        if (result.source_data?.companies_house?.company_profile) {
          const companyProfile = result.source_data.companies_house.company_profile;
          setFormData(prev => ({
            ...prev,
            company_number: companyProfile.company_number || prev.company_number,
            address: companyProfile.registered_office_address?.address_line_1 || prev.address
          }));
        }
        
        handleNext(); // Move to AI analysis step
      } else {
        setError(result.error || 'Failed to analyze company');
      }
    } catch (err) {
      setError(`Error: ${err}`);
    } finally {
      setSearching(false);
    }
  };

  const handleSave = async () => {
    // Map frontend field names to backend schema - simple version
    const customerData = {
      company_name: formData.company_name ||formData.name,
      website: formData.website,
      main_email: formData.email,
      main_phone: formData.phone,
      billing_address: formData.address,
      description: formData.description
    };
    
    onSave(customerData);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Customer Name"
                value={formData.name}
                onChange={handleInputChange('name')}
                required
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Company Name"
                value={formData.company_name}
                onChange={handleInputChange('company_name')}
                required
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={handleInputChange('phone')}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                label="Address"
                value={formData.address}
                onChange={handleInputChange('address')}
                multiline
                rows={2}
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Website"
                value={formData.website}
                onChange={handleInputChange('website')}
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Company Number"
                value={formData.company_number}
                onChange={handleInputChange('company_number')}
                placeholder="e.g., 12345678"
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                label="Industry"
                value={formData.industry}
                onChange={handleInputChange('industry')}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={handleInputChange('description')}
                multiline
                rows={3}
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <BusinessIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Company Search & Analysis</Typography>
            </Box>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                fullWidth
                label="Company Name"
                value={formData.company_name}
                onChange={handleInputChange('company_name')}
                placeholder="Enter company name to search"
              />
              <Button
                variant="contained"
                onClick={searchCompany}
                disabled={searching || !formData.company_name.trim()}
                startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
              >
                {searching ? 'Searching...' : 'Search & Analyze'}
              </Button>
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              This will search Companies House and Google Maps to gather comprehensive company data,
              then use AI to analyze the company for structured cabling opportunities.
            </Alert>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <AssessmentIcon sx={{ mr: 1 }} />
              <Typography variant="h6">AI Analysis Results</Typography>
            </Box>
            {aiAnalysis ? (
              <Grid container spacing={3}>
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Lead Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Chip
                          label={`${aiAnalysis.lead_score || 0}/100`}
                          color={getScoreColor(aiAnalysis.lead_score || 0)}
                          size="medium"
                        />
                        <Chip
                          label={aiAnalysis.urgency || 'Unknown'}
                          color={getUrgencyColor(aiAnalysis.urgency || '')}
                          sx={{ ml: 1 }}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {aiAnalysis.company_overview || 'No overview available'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Company Details
                      </Typography>
                      <Typography variant="body2">
                        <strong>Industry:</strong> {aiAnalysis.industry_analysis || 'Not specified'}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Size:</strong> {aiAnalysis.size_assessment || 'Not specified'}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Growth:</strong> {aiAnalysis.growth_potential || 'Not specified'}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Budget:</strong> {aiAnalysis.budget_estimate || 'Not specified'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        IT Infrastructure Needs
                      </Typography>
                      <Typography variant="body2">
                        {aiAnalysis.it_needs_assessment || 'No assessment available'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Opportunities
                      </Typography>
                      {aiAnalysis.opportunities?.map((opportunity, index) => (
                        <Chip
                          key={index}
                          label={opportunity}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )) || <Typography variant="body2">No opportunities identified</Typography>}
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Risk Factors
                      </Typography>
                      {aiAnalysis.risk_factors?.map((risk, index) => (
                        <Chip
                          key={index}
                          label={risk}
                          size="small"
                          color="warning"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )) || <Typography variant="body2">No risk factors identified</Typography>}
                    </CardContent>
                  </Card>
                </Grid>
                
                {aiAnalysis.recommended_approach && (
                  <Grid size={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Recommended Approach
                        </Typography>
                        <Typography variant="body2">
                          {aiAnalysis.recommended_approach}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
            ) : (
              <Alert severity="info">
                Please complete the company search step first to see AI analysis results.
              </Alert>
            )}
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Customer Information
            </Typography>
            <Grid container spacing={2}>
              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Typography variant="subtitle2">Customer Name:</Typography>
                <Typography>{formData.name}</Typography>
              </Grid>
              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Typography variant="subtitle2">Company:</Typography>
                <Typography>{formData.company_name}</Typography>
              </Grid>
              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Typography variant="subtitle2">Email:</Typography>
                <Typography>{formData.email}</Typography>
              </Grid>
              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Typography variant="subtitle2">Phone:</Typography>
                <Typography>{formData.phone}</Typography>
              </Grid>
              {aiAnalysis && (
                <>
                  <Grid size={12}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6">AI Analysis Summary</Typography>
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="subtitle2">Lead Score:</Typography>
                    <Chip
                      label={`${aiAnalysis.lead_score || 0}/100`}
                      color={getScoreColor(aiAnalysis.lead_score || 0)}
                    />
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="subtitle2">Urgency:</Typography>
                    <Chip
                      label={aiAnalysis.urgency || 'Unknown'}
                      color={getUrgencyColor(aiAnalysis.urgency || '')}
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        {customer ? 'Edit Customer' : 'Add New Customer'}
        <Stepper activeStep={activeStep} sx={{ mt: 2 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {renderStepContent(activeStep)}
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        {activeStep > 0 && (
          <Button onClick={handleBack}>Back</Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext}>
            Next
          </Button>
        ) : (
          <Button variant="contained" onClick={handleSave}>
            Save Customer
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default CustomerForm;
