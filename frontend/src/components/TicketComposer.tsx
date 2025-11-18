import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Grid,
  Paper,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Divider,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  LinearProgress,
  Fade,
  Zoom
} from '@mui/material';
import {
  Close as CloseIcon,
  AutoAwesome as SparkleIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  ArrowForward as ArrowForwardIcon,
  Lightbulb as LightbulbIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Build as BuildIcon,
  Send as SendIcon,
  CompareArrows as CompareIcon
} from '@mui/icons-material';
import { helpdeskAPI, customerAPI } from '../services/api';
// Using a simple diff view instead of Monaco Editor for better compatibility

interface TicketComposerProps {
  open: boolean;
  onClose: () => void;
  onSave: (ticket: any) => void;
  initialCustomerId?: string;
}

interface AIAnalysis {
  improved_description?: string;
  suggestions?: {
    next_actions?: string[];
    questions?: string[];
    solutions?: string[];
  };
  ticket_type_suggestion?: string;
  priority_suggestion?: string;
  sla_risk?: string;
  confidence?: number;
}

const TicketComposer: React.FC<TicketComposerProps> = ({
  open,
  onClose,
  onSave,
  initialCustomerId
}) => {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [originalDescription, setOriginalDescription] = useState('');
  const [improvedDescription, setImprovedDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [ticketType, setTicketType] = useState('support');
  const [customerId, setCustomerId] = useState(initialCustomerId || '');
  const [customers, setCustomers] = useState<any[]>([]);
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  
  // AI State
  const [analyzing, setAnalyzing] = useState(false);
  const [improving, setImproving] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [acceptedImprovement, setAcceptedImprovement] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftTicketId, setDraftTicketId] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      loadCustomers();
      // Reset form
      setSubject('');
      setDescription('');
      setOriginalDescription('');
      setImprovedDescription('');
      setAiAnalysis(null);
      setShowDiff(false);
      setAcceptedImprovement(false);
      setError(null);
      setDraftTicketId(null);
    }
  }, [open]);

  // Removed auto-improve - user must click analyze button

  const loadCustomers = async () => {
    try {
      setLoadingCustomers(true);
      const response = await customerAPI.list();
      setCustomers(response.data || []);
    } catch (err) {
      console.error('Error loading customers:', err);
    } finally {
      setLoadingCustomers(false);
    }
  };

  const handleAnalyze = async () => {
    if (!description || description.length < 20) {
      setError('Please enter a description (at least 20 characters)');
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);
      
      // Create a draft ticket for analysis
      const tempTicket = {
        subject: subject || 'Draft - Analyzing...',
        description,
        priority,
        ticket_type: ticketType,
        customer_id: customerId || undefined
      };
      
      const response = await helpdeskAPI.createTicket(tempTicket);
      const ticketId = response.data.id;
      setDraftTicketId(ticketId);
      
      // Analyze the draft ticket
      const aiResponse = await helpdeskAPI.analyzeTicketWithAI(ticketId);
      const analysis = aiResponse.data;
      
      setAiAnalysis(analysis);
      
      if (analysis.improved_description) {
        setOriginalDescription(description);
        setImprovedDescription(analysis.improved_description);
        setShowDiff(true);
      }
      
    } catch (err: any) {
      console.error('Error analyzing ticket:', err);
      setError(err.response?.data?.detail || 'Failed to analyze ticket');
      // Clean up draft ticket if analysis fails
      if (draftTicketId) {
        try {
          await helpdeskAPI.updateTicket(draftTicketId, { is_deleted: true });
        } catch (cleanupErr) {
          console.error('Failed to cleanup draft ticket:', cleanupErr);
        }
        setDraftTicketId(null);
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAcceptImprovement = () => {
    setDescription(improvedDescription);
    setAcceptedImprovement(true);
    setShowDiff(false);
  };

  const handleRejectImprovement = () => {
    setImprovedDescription('');
    setShowDiff(false);
  };

  const handleSave = async () => {
    try {
      const finalDescription = acceptedImprovement ? improvedDescription : description;
      
      if (draftTicketId) {
        // Update the draft ticket with final data
        const response = await helpdeskAPI.updateTicket(draftTicketId, {
          subject,
          description: finalDescription,
          priority,
          ticket_type: ticketType,
          customer_id: customerId || undefined
        });
        onSave(response.data);
      } else {
        // Create new ticket
        const ticketData = {
          subject,
          description: finalDescription,
          priority,
          ticket_type: ticketType,
          customer_id: customerId || undefined
        };
        
        const response = await helpdeskAPI.createTicket(ticketData);
        onSave(response.data);
      }
      
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create ticket');
    }
  };

  const handleClose = () => {
    // Clean up draft ticket if user cancels
    if (draftTicketId) {
      helpdeskAPI.updateTicket(draftTicketId, { is_deleted: true }).catch(console.error);
    }
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SparkleIcon color="primary" />
            Create Ticket with AI Assistance
          </Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Customer</InputLabel>
              <Select
                value={customerId}
                label="Customer"
                onChange={(e) => setCustomerId(e.target.value)}
                disabled={loadingCustomers}
              >
                <MenuItem value="">None</MenuItem>
                {customers.map((customer) => (
                  <MenuItem key={customer.id} value={customer.id}>
                    {customer.company_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={priority}
                label="Priority"
                onChange={(e) => setPriority(e.target.value)}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={ticketType}
                label="Type"
                onChange={(e) => setTicketType(e.target.value)}
              >
                <MenuItem value="support">Support</MenuItem>
                <MenuItem value="bug">Bug</MenuItem>
                <MenuItem value="feature">Feature Request</MenuItem>
                <MenuItem value="question">Question</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <TextField
          fullWidth
          label="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          sx={{ mb: 2 }}
          required
        />

        {!showDiff ? (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Description
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {improving && (
                  <Chip
                    icon={<CircularProgress size={16} />}
                    label="AI Improving..."
                    size="small"
                    color="primary"
                  />
                )}
                <Tooltip title="Analyze with AI">
                  <IconButton
                    size="small"
                    onClick={handleAnalyze}
                    disabled={analyzing || !description || description.length < 20}
                    color="primary"
                  >
                    <SparkleIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={12}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the issue... AI will automatically improve your description for clarity and completeness."
              sx={{
                flex: 1,
                '& .MuiInputBase-root': {
                  height: '100%',
                  alignItems: 'flex-start'
                }
              }}
              required
            />
          </Box>
        ) : (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Compare Original vs AI-Improved Description
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  startIcon={<CheckCircleIcon />}
                  onClick={handleAcceptImprovement}
                  variant="contained"
                  color="success"
                >
                  Accept
                </Button>
                <Button
                  size="small"
                  onClick={handleRejectImprovement}
                  variant="outlined"
                >
                  Reject
                </Button>
              </Box>
            </Box>
            <Grid container spacing={2} sx={{ flex: 1, minHeight: 0 }}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%', bgcolor: 'error.50', border: '1px solid', borderColor: 'error.200' }}>
                  <Typography variant="subtitle2" color="error.main" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CloseIcon fontSize="small" />
                    Original
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={15}
                    value={originalDescription}
                    InputProps={{ readOnly: true }}
                    sx={{
                      '& .MuiInputBase-root': {
                        bgcolor: 'background.paper',
                        fontSize: '0.875rem',
                        fontFamily: 'monospace'
                      }
                    }}
                  />
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%', bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                  <Typography variant="subtitle2" color="success.main" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircleIcon fontSize="small" />
                    AI-Improved
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={15}
                    value={improvedDescription}
                    InputProps={{ readOnly: true }}
                    sx={{
                      '& .MuiInputBase-root': {
                        bgcolor: 'background.paper',
                        fontSize: '0.875rem',
                        fontFamily: 'monospace'
                      }
                    }}
                  />
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}

        {aiAnalysis && (
          <Fade in={!!aiAnalysis}>
            <Card sx={{ mt: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LightbulbIcon color="primary" />
                  AI Suggestions
                </Typography>
                
                {aiAnalysis.suggestions?.next_actions && aiAnalysis.suggestions.next_actions.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Next Actions
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                      {aiAnalysis.suggestions.next_actions.map((action, idx) => (
                        <Chip
                          key={idx}
                          label={action}
                          icon={<ArrowForwardIcon />}
                          color="primary"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Stack>
                  </Box>
                )}

                {aiAnalysis.suggestions?.questions && aiAnalysis.suggestions.questions.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Clarification Questions
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                      {aiAnalysis.suggestions.questions.map((question, idx) => (
                        <Chip
                          key={idx}
                          label={question}
                          icon={<QuestionAnswerIcon />}
                          color="info"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Stack>
                  </Box>
                )}

                {aiAnalysis.suggestions?.solutions && aiAnalysis.suggestions.solutions.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Potential Solutions
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                      {aiAnalysis.suggestions.solutions.map((solution, idx) => (
                        <Chip
                          key={idx}
                          label={solution}
                          icon={<BuildIcon />}
                          color="success"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Stack>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Fade>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button onClick={handleClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={<SendIcon />}
          disabled={!subject || !description}
        >
          Create Ticket
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TicketComposer;

