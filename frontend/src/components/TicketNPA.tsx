import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Stack,
  Grid,
  FormControlLabel,
  Checkbox,
  Divider,
  LinearProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Article as ArticleIcon,
  AutoAwesome as AutoAwesomeIcon,
  Block as BlockIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Lightbulb as LightbulbIcon,
  Build as BuildIcon,
  PersonSearch as PersonSearchIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Search as SearchIcon,
  Done as DoneIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';
import { DateTimePicker } from '@mui/x-date-pickers';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface TicketNPAProps {
  ticketId: string;
  ticketStatus: string;
  onUpdate?: () => void;
}

const NPA_STATES = [
  { value: 'investigation', label: 'Investigation' },
  { value: 'waiting_customer', label: 'Waiting for Customer' },
  { value: 'waiting_vendor', label: 'Waiting for Vendor' },
  { value: 'waiting_parts', label: 'Waiting for Parts' },
  { value: 'solution', label: 'Solution' },
  { value: 'implementation', label: 'Implementation' },
  { value: 'testing', label: 'Testing' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'other', label: 'Other' }
];

const TicketNPA: React.FC<TicketNPAProps> = ({
  ticketId,
  ticketStatus,
  onUpdate,
  showHistory = true // Default to true for backward compatibility
}) => {
  const [loading, setLoading] = useState(true);
  const [npa, setNpa] = useState<any>(null);
  const [npaHistory, setNpaHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [editing, setEditing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addingToKB, setAddingToKB] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<any>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [answers, setAnswers] = useState<{ [key: string]: string }>({}); // key: npa_history_id or 'current' (original)
  const [answersCleaned, setAnswersCleaned] = useState<{ [key: string]: string }>({}); // key: npa_history_id or 'current' (cleaned)
  const [answersCleanupStatus, setAnswersCleanupStatus] = useState<{ [key: string]: string }>({}); // AI cleanup status
  const [savingAnswers, setSavingAnswers] = useState<{ [key: string]: boolean }>({});
  
  // Edit form state
  const [editNpaOriginal, setEditNpaOriginal] = useState('');
  const [editNpaCleaned, setEditNpaCleaned] = useState('');
  const [editNpaState, setEditNpaState] = useState('investigation');
  const [editDueDate, setEditDueDate] = useState<Date | null>(null);
  const [editDateOverride, setEditDateOverride] = useState(false);
  const [editAssignedTo, setEditAssignedTo] = useState('');
  const [editExcludeFromSla, setEditExcludeFromSla] = useState(false);

  // Initial load
  useEffect(() => {
    loadNPA();
    loadNPAHistory();
  }, [ticketId]);

  // Use refs to track cleanup status without causing re-renders
  const npaCleanupStatusRef = useRef<string | null>(null);
  const answersCleanupStatusRef = useRef<string | null>(null);
  const historyCleanupStatusRef = useRef<{ [key: string]: string }>({});
  
  // Update refs when status changes
  useEffect(() => {
    npaCleanupStatusRef.current = npa?.npa_ai_cleanup_status || null;
    answersCleanupStatusRef.current = npa?.npa_answers_ai_cleanup_status || null;
    // Also update the state for current answers cleanup status
    if (npa?.npa_answers_ai_cleanup_status) {
      setAnswersCleanupStatus(prev => ({ ...prev, current: npa.npa_answers_ai_cleanup_status }));
    }
  }, [npa?.npa_ai_cleanup_status, npa?.npa_answers_ai_cleanup_status]);
  
  useEffect(() => {
    historyCleanupStatusRef.current = answersCleanupStatus;
  }, [answersCleanupStatus]);
  
  // Separate polling effect - only runs when cleanup is actually processing
  useEffect(() => {
    const currentAnswersStatus = answersCleanupStatus['current'] || npa?.npa_answers_ai_cleanup_status;
    const checkProcessing = () => {
      const npaProcessing = npaCleanupStatusRef.current === 'processing';
      const answersProcessing = answersCleanupStatusRef.current === 'processing' || currentAnswersStatus === 'processing';
      const historyProcessing = Object.values(historyCleanupStatusRef.current).some(status => status === 'processing');
      return npaProcessing || answersProcessing || historyProcessing;
    };
    
    if (!checkProcessing()) {
      return; // Nothing is processing, don't poll
    }
    
    const interval = setInterval(() => {
      // Only reload if still processing
      if (checkProcessing()) {
        if (npaCleanupStatusRef.current === 'processing' || answersCleanupStatusRef.current === 'processing' || currentAnswersStatus === 'processing') {
          loadNPA();
        }
        const hasProcessingHistory = Object.values(historyCleanupStatusRef.current).some(status => status === 'processing');
        if (hasProcessingHistory) {
          loadNPAHistory();
        }
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [ticketId, npa?.npa_answers_ai_cleanup_status, answersCleanupStatus['current']]); // Include answers cleanup status

  const loadNPA = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.getTicketNPA(ticketId);
      setNpa(response.data);
      // Initialize current NPA answers if available
      if (response.data?.npa_answers_original_text) {
        setAnswers(prev => ({ ...prev, current: response.data.npa_answers_original_text }));
      }
      if (response.data?.npa_answers_cleaned_text) {
        setAnswersCleaned(prev => ({ ...prev, current: response.data.npa_answers_cleaned_text }));
      }
      if (response.data?.npa_answers_ai_cleanup_status) {
        setAnswersCleanupStatus(prev => ({ ...prev, current: response.data.npa_answers_ai_cleanup_status }));
      }
    } catch (error: any) {
      console.error('Error loading NPA:', error);
      setError(error.response?.data?.detail || 'Failed to load NPA');
    } finally {
      setLoading(false);
    }
  };

  const loadNPAHistory = async () => {
    try {
      setLoadingHistory(true);
      const response = await helpdeskAPI.getTicketNPAHistory(ticketId);
      setNpaHistory(response.data.history || []);
      // Initialize answers from history
      const historyAnswers: { [key: string]: string } = {};
      const historyAnswersCleaned: { [key: string]: string } = {};
      const historyCleanupStatus: { [key: string]: string } = {};
      (response.data.history || []).forEach((entry: any) => {
        if (entry.answers_to_questions) {
          historyAnswers[entry.id] = entry.answers_to_questions;
        }
        if (entry.answers_cleaned_text) {
          historyAnswersCleaned[entry.id] = entry.answers_cleaned_text;
        }
        if (entry.answers_ai_cleanup_status) {
          historyCleanupStatus[entry.id] = entry.answers_ai_cleanup_status;
        }
      });
      setAnswers(prev => ({ ...prev, ...historyAnswers }));
      setAnswersCleaned(prev => ({ ...prev, ...historyAnswersCleaned }));
      setAnswersCleanupStatus(prev => ({ ...prev, ...historyCleanupStatus }));
    } catch (error: any) {
      console.error('Error loading NPA history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSaveAnswers = async (npaHistoryId: string | 'current', answerText: string, triggerCleanup: boolean = true) => {
    try {
      setSavingAnswers(prev => ({ ...prev, [npaHistoryId]: true }));
      
      let response;
      if (npaHistoryId === 'current') {
        response = await helpdeskAPI.updateCurrentNPAAnswers(ticketId, answerText, triggerCleanup);
      } else {
        response = await helpdeskAPI.updateNPAHistoryAnswers(ticketId, npaHistoryId, answerText, triggerCleanup);
      }
      
      // Update cleaned text and status from response
      if (response.data.answers_original_text) {
        setAnswers(prev => ({ ...prev, [npaHistoryId]: response.data.answers_original_text }));
      }
      if (response.data.answers_cleaned_text) {
        setAnswersCleaned(prev => ({ ...prev, [npaHistoryId]: response.data.answers_cleaned_text }));
      }
      if (response.data.ai_cleanup_status) {
        setAnswersCleanupStatus(prev => ({ ...prev, [npaHistoryId]: response.data.ai_cleanup_status }));
      }
      
      // Reload to get updated data (including any AI cleanup that completed)
      await loadNPA();
      if (npaHistoryId !== 'current') {
        await loadNPAHistory();
      }
    } catch (error: any) {
      console.error('Error saving answers:', error);
      alert(error.response?.data?.detail || 'Failed to save answers');
    } finally {
      setSavingAnswers(prev => ({ ...prev, [npaHistoryId]: false }));
    }
  };

  const loadAISuggestions = async () => {
    try {
      setLoadingSuggestions(true);
      const response = await helpdeskAPI.getNPAAISuggestions(ticketId);
      if (response.data.success) {
        setAiSuggestions(response.data.suggestions);
      }
    } catch (error: any) {
      console.error('Error loading AI suggestions:', error);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const response = await helpdeskAPI.regenerateTicketNPA(ticketId);
      if (response.data.success) {
        await loadNPA();
        await loadNPAHistory();
        if (onUpdate) onUpdate();
      }
    } catch (error: any) {
      console.error('Error regenerating NPA:', error);
      setError(error.response?.data?.detail || 'Failed to regenerate NPA');
    } finally {
      setRegenerating(false);
    }
  };

  const handleEdit = () => {
    setEditNpaOriginal(npa?.npa_original_text || npa?.npa || '');
    setEditNpaCleaned(npa?.npa_cleaned_text || npa?.npa || '');
    setEditNpaState(npa?.npa_state || 'investigation');
    setEditDueDate(npa?.due_date ? new Date(npa.due_date) : null);
    setEditDateOverride(npa?.npa_date_override || false);
    setEditAssignedTo(npa?.assigned_to || '');
    setEditExcludeFromSla(npa?.npa_exclude_from_sla || false);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      setError(null);
      const dueDateStr = editDueDate ? editDueDate.toISOString() : undefined;
      
      await helpdeskAPI.updateTicketNPA(ticketId, {
        npa: editNpaOriginal,
        due_date: dueDateStr,
        assigned_to_id: editAssignedTo || undefined,
        npa_state: editNpaState,
        date_override: editDateOverride,
        exclude_from_sla: editExcludeFromSla,
        trigger_ai_cleanup: editNpaState === 'solution' || editNpaState === 'waiting_customer' || editNpaState === 'implementation'
      });
      
      setEditDialogOpen(false);
      await loadNPA();
      await loadNPAHistory();
      if (onUpdate) onUpdate();
    } catch (error: any) {
      console.error('Error updating NPA:', error);
      setError(error.response?.data?.detail || 'Failed to update NPA');
    }
  };

  const handleAddToKB = async () => {
    if (!npa?.npa_cleaned_text && !npa?.npa) {
      alert('No NPA text available to add to knowledge base');
      return;
    }

    if (!window.confirm('Create a knowledge base article from this solution?')) {
      return;
    }

    setAddingToKB(true);
    try {
      // Get ticket details for context
      const ticketResponse = await helpdeskAPI.getTicket(ticketId);
      const ticket = ticketResponse.data;

      // Create KB article
      await helpdeskAPI.createKnowledgeBaseArticle({
        title: `Solution: ${ticket.subject || 'Ticket Solution'}`,
        content: npa.npa_cleaned_text || npa.npa,
        summary: `Solution for: ${ticket.subject || 'Ticket'}`,
        category: 'Solutions',
        tags: [ticket.ticket_type || 'support', 'solution'],
        is_published: true,
        is_featured: false
      });

      alert('Knowledge base article created successfully!');
    } catch (error: any) {
      console.error('Error adding to KB:', error);
      alert(error.response?.data?.detail || 'Failed to create knowledge base article');
    } finally {
      setAddingToKB(false);
    }
  };

  const handleApplySelectedSuggestions = async () => {
    if (selectedSuggestions.size === 0) return;

    try {
      setError(null);
      
      // Build combined NPA text from selected suggestions
      let combinedText = '';
      
      if (selectedSuggestions.has('agent') && aiSuggestions?.suggested_agent) {
        const agent = aiSuggestions.suggested_agent;
        combinedText += `Assign to ${agent.agent_type || 'appropriate agent'}: ${agent.reason}`;
        if (agent.skills_needed && agent.skills_needed.length > 0) {
          combinedText += ` (Skills needed: ${agent.skills_needed.join(', ')})`;
        }
        combinedText += '\n\n';
      }
      
      if (selectedSuggestions.has('diagnosis') && aiSuggestions?.issue_diagnosis) {
        const diagnosis = aiSuggestions.issue_diagnosis;
        combinedText += `Issue Diagnosis: ${diagnosis.likely_cause}`;
        if (diagnosis.alternative_causes && diagnosis.alternative_causes.length > 0) {
          combinedText += `\nAlternative causes: ${diagnosis.alternative_causes.join(', ')}`;
        }
        combinedText += '\n\n';
      }
      
      if (selectedSuggestions.has('troubleshooting') && aiSuggestions?.troubleshooting_steps) {
        combinedText += 'Troubleshooting Steps:\n';
        aiSuggestions.troubleshooting_steps.forEach((step: any) => {
          combinedText += `${step.step}. ${step.action} (Expected: ${step.expected_result})`;
          if (step.if_fails) {
            combinedText += ` - If fails: ${step.if_fails}`;
          }
          combinedText += '\n';
        });
      }
      
      // Update NPA with combined text
      await helpdeskAPI.updateTicketNPA(ticketId, {
        npa: combinedText.trim(),
        npa_state: npa?.npa_state || 'investigation',
        trigger_ai_cleanup: true
      });
      
      // Clear selections and reload
      setSelectedSuggestions(new Set());
      await loadNPA();
      await loadNPAHistory();
      if (onUpdate) onUpdate();
      
      alert('Selected suggestions applied to NPA successfully!');
    } catch (error: any) {
      console.error('Error applying suggestions:', error);
      setError(error.response?.data?.detail || 'Failed to apply suggestions');
    }
  };

  const isOverdue = npa?.due_date && new Date(npa.due_date) < new Date();
  const isClosed = ['closed', 'resolved', 'cancelled'].includes(ticketStatus?.toLowerCase());
  const isSolution = npa?.npa_state === 'solution';
  const waitingStates = ['waiting_customer', 'waiting_vendor', 'waiting_parts'];
  const isWaiting = waitingStates.includes(npa?.npa_state);

  const getStateColor = (state: string) => {
    switch (state) {
      case 'solution': return 'success';
      case 'waiting_customer': return 'warning';
      case 'waiting_vendor': return 'warning';
      case 'waiting_parts': return 'warning';
      case 'investigation': return 'info';
      default: return 'default';
    }
  };

  const getCleanupStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'info';
      case 'failed': return 'error';
      case 'skipped': return 'default';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  // Don't show NPA for closed/resolved tickets
  if (isClosed) {
    return null;
  }

  // Show warning if NPA is missing
  if (!npa?.has_npa && npa?.required) {
    return (
      <Alert 
        severity="warning" 
        action={
          <Button size="small" onClick={handleRegenerate} disabled={regenerating}>
            {regenerating ? <CircularProgress size={16} /> : 'Generate NPA'}
          </Button>
        }
      >
        <Typography variant="body2">
          This ticket is missing a Next Point of Action. Generate one now to ensure the ticket progresses.
        </Typography>
      </Alert>
    );
  }

  const originalText = npa?.npa_original_text || npa?.npa || '';
  const cleanedText = npa?.npa_cleaned_text || npa?.npa || '';

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, border: isOverdue ? '2px solid' : '1px solid', borderColor: isOverdue ? 'error.main' : 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <AssignmentIcon color={isOverdue ? 'error' : 'primary'} />
            <Typography variant="h6">
              Next Point of Action
            </Typography>
            {npa?.npa_state && (
              <Chip
                label={NPA_STATES.find(s => s.value === npa.npa_state)?.label || npa.npa_state}
                color={getStateColor(npa.npa_state) as any}
                size="small"
              />
            )}
            {isOverdue && (
              <Chip
                label="Overdue"
                color="error"
                size="small"
                icon={<WarningIcon />}
              />
            )}
            {npa?.npa_exclude_from_sla && (
              <Chip
                label="SLA Excluded"
                size="small"
                variant="outlined"
                icon={<BlockIcon />}
                color="warning"
              />
            )}
            {npa?.auto_generated && (
              <Chip
                label="AI Generated"
                size="small"
                variant="outlined"
              />
            )}
            {npa?.npa_ai_cleanup_status && npa.npa_ai_cleanup_status !== 'skipped' && (
              <Chip
                label={
                  npa.npa_ai_cleanup_status === 'processing' ? 'AI Cleaning...' :
                  npa.npa_ai_cleanup_status === 'completed' ? 'AI Cleaned' :
                  npa.npa_ai_cleanup_status === 'failed' ? 'AI Cleanup Failed' :
                  'AI Cleanup Pending'
                }
                color={getCleanupStatusColor(npa.npa_ai_cleanup_status) as any}
                size="small"
                icon={npa.npa_ai_cleanup_status === 'processing' ? <CircularProgress size={12} /> : <AutoAwesomeIcon />}
              />
            )}
          </Box>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {/* Quick Actions */}
            {!isWaiting && (
              <Tooltip title="Pause SLA (Set to Waiting State)">
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<PauseIcon />}
                  onClick={() => {
                    setEditNpaState('waiting_customer');
                    setEditNpaOriginal(npa?.npa_original_text || npa?.npa || 'Waiting for customer response');
                    setEditNpaCleaned(npa?.npa_cleaned_text || npa?.npa || 'We are waiting for your response to proceed.');
                    setEditExcludeFromSla(true);
                    setEditDialogOpen(true);
                  }}
                  color="warning"
                >
                  Pause SLA
                </Button>
              </Tooltip>
            )}
            {isWaiting && (
              <Tooltip title="Resume SLA (Continue Work)">
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<PlayArrowIcon />}
                  onClick={() => {
                    setEditNpaState('investigation');
                    setEditNpaOriginal(npa?.npa_original_text || npa?.npa || 'Continue investigation');
                    setEditNpaCleaned(npa?.npa_cleaned_text || npa?.npa || 'Continuing investigation');
                    setEditExcludeFromSla(false);
                    setEditDialogOpen(true);
                  }}
                  color="success"
                >
                  Resume SLA
                </Button>
              </Tooltip>
            )}
            <Tooltip title="Mark Complete & Set Next Task">
              <Button
                size="small"
                variant="contained"
                startIcon={<DoneIcon />}
                onClick={() => {
                  setEditNpaState('solution');
                  setEditNpaOriginal('Solution found - ready for implementation');
                  setEditNpaCleaned('We have identified a solution and are ready to implement it.');
                  setEditExcludeFromSla(false);
                  setEditDialogOpen(true);
                }}
                color="success"
              >
                Complete & Next
              </Button>
            </Tooltip>
            <Tooltip title="Get AI Suggestions">
              <IconButton 
                size="small" 
                onClick={loadAISuggestions} 
                disabled={loadingSuggestions}
                color="primary"
              >
                {loadingSuggestions ? <CircularProgress size={16} /> : <LightbulbIcon />}
              </IconButton>
            </Tooltip>
            {isSolution && (
              <Tooltip title="Add to Knowledge Base">
                <IconButton 
                  size="small" 
                  onClick={handleAddToKB} 
                  disabled={addingToKB}
                  color="primary"
                >
                  {addingToKB ? <CircularProgress size={16} /> : <ArticleIcon />}
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Regenerate with AI">
              <IconButton size="small" onClick={handleRegenerate} disabled={regenerating}>
                {regenerating ? <CircularProgress size={16} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Edit NPA">
              <IconButton size="small" onClick={handleEdit}>
                <EditIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {npa?.npa_ai_cleanup_status === 'processing' && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              AI is cleaning up the text for customer-facing communication...
            </Typography>
          </Box>
        )}

        {/* Two-column editable text display */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Original Text (Agent Typed)"
              value={originalText}
              onChange={(e) => {
                // Update local state for immediate feedback
                setNpa({ ...npa, npa_original_text: e.target.value });
                // Auto-save after a delay
                const timeoutId = setTimeout(() => {
                  helpdeskAPI.updateTicketNPA(ticketId, {
                    npa: e.target.value,
                    npa_state: npa?.npa_state || 'investigation',
                    trigger_ai_cleanup: true
                  }).then(() => loadNPA());
                }, 1000);
                return () => clearTimeout(timeoutId);
              }}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'grey.50',
                  fontFamily: 'monospace'
                }
              }}
              helperText="Type your notes here - AI will clean this automatically"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="AI-Cleaned Text (Customer-Facing)"
              value={cleanedText}
              onChange={(e) => {
                setNpa({ ...npa, npa_cleaned_text: e.target.value });
                // Auto-save
                const timeoutId = setTimeout(() => {
                  helpdeskAPI.updateTicketNPA(ticketId, {
                    npa: npa?.npa_original_text || e.target.value,
                    npa_state: npa?.npa_state || 'investigation',
                    trigger_ai_cleanup: false
                  }).then(() => {
                    // Manually update cleaned text
                    helpdeskAPI.updateTicketNPA(ticketId, {
                      npa: npa?.npa_original_text || e.target.value,
                      npa_cleaned_text: e.target.value,
                      npa_state: npa?.npa_state || 'investigation',
                      trigger_ai_cleanup: false
                    }).then(() => loadNPA());
                  });
                }, 1000);
                return () => clearTimeout(timeoutId);
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

        {/* AI Suggestions Section */}
        {aiSuggestions && (
          <Box sx={{ mt: 3 }}>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LightbulbIcon color="primary" />
                AI Suggestions
              </Typography>
              {selectedSuggestions.size > 0 && (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<DoneIcon />}
                  onClick={handleApplySelectedSuggestions}
                  color="primary"
                >
                  Apply {selectedSuggestions.size} Selected
                </Button>
              )}
            </Box>
            
            <Grid container spacing={2}>
              {/* Agent Assignment Suggestion */}
              {aiSuggestions.suggested_agent && (
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card 
                    variant="outlined"
                    sx={{
                      border: selectedSuggestions.has('agent') ? '2px solid' : '1px solid',
                      borderColor: selectedSuggestions.has('agent') ? 'primary.main' : 'divider',
                      bgcolor: selectedSuggestions.has('agent') ? 'action.selected' : 'background.paper'
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <PersonSearchIcon fontSize="small" />
                          Suggested Agent
                        </Typography>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedSuggestions.has('agent')}
                              onChange={(e) => {
                                const newSet = new Set(selectedSuggestions);
                                if (e.target.checked) {
                                  newSet.add('agent');
                                } else {
                                  newSet.delete('agent');
                                }
                                setSelectedSuggestions(newSet);
                              }}
                              size="small"
                            />
                          }
                          label=""
                          sx={{ m: 0 }}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {aiSuggestions.suggested_agent.reason}
                      </Typography>
                      {aiSuggestions.suggested_agent.skills_needed && aiSuggestions.suggested_agent.skills_needed.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">Skills needed:</Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                            {aiSuggestions.suggested_agent.skills_needed.map((skill: string, idx: number) => (
                              <Chip key={idx} label={skill} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Issue Diagnosis */}
              {aiSuggestions.issue_diagnosis && (
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card 
                    variant="outlined"
                    sx={{
                      border: selectedSuggestions.has('diagnosis') ? '2px solid' : '1px solid',
                      borderColor: selectedSuggestions.has('diagnosis') ? 'primary.main' : 'divider',
                      bgcolor: selectedSuggestions.has('diagnosis') ? 'action.selected' : 'background.paper'
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <InfoIcon fontSize="small" />
                          Issue Diagnosis
                        </Typography>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedSuggestions.has('diagnosis')}
                              onChange={(e) => {
                                const newSet = new Set(selectedSuggestions);
                                if (e.target.checked) {
                                  newSet.add('diagnosis');
                                } else {
                                  newSet.delete('diagnosis');
                                }
                                setSelectedSuggestions(newSet);
                              }}
                              size="small"
                            />
                          }
                          label=""
                          sx={{ m: 0 }}
                        />
                      </Box>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Likely Cause:</strong> {aiSuggestions.issue_diagnosis.likely_cause}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Confidence: {Math.round((aiSuggestions.issue_diagnosis.confidence || 0) * 100)}% | 
                        Complexity: {aiSuggestions.issue_diagnosis.complexity || 'unknown'}
                      </Typography>
                      {aiSuggestions.issue_diagnosis.alternative_causes && aiSuggestions.issue_diagnosis.alternative_causes.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">Alternatives:</Typography>
                          <List dense>
                            {aiSuggestions.issue_diagnosis.alternative_causes.map((cause: string, idx: number) => (
                              <ListItem key={idx} sx={{ py: 0 }}>
                                <ListItemText primary={cause} primaryTypographyProps={{ variant: 'caption' }} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Troubleshooting Steps */}
              {aiSuggestions.troubleshooting_steps && aiSuggestions.troubleshooting_steps.length > 0 && (
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card 
                    variant="outlined"
                    sx={{
                      border: selectedSuggestions.has('troubleshooting') ? '2px solid' : '1px solid',
                      borderColor: selectedSuggestions.has('troubleshooting') ? 'primary.main' : 'divider',
                      bgcolor: selectedSuggestions.has('troubleshooting') ? 'action.selected' : 'background.paper'
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <BuildIcon fontSize="small" />
                          Troubleshooting Steps
                        </Typography>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedSuggestions.has('troubleshooting')}
                              onChange={(e) => {
                                const newSet = new Set(selectedSuggestions);
                                if (e.target.checked) {
                                  newSet.add('troubleshooting');
                                } else {
                                  newSet.delete('troubleshooting');
                                }
                                setSelectedSuggestions(newSet);
                              }}
                              size="small"
                            />
                          }
                          label=""
                          sx={{ m: 0 }}
                        />
                      </Box>
                      <List dense>
                        {aiSuggestions.troubleshooting_steps.map((step: any, idx: number) => (
                          <ListItem key={idx} sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 1 }}>
                            <Typography variant="body2" fontWeight="medium">
                              Step {step.step}: {step.action}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Expected: {step.expected_result}
                            </Typography>
                            {step.if_fails && (
                              <Typography variant="caption" color="warning.main">
                                If fails: {step.if_fails}
                              </Typography>
                            )}
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </Box>
        )}

        <Stack direction="row" spacing={2} sx={{ mt: 2, flexWrap: 'wrap' }}>
          {npa?.due_date && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <ScheduleIcon fontSize="small" color={isOverdue ? 'error' : 'action'} />
              <Typography variant="caption" color={isOverdue ? 'error' : 'text.secondary'}>
                Due: {new Date(npa.due_date).toLocaleString()}
              </Typography>
              {npa?.npa_date_override && (
                <Chip label="Manual" size="small" variant="outlined" sx={{ ml: 0.5 }} />
              )}
            </Box>
          )}
          {npa?.assigned_to && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <PersonIcon fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                Assigned to: {npa.assigned_to}
              </Typography>
            </Box>
          )}
        </Stack>

        {isOverdue && (
          <Alert severity="error" sx={{ mt: 2 }}>
            This Next Point of Action is overdue. Please update it or complete the action.
          </Alert>
        )}

        {isWaiting && (
          <Alert 
            severity="info" 
            sx={{ mt: 2 }} 
            icon={<PauseIcon />}
            action={
              <Button 
                size="small" 
                onClick={() => {
                  setEditNpaState('investigation');
                  setEditNpaOriginal(npa?.npa_original_text || npa?.npa || 'Continue investigation');
                  setEditNpaCleaned(npa?.npa_cleaned_text || npa?.npa || 'Continuing investigation');
                  setEditExcludeFromSla(false);
                  setEditDialogOpen(true);
                }}
              >
                Resume SLA
              </Button>
            }
          >
            <Typography variant="body2">
              <strong>SLA Paused:</strong> This NPA is in a waiting state and is excluded from SLA calculations. 
              Click "Resume SLA" when you're ready to continue work.
            </Typography>
          </Alert>
        )}
        
        {npa?.npa_state === 'solution' && (
          <Alert 
            severity="success" 
            sx={{ mt: 2 }} 
            icon={<CheckCircleIcon />}
            action={
              <Button 
                size="small" 
                variant="contained"
                startIcon={<NavigateNextIcon />}
                onClick={() => {
                  setEditNpaState('implementation');
                  setEditNpaOriginal('Implement the solution');
                  setEditNpaCleaned('We are now implementing the solution.');
                  setEditExcludeFromSla(false);
                  setEditDialogOpen(true);
                }}
              >
                Move to Implementation
              </Button>
            }
          >
            <Typography variant="body2">
              <strong>Solution Found:</strong> Ready to implement. Click "Move to Implementation" to proceed.
            </Typography>
          </Alert>
        )}
      </Paper>

      {/* NPA History Section - Only show if showHistory prop is true */}
      {showHistory && (npaHistory.length > 0 || loadingHistory) && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ArticleIcon />
            <Typography variant="h6">NPA History (Call History)</Typography>
            {loadingHistory && <CircularProgress size={20} />}
          </Box>
          
          {npaHistory.length === 0 && !loadingHistory ? (
            <Typography variant="body2" color="text.secondary">
              No NPA history available yet.
            </Typography>
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
                        label={NPA_STATES.find(s => s.value === entry.npa_state)?.label || entry.npa_state}
                        color={getStateColor(entry.npa_state) as any}
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
                    
                    {/* Answers to Questions - Two Column Layout */}
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Typography variant="subtitle2">
                        Answers to Questions in this NPA:
                      </Typography>
                      {answersCleanupStatus[entry.id] === 'processing' && (
                        <>
                          <CircularProgress size={16} />
                          <Chip label="AI Cleaning..." size="small" color="info" />
                        </>
                      )}
                      {answersCleanupStatus[entry.id] === 'completed' && (
                        <Chip label="AI Cleaned" size="small" color="success" />
                      )}
                      {answersCleanupStatus[entry.id] === 'failed' && (
                        <Chip label="AI Cleanup Failed" size="small" color="error" />
                      )}
                    </Box>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <TextField
                          fullWidth
                          multiline
                          rows={4}
                          label="Original Answers (As Typed)"
                          value={answers[entry.id] || ''}
                          onChange={(e) => setAnswers(prev => ({ ...prev, [entry.id]: e.target.value }))}
                          placeholder="Enter answers to questions asked in this NPA..."
                        />
                      </Grid>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <TextField
                          fullWidth
                          multiline
                          rows={4}
                          label="AI-Cleaned Answers (Customer-Facing)"
                          value={answersCleaned[entry.id] || ''}
                          onChange={(e) => setAnswersCleaned(prev => ({ ...prev, [entry.id]: e.target.value }))}
                          placeholder="AI-cleaned professional version will appear here..."
                          disabled={answersCleanupStatus[entry.id] === 'processing'}
                          sx={{
                            '& .MuiInputBase-input:disabled': {
                              backgroundColor: 'action.disabledBackground'
                            }
                          }}
                        />
                        {answersCleanupStatus[entry.id] === 'processing' && (
                          <LinearProgress sx={{ mt: 1 }} />
                        )}
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleSaveAnswers(entry.id, answers[entry.id] || '', true)}
                        disabled={savingAnswers[entry.id] || answersCleanupStatus[entry.id] === 'processing'}
                        startIcon={savingAnswers[entry.id] ? <CircularProgress size={16} /> : <DoneIcon />}
                      >
                        {savingAnswers[entry.id] ? 'Saving...' : 'Save & Clean with AI'}
                      </Button>
                      {answersCleaned[entry.id] && (
                        <Button
                          size="small"
                          variant="text"
                          onClick={() => {
                            setAnswers(prev => ({ ...prev, [entry.id]: answersCleaned[entry.id] }));
                          }}
                        >
                          Use Cleaned Version
                        </Button>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* Answers to Questions for Current NPA - Two Column Layout */}
      {npa && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ArticleIcon />
            <Typography variant="subtitle1">
              Answers to Questions in Current NPA
            </Typography>
            {answersCleanupStatus['current'] === 'processing' && (
              <>
                <CircularProgress size={16} />
                <Chip label="AI Cleaning..." size="small" color="info" />
              </>
            )}
            {answersCleanupStatus['current'] === 'completed' && (
              <Chip label="AI Cleaned" size="small" color="success" />
            )}
            {answersCleanupStatus['current'] === 'failed' && (
              <Chip label="AI Cleanup Failed" size="small" color="error" />
            )}
          </Box>
          
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Original Answers (As Typed)"
                value={answers['current'] || ''}
                onChange={(e) => setAnswers(prev => ({ ...prev, current: e.target.value }))}
                placeholder="Enter answers to questions asked in the current NPA..."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="AI-Cleaned Answers (Customer-Facing)"
                value={answersCleaned['current'] || ''}
                onChange={(e) => setAnswersCleaned(prev => ({ ...prev, current: e.target.value }))}
                placeholder="AI-cleaned professional version will appear here..."
                disabled={answersCleanupStatus['current'] === 'processing'}
                sx={{
                  '& .MuiInputBase-input:disabled': {
                    backgroundColor: 'action.disabledBackground'
                  }
                }}
              />
              {answersCleanupStatus['current'] === 'processing' && (
                <LinearProgress sx={{ mt: 1 }} />
              )}
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() => handleSaveAnswers('current', answers['current'] || '', true)}
              disabled={savingAnswers['current'] || answersCleanupStatus['current'] === 'processing'}
              startIcon={savingAnswers['current'] ? <CircularProgress size={16} /> : <DoneIcon />}
            >
              {savingAnswers['current'] ? 'Saving...' : 'Save & Clean with AI'}
            </Button>
            {answersCleaned['current'] && (
              <Button
                size="small"
                variant="text"
                onClick={() => {
                  // Copy cleaned to original if user wants to use cleaned version
                  setAnswers(prev => ({ ...prev, current: answersCleaned['current'] }));
                }}
              >
                Use Cleaned Version
              </Button>
            )}
          </Box>
        </Paper>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Edit Next Point of Action</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={12}>
              <FormControl fullWidth>
                <InputLabel>NPA State</InputLabel>
                <Select
                  value={editNpaState}
                  label="NPA State"
                  onChange={(e) => setEditNpaState(e.target.value)}
                >
                  {NPA_STATES.map((state) => (
                    <MenuItem key={state.value} value={state.value}>
                      {state.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Original Text (As Typed)"
                value={editNpaOriginal}
                onChange={(e) => setEditNpaOriginal(e.target.value)}
                required
                helperText="This is what you type - it will be stored for reference"
                sx={{ mb: 2 }}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Cleaned Text (Customer-Facing)"
                value={editNpaCleaned}
                onChange={(e) => setEditNpaCleaned(e.target.value)}
                helperText="AI-cleaned professional version (or edit manually)"
                sx={{ mb: 2 }}
              />
            </Grid>

            <Grid size={12}>
              <Divider sx={{ my: 1 }} />
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="Due Date"
                  value={editDueDate}
                  onChange={(newValue) => setEditDueDate(newValue)}
                  slotProps={{
                    textField: {
                      fullWidth: true
                    }
                  }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Assign To</InputLabel>
                <Select
                  value={editAssignedTo}
                  onChange={(e) => setEditAssignedTo(e.target.value)}
                  label="Assign To"
                >
                  <MenuItem value="">Unassigned</MenuItem>
                  {/* TODO: Load users from API */}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={editDateOverride}
                    onChange={(e) => setEditDateOverride(e.target.checked)}
                  />
                }
                label="Manually Override Due Date (prevents auto-calculation)"
              />
            </Grid>

            <Grid size={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={editExcludeFromSla}
                    onChange={(e) => setEditExcludeFromSla(e.target.checked)}
                  />
                }
                label="Exclude from SLA Calculations (e.g., waiting for customer/vendor/parts)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit} disabled={!editNpaOriginal.trim()}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TicketNPA;
