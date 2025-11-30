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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Add as AddIcon,
  AttachFile as AttachFileIcon,
  Description as DescriptionIcon,
  TrendingUp as TrendingUpIcon,
  CalendarToday as CalendarIcon,
  Link as LinkIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { opportunityAPI, quoteAPI, contractAPI, customerAPI } from '../services/api';

interface Opportunity {
  id: string;
  customer_id: string;
  title: string;
  description?: string;
  stage: string;
  conversion_probability: number;
  potential_deal_date?: string;
  estimated_value?: number;
  quote_ids?: string[];
  support_contract_ids?: string[];
  attachments?: Array<{ name: string; url: string; uploaded_at: string }>;
  notes?: string;
  recurring_quote_schedule?: any;
  created_at: string;
  updated_at: string;
}

const OpportunityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [contracts, setContracts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    title: '',
    description: '',
    stage: 'qualified',
    conversion_probability: 20,
    potential_deal_date: '',
    estimated_value: '',
    notes: ''
  });
  const [linkQuoteDialogOpen, setLinkQuoteDialogOpen] = useState(false);
  const [availableQuotes, setAvailableQuotes] = useState<any[]>([]);
  const [selectedQuoteId, setSelectedQuoteId] = useState('');
  const [createContractDialogOpen, setCreateContractDialogOpen] = useState(false);
  const [contractTemplates, setContractTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [placeholderValues, setPlaceholderValues] = useState<Record<string, any>>({});
  const [newContract, setNewContract] = useState({
    contract_name: '',
    contract_type: 'managed_services',
    start_date: new Date().toISOString().split('T')[0],
    monthly_value: '',
    annual_value: ''
  });

  useEffect(() => {
    if (id) {
      loadOpportunity();
    }
  }, [id]);

  const loadOpportunity = async () => {
    try {
      setLoading(true);
      const response = await opportunityAPI.get(id!);
      setOpportunity(response.data);
      
      // Load linked quotes if any
      if (response.data.quote_ids && response.data.quote_ids.length > 0) {
        loadQuotes(response.data.quote_ids);
      }
      
      // Load linked contracts
      loadContracts();
      
      // Initialize edit form
      setEditFormData({
        title: response.data.title,
        description: response.data.description || '',
        stage: response.data.stage,
        conversion_probability: response.data.conversion_probability,
        potential_deal_date: response.data.potential_deal_date ? 
          new Date(response.data.potential_deal_date).toISOString().split('T')[0] : '',
        estimated_value: response.data.estimated_value?.toString() || '',
        notes: response.data.notes || ''
      });
    } catch (error) {
      console.error('Error loading opportunity:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQuotes = async (quoteIds: string[]) => {
    try {
      const quotePromises = quoteIds.map(quoteId => 
        quoteAPI.get(quoteId).catch(() => null)
      );
      const quoteResults = await Promise.all(quotePromises);
      setQuotes(quoteResults.filter(q => q !== null).map(q => q.data));
    } catch (error) {
      console.error('Error loading quotes:', error);
    }
  };

  const loadAvailableQuotes = async () => {
    try {
      if (!opportunity) return;
      const response = await quoteAPI.list({ customer_id: opportunity.customer_id });
      setAvailableQuotes(response.data || []);
    } catch (error) {
      console.error('Error loading available quotes:', error);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await contractAPI.list({ opportunity_id: id });
      setContracts(response.data || []);
    } catch (error) {
      console.error('Error loading contracts:', error);
      setContracts([]);
    }
  };

  const loadContractTemplates = async () => {
    try {
      const response = await contractAPI.listTemplates({ is_active: true });
      setContractTemplates(response.data || []);
    } catch (error) {
      console.error('Error loading contract templates:', error);
    }
  };

  const handleTemplateSelect = async (templateId: string) => {
    try {
      const template = contractTemplates.find(t => t.id === templateId);
      if (!template) return;
      
      setSelectedTemplate(template);
      
      // Get current version to extract placeholders
      if (template.versions && template.versions.length > 0) {
        const currentVersion = template.versions.find((v: any) => v.is_current) || template.versions[0];
        
        // Initialize placeholder values with defaults
        const defaults: Record<string, any> = {};
        if (currentVersion.default_values) {
          Object.assign(defaults, currentVersion.default_values);
        }
        
        // Pre-fill with opportunity/customer data if available
        if (opportunity) {
          if (opportunity.estimated_value) {
            defaults.monthly_fee = (opportunity.estimated_value / 12).toFixed(2);
            defaults.annual_value = opportunity.estimated_value.toFixed(2);
          }
        }
        
        setPlaceholderValues(defaults);
      }
    } catch (error) {
      console.error('Error loading template:', error);
    }
  };

  const handleCreateContract = async () => {
    try {
      if (!opportunity) return;
      
      const contractData = {
        customer_id: opportunity.customer_id,
        template_id: selectedTemplate?.id || null,
        template_version_id: selectedTemplate?.versions?.find((v: any) => v.is_current)?.id || null,
        contract_name: newContract.contract_name,
        contract_type: newContract.contract_type,
        start_date: newContract.start_date,
        monthly_value: newContract.monthly_value ? parseFloat(newContract.monthly_value) : null,
        annual_value: newContract.annual_value ? parseFloat(newContract.annual_value) : null,
        placeholder_values: placeholderValues,
        opportunity_id: id
      };
      
      await contractAPI.create(contractData);
      setCreateContractDialogOpen(false);
      setNewContract({
        contract_name: '',
        contract_type: 'managed_services',
        start_date: new Date().toISOString().split('T')[0],
        monthly_value: '',
        annual_value: ''
      });
      setPlaceholderValues({});
      setSelectedTemplate(null);
      loadContracts();
      loadOpportunity();
    } catch (error) {
      console.error('Error creating contract:', error);
      alert('Failed to create contract');
    }
  };

  const handleUpdateStage = async (newStage: string) => {
    if (!opportunity) return;
    
    try {
      await opportunityAPI.updateStage(opportunity.id, newStage);
      await loadOpportunity();
    } catch (error) {
      console.error('Error updating stage:', error);
      alert('Failed to update stage');
    }
  };

  const handleSave = async () => {
    if (!opportunity) return;
    
    try {
      await opportunityAPI.update(opportunity.id, {
        ...editFormData,
        potential_deal_date: editFormData.potential_deal_date || null,
        estimated_value: editFormData.estimated_value ? parseFloat(editFormData.estimated_value) : null
      });
      setEditDialogOpen(false);
      await loadOpportunity();
    } catch (error) {
      console.error('Error updating opportunity:', error);
      alert('Failed to update opportunity');
    }
  };

  const handleLinkQuote = async () => {
    if (!opportunity || !selectedQuoteId) return;
    
    try {
      await opportunityAPI.attachQuote(opportunity.id, selectedQuoteId);
      setLinkQuoteDialogOpen(false);
      setSelectedQuoteId('');
      await loadOpportunity();
    } catch (error) {
      console.error('Error linking quote:', error);
      alert('Failed to link quote');
    }
  };

  const getStageColor = (stage: string) => {
    const stageColors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      qualified: 'info',
      scoping: 'primary',
      proposal_sent: 'warning',
      negotiation: 'warning',
      verbal_yes: 'success',
      closed_won: 'success',
      closed_lost: 'error'
    };
    return stageColors[stage] || 'default';
  };

  const getStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      qualified: 'Qualified',
      scoping: 'Scoping',
      proposal_sent: 'Proposal Sent',
      negotiation: 'Negotiation',
      verbal_yes: 'Verbal Yes',
      closed_won: 'Closed Won',
      closed_lost: 'Closed Lost'
    };
    return labels[stage] || stage;
  };

  const stageOptions = [
    { value: 'qualified', label: 'Qualified' },
    { value: 'scoping', label: 'Scoping' },
    { value: 'proposal_sent', label: 'Proposal Sent' },
    { value: 'negotiation', label: 'Negotiation' },
    { value: 'verbal_yes', label: 'Verbal Yes' },
    { value: 'closed_won', label: 'Closed Won' },
    { value: 'closed_lost', label: 'Closed Lost' }
  ];

  if (loading || !opportunity) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Box sx={{ textAlign: 'center' }}>
          {loading ? (
            <>
              <CircularProgress />
              <Typography sx={{ mt: 2 }}>Loading opportunity...</Typography>
            </>
          ) : (
            <Typography>Opportunity not found</Typography>
          )}
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate(`/customers/${opportunity.customer_id}`)}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {opportunity.title}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => setEditDialogOpen(true)}
        >
          Edit
        </Button>
      </Box>

      {/* Stage and Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Pipeline Stage
              </Typography>
              <Chip
                label={getStageLabel(opportunity.stage)}
                color={getStageColor(opportunity.stage)}
                size="medium"
                sx={{ mb: 2 }}
              />
              <Box sx={{ mt: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Change Stage</InputLabel>
                  <Select
                    value={opportunity.stage}
                    label="Change Stage"
                    onChange={(e) => handleUpdateStage(e.target.value)}
                  >
                    {stageOptions.map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Conversion Probability
              </Typography>
              <Typography variant="h4" color="primary">
                {opportunity.conversion_probability}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Estimated Value
              </Typography>
              <Typography variant="h4" color="success.main">
                {opportunity.estimated_value ? 
                  `£${opportunity.estimated_value.toLocaleString()}` : 
                  'Not set'
                }
              </Typography>
              {opportunity.potential_deal_date && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  <CalendarIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                  Expected: {new Date(opportunity.potential_deal_date).toLocaleDateString()}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab label="Overview" icon={<DescriptionIcon />} iconPosition="start" />
          <Tab label="Quotes" icon={<LinkIcon />} iconPosition="start" />
          <Tab label="Contracts" icon={<CheckCircleIcon />} iconPosition="start" />
          <Tab label="Attachments" icon={<AttachFileIcon />} iconPosition="start" />
          <Tab label="Notes" icon={<DescriptionIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {currentTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Overview</Typography>
          <Divider sx={{ mb: 2 }} />
          
          {opportunity.description && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1">{opportunity.description}</Typography>
            </Box>
          )}

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="text.secondary">Stage</Typography>
              <Chip
                label={getStageLabel(opportunity.stage)}
                color={getStageColor(opportunity.stage)}
                sx={{ mt: 0.5 }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="text.secondary">Conversion Probability</Typography>
              <Typography variant="body1">{opportunity.conversion_probability}%</Typography>
            </Grid>
            {opportunity.estimated_value && (
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">Estimated Value</Typography>
                <Typography variant="body1">£{opportunity.estimated_value.toLocaleString()}</Typography>
              </Grid>
            )}
            {opportunity.potential_deal_date && (
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">Potential Deal Date</Typography>
                <Typography variant="body1">
                  {new Date(opportunity.potential_deal_date).toLocaleDateString()}
                </Typography>
              </Grid>
            )}
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="text.secondary">Created</Typography>
              <Typography variant="body1">
                {new Date(opportunity.created_at).toLocaleDateString()}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="text.secondary">Last Updated</Typography>
              <Typography variant="body1">
                {new Date(opportunity.updated_at).toLocaleDateString()}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {currentTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Linked Quotes</Typography>
            <Button
              variant="outlined"
              startIcon={<LinkIcon />}
              onClick={() => {
                loadAvailableQuotes();
                setLinkQuoteDialogOpen(true);
              }}
            >
              Link Quote
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {quotes.length === 0 ? (
            <Alert severity="info">No quotes linked to this opportunity</Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Quote Number</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Total Amount</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {quotes.map((quote) => (
                    <TableRow key={quote.id}>
                      <TableCell>{quote.quote_number}</TableCell>
                      <TableCell>{quote.title}</TableCell>
                      <TableCell>
                        <Chip label={quote.status} size="small" />
                      </TableCell>
                      <TableCell>
                        {quote.total_amount ? `£${quote.total_amount.toLocaleString()}` : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/quotes/${quote.id}`)}
                        >
                          <EditIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {currentTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Contracts</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                loadContractTemplates();
                setCreateContractDialogOpen(true);
              }}
            >
              Create Contract
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          
          {contracts.length === 0 ? (
            <Alert severity="info">No contracts linked to this opportunity</Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Contract Number</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {contracts.map((contract) => (
                    <TableRow key={contract.id} hover>
                      <TableCell>{contract.contract_number}</TableCell>
                      <TableCell>{contract.contract_name}</TableCell>
                      <TableCell>
                        {contract.contract_type.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={contract.status.replace('_', ' ')} 
                          size="small"
                          color={
                            contract.status === 'active' ? 'success' :
                            contract.status === 'draft' ? 'default' :
                            contract.status === 'pending_signature' ? 'warning' :
                            contract.status === 'expired' || contract.status === 'cancelled' ? 'error' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>{new Date(contract.start_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {contract.annual_value ? `£${contract.annual_value.toLocaleString()}/yr` :
                         contract.monthly_value ? `£${contract.monthly_value.toLocaleString()}/mo` :
                         'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/contracts/${contract.id}`)}
                        >
                          <EditIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {currentTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Support Contracts</Typography>
          <Divider sx={{ mb: 2 }} />
          <Alert severity="info">
            Support contract management will be implemented in a future update.
          </Alert>
        </Paper>
      )}

      {currentTab === 3 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Attachments</Typography>
          <Divider sx={{ mb: 2 }} />
          {opportunity.attachments && opportunity.attachments.length > 0 ? (
            <List>
              {opportunity.attachments.map((attachment, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={attachment.name}
                    secondary={`Uploaded: ${new Date(attachment.uploaded_at).toLocaleDateString()}`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => window.open(attachment.url, '_blank')}
                    >
                      <AttachFileIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity="info">No attachments</Alert>
          )}
        </Paper>
      )}

      {currentTab === 4 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Notes</Typography>
          <Divider sx={{ mb: 2 }} />
          {opportunity.notes ? (
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {opportunity.notes}
            </Typography>
          ) : (
            <Alert severity="info">No notes</Alert>
          )}
        </Paper>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Opportunity</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Title"
              fullWidth
              value={editFormData.title}
              onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={4}
              value={editFormData.description}
              onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Stage</InputLabel>
              <Select
                value={editFormData.stage}
                label="Stage"
                onChange={(e) => setEditFormData({ ...editFormData, stage: e.target.value })}
              >
                {stageOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Conversion Probability (%)"
              type="number"
              fullWidth
              value={editFormData.conversion_probability}
              onChange={(e) => setEditFormData({ ...editFormData, conversion_probability: parseInt(e.target.value) || 0 })}
              inputProps={{ min: 0, max: 100 }}
            />
            <TextField
              label="Potential Deal Date"
              type="date"
              fullWidth
              value={editFormData.potential_deal_date}
              onChange={(e) => setEditFormData({ ...editFormData, potential_deal_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="Estimated Value"
              type="number"
              fullWidth
              value={editFormData.estimated_value}
              onChange={(e) => setEditFormData({ ...editFormData, estimated_value: e.target.value })}
            />
            <TextField
              label="Notes"
              fullWidth
              multiline
              rows={4}
              value={editFormData.notes}
              onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Link Quote Dialog */}
      <Dialog open={linkQuoteDialogOpen} onClose={() => setLinkQuoteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Quote to Opportunity</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Quote</InputLabel>
            <Select
              value={selectedQuoteId}
              label="Select Quote"
              onChange={(e) => setSelectedQuoteId(e.target.value)}
            >
              {availableQuotes
                .filter(q => !opportunity.quote_ids?.includes(q.id))
                .map(quote => (
                  <MenuItem key={quote.id} value={quote.id}>
                    {quote.quote_number} - {quote.title}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkQuoteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleLinkQuote} variant="contained" disabled={!selectedQuoteId}>
            Link Quote
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Contract Dialog */}
      <Dialog open={createContractDialogOpen} onClose={() => setCreateContractDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Contract</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Contract Template</InputLabel>
              <Select
                value={selectedTemplate?.id || ''}
                label="Contract Template"
                onChange={(e) => handleTemplateSelect(e.target.value)}
              >
                {contractTemplates.map(template => (
                  <MenuItem key={template.id} value={template.id}>
                    {template.name} ({template.contract_type.replace('_', ' ')})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Contract Name"
              fullWidth
              required
              value={newContract.contract_name}
              onChange={(e) => setNewContract({ ...newContract, contract_name: e.target.value })}
            />

            <FormControl fullWidth>
              <InputLabel>Contract Type</InputLabel>
              <Select
                value={newContract.contract_type}
                label="Contract Type"
                onChange={(e) => setNewContract({ ...newContract, contract_type: e.target.value })}
              >
                <MenuItem value="managed_services">Managed Services</MenuItem>
                <MenuItem value="software_license">Software License</MenuItem>
                <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="support_hours">Support Hours</MenuItem>
                <MenuItem value="consulting">Consulting</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Start Date"
              type="date"
              fullWidth
              required
              value={newContract.start_date}
              onChange={(e) => setNewContract({ ...newContract, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Monthly Value (GBP)"
                  type="number"
                  fullWidth
                  value={newContract.monthly_value}
                  onChange={(e) => {
                    const monthly = e.target.value;
                    setNewContract({ 
                      ...newContract, 
                      monthly_value: monthly,
                      annual_value: monthly ? (parseFloat(monthly) * 12).toString() : ''
                    });
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Annual Value (GBP)"
                  type="number"
                  fullWidth
                  value={newContract.annual_value}
                  onChange={(e) => {
                    const annual = e.target.value;
                    setNewContract({ 
                      ...newContract, 
                      annual_value: annual,
                      monthly_value: annual ? (parseFloat(annual) / 12).toString() : ''
                    });
                  }}
                />
              </Grid>
            </Grid>

            {selectedTemplate && selectedTemplate.versions && selectedTemplate.versions.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Template Placeholders</Typography>
                {Object.keys(placeholderValues).map(key => (
                  <TextField
                    key={key}
                    label={key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    fullWidth
                    sx={{ mt: 1 }}
                    value={placeholderValues[key] || ''}
                    onChange={(e) => setPlaceholderValues({ ...placeholderValues, [key]: e.target.value })}
                  />
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateContractDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateContract} 
            variant="contained" 
            disabled={!newContract.contract_name || !newContract.start_date}
          >
            Create Contract
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OpportunityDetail;

