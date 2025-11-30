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
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Assessment as AssessmentIcon,
  Schedule as ScheduleIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Flag as FlagIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';
import CustomerFormSimple from '../components/CustomerFormSimple';

const Customers: React.FC = () => {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<any>(null);
  const [sortBy, setSortBy] = useState<string>('company_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const response = await customerAPI.list();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error loading customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCustomers = customers.filter(customer =>
    customer.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (customer.website && customer.website.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const sortedCustomers = [...filteredCustomers].sort((a, b) => {
    let aVal: any;
    let bVal: any;

    switch (sortBy) {
      case 'company_name':
        aVal = a.company_name?.toLowerCase() || '';
        bVal = b.company_name?.toLowerCase() || '';
        break;
      case 'lead_score':
        aVal = a.lead_score || 0;
        bVal = b.lead_score || 0;
        break;
      case 'last_contact_date':
        aVal = a.last_contact_date ? new Date(a.last_contact_date).getTime() : 0;
        bVal = b.last_contact_date ? new Date(b.last_contact_date).getTime() : 0;
        break;
      case 'next_scheduled_contact':
        aVal = a.next_scheduled_contact ? new Date(a.next_scheduled_contact).getTime() : 0;
        bVal = b.next_scheduled_contact ? new Date(b.next_scheduled_contact).getTime() : 0;
        break;
      case 'business_sector':
        aVal = a.business_sector?.toLowerCase() || '';
        bVal = b.business_sector?.toLowerCase() || '';
        break;
      default:
        return 0;
    }

    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const handleAddCustomer = () => {
    setEditingCustomer(null);
    setShowCustomerForm(true);
  };

  const handleEditCustomer = (customer: any) => {
    setEditingCustomer(customer);
    setShowCustomerForm(true);
  };

  const handleSaveCustomer = async (customerData: any) => {
    try {
      if (editingCustomer) {
        // Update existing customer
        await customerAPI.update(editingCustomer.id, customerData);
      } else {
        // Create new customer
        await customerAPI.create(customerData);
      }
      setShowCustomerForm(false);
      setEditingCustomer(null);
      loadCustomers(); // Refresh the list
    } catch (error) {
      console.error('Error saving customer:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'lead':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Clean Centered Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Customers
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Comprehensive Customer Relationship Management
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddCustomer}
            sx={{ 
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            Add Customer
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search customers..."
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
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>SLA</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('company_name')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Company Name</strong>
                  {sortBy === 'company_name' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Website</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('business_sector')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Business Type</strong>
                  {sortBy === 'business_sector' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Status</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('lead_score')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Lead Score</strong>
                  {sortBy === 'lead_score' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('last_contact_date')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Last Contact</strong>
                  {sortBy === 'last_contact_date' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('next_scheduled_contact')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Next Action</strong>
                  {sortBy === 'next_scheduled_contact' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : sortedCustomers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  No customers found
                </TableCell>
              </TableRow>
            ) : (
              sortedCustomers.map((customer) => {
                const hasScheduledContact = customer.next_scheduled_contact && new Date(customer.next_scheduled_contact) > new Date();
                const isUpcoming = hasScheduledContact && new Date(customer.next_scheduled_contact) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
                
                return (
                <TableRow 
                  key={customer.id} 
                  hover
                  sx={{ 
                    backgroundColor: hasScheduledContact ? (isUpcoming ? 'rgba(255, 193, 7, 0.1)' : 'rgba(76, 175, 80, 0.05)') : 'inherit'
                  }}
                >
                  <TableCell>
                    <Tooltip title={
                      customer.sla_breach_status === 'critical' ? 'Critical SLA breach' :
                      customer.sla_breach_status === 'warning' ? 'SLA warning' :
                      'No SLA breaches'
                    }>
                      <FlagIcon 
                        sx={{ 
                          color: customer.sla_breach_status === 'critical' ? '#f44336' :
                                 customer.sla_breach_status === 'warning' ? '#ff9800' :
                                 '#4caf50',
                          fontSize: 20
                        }} 
                      />
                    </Tooltip>
                  </TableCell>
                  <TableCell>{customer.company_name}</TableCell>
                  <TableCell>
                    {customer.website ? (
                      <a href={customer.website} target="_blank" rel="noopener noreferrer">
                        {customer.website}
                      </a>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>{customer.business_type || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={customer.status}
                      color={getStatusColor(customer.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {customer.lead_score ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={customer.lead_score}
                          sx={{
                            width: 60,
                            height: 8,
                            borderRadius: 4,
                            backgroundColor: '#e0e0e0',
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: getScoreColor(customer.lead_score),
                              borderRadius: 4
                            }
                          }}
                        />
                        <Typography variant="body2" sx={{ minWidth: 30 }}>
                          {customer.lead_score}
                        </Typography>
                      </Box>
                    ) : (
                      <Chip label="No Score" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell>
                    {customer.last_contact_date ? (
                      <Typography variant="body2">
                        {new Date(customer.last_contact_date).toLocaleDateString()}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">Never</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {customer.next_scheduled_contact ? (
                      <Box>
                        <Chip
                          label={new Date(customer.next_scheduled_contact).toLocaleDateString()}
                          size="small"
                          color={isUpcoming ? 'warning' : 'success'}
                          icon={<ScheduleIcon fontSize="small" />}
                        />
                        {isUpcoming && (
                          <Typography variant="caption" color="warning.main" sx={{ display: 'block', mt: 0.5 }}>
                            Upcoming
                          </Typography>
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">None scheduled</Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/customers/${customer.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                    <Tooltip title="Edit Customer">
                      <IconButton
                        size="small"
                        onClick={() => handleEditCustomer(customer)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    {customer.ai_analysis && (
                      <Tooltip title="View AI Analysis">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/customers/${customer.id}/analysis`)}
                        >
                          <AssessmentIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Total: {filteredCustomers.length} customers
        </Typography>
      </Box>

      {/* Customer Form Dialog */}
      <CustomerFormSimple
        open={showCustomerForm}
        onClose={() => {
          setShowCustomerForm(false);
          setEditingCustomer(null);
        }}
        onSave={handleSaveCustomer}
      />
    </Container>
  );
};

export default Customers;

