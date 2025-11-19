import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Divider,
  Stack,
  LinearProgress
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  SentimentSatisfied as CSATIcon,
  ShoppingCart as ShoppingCartIcon,
  People as PeopleIcon,
  AutoAwesome as AIIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { metricsAPI } from '../services/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface SLAMetrics {
  first_response_time_avg?: number;
  resolution_time_avg?: number;
  breach_rate?: number;
  total_tickets?: number;
  tickets_by_status?: { [key: string]: number };
  tickets_by_priority?: { [key: string]: number };
}

interface AIUsageMetrics {
  total_calls?: number;
  total_tokens?: number;
  total_cost?: number;
  calls_by_provider?: { [key: string]: number };
  tokens_by_provider?: { [key: string]: number };
  cost_by_provider?: { [key: string]: number };
  calls_over_time?: Array<{ date: string; calls: number }>;
}

interface LeadVelocityMetrics {
  avg_time_to_convert?: number;
  conversion_rate?: number;
  leads_by_stage?: { [key: string]: number };
  conversion_funnel?: Array<{ stage: string; count: number }>;
}

interface QuoteCycleTimeMetrics {
  avg_cycle_time?: number;
  avg_time_by_stage?: { [key: string]: number };
  quotes_by_status?: { [key: string]: number };
  cycle_time_trend?: Array<{ date: string; days: number }>;
}

interface CSATMetrics {
  avg_score?: number;
  response_count?: number;
  scores_by_category?: { [key: string]: number };
  trend?: Array<{ date: string; score: number }>;
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

const MetricsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Date range filters
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  // Metrics data
  const [slaMetrics, setSlaMetrics] = useState<SLAMetrics | null>(null);
  const [aiUsageMetrics, setAiUsageMetrics] = useState<AIUsageMetrics | null>(null);
  const [leadVelocityMetrics, setLeadVelocityMetrics] = useState<LeadVelocityMetrics | null>(null);
  const [quoteCycleTimeMetrics, setQuoteCycleTimeMetrics] = useState<QuoteCycleTimeMetrics | null>(null);
  const [csatMetrics, setCsatMetrics] = useState<CSATMetrics | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);

  const loadSLAMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getSLA(startDate || undefined, endDate || undefined);
      setSlaMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading SLA metrics:', err);
      setError(err.response?.data?.detail || 'Failed to load SLA metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadAIUsageMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getAIUsage(startDate || undefined, endDate || undefined);
      setAiUsageMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading AI usage metrics:', err);
      setError(err.response?.data?.detail || 'Failed to load AI usage metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadLeadVelocityMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getLeadVelocity(startDate || undefined, endDate || undefined);
      setLeadVelocityMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading lead velocity metrics:', err);
      setError(err.response?.data?.detail || 'Failed to load lead velocity metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadQuoteCycleTimeMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getQuoteCycleTime(startDate || undefined, endDate || undefined);
      setQuoteCycleTimeMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading quote cycle time metrics:', err);
      setError(err.response?.data?.detail || 'Failed to load quote cycle time metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadCSATMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getCSAT(startDate || undefined, endDate || undefined);
      setCsatMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading CSAT metrics:', err);
      setError(err.response?.data?.detail || 'Failed to load CSAT metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await metricsAPI.getDashboard();
      setDashboardData(response.data);
    } catch (err: any) {
      console.error('Error loading dashboard:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 0) {
      loadDashboard();
    } else if (activeTab === 1) {
      loadSLAMetrics();
    } else if (activeTab === 2) {
      loadAIUsageMetrics();
    } else if (activeTab === 3) {
      loadLeadVelocityMetrics();
    } else if (activeTab === 4) {
      loadQuoteCycleTimeMetrics();
    } else if (activeTab === 5) {
      loadCSATMetrics();
    }
  }, [activeTab, startDate, endDate]);

  const formatTime = (minutes?: number) => {
    if (!minutes) return 'N/A';
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const formatCurrency = (amount?: number) => {
    if (amount === undefined || amount === null) return 'N/A';
    return `£${amount.toFixed(2)}`;
  };

  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toLocaleString();
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
            Metrics Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Track performance across SLA, AI usage, lead velocity, quotes, and customer satisfaction
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Start Date</InputLabel>
            <Select
              value={startDate}
              label="Start Date"
              onChange={(e) => setStartDate(e.target.value)}
            >
              <MenuItem value="">All Time</MenuItem>
              <MenuItem value={new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}>Last 7 days</MenuItem>
              <MenuItem value={new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}>Last 30 days</MenuItem>
              <MenuItem value={new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}>Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>End Date</InputLabel>
            <Select
              value={endDate}
              label="End Date"
              onChange={(e) => setEndDate(e.target.value)}
            >
              <MenuItem value="">Today</MenuItem>
              <MenuItem value={new Date().toISOString().split('T')[0]}>Today</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Refresh">
            <IconButton
              onClick={() => {
                if (activeTab === 0) loadDashboard();
                else if (activeTab === 1) loadSLAMetrics();
                else if (activeTab === 2) loadAIUsageMetrics();
                else if (activeTab === 3) loadLeadVelocityMetrics();
                else if (activeTab === 4) loadQuoteCycleTimeMetrics();
                else if (activeTab === 5) loadCSATMetrics();
              }}
              disabled={loading}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<AssessmentIcon />} iconPosition="start" label="Overview" sx={{ minHeight: 72 }} />
          <Tab icon={<ScheduleIcon />} iconPosition="start" label="SLA" sx={{ minHeight: 72 }} />
          <Tab icon={<AIIcon />} iconPosition="start" label="AI Usage" sx={{ minHeight: 72 }} />
          <Tab icon={<PeopleIcon />} iconPosition="start" label="Lead Velocity" sx={{ minHeight: 72 }} />
          <Tab icon={<ShoppingCartIcon />} iconPosition="start" label="Quote Cycle" sx={{ minHeight: 72 }} />
          <Tab icon={<CSATIcon />} iconPosition="start" label="CSAT" sx={{ minHeight: 72 }} />
        </Tabs>
      </Paper>

      {/* Content */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress size={60} />
        </Box>
      )}

      {!loading && (
        <>
          {/* Overview Tab */}
          {activeTab === 0 && dashboardData && (
            <Grid container spacing={3}>
              {/* Key Metrics Cards */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h3" fontWeight="bold">
                      {dashboardData.sla?.adherence_rate_percent?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>SLA Compliance</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
                      {dashboardData.sla?.total_tickets || 0} tickets
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h3" fontWeight="bold">
                      {dashboardData.ai_usage?.ticket_ai_usage_rate_percent?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>AI Usage Rate</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
                      {dashboardData.ai_usage?.tickets_with_ai || 0} tickets with AI
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h3" fontWeight="bold">
                      {dashboardData.lead_velocity?.conversion_rate_percent?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>Lead Conversion</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
                      {dashboardData.lead_velocity?.converted_leads || 0} of {dashboardData.lead_velocity?.total_leads || 0} leads
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h3" fontWeight="bold">
                      {dashboardData.csat?.average_rating?.toFixed(1) || 0}/5
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>CSAT Score</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
                      {dashboardData.csat?.total_ratings || 0} responses
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Additional Metrics */}
              {dashboardData.quote_cycle_time && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Quote Cycle Times</Typography>
                      <Stack spacing={2} sx={{ mt: 2 }}>
                        {dashboardData.quote_cycle_time.average_draft_to_sent_days && (
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="body2">Draft to Sent</Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {dashboardData.quote_cycle_time.average_draft_to_sent_days.toFixed(1)} days
                              </Typography>
                            </Box>
                          </Box>
                        )}
                        {dashboardData.quote_cycle_time.average_sent_to_accepted_days && (
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="body2">Sent to Accepted</Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {dashboardData.quote_cycle_time.average_sent_to_accepted_days.toFixed(1)} days
                              </Typography>
                            </Box>
                          </Box>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              )}
              
              {dashboardData.lead_velocity?.average_conversion_time_days && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Lead Velocity</Typography>
                      <Typography variant="h4" color="primary" sx={{ mt: 2 }}>
                        {dashboardData.lead_velocity.average_conversion_time_days.toFixed(1)} days
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average time to convert
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {/* SLA Metrics Tab */}
          {activeTab === 1 && slaMetrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Total Tickets</Typography>
                    <Typography variant="h3" color="primary">{slaMetrics.total_tickets || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>On Time</Typography>
                    <Typography variant="h3" color="success.main">{slaMetrics.on_time || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>SLA Adherence Rate</Typography>
                    <Typography variant="h3" color={slaMetrics.adherence_rate_percent && slaMetrics.adherence_rate_percent < 90 ? 'error' : 'success'}>
                      {slaMetrics.adherence_rate_percent?.toFixed(1) || 0}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={slaMetrics.adherence_rate_percent || 0}
                      color={slaMetrics.adherence_rate_percent && slaMetrics.adherence_rate_percent < 90 ? 'error' : 'success'}
                      sx={{ mt: 2, height: 8, borderRadius: 4 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Breach Summary</Typography>
                    <Box sx={{ mt: 2 }}>
                      <Stack spacing={2}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Breached:</Typography>
                          <Chip label={slaMetrics.breached || 0} color="error" />
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>On Time:</Typography>
                          <Chip label={slaMetrics.on_time || 0} color="success" />
                        </Box>
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* AI Usage Metrics Tab */}
          {activeTab === 2 && aiUsageMetrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>Tickets with AI</Typography>
                    <Typography variant="h3" fontWeight="bold">{aiUsageMetrics.tickets_with_ai || 0}</Typography>
                    <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                      {aiUsageMetrics.ticket_ai_usage_rate_percent?.toFixed(1) || 0}% of {aiUsageMetrics.total_tickets || 0} total tickets
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>Quotes with AI</Typography>
                    <Typography variant="h3" fontWeight="bold">{aiUsageMetrics.quotes_with_ai || 0}</Typography>
                    <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                      {aiUsageMetrics.quote_ai_usage_rate_percent?.toFixed(1) || 0}% of {aiUsageMetrics.total_quotes || 0} total quotes
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>AI Usage Summary</Typography>
                    <Box sx={{ mt: 2 }}>
                      <Stack spacing={2}>
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography>Tickets AI Usage Rate</Typography>
                            <Typography fontWeight="bold">{aiUsageMetrics.ticket_ai_usage_rate_percent?.toFixed(1) || 0}%</Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={aiUsageMetrics.ticket_ai_usage_rate_percent || 0}
                            color="primary"
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography>Quotes AI Usage Rate</Typography>
                            <Typography fontWeight="bold">{aiUsageMetrics.quote_ai_usage_rate_percent?.toFixed(1) || 0}%</Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={aiUsageMetrics.quote_ai_usage_rate_percent || 0}
                            color="secondary"
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Lead Velocity Metrics Tab */}
          {activeTab === 3 && leadVelocityMetrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Total Leads</Typography>
                    <Typography variant="h3" color="primary">{leadVelocityMetrics.total_leads || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Converted Leads</Typography>
                    <Typography variant="h3" color="success.main">{leadVelocityMetrics.converted_leads || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Conversion Rate</Typography>
                    <Typography variant="h3" color="success.main">{leadVelocityMetrics.conversion_rate_percent?.toFixed(1) || 0}%</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={leadVelocityMetrics.conversion_rate_percent || 0}
                      color="success"
                      sx={{ mt: 2, height: 8, borderRadius: 4 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
              {leadVelocityMetrics.average_conversion_time_days && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Average Time to Convert</Typography>
                      <Typography variant="h3" color="primary">{leadVelocityMetrics.average_conversion_time_days.toFixed(1)} days</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {/* Quote Cycle Time Metrics Tab */}
          {activeTab === 4 && quoteCycleTimeMetrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Total Quotes</Typography>
                    <Typography variant="h3" color="primary">{quoteCycleTimeMetrics.total_quotes || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              {quoteCycleTimeMetrics.average_draft_to_sent_days && (
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Avg Draft to Sent</Typography>
                      <Typography variant="h3" color="primary">{quoteCycleTimeMetrics.average_draft_to_sent_days.toFixed(1)} days</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
              {quoteCycleTimeMetrics.average_sent_to_accepted_days && (
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Avg Sent to Accepted</Typography>
                      <Typography variant="h3" color="success.main">{quoteCycleTimeMetrics.average_sent_to_accepted_days.toFixed(1)} days</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {/* CSAT Metrics Tab */}
          {activeTab === 5 && csatMetrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>Average CSAT Score</Typography>
                    <Typography variant="h3" fontWeight="bold">{csatMetrics.average_rating?.toFixed(1) || 0}/5</Typography>
                    <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                      Based on {formatNumber(csatMetrics.total_ratings)} responses
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>CSAT Distribution</Typography>
                    {csatMetrics.distribution && Object.keys(csatMetrics.distribution).length > 0 ? (
                      <Box sx={{ mt: 2 }}>
                        {Object.entries(csatMetrics.distribution).map(([rating, count]: [string, any]) => (
                          <Box key={rating} sx={{ mb: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="body2">{rating} Star{count !== 1 ? 's' : ''}</Typography>
                              <Typography variant="body2" fontWeight="bold">{count}</Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={(count / (csatMetrics.total_ratings || 1)) * 100}
                              color="success"
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                        No CSAT data available
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </>
      )}
    </Container>
  );
};

export default MetricsDashboard;

