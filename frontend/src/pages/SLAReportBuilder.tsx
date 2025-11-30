import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  GetApp as DownloadIcon,
  FilterList as FilterIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { slaAPI, customerAPI } from '../services/api';

interface ReportConfig {
  reportType: 'sla_compliance' | 'customer_sla' | 'agent_performance' | 'breach_analysis' | 'trends';
  dateRange: {
    start: string;
    end: string;
  };
  filters: {
    customerIds?: string[];
    policyIds?: string[];
    priorities?: string[];
    ticketTypes?: string[];
    includeResolved?: boolean;
    includeOpen?: boolean;
  };
  metrics: {
    complianceRate: boolean;
    breachCount: boolean;
    averageResponseTime: boolean;
    averageResolutionTime: boolean;
    agentPerformance: boolean;
    customerBreakdown: boolean;
  };
  format: 'csv' | 'pdf' | 'excel';
}

const SLAReportBuilder: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reportConfig, setReportConfig] = useState<ReportConfig>({
    reportType: 'sla_compliance',
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    filters: {
      includeResolved: true,
      includeOpen: true
    },
    metrics: {
      complianceRate: true,
      breachCount: true,
      averageResponseTime: true,
      averageResolutionTime: true,
      agentPerformance: false,
      customerBreakdown: false
    },
    format: 'csv'
  });
  const [customers, setCustomers] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [previewData, setPreviewData] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    loadCustomers();
    loadPolicies();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await customerAPI.list({ limit: 1000 });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const loadPolicies = async () => {
    try {
      const response = await slaAPI.listPolicies();
      setPolicies(response.data || []);
    } catch (error) {
      console.error('Error loading policies:', error);
    }
  };

  const handleGeneratePreview = async () => {
    try {
      setLoading(true);
      // Generate preview based on report type
      const response = await slaAPI.getCompliance({
        start_date: reportConfig.dateRange.start,
        end_date: reportConfig.dateRange.end
      });
      setPreviewData(response.data);
      setTabValue(1);
    } catch (error) {
      console.error('Error generating preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async () => {
    try {
      setLoading(true);
      const response = await slaAPI.exportReport({
        start_date: reportConfig.dateRange.start,
        end_date: reportConfig.dateRange.end,
        format: reportConfig.format,
        ...reportConfig.filters,
        metrics: reportConfig.metrics
      });

      // Create download link
      const blob = new Blob([response.data], {
        type: reportConfig.format === 'pdf' ? 'application/pdf' :
              reportConfig.format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' :
              'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sla_report_${reportConfig.dateRange.start}_${reportConfig.dateRange.end}.${reportConfig.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssessmentIcon /> SLA Report Builder
        </Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExportReport}
          disabled={loading}
        >
          Export Report
        </Button>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Configure Report" />
          <Tab label="Preview" />
        </Tabs>
      </Paper>

      {tabValue === 0 && (
        <Grid container spacing={3}>
          {/* Report Type */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Report Type
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Report Type</InputLabel>
                  <Select
                    value={reportConfig.reportType}
                    label="Report Type"
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      reportType: e.target.value as any
                    })}
                  >
                    <MenuItem value="sla_compliance">SLA Compliance</MenuItem>
                    <MenuItem value="customer_sla">Customer SLA Summary</MenuItem>
                    <MenuItem value="agent_performance">Agent Performance</MenuItem>
                    <MenuItem value="breach_analysis">Breach Analysis</MenuItem>
                    <MenuItem value="trends">Historical Trends</MenuItem>
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>

          {/* Date Range */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Date Range
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexDirection: 'column' }}>
                  <TextField
                    label="Start Date"
                    type="date"
                    value={reportConfig.dateRange.start}
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      dateRange: { ...reportConfig.dateRange, start: e.target.value }
                    })}
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                  />
                  <TextField
                    label="End Date"
                    type="date"
                    value={reportConfig.dateRange.end}
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      dateRange: { ...reportConfig.dateRange, end: e.target.value }
                    })}
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Metrics Selection */}
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Metrics to Include
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.complianceRate}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, complianceRate: e.target.checked }
                          })}
                        />
                      }
                      label="Compliance Rate"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.breachCount}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, breachCount: e.target.checked }
                          })}
                        />
                      }
                      label="Breach Count"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.averageResponseTime}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, averageResponseTime: e.target.checked }
                          })}
                        />
                      }
                      label="Average Response Time"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.averageResolutionTime}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, averageResolutionTime: e.target.checked }
                          })}
                        />
                      }
                      label="Average Resolution Time"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.agentPerformance}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, agentPerformance: e.target.checked }
                          })}
                        />
                      }
                      label="Agent Performance"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={reportConfig.metrics.customerBreakdown}
                          onChange={(e) => setReportConfig({
                            ...reportConfig,
                            metrics: { ...reportConfig.metrics, customerBreakdown: e.target.checked }
                          })}
                        />
                      }
                      label="Customer Breakdown"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Export Format */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Export Format
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Format</InputLabel>
                  <Select
                    value={reportConfig.format}
                    label="Format"
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      format: e.target.value as 'csv' | 'pdf' | 'excel'
                    })}
                  >
                    <MenuItem value="csv">CSV</MenuItem>
                    <MenuItem value="pdf">PDF</MenuItem>
                    <MenuItem value="excel">Excel</MenuItem>
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>

          {/* Actions */}
          <Grid size={{ xs: 12 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={handleGeneratePreview}
                disabled={loading}
              >
                Generate Preview
              </Button>
            </Box>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && previewData && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Report Preview
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            This is a preview of the report data. Export to see the full report in your selected format.
          </Alert>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Metric</strong></TableCell>
                  <TableCell align="right"><strong>Value</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Total Tickets</TableCell>
                  <TableCell align="right">{previewData.total_tickets}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>First Response Compliance Rate</TableCell>
                  <TableCell align="right">{previewData.first_response?.compliance_rate?.toFixed(1)}%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Resolution Compliance Rate</TableCell>
                  <TableCell align="right">{previewData.resolution?.compliance_rate?.toFixed(1)}%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Total Breaches</TableCell>
                  <TableCell align="right">
                    {(previewData.first_response?.breached || 0) + (previewData.resolution?.breached || 0)}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}
    </Container>
  );
};

export default SLAReportBuilder;

