import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  AutoAwesome as SparkleIcon,
  Lightbulb as LightbulbIcon,
  TrendingUp as TrendingUpIcon,
  Email as EmailIcon,
  QuestionAnswer as QuestionAnswerIcon,
  ShoppingCart as ShoppingCartIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  ContentCopy as CopyIcon,
  Send as SendIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { quoteAICopilotAPI } from '../services/api';

interface QuoteAICopilotProps {
  quoteId: string;
  compact?: boolean;
}

interface ScopeAnalysis {
  summary?: string;
  gaps?: string[];
  clarification_questions?: string[];
}

interface UpsellSuggestion {
  product_name: string;
  description: string;
  estimated_value?: number;
  reason: string;
}

interface EmailCopy {
  subject: string;
  body: string;
}

const QuoteAICopilot: React.FC<QuoteAICopilotProps> = ({
  quoteId,
  compact = false
}) => {
  const [scopeAnalysis, setScopeAnalysis] = useState<ScopeAnalysis | null>(null);
  const [upsells, setUpsells] = useState<UpsellSuggestion[]>([]);
  const [crossSells, setCrossSells] = useState<UpsellSuggestion[]>([]);
  const [emailCopy, setEmailCopy] = useState<EmailCopy | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'scope' | 'upsells' | 'email'>('scope');
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [emailType, setEmailType] = useState('send_quote');

  const loadScopeAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await quoteAICopilotAPI.analyzeScope(quoteId);
      setScopeAnalysis(response.data);
    } catch (err: any) {
      console.error('Error loading scope analysis:', err);
      setError(err.response?.data?.detail || 'Failed to load scope analysis');
    } finally {
      setLoading(false);
    }
  };

  const loadUpsells = async () => {
    try {
      setLoading(true);
      setError(null);
      const upsellsResponse = await quoteAICopilotAPI.getUpsells(quoteId);
      const crossSellsResponse = await quoteAICopilotAPI.getCrossSells(quoteId);
      setUpsells(upsellsResponse.data.upsells || []);
      setCrossSells(crossSellsResponse.data.cross_sells || []);
    } catch (err: any) {
      console.error('Error loading upsells:', err);
      setError(err.response?.data?.detail || 'Failed to load upsells');
    } finally {
      setLoading(false);
    }
  };

  const generateEmailCopy = async (type: string = 'send_quote') => {
    try {
      setLoading(true);
      setError(null);
      const response = await quoteAICopilotAPI.generateEmailCopy(quoteId, type);
      setEmailCopy(response.data);
      setEmailDialogOpen(true);
    } catch (err: any) {
      console.error('Error generating email copy:', err);
      setError(err.response?.data?.detail || 'Failed to generate email copy');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (quoteId && activeTab === 'scope') {
      loadScopeAnalysis();
    } else if (quoteId && activeTab === 'upsells') {
      loadUpsells();
    }
  }, [quoteId, activeTab]);

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: '2px solid',
        borderColor: 'primary.main'
      }}
    >
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SparkleIcon sx={{ fontSize: 32 }} />
            <Typography variant="h6" component="div" fontWeight="bold">
              AI Quote Copilot
            </Typography>
          </Box>
          <Tooltip title="Refresh">
            <IconButton
              size="small"
              onClick={() => {
                if (activeTab === 'scope') loadScopeAnalysis();
                else if (activeTab === 'upsells') loadUpsells();
              }}
              disabled={loading}
              sx={{ color: 'white' }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Tabs */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Button
            variant={activeTab === 'scope' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<AssessmentIcon />}
            onClick={() => setActiveTab('scope')}
            sx={{
              bgcolor: activeTab === 'scope' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Scope
          </Button>
          <Button
            variant={activeTab === 'upsells' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<ShoppingCartIcon />}
            onClick={() => setActiveTab('upsells')}
            sx={{
              bgcolor: activeTab === 'upsells' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Upsells
          </Button>
          <Button
            variant={activeTab === 'email' ? 'contained' : 'outlined'}
            size="small"
            startIcon={<EmailIcon />}
            onClick={() => {
              setActiveTab('email');
              generateEmailCopy('send_quote');
            }}
            sx={{
              bgcolor: activeTab === 'email' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              borderColor: 'white',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderColor: 'white'
              }
            }}
          >
            Email Copy
          </Button>
        </Box>

        <Divider sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.3)' }} />

        {/* Content */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress sx={{ color: 'white' }} />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.9)', color: 'error.main' }}>
            {error}
          </Alert>
        )}

        {!loading && !error && (
          <>
            {/* Scope Analysis */}
            {activeTab === 'scope' && scopeAnalysis && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {scopeAnalysis.summary && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(255,255,255,0.1)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AssessmentIcon /> Summary
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'white', whiteSpace: 'pre-wrap' }}>
                      {scopeAnalysis.summary}
                    </Typography>
                  </Paper>
                )}

                {scopeAnalysis.gaps && scopeAnalysis.gaps.length > 0 && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(255,193,7,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WarningIcon /> Potential Gaps
                    </Typography>
                    <List dense>
                      {scopeAnalysis.gaps.map((gap, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <WarningIcon sx={{ color: 'warning.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={gap}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}

                {scopeAnalysis.clarification_questions && scopeAnalysis.clarification_questions.length > 0 && (
                  <Paper sx={{ p: 2, bgcolor: 'rgba(33,150,243,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <QuestionAnswerIcon /> Clarification Questions
                    </Typography>
                    <List dense>
                      {scopeAnalysis.clarification_questions.map((question, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <QuestionAnswerIcon sx={{ color: 'info.main', fontSize: 20 }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={question}
                            primaryTypographyProps={{ variant: 'body2', sx: { color: 'white' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}
              </Box>
            )}

            {/* Upsells & Cross-sells */}
            {activeTab === 'upsells' && (upsells.length > 0 || crossSells.length > 0) && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {upsells.length > 0 && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(76,175,80,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TrendingUpIcon /> Upsell Opportunities
                    </Typography>
                    <List dense>
                      {upsells.map((upsell, idx) => (
                        <ListItem key={idx} sx={{ px: 0, flexDirection: 'column', alignItems: 'flex-start' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 0.5 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'white' }}>
                              {upsell.product_name}
                            </Typography>
                            {upsell.estimated_value && (
                              <Chip
                                label={`£${upsell.estimated_value.toLocaleString()}`}
                                size="small"
                                sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white' }}
                              />
                            )}
                          </Box>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)', mb: 0.5 }}>
                            {upsell.description}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontStyle: 'italic' }}>
                            {upsell.reason}
                          </Typography>
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}

                {crossSells.length > 0 && (
                  <Paper sx={{ p: 2, bgcolor: 'rgba(156,39,176,0.2)' }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ShoppingCartIcon /> Cross-sell Opportunities
                    </Typography>
                    <List dense>
                      {crossSells.map((crossSell, idx) => (
                        <ListItem key={idx} sx={{ px: 0, flexDirection: 'column', alignItems: 'flex-start' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 0.5 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'white' }}>
                              {crossSell.product_name}
                            </Typography>
                            {crossSell.estimated_value && (
                              <Chip
                                label={`£${crossSell.estimated_value.toLocaleString()}`}
                                size="small"
                                sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white' }}
                              />
                            )}
                          </Box>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)', mb: 0.5 }}>
                            {crossSell.description}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontStyle: 'italic' }}>
                            {crossSell.reason}
                          </Typography>
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}

                {upsells.length === 0 && crossSells.length === 0 && (
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center', py: 4 }}>
                    No upsell or cross-sell opportunities identified at this time.
                  </Typography>
                )}
              </Box>
            )}

            {/* Email Copy */}
            {activeTab === 'email' && emailCopy && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                <Paper sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.1)' }}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EmailIcon /> Email Copy
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>Subject:</Typography>
                    <Typography variant="body2" sx={{ color: 'white', fontWeight: 'bold', mb: 1 }}>
                      {emailCopy.subject}
                    </Typography>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => navigator.clipboard.writeText(emailCopy.subject)}
                      sx={{ color: 'white', borderColor: 'white', mb: 2 }}
                      variant="outlined"
                    >
                      Copy Subject
                    </Button>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>Body:</Typography>
                    <Typography variant="body2" sx={{ color: 'white', whiteSpace: 'pre-wrap', mb: 1 }}>
                      {emailCopy.body}
                    </Typography>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => navigator.clipboard.writeText(emailCopy.body)}
                      sx={{ color: 'white', borderColor: 'white' }}
                      variant="outlined"
                    >
                      Copy Body
                    </Button>
                  </Box>
                </Paper>
              </Box>
            )}
          </>
        )}
      </CardContent>

      {/* Email Copy Dialog */}
      <Dialog
        open={emailDialogOpen}
        onClose={() => setEmailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EmailIcon color="primary" />
            AI-Generated Email Copy
          </Box>
        </DialogTitle>
        <DialogContent>
          {emailCopy && (
            <Box>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Email Type</InputLabel>
                <Select
                  value={emailType}
                  label="Email Type"
                  onChange={(e) => {
                    setEmailType(e.target.value);
                    generateEmailCopy(e.target.value);
                  }}
                >
                  <MenuItem value="send_quote">Send Quote</MenuItem>
                  <MenuItem value="follow_up">Follow Up</MenuItem>
                  <MenuItem value="negotiation">Negotiation</MenuItem>
                  <MenuItem value="won">Won</MenuItem>
                  <MenuItem value="lost">Lost</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Subject"
                value={emailCopy.subject}
                InputProps={{ readOnly: true }}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                multiline
                rows={12}
                label="Body"
                value={emailCopy.body}
                InputProps={{ readOnly: true }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmailDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<ContentCopy />}
            onClick={() => {
              if (emailCopy) {
                navigator.clipboard.writeText(`${emailCopy.subject}\n\n${emailCopy.body}`);
              }
            }}
          >
            Copy All
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default QuoteAICopilot;

