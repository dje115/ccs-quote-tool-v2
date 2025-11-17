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
  AccordionDetails
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
  Build as BuildIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { helpdeskAPI } from '../services/api';

const TicketDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);

  useEffect(() => {
    if (id) {
      loadTicket();
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
    } catch (error: any) {
      console.error('Error adding comment:', error);
      setError(error.response?.data?.detail || 'Failed to add comment');
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
      <Container maxWidth="lg" sx={{ py: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !ticket) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Alert severity="error">{error || 'Ticket not found'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/helpdesk')} sx={{ mt: 2 }}>
          Back to Helpdesk
        </Button>
      </Container>
    );
  }

  const aiSuggestions = ticket.ai_suggestions || {};
  const hasAISuggestions = aiSuggestions.next_actions || aiSuggestions.questions || aiSuggestions.solutions;

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/helpdesk')}>
          Back to Helpdesk
        </Button>
        <Typography variant="h4" component="h1">
          Ticket {ticket.ticket_number}
        </Typography>
      </Box>

      {/* Ticket Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="h5" gutterBottom>
              {ticket.subject}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip
                label={ticket.status}
                color={getStatusColor(ticket.status) as any}
                size="small"
              />
              <Chip
                label={ticket.priority}
                color={getPriorityColor(ticket.priority) as any}
                size="small"
              />
              {ticket.ticket_type && (
                <Chip label={ticket.ticket_type} size="small" variant="outlined" />
              )}
            </Box>
            {ticket.customer_id && (
              <Typography variant="body2" color="text.secondary">
                Customer ID: {ticket.customer_id}
              </Typography>
            )}
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary">
              Created: {new Date(ticket.created_at).toLocaleString()}
            </Typography>
            {ticket.updated_at && (
              <Typography variant="body2" color="text.secondary">
                Updated: {new Date(ticket.updated_at).toLocaleString()}
              </Typography>
            )}
            {ticket.assigned_to_id && (
              <Typography variant="body2" color="text.secondary">
                Assigned to: {ticket.assigned_to_name || ticket.assigned_to_id}
              </Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

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
          <Typography variant="h6" gutterBottom>
            Description
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {/* Show improved description if available, otherwise show original */}
          {ticket.improved_description ? (
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
              {ticket.description}
            </Typography>
          )}
        </Paper>
      )}

      {/* Tab Panel 1: AI Analysis */}
      {currentTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SparkleIcon /> AI Analysis & Suggestions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {!hasAISuggestions ? (
            <Alert severity="info">
              No AI analysis available for this ticket. AI analysis is performed automatically when tickets are created.
            </Alert>
          ) : (
            <Box>
              {ticket.ai_analysis_date && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Analyzed: {new Date(ticket.ai_analysis_date).toLocaleString()}
                </Typography>
              )}

              {/* Next Actions */}
              {aiSuggestions.next_actions && aiSuggestions.next_actions.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PlayArrowIcon color="primary" /> Next Actions
                    </Typography>
                    <List>
                      {aiSuggestions.next_actions.map((action: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CheckCircleIcon color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={action} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Questions to Ask */}
              {aiSuggestions.questions && aiSuggestions.questions.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <QuestionAnswerIcon color="warning" /> Questions to Ask
                    </Typography>
                    <List>
                      {aiSuggestions.questions.map((question: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <WarningIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={question} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Potential Solutions */}
              {aiSuggestions.solutions && aiSuggestions.solutions.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <BuildIcon color="success" /> Potential Solutions
                    </Typography>
                    <List>
                      {aiSuggestions.solutions.map((solution: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <LightbulbIcon color="success" />
                          </ListItemIcon>
                          <ListItemText primary={solution} />
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
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => setCommentDialogOpen(true)}
            >
              Add Comment
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {ticket.comments && ticket.comments.length > 0 ? (
            <List>
              {ticket.comments.map((comment: any) => (
                <ListItem key={comment.id} alignItems="flex-start">
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2">
                          {comment.author_name || comment.author_email || 'System'}
                        </Typography>
                        {comment.is_internal && (
                          <Chip label="Internal" size="small" color="warning" />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {new Date(comment.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                        {comment.comment}
                      </Typography>
                    }
                  />
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
          <Typography variant="h6" gutterBottom>
            Ticket History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {ticket.history && ticket.history.length > 0 ? (
            <List>
              {ticket.history.map((historyItem: any) => (
                <ListItem key={historyItem.id}>
                  <ListItemText
                    primary={`${historyItem.field_name}: ${historyItem.old_value || 'N/A'} → ${historyItem.new_value}`}
                    secondary={new Date(historyItem.created_at).toLocaleString()}
                  />
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
          >
            Add Comment
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TicketDetail;

