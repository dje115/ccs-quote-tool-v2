import React, { useEffect, useMemo, useState } from 'react';
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
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Send as SendIcon,
  Work as WorkIcon,
  Link as LinkIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { quoteAPI, opportunityAPI, customerAPI } from '../services/api';
import QuoteAICopilot from '../components/QuoteAICopilot';
import QuoteDocumentViewer from '../components/QuoteDocumentViewer';
import QuoteDocumentEditor from '../components/QuoteDocumentEditor';
import QuotePromptManager from '../components/QuotePromptManager';
import ManualQuoteBuilder from '../components/ManualQuoteBuilder';

const QuoteDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [editingDocument, setEditingDocument] = useState<string | null>(null);
  const [workflowLog, setWorkflowLog] = useState<any[]>([]);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [statusDialog, setStatusDialog] = useState<{ open: boolean; status: string | null; label: string }>({ open: false, status: null, label: '' });
  const [statusComment, setStatusComment] = useState('');
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [linkedOpportunities, setLinkedOpportunities] = useState<any[]>([]);
  const [linkOpportunityDialogOpen, setLinkOpportunityDialogOpen] = useState(false);
  const [availableOpportunities, setAvailableOpportunities] = useState<any[]>([]);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string>('');
  const [linkOpportunityLoading, setLinkOpportunityLoading] = useState(false);
  const [linkOpportunityError, setLinkOpportunityError] = useState<string | null>(null);
  const TAB_INDEX = {
    OVERVIEW: 0,
    LINE_ITEMS: 1,
    PROJECT_DETAILS: 2,
    DOCUMENTS: 3,
    AI_ANALYSIS: 4,
    PRICING: 5,
    ORDERS: 6,
    WORKFLOW: 7,
    AI_PROMPT: 8
  } as const;
  const workflowTabIndex = TAB_INDEX.WORKFLOW;
  const tabLabels = [
    'Overview',
    'Line Items',
    'Project Details',
    'Documents',
    'AI Analysis',
    'Pricing',
    'Orders',
    'Workflow',
    'AI Prompt'
  ];

  useEffect(() => {
    if (id) {
      loadQuote();
      
      // Check URL params for tab and edit document
      const tabParam = searchParams.get('tab');
      const editParam = searchParams.get('edit');
      
      if (tabParam) {
        const normalized = tabParam.toLowerCase();
        const tabMap: Record<string, number> = {
          documents: TAB_INDEX.DOCUMENTS,
          'line-items': TAB_INDEX.LINE_ITEMS,
          workflow: TAB_INDEX.WORKFLOW,
          pricing: TAB_INDEX.PRICING,
          orders: TAB_INDEX.ORDERS,
          'ai-prompt': TAB_INDEX.AI_PROMPT
        };
        if (tabMap[normalized] !== undefined) {
          setCurrentTab(tabMap[normalized]);
        }
      }
      
      if (editParam) {
        setEditingDocument(editParam);
      }
    }
  }, [id, searchParams]);

  const loadQuote = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await quoteAPI.get(id!);
      setQuote(response.data);
      
      // Load linked opportunities if quote has opportunity_ids
      if (response.data.opportunity_ids && Array.isArray(response.data.opportunity_ids) && response.data.opportunity_ids.length > 0) {
        try {
          const oppPromises = response.data.opportunity_ids.map((oppId: string) => 
            opportunityAPI.get(oppId).catch(() => null)
          );
          const oppResults = await Promise.all(oppPromises);
          setLinkedOpportunities(oppResults.filter(r => r !== null).map(r => r.data));
        } catch (err) {
          console.error('Error loading linked opportunities:', err);
        }
      }
    } catch (error: any) {
      console.error('Error loading quote:', error);
      setError(error.response?.data?.detail || 'Failed to load quote');
    } finally {
      setLoading(false);
    }
  };
  
  const loadAvailableOpportunities = async () => {
    if (!quote?.customer_id) return;
    try {
      const response = await opportunityAPI.getCustomerOpportunities(quote.customer_id);
      // Filter out already linked opportunities
      const linkedIds = linkedOpportunities.map(opp => opp.id);
      setAvailableOpportunities((response.data || []).filter((opp: any) => !linkedIds.includes(opp.id)));
    } catch (error) {
      console.error('Error loading available opportunities:', error);
      setAvailableOpportunities([]);
    }
  };
  
  const handleLinkOpportunity = async () => {
    if (!selectedOpportunityId || !id) return;
    setLinkOpportunityLoading(true);
    setLinkOpportunityError(null);
    try {
      await opportunityAPI.attachQuote(selectedOpportunityId, id);
      // Reload quote to get updated opportunity_ids
      await loadQuote();
      setLinkOpportunityDialogOpen(false);
      setSelectedOpportunityId('');
    } catch (error: any) {
      console.error('Error linking opportunity:', error);
      setLinkOpportunityError(error.response?.data?.detail || 'Failed to link opportunity');
    } finally {
      setLinkOpportunityLoading(false);
    }
  };

  const loadWorkflowLog = async () => {
    if (!id) return;
    try {
      setWorkflowLoading(true);
      const response = await quoteAPI.getWorkflowLog(id);
      setWorkflowLog(response.data || []);
    } catch (error) {
      console.error('Error loading workflow log:', error);
    } finally {
      setWorkflowLoading(false);
    }
  };

  useEffect(() => {
    if (currentTab === workflowTabIndex && id) {
      loadWorkflowLog();
    }
  }, [currentTab, id]);

  const normalizedStatus = (quote?.status || 'draft').toLowerCase();

  const statusTimeline = useMemo(() => ['draft', 'sent', 'viewed', 'accepted'], []);
  const currentStepIndex = Math.max(statusTimeline.indexOf(normalizedStatus), 0);

  const statusActions = useMemo(
    () => [
      { label: 'Send Quote', status: 'sent', color: 'primary', description: 'Mark the quote as sent to the customer', visible: normalizedStatus === 'draft' },
      { label: 'Mark Viewed', status: 'viewed', color: 'info', description: 'Track when the customer viewed the proposal', visible: normalizedStatus === 'sent' },
      { label: 'Mark Accepted', status: 'accepted', color: 'success', description: 'Customer has approved the quote', visible: ['sent', 'viewed'].includes(normalizedStatus) },
      { label: 'Mark Rejected', status: 'rejected', color: 'warning', description: 'Customer has declined the quote', visible: ['sent', 'viewed'].includes(normalizedStatus) },
      { label: 'Cancel Quote', status: 'cancelled', color: 'error', description: 'Withdraw this quote from circulation', visible: ['draft', 'sent', 'viewed'].includes(normalizedStatus) }
    ],
    [normalizedStatus]
  );

  const handleTotalsUpdate = (totals: { subtotal: number; tax_rate?: number; tax_amount?: number; total_amount?: number }) => {
    setQuote((prev: any) => {
      if (!prev) return prev;
      return {
        ...prev,
        subtotal: totals.subtotal ?? prev.subtotal,
        tax_rate: totals.tax_rate ?? prev.tax_rate,
        tax_amount: totals.tax_amount ?? prev.tax_amount,
        total_amount: totals.total_amount ?? prev.total_amount
      };
    });
  };

  const openStatusDialog = (status: string, label: string) => {
    setStatusComment('');
    setStatusDialog({ open: true, status, label });
  };

  const closeStatusDialog = () => {
    setStatusDialog({ open: false, status: null, label: '' });
  };

  const handleStatusSubmit = async () => {
    if (!statusDialog.status || !id) return;
    try {
      setStatusUpdating(true);
      const response = await quoteAPI.changeStatus(id, {
        status: statusDialog.status,
        comment: statusComment || undefined,
        action: statusDialog.label
      });
      const data = response.data;
      setQuote((prev: any) => {
        if (!prev) return prev;
        return {
          ...prev,
          status: data.status,
          approval_state: data.approval_state,
          sent_at: data.sent_at,
          accepted_at: data.accepted_at,
          rejected_at: data.rejected_at,
          cancelled_at: data.cancelled_at
        };
      });
      await loadWorkflowLog();
      closeStatusDialog();
    } catch (err: any) {
      console.error('Error changing status:', err);
      alert(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setStatusUpdating(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !quote) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Alert severity="error">{error || 'Quote not found'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/quotes')} sx={{ mt: 2 }}>
          Back to Quotes
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/quotes')}>
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Quote: {quote.quote_number || quote.title}
        </Typography>
        <Chip
          label={quote.status || 'DRAFT'}
          color={quote.status === 'accepted' ? 'success' : quote.status === 'rejected' ? 'error' : 'default'}
          sx={{ ml: 'auto' }}
        />
      </Box>

      <Paper sx={{ p: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)} sx={{ mb: 3 }} variant="scrollable" scrollButtons="auto">
          {tabLabels.map((label) => (
            <Tab key={label} label={label} />
          ))}
        </Tabs>

        {currentTab === TAB_INDEX.OVERVIEW && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Quote Information
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Quote Number" secondary={quote.quote_number || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Title" secondary={quote.title || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Status" secondary={quote.status || 'DRAFT'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Total Amount" secondary={quote.total_amount ? `£${parseFloat(quote.total_amount).toFixed(2)}` : 'N/A'} />
                  </ListItem>
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Dates
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Created" secondary={quote.created_at ? new Date(quote.created_at).toLocaleDateString() : 'N/A'} />
                  </ListItem>
                  {quote.valid_until && (
                    <ListItem>
                      <ListItemText primary="Valid Until" secondary={new Date(quote.valid_until).toLocaleDateString()} />
                    </ListItem>
                  )}
                </List>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            {/* Linked Opportunities Section */}
            {quote.customer_id && (
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WorkIcon /> Linked Opportunities
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<LinkIcon />}
                    onClick={() => {
                      setLinkOpportunityDialogOpen(true);
                      loadAvailableOpportunities();
                    }}
                  >
                    Link to Opportunity
                  </Button>
                </Box>
                {linkedOpportunities.length === 0 ? (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    This quote is not linked to any opportunities. Link it to track it in your sales pipeline.
                  </Alert>
                ) : (
                  <List>
                    {linkedOpportunities.map((opp: any) => (
                      <ListItem
                        key={opp.id}
                        secondaryAction={
                          <IconButton
                            edge="end"
                            onClick={() => navigate(`/opportunities/${opp.id}`)}
                          >
                            <WorkIcon />
                          </IconButton>
                        }
                      >
                        <ListItemText
                          primary={opp.title}
                          secondary={`Stage: ${opp.stage.replace('_', ' ').replace(/\b\w/g, char => char.toUpperCase())} | Probability: ${opp.conversion_probability}% | Value: ${opp.estimated_value ? `£${opp.estimated_value.toLocaleString()}` : 'Not set'}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            )}

            <Divider sx={{ my: 3 }} />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" startIcon={<EditIcon />}>
                Edit Quote
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />}>
                Download PDF
              </Button>
              <Button variant="outlined" startIcon={<SendIcon />}>
                Send Quote
              </Button>
            </Box>
          </Box>
        )}

        {currentTab === TAB_INDEX.LINE_ITEMS && (
          <ManualQuoteBuilder
            quoteId={quote.id}
            initialTaxRate={
              quote.tax_rate !== undefined && quote.tax_rate !== null ? Number(quote.tax_rate) : undefined
            }
            onTotalsChange={handleTotalsUpdate}
          />
        )}

        {currentTab === TAB_INDEX.PROJECT_DETAILS && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Project Details
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              {quote.project_title && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Project Title</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.project_title}</Typography>
                </Grid>
              )}
              {quote.site_address && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Site Address</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.site_address}</Typography>
                </Grid>
              )}
              {quote.building_type && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Building Type</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.building_type}</Typography>
                </Grid>
              )}
              {quote.building_size && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Building Size</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.building_size} sqm</Typography>
                </Grid>
              )}
              {quote.number_of_floors && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Number of Floors</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.number_of_floors}</Typography>
                </Grid>
              )}
              {quote.number_of_rooms && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Number of Rooms</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.number_of_rooms}</Typography>
                </Grid>
              )}
              {quote.description && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Description</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.description}</Typography>
                </Grid>
              )}
            </Grid>
          </Box>
        )}

        {currentTab === TAB_INDEX.DOCUMENTS && (
          <Box>
            {editingDocument ? (
              <QuoteDocumentEditor
                quoteId={quote.id}
                documentType={editingDocument}
                onSave={() => {
                  setEditingDocument(null);
                  loadQuote();
                }}
                onCancel={() => setEditingDocument(null)}
              />
            ) : (
              <QuoteDocumentViewer
                quoteId={quote.id}
                onEdit={(documentType) => setEditingDocument(documentType)}
              />
            )}
          </Box>
        )}

        {currentTab === TAB_INDEX.AI_ANALYSIS && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  AI Analysis
                </Typography>
                {quote.ai_analysis ? (
                  <Card sx={{ mt: 2 }}>
                    <CardContent>
                      <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                        {typeof quote.ai_analysis === 'string' ? quote.ai_analysis : JSON.stringify(quote.ai_analysis, null, 2)}
                      </Typography>
                    </CardContent>
                  </Card>
                ) : (
                  <Alert severity="info" sx={{ mt: 2 }}>No AI analysis available for this quote.</Alert>
                )}
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <QuoteAICopilot quoteId={quote.id} compact={true} />
            </Grid>
          </Grid>
        )}

        {currentTab === TAB_INDEX.PRICING && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Pricing Breakdown
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Subtotal</Typography>
                <Typography variant="h6">£{quote.subtotal ? parseFloat(quote.subtotal).toFixed(2) : '0.00'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Tax ({quote.tax_rate ? (quote.tax_rate * 100).toFixed(0) : 20}%)</Typography>
                <Typography variant="h6">£{quote.tax_amount ? parseFloat(quote.tax_amount).toFixed(2) : '0.00'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2">Total Amount</Typography>
                <Typography variant="h4" color="primary">£{quote.total_amount ? parseFloat(quote.total_amount).toFixed(2) : '0.00'}</Typography>
              </Grid>
            </Grid>
          </Box>
        )}

        {currentTab === TAB_INDEX.ORDERS && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Customer Order & Supplier POs
            </Typography>
            <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h5" fontWeight="bold" gutterBottom>
                Orders dashboard coming soon
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Accepted quotes will soon create draft customer orders, supplier purchase orders, and track fulfilment status here.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                For now, convert accepted quotes manually and keep stakeholders synced via the Workflow tab.
              </Typography>
            </Paper>
          </Box>
        )}

        {currentTab === TAB_INDEX.WORKFLOW && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={7}>
                <Typography variant="h6" gutterBottom>
                  Lifecycle Progress
                </Typography>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Stepper activeStep={currentStepIndex}>
                    {statusTimeline.map((status, idx) => (
                      <Step key={status} completed={idx < currentStepIndex}>
                        <StepLabel sx={{ textTransform: 'capitalize' }}>{status.replace('_', ' ')}</StepLabel>
                      </Step>
                    ))}
                  </Stepper>

                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Current Status
                      </Typography>
                      <Chip
                        label={normalizedStatus.toUpperCase()}
                        color={
                          normalizedStatus === 'accepted'
                            ? 'success'
                            : normalizedStatus === 'rejected'
                              ? 'error'
                              : 'default'
                        }
                        sx={{ mt: 1 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Approval State
                      </Typography>
                      <Typography variant="body1" sx={{ mt: 1, textTransform: 'capitalize' }}>
                        {quote.approval_state || 'Not set'}
                      </Typography>
                    </Grid>
                    {quote.sent_at && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Sent At
                        </Typography>
                        <Typography variant="body2">{new Date(quote.sent_at).toLocaleString()}</Typography>
                      </Grid>
                    )}
                    {quote.viewed_at && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Last Viewed
                        </Typography>
                        <Typography variant="body2">{new Date(quote.viewed_at).toLocaleString()}</Typography>
                      </Grid>
                    )}
                    {quote.accepted_at && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Accepted At
                        </Typography>
                        <Typography variant="body2">{new Date(quote.accepted_at).toLocaleString()}</Typography>
                      </Grid>
                    )}
                    {quote.rejected_at && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Rejected At
                        </Typography>
                        <Typography variant="body2">{new Date(quote.rejected_at).toLocaleString()}</Typography>
                      </Grid>
                    )}
                    {quote.cancelled_at && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Cancelled At
                        </Typography>
                        <Typography variant="body2">{new Date(quote.cancelled_at).toLocaleString()}</Typography>
                      </Grid>
                    )}
                  </Grid>
                </Paper>
              </Grid>
              <Grid item xs={12} md={5}>
                <Typography variant="h6" gutterBottom>
                  Workflow Actions
                </Typography>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Stack spacing={2}>
                    {statusActions.filter((action) => action.visible).length === 0 && (
                      <Typography variant="body2" color="text.secondary">
                        No actions available for the current status.
                      </Typography>
                    )}
                    {statusActions
                      .filter((action) => action.visible)
                      .map((action) => (
                        <Box key={action.status} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 2 }}>
                          <Typography variant="subtitle1">{action.label}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {action.description}
                          </Typography>
                          <Button
                            variant="contained"
                            color={action.color as any}
                            fullWidth
                            onClick={() => openStatusDialog(action.status, action.label)}
                          >
                            {action.label}
                          </Button>
                        </Box>
                      ))}
                  </Stack>
                </Paper>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Activity Log
                </Typography>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  {workflowLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                      <CircularProgress size={28} />
                    </Box>
                  ) : workflowLog.length === 0 ? (
                    <Alert severity="info">No workflow activity recorded yet.</Alert>
                  ) : (
                    <List>
                      {workflowLog.map((entry: any) => (
                        <ListItem key={entry.id} alignItems="flex-start" sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
                          <ListItemText
                            primary={
                              <Box display="flex" justifyContent="space-between" alignItems="center">
                                <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                                  {entry.to_status?.replace('_', ' ') || 'Status update'}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {entry.created_at ? new Date(entry.created_at).toLocaleString() : ''}
                                </Typography>
                              </Box>
                            }
                            secondary={
                              <>
                                {entry.action && (
                                  <Typography variant="body2" color="text.secondary">
                                    Action: {entry.action}
                                  </Typography>
                                )}
                                {entry.comment && (
                                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', mt: 0.5 }}>
                                    {entry.comment}
                                  </Typography>
                                )}
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}

        {currentTab === TAB_INDEX.AI_PROMPT && (
          <Box>
            <QuotePromptManager quoteId={quote.id} />
          </Box>
        )}
      </Paper>

      <Dialog open={statusDialog.open} onClose={closeStatusDialog} fullWidth maxWidth="sm">
        <DialogTitle>{statusDialog.label}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Optionally capture context for this transition (visible in the workflow log).
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={3}
            label="Comment"
            value={statusComment}
            onChange={(e) => setStatusComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeStatusDialog} disabled={statusUpdating}>
            Cancel
          </Button>
          <Button onClick={handleStatusSubmit} variant="contained" disabled={statusUpdating}>
            {statusUpdating ? 'Updating...' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Link Opportunity Dialog */}
      <Dialog 
        open={linkOpportunityDialogOpen} 
        onClose={() => {
          setLinkOpportunityDialogOpen(false);
          setSelectedOpportunityId('');
          setLinkOpportunityError(null);
        }} 
        fullWidth 
        maxWidth="sm"
      >
        <DialogTitle>Link Quote to Opportunity</DialogTitle>
        <DialogContent>
          {linkOpportunityError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {linkOpportunityError}
            </Alert>
          )}
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select an opportunity to link this quote to. This will help track the quote in your sales pipeline.
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Opportunity</InputLabel>
            <Select
              value={selectedOpportunityId}
              onChange={(e) => setSelectedOpportunityId(e.target.value)}
              label="Select Opportunity"
            >
              {availableOpportunities.length === 0 ? (
                <MenuItem disabled value="">
                  No available opportunities
                </MenuItem>
              ) : (
                availableOpportunities.map((opp: any) => (
                  <MenuItem key={opp.id} value={opp.id}>
                    <Box>
                      <Typography variant="body1">{opp.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {opp.stage.replace('_', ' ').replace(/\b\w/g, char => char.toUpperCase())} • 
                        {opp.estimated_value ? ` £${opp.estimated_value.toLocaleString()}` : ' Value not set'} • 
                        {opp.conversion_probability}% probability
                      </Typography>
                    </Box>
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          {availableOpportunities.length === 0 && quote?.customer_id && (
            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => navigate(`/opportunities?customer_id=${quote.customer_id}`)}
                fullWidth
              >
                Create New Opportunity
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setLinkOpportunityDialogOpen(false);
              setSelectedOpportunityId('');
              setLinkOpportunityError(null);
            }} 
            disabled={linkOpportunityLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleLinkOpportunity} 
            variant="contained" 
            disabled={linkOpportunityLoading || !selectedOpportunityId}
            startIcon={<LinkIcon />}
          >
            {linkOpportunityLoading ? 'Linking...' : 'Link Opportunity'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default QuoteDetail;

