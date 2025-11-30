import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Tooltip,
  IconButton,
  Link
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Flag as FlagIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import { slaAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface CustomerSLAWidgetProps {
  customerId: string;
}

const CustomerSLAWidget: React.FC<CustomerSLAWidgetProps> = ({ customerId }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSLASummary();
  }, [customerId]);

  const loadSLASummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await slaAPI.getCustomerSummary(customerId);
      setSummary(response.data);
    } catch (err: any) {
      console.error('Error loading SLA summary:', err);
      setError(err.response?.data?.detail || 'Failed to load SLA summary');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'success';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <CheckCircleIcon color="success" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No SLA data available for this customer.</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6">SLA Status</Typography>
          </Box>
          <Chip
            icon={getStatusIcon(summary.overall_status)}
            label={summary.overall_status.toUpperCase()}
            color={getStatusColor(summary.overall_status)}
            size="small"
          />
        </Box>

        {/* Key Metrics */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Box sx={{ flex: 1, minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary">Total Tickets</Typography>
            <Typography variant="h5" fontWeight="bold">{summary.total_tickets}</Typography>
          </Box>
          <Box sx={{ flex: 1, minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary">Tickets with SLA</Typography>
            <Typography variant="h5" fontWeight="bold">{summary.tickets_with_sla}</Typography>
          </Box>
          <Box sx={{ flex: 1, minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary">Compliance Rate</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h5" fontWeight="bold">{summary.compliance_rate}%</Typography>
              <LinearProgress
                variant="determinate"
                value={summary.compliance_rate}
                sx={{
                  width: 60,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: '#e0e0e0',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: summary.compliance_rate >= 95 ? '#4caf50' :
                                     summary.compliance_rate >= 80 ? '#ff9800' : '#f44336',
                    borderRadius: 4
                  }
                }}
              />
            </Box>
          </Box>
        </Box>

        {/* Active Breaches */}
        {(summary.active_breaches.total > 0) && (
          <Alert 
            severity={summary.active_breaches.critical > 0 ? 'error' : 'warning'}
            sx={{ mb: 2 }}
            icon={<FlagIcon />}
          >
            <Box>
              <Typography variant="subtitle2" fontWeight="bold">
                Active SLA Breaches: {summary.active_breaches.total}
              </Typography>
              <Typography variant="body2">
                {summary.active_breaches.critical > 0 && (
                  <span style={{ color: '#f44336' }}>
                    {summary.active_breaches.critical} Critical
                  </span>
                )}
                {summary.active_breaches.critical > 0 && summary.active_breaches.warning > 0 && ' • '}
                {summary.active_breaches.warning > 0 && (
                  <span style={{ color: '#ff9800' }}>
                    {summary.active_breaches.warning} Warning
                  </span>
                )}
              </Typography>
            </Box>
          </Alert>
        )}

        {/* Recent Tickets */}
        {summary.recent_tickets && summary.recent_tickets.length > 0 && (
          <Box>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
              Recent Tickets with SLA
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Ticket</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell align="center">SLA Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.recent_tickets.slice(0, 5).map((ticket: any) => (
                    <TableRow key={ticket.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Link
                            component="button"
                            variant="body2"
                            onClick={() => navigate(`/helpdesk/${ticket.id}`)}
                            sx={{ textDecoration: 'none', cursor: 'pointer' }}
                          >
                            {ticket.ticket_number}
                          </Link>
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/helpdesk/${ticket.id}`)}
                          >
                            <OpenInNewIcon fontSize="small" />
                          </IconButton>
                        </Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {ticket.subject}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={ticket.status}
                          size="small"
                          color={ticket.status === 'resolved' || ticket.status === 'closed' ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={ticket.priority}
                          size="small"
                          color={
                            ticket.priority === 'urgent' ? 'error' :
                            ticket.priority === 'high' ? 'warning' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        {ticket.critical_breaches > 0 ? (
                          <Tooltip title={`${ticket.critical_breaches} critical breach(es)`}>
                            <ErrorIcon color="error" fontSize="small" />
                          </Tooltip>
                        ) : ticket.active_breaches > 0 ? (
                          <Tooltip title={`${ticket.active_breaches} warning breach(es)`}>
                            <WarningIcon color="warning" fontSize="small" />
                          </Tooltip>
                        ) : (
                          <Tooltip title="No active breaches">
                            <CheckCircleIcon color="success" fontSize="small" />
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {summary.recent_tickets.length > 5 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Showing 5 of {summary.recent_tickets.length} tickets
              </Typography>
            )}
          </Box>
        )}

        {(!summary.recent_tickets || summary.recent_tickets.length === 0) && (
          <Alert severity="info">No tickets with SLA found for this customer.</Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default CustomerSLAWidget;

