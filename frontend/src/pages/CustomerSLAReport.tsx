import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  CircularProgress,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  ArrowBack as ArrowBackIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon
} from '@mui/icons-material';
import { slaAPI } from '../services/api';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
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

interface CustomerReport {
  customer_id: string;
  customer_name: string;
  period: {
    start: string;
    end: string;
  };
  summary: {
    total_tickets: number;
    tickets_with_sla: number;
    resolved_tickets: number;
    responded_tickets: number;
    avg_resolution_hours: number | null;
    avg_first_response_hours: number | null;
  };
  sla_metrics: {
    first_response_breaches: number;
    resolution_breaches: number;
    first_response_compliance_rate: number;
    resolution_compliance_rate: number;
    active_breach_alerts: number;
    critical_breaches: number;
    warning_breaches: number;
  };
  distributions: {
    priority: Record<string, number>;
    status: Record<string, number>;
    type: Record<string, number>;
  };
  recent_tickets: Array<{
    id: string;
    ticket_number: string;
    subject: string;
    status: string;
    priority: string;
    type: string;
    created_at: string;
    resolved_at: string | null;
    first_response_at: string | null;
    sla_policy_id: string | null;
    sla_first_response_breached: boolean;
    sla_resolution_breached: boolean;
    active_breaches: number;
    critical_breaches: number;
  }>;
}

const CustomerSLAReport: React.FC = () => {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<CustomerReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    if (customerId) {
      loadReport();
    }
  }, [customerId, startDate, endDate]);

  const loadReport = async () => {
    if (!customerId) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await slaAPI.getCustomerReport(customerId, startDate, endDate);
      setReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load customer SLA report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'pdf' | 'excel' = 'csv') => {
    if (!report || !customerId) return;
    
    try {
      if (format === 'csv') {
        // Create CSV content
        const headers = [
          'Ticket Number',
          'Subject',
          'Status',
          'Priority',
          'Type',
          'Created At',
          'Resolved At',
          'First Response At',
          'SLA First Response Breached',
          'SLA Resolution Breached',
          'Active Breaches'
        ];
        
        const rows = report.recent_tickets.map(ticket => [
          ticket.ticket_number,
          ticket.subject,
          ticket.status,
          ticket.priority,
          ticket.type,
          ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '',
          ticket.resolved_at ? new Date(ticket.resolved_at).toLocaleString() : '',
          ticket.first_response_at ? new Date(ticket.first_response_at).toLocaleString() : '',
          ticket.sla_first_response_breached ? 'Yes' : 'No',
          ticket.sla_resolution_breached ? 'Yes' : 'No',
          ticket.active_breaches
        ]);
        
        const csvContent = [
          `Customer SLA Report: ${report.customer_name}`,
          `Period: ${report.period.start} to ${report.period.end}`,
          '',
          headers.join(','),
          ...rows.map((row: any[]) => row.map((cell: any) => `"${cell}"`).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `customer_sla_report_${customerId}_${startDate}_${endDate}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        // For PDF and Excel, we'll need backend support
        // For now, show a message
        alert(`${format.toUpperCase()} export will be available soon. Please use CSV export for now.`);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mt: 2 }}>
          Go Back
        </Button>
      </Container>
    );
  }

  if (!report) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Alert severity="info">No report data available.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mb: 1 }}>
            Back
          </Button>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon /> SLA Report: {report.customer_name}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('csv')}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('pdf')}
          >
            Export PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('excel')}
          >
            Export Excel
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
          <Button variant="contained" onClick={loadReport}>
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Tickets
              </Typography>
              <Typography variant="h4">{report.summary.total_tickets}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Tickets with SLA
              </Typography>
              <Typography variant="h4">{report.summary.tickets_with_sla}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                First Response Compliance
              </Typography>
              <Typography
                variant="h4"
                color={report.sla_metrics.first_response_compliance_rate >= 95 ? 'success.main' : 'warning.main'}
              >
                {report.sla_metrics.first_response_compliance_rate.toFixed(1)}%
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
              <Typography
                variant="h4"
                color={report.sla_metrics.resolution_compliance_rate >= 95 ? 'success.main' : 'warning.main'}
              >
                {report.sla_metrics.resolution_compliance_rate.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Overview" />
          <Tab label="Distributions" />
          <Tab label="Recent Tickets" />
        </Tabs>
      </Paper>

      {/* Overview Tab */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                SLA Compliance Rates
              </Typography>
              <Box sx={{ height: 300, mt: 2 }}>
                <Doughnut
                  data={{
                    labels: ['First Response', 'Resolution'],
                    datasets: [
                      {
                        label: 'Compliance Rate (%)',
                        data: [
                          report.sla_metrics.first_response_compliance_rate,
                          report.sla_metrics.resolution_compliance_rate
                        ],
                        backgroundColor: [
                          report.sla_metrics.first_response_compliance_rate >= 95 ? '#4caf50' : '#ff9800',
                          report.sla_metrics.resolution_compliance_rate >= 95 ? '#2196f3' : '#f44336'
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
                      legend: { position: 'bottom' },
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
                Summary Statistics
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Resolved Tickets
                    </Typography>
                    <Typography variant="h6">{report.summary.resolved_tickets}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Responded Tickets
                    </Typography>
                    <Typography variant="h6">{report.summary.responded_tickets}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Avg Resolution Time
                    </Typography>
                    <Typography variant="h6">
                      {report.summary.avg_resolution_hours
                        ? `${report.summary.avg_resolution_hours.toFixed(1)} hrs`
                        : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Avg First Response Time
                    </Typography>
                    <Typography variant="h6">
                      {report.summary.avg_first_response_hours
                        ? `${report.summary.avg_first_response_hours.toFixed(1)} hrs`
                        : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Active Breach Alerts
                    </Typography>
                    <Typography variant="h6" color="error.main">
                      {report.sla_metrics.active_breach_alerts}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Critical Breaches
                    </Typography>
                    <Typography variant="h6" color="error.main">
                      {report.sla_metrics.critical_breaches}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Distributions Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Priority Distribution
              </Typography>
              <Box sx={{ height: 300, mt: 2 }}>
                <Doughnut
                  data={{
                    labels: Object.keys(report.distributions.priority),
                    datasets: [
                      {
                        data: Object.values(report.distributions.priority),
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
                    labels: Object.keys(report.distributions.status),
                    datasets: [
                      {
                        data: Object.values(report.distributions.status),
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
                    labels: Object.keys(report.distributions.type),
                    datasets: [
                      {
                        data: Object.values(report.distributions.type),
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

      {/* Recent Tickets Tab */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent Tickets ({report.recent_tickets.length})
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Ticket #</strong></TableCell>
                  <TableCell><strong>Subject</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Priority</strong></TableCell>
                  <TableCell><strong>SLA Status</strong></TableCell>
                  <TableCell><strong>Created</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {report.recent_tickets.map((ticket) => (
                  <TableRow key={ticket.id} hover>
                    <TableCell>{ticket.ticket_number}</TableCell>
                    <TableCell>{ticket.subject}</TableCell>
                    <TableCell>
                      <Chip
                        label={ticket.status}
                        size="small"
                        color={
                          ticket.status === 'open' ? 'error' :
                          ticket.status === 'in_progress' ? 'warning' :
                          ticket.status === 'resolved' ? 'success' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ticket.priority}
                        size="small"
                        color={
                          ticket.priority === 'urgent' ? 'error' :
                          ticket.priority === 'high' ? 'warning' :
                          ticket.priority === 'medium' ? 'info' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      {ticket.sla_policy_id ? (
                        <Chip
                          label={
                            ticket.sla_first_response_breached || ticket.sla_resolution_breached
                              ? 'Breached'
                              : 'Compliant'
                          }
                          size="small"
                          color={
                            ticket.sla_first_response_breached || ticket.sla_resolution_breached
                              ? 'error'
                              : 'success'
                          }
                        />
                      ) : (
                        <Chip label="No SLA" size="small" color="default" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      {ticket.created_at
                        ? new Date(ticket.created_at).toLocaleDateString()
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        onClick={() => navigate(`/helpdesk/${ticket.id}`)}
                      >
                        View
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

export default CustomerSLAReport;

