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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Assessment as AssessmentIcon,
  ShoppingCart as ShoppingCartIcon,
  People as PeopleIcon,
  BugReport as BugReportIcon,
  Timeline as TimelineIcon,
  FilterList as FilterIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';
import { trendsAPI } from '../services/api';

interface RecurringDefect {
  issue: string;
  occurrences: number;
  affected_customers: string[];
  first_seen: string;
  last_seen: string;
  severity?: string;
}

interface QuoteHurdle {
  hurdle: string;
  frequency: number;
  affected_quotes: number;
  avg_impact_days?: number;
}

interface ChurnSignal {
  signal: string;
  affected_customers: string[];
  risk_level: 'high' | 'medium' | 'low';
  recommendation?: string;
}

interface TrendReport {
  summary: string;
  key_insights: string[];
  recommendations: string[];
  period_days: number;
}

const TrendsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [daysBack, setDaysBack] = useState(30);
  const [minOccurrences, setMinOccurrences] = useState(3);
  
  // Data
  const [recurringDefects, setRecurringDefects] = useState<RecurringDefect[]>([]);
  const [quoteHurdles, setQuoteHurdles] = useState<QuoteHurdle[]>([]);
  const [churnSignals, setChurnSignals] = useState<ChurnSignal[]>([]);
  const [trendReport, setTrendReport] = useState<TrendReport | null>(null);

  const loadRecurringDefects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await trendsAPI.getRecurringDefects(daysBack, minOccurrences);
      setRecurringDefects(response.data.defects || []);
    } catch (err: any) {
      console.error('Error loading recurring defects:', err);
      setError(err.response?.data?.detail || 'Failed to load recurring defects');
    } finally {
      setLoading(false);
    }
  };

  const loadQuoteHurdles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await trendsAPI.getQuoteHurdles(daysBack);
      setQuoteHurdles(response.data.hurdles || []);
    } catch (err: any) {
      console.error('Error loading quote hurdles:', err);
      setError(err.response?.data?.detail || 'Failed to load quote hurdles');
    } finally {
      setLoading(false);
    }
  };

  const loadChurnSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await trendsAPI.getChurnSignals(daysBack);
      setChurnSignals(response.data.signals || []);
    } catch (err: any) {
      console.error('Error loading churn signals:', err);
      setError(err.response?.data?.detail || 'Failed to load churn signals');
    } finally {
      setLoading(false);
    }
  };

  const loadTrendReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await trendsAPI.getTrendReport(daysBack);
      setTrendReport(response.data);
    } catch (err: any) {
      console.error('Error loading trend report:', err);
      setError(err.response?.data?.detail || 'Failed to load trend report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 0) {
      loadRecurringDefects();
    } else if (activeTab === 1) {
      loadQuoteHurdles();
    } else if (activeTab === 2) {
      loadChurnSignals();
    } else if (activeTab === 3) {
      loadTrendReport();
    }
  }, [activeTab, daysBack, minOccurrences]);

  const getSeverityColor = (severity?: string) => {
    if (!severity) return 'default';
    if (severity.toLowerCase().includes('high') || severity.toLowerCase().includes('critical')) return 'error';
    if (severity.toLowerCase().includes('medium')) return 'warning';
    return 'info';
  };

  const getRiskColor = (risk: string) => {
    if (risk === 'high') return 'error';
    if (risk === 'medium') return 'warning';
    return 'info';
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimelineIcon color="primary" sx={{ fontSize: 40 }} />
            Trend Detection Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            AI-powered insights across your customer base
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={daysBack}
              label="Time Period"
              onChange={(e) => setDaysBack(Number(e.target.value))}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
              <MenuItem value={180}>Last 180 days</MenuItem>
              <MenuItem value={365}>Last year</MenuItem>
            </Select>
          </FormControl>
          {activeTab === 0 && (
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Min Occurrences</InputLabel>
              <Select
                value={minOccurrences}
                label="Min Occurrences"
                onChange={(e) => setMinOccurrences(Number(e.target.value))}
              >
                <MenuItem value={2}>2+</MenuItem>
                <MenuItem value={3}>3+</MenuItem>
                <MenuItem value={5}>5+</MenuItem>
                <MenuItem value={10}>10+</MenuItem>
              </Select>
            </FormControl>
          )}
          <Tooltip title="Refresh">
            <IconButton
              onClick={() => {
                if (activeTab === 0) loadRecurringDefects();
                else if (activeTab === 1) loadQuoteHurdles();
                else if (activeTab === 2) loadChurnSignals();
                else if (activeTab === 3) loadTrendReport();
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
          <Tab
            icon={<BugReportIcon />}
            iconPosition="start"
            label="Recurring Defects"
            sx={{ minHeight: 72 }}
          />
          <Tab
            icon={<ShoppingCartIcon />}
            iconPosition="start"
            label="Quote Hurdles"
            sx={{ minHeight: 72 }}
          />
          <Tab
            icon={<PeopleIcon />}
            iconPosition="start"
            label="Churn Signals"
            sx={{ minHeight: 72 }}
          />
          <Tab
            icon={<AssessmentIcon />}
            iconPosition="start"
            label="Trend Report"
            sx={{ minHeight: 72 }}
          />
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
          {/* Recurring Defects Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              {recurringDefects.length === 0 ? (
                <Grid item xs={12}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center', py: 6 }}>
                      <CheckCircleIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        No Recurring Defects Found
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Great news! No recurring issues detected in the selected time period.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ) : (
                recurringDefects.map((defect, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card
                      sx={{
                        height: '100%',
                        border: '2px solid',
                        borderColor: getSeverityColor(defect.severity) === 'error' ? 'error.main' : 
                                     getSeverityColor(defect.severity) === 'warning' ? 'warning.main' : 'divider',
                        '&:hover': {
                          boxShadow: 6,
                          transform: 'translateY(-2px)',
                          transition: 'all 0.3s ease'
                        }
                      }}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" gutterBottom fontWeight="bold">
                              {defect.issue}
                            </Typography>
                            {defect.severity && (
                              <Chip
                                label={defect.severity}
                                color={getSeverityColor(defect.severity) as any}
                                size="small"
                                sx={{ mb: 1 }}
                              />
                            )}
                          </Box>
                          <Chip
                            label={`${defect.occurrences} occurrences`}
                            color="primary"
                            sx={{ fontWeight: 'bold' }}
                          />
                        </Box>
                        <Divider sx={{ my: 2 }} />
                        <Stack spacing={1}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PeopleIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              <strong>{defect.affected_customers.length}</strong> customers affected
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TimelineIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              First seen: {new Date(defect.first_seen).toLocaleDateString()}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TimelineIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              Last seen: {new Date(defect.last_seen).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          )}

          {/* Quote Hurdles Tab */}
          {activeTab === 1 && (
            <Grid container spacing={3}>
              {quoteHurdles.length === 0 ? (
                <Grid item xs={12}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center', py: 6 }}>
                      <CheckCircleIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        No Quote Hurdles Found
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Your quotes are moving smoothly through the pipeline!
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ) : (
                quoteHurdles.map((hurdle, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card
                      sx={{
                        height: '100%',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        '&:hover': {
                          boxShadow: 6,
                          transform: 'translateY(-2px)',
                          transition: 'all 0.3s ease'
                        }
                      }}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Typography variant="h6" fontWeight="bold" sx={{ color: 'white' }}>
                            {hurdle.hurdle}
                          </Typography>
                          <Chip
                            label={`${hurdle.frequency}%`}
                            sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white', fontWeight: 'bold' }}
                          />
                        </Box>
                        <Divider sx={{ my: 2, bgcolor: 'rgba(255,255,255,0.3)' }} />
                        <Stack spacing={1}>
                          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                            <strong>{hurdle.affected_quotes}</strong> quotes affected
                          </Typography>
                          {hurdle.avg_impact_days && (
                            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                              Average delay: <strong>{hurdle.avg_impact_days} days</strong>
                            </Typography>
                          )}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          )}

          {/* Churn Signals Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              {churnSignals.length === 0 ? (
                <Grid item xs={12}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center', py: 6 }}>
                      <CheckCircleIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        No Churn Signals Detected
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Your customers are showing healthy engagement patterns!
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ) : (
                <>
                  {churnSignals.map((signal, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card
                        sx={{
                          height: '100%',
                          border: '2px solid',
                          borderColor: getRiskColor(signal.risk_level) === 'error' ? 'error.main' : 
                                       getRiskColor(signal.risk_level) === 'warning' ? 'warning.main' : 'info.main',
                          '&:hover': {
                            boxShadow: 6,
                            transform: 'translateY(-2px)',
                            transition: 'all 0.3s ease'
                          }
                        }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="h6" gutterBottom fontWeight="bold">
                                {signal.signal}
                              </Typography>
                              <Chip
                                label={signal.risk_level.toUpperCase()}
                                color={getRiskColor(signal.risk_level) as any}
                                size="small"
                                sx={{ mb: 1 }}
                              />
                            </Box>
                            <Chip
                              label={`${signal.affected_customers.length} customers`}
                              color="primary"
                              sx={{ fontWeight: 'bold' }}
                            />
                          </Box>
                          <Divider sx={{ my: 2 }} />
                          {signal.recommendation && (
                            <Alert severity={signal.risk_level === 'high' ? 'error' : signal.risk_level === 'medium' ? 'warning' : 'info'} sx={{ mb: 2 }}>
                              <Typography variant="body2" fontWeight="bold">Recommendation:</Typography>
                              <Typography variant="body2">{signal.recommendation}</Typography>
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </>
              )}
            </Grid>
          )}

          {/* Trend Report Tab */}
          {activeTab === 3 && trendReport && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AssessmentIcon sx={{ fontSize: 32 }} />
                      Executive Summary
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 2, color: 'rgba(255,255,255,0.95)', whiteSpace: 'pre-wrap' }}>
                      {trendReport.summary}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {trendReport.key_insights && trendReport.key_insights.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LightbulbIcon color="primary" />
                        Key Insights
                      </Typography>
                      <List>
                        {trendReport.key_insights.map((insight, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckCircleIcon color="success" />
                            </ListItemIcon>
                            <ListItemText primary={insight} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {trendReport.recommendations && trendReport.recommendations.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUpIcon color="primary" />
                        Recommendations
                      </Typography>
                      <List>
                        {trendReport.recommendations.map((rec, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <WarningIcon color="warning" />
                            </ListItemIcon>
                            <ListItemText primary={rec} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}
        </>
      )}
    </Container>
  );
};

export default TrendsDashboard;

