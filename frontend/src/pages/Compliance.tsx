import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Alert,
  CircularProgress,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Gavel as GavelIcon,
  VerifiedUser as VerifiedUserIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  ContentCopy as ContentCopyIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { complianceAPI } from '../services/api';

interface SecurityEvent {
  id: string;
  event_type: string;
  severity: string;
  description: string;
  ip_address?: string;
  user_agent?: string;
  occurred_at: string;
  resolved?: string;
  resolved_at?: string;
}

interface SecurityStatistics {
  total_events: number;
  by_type: Record<string, number>;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  failed_logins: number;
  account_lockouts: number;
  rate_limit_exceeded: number;
}

interface DataCollectionAnalysis {
  data_categories: Record<string, any>;
  data_retention: Record<string, string>;
  data_sharing: Record<string, any>;
  data_subject_rights: Record<string, string>;
  security_measures: string[];
  last_updated: string;
}

interface SARExport {
  export_date: string;
  user_id: string;
  tenant_id: string;
  data: Record<string, any>;
}

const Compliance: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Security Dashboard State
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [securityStats, setSecurityStats] = useState<SecurityStatistics | null>(null);
  const [eventsLoading, setEventsLoading] = useState(false);

  // GDPR State
  const [dataAnalysis, setDataAnalysis] = useState<DataCollectionAnalysis | null>(null);
  const [policyText, setPolicyText] = useState<string>('');
  const [policyLoading, setPolicyLoading] = useState(false);
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false);
  const [includeISO, setIncludeISO] = useState(false);
  const [sarExport, setSarExport] = useState<SARExport | null>(null);
  const [sarLoading, setSarLoading] = useState(false);
  const [sarDialogOpen, setSarDialogOpen] = useState(false);

  // Load security events
  const loadSecurityEvents = async () => {
    setEventsLoading(true);
    setError(null);
    try {
      const [events, stats] = await Promise.all([
        complianceAPI.getSecurityEvents({ hours: 24, limit: 100 }),
        complianceAPI.getSecurityStatistics({ hours: 24 }),
      ]);
      setSecurityEvents(events);
      setSecurityStats(stats);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load security events');
    } finally {
      setEventsLoading(false);
    }
  };

  // Load GDPR data analysis
  const loadDataAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const analysis = await complianceAPI.getDataCollectionAnalysis();
      setDataAnalysis(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data analysis');
    } finally {
      setLoading(false);
    }
  };

  // Generate GDPR policy
  const generatePolicy = async () => {
    setPolicyLoading(true);
    setError(null);
    try {
      const response = await complianceAPI.generateGDPRPolicy({ include_iso_sections: includeISO });
      setPolicyText(response.policy);
      setPolicyDialogOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate policy');
    } finally {
      setPolicyLoading(false);
    }
  };

  // Generate SAR export
  const generateSARExport = async () => {
    setSarLoading(true);
    setError(null);
    try {
      const export_data = await complianceAPI.getSARExport();
      setSarExport(export_data);
      setSarDialogOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate SAR export');
    } finally {
      setSarLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 0) {
      loadSecurityEvents();
    } else if (activeTab === 1) {
      loadDataAnalysis();
    }
  }, [activeTab]);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const downloadJSON = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Compliance & Security
      </Typography>

      <Paper sx={{ mt: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<SecurityIcon />} iconPosition="start" label="Security Dashboard" />
          <Tab icon={<GavelIcon />} iconPosition="start" label="GDPR" />
          <Tab icon={<VerifiedUserIcon />} iconPosition="start" label="ISO Standards" disabled />
        </Tabs>

        {/* Security Dashboard Tab */}
        {activeTab === 0 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Security Events & Monitoring</Typography>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadSecurityEvents}
                disabled={eventsLoading}
              >
                Refresh
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {eventsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                {/* Statistics Cards */}
                {securityStats && (
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Total Events (24h)
                          </Typography>
                          <Typography variant="h4">{securityStats.total_events}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Failed Logins
                          </Typography>
                          <Typography variant="h4" color="error">
                            {securityStats.failed_logins}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Account Lockouts
                          </Typography>
                          <Typography variant="h4" color="warning.main">
                            {securityStats.account_lockouts}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Rate Limit Violations
                          </Typography>
                          <Typography variant="h4" color="info.main">
                            {securityStats.rate_limit_exceeded}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                )}

                {/* Events Table */}
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>IP Address</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {securityEvents.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center">
                            No security events in the last 24 hours
                          </TableCell>
                        </TableRow>
                      ) : (
                        securityEvents.map((event) => (
                          <TableRow key={event.id}>
                            <TableCell>
                              {new Date(event.occurred_at).toLocaleString()}
                            </TableCell>
                            <TableCell>{event.event_type.replace(/_/g, ' ')}</TableCell>
                            <TableCell>
                              <Chip
                                label={event.severity}
                                color={getSeverityColor(event.severity) as any}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>{event.description}</TableCell>
                            <TableCell>{event.ip_address || 'N/A'}</TableCell>
                            <TableCell>
                              {event.resolved ? (
                                <Chip
                                  icon={<CheckCircleIcon />}
                                  label="Resolved"
                                  color="success"
                                  size="small"
                                />
                              ) : (
                                <Chip
                                  icon={<WarningIcon />}
                                  label="Active"
                                  color="warning"
                                  size="small"
                                />
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Box>
        )}

        {/* GDPR Tab */}
        {activeTab === 1 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              GDPR Compliance Tools
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            <Grid container spacing={3}>
              {/* Data Collection Analysis */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Data Collection Analysis
                    </Typography>
                    {loading ? (
                      <CircularProgress />
                    ) : dataAnalysis ? (
                      <Box>
                        <Typography variant="body2" color="textSecondary" paragraph>
                          Last Updated: {new Date(dataAnalysis.last_updated).toLocaleString()}
                        </Typography>
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Data Categories:
                          </Typography>
                          {Object.keys(dataAnalysis.data_categories).map((category) => (
                            <Chip
                              key={category}
                              label={category.replace(/_/g, ' ')}
                              sx={{ mr: 1, mb: 1 }}
                              size="small"
                            />
                          ))}
                        </Box>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={loadDataAnalysis}
                          sx={{ mt: 2 }}
                        >
                          Refresh Analysis
                        </Button>
                      </Box>
                    ) : (
                      <Button variant="outlined" onClick={loadDataAnalysis}>
                        Load Data Analysis
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* GDPR Policy Generator */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Privacy Policy Generator
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Generate a GDPR-compliant privacy policy based on your data collection practices.
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <label>
                        <input
                          type="checkbox"
                          checked={includeISO}
                          onChange={(e) => setIncludeISO(e.target.checked)}
                          style={{ marginRight: 8 }}
                        />
                        Include ISO 27001 & ISO 9001 references
                      </label>
                    </Box>
                    <Button
                      variant="contained"
                      onClick={generatePolicy}
                      disabled={policyLoading}
                      fullWidth
                    >
                      {policyLoading ? <CircularProgress size={24} /> : 'Generate Policy'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              {/* SAR Tool */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Subject Access Request (SAR) Tool
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Generate a data export for GDPR Subject Access Requests. This exports all personal data
                      associated with your account.
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<DownloadIcon />}
                      onClick={generateSARExport}
                      disabled={sarLoading}
                    >
                      {sarLoading ? 'Generating...' : 'Generate SAR Export'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* ISO Standards Tab */}
        {activeTab === 2 && (
          <Box sx={{ p: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              ISO 27001 (Information Security) and ISO 9001 (Quality Management) modules coming soon.
            </Alert>
            <Typography variant="h6" gutterBottom>
              ISO 27001 - Information Security Management
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              This module will help you:
            </Typography>
            <ul>
              <li>Document information security policies and procedures</li>
              <li>Conduct risk assessments and manage security risks</li>
              <li>Track security controls and compliance</li>
              <li>Generate ISO 27001 audit reports</li>
            </ul>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
              ISO 9001 - Quality Management System
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              This module will help you:
            </Typography>
            <ul>
              <li>Document quality management processes</li>
              <li>Track quality objectives and metrics</li>
              <li>Manage non-conformities and corrective actions</li>
              <li>Generate ISO 9001 audit reports</li>
            </ul>
          </Box>
        )}
      </Paper>

      {/* GDPR Policy Dialog */}
      <Dialog
        open={policyDialogOpen}
        onClose={() => setPolicyDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Generated GDPR Privacy Policy
          <IconButton
            onClick={() => copyToClipboard(policyText)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <ContentCopyIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            multiline
            fullWidth
            rows={20}
            value={policyText}
            variant="outlined"
            InputProps={{
              readOnly: true,
            }}
            sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => downloadJSON({ policy: policyText }, 'gdpr-policy.json')}>
            Download JSON
          </Button>
          <Button onClick={() => {
            const blob = new Blob([policyText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'gdpr-privacy-policy.txt';
            a.click();
            URL.revokeObjectURL(url);
          }}>
            Download Text
          </Button>
          <Button onClick={() => setPolicyDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* SAR Export Dialog */}
      <Dialog
        open={sarDialogOpen}
        onClose={() => setSarDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Subject Access Request Export
          <IconButton
            onClick={() => sarExport && copyToClipboard(JSON.stringify(sarExport, null, 2))}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <ContentCopyIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {sarExport && (
            <Box>
              <Typography variant="body2" color="textSecondary" paragraph>
                Export Date: {new Date(sarExport.export_date).toLocaleString()}
              </Typography>
              <TextField
                multiline
                fullWidth
                rows={15}
                value={JSON.stringify(sarExport, null, 2)}
                variant="outlined"
                InputProps={{
                  readOnly: true,
                }}
                sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => sarExport && downloadJSON(sarExport, `sar-export-${Date.now()}.json`)}
          >
            Download JSON
          </Button>
          <Button onClick={() => setSarDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Compliance;
