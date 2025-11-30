import React, { useEffect, useState } from 'react';
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
  Grid,
  Switch,
  FormControlLabel,
  Alert,
  Tabs,
  Tab,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { slaAPI } from '../services/api';

interface SLAPolicy {
  id: string;
  name: string;
  description?: string;
  sla_level?: string;
  first_response_hours?: number;
  resolution_hours?: number;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
}

const SLAManagement: React.FC = () => {
  const navigate = useNavigate();
  const [policies, setPolicies] = useState<SLAPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<SLAPolicy | null>(null);
  const [notificationDialogOpen, setNotificationDialogOpen] = useState(false);
  const [selectedPolicyForNotifications, setSelectedPolicyForNotifications] = useState<SLAPolicy | null>(null);
  const [notificationSettings, setNotificationSettings] = useState({
    warning_threshold: 80,
    critical_threshold: 95,
    auto_escalate: true
  });
  const [tabValue, setTabValue] = useState(0);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    sla_level: '',
    first_response_hours: '',
    resolution_hours: '',
    is_active: true,
    is_default: false
  });

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const response = await slaAPI.listPolicies();
      setPolicies(response.data || []);
    } catch (error) {
      console.error('Error loading SLA policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (policy?: SLAPolicy) => {
    if (policy) {
      setEditingPolicy(policy);
      setFormData({
        name: policy.name,
        description: policy.description || '',
        sla_level: policy.sla_level || '',
        first_response_hours: policy.first_response_hours?.toString() || '',
        resolution_hours: policy.resolution_hours?.toString() || '',
        is_active: policy.is_active,
        is_default: policy.is_default
      });
    } else {
      setEditingPolicy(null);
      setFormData({
        name: '',
        description: '',
        sla_level: '',
        first_response_hours: '',
        resolution_hours: '',
        is_active: true,
        is_default: false
      });
    }
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      const data = {
        name: formData.name,
        description: formData.description || null,
        sla_level: formData.sla_level || null,
        first_response_hours: formData.first_response_hours ? parseInt(formData.first_response_hours) : null,
        resolution_hours: formData.resolution_hours ? parseInt(formData.resolution_hours) : null,
        is_active: formData.is_active,
        is_default: formData.is_default
      };

      if (editingPolicy) {
        await slaAPI.updatePolicy(editingPolicy.id, data);
      } else {
        await slaAPI.createPolicy(data);
      }

      setDialogOpen(false);
      loadPolicies();
    } catch (error) {
      console.error('Error saving SLA policy:', error);
      alert('Failed to save SLA policy');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this SLA policy?')) {
      return;
    }

    try {
      await slaAPI.deletePolicy(id);
      loadPolicies();
    } catch (error) {
      console.error('Error deleting SLA policy:', error);
      alert('Failed to delete SLA policy');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssessmentIcon /> SLA Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/sla/dashboard')}
          >
            View Dashboard
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={async () => {
              setLoadingTemplates(true);
              try {
                const response = await slaAPI.listTemplates();
                setTemplates(response.data || []);
                setTemplateDialogOpen(true);
              } catch (error) {
                console.error('Error loading templates:', error);
                alert('Failed to load templates');
              } finally {
                setLoadingTemplates(false);
              }
            }}
          >
            Create from Template
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Custom Policy
          </Button>
        </Box>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Policies" />
          <Tab label="Notification Rules" />
        </Tabs>
      </Paper>

      {tabValue === 0 && (
        <TableContainer component={Paper}>
          <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Name</strong></TableCell>
              <TableCell><strong>SLA Level</strong></TableCell>
              <TableCell><strong>First Response</strong></TableCell>
              <TableCell><strong>Resolution</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell><strong>Default</strong></TableCell>
              <TableCell align="right"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">Loading...</TableCell>
              </TableRow>
            ) : policies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No SLA policies found. Create your first policy to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              policies.map((policy) => (
                <TableRow key={policy.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {policy.name}
                    </Typography>
                    {policy.description && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {policy.description.substring(0, 50)}...
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{policy.sla_level || 'N/A'}</TableCell>
                  <TableCell>
                    {policy.first_response_hours ? `${policy.first_response_hours}h` : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {policy.resolution_hours ? `${policy.resolution_hours}h` : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={policy.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={policy.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    {policy.is_default && (
                      <Chip
                        label="Default"
                        size="small"
                        color="primary"
                        icon={<CheckCircleIcon />}
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedPolicyForNotifications(policy);
                        setNotificationSettings({
                          warning_threshold: 80, // Default, will be loaded from policy
                          critical_threshold: 95,
                          auto_escalate: policy.is_default || false
                        });
                        setNotificationDialogOpen(true);
                      }}
                      title="Notification Settings"
                    >
                      <SettingsIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(policy)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(policy.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Notification Rules
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Configure notification thresholds and escalation rules for each SLA policy.
            Click the settings icon next to a policy to configure its notification rules.
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Notification rules are configured per policy. Use the settings icon in the Policies tab to configure notifications.
          </Alert>
        </Paper>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPolicy ? 'Edit SLA Policy' : 'Create SLA Policy'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Policy Name *"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            <TextField
              label="SLA Level"
              fullWidth
              placeholder="e.g., Gold, Silver, Bronze, 24/7"
              value={formData.sla_level}
              onChange={(e) => setFormData({ ...formData, sla_level: e.target.value })}
            />
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="First Response (hours)"
                  type="number"
                  fullWidth
                  value={formData.first_response_hours}
                  onChange={(e) => setFormData({ ...formData, first_response_hours: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Resolution (hours)"
                  type="number"
                  fullWidth
                  value={formData.resolution_hours}
                  onChange={(e) => setFormData({ ...formData, resolution_hours: e.target.value })}
                />
              </Grid>
            </Grid>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                />
              }
              label="Default Policy"
            />
            {formData.is_default && (
              <Alert severity="info">
                This will become the default SLA policy for all tickets without a specific policy.
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={!formData.name}
          >
            {editingPolicy ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Settings Dialog */}
      <Dialog open={notificationDialogOpen} onClose={() => setNotificationDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Notification Settings - {selectedPolicyForNotifications?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Warning Threshold (%)"
              type="number"
              fullWidth
              value={notificationSettings.warning_threshold}
              onChange={(e) => setNotificationSettings({
                ...notificationSettings,
                warning_threshold: parseInt(e.target.value) || 80
              })}
              helperText="Send warning notification when SLA usage reaches this percentage"
              inputProps={{ min: 0, max: 100 }}
            />
            <TextField
              label="Critical Threshold (%)"
              type="number"
              fullWidth
              value={notificationSettings.critical_threshold}
              onChange={(e) => setNotificationSettings({
                ...notificationSettings,
                critical_threshold: parseInt(e.target.value) || 95
              })}
              helperText="Send critical alert when SLA usage reaches this percentage"
              inputProps={{ min: 0, max: 100 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.auto_escalate}
                  onChange={(e) => setNotificationSettings({
                    ...notificationSettings,
                    auto_escalate: e.target.checked
                  })}
                />
              }
              label="Auto-escalate on breach"
            />
            <Alert severity="info">
              Warning threshold must be less than critical threshold. Notifications will be sent to assigned agents and administrators.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotificationDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={async () => {
              try {
                if (selectedPolicyForNotifications) {
                  await slaAPI.updateNotificationSettings(selectedPolicyForNotifications.id, {
                    warning_threshold: notificationSettings.warning_threshold,
                    critical_threshold: notificationSettings.critical_threshold,
                    auto_escalate: notificationSettings.auto_escalate
                  });
                  setNotificationDialogOpen(false);
                  loadPolicies();
                }
              } catch (error) {
                console.error('Error updating notification settings:', error);
                alert('Failed to update notification settings');
              }
            }}
            variant="contained"
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SLAManagement;

