import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  IconButton,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Paper,
  Alert,
  CircularProgress,
  Menu,
  MenuItem,
  Divider,
  Tabs,
  Tab,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  People as PeopleIcon,
  Business as BusinessIcon,
  Description as DescriptionIcon,
  Campaign as CampaignIcon,
  AttachMoney as MoneyIcon,
  Send as SendIcon,
  Timeline as TimelineIcon,
  Lightbulb as LightbulbIcon,
  AutoAwesome as AIIcon,
  MoreVert as MoreVertIcon,
  Dashboard as DashboardIcon,
  ShowChart as ChartIcon,
  Insights as InsightsIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { dashboardAPI } from '../services/api';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardData {
  stats: {
    total_discovery: number;
    total_leads: number;
    total_prospects: number;
    total_opportunities: number;
    total_customers: number;
    total_cold_leads: number;
    total_inactive: number;
    total_quotes: number;
    quotes_pending: number;
    quotes_accepted: number;
    total_revenue: number;
    avg_deal_value: number;
    conversion_rate: number;
  };
  conversion_funnel: Array<{
    status: string;
    count: number;
    percentage: number;
    color: string;
  }>;
  recent_activity: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    timestamp: string;
    icon: string;
  }>;
  monthly_trends: Array<{
    month: string;
    new_leads: number;
    converted: number;
    revenue: number;
  }>;
  ai_insights: Array<{
    type: string;
    title: string;
    description: string;
    priority: string;
    action: string | null;
  }>;
  top_leads: Array<{
    id: string;
    company_name: string;
    status: string;
    lead_score: number;
    created_at: string;
  }>;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiChartData, setAiChartData] = useState<any>(null);
  const [aiChartType, setAiChartType] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [statusMenuAnchor, setStatusMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [currentTab, setCurrentTab] = useState(0);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await dashboardAPI.get('/');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAIQuery = async (customQuery?: string) => {
    const queryText = customQuery || aiQuery;
    if (!queryText.trim()) return;
    
    setAiLoading(true);
    try {
      const response = await dashboardAPI.post('/ai-query', { query: queryText });
      setAiResponse(response.data.answer);
      
      // Set chart data if visualization is provided
      if (response.data.chart_data) {
        setAiChartData(response.data.chart_data);
        setAiChartType(response.data.visualization_type);
      } else {
        setAiChartData(null);
        setAiChartType(null);
      }
      
      // Set suggested follow-up questions
      if (response.data.suggested_followup) {
        setSuggestedQuestions(response.data.suggested_followup);
      }
      
    } catch (error) {
      console.error('AI query failed:', error);
      setAiResponse('Sorry, I encountered an error processing your request.');
      setAiChartData(null);
      setAiChartType(null);
    } finally {
      setAiLoading(false);
    }
  };

  const handleStatusChange = async (customerId: string, newStatus: string) => {
    try {
      await dashboardAPI.post(`/customers/${customerId}/change-status`, null, {
        params: { new_status: newStatus }
      });
      loadDashboard();
      setStatusMenuAnchor(null);
      setSelectedLead(null);
    } catch (error) {
      console.error('Failed to change status:', error);
    }
  };

  const openStatusMenu = (event: React.MouseEvent<HTMLElement>, lead: any) => {
    setStatusMenuAnchor(event.currentTarget);
    setSelectedLead(lead);
  };

  if (loading || !dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const { stats, conversion_funnel, recent_activity, monthly_trends, ai_insights, top_leads } = dashboardData;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      default: return 'info';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'lead': return 'primary';
      case 'prospect': return 'secondary';
      case 'customer': return 'success';
      case 'cold_lead': return 'warning';
      default: return 'default';
    }
  };

  // Chart data
  const trendsChartData = {
    labels: monthly_trends.map(t => t.month),
    datasets: [
      {
        label: 'New Leads',
        data: monthly_trends.map(t => t.new_leads),
        borderColor: '#3498db',
        backgroundColor: 'rgba(52, 152, 219, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Converted',
        data: monthly_trends.map(t => t.converted),
        borderColor: '#2ecc71',
        backgroundColor: 'rgba(46, 204, 113, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const revenueChartData = {
    labels: monthly_trends.map(t => t.month),
    datasets: [
      {
        label: 'Revenue (£)',
        data: monthly_trends.map(t => t.revenue),
        backgroundColor: 'rgba(46, 204, 113, 0.8)',
        borderColor: '#2ecc71',
        borderWidth: 1
      }
    ]
  };

  const funnelChartData = {
    labels: conversion_funnel.map(f => f.status),
    datasets: [
      {
        data: conversion_funnel.map(f => f.count),
        backgroundColor: conversion_funnel.map(f => f.color),
        borderWidth: 0
      }
    ]
  };

  return (
    <>
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Clean Centered Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          CRM Dashboard
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          AI-Powered Insights & Analytics
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => navigate('/customers/new')}
            sx={{ 
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            New Customer
          </Button>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<CampaignIcon />}
            onClick={() => navigate('/campaigns')}
            sx={{ 
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            New Campaign
          </Button>
        </Box>
      </Box>
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab icon={<DashboardIcon />} label="Overview" iconPosition="start" />
          <Tab icon={<ChartIcon />} label="Analytics" iconPosition="start" />
          <Tab icon={<AIIcon />} label="AI Assistant" iconPosition="start" />
          <Tab 
            icon={<InsightsIcon />} 
            label={
              <Box display="flex" alignItems="center" gap={1}>
                Insights
                {ai_insights.length > 0 && (
                  <Chip label={ai_insights.length} size="small" color="error" sx={{ height: 20 }} />
                )}
              </Box>
            } 
            iconPosition="start" 
          />
        </Tabs>
      </Box>
      {/* Tab 0: Overview */}
      {currentTab === 0 && (
        <>
          {/* Key Stats */}
          <Grid container spacing={3} sx={{ mb: 4, width: '100%', justifyContent: 'center' }}>
            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 3
              }}>
              <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', cursor: 'pointer' }} onClick={() => navigate('/customers?status=lead')}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">{stats.total_leads}</Typography>
                      <Typography variant="body2">Leads</Typography>
                    </Box>
                    <PeopleIcon sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 3
              }}>
              <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white', cursor: 'pointer' }} onClick={() => navigate('/customers?status=prospect')}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">{stats.total_prospects}</Typography>
                      <Typography variant="body2">Prospects</Typography>
                    </Box>
                    <TimelineIcon sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 3
              }}>
              <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white', cursor: 'pointer' }} onClick={() => navigate('/customers?status=customer')}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">{stats.total_customers}</Typography>
                      <Typography variant="body2">Customers</Typography>
                    </Box>
                    <BusinessIcon sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 3
              }}>
              <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white'}}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">{formatCurrency(stats.total_revenue)}</Typography>
                      <Typography variant="body2">Total Revenue</Typography>
                    </Box>
                    <MoneyIcon sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Secondary Stats */}
          <Grid container spacing={3} sx={{ mb: 4, width: '100%', justifyContent: 'center' }}>
            <Grid
              size={{
                xs: 6,
                md: 3
              }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.conversion_rate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">Conversion Rate</Typography>
              </Paper>
            </Grid>
            <Grid
              size={{
                xs: 6,
                md: 3
              }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" fontWeight="bold">
                  {formatCurrency(stats.avg_deal_value)}
                </Typography>
                <Typography variant="body2" color="text.secondary">Avg Deal Value</Typography>
              </Paper>
            </Grid>
            <Grid
              size={{
                xs: 6,
                md: 3
              }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main" fontWeight="bold">
                  {stats.quotes_pending}
                </Typography>
                <Typography variant="body2" color="text.secondary">Pending Quotes</Typography>
              </Paper>
            </Grid>
            <Grid
              size={{
                xs: 6,
                md: 3
              }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="info.main" fontWeight="bold">
                  {stats.total_cold_leads}
                </Typography>
                <Typography variant="body2" color="text.secondary">Cold Leads</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Top Leads & Recent Activity */}
          <Grid container spacing={3} sx={{ width: '100%' }}>
            <Grid
              size={{
                xs: 12,
                md: 6
              }}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" fontWeight="bold">
                      Top Leads by Score
                    </Typography>
                    <Button size="small" onClick={() => navigate('/customers')}>View All</Button>
                  </Box>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Company</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="center">Score</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {top_leads.slice(0, 5).map((lead) => (
                          <TableRow key={lead.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/customers/${lead.id}`)}>
                            <TableCell>{lead.company_name}</TableCell>
                            <TableCell>
                              <Chip 
                                label={lead.status.replace('_', ' ').toUpperCase()} 
                                size="small" 
                                color={getStatusColor(lead.status) as any}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={lead.lead_score} 
                                size="small" 
                                color={lead.lead_score >= 70 ? 'success' : lead.lead_score >= 40 ? 'warning' : 'default'}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <IconButton size="small" onClick={(e) => { e.stopPropagation(); openStatusMenu(e, lead); }}>
                                <MoreVertIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
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
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Recent Activity
                  </Typography>
                  <List>
                    {recent_activity.map((activity) => (
                      <ListItem key={activity.id} sx={{ px: 0, cursor: 'pointer' }} onClick={() => navigate(`/customers/${activity.id}`)}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'primary.light' }}>
                            <BusinessIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={activity.title}
                          secondary={activity.description}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
      {/* Tab 1: Analytics */}
      {currentTab === 1 && (
        <Grid container spacing={3}>
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  6-Month Performance Trends
                </Typography>
                <Line data={trendsChartData} options={{ responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }} />
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
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Revenue by Month
                </Typography>
                <Bar data={revenueChartData} options={{ responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } }} />
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
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Conversion Funnel
                </Typography>
                <Doughnut data={funnelChartData} options={{ responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }} />
              </CardContent>
            </Card>
          </Grid>

          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Monthly Performance Summary
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Month</TableCell>
                        <TableCell align="right">New Leads</TableCell>
                        <TableCell align="right">Converted</TableCell>
                        <TableCell align="right">Revenue</TableCell>
                        <TableCell align="right">Conversion Rate</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {monthly_trends.map((trend, index) => {
                        const conversionRate = trend.new_leads > 0 ? (trend.converted / trend.new_leads * 100).toFixed(1) : '0.0';
                        return (
                          <TableRow key={index}>
                            <TableCell>{trend.month}</TableCell>
                            <TableCell align="right">{trend.new_leads}</TableCell>
                            <TableCell align="right">{trend.converted}</TableCell>
                            <TableCell align="right">{formatCurrency(trend.revenue)}</TableCell>
                            <TableCell align="right">{conversionRate}%</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
      {/* Tab 2: AI Assistant */}
      {currentTab === 2 && (
        <Grid container spacing={3}>
          {/* AI Query Input Card */}
          <Grid size={12}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <AIIcon sx={{ color: 'white', fontSize: 32 }} />
                  <Typography variant="h5" fontWeight="bold" color="white">
                    AI-Powered CRM Assistant
                  </Typography>
                </Box>
                <Typography variant="body2" color="white" sx={{ mb: 3, opacity: 0.9 }}>
                  Ask questions and get instant insights with visual dashboards. I can analyze your customers, trends, and performance metrics.
                </Typography>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="E.g., 'Show me customer breakdown by status' or 'What's the trend over the last 6 months?'"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !aiLoading && handleAIQuery()}
                  sx={{ mb: 2, backgroundColor: 'white', borderRadius: 1 }}
                  InputProps={{
                    endAdornment: (
                      <IconButton onClick={() => handleAIQuery()} disabled={aiLoading} color="primary">
                        {aiLoading ? <CircularProgress size={24} /> : <SendIcon />}
                      </IconButton>
                    )
                  }}
                  multiline
                  rows={2}
                />
              </CardContent>
            </Card>
          </Grid>

          {/* AI Response with Visualization */}
          {aiResponse && (
            <>
              <Grid
                size={{
                  xs: 12,
                  md: aiChartData ? 6 : 12
                }}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <AIIcon color="primary" />
                      <Typography variant="h6" fontWeight="bold">
                        AI Analysis
                      </Typography>
                    </Box>
                    <Alert severity="info" sx={{ whiteSpace: 'pre-wrap', fontSize: '1rem' }}>
                      {aiResponse}
                    </Alert>
                    
                    {/* Suggested Follow-up Questions */}
                    {suggestedQuestions && suggestedQuestions.length > 0 && (
                      <Box mt={3}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Suggested Follow-up Questions:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={1}>
                          {suggestedQuestions.slice(0, 3).map((question, index) => (
                            <Chip
                              key={index}
                              label={question}
                              onClick={() => { setAiQuery(question); handleAIQuery(question); }}
                              sx={{ cursor: 'pointer' }}
                              variant="outlined"
                              color="primary"
                              size="small"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Dynamic Visualization */}
              {aiChartData && (
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <ChartIcon color="primary" />
                        <Typography variant="h6" fontWeight="bold">
                          Data Visualization
                        </Typography>
                      </Box>
                      <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {aiChartType === 'bar_chart' && (
                          <Bar 
                            data={aiChartData} 
                            options={{ 
                              responsive: true, 
                              maintainAspectRatio: false,
                              plugins: { legend: { display: false } }
                            }} 
                          />
                        )}
                        {aiChartType === 'line_chart' && (
                          <Line 
                            data={aiChartData} 
                            options={{ 
                              responsive: true, 
                              maintainAspectRatio: false,
                              plugins: { legend: { position: 'bottom' } }
                            }} 
                          />
                        )}
                        {aiChartType === 'doughnut_chart' && (
                          <Doughnut 
                            data={aiChartData} 
                            options={{ 
                              responsive: true, 
                              maintainAspectRatio: false,
                              plugins: { legend: { position: 'bottom' } }
                            }} 
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </>
          )}

          {/* Example/Quick Action Questions */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Quick Insights
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Click any question to get instant AI-powered insights with visualizations
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1} mt={2}>
                  {[
                    "Show me the breakdown of customers by status",
                    "What's the trend over the last 6 months?",
                    "Who are my top 5 leads?",
                    "Show me the distribution of my customers",
                    "How many new customers did we get this month?",
                    "What's my conversion rate from leads to customers?"
                  ].map((question, index) => (
                    <Chip
                      key={index}
                      label={question}
                      onClick={() => { setAiQuery(question); handleAIQuery(question); }}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { backgroundColor: 'primary.light', color: 'white' }
                      }}
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
      {/* Tab 3: AI Insights */}
      {currentTab === 3 && (
        <Grid container spacing={3}>
          <Grid size={12}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <LightbulbIcon color="warning" sx={{ fontSize: 32 }} />
              <Typography variant="h5" fontWeight="bold">
                AI-Powered Insights & Recommendations
              </Typography>
            </Box>
          </Grid>

          {ai_insights.map((insight, index) => (
            <Grid
              key={index}
              size={{
                xs: 12,
                md: 6
              }}>
              <Alert
                severity={getPriorityColor(insight.priority) as any}
                sx={{ height: '100%' }}
                action={
                  insight.action && (
                    <Button size="small" color="inherit" variant="outlined">
                      Take Action
                    </Button>
                  )
                }
              >
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  {insight.title}
                </Typography>
                <Typography variant="body2">
                  {insight.description}
                </Typography>
              </Alert>
            </Grid>
          ))}

          {ai_insights.length === 0 && (
            <Grid size={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 8 }}>
                  <LightbulbIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No insights available at the moment
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Keep adding data and we'll provide AI-powered recommendations
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}
    </Container>
      {/* Status Change Menu */}
      <Menu
        anchorEl={statusMenuAnchor}
        open={Boolean(statusMenuAnchor)}
        onClose={() => setStatusMenuAnchor(null)}
      >
        <MenuItem onClick={() => selectedLead && handleStatusChange(selectedLead.id, 'prospect')}>
          Move to Prospect
        </MenuItem>
        <MenuItem onClick={() => selectedLead && handleStatusChange(selectedLead.id, 'customer')}>
          Convert to Customer
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => selectedLead && handleStatusChange(selectedLead.id, 'cold_lead')}>
          Mark as Cold Lead
        </MenuItem>
        <MenuItem onClick={() => selectedLead && handleStatusChange(selectedLead.id, 'inactive')}>
          Mark as Inactive
        </MenuItem>
      </Menu>
    </>
  );
};

export default Dashboard;
