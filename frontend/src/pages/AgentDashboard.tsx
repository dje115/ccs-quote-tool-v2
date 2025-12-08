import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Alert,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  AccessTime as AccessTimeIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { helpdeskAPI } from '../services/api';

interface DashboardData {
  my_tickets: any[];
  status_counts: Record<string, number>;
  priority_breakdown: Record<string, number>;
  sla: {
    breached: number;
    at_risk: number;
  };
  recent_activity: any[];
  overdue_tickets: any[];
  time_tracking: {
    today_hours: number;
    week_hours: number;
  };
}

const AgentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.getAgentDashboard();
      setDashboardData(response.data);
    } catch (err: any) {
      console.error('Error loading dashboard:', err);
      setError(err.response?.data?.detail || 'Error loading dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'open':
        return 'error';
      case 'in_progress':
        return 'warning';
      case 'resolved':
        return 'success';
      case 'closed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
        <Button onClick={loadDashboard} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Container>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Agent Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadDashboard}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* My Tickets Summary */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="My Assigned Tickets"
              avatar={<AssignmentIcon color="primary" />}
            />
            <CardContent>
              <Box sx={{ mb: 2 }}>
                <Grid container spacing={2}>
                  {Object.entries(dashboardData.status_counts).map(([status, count]) => (
                    <Grid size={{ xs: 6, sm: 3 }} key={status}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color={`${getStatusColor(status)}.main`}>
                          {count}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {status.replace('_', ' ')}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Recent Tickets:
              </Typography>
              <List dense>
                {dashboardData.my_tickets.slice(0, 5).map((ticket) => (
                  <ListItem
                    key={ticket.id}
                    button
                    onClick={() => navigate(`/helpdesk/tickets/${ticket.id}`)}
                    sx={{ borderRadius: 1, mb: 0.5 }}
                  >
                    <ListItemIcon>
                      <AssignmentIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={ticket.ticket_number}
                      secondary={ticket.subject}
                    />
                    <Chip
                      label={ticket.priority}
                      size="small"
                      color={getPriorityColor(ticket.priority) as any}
                      sx={{ ml: 1 }}
                    />
                  </ListItem>
                ))}
                {dashboardData.my_tickets.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                    No assigned tickets
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Priority Breakdown */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="Priority Breakdown"
              avatar={<TrendingUpIcon color="primary" />}
            />
            <CardContent>
              {Object.entries(dashboardData.priority_breakdown).map(([priority, count]) => (
                <Box key={priority} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" textTransform="capitalize">
                      {priority}
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {count}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(count / Math.max(...Object.values(dashboardData.priority_breakdown))) * 100}
                    color={getPriorityColor(priority) as any}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                </Box>
              ))}
              {Object.keys(dashboardData.priority_breakdown).length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No active tickets
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* SLA Status */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="SLA Status"
              avatar={<ScheduleIcon color="primary" />}
            />
            <CardContent>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {dashboardData.sla.breached > 0 ? (
                    <WarningIcon color="error" />
                  ) : (
                    <CheckCircleIcon color="success" />
                  )}
                  <Typography variant="h6">
                    {dashboardData.sla.breached} Breached
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {dashboardData.sla.at_risk} tickets with active SLA
                </Typography>
              </Box>
              {dashboardData.overdue_tickets.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>
                    Overdue Tickets:
                  </Typography>
                  <List dense>
                    {dashboardData.overdue_tickets.map((ticket) => (
                      <ListItem
                        key={ticket.id}
                        button
                        onClick={() => navigate(`/helpdesk/tickets/${ticket.id}`)}
                        sx={{ borderRadius: 1, mb: 0.5 }}
                      >
                        <ListItemIcon>
                          <WarningIcon color="error" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={ticket.ticket_number}
                          secondary={ticket.subject}
                        />
                        <Chip
                          label={ticket.priority}
                          size="small"
                          color={getPriorityColor(ticket.priority) as any}
                          sx={{ ml: 1 }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Time Tracking */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="Time Tracking"
              avatar={<AccessTimeIcon color="primary" />}
            />
            <CardContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Today: {dashboardData.time_tracking.today_hours.toFixed(2)}h
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This Week: {dashboardData.time_tracking.week_hours.toFixed(2)}h
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min((dashboardData.time_tracking.today_hours / 8) * 100, 100)}
                color={dashboardData.time_tracking.today_hours >= 8 ? 'success' : 'primary'}
                sx={{ height: 8, borderRadius: 1, mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {dashboardData.time_tracking.today_hours >= 8 ? 'Full day logged' : `${(8 - dashboardData.time_tracking.today_hours).toFixed(2)}h remaining to 8h target`}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader
              title="Recent Activity (Last 24 Hours)"
              avatar={<ScheduleIcon color="primary" />}
            />
            <CardContent>
              <List>
                {dashboardData.recent_activity.map((ticket, index) => (
                  <React.Fragment key={ticket.id}>
                    <ListItem
                      button
                      onClick={() => navigate(`/helpdesk/tickets/${ticket.id}`)}
                    >
                      <ListItemIcon>
                        <AssignmentIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={ticket.ticket_number}
                        secondary={
                          <Box>
                            <Typography variant="body2">{ticket.subject}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              Updated: {new Date(ticket.updated_at).toLocaleString()}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={ticket.status}
                        size="small"
                        color={getStatusColor(ticket.status) as any}
                        sx={{ ml: 1 }}
                      />
                      <Chip
                        label={ticket.priority}
                        size="small"
                        color={getPriorityColor(ticket.priority) as any}
                        sx={{ ml: 1 }}
                      />
                    </ListItem>
                    {index < dashboardData.recent_activity.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
                {dashboardData.recent_activity.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                    No recent activity
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AgentDashboard;

