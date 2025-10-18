import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Tooltip,
  Checkbox
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';

const Competitors: React.FC = () => {
  const navigate = useNavigate();
  const [competitors, setCompetitors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCompetitors, setSelectedCompetitors] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadCompetitors();
  }, []);

  const loadCompetitors = async () => {
    try {
      setLoading(true);
      const response = await customerAPI.getCompetitors();
      setCompetitors(response.data);
    } catch (error) {
      console.error('Failed to load competitors:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCompetitors = competitors.filter(comp =>
    comp.company_name.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success'> = {
      'LEAD': 'info',
      'PROSPECT': 'warning',
      'OPPORTUNITY': 'primary',
      'CUSTOMER': 'success',
      'COLD_LEAD': 'default',
      'INACTIVE': 'default',
      'LOST': 'error'
    };
    return colors[status] || 'default';
  };

  const handleSelectCompetitor = (competitorId: string) => {
    const newSelected = new Set(selectedCompetitors);
    if (newSelected.has(competitorId)) {
      newSelected.delete(competitorId);
    } else {
      newSelected.add(competitorId);
    }
    setSelectedCompetitors(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedCompetitors.size === filteredCompetitors.length) {
      setSelectedCompetitors(new Set());
    } else {
      setSelectedCompetitors(new Set(filteredCompetitors.map(c => c.id)));
    }
  };

  const handleAddAllToLeadCampaign = async () => {
    if (selectedCompetitors.size === 0) {
      alert('Please select at least one competitor');
      return;
    }

    // Navigate to company list import campaign creation
    const selectedCompanyIds = Array.from(selectedCompetitors);
    navigate('/campaigns/create', {
      state: {
        type: 'company_list_import',
        companies: selectedCompanyIds
      }
    });
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Clean Centered Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Competitors
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Competitor analysis and tracking
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/customers/new')}
            sx={{ 
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            Add Competitor
          </Button>
        </Box>
      </Box>

        {/* Search */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search competitors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {/* Stats and Actions */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, gap: 2 }}>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6" color="primary">
                  Total Competitors: {filteredCompetitors.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {selectedCompetitors.size > 0 ? `${selectedCompetitors.size} selected` : 'Companies marked as competitors'}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Add to Campaign Button */}
          {selectedCompetitors.size > 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<UploadIcon />}
              onClick={handleAddAllToLeadCampaign}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                px: 3,
                py: 1.5
              }}
            >
              Add {selectedCompetitors.size} to Campaign
            </Button>
          )}
        </Box>

        {/* Competitors Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.light' }}>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedCompetitors.size > 0 && selectedCompetitors.size < filteredCompetitors.length}
                    checked={selectedCompetitors.size === filteredCompetitors.length && filteredCompetitors.length > 0}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell><strong>Company Name</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Sector</strong></TableCell>
                <TableCell><strong>Size</strong></TableCell>
                <TableCell><strong>Website</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    Loading competitors...
                  </TableCell>
                </TableRow>
              ) : filteredCompetitors.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary">
                      No competitors found. Mark customers as competitors in the CRM to track them here.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCompetitors.map((competitor) => (
                  <TableRow 
                    key={competitor.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedCompetitors.has(competitor.id)}
                        onChange={() => handleSelectCompetitor(competitor.id)}
                      />
                    </TableCell>
                    <TableCell onClick={() => navigate(`/customers/${competitor.id}`)}>
                      <Typography variant="body2" fontWeight="medium">
                        {competitor.company_name}
                      </Typography>
                    </TableCell>
                    <TableCell onClick={() => navigate(`/customers/${competitor.id}`)}>
                      <Chip
                        label={competitor.status}
                        color={getStatusColor(competitor.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell onClick={() => navigate(`/customers/${competitor.id}`)}>
                      {competitor.business_sector ? (
                        <Chip label={competitor.business_sector} size="small" variant="outlined" />
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell onClick={() => navigate(`/customers/${competitor.id}`)}>
                      {competitor.business_size ? (
                        <Typography variant="body2">{competitor.business_size}</Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell onClick={() => navigate(`/customers/${competitor.id}`)}>
                      {competitor.website ? (
                        <a href={competitor.website} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                          <Typography variant="body2" color="primary">Visit</Typography>
                        </a>
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/customers/${competitor.id}`);
                          }}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
    </Container>
  );
};

export default Competitors;



