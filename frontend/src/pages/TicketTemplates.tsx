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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Grid,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Description as TemplateIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface TicketTemplate {
  id: string;
  name: string;
  category?: string;
  subject_template?: string;
  description_template?: string;
  npa_template?: string;
  tags?: string[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

const TicketTemplates: React.FC = () => {
  const [templates, setTemplates] = useState<TicketTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<TicketTemplate | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    subject_template: '',
    description_template: '',
    npa_template: '',
    tags: '',
    is_active: true
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.getTemplates();
      setTemplates(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (template?: TicketTemplate) => {
    if (template) {
      setEditingTemplate(template);
      setFormData({
        name: template.name || '',
        category: template.category || '',
        subject_template: template.subject_template || '',
        description_template: template.description_template || '',
        npa_template: template.npa_template || '',
        tags: template.tags?.join(', ') || '',
        is_active: template.is_active
      });
    } else {
      setEditingTemplate(null);
      setFormData({
        name: '',
        category: '',
        subject_template: '',
        description_template: '',
        npa_template: '',
        tags: '',
        is_active: true
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingTemplate(null);
  };

  const handleSave = async () => {
    try {
      setError(null);
      const tagsArray = formData.tags
        ? formData.tags.split(',').map(t => t.trim()).filter(Boolean)
        : [];

      const templateData = {
        name: formData.name,
        category: formData.category || null,
        subject_template: formData.subject_template || null,
        description_template: formData.description_template || null,
        npa_template: formData.npa_template || null,
        tags: tagsArray,
        is_active: formData.is_active
      };

      if (editingTemplate) {
        await helpdeskAPI.updateTemplate(editingTemplate.id, templateData);
        setSuccess('Template updated successfully!');
      } else {
        await helpdeskAPI.createTemplate(templateData);
        setSuccess('Template created successfully!');
      }

      handleCloseDialog();
      loadTemplates();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save template');
    }
  };

  const handleDelete = async (templateId: string) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      setError(null);
      await helpdeskAPI.deleteTemplate(templateId);
      setSuccess('Template deleted successfully!');
      loadTemplates();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete template');
    }
  };

  const categories = Array.from(new Set(templates.map(t => t.category).filter(Boolean))) as string[];

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = !searchTerm || 
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.category?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TemplateIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" component="h1">
                Ticket Templates
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Create and manage ticket templates for quick ticket creation
              </Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Template
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

        <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
          <TextField
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
          />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              label="Category"
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="all">All Categories</MenuItem>
              {categories.map(cat => (
                <MenuItem key={cat} value={cat}>{cat}</MenuItem>
              ))}
            </Select>
          </FormControl>
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
                  <TableCell><strong>Category</strong></TableCell>
                  <TableCell><strong>Subject Template</strong></TableCell>
                  <TableCell><strong>Tags</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTemplates.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No templates found. Create your first template to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTemplates.map((template) => (
                    <TableRow key={template.id} hover>
                      <TableCell>{template.name}</TableCell>
                      <TableCell>
                        {template.category ? (
                          <Chip label={template.category} size="small" />
                        ) : (
                          <Typography variant="body2" color="text.secondary">—</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                          {template.subject_template || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {template.tags && template.tags.length > 0 ? (
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {template.tags.slice(0, 3).map((tag, idx) => (
                              <Chip key={idx} label={tag} size="small" variant="outlined" />
                            ))}
                            {template.tags.length > 3 && (
                              <Chip label={`+${template.tags.length - 3}`} size="small" />
                            )}
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">—</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={template.is_active ? 'Active' : 'Inactive'}
                          color={template.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(template)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(template.id)}
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
          {editingTemplate ? 'Edit Template' : 'Create Template'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Template Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Category"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                placeholder="e.g., Network Issues, Hardware, Software"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Subject Template"
                value={formData.subject_template}
                onChange={(e) => setFormData({ ...formData, subject_template: e.target.value })}
                placeholder="e.g., {{customer_name}} - Network Issue"
                helperText="Use {{variable_name}} for dynamic content"
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description Template"
                value={formData.description_template}
                onChange={(e) => setFormData({ ...formData, description_template: e.target.value })}
                placeholder="Template for ticket description..."
                helperText="Use {{variable_name}} for dynamic content"
                multiline
                rows={4}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="NPA Template"
                value={formData.npa_template}
                onChange={(e) => setFormData({ ...formData, npa_template: e.target.value })}
                placeholder="Template for Next Point of Action..."
                helperText="Use {{variable_name}} for dynamic content"
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Tags (comma-separated)"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="e.g., network, urgent, hardware"
                helperText="Separate multiple tags with commas"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!formData.name}>
            {editingTemplate ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TicketTemplates;

