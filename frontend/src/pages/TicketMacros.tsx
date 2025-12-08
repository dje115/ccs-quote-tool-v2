import React, { useState, useEffect } from 'react';
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
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Grid,
  InputAdornment,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Build as MacroIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface MacroAction {
  type: string;
  [key: string]: any;
}

interface TicketMacro {
  id: string;
  name: string;
  description?: string;
  actions: MacroAction[];
  is_shared: boolean;
  created_at?: string;
  updated_at?: string;
}

const TicketMacros: React.FC = () => {
  const [macros, setMacros] = useState<TicketMacro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMacro, setEditingMacro] = useState<TicketMacro | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    actions: '[]' as string,
    is_shared: false
  });

  useEffect(() => {
    loadMacros();
  }, []);

  const loadMacros = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.getMacros(true); // Include shared macros
      setMacros(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load macros');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (macro?: TicketMacro) => {
    if (macro) {
      setEditingMacro(macro);
      setFormData({
        name: macro.name || '',
        description: macro.description || '',
        actions: JSON.stringify(macro.actions || [], null, 2),
        is_shared: macro.is_shared || false
      });
    } else {
      setEditingMacro(null);
      setFormData({
        name: '',
        description: '',
        actions: JSON.stringify([
          {
            type: 'update_status',
            status: 'in_progress'
          },
          {
            type: 'add_comment',
            comment: 'Macro executed',
            is_internal: false
          }
        ], null, 2),
        is_shared: false
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingMacro(null);
  };

  const handleSave = async () => {
    try {
      setError(null);
      
      let actions: MacroAction[];
      try {
        actions = JSON.parse(formData.actions);
        if (!Array.isArray(actions)) {
          throw new Error('Actions must be an array');
        }
      } catch (e) {
        setError('Invalid JSON format for actions. Please check your syntax.');
        return;
      }

      const macroData = {
        name: formData.name,
        description: formData.description || null,
        actions: actions,
        is_shared: formData.is_shared
      };

      if (editingMacro) {
        await helpdeskAPI.updateMacro(editingMacro.id, macroData);
        setSuccess('Macro updated successfully!');
      } else {
        await helpdeskAPI.createMacro(macroData);
        setSuccess('Macro created successfully!');
      }

      handleCloseDialog();
      loadMacros();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save macro');
    }
  };

  const handleDelete = async (macroId: string) => {
    if (!window.confirm('Are you sure you want to delete this macro?')) {
      return;
    }

    try {
      setError(null);
      await helpdeskAPI.deleteMacro(macroId);
      setSuccess('Macro deleted successfully!');
      loadMacros();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete macro');
    }
  };

  const filteredMacros = macros.filter(macro =>
    !searchTerm ||
    macro.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    macro.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getActionDescription = (action: MacroAction): string => {
    switch (action.type) {
      case 'update_status':
        return `Update status to: ${action.status || 'N/A'}`;
      case 'update_priority':
        return `Update priority to: ${action.priority || 'N/A'}`;
      case 'assign':
        return `Assign to: ${action.user_id || action.user_name || 'User'}`;
      case 'add_comment':
        return `Add comment: ${action.comment?.substring(0, 50) || 'N/A'}...`;
      case 'add_tag':
        return `Add tag: ${action.tag || 'N/A'}`;
      case 'remove_tag':
        return `Remove tag: ${action.tag || 'N/A'}`;
      case 'set_custom_field':
        return `Set ${action.field_name || 'field'}: ${action.field_value || 'N/A'}`;
      default:
        return `${action.type || 'Unknown action'}`;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <MacroIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" component="h1">
                Ticket Macros
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Create and manage automated actions for tickets
              </Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Macro
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <TextField
            placeholder="Search macros..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
          />
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Name</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                  <TableCell><strong>Shared</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredMacros.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No macros found. Create your first macro to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredMacros.map((macro) => (
                    <TableRow key={macro.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <PlayIcon fontSize="small" color="action" />
                          <Typography variant="body2" fontWeight="medium">
                            {macro.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 300 }}>
                          {macro.description || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          {macro.actions?.slice(0, 2).map((action, idx) => (
                            <Chip
                              key={idx}
                              label={getActionDescription(action)}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                          {macro.actions && macro.actions.length > 2 && (
                            <Chip
                              label={`+${macro.actions.length - 2} more`}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={macro.is_shared ? 'Shared' : 'Private'}
                          color={macro.is_shared ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(macro)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(macro.id)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingMacro ? 'Edit Macro' : 'Create Macro'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Macro Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="e.g., Escalate to Manager"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
                placeholder="Describe what this macro does..."
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_shared}
                    onChange={(e) => setFormData({ ...formData, is_shared: e.target.checked })}
                  />
                }
                label="Share with all users"
              />
            </Grid>
            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle2">Action Types Reference</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography variant="body2"><strong>update_status:</strong> {`{ "type": "update_status", "status": "in_progress" }`}</Typography>
                    <Typography variant="body2"><strong>update_priority:</strong> {`{ "type": "update_priority", "priority": "high" }`}</Typography>
                    <Typography variant="body2"><strong>assign:</strong> {`{ "type": "assign", "user_id": "user-id" }`}</Typography>
                    <Typography variant="body2"><strong>add_comment:</strong> {`{ "type": "add_comment", "comment": "text", "is_internal": false }`}</Typography>
                    <Typography variant="body2"><strong>add_tag:</strong> {`{ "type": "add_tag", "tag": "urgent" }`}</Typography>
                    <Typography variant="body2"><strong>remove_tag:</strong> {`{ "type": "remove_tag", "tag": "urgent" }`}</Typography>
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Actions (JSON Array)"
                value={formData.actions}
                onChange={(e) => setFormData({ ...formData, actions: e.target.value })}
                multiline
                rows={12}
                required
                helperText="Enter actions as a JSON array. Each action must have a 'type' field."
                error={!!error && error.includes('JSON')}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!formData.name || !formData.actions}>
            {editingMacro ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TicketMacros;

