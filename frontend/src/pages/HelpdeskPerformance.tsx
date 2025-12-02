import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as AccessTimeIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { helpdeskAPI, slaAPI } from '../services/api';
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

interface VolumeTrend {
  period: string;
  total_tickets: number;
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
}

interface ResolutionTimeAnalytics {
  group_value: string;
  total_tickets: number;
  avg_resolution_hours: number;
  avg_first_response_hours: number;
  min_resolution_hours: number;
  max_resolution_hours: number;
}

interface Distributions {
  priority_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
}

interface CustomerPerformance {
  customer_id: string;
  customer_name: string;
  total_tickets: number;
  avg_resolution_hours: number;
  avg_first_response_hours: number;
  first_response_breaches: number;
  resolution_breaches: number;
  first_response_compliance_rate: number;
  resolution_compliance_rate: number;
}

interface AgentWorkload {
  agent_id: string;
  agent_name: string;
  agent_email: string;
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  avg_resolution_hours: number | null;
}

const HelpdeskPerformance: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [interval, setInterval] = useState<'day' | 'week' | 'month'>('day');
  const [groupBy, setGroupBy] = useState<'priority' | 'type' | 'status'>('priority');
  const [tabValue, setTabValue] = useState(0);
  
  // Data states
  const [volumeTrends, setVolumeTrends] = useState<VolumeTrend[]>([]);
  const [resolutionAnalytics, setResolutionAnalytics] = useState<ResolutionTimeAnalytics[]>([]);
  const [distributions, setDistributions] = useState<Distributions | null>(null);
  const [customerPerformance, setCustomerPerformance] = useState<CustomerPerformance[]>([]);
  const [agentWorkload, setAgentWorkload] = useState<AgentWorkload[]>([]);
  const [agentPerformance, setAgentPerformance] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadAllData();
  }, [startDate, endDate, interval, groupBy, tabValue]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      
      // Load stats
      const statsResponse = await helpdeskAPI.getTicketStats();
      setStats(statsResponse.data);
      
      // Load data based on active tab
      if (tabValue === 0) {
        // Overview - load volume trends and distributions
        await Promise.all([
          loadVolumeTrends(),
          loadDistributions()
        ]);
      } else if (tabValue === 1) {
        // Agent Performance
        await Promise.all([
          loadAgentPerformance(),
          loadAgentWorkload()
        ]);
      } else if (tabValue === 2) {
        // Resolution Times
        await loadResolutionAnalytics();
      } else if (tabValue === 3) {
        // Customer Performance
        await loadCustomerPerformance();
      }
    } catch (error) {
      console.error('Error loading helpdesk performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVolumeTrends = async () => {
    try {
      const response = await helpdeskAPI.getVolumeTrends(startDate, endDate, interval);
      setVolumeTrends(response.data?.trends || []);
    } catch (error) {
      console.error('Error loading volume trends:', error);
    }
  };

  const loadResolutionAnalytics = async () => {
    try {
      const response = await helpdeskAPI.getResolutionTimeAnalytics(startDate, endDate, groupBy);
      setResolutionAnalytics(response.data?.analytics || []);
    } catch (error) {
      console.error('Error loading resolution analytics:', error);
    }
  };

  const loadDistributions = async () => {
    try {
      const response = await helpdeskAPI.getDistributions(startDate, endDate);
      setDistributions(response.data || null);
    } catch (error) {
      console.error('Error loading distributions:', error);
    }
  };

  const loadCustomerPerformance = async () => {
    try {
      const response = await helpdeskAPI.getCustomerPerformance(startDate, endDate, 20);
      setCustomerPerformance(response.data?.customer_performance || []);
    } catch (error) {
      console.error('Error loading customer performance:', error);
    }
  };

  const loadAgentWorkload = async () => {
    try {
      const response = await helpdeskAPI.getAgentWorkload(startDate, endDate);
      setAgentWorkload(response.data?.agent_workload || []);
    } catch (error) {
      console.error('Error loading agent workload:', error);
    }
  };

  const loadAgentPerformance = async () => {
    try {
      const response = await slaAPI.getPerformanceByAgent({ start_date: startDate, end_date: endDate });
      setAgentPerformance(response.data?.performance_by_agent || []);
    } catch (error) {
      console.error('Error loading agent performance:', error);
    }
  };

  const handleExport = async (format: 'csv' | 'pdf' | 'excel', reportType: string = 'overview') => {
    try {
      const response = await helpdeskAPI.exportAnalytics(startDate, endDate, format, reportType);
      
      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : 
              format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 
              'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const extension = format === 'excel' ? 'xlsx' : format;
      link.download = `helpdesk_performance_${reportType}_${startDate}_${endDate}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report');
    }
  };

  if (loading && !stats) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssessmentIcon /> Helpdesk Performance Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {
              const reportType = tabValue === 0 ? 'overview' : 
                               tabValue === 1 ? 'agents' : 
                               tabValue === 2 ? 'resolution' : 'customers';
              handleExport('csv', reportType);
            }}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {
              const reportType = tabValue === 0 ? 'overview' : 
                               tabValue === 1 ? 'agents' : 
                               tabValue === 2 ? 'resolution' : 'customers';
              handleExport('pdf', reportType);
            }}
          >
            Export PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {
              const reportType = tabValue === 0 ? 'overview' : 
                               tabValue === 1 ? 'agents' : 
                               tabValue === 2 ? 'resolution' : 'customers';
              handleExport('excel', reportType);
            }}
          >
            Export Excel
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAllData}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Tickets
                </Typography>
                <Typography variant="h4">{stats.total || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Open Tickets
                </Typography>
                <Typography variant="h4" color="error.main">{stats.open || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  In Progress
                </Typography>
                <Typography variant="h4" color="warning.main">{stats.in_progress || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Resolved
                </Typography>
                <Typography variant="h4" color="success.main">{stats.resolved || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          {stats.sla && (
            <>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      SLA Compliance Rate
                    </Typography>
                    <Typography variant="h4" color={stats.sla.compliance_rate >= 95 ? 'success.main' : 'warning.main'}>
                      {stats.sla.compliance_rate?.toFixed(1) || 0}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Active Breaches
                    </Typography>
                    <Typography variant="h4" color="error.main">
                      {stats.sla.active_breach_alerts || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </>
          )}
        </Grid>
      )}

      {/* Date Range and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <TextField
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <TextField
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Grid>
          {tabValue === 0 && (
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Interval</InputLabel>
                <Select
                  value={interval}
                  label="Interval"
                  onChange={(e) => setInterval(e.target.value as 'day' | 'week' | 'month')}
                >
                  <MenuItem value="day">Daily</MenuItem>
                  <MenuItem value="week">Weekly</MenuItem>
                  <MenuItem value="month">Monthly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
          {tabValue === 2 && (
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Group By</InputLabel>
                <Select
                  value={groupBy}
                  label="Group By"
                  onChange={(e) => setGroupBy(e.target.value as 'priority' | 'type' | 'status')}
                >
                  <MenuItem value="priority">Priority</MenuItem>
                  <MenuItem value="type">Type</MenuItem>
                  <MenuItem value="status">Status</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Overview" />
          <Tab label="Agent Performance" />
          <Tab label="Resolution Times" />
          <Tab label="Customer Performance" />
        </Tabs>
      </Paper>

      {/* Overview Tab */}
      {tabValue === 0 && (
        <>
          {/* Volume Trends Chart */}
          {volumeTrends.length > 0 && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Ticket Volume Trends
              </Typography>
              <Box sx={{ height: 400, mt: 2 }}>
                <Line
                  data={{
                    labels: volumeTrends.map(t => new Date(t.period).toLocaleDateString()),
                    datasets: [
                      {
                        label: 'Total Tickets',
                        data: volumeTrends.map(t => t.total_tickets),
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        fill: true,
                        tension: 0.4
                      },
                      {
                        label: 'Open',
                        data: volumeTrends.map(t => t.open),
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        fill: true,
                        tension: 0.4
                      },
                      {
                        label: 'In Progress',
                        data: volumeTrends.map(t => t.in_progress),
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        fill: true,
                        tension: 0.4
                      },
                      {
                        label: 'Resolved',
                        data: volumeTrends.map(t => t.resolved),
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        fill: true,
                        tension: 0.4
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { position: 'top' },
                      title: { display: false }
                    },
                    scales: {
                      y: { beginAtZero: true }
                    }
                  }}
                />
              </Box>
            </Paper>
          )}

          {/* Distributions */}
          {distributions && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Priority Distribution
                  </Typography>
                  <Box sx={{ height: 300, mt: 2 }}>
                    <Doughnut
                      data={{
                        labels: Object.keys(distributions.priority_distribution),
                        datasets: [
                          {
                            data: Object.values(distributions.priority_distribution),
                            backgroundColor: [
                              '#f44336',
                              '#ff9800',
                              '#2196f3',
                              '#4caf50',
                              '#9e9e9e'
                            ]
                          }
                        ]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: 'bottom' }
                        }
                      }}
                    />
                  </Box>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Status Distribution
                  </Typography>
                  <Box sx={{ height: 300, mt: 2 }}>
                    <Doughnut
                      data={{
                        labels: Object.keys(distributions.status_distribution),
                        datasets: [
                          {
                            data: Object.values(distributions.status_distribution),
                            backgroundColor: [
                              '#f44336',
                              '#ff9800',
                              '#2196f3',
                              '#4caf50',
                              '#9e9e9e'
                            ]
                          }
                        ]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: 'bottom' }
                        }
                      }}
                    />
                  </Box>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Type Distribution
                  </Typography>
                  <Box sx={{ height: 300, mt: 2 }}>
                    <Doughnut
                      data={{
                        labels: Object.keys(distributions.type_distribution),
                        datasets: [
                          {
                            data: Object.values(distributions.type_distribution),
                            backgroundColor: [
                              '#2196f3',
                              '#4caf50',
                              '#ff9800',
                              '#9e9e9e'
                            ]
                          }
                        ]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: 'bottom' }
                        }
                      }}
                    />
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          )}
        </>
      )}

      {/* Agent Performance Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Agent Performance (SLA Compliance)
              </Typography>
              {agentPerformance.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Agent</strong></TableCell>
                        <TableCell align="right"><strong>Total</strong></TableCell>
                        <TableCell align="right"><strong>FR Compliance</strong></TableCell>
                        <TableCell align="right"><strong>Res Compliance</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {agentPerformance.map((agent, idx) => (
                        <TableRow key={idx} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {agent.agent_name}
                            </Typography>
                            {agent.agent_email && (
                              <Typography variant="caption" color="text.secondary">
                                {agent.agent_email}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">{agent.total_tickets}</TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color={agent.first_response.compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                              fontWeight="medium"
                            >
                              {agent.first_response.compliance_rate.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color={agent.resolution.compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                              fontWeight="medium"
                            >
                              {agent.resolution.compliance_rate.toFixed(1)}%
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">No agent performance data available.</Alert>
              )}
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Agent Workload
              </Typography>
              {agentWorkload.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Agent</strong></TableCell>
                        <TableCell align="right"><strong>Total</strong></TableCell>
                        <TableCell align="right"><strong>Open</strong></TableCell>
                        <TableCell align="right"><strong>In Progress</strong></TableCell>
                        <TableCell align="right"><strong>Resolved</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {agentWorkload.map((agent, idx) => (
                        <TableRow key={idx} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {agent.agent_name}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">{agent.total_tickets}</TableCell>
                          <TableCell align="right">
                            <Chip label={agent.open_tickets} size="small" color="error" />
                          </TableCell>
                          <TableCell align="right">
                            <Chip label={agent.in_progress_tickets} size="small" color="warning" />
                          </TableCell>
                          <TableCell align="right">
                            <Chip label={agent.resolved_tickets} size="small" color="success" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">No agent workload data available.</Alert>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Resolution Times Tab */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Resolution Time Analytics (Grouped by {groupBy})
          </Typography>
          {resolutionAnalytics.length > 0 ? (
            <>
              <Box sx={{ height: 400, mt: 2, mb: 3 }}>
                <Bar
                  data={{
                    labels: resolutionAnalytics.map(a => a.group_value),
                    datasets: [
                      {
                        label: 'Avg Resolution Time (hours)',
                        data: resolutionAnalytics.map(a => a.avg_resolution_hours),
                        backgroundColor: '#2196f3'
                      },
                      {
                        label: 'Avg First Response Time (hours)',
                        data: resolutionAnalytics.map(a => a.avg_first_response_hours),
                        backgroundColor: '#4caf50'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { position: 'top' }
                    },
                    scales: {
                      y: { beginAtZero: true }
                    }
                  }}
                />
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>{groupBy.charAt(0).toUpperCase() + groupBy.slice(1)}</strong></TableCell>
                      <TableCell align="right"><strong>Total Tickets</strong></TableCell>
                      <TableCell align="right"><strong>Avg Resolution (hrs)</strong></TableCell>
                      <TableCell align="right"><strong>Avg First Response (hrs)</strong></TableCell>
                      <TableCell align="right"><strong>Min Resolution (hrs)</strong></TableCell>
                      <TableCell align="right"><strong>Max Resolution (hrs)</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {resolutionAnalytics.map((analytics, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>
                          <Chip label={analytics.group_value} size="small" />
                        </TableCell>
                        <TableCell align="right">{analytics.total_tickets}</TableCell>
                        <TableCell align="right">{analytics.avg_resolution_hours.toFixed(2)}</TableCell>
                        <TableCell align="right">{analytics.avg_first_response_hours.toFixed(2)}</TableCell>
                        <TableCell align="right">{analytics.min_resolution_hours.toFixed(2)}</TableCell>
                        <TableCell align="right">{analytics.max_resolution_hours.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          ) : (
            <Alert severity="info">No resolution time data available for the selected period.</Alert>
          )}
        </Paper>
      )}

      {/* Customer Performance Tab */}
      {tabValue === 3 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Customer Performance by SLA Compliance
          </Typography>
          {customerPerformance.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Customer</strong></TableCell>
                    <TableCell align="right"><strong>Total Tickets</strong></TableCell>
                    <TableCell align="right"><strong>Avg Resolution (hrs)</strong></TableCell>
                    <TableCell align="right"><strong>Avg First Response (hrs)</strong></TableCell>
                    <TableCell align="right"><strong>FR Breaches</strong></TableCell>
                    <TableCell align="right"><strong>FR Compliance</strong></TableCell>
                    <TableCell align="right"><strong>Res Breaches</strong></TableCell>
                    <TableCell align="right"><strong>Res Compliance</strong></TableCell>
                    <TableCell align="right"><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {customerPerformance.map((customer) => (
                    <TableRow key={customer.customer_id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {customer.customer_name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{customer.total_tickets}</TableCell>
                      <TableCell align="right">{customer.avg_resolution_hours.toFixed(1)}</TableCell>
                      <TableCell align="right">{customer.avg_first_response_hours.toFixed(1)}</TableCell>
                      <TableCell align="right">
                        <Chip
                          label={customer.first_response_breaches}
                          size="small"
                          color={customer.first_response_breaches > 0 ? 'error' : 'success'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={customer.first_response_compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {customer.first_response_compliance_rate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={customer.resolution_breaches}
                          size="small"
                          color={customer.resolution_breaches > 0 ? 'error' : 'success'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={customer.resolution_compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {customer.resolution_compliance_rate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          onClick={() => navigate(`/sla/customers/${customer.customer_id}/report`)}
                        >
                          View Report
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No customer performance data available.</Alert>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default HelpdeskPerformance;

