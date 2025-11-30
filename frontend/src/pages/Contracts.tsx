import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { contractAPI, customerAPI } from '../services/api';

interface Contract {
  id: string;
  contract_number: string;
  contract_name: string;
  description?: string;
  contract_type: string;
  status: string;
  start_date: string;
  end_date?: string;
  monthly_value?: number;
  annual_value?: number;
  customer_id: string;
  opportunity_id?: string;
  created_at: string;
}

const Contracts: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [newContract, setNewContract] = useState({
    customer_id: '',
    template_id: '',
    contract_name: '',
    contract_type: 'managed_services',
    start_date: new Date().toISOString().split('T')[0],
    placeholder_values: {}
  });

  useEffect(() => {
    loadContracts();
    loadCustomers();
  }, [statusFilter, typeFilter]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (typeFilter !== 'all') {
        params.contract_type = typeFilter;
      }
      
      const response = await contractAPI.list(params);
      setContracts(response.data || []);
    } catch (error) {
      console.error('Error loading contracts:', error);
      setContracts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await customerAPI.list({ limit: 1000, exclude_leads: false });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const filteredContracts = contracts.filter(contract =>
    contract.contract_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.contract_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contract.description && contract.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'draft':
        return 'default';
      case 'pending_signature':
        return 'warning';
      case 'expired':
        return 'error';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTypeLabel = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const handleCreateContract = async () => {
    try {
      await contractAPI.create(newContract);
      setCreateDialogOpen(false);
      setNewContract({
        customer_id: '',
        template_id: '',
        contract_name: '',
        contract_type: 'managed_services',
        start_date: new Date().toISOString().split('T')[0],
        placeholder_values: {}
      });
      loadContracts();
    } catch (error) {
      console.error('Error creating contract:', error);
      alert('Failed to create contract');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DescriptionIcon /> Contracts
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/contracts/templates')}
          >
            Manage Templates
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Contract
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
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

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Contract #</strong></TableCell>
              <TableCell><strong>Name</strong></TableCell>
              <TableCell><strong>Customer</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell><strong>Start Date</strong></TableCell>
              <TableCell><strong>Value</strong></TableCell>
              <TableCell><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredContracts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {loading ? 'Loading contracts...' : 'No contracts found'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredContracts.map((contract) => (
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
                  <TableCell>
                    {customers.find(c => c.id === contract.customer_id)?.company_name || 'Unknown'}
                  </TableCell>
                  <TableCell>{getTypeLabel(contract.contract_type)}</TableCell>
                  <TableCell>
                    <Chip
                      label={contract.status.replace('_', ' ')}
                      size="small"
                      color={getStatusColor(contract.status) as any}
                    />
                  </TableCell>
                  <TableCell>{new Date(contract.start_date).toLocaleDateString()}</TableCell>
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
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Contract Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Contract</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Customer *</InputLabel>
              <Select
                value={newContract.customer_id}
                label="Customer *"
                onChange={(e) => setNewContract({ ...newContract, customer_id: e.target.value })}
              >
                {customers.map((customer) => (
                  <MenuItem key={customer.id} value={customer.id}>
                    {customer.company_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Contract Name *"
              fullWidth
              value={newContract.contract_name}
              onChange={(e) => setNewContract({ ...newContract, contract_name: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Contract Type *</InputLabel>
              <Select
                value={newContract.contract_type}
                label="Contract Type *"
                onChange={(e) => setNewContract({ ...newContract, contract_type: e.target.value })}
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
              value={newContract.start_date}
              onChange={(e) => setNewContract({ ...newContract, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateContract}
            variant="contained"
            disabled={!newContract.customer_id || !newContract.contract_name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Contracts;

