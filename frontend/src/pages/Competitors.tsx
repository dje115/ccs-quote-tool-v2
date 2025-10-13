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
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';

const Competitors: React.FC = () => {
  const navigate = useNavigate();
  const [competitors, setCompetitors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

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

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Competitors
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Competitor analysis and tracking
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/customers/new')}
          >
            Add Competitor
          </Button>
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

        {/* Stats */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" color="primary">
            Total Competitors: {filteredCompetitors.length}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Companies marked as competitors for competitive analysis
          </Typography>
        </Paper>

        {/* Competitors Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.light' }}>
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
                  <TableCell colSpan={6} align="center">
                    Loading competitors...
                  </TableCell>
                </TableRow>
              ) : filteredCompetitors.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
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
                    onClick={() => navigate(`/customers/${competitor.id}`)}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {competitor.company_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={competitor.status}
                        color={getStatusColor(competitor.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {competitor.business_sector ? (
                        <Chip label={competitor.business_sector} size="small" variant="outlined" />
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {competitor.business_size ? (
                        <Typography variant="body2">{competitor.business_size}</Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {competitor.website ? (
                        <a href={competitor.website} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                          <Typography variant="body2" color="primary">Visit</Typography>
                        </a>
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
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
      </Box>
    </Container>
  );
};

export default Competitors;

