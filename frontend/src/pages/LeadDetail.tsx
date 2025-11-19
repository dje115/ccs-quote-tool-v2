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
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Business as BusinessIcon,
  TrendingUp as ConvertIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { campaignAPI, customerAPI, leadAPI } from '../services/api';
import LeadIntelligence from '../components/LeadIntelligence';
import { useWebSocketContext } from '../contexts/WebSocketContext';

const LeadDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lead, setLead] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const { subscribe, isConnected } = useWebSocketContext();

  useEffect(() => {
    if (id) {
      loadLead();
    }
  }, [id]);

  // Subscribe to lead analysis events via WebSocket
  useEffect(() => {
    if (!isConnected || !id) return;

    // Subscribe to lead_analysis.started for this lead (updates status from 'queued' to 'running')
    const unsubscribeStarted = subscribe('lead_analysis.started', (event) => {
      if (event.data.lead_id === id) {
        console.log(`Lead analysis started for ${event.data.lead_name}`);
        setAnalysisStatus('running');
        setAnalysisTaskId(event.data.task_id);
      }
    });

    // Subscribe to lead_analysis.completed for this lead (reloads lead data)
    const unsubscribeCompleted = subscribe('lead_analysis.completed', (event) => {
      if (event.data.lead_id === id) {
        console.log(`Lead analysis completed for ${event.data.lead_name}`);
        setAnalysisStatus('completed');
        setAnalysisTaskId(null);
        // Reload lead to get updated analysis data
        loadLead();
      }
    });

    // Subscribe to lead_analysis.failed for this lead
    const unsubscribeFailed = subscribe('lead_analysis.failed', (event) => {
      if (event.data.lead_id === id) {
        console.error(`Lead analysis failed: ${event.data.error}`);
        setAnalysisStatus('failed');
        setAnalysisTaskId(null);
        alert(`AI analysis failed: ${event.data.error}`);
      }
    });

    return () => {
      unsubscribeStarted();
      unsubscribeCompleted();
      unsubscribeFailed();
    };
  }, [isConnected, id, subscribe]);

  const loadLead = async () => {
    try {
      setLoading(true);
      // Fetch from campaigns API - this is a discovery/campaign lead
      // We need to get all leads and find the one with this ID
      const response = await campaignAPI.listAllLeads();
      const foundLead = response.data.data.find((l: any) => l.id === id);
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
      
      console.log('[convertLead] Success response:', response.data);
      alert('Discovery converted to CRM lead successfully!');
      
      // Navigate to the new customer record
      if (response.data?.customer_id) {
        navigate(`/customers/${response.data.customer_id}`);
      } else {
        navigate('/customers');
      }
    } catch (error: any) {
      console.error('[convertLead] Full error:', error);
      console.error('[convertLead] Error response:', error.response);
      console.error('[convertLead] Error data:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to convert discovery';
      alert(`Failed to convert discovery: ${errorMessage}`);
    } finally {
      setConverting(false);
    }
  };

  const [analysisTaskId, setAnalysisTaskId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'queued' | 'running' | 'completed' | 'failed'>('idle');

  const handleRunAIAnalysis = async () => {
    if (!lead) return;

    if (!window.confirm('Run AI analysis on this discovery? This will analyze the company using all available data.')) {
      return;
    }

    setAnalyzing(true);
    setAnalysisStatus('queued');
    try {
      const response = await campaignAPI.analyzeLead(lead.id);
      
      if (response.data?.success) {
        if (response.data.status === 'queued') {
          // Analysis queued - start polling
          setAnalysisTaskId(response.data.task_id);
          alert('AI analysis queued in background. The page will refresh automatically when complete.');
        } else {
          // Immediate completion (shouldn't happen with background task, but handle it)
          alert('AI analysis completed successfully!');
          loadLead();
          setAnalysisStatus('completed');
        }
      } else {
        alert(`AI analysis failed: ${response.data?.error || 'Unknown error'}`);
        setAnalysisStatus('failed');
      }
    } catch (error: any) {
      console.error('Error running AI analysis:', error);
      alert(`Failed to run AI analysis: ${error.response?.data?.detail || error.message}`);
      setAnalysisStatus('failed');
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
        {/* Quick Telesales Summary */}
        {lead.qualification_reason && (
          <Grid size={12}>
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'success.light', border: '2px solid', borderColor: 'success.main' }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'success.dark', fontWeight: 'bold' }}>
                📞 Quick Telesales Summary
              </Typography>
              <Divider sx={{ mb: 2, borderColor: 'success.main' }} />
              <Typography 
                variant="body2" 
                sx={{ 
                  whiteSpace: 'pre-line',
                  '& strong': { fontWeight: 'bold', color: 'success.dark' }
                }}
                dangerouslySetInnerHTML={{
                  __html: lead.qualification_reason.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                }}
              />
            </Paper>
          </Grid>
        )}

        {/* Left Sidebar - Status/Lead Score and Quick Actions */}
        <Grid
          size={{
            xs: 12,
            md: 4
          }}>
          {/* Status and Lead Score - Above Quick Actions */}
          <Card sx={{ mb: 2 }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ mb: 1 }}>
                Status
              </Typography>
              <Chip
                label={lead.status}
                color={getStatusColor(lead.status)}
                size="small"
                sx={{ mb: 2 }}
              />

              <Typography variant="subtitle1" gutterBottom>
                Lead Score
              </Typography>
              <Chip
                label={lead.lead_score || 0}
                color={lead.lead_score >= 70 ? 'success' : lead.lead_score >= 40 ? 'warning' : 'default'}
                size="medium"
                sx={{ mb: 2 }}
              />

              <Typography variant="caption" display="block" sx={{ mt: 1 }} color="text.secondary">
                Created: {new Date(lead.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ mb: 1 }}>
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
                    disabled={analyzing || analysisStatus === 'queued' || analysisStatus === 'running'}
                  >
                    {analysisStatus === 'queued' ? 'Queued...' : 
                     analysisStatus === 'running' ? 'Running...' :
                     analyzing ? 'Queuing...' : 'Run AI Analysis'}
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

          {/* Lead Intelligence Widget */}
          {lead.id && (
            <Box sx={{ mb: 3 }}>
              <LeadIntelligence 
                leadId={lead.id} 
                compact={true}
                existingAnalysis={lead.ai_analysis} // Pass existing analysis to avoid API call on load
              />
            </Box>
          )}
        </Grid>

        {/* Company Information - Right side */}
        <Grid
          size={{
            xs: 12,
            md: 8
          }}>
          <Paper 
            elevation={2}
            sx={{ 
              p: 3, 
              mb: 3, 
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'primary.main',
              backgroundColor: 'background.paper'
            }}
          >
            <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
              Company Information
            </Typography>
            <Divider sx={{ mb: 2, borderColor: 'primary.main' }} />

            <Grid container spacing={2}>
              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Business Sector
                    </Typography>
                    <Typography>
                      {lead.business_sector || 
                       (lead.ai_analysis && typeof lead.ai_analysis === 'object' ? lead.ai_analysis.business_sector : null) || 
                       'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Company Size
                    </Typography>
                    <Typography>
                      {lead.company_size || 
                       (lead.ai_analysis && typeof lead.ai_analysis === 'object' ? lead.ai_analysis.business_size_category : null) || 
                       'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
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
                <Grid size={{ xs: 12 }}>
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

              <Grid
                size={{
                  xs: 12,
                  sm: 6
                }}>
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
                <Grid
                  size={{
                    xs: 12,
                    sm: 6
                  }}>
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
                <Grid size={{ xs: 12 }}>
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
                <Grid
                  size={{
                    xs: 12,
                    sm: 6
                  }}>
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
                <Grid
                  size={{
                    xs: 12,
                    sm: 6
                  }}>
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
                <Grid
                  size={{
                    xs: 12,
                    sm: 6
                  }}>
                  <Typography variant="caption" color="text.secondary">
                    Employees (Estimate)
                  </Typography>
                  <Typography>{lead.employee_count_estimate}</Typography>
                </Grid>
              )}

              {lead.annual_revenue_estimate && (
                <Grid
                  size={{
                    xs: 12,
                    sm: 6
                  }}>
                  <Typography variant="caption" color="text.secondary">
                    Annual Revenue (Estimate)
                  </Typography>
                  <Typography>£{lead.annual_revenue_estimate?.toLocaleString()}</Typography>
                </Grid>
              )}
            </Grid>

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

          {/* AI Analysis - Right side, below Company Information */}
          {lead.ai_analysis && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                AI Business Intelligence
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {typeof lead.ai_analysis === 'object' ? (
                <Box>
                  {/* Conversion Probability */}
                  {lead.ai_analysis.conversion_probability !== undefined && (
                    <Box sx={{ mb: 3, p: 2, bgcolor: 'rgba(76,175,80,0.1)', borderRadius: 2, border: '1px solid rgba(76,175,80,0.3)' }}>
                      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUpIcon color="success" /> Conversion Probability
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                        {lead.ai_analysis.conversion_probability}%
                      </Typography>
                    </Box>
                  )}

                  {/* Opportunity Summary */}
                  {lead.ai_analysis.opportunity_summary && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Opportunity Summary
                      </Typography>
                      <Typography variant="body2" paragraph sx={{ whiteSpace: 'pre-wrap' }}>
                        {lead.ai_analysis.opportunity_summary}
                      </Typography>
                    </Box>
                  )}

                  {/* Risk Assessment */}
                  {lead.ai_analysis.risk_assessment && Array.isArray(lead.ai_analysis.risk_assessment) && lead.ai_analysis.risk_assessment.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="error.main" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Risk Assessment
                      </Typography>
                      <List dense>
                        {lead.ai_analysis.risk_assessment.map((risk: string, index: number) => (
                          <ListItem key={index} sx={{ pl: 0 }}>
                            <ListItemIcon>
                              <WarningIcon color="error" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={risk} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}

                  {/* Recommendations */}
                  {lead.ai_analysis.recommendations && Array.isArray(lead.ai_analysis.recommendations) && lead.ai_analysis.recommendations.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="success.main" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Recommendations
                      </Typography>
                      <List dense>
                        {lead.ai_analysis.recommendations.map((rec: string, index: number) => (
                          <ListItem key={index} sx={{ pl: 0 }}>
                            <ListItemIcon>
                              <LightbulbIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={rec} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}

                  {/* Next Steps */}
                  {lead.ai_analysis.next_steps && Array.isArray(lead.ai_analysis.next_steps) && lead.ai_analysis.next_steps.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="info.main" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Next Steps
                      </Typography>
                      <List dense>
                        {lead.ai_analysis.next_steps.map((step: string, index: number) => (
                          <ListItem key={index} sx={{ pl: 0 }}>
                            <ListItemIcon>
                              <CheckCircleIcon color="info" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={step} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}

                  {/* Legacy format support - for old analysis data */}
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
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Business Sector</Typography>
                        <Typography variant="body2">{lead.ai_analysis.business_sector}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.business_size_category && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Company Size</Typography>
                        <Typography variant="body2">{lead.ai_analysis.business_size_category}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.estimated_employees && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Estimated Employees</Typography>
                        <Typography variant="body2">{lead.ai_analysis.estimated_employees}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.estimated_revenue && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Estimated Revenue</Typography>
                        <Typography variant="body2">{lead.ai_analysis.estimated_revenue}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.technology_maturity && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Technology Maturity</Typography>
                        <Typography variant="body2">{lead.ai_analysis.technology_maturity}</Typography>
                      </Grid>
                    )}
                    {(lead.ai_analysis.service_budget_estimate || lead.ai_analysis.it_budget_estimate) && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
                        <Typography variant="caption" color="text.secondary">Service Budget Estimate</Typography>
                        <Typography variant="body2">{lead.ai_analysis.service_budget_estimate || lead.ai_analysis.it_budget_estimate}</Typography>
                      </Grid>
                    )}
                    {lead.ai_analysis.growth_potential && (
                      <Grid
                        size={{
                          xs: 12,
                          sm: 6
                        }}>
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

          {/* External Data - Right side, below AI Analysis */}
          {(lead.google_maps_data || lead.companies_house_data || lead.linkedin_data || lead.website_data) && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Additional Data
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {lead.google_maps_data && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Google Maps Data</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    {lead.google_maps_data.rating && `Rating: ${lead.google_maps_data.rating} ⭐`}
                    {lead.google_maps_data.user_ratings_total && ` (${lead.google_maps_data.user_ratings_total} reviews)`}
                  </Typography>
                  {lead.google_maps_data.formatted_address && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Address: {lead.google_maps_data.formatted_address}
                    </Typography>
                  )}
                </Box>
              )}
              {lead.companies_house_data && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Companies House</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    {lead.companies_house_data.company_number && `Company Number: ${lead.companies_house_data.company_number}`}
                  </Typography>
                  {lead.companies_house_data.company_status && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Status: {lead.companies_house_data.company_status}
                    </Typography>
                  )}
                </Box>
              )}
              {lead.linkedin_data && lead.linkedin_data.linkedin_url && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">LinkedIn</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    <a href={lead.linkedin_data.linkedin_url} target="_blank" rel="noopener noreferrer">
                      View LinkedIn Profile
                    </a>
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default LeadDetail;

