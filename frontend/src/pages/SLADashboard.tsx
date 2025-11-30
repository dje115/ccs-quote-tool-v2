import React, { useEffect, useState } from 'react';
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
  Tab
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { slaAPI } from '../services/api';
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

interface ComplianceData {
  period: {
    start: string;
    end: string;
  };
  total_tickets: number;
  first_response: {
    met: number;
    breached: number;
    compliance_rate: number;
    average_time_hours: number;
  };
  resolution: {
    met: number;
    breached: number;
    compliance_rate: number;
    average_time_hours: number;
  };
}

interface BreachAlert {
  id: string;
  ticket_id?: string;
  contract_id?: string;
  breach_type: string;
  breach_percent: number;
  alert_level: string;
  acknowledged: boolean;
  created_at: string;
}

const SLADashboard: React.FC = () => {
  const navigate = useNavigate();
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null);
  const [breachAlerts, setBreachAlerts] = useState<BreachAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [agentPerformance, setAgentPerformance] = useState<any[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [trends, setTrends] = useState<any[]>([]);
  const [loadingTrends, setLoadingTrends] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    loadData();
    loadAgentPerformance();
    if (tabValue === 1) {
      loadTrends();
    }
  }, [startDate, endDate, tabValue]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [complianceResponse, alertsResponse] = await Promise.all([
        slaAPI.getCompliance({ start_date: startDate, end_date: endDate }),
        slaAPI.listBreachAlerts({ acknowledged: false })
      ]);
      setComplianceData(complianceResponse.data);
      setBreachAlerts(alertsResponse.data || []);
    } catch (error) {
      console.error('Error loading SLA data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAgentPerformance = async () => {
    try {
      setLoadingAgents(true);
      const response = await slaAPI.getPerformanceByAgent({ start_date: startDate, end_date: endDate });
      setAgentPerformance(response.data?.performance_by_agent || []);
    } catch (error) {
      console.error('Error loading agent performance:', error);
    } finally {
      setLoadingAgents(false);
    }
  };

  const loadTrends = async () => {
    try {
      setLoadingTrends(true);
      const response = await slaAPI.getTrends({
        start_date: startDate,
        end_date: endDate,
        interval: 'day'
      });
      setTrends(response.data?.trends || []);
    } catch (error) {
      console.error('Error loading trends:', error);
    } finally {
      setLoadingTrends(false);
    }
  };

  const handleExportReport = async (format: 'csv' | 'pdf') => {
    try {
      const response = await slaAPI.exportReport({
        start_date: startDate,
        end_date: endDate,
        format
      });
      
      // Create download link
      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sla_report_${startDate}_${endDate}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report');
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await slaAPI.acknowledgeBreachAlert(alertId);
      loadData();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const chartData = complianceData ? {
    labels: ['First Response', 'Resolution'],
    datasets: [
      {
        label: 'Compliance Rate (%)',
        data: [
          complianceData.first_response.compliance_rate,
          complianceData.resolution.compliance_rate
        ],
        backgroundColor: ['#4caf50', '#2196f3'],
      }
    ]
  } : null;

  if (loading) {
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssessmentIcon /> SLA Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/sla/reports')}
          >
            Report Builder
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/sla')}
          >
            Manage Policies
          </Button>
        </Box>
      </Box>

      {/* Date Range Selector */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Button variant="contained" onClick={loadData}>
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Breach Alerts */}
      {breachAlerts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {breachAlerts.length} Unacknowledged SLA Breach Alert{breachAlerts.length !== 1 ? 's' : ''}
            </Typography>
            <Button
              size="small"
              onClick={() => navigate('/sla')}
            >
              View All
            </Button>
          </Box>
        </Alert>
      )}

      {/* Key Metrics */}
      {complianceData && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Tickets
                </Typography>
                <Typography variant="h4">
                  {complianceData.total_tickets}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  First Response Compliance
                </Typography>
                <Typography variant="h4" color={complianceData.first_response.compliance_rate >= 95 ? 'success.main' : 'warning.main'}>
                  {complianceData.first_response.compliance_rate.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg: {complianceData.first_response.average_time_hours.toFixed(1)}h
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Resolution Compliance
                </Typography>
                <Typography variant="h4" color={complianceData.resolution.compliance_rate >= 95 ? 'success.main' : 'warning.main'}>
                  {complianceData.resolution.compliance_rate.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg: {complianceData.resolution.average_time_hours.toFixed(1)}h
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Breaches
                </Typography>
                <Typography variant="h4" color="error.main">
                  {complianceData.first_response.breached + complianceData.resolution.breached}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Compliance Visualization */}
      {complianceData && tabValue === 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Compliance Rates
              </Typography>
              <Box sx={{ height: 300, mt: 2 }}>
                <Doughnut
                  data={{
                    labels: ['First Response', 'Resolution'],
                    datasets: [
                      {
                        label: 'Compliance Rate (%)',
                        data: [
                          complianceData.first_response.compliance_rate,
                          complianceData.resolution.compliance_rate
                        ],
                        backgroundColor: [
                          complianceData.first_response.compliance_rate >= 95 ? '#4caf50' : '#ff9800',
                          complianceData.resolution.compliance_rate >= 95 ? '#2196f3' : '#f44336'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom'
                      },
                      tooltip: {
                        callbacks: {
                          label: (context: any) => {
                            return `${context.label}: ${context.parsed.toFixed(1)}%`;
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Breach Breakdown
              </Typography>
              <Box sx={{ height: 300, mt: 2 }}>
                <Bar
                  data={{
                    labels: ['First Response', 'Resolution'],
                    datasets: [
                      {
                        label: 'Met',
                        data: [
                          complianceData.first_response.met,
                          complianceData.resolution.met
                        ],
                        backgroundColor: '#4caf50'
                      },
                      {
                        label: 'Breached',
                        data: [
                          complianceData.first_response.breached,
                          complianceData.resolution.breached
                        ],
                        backgroundColor: '#f44336'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true
                      }
                    },
                    plugins: {
                      legend: {
                        position: 'top'
                      }
                    }
                  }}
                />
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Agent Performance Table */}
      {agentPerformance.length > 0 && tabValue === 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Agent Performance
          </Typography>
          {loadingAgents ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Agent</strong></TableCell>
                    <TableCell><strong>Total Tickets</strong></TableCell>
                    <TableCell><strong>FR Breaches</strong></TableCell>
                    <TableCell><strong>FR Compliance</strong></TableCell>
                    <TableCell><strong>Res Breaches</strong></TableCell>
                    <TableCell><strong>Res Compliance</strong></TableCell>
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
                      <TableCell>{agent.total_tickets}</TableCell>
                      <TableCell>
                        <Chip
                          label={agent.first_response.breaches}
                          size="small"
                          color={agent.first_response.breaches > 0 ? 'error' : 'success'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color={agent.first_response.compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {agent.first_response.compliance_rate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={agent.resolution.breaches}
                          size="small"
                          color={agent.resolution.breaches > 0 ? 'error' : 'success'}
                        />
                      </TableCell>
                      <TableCell>
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
          )}
        </Paper>
      )}

      {/* Trends View */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            SLA Compliance Trends
          </Typography>
          {loadingTrends ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : trends.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Period</strong></TableCell>
                    <TableCell><strong>Total Tickets</strong></TableCell>
                    <TableCell><strong>FR Compliance</strong></TableCell>
                    <TableCell><strong>FR Breaches</strong></TableCell>
                    <TableCell><strong>Res Compliance</strong></TableCell>
                    <TableCell><strong>Res Breaches</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trends.map((trend, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>
                        {new Date(trend.period).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{trend.total_tickets}</TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color={trend.first_response.compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {trend.first_response.compliance_rate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>{trend.first_response.breaches}</TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color={trend.resolution.compliance_rate >= 95 ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {trend.resolution.compliance_rate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>{trend.resolution.breaches}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ p: 3, textAlign: 'center' }}>
              No trend data available for the selected period.
            </Typography>
          )}
        </Paper>
      )}

      {/* Breach Alerts Table */}
      {breachAlerts.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent Breach Alerts
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Breach %</strong></TableCell>
                  <TableCell><strong>Level</strong></TableCell>
                  <TableCell><strong>Date</strong></TableCell>
                  <TableCell align="right"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {breachAlerts.slice(0, 10).map((alert) => (
                  <TableRow key={alert.id} hover>
                    <TableCell>
                      {alert.breach_type === 'first_response' ? 'First Response' : 'Resolution'}
                    </TableCell>
                    <TableCell>{alert.breach_percent}%</TableCell>
                    <TableCell>
                      <Chip
                        label={alert.alert_level}
                        size="small"
                        color={alert.alert_level === 'critical' ? 'error' : 'warning'}
                        icon={alert.alert_level === 'critical' ? <WarningIcon /> : <CheckCircleIcon />}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(alert.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                      >
                        Acknowledge
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Container>
  );
};

export default SLADashboard;

