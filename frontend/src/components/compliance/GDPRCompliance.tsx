import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Policy,
  FileDownload,
  Add,
  Refresh,
  CheckCircle,
  Schedule,
} from '@mui/icons-material';
import { complianceAPI } from '../../services/api';

interface PrivacyPolicy {
  id: string;
  version: string;
  title: string;
  content: string;
  is_active: boolean;
  generated_by_ai: boolean;
  effective_date: string;
  next_review_date?: string;
}

interface SAR {
  id: string;
  requestor_email: string;
  status: string;
  request_date: string;
  due_date?: string;
  verified: boolean;
}

const GDPRCompliance: React.FC = () => {
  const [policies, setPolicies] = useState<PrivacyPolicy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<PrivacyPolicy | null>(null);
  const [sarDialogOpen, setSarDialogOpen] = useState(false);
  const [sarEmail, setSarEmail] = useState('');
  const [sarName, setSarName] = useState('');

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await complianceAPI.listPrivacyPolicies();
      setPolicies(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load privacy policies');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePolicy = async (useAI: boolean = true) => {
    setGenerating(true);
    setError(null);
    try {
      const policy = await complianceAPI.generatePrivacyPolicy(useAI);
      setPolicies([policy, ...policies]);
      setSelectedPolicy(policy);
      setPolicyDialogOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate privacy policy');
    } finally {
      setGenerating(false);
    }
  };

  const handleCreateSAR = async () => {
    if (!sarEmail) {
      setError('Email is required');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await complianceAPI.createSAR({
        requestor_email: sarEmail,
        requestor_name: sarName || undefined,
      });
      setSarDialogOpen(false);
      setSarEmail('');
      setSarName('');
      alert('Subject Access Request created. Please check your email for verification.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create SAR');
    } finally {
      setLoading(false);
    }
  };

  const handleViewPolicy = (policy: PrivacyPolicy) => {
    setSelectedPolicy(policy);
    setPolicyDialogOpen(true);
  };

  const handleDownloadPolicy = (policy: PrivacyPolicy) => {
    const blob = new Blob([policy.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `privacy-policy-v${policy.version}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Privacy Policy Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Privacy Policy Management</Typography>
                <Box>
                  <Button
                    variant="outlined"
                    startIcon={<Policy />}
                    onClick={() => handleGeneratePolicy(true)}
                    disabled={generating}
                    sx={{ mr: 1 }}
                  >
                    {generating ? 'Generating...' : 'Generate with AI'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={fetchPolicies}
                    disabled={loading}
                  >
                    Refresh
                  </Button>
                </Box>
              </Box>

              {loading && policies.length === 0 ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : policies.length === 0 ? (
                <Alert severity="info">
                  No privacy policies found. Generate one to get started.
                </Alert>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Version</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Generated</TableCell>
                        <TableCell>Effective Date</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {policies.map((policy) => (
                        <TableRow key={policy.id}>
                          <TableCell>{policy.version}</TableCell>
                          <TableCell>{policy.title}</TableCell>
                          <TableCell>
                            <Chip
                              label={policy.is_active ? 'Active' : 'Inactive'}
                              color={policy.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {policy.generated_by_ai ? (
                              <Chip label="AI Generated" color="primary" size="small" />
                            ) : (
                              'Manual'
                            )}
                          </TableCell>
                          <TableCell>
                            {new Date(policy.effective_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              onClick={() => handleViewPolicy(policy)}
                            >
                              <Policy />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadPolicy(policy)}
                            >
                              <FileDownload />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Subject Access Request Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Subject Access Request (SAR)</Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setSarDialogOpen(true)}
                >
                  Create SAR
                </Button>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Users can request a copy of all their personal data stored in the system.
                This is required by GDPR Article 15.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Policy View Dialog */}
      <Dialog
        open={policyDialogOpen}
        onClose={() => setPolicyDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedPolicy?.title}
          {selectedPolicy?.is_active && (
            <Chip label="Active" color="success" size="small" sx={{ ml: 2 }} />
          )}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {selectedPolicy?.content}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPolicyDialogOpen(false)}>Close</Button>
          {selectedPolicy && (
            <Button
              startIcon={<FileDownload />}
              onClick={() => handleDownloadPolicy(selectedPolicy)}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* SAR Creation Dialog */}
      <Dialog open={sarDialogOpen} onClose={() => setSarDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Subject Access Request</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Requestor Email"
            type="email"
            value={sarEmail}
            onChange={(e) => setSarEmail(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Requestor Name (Optional)"
            value={sarName}
            onChange={(e) => setSarName(e.target.value)}
            margin="normal"
          />
          <Alert severity="info" sx={{ mt: 2 }}>
            A verification email will be sent to the requestor. They must verify their email
            before the data export can be generated.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSarDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateSAR}
            disabled={!sarEmail || loading}
          >
            Create SAR
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GDPRCompliance;

