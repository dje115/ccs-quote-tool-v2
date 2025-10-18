import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  AlertTitle,
  Divider,
  CircularProgress,
  Stack,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Email as EmailIcon,
  Business as BusinessIcon,
  Add as AddIcon,
  Close as CloseIcon,
  AutoAwesome as AIIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Notes as NotesIcon,
  Call as CallIcon,
  Event as EventIcon,
  Task as TaskIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { activityAPI } from '../services/api';

interface Activity {
  id: string;
  activity_type: string;
  activity_date: string;
  notes: string;
  notes_cleaned?: string;
  ai_suggested_action?: string;
  subject?: string;
  duration_minutes?: number;
  outcome?: string;
  follow_up_required: boolean;
  follow_up_date?: string;
  ai_context?: any;
  created_at: string;
}

interface ActionSuggestion {
  call_suggestion?: {
    priority: string;
    reason: string;
    talking_points: string[];
    best_time: string;
  };
  email_suggestion?: {
    priority: string;
    reason: string;
    subject: string;
    key_topics: string[];
  };
  visit_suggestion?: {
    priority: string;
    reason: string;
    objectives: string[];
    timing: string;
  };
}

interface Props {
  customerId: string;
}

const ActivityCenter: React.FC<Props> = ({ customerId }) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [suggestions, setSuggestions] = useState<ActionSuggestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsRefreshing, setSuggestionsRefreshing] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [newActivity, setNewActivity] = useState({
    activity_type: 'note',
    notes: '',
    subject: '',
    duration_minutes: '',
    outcome: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadActivities();
    loadSuggestions();
  }, [customerId]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const response = await activityAPI.getCustomerActivities(customerId);
      setActivities(response.data || []);
    } catch (error) {
      console.error('Error loading activities:', error);
      setError('Failed to load activities');
    } finally {
      setLoading(false);
    }
  };

  const loadSuggestions = async () => {
    try {
      setSuggestionsLoading(true);
      // Load cached suggestions (fast - from database)
      const response = await activityAPI.getActionSuggestions(customerId, false);
      if (response.data.success && response.data.suggestions) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const refreshSuggestionsBackground = async () => {
    try {
      setSuggestionsRefreshing(true);
      setSuccess('AI is generating new suggestions in the background. Please wait...');
      
      // Queue the background task
      await activityAPI.refreshSuggestionsBackground(customerId);
      
      // Poll for updated suggestions every 3 seconds
      const pollInterval = setInterval(async () => {
        try {
          const response = await activityAPI.getActionSuggestions(customerId, false);
          if (response.data.success && response.data.suggestions && !response.data.cached) {
            // New suggestions are available!
            setSuggestions(response.data.suggestions);
            setSuccess('Suggestions updated successfully!');
            setSuggestionsRefreshing(false);
            clearInterval(pollInterval);
            setTimeout(() => setSuccess(null), 3000);
          }
        } catch (error) {
          console.error('Error polling suggestions:', error);
        }
      }, 3000);
      
      // Stop polling after 60 seconds
      setTimeout(() => {
        clearInterval(pollInterval);
        if (suggestionsRefreshing) {
          setSuggestionsRefreshing(false);
          setError('Suggestion refresh is taking longer than expected. Please refresh the page in a moment.');
          setTimeout(() => setError(null), 5000);
        }
      }, 60000);
      
    } catch (error) {
      console.error('Error refreshing suggestions:', error);
      setError('Failed to queue suggestion refresh');
      setSuggestionsRefreshing(false);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleCreateActivity = async () => {
    if (!newActivity.notes.trim()) {
      setError('Please enter notes');
      return;
    }

    try {
      setSubmitting(true);
      await activityAPI.createActivity({
        customer_id: customerId,
        activity_type: newActivity.activity_type,
        notes: newActivity.notes,
        subject: newActivity.subject || undefined,
        duration_minutes: newActivity.duration_minutes ? parseInt(newActivity.duration_minutes) : undefined,
        outcome: newActivity.outcome || undefined,
        process_with_ai: true
      });

      setSuccess('Activity logged successfully with AI enhancement!');
      setShowDialog(false);
      setNewActivity({
        activity_type: 'note',
        notes: '',
        subject: '',
        duration_minutes: '',
        outcome: ''
      });
      loadActivities();
      loadSuggestions(); // Refresh suggestions after new activity

      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Error creating activity:', error);
      setError('Failed to create activity');
      setTimeout(() => setError(null), 5000);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActivity = (activityId: string) => {
    setExpandedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityId)) {
        newSet.delete(activityId);
      } else {
        newSet.add(activityId);
      }
      return newSet;
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'call': return <CallIcon />;
      case 'email': return <EmailIcon />;
      case 'meeting': return <EventIcon />;
      case 'note': return <NotesIcon />;
      case 'task': return <TaskIcon />;
      default: return <NotesIcon />;
    }
  };

  const ActionBanner: React.FC<{ title: string; icon: React.ReactNode; color: string; data: any; type: 'call' | 'email' | 'visit' }> = ({ title, icon, color, data, type }) => {
    if (!data) return null;

    return (
      <Card sx={{ mb: 2, borderLeft: 4, borderColor: `${color}.main`, bgcolor: `${color}.50` }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {icon}
              <Typography variant="h6" color={`${color}.dark`}>
                {title}
              </Typography>
            </Box>
            <Chip 
              label={`${data.priority.toUpperCase()} PRIORITY`} 
              color={getPriorityColor(data.priority)} 
              size="small" 
            />
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            <strong>Why:</strong> {data.reason}
          </Typography>

          {type === 'call' && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                📋 Talking Points:
              </Typography>
              <List dense>
                {data.talking_points?.map((point: string, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemIcon sx={{ minWidth: 30 }}>•</ListItemIcon>
                    <ListItemText primary={point} />
                  </ListItem>
                ))}
              </List>
              <Typography variant="caption" color="text.secondary">
                💡 Best time: {data.best_time}
              </Typography>
            </>
          )}

          {type === 'email' && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                ✉️ Suggested Subject: <em>{data.subject}</em>
              </Typography>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                📋 Key Topics:
              </Typography>
              <List dense>
                {data.key_topics?.map((topic: string, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemIcon sx={{ minWidth: 30 }}>•</ListItemIcon>
                    <ListItemText primary={topic} />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {type === 'visit' && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                🎯 Objectives:
              </Typography>
              <List dense>
                {data.objectives?.map((obj: string, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemIcon sx={{ minWidth: 30 }}>•</ListItemIcon>
                    <ListItemText primary={obj} />
                  </ListItem>
                ))}
              </List>
              <Typography variant="caption" color="text.secondary">
                ⏰ Timing: {data.timing}
              </Typography>
            </>
          )}

          <Button
            variant="contained"
            color={color as any}
            size="small"
            sx={{ mt: 2 }}
            onClick={() => {
              setNewActivity({
                ...newActivity,
                activity_type: type === 'visit' ? 'meeting' : type,
                notes: type === 'call' 
                  ? `Call planned. Talking points:\n${data.talking_points?.join('\n') || ''}`
                  : type === 'email'
                  ? `Email to send: ${data.subject}\n\nTopics:\n${data.key_topics?.join('\n') || ''}`
                  : `Visit planned. Objectives:\n${data.objectives?.join('\n') || ''}`
              });
              setShowDialog(true);
            }}
          >
            Log This {type === 'visit' ? 'Meeting' : title}
          </Button>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Success/Error Messages */}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {/* AI-Powered Action Suggestions */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AIIcon color="primary" />
            AI-Powered Action Suggestions
          </Typography>
          <Button
            size="small"
            onClick={refreshSuggestionsBackground}
            disabled={suggestionsLoading || suggestionsRefreshing}
            startIcon={(suggestionsLoading || suggestionsRefreshing) ? <CircularProgress size={16} /> : <AIIcon />}
          >
            {suggestionsRefreshing ? 'Refreshing...' : 'Refresh Suggestions'}
          </Button>
        </Box>

        {suggestionsLoading ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              AI is analyzing customer history and generating personalized action suggestions...
            </Typography>
          </Box>
        ) : suggestions ? (
          <Grid container spacing={2}>
            <Grid
              size={{
                xs: 12,
                md: 4
              }}>
              <ActionBanner
                title="Call Suggestion"
                icon={<PhoneIcon />}
                color="primary"
                data={suggestions.call_suggestion}
                type="call"
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                md: 4
              }}>
              <ActionBanner
                title="Email Suggestion"
                icon={<EmailIcon />}
                color="secondary"
                data={suggestions.email_suggestion}
                type="email"
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                md: 4
              }}>
              <ActionBanner
                title="Visit Suggestion"
                icon={<BusinessIcon />}
                color="success"
                data={suggestions.visit_suggestion}
                type="visit"
              />
            </Grid>
          </Grid>
        ) : (
          <Alert severity="info">
            <AlertTitle>No AI Suggestions Yet</AlertTitle>
            Click "Refresh Suggestions" to generate AI-powered action recommendations based on customer history and analysis.
          </Alert>
        )}
      </Box>
      <Divider sx={{ my: 4 }} />
      {/* Activity Log */}
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">
            Activity History
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowDialog(true)}
          >
            Log Activity
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : activities.length === 0 ? (
          <Alert severity="info">
            No activities logged yet. Click "Log Activity" to get started!
          </Alert>
        ) : (
          <Stack spacing={2}>
            {activities.map((activity) => (
              <Card key={activity.id} variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ display: 'flex', gap: 2, flex: 1 }}>
                      <Box sx={{ color: 'primary.main' }}>
                        {getActivityIcon(activity.activity_type)}
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Chip 
                            label={activity.activity_type.toUpperCase()} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                          />
                          {activity.subject && (
                            <Typography variant="subtitle2">
                              {activity.subject}
                            </Typography>
                          )}
                          {activity.duration_minutes && (
                            <Chip 
                              label={`${activity.duration_minutes} min`} 
                              size="small" 
                              icon={<ScheduleIcon />}
                            />
                          )}
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(activity.activity_date).toLocaleString()}
                        </Typography>

                        {/* AI-Enhanced Notes */}
                        {activity.notes_cleaned ? (
                          <Box sx={{ mt: 2 }}>
                            <Alert severity="success" icon={<AIIcon />} sx={{ mb: 1 }}>
                              <AlertTitle>AI-Enhanced Notes</AlertTitle>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                                {activity.notes_cleaned}
                              </Typography>
                            </Alert>

                            {activity.ai_suggested_action && (
                              <Alert severity="info" icon={<TrendingUpIcon />}>
                                <Typography variant="subtitle2">Next Action:</Typography>
                                <Typography variant="body2">
                                  {activity.ai_suggested_action}
                                </Typography>
                              </Alert>
                            )}

                            {/* Collapsible Original Notes */}
                            <Box sx={{ mt: 1 }}>
                              <Button
                                size="small"
                                onClick={() => toggleActivity(activity.id)}
                                endIcon={expandedActivities.has(activity.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                              >
                                {expandedActivities.has(activity.id) ? 'Hide' : 'Show'} Original Notes
                              </Button>
                              <Collapse in={expandedActivities.has(activity.id)}>
                                <Paper elevation={0} sx={{ p: 2, mt: 1, bgcolor: 'grey.50' }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Original Notes:
                                  </Typography>
                                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', mt: 1 }}>
                                    {activity.notes}
                                  </Typography>
                                </Paper>
                              </Collapse>
                            </Box>
                          </Box>
                        ) : (
                          <Paper elevation={0} sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                              {activity.notes}
                            </Typography>
                          </Paper>
                        )}

                        {activity.follow_up_required && activity.follow_up_date && (
                          <Alert severity="warning" icon={<WarningIcon />} sx={{ mt: 2 }}>
                            <Typography variant="subtitle2">
                              Follow-up Required: {new Date(activity.follow_up_date).toLocaleDateString()}
                            </Typography>
                          </Alert>
                        )}
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Box>
      {/* Log Activity Dialog */}
      <Dialog open={showDialog} onClose={() => setShowDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Log New Activity
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Activity Type</InputLabel>
              <Select
                value={newActivity.activity_type}
                onChange={(e) => setNewActivity({ ...newActivity, activity_type: e.target.value })}
                label="Activity Type"
              >
                <MenuItem value="note">Note</MenuItem>
                <MenuItem value="call">Phone Call</MenuItem>
                <MenuItem value="email">Email</MenuItem>
                <MenuItem value="meeting">Meeting / Visit</MenuItem>
                <MenuItem value="task">Task</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Subject (optional)"
              value={newActivity.subject}
              onChange={(e) => setNewActivity({ ...newActivity, subject: e.target.value })}
              fullWidth
            />

            <TextField
              label="Notes"
              value={newActivity.notes}
              onChange={(e) => setNewActivity({ ...newActivity, notes: e.target.value })}
              multiline
              rows={6}
              fullWidth
              required
              helperText="AI will automatically clean up and structure your notes, and suggest next actions"
            />

            {(newActivity.activity_type === 'call' || newActivity.activity_type === 'meeting') && (
              <TextField
                label="Duration (minutes)"
                type="number"
                value={newActivity.duration_minutes}
                onChange={(e) => setNewActivity({ ...newActivity, duration_minutes: e.target.value })}
                fullWidth
              />
            )}

            <FormControl fullWidth>
              <InputLabel>Outcome (optional)</InputLabel>
              <Select
                value={newActivity.outcome}
                onChange={(e) => setNewActivity({ ...newActivity, outcome: e.target.value })}
                label="Outcome (optional)"
              >
                <MenuItem value="">None</MenuItem>
                <MenuItem value="successful">Successful</MenuItem>
                <MenuItem value="no_answer">No Answer</MenuItem>
                <MenuItem value="voicemail">Voicemail</MenuItem>
                <MenuItem value="follow_up_required">Follow-up Required</MenuItem>
                <MenuItem value="meeting_scheduled">Meeting Scheduled</MenuItem>
                <MenuItem value="quote_requested">Quote Requested</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateActivity} 
            variant="contained" 
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <CheckCircleIcon />}
          >
            {submitting ? 'Processing with AI...' : 'Log Activity'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ActivityCenter;

