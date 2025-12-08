import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  Paper,
  Grid
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { helpdeskAPI } from '../services/api';

interface Pattern {
  pattern_name: string;
  description: string;
  ticket_ids: string[];
  common_themes: string[];
  frequency: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface SimilarTicket {
  ticket_id: string;
  similar_ticket_id: string;
  similarity_score: number;
  reason: string;
}

interface PatternAnalysisResult {
  patterns: Pattern[];
  similar_tickets: SimilarTicket[];
  total_tickets_analyzed?: number;
  message?: string;
}

interface CustomerPatternAnalysisProps {
  open: boolean;
  onClose: () => void;
  customerId: string;
  customerName?: string;
}

const CustomerPatternAnalysis: React.FC<CustomerPatternAnalysisProps> = ({
  open,
  onClose,
  customerId,
  customerName
}) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<PatternAnalysisResult | null>(null);
  const [limit, setLimit] = useState(50);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError(null);
      setResults(null);
      
      const response = await helpdeskAPI.detectCustomerPatterns(customerId, limit, 3);
      setResults(response.data);
    } catch (err: any) {
      console.error('Error analyzing patterns:', err);
      setError(err.response?.data?.detail || 'Error analyzing ticket patterns');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
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

  const handleTicketClick = (ticketId: string) => {
    navigate(`/helpdesk/${ticketId}`);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            Ticket Pattern Analysis
            {customerName && (
              <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                for {customerName}
              </Typography>
            )}
          </Typography>
          <Button
            variant="outlined"
            onClick={handleAnalyze}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <TrendingUpIcon />}
          >
            {results ? 'Re-analyze' : 'Analyze Patterns'}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {!results && !loading && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              Click "Analyze Patterns" to identify recurring issues and similar tickets for this customer.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              This will analyze up to {limit} recent tickets to find patterns, common themes, and potential duplicates.
            </Typography>
          </Box>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Analyzing ticket patterns...
            </Typography>
          </Box>
        )}

        {results && (
          <Box>
            {results.message && (
              <Alert severity="info" sx={{ mb: 2 }}>
                {results.message}
              </Alert>
            )}

            {results.total_tickets_analyzed && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Analyzed {results.total_tickets_analyzed} tickets
              </Typography>
            )}

            {/* Patterns Section */}
            {results.patterns && results.patterns.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningIcon color="primary" />
                  Recurring Patterns ({results.patterns.length})
                </Typography>
                {results.patterns.map((pattern, index) => (
                  <Accordion key={index} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                        <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                          {pattern.pattern_name}
                        </Typography>
                        <Chip
                          label={pattern.severity}
                          size="small"
                          color={getSeverityColor(pattern.severity) as any}
                        />
                        <Chip
                          label={`${pattern.frequency} tickets`}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {pattern.description}
                      </Typography>
                      
                      {pattern.common_themes && pattern.common_themes.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Common Themes:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {pattern.common_themes.map((theme, idx) => (
                              <Chip key={idx} label={theme} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </Box>
                      )}

                      {pattern.ticket_ids && pattern.ticket_ids.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Related Tickets ({pattern.ticket_ids.length}):
                          </Typography>
                          <List dense>
                            {pattern.ticket_ids.map((ticketId, idx) => (
                              <ListItem
                                key={idx}
                                button
                                onClick={() => handleTicketClick(ticketId)}
                                sx={{ borderRadius: 1, mb: 0.5 }}
                              >
                                <ListItemText
                                  primary={`Ticket ${ticketId.substring(0, 8)}...`}
                                  secondary={`Click to view ticket details`}
                                />
                                <LinkIcon fontSize="small" sx={{ ml: 1 }} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            )}

            {/* Similar Tickets Section */}
            {results.similar_tickets && results.similar_tickets.length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinkIcon color="primary" />
                  Similar Tickets ({results.similar_tickets.length})
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <List>
                    {results.similar_tickets.map((similar, index) => (
                      <React.Fragment key={index}>
                        <ListItem>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Button
                                  size="small"
                                  onClick={() => handleTicketClick(similar.ticket_id)}
                                  sx={{ textTransform: 'none' }}
                                >
                                  Ticket {similar.ticket_id.substring(0, 8)}...
                                </Button>
                                <Typography component="span" variant="body2">
                                  is similar to
                                </Typography>
                                <Button
                                  size="small"
                                  onClick={() => handleTicketClick(similar.similar_ticket_id)}
                                  sx={{ textTransform: 'none' }}
                                >
                                  Ticket {similar.similar_ticket_id.substring(0, 8)}...
                                </Button>
                                <Chip
                                  label={`${(similar.similarity_score * 100).toFixed(0)}% similar`}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={similar.reason || 'These tickets appear to be related'}
                          />
                        </ListItem>
                        {index < results.similar_tickets.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Paper>
              </Box>
            )}

            {results.patterns && results.patterns.length === 0 && 
             results.similar_tickets && results.similar_tickets.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No patterns or similar tickets found. This could indicate:
                <ul style={{ marginTop: 8, marginBottom: 0 }}>
                  <li>Issues are unique and not recurring</li>
                  <li>Not enough tickets to identify patterns</li>
                  <li>Customer has diverse support needs</li>
                </ul>
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default CustomerPatternAnalysis;

