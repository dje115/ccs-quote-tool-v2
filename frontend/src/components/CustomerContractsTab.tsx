import React, { useState, useEffect } from 'react';
import {
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
  Tabs,
  Tab,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  Link as MuiLink,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Description as DescriptionIcon,
  Psychology as AiIcon,
  Assessment as AssessmentIcon,
  AutoAwesome as AutoAwesomeIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { contractAPI, supportContractAPI, slaAPI } from '../services/api';

interface CustomerContractsTabProps {
  customerId: string;
}

const CustomerContractsTab: React.FC<CustomerContractsTabProps> = ({ customerId }) => {
  const navigate = useNavigate();
  const [subTab, setSubTab] = useState(0); // 0 = Regular Contracts, 1 = Support Contracts
  const [regularContracts, setRegularContracts] = useState<any[]>([]);
  const [supportContracts, setSupportContracts] = useState<any[]>([]);
  const [slaPolicies, setSlaPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  
  // Regular Contract Dialog State
  const [regularDialogOpen, setRegularDialogOpen] = useState(false);
  const [regularContract, setRegularContract] = useState<any>(null);
  const [regularFormData, setRegularFormData] = useState({
    contract_name: '',
    contract_type: 'managed_services',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    monthly_value: '',
    annual_value: '',
    description: '',
    template_id: ''
  });
  
  // Support Contract Dialog State
  const [supportDialogOpen, setSupportDialogOpen] = useState(false);
  const [supportContract, setSupportContract] = useState<any>(null);
  const [supportFormData, setSupportFormData] = useState({
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
    notes: '',
    generate_quote: false
  });
  
  // AI Generation State
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiFormData, setAiFormData] = useState({
    contract_type: 'managed_services',
    description: '',
    requirements: '',
    sla_requirements: '',
    renewal_preferences: ''
  });
  const [aiGeneratedContent, setAiGeneratedContent] = useState<any>(null);
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadContracts();
    loadSlaPolicies();
  }, [customerId, statusFilter, typeFilter]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      
      // Load regular contracts
      const regularParams: any = { customer_id: customerId };
      if (statusFilter !== 'all') {
        regularParams.status = statusFilter;
      }
      if (typeFilter !== 'all') {
        regularParams.contract_type = typeFilter;
      }
      const regularResponse = await contractAPI.list(regularParams);
      setRegularContracts(regularResponse.data || []);
      
      // Load support contracts
      const supportParams: any = { customer_id: customerId };
      if (statusFilter !== 'all') {
        supportParams.status = statusFilter;
      }
      if (typeFilter !== 'all') {
        supportParams.contract_type = typeFilter;
      }
      const supportResponse = await supportContractAPI.list(supportParams);
      setSupportContracts(supportResponse.data || []);
    } catch (error: any) {
      console.error('Error loading contracts:', error);
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

  const handleOpenRegularDialog = (contract?: any) => {
    if (contract) {
      setRegularContract(contract);
      setRegularFormData({
        contract_name: contract.contract_name || '',
        contract_type: contract.contract_type || 'managed_services',
        start_date: contract.start_date ? new Date(contract.start_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        end_date: contract.end_date ? new Date(contract.end_date).toISOString().split('T')[0] : '',
        monthly_value: contract.monthly_value?.toString() || '',
        annual_value: contract.annual_value?.toString() || '',
        description: contract.description || '',
        template_id: contract.template_id || ''
      });
    } else {
      setRegularContract(null);
      setRegularFormData({
        contract_name: '',
        contract_type: 'managed_services',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        monthly_value: '',
        annual_value: '',
        description: '',
        template_id: ''
      });
    }
    setRegularDialogOpen(true);
  };

  const handleOpenSupportDialog = (contract?: any) => {
    if (contract) {
      setSupportContract(contract);
      setSupportFormData({
        contract_name: contract.contract_name || '',
        description: contract.description || '',
        contract_type: contract.contract_type || 'managed_services',
        start_date: contract.start_date ? new Date(contract.start_date).toISOString().split('T')[0] : '',
        end_date: contract.end_date ? new Date(contract.end_date).toISOString().split('T')[0] : '',
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
        notes: contract.notes || '',
        generate_quote: false
      });
    } else {
      setSupportContract(null);
      setSupportFormData({
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
        notes: '',
        generate_quote: false
      });
    }
    setSupportDialogOpen(true);
  };

  const handleSaveRegularContract = async () => {
    try {
      setError(null);
      const data: any = {
        customer_id: customerId,
        contract_name: regularFormData.contract_name,
        contract_type: regularFormData.contract_type,
        start_date: regularFormData.start_date,
        placeholder_values: {}
      };
      
      if (regularFormData.end_date) data.end_date = regularFormData.end_date;
      if (regularFormData.monthly_value) data.monthly_value = parseFloat(regularFormData.monthly_value);
      if (regularFormData.annual_value) data.annual_value = parseFloat(regularFormData.annual_value);
      if (regularFormData.description) data.description = regularFormData.description;
      if (regularFormData.template_id) data.template_id = regularFormData.template_id;

      if (regularContract) {
        await contractAPI.update(regularContract.id, data);
        setSuccess('Contract updated successfully');
      } else {
        await contractAPI.create(data);
        setSuccess('Contract created successfully');
      }
      
      setRegularDialogOpen(false);
      loadContracts();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save contract');
    }
  };

  const handleSaveSupportContract = async () => {
    try {
      setError(null);
      const data: any = {
        customer_id: customerId,
        contract_name: supportFormData.contract_name,
        contract_type: supportFormData.contract_type,
        start_date: supportFormData.start_date,
        auto_renew: supportFormData.auto_renew,
        setup_fee: parseFloat(supportFormData.setup_fee) || 0,
        renewal_notice_days: parseInt(supportFormData.renewal_notice_days) || 90,
        cancellation_notice_days: parseInt(supportFormData.cancellation_notice_days) || 30
      };

      if (supportFormData.end_date) data.end_date = supportFormData.end_date;
      if (supportFormData.renewal_frequency) data.renewal_frequency = supportFormData.renewal_frequency;
      if (supportFormData.monthly_value) data.monthly_value = parseFloat(supportFormData.monthly_value);
      if (supportFormData.annual_value) data.annual_value = parseFloat(supportFormData.annual_value);
      if (supportFormData.description) data.description = supportFormData.description;
      if (supportFormData.terms) data.terms = supportFormData.terms;
      if (supportFormData.sla_level) data.sla_level = supportFormData.sla_level;
      if (supportFormData.sla_policy_id) data.sla_policy_id = supportFormData.sla_policy_id;
      if (supportFormData.support_hours_included) data.support_hours_included = parseInt(supportFormData.support_hours_included);
      if (supportFormData.notes) data.notes = supportFormData.notes;
      if (supportFormData.generate_quote) data.generate_quote = supportFormData.generate_quote;

      if (supportContract) {
        await supportContractAPI.update(supportContract.id, data);
        setSuccess('Support contract updated successfully');
      } else {
        const response = await supportContractAPI.create(data);
        setSuccess('Support contract created successfully' + (supportFormData.generate_quote ? '. Quote and proposal are being generated...' : ''));
      }
      
      setSupportDialogOpen(false);
      loadContracts();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save support contract');
    }
  };

  const handleGenerateWithAI = async () => {
    try {
      setAiGenerating(true);
      setError(null);
      
      const requirements: any = {
        description: aiFormData.description
      };
      
      if (aiFormData.requirements) {
        requirements.additional_requirements = aiFormData.requirements;
      }
      
      if (subTab === 1) { // Support contract
        if (aiFormData.sla_requirements) {
          requirements.sla_requirements = aiFormData.sla_requirements;
        }
        if (aiFormData.renewal_preferences) {
          requirements.renewal_preferences = aiFormData.renewal_preferences;
        }
      }
      
      let response;
      if (subTab === 0) {
        // Regular contract generation
        response = await contractAPI.generateContract({
          contract_type: aiFormData.contract_type,
          description: aiFormData.description,
          requirements: requirements
        });
      } else {
        // Support contract generation
        response = await supportContractAPI.generateContract({
          contract_type: aiFormData.contract_type,
          description: aiFormData.description,
          requirements: requirements
        });
      }
      
      setAiGeneratedContent(response.data);
      setSuccess('Contract generated successfully! Review and edit before saving.');
      setTimeout(() => setSuccess(null), 5000);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to generate contract with AI');
    } finally {
      setAiGenerating(false);
    }
  };

  const handleUseAIGenerated = () => {
    if (!aiGeneratedContent) return;
    
    if (subTab === 0) {
      // Parse start date if provided
      let startDate = new Date().toISOString().split('T')[0];
      if (aiGeneratedContent.start_date) {
        try {
          const parsed = new Date(aiGeneratedContent.start_date);
          if (!isNaN(parsed.getTime())) {
            startDate = parsed.toISOString().split('T')[0];
          }
        } catch (e) {
          // Use default
        }
      }
      
      let endDate = '';
      if (aiGeneratedContent.end_date) {
        try {
          const parsed = new Date(aiGeneratedContent.end_date);
          if (!isNaN(parsed.getTime())) {
            endDate = parsed.toISOString().split('T')[0];
          }
        } catch (e) {
          // Leave empty
        }
      }
      
      // Populate regular contract form with ALL AI-generated fields
      setRegularFormData({
        contract_name: aiGeneratedContent.contract_name || '',
        contract_type: aiFormData.contract_type,
        start_date: startDate,
        end_date: endDate,
        monthly_value: aiGeneratedContent.monthly_value?.toString() || '',
        annual_value: aiGeneratedContent.annual_value?.toString() || '',
        description: aiGeneratedContent.description || aiFormData.description,
        template_id: ''
      });
      setAiDialogOpen(false);
      setRegularDialogOpen(true);
    } else {
      // Parse dates if provided
      let startDate = new Date().toISOString().split('T')[0];
      if (aiGeneratedContent.start_date) {
        try {
          const parsed = new Date(aiGeneratedContent.start_date);
          if (!isNaN(parsed.getTime())) {
            startDate = parsed.toISOString().split('T')[0];
          }
        } catch (e) {
          // Use default
        }
      }
      
      let endDate = '';
      if (aiGeneratedContent.end_date) {
        try {
          const parsed = new Date(aiGeneratedContent.end_date);
          if (!isNaN(parsed.getTime())) {
            endDate = parsed.toISOString().split('T')[0];
          }
        } catch (e) {
          // Leave empty
        }
      }
      
      // Populate support contract form with ALL AI-generated fields
      setSupportFormData({
        contract_name: aiGeneratedContent.contract_name || '',
        description: aiGeneratedContent.description || aiFormData.description,
        contract_type: aiFormData.contract_type,
        start_date: startDate,
        end_date: endDate,
        renewal_frequency: aiGeneratedContent.renewal_frequency || 'annual',
        auto_renew: aiGeneratedContent.auto_renew !== undefined ? aiGeneratedContent.auto_renew : true,
        monthly_value: aiGeneratedContent.monthly_value?.toString() || '',
        annual_value: aiGeneratedContent.annual_value?.toString() || '',
        setup_fee: aiGeneratedContent.setup_fee?.toString() || '0',
        currency: 'GBP',
        terms: aiGeneratedContent.terms || '',
        sla_level: aiGeneratedContent.sla_level || '',
        sla_policy_id: aiGeneratedContent.sla_policy_id || '',
        support_hours_included: aiGeneratedContent.support_hours_included?.toString() || '',
        renewal_notice_days: aiGeneratedContent.renewal_notice_days?.toString() || '90',
        cancellation_notice_days: aiGeneratedContent.cancellation_notice_days?.toString() || '30',
        notes: aiGeneratedContent.notes || '',
        generate_quote: false
      });
      setAiDialogOpen(false);
      setSupportDialogOpen(true);
    }
    
    setAiGeneratedContent(null);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'draft':
        return 'default';
      case 'pending_signature':
      case 'pending_renewal':
        return 'warning';
      case 'expired':
      case 'cancelled':
        return 'error';
      case 'suspended':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getTypeLabel = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const getSlaPolicyName = (policyId: string) => {
    const policy = slaPolicies.find(p => p.id === policyId);
    return policy ? policy.name : 'Not linked';
  };

  const filteredRegularContracts = regularContracts.filter(contract =>
    contract.contract_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.contract_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contract.description && contract.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const filteredSupportContracts = supportContracts.filter(contract =>
    contract.contract_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.contract_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contract.description && contract.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <Box>
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

      {/* Sub-tabs for Regular vs Support Contracts */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={subTab}
          onChange={(e, newValue) => setSubTab(newValue)}
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
          }}
        >
          <Tab label="Regular Contracts" />
          <Tab label="Support Contracts" />
        </Tabs>
      </Paper>

      {/* Header with Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DescriptionIcon />
          {subTab === 0 ? 'Regular Contracts' : 'Support Contracts'}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AiIcon />}
            onClick={() => setAiDialogOpen(true)}
          >
            Generate with AI
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => subTab === 0 ? handleOpenRegularDialog() : handleOpenSupportDialog()}
          >
            Create {subTab === 0 ? 'Contract' : 'Support Contract'}
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <TextField
            fullWidth
            placeholder="Search contracts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Statuses</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="pending_signature">Pending Signature</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="expired">Expired</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              label="Type"
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="managed_services">Managed Services</MenuItem>
              <MenuItem value="software_license">Software License</MenuItem>
              <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
              <MenuItem value="maintenance">Maintenance</MenuItem>
              <MenuItem value="support_hours">Support Hours</MenuItem>
              <MenuItem value="consulting">Consulting</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Regular Contracts Table */}
      {subTab === 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Contract #</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Type</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Start Date</strong></TableCell>
                <TableCell><strong>Value</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredRegularContracts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No regular contracts found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredRegularContracts.map((contract) => (
                  <TableRow key={contract.id} hover>
                    <TableCell>{contract.contract_number}</TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {contract.contract_name}
                      </Typography>
                      {contract.description && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {contract.description.substring(0, 50)}...
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{getTypeLabel(contract.contract_type)}</TableCell>
                    <TableCell>
                      <Chip
                        label={contract.status.replace('_', ' ')}
                        size="small"
                        color={getStatusColor(contract.status) as any}
                      />
                    </TableCell>
                    <TableCell>
                      {contract.start_date ? new Date(contract.start_date).toLocaleDateString() : 'N/A'}
                    </TableCell>
                    <TableCell>
                      {contract.annual_value ? `£${contract.annual_value.toLocaleString()}/yr` :
                       contract.monthly_value ? `£${contract.monthly_value.toLocaleString()}/mo` :
                       'N/A'}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/contracts/${contract.id}`)}
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenRegularDialog(contract)}
                      >
                        <EditIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Support Contracts Table */}
      {subTab === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Contract #</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Type</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>SLA Policy</strong></TableCell>
                <TableCell><strong>Start Date</strong></TableCell>
                <TableCell><strong>Renewal Date</strong></TableCell>
                <TableCell><strong>Value</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredSupportContracts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No support contracts found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredSupportContracts.map((contract) => (
                  <TableRow key={contract.id} hover>
                    <TableCell>{contract.contract_number}</TableCell>
                    <TableCell>{contract.contract_name}</TableCell>
                    <TableCell>
                      <Chip
                        label={getTypeLabel(contract.contract_type)}
                        size="small"
                        variant="outlined"
                      />
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
                      <IconButton
                        size="small"
                        onClick={() => handleOpenSupportDialog(contract)}
                      >
                        <EditIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Regular Contract Create/Edit Dialog */}
      <Dialog open={regularDialogOpen} onClose={() => setRegularDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {regularContract ? 'Edit Contract' : 'Create New Contract'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Contract Name *"
              fullWidth
              value={regularFormData.contract_name}
              onChange={(e) => setRegularFormData({ ...regularFormData, contract_name: e.target.value })}
              required
            />
            <FormControl fullWidth required>
              <InputLabel>Contract Type *</InputLabel>
              <Select
                value={regularFormData.contract_type}
                label="Contract Type *"
                onChange={(e) => setRegularFormData({ ...regularFormData, contract_type: e.target.value })}
              >
                <MenuItem value="managed_services">Managed Services</MenuItem>
                <MenuItem value="software_license">Software License</MenuItem>
                <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="support_hours">Support Hours</MenuItem>
                <MenuItem value="consulting">Consulting</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Start Date *"
              type="date"
              fullWidth
              value={regularFormData.start_date}
              onChange={(e) => setRegularFormData({ ...regularFormData, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              required
            />
            <TextField
              label="End Date (Optional)"
              type="date"
              fullWidth
              value={regularFormData.end_date}
              onChange={(e) => setRegularFormData({ ...regularFormData, end_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Monthly Value"
                  type="number"
                  fullWidth
                  value={regularFormData.monthly_value}
                  onChange={(e) => setRegularFormData({ ...regularFormData, monthly_value: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Annual Value"
                  type="number"
                  fullWidth
                  value={regularFormData.annual_value}
                  onChange={(e) => setRegularFormData({ ...regularFormData, annual_value: e.target.value })}
                />
              </Grid>
            </Grid>
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={regularFormData.description}
              onChange={(e) => setRegularFormData({ ...regularFormData, description: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRegularDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveRegularContract}
            variant="contained"
            disabled={!regularFormData.contract_name}
          >
            {regularContract ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Support Contract Create/Edit Dialog */}
      <Dialog open={supportDialogOpen} onClose={() => setSupportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {supportContract ? 'Edit Support Contract' : 'Create Support Contract'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Contract Name"
                value={supportFormData.contract_name}
                onChange={(e) => setSupportFormData({ ...supportFormData, contract_name: e.target.value })}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required>
                <InputLabel>Contract Type</InputLabel>
                <Select
                  value={supportFormData.contract_type}
                  onChange={(e) => setSupportFormData({ ...supportFormData, contract_type: e.target.value })}
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
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                value={supportFormData.start_date}
                onChange={(e) => setSupportFormData({ ...supportFormData, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="date"
                label="End Date (Optional)"
                value={supportFormData.end_date}
                onChange={(e) => setSupportFormData({ ...supportFormData, end_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Renewal Frequency</InputLabel>
                <Select
                  value={supportFormData.renewal_frequency}
                  onChange={(e) => setSupportFormData({ ...supportFormData, renewal_frequency: e.target.value })}
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
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={supportFormData.auto_renew}
                    onChange={(e) => setSupportFormData({ ...supportFormData, auto_renew: e.target.checked })}
                  />
                }
                label="Auto Renew"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={supportFormData.generate_quote}
                    onChange={(e) => setSupportFormData({ ...supportFormData, generate_quote: e.target.checked })}
                  />
                }
                label="Generate Quote & Proposal (AI-powered quote will be created from this contract and available in Quotes section)"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="Monthly Value"
                value={supportFormData.monthly_value}
                onChange={(e) => setSupportFormData({ ...supportFormData, monthly_value: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="Annual Value"
                value={supportFormData.annual_value}
                onChange={(e) => setSupportFormData({ ...supportFormData, annual_value: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="SLA Level (Text)"
                value={supportFormData.sla_level}
                onChange={(e) => setSupportFormData({ ...supportFormData, sla_level: e.target.value })}
                placeholder="e.g., 24/7, Business Hours"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>SLA Policy</InputLabel>
                <Select
                  value={supportFormData.sla_policy_id}
                  onChange={(e) => setSupportFormData({ ...supportFormData, sla_policy_id: e.target.value })}
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
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="number"
                label="Support Hours Included"
                value={supportFormData.support_hours_included}
                onChange={(e) => setSupportFormData({ ...supportFormData, support_hours_included: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={supportFormData.description}
                onChange={(e) => setSupportFormData({ ...supportFormData, description: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Terms & Conditions"
                value={supportFormData.terms}
                onChange={(e) => setSupportFormData({ ...supportFormData, terms: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Notes"
                value={supportFormData.notes}
                onChange={(e) => setSupportFormData({ ...supportFormData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSupportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveSupportContract} variant="contained" color="primary">
            {supportContract ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Generation Dialog */}
      <Dialog open={aiDialogOpen} onClose={() => setAiDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesomeIcon />
            Generate {subTab === 0 ? 'Contract' : 'Support Contract'} with AI
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth required>
              <InputLabel>Contract Type</InputLabel>
              <Select
                value={aiFormData.contract_type}
                label="Contract Type"
                onChange={(e) => setAiFormData({ ...aiFormData, contract_type: e.target.value })}
              >
                <MenuItem value="managed_services">Managed Services</MenuItem>
                <MenuItem value="software_license">Software License</MenuItem>
                <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="support_hours">Support Hours</MenuItem>
                <MenuItem value="consulting">Consulting</MenuItem>
                {subTab === 1 && <MenuItem value="warranty">Warranty</MenuItem>}
              </Select>
            </FormControl>
            <TextField
              label="Description *"
              fullWidth
              multiline
              rows={4}
              value={aiFormData.description}
              onChange={(e) => setAiFormData({ ...aiFormData, description: e.target.value })}
              placeholder="Describe what this contract should cover, services included, etc."
              required
            />
            <TextField
              label="Additional Requirements (Optional)"
              fullWidth
              multiline
              rows={3}
              value={aiFormData.requirements}
              onChange={(e) => setAiFormData({ ...aiFormData, requirements: e.target.value })}
              placeholder="Any specific terms, pricing structure, duration, etc."
            />
            {subTab === 1 && (
              <>
                <TextField
                  label="SLA Requirements (Optional)"
                  fullWidth
                  multiline
                  rows={2}
                  value={aiFormData.sla_requirements}
                  onChange={(e) => setAiFormData({ ...aiFormData, sla_requirements: e.target.value })}
                  placeholder="e.g., 24/7 support, 4-hour response time, business hours only"
                />
                <TextField
                  label="Renewal Preferences (Optional)"
                  fullWidth
                  multiline
                  rows={2}
                  value={aiFormData.renewal_preferences}
                  onChange={(e) => setAiFormData({ ...aiFormData, renewal_preferences: e.target.value })}
                  placeholder="e.g., Annual renewal, auto-renew enabled, 90-day notice period"
                />
              </>
            )}
            {aiGeneratedContent && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Contract Generated Successfully!
                </Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Review the generated contract details below, then click "Use Generated Contract" to populate the form.
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                    {JSON.stringify(aiGeneratedContent, null, 2)}
                  </Typography>
                </Box>
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setAiDialogOpen(false);
            setAiGeneratedContent(null);
          }}>
            Cancel
          </Button>
          {aiGeneratedContent ? (
            <Button
              onClick={handleUseAIGenerated}
              variant="contained"
              startIcon={<CheckIcon />}
            >
              Use Generated Contract
            </Button>
          ) : (
            <Button
              onClick={handleGenerateWithAI}
              variant="contained"
              disabled={!aiFormData.description || aiGenerating}
              startIcon={aiGenerating ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
            >
              {aiGenerating ? 'Generating...' : 'Generate Contract'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CustomerContractsTab;

