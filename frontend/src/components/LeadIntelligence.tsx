import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  LinearProgress
} from '@mui/material';
import {
  AutoAwesome as SparkleIcon,
  TrendingUp as TrendingUpIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  CalendarToday as CalendarIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Lightbulb as LightbulbIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { leadIntelligenceAPI } from '../services/api';

interface LeadIntelligenceProps {
  leadId: string;
  compact?: boolean;
  existingAnalysis?: any; // Pass existing ai_analysis data from lead
}

interface LeadAnalysis {
  lead_score?: number;
  selling_points?: string[];
  risks?: string[];
  conversion_probability?: number;
}

interface OutreachPlan {
  channels?: string[];
  messaging_ideas?: string[];
  next_steps?: string[];
}

interface SimilarLead {
  id: string;
  company_name: string;
  converted_at: string;
  similarity_score?: number;
}

const LeadIntelligence: React.FC<LeadIntelligenceProps> = ({
  leadId,
  compact = false,
  existingAnalysis = null
}) => {
  const [analysis, setAnalysis] = useState<LeadAnalysis | null>(null);
  const [outreachPlan, setOutreachPlan] = useState<OutreachPlan | null>(null);
  const [similarLeads, setSimilarLeads] = useState<SimilarLead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'analysis' | 'outreach' | 'similar'>('analysis');

  // Initialize with existing analysis if provided
  useEffect(() => {
    if (existingAnalysis && typeof existingAnalysis === 'object') {
      // Map existing analysis to component format
      setAnalysis({
        conversion_probability: existingAnalysis.conversion_probability,
        lead_score: existingAnalysis.conversion_probability, // Use conversion_probability as lead_score
        risks: existingAnalysis.risk_assessment || [],
        selling_points: existingAnalysis.recommendations || []
      });
    }
  }, [existingAnalysis]);

  const loadAnalysis = async (forceRefresh = false) => {
    // If we have existing analysis and not forcing refresh, skip API call
    if (existingAnalysis && !forceRefresh) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await leadIntelligenceAPI.analyzeLead(leadId);
      setAnalysis(response.data);
    } catch (err: any) {
      console.error('Error loading lead analysis:', err);
      setError(err.response?.data?.detail || 'Failed to load lead analysis');
    } finally {
      setLoading(false);
    }
  };

  const loadOutreachPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await leadIntelligenceAPI.getOutreachPlan(leadId);
      setOutreachPlan(response.data);
    } catch (err: any) {
      console.error('Error loading outreach plan:', err);
      setError(err.response?.data?.detail || 'Failed to load outreach plan');
    } finally {
      setLoading(false);
    }
  };

  const loadSimilarLeads = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await leadIntelligenceAPI.getSimilarLeads(leadId);
      setSimilarLeads(response.data.similar_leads || []);
    } catch (err: any) {
      console.error('Error loading similar leads:', err);
      setError(err.response?.data?.detail || 'Failed to load similar leads');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only load if we don't have existing data or user switches tabs
    if (leadId && activeView === 'analysis') {
      // Only call API if no existing analysis
      if (!existingAnalysis) {
        loadAnalysis();
      }
    } else if (leadId && activeView === 'outreach') {
      loadOutreachPlan();
    } else if (leadId && activeView === 'similar') {
      loadSimilarLeads();
    }
  }, [leadId, activeView]); // Don't include existingAnalysis in deps to avoid re-running

  const getScoreColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        color: 'white',
        border: '2px solid',
        borderColor: 'secondary.main'
      }}
    >
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SparkleIcon sx={{ fontSize: 32 }} />
            <Typography variant="h6" component="div" fontWeight="bold">
              Lead Intelligence
            </Typography>
          </Box>
          <Tooltip title="Refresh">
            <span>
              <IconButton
                size="small"
                onClick={() => {
                  if (activeView === 'analysis') loadAnalysis(true); // Force refresh
                  else if (activeView === 'outreach') loadOutreachPlan();
                  else if (activeView === 'similar') loadSimilarLeads();
                }}
                disabled={loading}
                sx={{ color: 'white' }}
              >
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>

        {/* Tabs */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Button
            variant={activeView === 'analysis' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<AssessmentIcon />}
            onClick={() => setActiveView('analysis')}
            sx={{
              bgcolor: activeView === 'analysis' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Analysis
          </Button>
          <Button
            variant={activeView === 'outreach' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<EmailIcon />}
            onClick={() => setActiveView('outreach')}
            sx={{
              bgcolor: activeView === 'outreach' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Outreach
          </Button>
          <Button
            variant={activeView === 'similar' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<PeopleIcon />}
            onClick={() => setActiveView('similar')}
            sx={{
              bgcolor: activeView === 'similar' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Similar
          </Button>
        </Box>

        <Divider sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.3)' }} />

        {/* Content */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress sx={{ color: 'white' }} />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.9)', color: 'error.main' }}>
            {error}
          </Alert>
        )}

        {!loading && !error && (
          <>
            {/* Analysis View */}
            {activeView === 'analysis' && analysis && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {analysis.lead_score !== undefined && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(255,255,255,0.1)' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h4" component="div" fontWeight="bold">
                        {analysis.lead_score}
                      </Typography>
                      <Chip
                        label={analysis.lead_score >= 80 ? 'High' : analysis.lead_score >= 60 ? 'Medium' : 'Low'}
                        color={getScoreColor(analysis.lead_score) as any}
                        sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white' }}
                      />
                    </Box>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      Lead Score
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={analysis.lead_score}
                      color={getScoreColor(analysis.lead_score) as any}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        mt: 1,
                        bgcolor: 'rgba(255,255,255,0.2)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4
                        }
                      }}
                    />
                  </Paper>
                )}

                {analysis.conversion_probability !== undefined && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(76,175,80,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TrendingUpIcon /> Conversion Probability
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'white' }}>
                      {analysis.conversion_probability}%
                    </Typography>
                  </Paper>
                )}

                {analysis.selling_points && analysis.selling_points.length > 0 && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(76,175,80,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LightbulbIcon /> Key Selling Points
                    </Typography>
                    <List dense>
                      {analysis.selling_points.map((point, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={point}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}

                {analysis.risks && analysis.risks.length > 0 && (
                  <Paper sx={{ p: 2, bgcolor: 'rgba(244,67,54,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WarningIcon /> Risks & Concerns
                    </Typography>
                    <List dense>
                      {analysis.risks.map((risk, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <WarningIcon sx={{ color: 'error.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={risk}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}
              </Box>
            )}

            {/* Outreach Plan View */}
            {activeView === 'outreach' && outreachPlan && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {outreachPlan.channels && outreachPlan.channels.length > 0 && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(33,150,243,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <EmailIcon /> Recommended Channels
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mt: 1 }}>
                      {outreachPlan.channels.map((channel, idx) => (
                        <Chip
                          key={idx}
                          label={channel}
                          size="small"
                          sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white' }}
                        />
                      ))}
                    </Stack>
                  </Paper>
                )}

                {outreachPlan.messaging_ideas && outreachPlan.messaging_ideas.length > 0 && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(156,39,176,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LightbulbIcon /> Messaging Ideas
                    </Typography>
                    <List dense>
                      {outreachPlan.messaging_ideas.map((idea, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <LightbulbIcon sx={{ color: 'secondary.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={idea}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}

                {outreachPlan.next_steps && outreachPlan.next_steps.length > 0 && (
                  <Paper sx={{ p: 2, bgcolor: 'rgba(76,175,80,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CalendarIcon /> Next Steps
                    </Typography>
                    <List dense>
                      {outreachPlan.next_steps.map((step, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={step}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}
              </Box>
            )}

            {/* Similar Leads View */}
            {activeView === 'similar' && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {similarLeads.length > 0 ? (
                  <List>
                    {similarLeads.map((lead, idx) => (
                      <ListItem
                        key={lead.id || lead.company_name || `similar-lead-${idx}`}
                        sx={{
                          px: 0,
                          py: 1.5,
                          bgcolor: 'rgba(255,255,255,0.1)',
                          mb: 1,
                          borderRadius: 1,
                          '&:hover': {
                            bgcolor: 'rgba(255,255,255,0.2)'
                          }
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <PeopleIcon sx={{ color: 'white', fontSize: 24 }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={lead.company_name}
                          secondary={`Converted ${new Date(lead.converted_at).toLocaleDateString()}${lead.similarity_score ? ` • ${lead.similarity_score}% match` : ''}`}
                          primaryTypographyProps={{ variant: 'body2', sx: { fontWeight: 'bold', color: 'white' } }}
                          secondaryTypographyProps={{ variant: 'caption', sx: { color: 'rgba(255,255,255,0.7)' } }}
                        />
                        {lead.similarity_score && (
                          <Chip
                            label={`${lead.similarity_score}%`}
                            size="small"
                            sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white' }}
                          />
                        )}
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center', py: 4 }}>
                    No similar converted leads found.
                  </Typography>
                )}
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default LeadIntelligence;

