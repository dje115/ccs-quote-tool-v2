import React, { useEffect, useState, useRef } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
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
  Stack,
  Grid,
  Checkbox,
  ButtonGroup,
  FormControl,
  InputLabel,
  Select,
  FormControlLabel
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
  AddComment as AddCommentIcon,
  Reply as ReplyIcon,
  Assessment as AssessmentIcon,
  AccessTime as AccessTimeIcon,
  Error as ErrorIcon,
  Article as ArticleIcon,
  MergeType as MergeTypeIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { helpdeskAPI, slaAPI } from '../services/api';
import TicketKBAnswer from '../components/TicketKBAnswer';
import TicketNPA from '../components/TicketNPA';
import TicketChatbot from '../components/TicketChatbot';
import TicketTemplateSelector from '../components/TicketTemplateSelector';
import QuickReplyMenu from '../components/QuickReplyMenu';
import KeyboardShortcutsHelp from '../components/KeyboardShortcutsHelp';
import TicketMacroMenu from '../components/TicketMacroMenu';
import TicketMergeDialog from '../components/TicketMergeDialog';
import { useKeyboardShortcuts, KeyboardShortcut } from '../hooks/useKeyboardShortcuts';

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
  const [improvingDescription, setImprovingDescription] = useState(false);
  const [generatingAutoResponse, setGeneratingAutoResponse] = useState(false);
  const [kbSuggestions, setKbSuggestions] = useState<any[]>([]);
  const [loadingKbSuggestions, setLoadingKbSuggestions] = useState(false);
  const [selectedActions, setSelectedActions] = useState<Set<number>>(new Set());
  const [selectedQuestions, setSelectedQuestions] = useState<Set<number>>(new Set());
  const [selectedSolutions, setSelectedSolutions] = useState<Set<number>>(new Set());
  const [npaDialogOpen, setNpaDialogOpen] = useState(false);
  const [selectedNpaState, setSelectedNpaState] = useState('investigation');
  const [selectedExcludeFromSla, setSelectedExcludeFromSla] = useState(false);
  const [npaAction, setNpaAction] = useState<'append' | 'new'>('append'); // 'append' = add to existing, 'new' = close existing and create new
  const [currentNpa, setCurrentNpa] = useState<any>(null);
  const [npaHistory, setNpaHistory] = useState<any[]>([]);
  const [loadingNpaHistory, setLoadingNpaHistory] = useState(false);
  const [shortcutsHelpOpen, setShortcutsHelpOpen] = useState(false);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);

  // Use ref to track description cleanup status to avoid re-renders
  const descriptionCleanupStatusRef = useRef<string | null>(null);
  
  useEffect(() => {
    if (id) {
      loadTicket();
      loadSlaCompliance();
      loadKbSuggestions();
      loadCurrentNPA();
      loadNpaHistory();
    }
  }, [id]);
  
  // Update ref when ticket changes
  useEffect(() => {
    descriptionCleanupStatusRef.current = ticket?.description_ai_cleanup_status || null;
  }, [ticket?.description_ai_cleanup_status]);
  
  // Poll for description cleanup status only when processing
  useEffect(() => {
    if (descriptionCleanupStatusRef.current !== 'processing') {
      return; // Not processing, don't poll
    }
    
    const interval = setInterval(() => {
      if (descriptionCleanupStatusRef.current === 'processing') {
        loadTicket();
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [id, ticket?.description_ai_cleanup_status]); // Only re-run if ticket ID or status changes

  // Keyboard Shortcuts
  const shortcuts: KeyboardShortcut[] = [
    {
      key: 's',
      ctrl: true,
      description: 'Save ticket',
      action: async () => {
        if (ticket) {
          try {
            await helpdeskAPI.updateTicket(ticket.id, ticket);
            setSuccess('Ticket saved');
          } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to save ticket');
          }
        }
      },
      disabled: !ticket
    },
    {
      key: 'r',
      ctrl: true,
      description: 'Reply/Add Comment',
      action: () => {
        setCommentDialogOpen(true);
      },
      disabled: !ticket
    },
    {
      key: 'k',
      ctrl: true,
      description: 'Open Knowledge Base',
      action: () => {
        setCurrentTab(1);
      },
      disabled: !ticket
    },
    {
      key: '/',
      ctrl: true,
      description: 'Show Shortcuts Help',
      action: () => {
        setShortcutsHelpOpen(true);
      }
    },
    {
      key: 'Escape',
      description: 'Close Dialog',
      action: () => {
        if (commentDialogOpen) setCommentDialogOpen(false);
        if (npaDialogOpen) setNpaDialogOpen(false);
        if (statusMenuAnchor) setStatusMenuAnchor(null);
        if (priorityMenuAnchor) setPriorityMenuAnchor(null);
        if (actionMenuAnchor) setActionMenuAnchor(null);
      }
    }
  ];

  useKeyboardShortcuts(shortcuts);

  const loadCurrentNPA = async () => {
    try {
      const response = await helpdeskAPI.getTicketNPA(id!);
      setCurrentNpa(response.data);
    } catch (error) {
      console.error('Error loading current NPA:', error);
      setCurrentNpa(null);
    }
  };

  const loadNpaHistory = async () => {
    if (!id) return;
    try {
      setLoadingNpaHistory(true);
      const response = await helpdeskAPI.getTicketNPAHistory(id);
      setNpaHistory(response.data.history || []);
    } catch (error: any) {
      console.error('Error loading NPA history:', error);
      setNpaHistory([]);
    } finally {
      setLoadingNpaHistory(false);
    }
  };

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
        await loadKbSuggestions();
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

  const loadKbSuggestions = async () => {
    if (!id) return;
    try {
      setLoadingKbSuggestions(true);
      const response = await helpdeskAPI.getKnowledgeBaseSuggestions(id, 5);
      setKbSuggestions(response.data.suggestions || []);
    } catch (error: any) {
      console.error('Error loading KB suggestions:', error);
      // Don't show error - KB suggestions are optional
    } finally {
      setLoadingKbSuggestions(false);
    }
  };

  const handleImproveDescription = async () => {
    if (!ticket?.description) {
      setError('No description to improve');
      return;
    }
    try {
      setImprovingDescription(true);
      setError(null);
      const response = await helpdeskAPI.improveTicketDescription(id!, ticket.description);
      if (response.data.improved_description) {
        setSuccess('Description improved! Review the changes below.');
        // Update ticket with improved description
        setTicket({
          ...ticket,
          improved_description: response.data.improved_description,
          original_description: response.data.original_description
        });
      }
    } catch (error: any) {
      console.error('Error improving description:', error);
      setError(error.response?.data?.detail || 'Failed to improve description');
    } finally {
      setImprovingDescription(false);
    }
  };

  const handleGenerateAutoResponse = async (responseType: string = 'acknowledgment') => {
    try {
      setGeneratingAutoResponse(true);
      setError(null);
      const response = await helpdeskAPI.generateAutoResponse(id!, responseType);
      if (response.data.response_text) {
        setNewComment(response.data.response_text);
        setCommentDialogOpen(true);
        setSuccess('Auto response generated! Review and send as a comment.');
      }
    } catch (error: any) {
      console.error('Error generating auto response:', error);
      setError(error.response?.data?.detail || 'Failed to generate auto response');
    } finally {
      setGeneratingAutoResponse(false);
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

  const handleApplySelectedToNPA = async () => {
    const allSelected: string[] = [];
    
    if (aiSuggestions.next_actions) {
      aiSuggestions.next_actions.forEach((action: string, index: number) => {
        if (selectedActions.has(index)) {
          allSelected.push(action);
        }
      });
    }
    
    if (aiSuggestions.questions) {
      aiSuggestions.questions.forEach((question: string, index: number) => {
        if (selectedQuestions.has(index)) {
          allSelected.push(`Question: ${question}`);
        }
      });
    }
    
    if (aiSuggestions.solutions) {
      aiSuggestions.solutions.forEach((solution: string, index: number) => {
        if (selectedSolutions.has(index)) {
          allSelected.push(`Solution: ${solution}`);
        }
      });
    }
    
    if (allSelected.length === 0) {
      alert('Please select at least one suggestion');
      return;
    }
    
    // Load current NPA to check if one exists
    await loadCurrentNPA();
    
    // Open dialog to select NPA state and action
    setNpaDialogOpen(true);
  };

  const handleConfirmApplyToNPA = async () => {
    const allSelected: string[] = [];
    
    if (aiSuggestions.next_actions) {
      aiSuggestions.next_actions.forEach((action: string, index: number) => {
        if (selectedActions.has(index)) {
          allSelected.push(action);
        }
      });
    }
    
    if (aiSuggestions.questions) {
      aiSuggestions.questions.forEach((question: string, index: number) => {
        if (selectedQuestions.has(index)) {
          allSelected.push(`Question: ${question}`);
        }
      });
    }
    
    if (aiSuggestions.solutions) {
      aiSuggestions.solutions.forEach((solution: string, index: number) => {
        if (selectedSolutions.has(index)) {
          allSelected.push(`Solution: ${solution}`);
        }
      });
    }
    
    try {
      const newText = allSelected.join('\n\n');
      
      // Auto-set exclude_from_sla based on state if not explicitly set
      let excludeFromSla = selectedExcludeFromSla;
      if (!excludeFromSla) {
        const waitingStates = ['waiting_customer', 'waiting_vendor', 'waiting_parts'];
        excludeFromSla = waitingStates.includes(selectedNpaState);
      }
      
      if (npaAction === 'append' && currentNpa?.npa_original_text) {
        // Append to existing NPA
        const combinedText = `${currentNpa.npa_original_text}\n\n--- Additional Actions ---\n\n${newText}`;
        await helpdeskAPI.updateTicketNPA(id!, {
          npa: combinedText.trim(),
          npa_state: selectedNpaState,
          exclude_from_sla: excludeFromSla,
          trigger_ai_cleanup: true
        });
        setSuccess(`${allSelected.length} suggestion(s) appended to existing NPA successfully!`);
      } else {
        // Close existing NPA (mark as solution) and create new one
        if (currentNpa?.npa_original_text) {
          // First, mark the current NPA as solution/complete
          // Pass completed_by_id to ensure it's saved to history
          // Note: We need to get the current user ID - for now, just mark as solution
          // The backend will save to history because we're changing the state to 'solution'
          await helpdeskAPI.updateTicketNPA(id!, {
            npa: currentNpa.npa_original_text,
            npa_state: 'solution',
            exclude_from_sla: false,
            trigger_ai_cleanup: false
          });
        }
        
        // Then create new NPA with selected suggestions
        // This will save the previous NPA to history (if it exists) because the text is changing
        await helpdeskAPI.updateTicketNPA(id!, {
          npa: newText.trim(),
          npa_state: selectedNpaState,
          exclude_from_sla: excludeFromSla,
          trigger_ai_cleanup: true
        });
        setSuccess(`${allSelected.length} suggestion(s) added to new NPA (previous NPA marked as solution)!`);
      }
      
      // Clear selections and reload
      setSelectedActions(new Set());
      setSelectedQuestions(new Set());
      setSelectedSolutions(new Set());
      setNpaDialogOpen(false);
      await loadTicket();
      await loadCurrentNPA();
    } catch (error: any) {
      console.error('Error applying suggestions:', error);
      setError(error.response?.data?.detail || 'Failed to apply suggestions to NPA');
      setNpaDialogOpen(false);
    }
  };

  const handleApplySelectedToComment = async () => {
    const allSelected: string[] = [];
    
    if (aiSuggestions.next_actions) {
      aiSuggestions.next_actions.forEach((action: string, index: number) => {
        if (selectedActions.has(index)) {
          allSelected.push(`Action: ${action}`);
        }
      });
    }
    
    if (aiSuggestions.questions) {
      aiSuggestions.questions.forEach((question: string, index: number) => {
        if (selectedQuestions.has(index)) {
          allSelected.push(`Question: ${question}`);
        }
      });
    }
    
    if (aiSuggestions.solutions) {
      aiSuggestions.solutions.forEach((solution: string, index: number) => {
        if (selectedSolutions.has(index)) {
          allSelected.push(`Solution: ${solution}`);
        }
      });
    }
    
    if (allSelected.length === 0) {
      alert('Please select at least one suggestion');
      return;
    }
    
    const combinedText = allSelected.join('\n\n');
    setNewComment(combinedText);
    setCommentDialogOpen(true);
    
    // Clear selections after opening dialog
    setSelectedActions(new Set());
    setSelectedQuestions(new Set());
    setSelectedSolutions(new Set());
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
          {id && (
            <>
              <TicketTemplateSelector
                ticketId={id}
                onTemplateApplied={async (template) => {
                  setSuccess(`Template "${template.name}" applied successfully!`);
                  await loadTicket();
                  await loadCurrentNPA();
                }}
              />
              <TicketMacroMenu
                ticketId={id}
                onMacroExecuted={async () => {
                  setSuccess('Macro executed successfully!');
                  await loadTicket();
                  await loadCurrentNPA();
                }}
                onError={(error) => setError(error)}
              />
            </>
          )}
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
        <Divider />
        <MenuItem onClick={() => { setActionMenuAnchor(null); setMergeDialogOpen(true); }}>
          <ListItemIcon><MergeTypeIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Merge Ticket</ListItemText>
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
          <Grid size={{ xs: 12, md: 8 }}>
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
            {ticket?.customer_name && (
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Customer: {ticket.customer_name}
              </Typography>
            )}
            {!ticket?.customer_name && ticket?.customer_id && (
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Customer ID: {ticket.customer_id}
              </Typography>
            )}
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
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
              <Grid size={{ xs: 12, sm: 6 }}>
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
              <Grid size={{ xs: 12, sm: 6 }}>
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
          <Tab label="Q&A" icon={<QuestionAnswerIcon />} />
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
            <Stack direction="row" spacing={1}>
              {ticket?.description_ai_cleanup_status === 'processing' && (
                <Chip
                  label="AI Cleaning..."
                  color="info"
                  size="small"
                  icon={<CircularProgress size={12} />}
                />
              )}
              {ticket?.description_ai_cleanup_status === 'completed' && (
                <Chip
                  label="AI Cleaned"
                  color="success"
                  size="small"
                  icon={<SparkleIcon />}
                />
              )}
              <Button
                variant="outlined"
                size="small"
                startIcon={analyzing ? <CircularProgress size={16} /> : <SparkleIcon />}
                onClick={handleRunAIAnalysis}
                disabled={analyzing}
              >
                {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
              </Button>
            </Stack>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {ticket?.description_ai_cleanup_status === 'processing' && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                AI is cleaning up the description for customer-facing communication...
              </Typography>
            </Box>
          )}

          {/* Two-column editable description */}
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={8}
                label="Original Description (Agent Typed)"
                value={ticket?.original_description || ticket?.description || ''}
                onChange={(e) => {
                  const newValue = e.target.value;
                  // Update local state immediately
                  setTicket({ ...ticket, original_description: newValue });
                  
                  // Debounce auto-save
                  if ((window as any).descriptionSaveTimeout) {
                    clearTimeout((window as any).descriptionSaveTimeout);
                  }
                  (window as any).descriptionSaveTimeout = setTimeout(async () => {
                    try {
                      await helpdeskAPI.updateTicket(id!, {
                        original_description: newValue,
                        description: newValue, // Update main description too
                        trigger_description_cleanup: true // Trigger AI cleanup
                      });
                      await loadTicket(); // Reload to get cleaned version
                    } catch (error) {
                      console.error('Error updating description:', error);
                    }
                  }, 1000);
                }}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'grey.50',
                    fontFamily: 'monospace'
                  }
                }}
                helperText="Type your notes here - AI will clean this automatically in the background"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={8}
                label="AI-Cleaned Description (Customer-Facing)"
                value={ticket?.cleaned_description || ticket?.improved_description || ticket?.description || ''}
                onChange={(e) => {
                  const newValue = e.target.value;
                  // Update local state immediately
                  setTicket({ ...ticket, cleaned_description: newValue });
                  
                  // Debounce auto-save
                  if ((window as any).cleanedDescriptionSaveTimeout) {
                    clearTimeout((window as any).cleanedDescriptionSaveTimeout);
                  }
                  (window as any).cleanedDescriptionSaveTimeout = setTimeout(async () => {
                    try {
                      await helpdeskAPI.updateTicket(id!, {
                        cleaned_description: newValue,
                        description: newValue // Update main description to cleaned version
                      });
                      await loadTicket();
                    } catch (error) {
                      console.error('Error updating cleaned description:', error);
                    }
                  }, 1000);
                }}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'success.50',
                    borderColor: 'success.main'
                  }
                }}
                helperText="Professional version for customer communication (editable)"
              />
            </Grid>
          </Grid>

          {/* Next Point of Action */}
          <Box sx={{ mt: 3 }}>
            <TicketNPA 
              ticketId={id!} 
              ticketStatus={ticket?.status || ''}
              onUpdate={loadTicket}
              showHistory={false}
            />
          </Box>
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

              {/* Knowledge Base Suggestions */}
              {kbSuggestions.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Divider sx={{ mb: 2 }} />
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ArticleIcon color="primary" /> Suggested Knowledge Base Articles
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    AI-suggested articles that may help resolve this ticket
                  </Typography>
                  <List>
                    {kbSuggestions.map((suggestion: any, index: number) => (
                      <ListItem
                        key={index}
                        sx={{
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1
                        }}
                      >
                        <ListItemIcon>
                          <ArticleIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={suggestion.article?.title || suggestion.title}
                          secondary={`Relevance: ${suggestion.relevance_score ? (suggestion.relevance_score * 100).toFixed(0) + '%' : 'High'}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* AI Tools Section */}
              <Box sx={{ mb: 3 }}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BuildIcon color="primary" /> AI Tools
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Use AI to improve ticket description or generate auto responses
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={improvingDescription ? <CircularProgress size={16} /> : <EditIcon />}
                    onClick={handleImproveDescription}
                    disabled={improvingDescription || !ticket?.description}
                  >
                    {improvingDescription ? 'Improving...' : 'Improve Description'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={generatingAutoResponse ? <CircularProgress size={16} /> : <SendIcon />}
                    onClick={() => handleGenerateAutoResponse('acknowledgment')}
                    disabled={generatingAutoResponse}
                  >
                    {generatingAutoResponse ? 'Generating...' : 'Auto Response'}
                  </Button>
                </Stack>
                {ticket?.improved_description && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Improved Description:</Typography>
                    <Typography variant="body2">{ticket.improved_description}</Typography>
                  </Alert>
                )}
              </Box>

              {/* Knowledge Base Answer Generation */}
              <Box sx={{ mb: 3 }}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <QuestionAnswerIcon color="primary" /> Find Answer & Generate Response
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Use AI to find answers from knowledge base or generate a response. Works even without KB articles.
                </Typography>
                <TicketKBAnswer 
                  ticketId={id!}
                  onAnswerGenerated={(answer) => {
                    setNewComment(answer);
                    setCommentDialogOpen(true);
                  }}
                />
              </Box>

              {/* Next Actions - Actionable */}
              {aiSuggestions.next_actions && aiSuggestions.next_actions.length > 0 && (
                <Card sx={{ mb: 2, borderLeft: '4px solid', borderLeftColor: 'primary.main' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PlayArrowIcon color="primary" /> Next Actions
                      </Typography>
                      {(selectedActions.size > 0 || selectedQuestions.size > 0 || selectedSolutions.size > 0) && (
                        <ButtonGroup size="small" variant="contained">
                          <Button
                            startIcon={<AssignmentIcon />}
                            onClick={handleApplySelectedToNPA}
                            color="primary"
                          >
                            Add {selectedActions.size + selectedQuestions.size + selectedSolutions.size} to NPA
                          </Button>
                          <Button
                            startIcon={<AddCommentIcon />}
                            onClick={handleApplySelectedToComment}
                            color="secondary"
                          >
                            Add to Comment
                          </Button>
                        </ButtonGroup>
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Select actions to add to NPA (recommended) or as comments
                    </Typography>
                    <List>
                      {aiSuggestions.next_actions.map((action: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: selectedActions.has(index) ? '2px solid' : '1px solid',
                            borderColor: selectedActions.has(index) ? 'primary.main' : 'divider',
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: selectedActions.has(index) ? 'action.selected' : 'background.paper',
                            '&:hover': {
                              bgcolor: 'action.hover'
                            }
                          }}
                        >
                          <ListItemIcon>
                            <Checkbox
                              checked={selectedActions.has(index)}
                              onChange={(e) => {
                                const newSet = new Set(selectedActions);
                                if (e.target.checked) {
                                  newSet.add(index);
                                } else {
                                  newSet.delete(index);
                                }
                                setSelectedActions(newSet);
                              }}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={action}
                            secondary={selectedActions.has(index) ? "Selected - will be added to NPA" : "Select to add to NPA or comment"}
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
                            Quick Add Comment
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
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Select questions to add to NPA (recommended) or as comments
                    </Typography>
                    <List>
                      {aiSuggestions.questions.map((question: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: selectedQuestions.has(index) ? '2px solid' : '1px solid',
                            borderColor: selectedQuestions.has(index) ? 'warning.main' : 'divider',
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: selectedQuestions.has(index) ? 'action.selected' : 'background.paper',
                            '&:hover': {
                              bgcolor: 'action.hover'
                            }
                          }}
                        >
                          <ListItemIcon>
                            <Checkbox
                              checked={selectedQuestions.has(index)}
                              onChange={(e) => {
                                const newSet = new Set(selectedQuestions);
                                if (e.target.checked) {
                                  newSet.add(index);
                                } else {
                                  newSet.delete(index);
                                }
                                setSelectedQuestions(newSet);
                              }}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={question}
                            secondary={selectedQuestions.has(index) ? "Selected - will be added to NPA" : "Select to add to NPA or comment"}
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
                            Quick Add Comment
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
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Select solutions to add to NPA (recommended) or as comments
                    </Typography>
                    <List>
                      {aiSuggestions.solutions.map((solution: string, index: number) => (
                        <ListItem
                          key={index}
                          sx={{
                            border: selectedSolutions.has(index) ? '2px solid' : '1px solid',
                            borderColor: selectedSolutions.has(index) ? 'success.main' : 'divider',
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: selectedSolutions.has(index) ? 'action.selected' : 'background.paper',
                            '&:hover': {
                              bgcolor: 'action.hover'
                            }
                          }}
                        >
                          <ListItemIcon>
                            <Checkbox
                              checked={selectedSolutions.has(index)}
                              onChange={(e) => {
                                const newSet = new Set(selectedSolutions);
                                if (e.target.checked) {
                                  newSet.add(index);
                                } else {
                                  newSet.delete(index);
                                }
                                setSelectedSolutions(newSet);
                              }}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={solution}
                            secondary={selectedSolutions.has(index) ? "Selected - will be added to NPA" : "Select to add to NPA or comment"}
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
                            Quick Add Comment
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

      {/* Tab Panel 2: Q&A - Agent Chatbot */}
      {currentTab === 2 && (
        <Paper sx={{ p: 3, height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
          <TicketChatbot ticketId={id!} />
        </Paper>
      )}

      {/* Tab Panel 3: Comments */}
      {currentTab === 3 && (
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

      {/* Tab Panel 4: History */}
      {currentTab === 4 && (
        <Box>
          {/* Ticket History */}
          <Paper sx={{ p: 3, mb: 3 }}>
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
              <Alert severity="info">No ticket history available.</Alert>
            )}
          </Paper>

          {/* NPA History (Call History) */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ArticleIcon />
              <Typography variant="h6">NPA History (Call History)</Typography>
              {loadingNpaHistory && <CircularProgress size={20} />}
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {loadingNpaHistory ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : npaHistory.length === 0 ? (
              <Alert severity="info">No NPA history available yet.</Alert>
            ) : (
              <List>
                {npaHistory.map((entry: any, index: number) => (
                  <Accordion key={entry.id} defaultExpanded={index === npaHistory.length - 1}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                        <Chip
                          label={`NPA #${npaHistory.length - index}`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={entry.npa_state === 'investigation' ? 'Investigation' : 
                                 entry.npa_state === 'waiting_customer' ? 'Waiting for Customer' :
                                 entry.npa_state === 'waiting_vendor' ? 'Waiting for Vendor' :
                                 entry.npa_state === 'waiting_parts' ? 'Waiting for Parts' :
                                 entry.npa_state === 'solution' ? 'Solution' :
                                 entry.npa_state === 'implementation' ? 'Implementation' :
                                 entry.npa_state === 'testing' ? 'Testing' :
                                 entry.npa_state === 'documentation' ? 'Documentation' :
                                 entry.npa_state || 'Other'}
                          color={entry.npa_state === 'waiting_customer' || entry.npa_state === 'waiting_vendor' || entry.npa_state === 'waiting_parts' ? 'warning' :
                                 entry.npa_state === 'solution' ? 'success' :
                                 entry.npa_state === 'investigation' ? 'info' : 'default' as any}
                          size="small"
                        />
                        {entry.completed_at && (
                          <Chip
                            label={`Completed ${new Date(entry.completed_at).toLocaleDateString()}`}
                            color="success"
                            size="small"
                            variant="outlined"
                          />
                        )}
                        <Typography variant="body2" sx={{ ml: 'auto', color: 'text.secondary' }}>
                          {new Date(entry.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Original Text:
                        </Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                          {entry.npa_original_text}
                        </Typography>
                        
                        {entry.npa_cleaned_text && entry.npa_cleaned_text !== entry.npa_original_text && (
                          <>
                            <Typography variant="subtitle2" gutterBottom>
                              Cleaned Text (Customer-Facing):
                            </Typography>
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                              {entry.npa_cleaned_text}
                            </Typography>
                          </>
                        )}
                        
                        {entry.assigned_to_name && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Assigned to: {entry.assigned_to_name}
                          </Typography>
                        )}
                        
                        {entry.due_date && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Due: {new Date(entry.due_date).toLocaleString()}
                          </Typography>
                        )}
                        
                        {entry.completion_notes && (
                          <>
                            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                              Completion Notes:
                            </Typography>
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                              {entry.completion_notes}
                            </Typography>
                          </>
                        )}
                      </Box>
                      
                      {entry.answers_to_questions && (
                        <>
                          <Divider sx={{ my: 2 }} />
                          <Typography variant="subtitle2" gutterBottom>
                            Answers to Questions:
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                            {entry.answers_to_questions}
                          </Typography>
                          {entry.answers_cleaned_text && entry.answers_cleaned_text !== entry.answers_to_questions && (
                            <>
                              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                                AI-Cleaned Answers:
                              </Typography>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                {entry.answers_cleaned_text}
                              </Typography>
                            </>
                          )}
                        </>
                      )}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </List>
            )}
          </Paper>
        </Box>
      )}

      {/* Add Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
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
            <Button
              variant="outlined"
              startIcon={<ReplyIcon />}
              onClick={(e) => setQuickReplyAnchor(e.currentTarget)}
              sx={{ mt: 2, minWidth: 120 }}
              size="small"
            >
              Quick Reply
            </Button>
          </Box>
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
        
        {/* Quick Reply Menu */}
        <QuickReplyMenu
          anchorEl={quickReplyAnchor}
          open={Boolean(quickReplyAnchor)}
          onClose={() => setQuickReplyAnchor(null)}
          onSelect={(content) => {
            setNewComment(prev => prev ? `${prev}\n\n${content}` : content);
            setQuickReplyAnchor(null);
          }}
          ticketId={id || undefined}
        />
      </Dialog>

      {/* NPA State Selection Dialog */}
      <Dialog 
        open={npaDialogOpen} 
        onClose={() => {
          setNpaDialogOpen(false);
          // Reset to defaults when closing
          setSelectedNpaState('investigation');
          setSelectedExcludeFromSla(false);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Set NPA State & Options</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {/* Show current NPA if exists */}
            {currentNpa?.npa_original_text && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Current NPA:
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', maxHeight: '100px', overflow: 'auto' }}>
                  {currentNpa.npa_original_text.substring(0, 200)}
                  {currentNpa.npa_original_text.length > 200 ? '...' : ''}
                </Typography>
              </Alert>
            )}
            
            {/* Action selection: Append or New */}
            {currentNpa?.npa_original_text && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Action</InputLabel>
                <Select
                  value={npaAction}
                  label="Action"
                  onChange={(e) => setNpaAction(e.target.value as 'append' | 'new')}
                >
                  <MenuItem value="append">Add to existing NPA (append)</MenuItem>
                  <MenuItem value="new">Close current NPA and create new one</MenuItem>
                </Select>
              </FormControl>
            )}
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>NPA State</InputLabel>
              <Select
                value={selectedNpaState}
                label="NPA State"
                onChange={(e) => {
                  setSelectedNpaState(e.target.value);
                  // Auto-set exclude_from_sla for waiting states
                  const waitingStates = ['waiting_customer', 'waiting_vendor', 'waiting_parts'];
                  if (waitingStates.includes(e.target.value)) {
                    setSelectedExcludeFromSla(true);
                  } else if (e.target.value === 'investigation') {
                    setSelectedExcludeFromSla(false);
                  }
                }}
              >
                <MenuItem value="investigation">Investigation (SLA Active)</MenuItem>
                <MenuItem value="waiting_customer">Waiting for Customer (Pause SLA)</MenuItem>
                <MenuItem value="waiting_vendor">Waiting for Vendor (Pause SLA)</MenuItem>
                <MenuItem value="waiting_parts">Waiting for Parts (Pause SLA)</MenuItem>
                <MenuItem value="solution">Solution (Customer-Facing)</MenuItem>
                <MenuItem value="implementation">Implementation (Customer-Facing)</MenuItem>
                <MenuItem value="testing">Testing</MenuItem>
                <MenuItem value="documentation">Documentation</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={selectedExcludeFromSla}
                  onChange={(e) => setSelectedExcludeFromSla(e.target.checked)}
                  disabled={['waiting_customer', 'waiting_vendor', 'waiting_parts'].includes(selectedNpaState)}
                />
              }
              label="Exclude from SLA (pause SLA tracking)"
            />
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                {currentNpa?.npa_original_text ? (
                  <>
                    <strong>Add to existing:</strong> Appends suggestions to the current NPA.
                    <br />
                    <strong>Create new:</strong> Marks current NPA as "Solution" and creates a new NPA.
                    <br /><br />
                  </>
                ) : null}
                <strong>Waiting states</strong> (Waiting for Customer/Vendor/Parts) automatically pause SLA tracking.
                <br />
                <strong>Investigation</strong> keeps SLA active and tracks response time.
                <br />
                <strong>Solution/Implementation</strong> are customer-facing and will trigger AI cleanup for professional communication.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setNpaDialogOpen(false);
            setSelectedNpaState('investigation');
            setSelectedExcludeFromSla(false);
            setNpaAction('append');
          }}>Cancel</Button>
          <Button variant="contained" onClick={handleConfirmApplyToNPA} startIcon={<AssignmentIcon />}>
            {npaAction === 'append' ? 'Add to NPA' : 'Create New NPA'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Keyboard Shortcuts Help */}
      <KeyboardShortcutsHelp
        open={shortcutsHelpOpen}
        onClose={() => setShortcutsHelpOpen(false)}
        customShortcuts={[
          { key: 's', ctrl: true, description: 'Save ticket' },
          { key: 'e', ctrl: true, description: 'Edit ticket' },
          { key: 'a', ctrl: true, description: 'Assign ticket' },
          { key: 'r', ctrl: true, description: 'Reply/Add Comment' },
          { key: 'k', ctrl: true, description: 'Open Knowledge Base' },
          { key: '/', ctrl: true, description: 'Show Shortcuts Help' },
          { key: 'Escape', description: 'Close Dialog' }
        ]}
      />

      {/* Merge Ticket Dialog */}
      {ticket && (
        <TicketMergeDialog
          open={mergeDialogOpen}
          onClose={() => setMergeDialogOpen(false)}
          sourceTicket={{
            id: ticket.id,
            ticket_number: ticket.ticket_number,
            subject: ticket.subject,
            status: ticket.status,
            priority: ticket.priority,
            created_at: ticket.created_at
          }}
          onMergeSuccess={async () => {
            setSuccess('Ticket merged successfully!');
            await loadTicket();
          }}
        />
      )}
    </Container>
  );
};

export default TicketDetail;
