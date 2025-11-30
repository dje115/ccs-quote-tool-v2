import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  LinearProgress,
  Stack
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
  AutoAwesome as SparkleIcon,
  ExpandMore as ExpandMoreIcon,
  QuestionAnswer as QuestionAnswerIcon,
  PlayArrow as PlayArrowIcon,
  Build as BuildIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon,
  PersonAdd as PersonAddIcon,
  Flag as FlagIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  Close as CloseIcon,
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
  AddComment as AddCommentIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { helpdeskAPI, slaAPI } from '../services/api';
import {
  Assessment as AssessmentIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';

const TicketDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [statusMenuAnchor, setStatusMenuAnchor] = useState<null | HTMLElement>(null);
  const [priorityMenuAnchor, setPriorityMenuAnchor] = useState<null | HTMLElement>(null);
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [slaCompliance, setSlaCompliance] = useState<any>(null);
  const [loadingSla, setLoadingSla] = useState(false);

  useEffect(() => {
    if (id) {
      loadTicket();
      loadSlaCompliance();
    }
  }, [id]);

  const loadTicket = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.getTicket(id!);
      setTicket(response.data);
    } catch (error: any) {
      console.error('Error loading ticket:', error);
      setError(error.response?.data?.detail || 'Failed to load ticket');
    } finally {
      setLoading(false);
    }
  };

  const loadSlaCompliance = async () => {
    try {
      setLoadingSla(true);
      const response = await slaAPI.getTicketCompliance(id!);
      setSlaCompliance(response.data);
    } catch (error: any) {
      console.error('Error loading SLA compliance:', error);
      // Don't show error - SLA might not be configured
    } finally {
      setLoadingSla(false);
    }
  };

  const handleRunAIAnalysis = async () => {
    try {
      setAnalyzing(true);
      setError(null);
      setSuccess(null);
      const response = await helpdeskAPI.analyzeTicket(id!);
      if (response.data.success) {
        setSuccess('AI analysis completed successfully!');
        await loadTicket();
        // Switch to AI Analysis tab
        setCurrentTab(1);
      }
    } catch (error: any) {
      console.error('Error running AI analysis:', error);
      setError(error.response?.data?.detail || 'Failed to run AI analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAddComment = async () => {
    try {
      await helpdeskAPI.addComment(id!, {
        comment: newComment,
        is_internal: isInternal
      });
      setCommentDialogOpen(false);
      setNewComment('');
      setIsInternal(false);
      await loadTicket();
      setSuccess('Comment added successfully!');
    } catch (error: any) {
      console.error('Error adding comment:', error);
      setError(error.response?.data?.detail || 'Failed to add comment');
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await helpdeskAPI.updateStatus(id!, newStatus);
      setStatusMenuAnchor(null);
      await loadTicket();
      setSuccess(`Ticket status updated to ${newStatus}`);
    } catch (error: any) {
      console.error('Error updating status:', error);
      setError(error.response?.data?.detail || 'Failed to update status');
    }
  };

  const handlePriorityChange = async (newPriority: string) => {
    try {
      await helpdeskAPI.updateTicket(id!, { priority: newPriority });
      setPriorityMenuAnchor(null);
      await loadTicket();
      await loadSlaCompliance(); // Refresh SLA status after priority change
      setSuccess(`Ticket priority updated to ${newPriority}`);
    } catch (error: any) {
      console.error('Error updating priority:', error);
      setError(error.response?.data?.detail || 'Failed to update priority');
    }
  };

  const handleActionClick = (action: string) => {
    // Parse action and create appropriate response
    // For now, open comment dialog with pre-filled text
    setNewComment(`Following up on: ${action}`);
    setCommentDialogOpen(true);
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
      <Container maxWidth="lg" sx={{ py: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error && !ticket) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Alert severity="error">{error || 'Ticket not found'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/helpdesk')} sx={{ mt: 2 }}>
          Back to Helpdesk
        </Button>
      </Container>
    );
  }

  const aiSuggestions = ticket?.ai_suggestions || {};
  const hasAISuggestions = aiSuggestions.next_actions || aiSuggestions.questions || aiSuggestions.solutions;

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Success/Error Messages */}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Header with Quick Actions */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button startIcon={<BackIcon />} onClick={() => navigate('/helpdesk')}>
            Back to Helpdesk
          </Button>
          <Typography variant="h4" component="h1">
            Ticket {ticket?.ticket_number}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Run AI Analysis">
            <Button
              variant="outlined"
              startIcon={analyzing ? <CircularProgress size={16} /> : <SparkleIcon />}
              onClick={handleRunAIAnalysis}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
            </Button>
          </Tooltip>
          <IconButton
            onClick={(e) => setActionMenuAnchor(e.currentTarget)}
            size="small"
          >
            <MoreVertIcon />
          </IconButton>
        </Stack>
      </Box>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={() => setActionMenuAnchor(null)}
      >
        <MenuItem onClick={() => { setActionMenuAnchor(null); setCommentDialogOpen(true); }}>
          <ListItemIcon><AddCommentIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Add Comment</ListItemText>
        </MenuItem>
        <MenuItem onClick={(e) => { setActionMenuAnchor(null); setStatusMenuAnchor(e.currentTarget); }}>
          <ListItemIcon><CheckCircleOutlineIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Change Status</ListItemText>
        </MenuItem>
        <MenuItem onClick={(e) => { setActionMenuAnchor(null); setPriorityMenuAnchor(e.currentTarget); }}>
          <ListItemIcon><FlagIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Change Priority</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { setActionMenuAnchor(null); }}>
          <ListItemIcon><AssignmentIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Assign Ticket</ListItemText>
        </MenuItem>
      </Menu>

      {/* Status Menu */}
      <Menu
        anchorEl={statusMenuAnchor}
        open={Boolean(statusMenuAnchor)}
        onClose={() => setStatusMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleStatusChange('open')}>Open</MenuItem>
        <MenuItem onClick={() => handleStatusChange('in_progress')}>In Progress</MenuItem>
        <MenuItem onClick={() => handleStatusChange('waiting_customer')}>Waiting Customer</MenuItem>
        <MenuItem onClick={() => handleStatusChange('resolved')}>Resolved</MenuItem>
        <MenuItem onClick={() => handleStatusChange('closed')}>Closed</MenuItem>
      </Menu>

      {/* Priority Menu */}
      <Menu
        anchorEl={priorityMenuAnchor}
        open={Boolean(priorityMenuAnchor)}
        onClose={() => setPriorityMenuAnchor(null)}
      >
        <MenuItem onClick={() => handlePriorityChange('urgent')}>Urgent</MenuItem>
        <MenuItem onClick={() => handlePriorityChange('high')}>High</MenuItem>
        <MenuItem onClick={() => handlePriorityChange('medium')}>Medium</MenuItem>
        <MenuItem onClick={() => handlePriorityChange('low')}>Low</MenuItem>
      </Menu>

      {/* Ticket Header Card */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              {ticket?.subject}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Chip
                label={ticket?.status}
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                size="small"
              />
              <Chip
                label={ticket?.priority}
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                size="small"
              />
              {ticket?.ticket_type && (
                <Chip
                  label={ticket?.ticket_type}
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  size="small"
                  variant="outlined"
                />
              )}
            </Stack>
            {ticket?.customer_id && (
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Customer ID: {ticket.customer_id}
              </Typography>
            )}
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>
                Created: {new Date(ticket?.created_at).toLocaleString()}
              </Typography>
              {ticket?.updated_at && (
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>
                  Updated: {new Date(ticket.updated_at).toLocaleString()}
                </Typography>
              )}
              {ticket?.assigned_to_name && (
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Assigned to: {ticket.assigned_to_name}
                </Typography>
              )}
              {ticket?.ai_analysis_date && (
                <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
                  <SparkleIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                  AI Analyzed: {new Date(ticket.ai_analysis_date).toLocaleString()}
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* SLA Status Card */}
      {slaCompliance && (
        <Paper sx={{ p: 2, mb: 3, borderLeft: '4px solid', borderLeftColor: slaCompliance.compliant ? 'success.main' : 'error.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <AssessmentIcon color={slaCompliance.compliant ? 'success' : 'error'} />
            <Typography variant="h6">
              SLA Status
            </Typography>
            {slaCompliance.compliant ? (
              <Chip label="Compliant" size="small" color="success" icon={<CheckCircleIcon />} />
            ) : (
              <Chip label="Breached" size="small" color="error" icon={<ErrorIcon />} />
            )}
          </Box>
          <Grid container spacing={2}>
            {slaCompliance.first_response && (
              <Grid item xs={12} sm={6}>
                <Card variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    First Response
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <AccessTimeIcon fontSize="small" color={slaCompliance.first_response.breached ? 'error' : 'success'} />
                    <Typography variant="body2" fontWeight="medium">
                      {slaCompliance.first_response.actual_hours?.toFixed(1) || 'N/A'}h / {slaCompliance.first_response.target_hours || 'N/A'}h
                    </Typography>
                  </Box>
                  {slaCompliance.first_response.breached ? (
                    <Chip label="Breached" size="small" color="error" sx={{ mt: 0.5 }} />
                  ) : slaCompliance.first_response.met ? (
                    <Chip label="Met" size="small" color="success" sx={{ mt: 0.5 }} />
                  ) : (
                    <Box sx={{ mt: 0.5 }}>
                      <Typography variant="caption" color="warning.main">
                        {slaCompliance.first_response.percent_used?.toFixed(1) || 0}% used
                      </Typography>
                      {slaCompliance.first_response.time_remaining_hours !== undefined && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {slaCompliance.first_response.time_remaining_hours.toFixed(1)}h remaining
                        </Typography>
                      )}
                    </Box>
                  )}
                </Card>
              </Grid>
            )}
            {slaCompliance.resolution && (
              <Grid item xs={12} sm={6}>
                <Card variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Resolution
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <AccessTimeIcon fontSize="small" color={slaCompliance.resolution.breached ? 'error' : 'success'} />
                    <Typography variant="body2" fontWeight="medium">
                      {slaCompliance.resolution.actual_hours?.toFixed(1) || 'N/A'}h / {slaCompliance.resolution.target_hours || 'N/A'}h
                    </Typography>
                  </Box>
                  {slaCompliance.resolution.breached ? (
                    <Chip label="Breached" size="small" color="error" sx={{ mt: 0.5 }} />
                  ) : slaCompliance.resolution.met ? (
                    <Chip label="Met" size="small" color="success" sx={{ mt: 0.5 }} />
                  ) : (
                    <Box sx={{ mt: 0.5 }}>
                      <Typography variant="caption" color="warning.main">
                        {slaCompliance.resolution.percent_used?.toFixed(1) || 0}% used
                      </Typography>
                      {slaCompliance.resolution.time_remaining_hours !== undefined && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {slaCompliance.resolution.time_remaining_hours.toFixed(1)}h remaining
                        </Typography>
                      )}
                    </Box>
                  )}
                </Card>
              </Grid>
            )}
          </Grid>
          {slaCompliance.breaches && slaCompliance.breaches.length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                SLA Breach Detected: {slaCompliance.breaches.join(', ').replace('_', ' ')}
              </Typography>
            </Alert>
          )}
        </Paper>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab label="Description" />
          <Tab label="AI Analysis" icon={hasAISuggestions ? <SparkleIcon /> : undefined} />
          <Tab label="Comments" />
          <Tab label="History" />
        </Tabs>
      </Paper>

      {/* Tab Panel 0: Description */}
      {currentTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Description
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={analyzing ? <CircularProgress size={16} /> : <SparkleIcon />}
              onClick={handleRunAIAnalysis}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {ticket?.improved_description ? (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>AI-Improved Description</strong> (shown to customer)
                </Typography>
              </Alert>
              <Typography variant="body1" sx={{ mb: 3, whiteSpace: 'pre-wrap' }}>
                {ticket.improved_description}
              </Typography>
              
              {ticket.original_description && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="body2" color="text.secondary">
                      View Original Description (Internal)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', color: 'text.secondary' }}>
                      {ticket.original_description}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          ) : (
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {ticket?.description}
            </Typography>
          )}
        </Paper>
      )}

      {/* Tab Panel 1: AI Analysis */}
      {currentTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SparkleIcon /> AI Analysis & Suggestions
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={analyzing ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleRunAIAnalysis}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing...' : 'Refresh Analysis'}
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {analyzing && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                AI is analyzing the ticket and generating suggestions...
              </Typography>
            </Box>
          )}

          {!hasAISuggestions && !analyzing ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                No AI analysis available for this ticket.
              </Typography>
              <Button
                variant="contained"
                size="small"
                startIcon={<SparkleIcon />}
                onClick={handleRunAIAnalysis}
                sx={{ mt: 1 }}
              >
                Run AI Analysis Now
              </Button>
            </Alert>
          ) : (
            <Box>
              {ticket?.ai_analysis_date && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Last analyzed: {new Date(ticket.ai_analysis_date).toLocaleString()}
                </Typography>
              )}

              {/* Next Actions - Actionable */}
              {aiSuggestions.next_actions && aiSuggestions.next_actions.length > 0 && (
                <Card sx={{ mb: 2, borderLeft: '4px solid', borderLeftColor: 'primary.main' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PlayArrowIcon color="primary" /> Next Actions
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Click an action to add it as a comment and track progress
                    </Typography>
                    <List>
                      {aiSuggestions.next_actions.map((action: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            mb: 1,
                            '&:hover': {
                              bgcolor: 'action.hover',
                              cursor: 'pointer'
                            }
                          }}
                          onClick={() => handleActionClick(action)}
                        >
                          <ListItemIcon>
                            <CheckCircleIcon color="primary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={action}
                            secondary="Click to add as comment"
                          />
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<AddCommentIcon />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleActionClick(action);
                            }}
                          >
                            Use This
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Questions to Ask */}
              {aiSuggestions.questions && aiSuggestions.questions.length > 0 && (
                <Card sx={{ mb: 2, borderLeft: '4px solid', borderLeftColor: 'warning.main' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <QuestionAnswerIcon color="warning" /> Questions to Ask
                    </Typography>
                    <List>
                      {aiSuggestions.questions.map((question: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            mb: 1,
                            '&:hover': {
                              bgcolor: 'action.hover',
                              cursor: 'pointer'
                            }
                          }}
                          onClick={() => handleActionClick(question)}
                        >
                          <ListItemIcon>
                            <WarningIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText
                            primary={question}
                            secondary="Click to add as comment"
                          />
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<AddCommentIcon />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleActionClick(question);
                            }}
                          >
                            Use This
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Potential Solutions */}
              {aiSuggestions.solutions && aiSuggestions.solutions.length > 0 && (
                <Card sx={{ mb: 2, borderLeft: '4px solid', borderLeftColor: 'success.main' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <BuildIcon color="success" /> Potential Solutions
                    </Typography>
                    <List>
                      {aiSuggestions.solutions.map((solution: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            mb: 1,
                            '&:hover': {
                              bgcolor: 'action.hover',
                              cursor: 'pointer'
                            }
                          }}
                          onClick={() => handleActionClick(solution)}
                        >
                          <ListItemIcon>
                            <LightbulbIcon color="success" />
                          </ListItemIcon>
                          <ListItemText
                            primary={solution}
                            secondary="Click to add as comment"
                          />
                          <Button
                            size="small"
                            variant="outlined"
                            color="success"
                            startIcon={<CheckCircleIcon />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleActionClick(solution);
                            }}
                          >
                            Try This
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}
            </Box>
          )}
        </Paper>
      )}

      {/* Tab Panel 2: Comments */}
      {currentTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Comments
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                size="small"
                startIcon={analyzing ? <CircularProgress size={16} /> : <SparkleIcon />}
                onClick={handleRunAIAnalysis}
                disabled={analyzing}
              >
                {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
              </Button>
              <Button
                variant="contained"
                startIcon={<SendIcon />}
                onClick={() => setCommentDialogOpen(true)}
              >
                Add Comment
              </Button>
            </Stack>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {ticket?.comments && ticket.comments.length > 0 ? (
            <List>
              {ticket.comments.map((comment: any) => (
                <ListItem key={comment.id} alignItems="flex-start" sx={{ mb: 2 }}>
                  <Card sx={{ width: '100%', p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {comment.author_name || comment.author_email || 'System'}
                      </Typography>
                      {comment.is_internal && (
                        <Chip label="Internal" size="small" color="warning" />
                      )}
                      <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                        {new Date(comment.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {comment.comment}
                    </Typography>
                  </Card>
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity="info">No comments yet. Add a comment to start the conversation.</Alert>
          )}
        </Paper>
      )}

      {/* Tab Panel 3: History */}
      {currentTab === 3 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Ticket History
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={analyzing ? <CircularProgress size={16} /> : <SparkleIcon />}
              onClick={handleRunAIAnalysis}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {ticket?.history && ticket.history.length > 0 ? (
            <List>
              {ticket.history.map((historyItem: any) => (
                <ListItem key={historyItem.id}>
                  <Card sx={{ width: '100%', p: 2 }}>
                    <Typography variant="body2">
                      <strong>{historyItem.field_name}:</strong> {historyItem.old_value || 'N/A'} → {historyItem.new_value}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(historyItem.created_at).toLocaleString()}
                    </Typography>
                  </Card>
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity="info">No history available.</Alert>
          )}
        </Paper>
      )}

      {/* Add Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={6}
            label="Comment"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            margin="normal"
            required
            placeholder="Add your comment here..."
          />
          <Box sx={{ mt: 2 }}>
            <input
              type="checkbox"
              id="isInternal"
              checked={isInternal}
              onChange={(e) => setIsInternal(e.target.checked)}
            />
            <label htmlFor="isInternal" style={{ marginLeft: 8 }}>
              Internal comment (not visible to customer)
            </label>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddComment}
            variant="contained"
            disabled={!newComment.trim()}
            startIcon={<SendIcon />}
          >
            Add Comment
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TicketDetail;
