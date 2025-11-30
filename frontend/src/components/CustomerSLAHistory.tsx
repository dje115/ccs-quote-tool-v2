import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  LinearProgress,
  Chip,
  TextField,
  Button
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import { slaAPI } from '../services/api';

interface CustomerSLAHistoryProps {
  customerId: string;
}

const CustomerSLAHistory: React.FC<CustomerSLAHistoryProps> = ({ customerId }) => {
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    loadHistory();
  }, [customerId, startDate, endDate]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await slaAPI.getCustomerComplianceHistory(customerId, {
        start_date: startDate,
        end_date: endDate
      });
      setHistory(response.data);
    } catch (err: any) {
      console.error('Error loading SLA history:', err);
      setError(err.response?.data?.detail || 'Failed to load SLA compliance history');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!history || !history.daily_compliance || history.daily_compliance.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No SLA compliance history available for this period.</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6">SLA Compliance History</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <TextField
              type="date"
              label="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ width: 150 }}
            />
            <TextField
              type="date"
              label="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ width: 150 }}
            />
            <Button variant="outlined" size="small" onClick={loadHistory}>
              Refresh
            </Button>
          </Box>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Period: {new Date(history.period.start).toLocaleDateString()} - {new Date(history.period.end).toLocaleDateString()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Records: {history.total_records}
          </Typography>
        </Box>

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Date</strong></TableCell>
                <TableCell align="center"><strong>Total Checks</strong></TableCell>
                <TableCell align="center"><strong>Compliant</strong></TableCell>
                <TableCell align="center"><strong>Breached</strong></TableCell>
                <TableCell align="center"><strong>Compliance Rate</strong></TableCell>
                <TableCell align="center"><strong>Trend</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.daily_compliance.map((day: any, index: number) => {
                const complianceRate = day.total_checks > 0 
                  ? ((day.compliant / day.total_checks) * 100).toFixed(1)
                  : '100.0';
                
                // Compare with previous day
                const prevDay = index < history.daily_compliance.length - 1 
                  ? history.daily_compliance[index + 1] 
                  : null;
                const prevRate = prevDay && prevDay.total_checks > 0
                  ? (prevDay.compliant / prevDay.total_checks) * 100
                  : null;
                const trend = prevRate !== null 
                  ? (parseFloat(complianceRate) - prevRate) 
                  : null;

                return (
                  <TableRow key={day.date} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CalendarIcon fontSize="small" color="action" />
                        {new Date(day.date).toLocaleDateString()}
                      </Box>
                    </TableCell>
                    <TableCell align="center">{day.total_checks}</TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={day.compliant} 
                        color="success" 
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={day.breached} 
                        color={day.breached > 0 ? 'error' : 'default'} 
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center' }}>
                        <Typography variant="body2" fontWeight="medium">
                          {complianceRate}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={parseFloat(complianceRate)}
                          sx={{
                            width: 60,
                            height: 6,
                            borderRadius: 3,
                            backgroundColor: '#e0e0e0',
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: parseFloat(complianceRate) >= 95 ? '#4caf50' :
                                               parseFloat(complianceRate) >= 80 ? '#ff9800' : '#f44336',
                              borderRadius: 3
                            }
                          }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      {trend !== null && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'center' }}>
                          {trend > 0 ? (
                            <>
                              <TrendingUpIcon fontSize="small" color="success" />
                              <Typography variant="caption" color="success.main">
                                +{trend.toFixed(1)}%
                              </Typography>
                            </>
                          ) : trend < 0 ? (
                            <>
                              <TrendingDownIcon fontSize="small" color="error" />
                              <Typography variant="caption" color="error.main">
                                {trend.toFixed(1)}%
                              </Typography>
                            </>
                          ) : (
                            <Typography variant="caption" color="text.secondary">
                              No change
                            </Typography>
                          )}
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default CustomerSLAHistory;

