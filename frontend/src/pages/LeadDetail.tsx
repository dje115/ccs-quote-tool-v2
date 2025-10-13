import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
  Divider,
  IconButton,
  Alert
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Business as BusinessIcon,
  TrendingUp as ConvertIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { campaignAPI, customerAPI } from '../services/api';

const LeadDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lead, setLead] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (id) {
      loadLead();
    }
  }, [id]);

  const loadLead = async () => {
    try {
      setLoading(true);
      // Fetch from campaigns API - this is a discovery/campaign lead
      // We need to get all leads and find the one with this ID
      const response = await campaignAPI.listAllLeads();
      const foundLead = response.data.find((l: any) => l.id === id);
      setLead(foundLead);
    } catch (error) {
      console.error('Error loading discovery:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToLead = async () => {
    if (!lead) return;

    if (!window.confirm('Convert this discovery to a CRM lead? This will create a new customer record in the CRM.')) {
      return;
    }

    setConverting(true);
    try {
      // Use the campaign API convert endpoint
      const response = await campaignAPI.convertLead(lead.id);
      
      alert('Discovery converted to CRM lead successfully!');
      
      // Navigate to the new customer record
      if (response.data?.customer_id) {
        navigate(`/customers/${response.data.customer_id}`);
      } else {
        navigate('/customers');
      }
    } catch (error) {
      console.error('Error converting discovery:', error);
      alert('Failed to convert discovery to CRM lead');
    } finally {
      setConverting(false);
    }
  };

  const handleRunAIAnalysis = async () => {
    if (!lead) return;

    if (!window.confirm('Run AI analysis on this discovery? This will analyze the company using all available data.')) {
      return;
    }

    setAnalyzing(true);
    try {
      const response = await campaignAPI.analyzeLead(lead.id);
      
      if (response.data?.success) {
        alert('AI analysis completed successfully!');
        // Reload lead to get updated analysis
        loadLead();
      } else {
        alert(`AI analysis failed: ${response.data?.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('Error running AI analysis:', error);
      alert(`Failed to run AI analysis: ${error.response?.data?.detail || error.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  if (!lead) {
    return (
      <Container maxWidth="lg">
        <Typography>Lead not found</Typography>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new':
        return 'info';
      case 'contacted':
        return 'warning';
      case 'qualified':
        return 'success';
      case 'converted':
        return 'success';
      case 'disqualified':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/leads')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {lead.company_name}
        </Typography>
        {lead.status !== 'converted' && (
          <Button
            variant="contained"
            color="success"
            startIcon={<ConvertIcon />}
            onClick={handleConvertToLead}
            disabled={converting}
          >
            {converting ? 'Converting...' : 'Convert to CRM Lead'}
          </Button>
        )}
      </Box>

      {lead.status === 'converted' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          This discovery has been converted to a CRM lead
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Lead Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Company Information
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Business Sector
                    </Typography>
                    <Typography>{lead.business_sector || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Company Size
                    </Typography>
                    <Typography>{lead.company_size || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Postcode
                    </Typography>
                    <Typography>{lead.postcode || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              {lead.address && (
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <BusinessIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Address
                      </Typography>
                      <Typography>{lead.address}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Source
                    </Typography>
                    <Typography>{lead.source || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              {lead.campaign_name && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <BusinessIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Campaign
                      </Typography>
                      <Typography>{lead.campaign_name}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.website && (
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <WebsiteIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Website
                      </Typography>
                      <Typography>
                        <a href={lead.website} target="_blank" rel="noopener noreferrer">
                          {lead.website}
                        </a>
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.contact_email && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <EmailIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Email
                      </Typography>
                      <Typography>{lead.contact_email}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.contact_phone && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <PhoneIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Phone
                      </Typography>
                      <Typography>{lead.contact_phone}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.employee_count_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Employees (Estimate)
                  </Typography>
                  <Typography>{lead.employee_count_estimate}</Typography>
                </Grid>
              )}

              {lead.annual_revenue_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Annual Revenue (Estimate)
                  </Typography>
                  <Typography>£{lead.annual_revenue_estimate?.toLocaleString()}</Typography>
                </Grid>
              )}
            </Grid>

            {lead.description && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  Description
                </Typography>
                <Typography>{lead.description}</Typography>
              </Box>
            )}

            {lead.project_value && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Estimated Project Value
                </Typography>
                <Typography>{lead.project_value}</Typography>
              </Box>
            )}

            {lead.timeline && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Timeline
                </Typography>
                <Typography>{lead.timeline}</Typography>
              </Box>
            )}
          </Paper>

          {/* AI Analysis */}
          {lead.ai_analysis && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                AI Business Intelligence
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {typeof lead.ai_analysis === 'object' ? (
                <Box>
                  {lead.ai_analysis.company_profile && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Company Profile
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {lead.ai_analysis.company_profile}
                      </Typography>
                    </Box>
                  )}
                  
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    {lead.ai_analysis.business_sector && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Business Sector</Typography>
                        <Typography variant="body2">{lead.ai_analysis.business_sector}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.business_size_category && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Company Size</Typography>
                        <Typography variant="body2">{lead.ai_analysis.business_size_category}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.estimated_employees && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Estimated Employees</Typography>
                        <Typography variant="body2">{lead.ai_analysis.estimated_employees}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.estimated_revenue && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Estimated Revenue</Typography>
                        <Typography variant="body2">{lead.ai_analysis.estimated_revenue}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.technology_maturity && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Technology Maturity</Typography>
                        <Typography variant="body2">{lead.ai_analysis.technology_maturity}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.it_budget_estimate && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">IT Budget Estimate</Typography>
                        <Typography variant="body2">{lead.ai_analysis.it_budget_estimate}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.growth_potential && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">Growth Potential</Typography>
                        <Chip 
                          label={lead.ai_analysis.growth_potential} 
                          color={
                            lead.ai_analysis.growth_potential === 'High' ? 'success' : 
                            lead.ai_analysis.growth_potential === 'Medium' ? 'warning' : 'default'
                          }
                          size="small"
                        />
                      </Grid>
                    )}
                  </Grid>

                  {lead.ai_analysis.primary_business_activities && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Primary Business Activities
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.primary_business_activities}</Typography>
                    </Box>
                  )}

                  {lead.ai_analysis.financial_health_analysis && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Financial Health Analysis
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.financial_health_analysis}</Typography>
                    </Box>
                  )}

                  {lead.ai_analysis.technology_needs && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Technology Needs
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.technology_needs}</Typography>
                    </Box>
                  )}

                  {lead.ai_analysis.opportunities && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="success.main" gutterBottom>
                        Business Opportunities
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.opportunities}</Typography>
                    </Box>
                  )}

                  {lead.ai_analysis.competitors && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Competitive Landscape
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.competitors}</Typography>
                    </Box>
                  )}

                  {lead.ai_analysis.risks && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="error.main" gutterBottom>
                        Risk Factors
                      </Typography>
                      <Typography variant="body2">{lead.ai_analysis.risks}</Typography>
                    </Box>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {lead.ai_analysis}
                </Typography>
              )}
            </Paper>
          )}

          {/* External Data */}
          {lead.external_data && Object.keys(lead.external_data).length > 0 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Additional Data
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {lead.external_data.google_maps && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Google Maps Data</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    {lead.external_data.google_maps.rating && `Rating: ${lead.external_data.google_maps.rating} ⭐`}
                    {lead.external_data.google_maps.user_ratings_total && ` (${lead.external_data.google_maps.user_ratings_total} reviews)`}
                  </Typography>
                </Box>
              )}
              {lead.external_data.companies_house && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Companies House</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    {lead.external_data.companies_house.company_number && `Company Number: ${lead.external_data.companies_house.company_number}`}
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status
              </Typography>
              <Chip
                label={lead.status}
                color={getStatusColor(lead.status)}
                sx={{ mb: 2 }}
              />

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Lead Score
              </Typography>
              <Chip
                label={lead.lead_score || 0}
                color={lead.lead_score >= 70 ? 'success' : lead.lead_score >= 40 ? 'warning' : 'default'}
                sx={{ fontSize: '1.2rem', padding: '20px 12px' }}
              />

              <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                Created: {new Date(lead.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              {lead.status !== 'converted' && (
                <>
                  <Button
                    fullWidth
                    variant="contained"
                    color="success"
                    sx={{ mb: 1 }}
                    startIcon={<ConvertIcon />}
                    onClick={handleConvertToLead}
                    disabled={converting}
                  >
                    {converting ? 'Converting...' : 'Convert to CRM Lead'}
                  </Button>
                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    sx={{ mb: 1 }}
                    onClick={handleRunAIAnalysis}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    onClick={() => leadAPI.update(id!, { status: 'disqualified' })}
                  >
                    Disqualify
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default LeadDetail;

