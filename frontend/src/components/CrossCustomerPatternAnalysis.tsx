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
  Grid,
  TextField
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { helpdeskAPI } from '../services/api';

interface CrossCustomerPattern {
  pattern_name: string;
  description: string;
  customer_ids: string[];
  ticket_count: number;
  common_themes: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface CrossCustomerPatternResult {
  patterns: CrossCustomerPattern[];
  total_tickets_analyzed?: number;
  total_customers_analyzed?: number;
  message?: string;
}

interface CrossCustomerPatternAnalysisProps {
  open: boolean;
  onClose: () => void;
}

const CrossCustomerPatternAnalysis: React.FC<CrossCustomerPatternAnalysisProps> = ({
  open,
  onClose
}) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CrossCustomerPatternResult | null>(null);
  const [limitPerCustomer, setLimitPerCustomer] = useState(20);
  const [minTicketsPerPattern, setMinTicketsPerPattern] = useState(3);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError(null);
      setResults(null);
      
      const response = await helpdeskAPI.detectCrossCustomerPatterns(
        limitPerCustomer,
        minTicketsPerPattern
      );
      setResults(response.data);
    } catch (err: any) {
      console.error('Error analyzing cross-customer patterns:', err);
      setError(err.response?.data?.detail || 'Error analyzing cross-customer patterns');
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

  const handleCustomerClick = (customerId: string) => {
    navigate(`/customers/${customerId}`);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PeopleIcon color="primary" />
            Cross-Customer Pattern Analysis
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
          <Box>
            <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
              Analyze tickets across all customers to identify widespread issues and systemic problems.
            </Typography>
            
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Analysis Parameters
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    label="Tickets per Customer"
                    type="number"
                    value={limitPerCustomer}
                    onChange={(e) => setLimitPerCustomer(parseInt(e.target.value) || 20)}
                    inputProps={{ min: 1, max: 100 }}
                    fullWidth
                    size="small"
                    helperText="Maximum tickets to analyze per customer"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    label="Minimum Tickets per Pattern"
                    type="number"
                    value={minTicketsPerPattern}
                    onChange={(e) => setMinTicketsPerPattern(parseInt(e.target.value) || 3)}
                    inputProps={{ min: 1, max: 50 }}
                    fullWidth
                    size="small"
                    helperText="Minimum tickets required to form a pattern"
                  />
                </Grid>
              </Grid>
            </Paper>

            <Alert severity="info">
              <Typography variant="body2" component="div">
                This analysis will:
                <ul style={{ marginTop: 8, marginBottom: 0 }}>
                  <li>Examine tickets from all customers</li>
                  <li>Identify patterns affecting multiple customers</li>
                  <li>Highlight systemic issues that may need attention</li>
                  <li>Help prioritize widespread problems</li>
                </ul>
              </Typography>
            </Alert>
          </Box>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Analyzing cross-customer patterns...
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

            {(results.total_tickets_analyzed || results.total_customers_analyzed) && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Grid container spacing={2}>
                  {results.total_tickets_analyzed && (
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="body2" color="text.secondary">
                        Tickets Analyzed
                      </Typography>
                      <Typography variant="h6">
                        {results.total_tickets_analyzed}
                      </Typography>
                    </Grid>
                  )}
                  {results.total_customers_analyzed && (
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="body2" color="text.secondary">
                        Customers Analyzed
                      </Typography>
                      <Typography variant="h6">
                        {results.total_customers_analyzed}
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            )}

            {/* Patterns Section */}
            {results.patterns && results.patterns.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningIcon color="primary" />
                  Widespread Patterns ({results.patterns.length})
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  These patterns affect multiple customers and may indicate systemic issues.
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
                          label={`${pattern.ticket_count} tickets`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${pattern.customer_ids.length} customers`}
                          size="small"
                          variant="outlined"
                          color="primary"
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

                      {pattern.customer_ids && pattern.customer_ids.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Affected Customers ({pattern.customer_ids.length}):
                          </Typography>
                          <List dense>
                            {pattern.customer_ids.map((customerId, idx) => (
                              <ListItem
                                key={idx}
                                button
                                onClick={() => handleCustomerClick(customerId)}
                                sx={{ borderRadius: 1, mb: 0.5 }}
                              >
                                <ListItemText
                                  primary={`Customer ${customerId.substring(0, 8)}...`}
                                  secondary={`Click to view customer details`}
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

            {results.patterns && results.patterns.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography component="div" variant="body2">
                  No widespread patterns found. This could indicate:
                  <ul style={{ marginTop: 8, marginBottom: 0 }}>
                    <li>Issues are customer-specific rather than systemic</li>
                    <li>Not enough tickets meet the minimum threshold</li>
                    <li>Try adjusting the analysis parameters</li>
                  </ul>
                </Typography>
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

export default CrossCustomerPatternAnalysis;

