import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Link as MuiLink
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { supportContractAPI, slaAPI } from '../services/api';

const SupportContracts: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<any[]>([]);
  const [slaPolicies, setSlaPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    customer_id: '',
    contract_name: '',
    description: '',
    contract_type: 'managed_services',
    start_date: '',
    end_date: '',
    renewal_frequency: 'annual',
    auto_renew: true,
    monthly_value: '',
    annual_value: '',
    setup_fee: '0',
    currency: 'GBP',
    terms: '',
    sla_level: '',
    sla_policy_id: '',
    support_hours_included: '',
    renewal_notice_days: '90',
    cancellation_notice_days: '30',
    notes: ''
  });

  useEffect(() => {
    loadContracts();
    loadSlaPolicies();
  }, []);

  const loadContracts = async () => {
    try {
      setLoading(true);
      const response = await supportContractAPI.list();
      setContracts(response.data || []);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const loadSlaPolicies = async () => {
    try {
      const response = await slaAPI.listPolicies({ is_active: true });
      setSlaPolicies(response.data || []);
    } catch (error: any) {
      console.error('Failed to load SLA policies:', error);
    }
  };

  const handleOpenDialog = (contract?: any) => {
    if (contract) {
      setEditingContract(contract);
      setFormData({
        customer_id: contract.customer_id || '',
        contract_name: contract.contract_name || '',
        description: contract.description || '',
        contract_type: contract.contract_type || 'managed_services',
        start_date: contract.start_date || '',
        end_date: contract.end_date || '',
        renewal_frequency: contract.renewal_frequency || 'annual',
        auto_renew: contract.auto_renew !== undefined ? contract.auto_renew : true,
        monthly_value: contract.monthly_value?.toString() || '',
        annual_value: contract.annual_value?.toString() || '',
        setup_fee: contract.setup_fee?.toString() || '0',
        currency: contract.currency || 'GBP',
        terms: contract.terms || '',
        sla_level: contract.sla_level || '',
        sla_policy_id: contract.sla_policy_id || '',
        support_hours_included: contract.support_hours_included?.toString() || '',
        renewal_notice_days: contract.renewal_notice_days?.toString() || '90',
        cancellation_notice_days: contract.cancellation_notice_days?.toString() || '30',
        notes: contract.notes || ''
      });
    } else {
      setEditingContract(null);
      setFormData({
        customer_id: '',
        contract_name: '',
        description: '',
        contract_type: 'managed_services',
        start_date: '',
        end_date: '',
        renewal_frequency: 'annual',
        auto_renew: true,
        monthly_value: '',
        annual_value: '',
        setup_fee: '0',
        currency: 'GBP',
        terms: '',
        sla_level: '',
        sla_policy_id: '',
        support_hours_included: '',
        renewal_notice_days: '90',
        cancellation_notice_days: '30',
        notes: ''
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingContract(null);
    setError(null);
  };

  const handleSave = async () => {
    try {
      setError(null);
      const data: any = {
        ...formData,
        customer_id: formData.customer_id,
        contract_name: formData.contract_name,
        contract_type: formData.contract_type,
        start_date: formData.start_date,
        auto_renew: formData.auto_renew,
        setup_fee: parseFloat(formData.setup_fee) || 0,
        renewal_notice_days: parseInt(formData.renewal_notice_days) || 90,
        cancellation_notice_days: parseInt(formData.cancellation_notice_days) || 30
      };

      if (formData.end_date) data.end_date = formData.end_date;
      if (formData.renewal_frequency) data.renewal_frequency = formData.renewal_frequency;
      if (formData.monthly_value) data.monthly_value = parseFloat(formData.monthly_value);
      if (formData.annual_value) data.annual_value = parseFloat(formData.annual_value);
      if (formData.description) data.description = formData.description;
      if (formData.terms) data.terms = formData.terms;
      if (formData.sla_level) data.sla_level = formData.sla_level;
      if (formData.sla_policy_id) data.sla_policy_id = formData.sla_policy_id;
      if (formData.support_hours_included) data.support_hours_included = parseInt(formData.support_hours_included);
      if (formData.notes) data.notes = formData.notes;

      if (editingContract) {
        await supportContractAPI.update(editingContract.id, data);
        setSuccess('Contract updated successfully');
      } else {
        await supportContractAPI.create(data);
        setSuccess('Contract created successfully');
      }
      
      handleCloseDialog();
      loadContracts();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save contract');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'draft': return 'default';
      case 'pending_renewal': return 'warning';
      case 'expired': return 'error';
      case 'cancelled': return 'error';
      case 'suspended': return 'warning';
      default: return 'default';
    }
  };

  const getContractTypeLabel = (type: string) => {
    return type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || type;
  };

  const getSlaPolicyName = (policyId: string) => {
    const policy = slaPolicies.find(p => p.id === policyId);
    return policy ? policy.name : 'Not linked';
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Support Contracts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Contract
        </Button>
      </Box>

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

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Contract Number</strong></TableCell>
              <TableCell><strong>Name</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell><strong>Customer</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell><strong>SLA Policy</strong></TableCell>
              <TableCell><strong>Start Date</strong></TableCell>
              <TableCell><strong>Renewal Date</strong></TableCell>
              <TableCell><strong>Value</strong></TableCell>
              <TableCell><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {contracts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>
                    No support contracts found. Create your first contract to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              contracts.map((contract) => (
                <TableRow key={contract.id} hover>
                  <TableCell>{contract.contract_number}</TableCell>
                  <TableCell>{contract.contract_name}</TableCell>
                  <TableCell>
                    <Chip 
                      label={getContractTypeLabel(contract.contract_type)} 
                      size="small" 
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <MuiLink
                      component="button"
                      variant="body2"
                      onClick={() => navigate(`/customers/${contract.customer_id}`)}
                      sx={{ textDecoration: 'none' }}
                    >
                      View Customer
                    </MuiLink>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={contract.status} 
                      size="small" 
                      color={getStatusColor(contract.status) as any}
                    />
                  </TableCell>
                  <TableCell>
                    {contract.sla_policy_id ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AssessmentIcon fontSize="small" color="primary" />
                        <MuiLink
                          component="button"
                          variant="body2"
                          onClick={() => navigate(`/sla/policies/${contract.sla_policy_id}`)}
                          sx={{ textDecoration: 'none' }}
                        >
                          {getSlaPolicyName(contract.sla_policy_id)}
                        </MuiLink>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Not linked
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {contract.start_date ? new Date(contract.start_date).toLocaleDateString() : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {contract.renewal_date ? new Date(contract.renewal_date).toLocaleDateString() : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {contract.total_value 
                      ? `£${contract.total_value.toLocaleString()}` 
                      : contract.monthly_value 
                        ? `£${contract.monthly_value}/mo` 
                        : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => handleOpenDialog(contract)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingContract ? 'Edit Support Contract' : 'Create Support Contract'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Contract Name"
                value={formData.contract_name}
                onChange={(e) => setFormData({ ...formData, contract_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Contract Type</InputLabel>
                <Select
                  value={formData.contract_type}
                  onChange={(e) => setFormData({ ...formData, contract_type: e.target.value })}
                  label="Contract Type"
                >
                  <MenuItem value="managed_services">Managed Services</MenuItem>
                  <MenuItem value="maintenance">Maintenance</MenuItem>
                  <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                  <MenuItem value="support_hours">Support Hours</MenuItem>
                  <MenuItem value="warranty">Warranty</MenuItem>
                  <MenuItem value="consulting">Consulting</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Customer ID"
                value={formData.customer_id}
                onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                required
                helperText="Enter customer ID or use customer detail page to create"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="End Date (Optional)"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Renewal Frequency</InputLabel>
                <Select
                  value={formData.renewal_frequency}
                  onChange={(e) => setFormData({ ...formData, renewal_frequency: e.target.value })}
                  label="Renewal Frequency"
                >
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="quarterly">Quarterly</MenuItem>
                  <MenuItem value="semi_annual">Semi-Annual</MenuItem>
                  <MenuItem value="annual">Annual</MenuItem>
                  <MenuItem value="biennial">Biennial</MenuItem>
                  <MenuItem value="triennial">Triennial</MenuItem>
                  <MenuItem value="one_time">One Time</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Monthly Value"
                value={formData.monthly_value}
                onChange={(e) => setFormData({ ...formData, monthly_value: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Annual Value"
                value={formData.annual_value}
                onChange={(e) => setFormData({ ...formData, annual_value: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="SLA Level (Text)"
                value={formData.sla_level}
                onChange={(e) => setFormData({ ...formData, sla_level: e.target.value })}
                placeholder="e.g., 24/7, Business Hours"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>SLA Policy</InputLabel>
                <Select
                  value={formData.sla_policy_id}
                  onChange={(e) => setFormData({ ...formData, sla_policy_id: e.target.value })}
                  label="SLA Policy"
                >
                  <MenuItem value="">
                    <em>None - Not linked to SLA policy</em>
                  </MenuItem>
                  {slaPolicies.map((policy) => (
                    <MenuItem key={policy.id} value={policy.id}>
                      {policy.name} ({policy.first_response_hours}h response / {policy.resolution_hours}h resolution)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Support Hours Included"
                value={formData.support_hours_included}
                onChange={(e) => setFormData({ ...formData, support_hours_included: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Terms & Conditions"
                value={formData.terms}
                onChange={(e) => setFormData({ ...formData, terms: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            {editingContract ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SupportContracts;

