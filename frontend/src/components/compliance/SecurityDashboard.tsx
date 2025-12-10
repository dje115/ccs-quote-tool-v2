import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  IconButton,
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  FilterList,
} from '@mui/icons-material';
import { complianceAPI } from '../../services/api';

interface SecurityEvent {
  id: string;
  event_type: string;
  severity: string;
  description: string;
  ip_address?: string;
  occurred_at: string;
  tenant_id?: string;
  user_id?: string;
}

interface SecurityStatistics {
  total_events: number;
  by_type: Record<string, number>;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  failed_logins: number;
  account_lockouts: number;
  rate_limit_exceeded: number;
}

const SecurityDashboard: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [statistics, setStatistics] = useState<SecurityStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hours, setHours] = useState(24);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [eventsData, statsData] = await Promise.all([
        complianceAPI.getSecurityEvents({
          hours,
          limit: 100,
          event_type: eventTypeFilter !== 'all' ? eventTypeFilter : undefined,
          severity: severityFilter !== 'all' ? severityFilter : undefined,
        }),
        complianceAPI.getSecurityStatistics({ hours }),
      ]);
      setEvents(eventsData);
      setStatistics(statsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load security data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [hours, eventTypeFilter, severityFilter]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatEventType = (type: string) => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (loading && !statistics) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {statistics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Events (24h)
                </Typography>
                <Typography variant="h4">{statistics.total_events}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Failed Logins
                </Typography>
                <Typography variant="h4" color="error">
                  {statistics.failed_logins}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Account Lockouts
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {statistics.account_lockouts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Rate Limit Violations
                </Typography>
                <Typography variant="h4" color="info.main">
                  {statistics.rate_limit_exceeded}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              label="Time Period (hours)"
              type="number"
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
              fullWidth
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Event Type</InputLabel>
              <Select
                value={eventTypeFilter}
                label="Event Type"
                onChange={(e) => setEventTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="failed_login">Failed Login</MenuItem>
                <MenuItem value="account_locked">Account Locked</MenuItem>
                <MenuItem value="rate_limit_exceeded">Rate Limit</MenuItem>
                <MenuItem value="two_factor_failed">2FA Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Severity</InputLabel>
              <Select
                value={severityFilter}
                label="Severity"
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <MenuItem value="all">All Severities</MenuItem>
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchData}
              fullWidth
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Events Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Event Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>IP Address</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : events.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No security events found
                </TableCell>
              </TableRow>
            ) : (
              events.map((event) => (
                <TableRow key={event.id}>
                  <TableCell>
                    {new Date(event.occurred_at).toLocaleString()}
                  </TableCell>
                  <TableCell>{formatEventType(event.event_type)}</TableCell>
                  <TableCell>
                    <Chip
                      label={event.severity}
                      color={getSeverityColor(event.severity) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{event.description}</TableCell>
                  <TableCell>{event.ip_address || 'N/A'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SecurityDashboard;

