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
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tooltip,
  Switch,
  FormControlLabel,
  Grid
} from '@mui/material';
import {
  Edit as EditIcon,
  History as HistoryIcon,
  Restore as RestoreIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  Psychology as PsychologyIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { promptsAPI, providerKeysAPI } from '../services/api';
import { PromptCategory } from '../types/prompts';

interface Prompt {
  id: string;
  name: string;
  category: string;
  description?: string;
  quote_type?: string;
  system_prompt: string;
  user_prompt_template: string;
  model: string;
  temperature: number;
  max_tokens: number;
  version: number;
  is_active: boolean;
  is_system: boolean;
  tenant_id?: string;
  created_by?: string;
  variables?: Record<string, any>;
  provider_id?: string;
  provider_model?: string;
  provider_settings?: Record<string, any>;
  use_system_default: boolean;
  created_at: string;
  updated_at: string;
}

interface Provider {
  id: string;
  name: string;
  slug: string;
  provider_type: string;
  supported_models?: string[];
  has_valid_key: boolean;
}

interface PromptVersion {
  id: string;
  prompt_id: string;
  version: number;
  note?: string;
  system_prompt: string;
  user_prompt_template: string;
  variables?: Record<string, any>;
  model: string;
  temperature: number;
  max_tokens: number;
  created_by?: string;
  created_at: string;
}

const PromptManagement: React.FC = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showVersionsDialog, setShowVersionsDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  
  // Provider state
  const [availableProviders, setAvailableProviders] = useState<Provider[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    quote_type: '',
    description: '',
    system_prompt: '',
    user_prompt_template: '',
    model: 'gpt-5-mini',
    temperature: 0.7,
    max_tokens: 8000,
    variables: {} as Record<string, any>,
    note: '',
    provider_id: '',
    provider_model: '',
    provider_settings: {} as Record<string, any>,
    use_system_default: true
  });

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'customer_analysis', label: 'Customer Analysis' },
    { value: 'quote_analysis', label: 'Quote Analysis' },
    { value: 'product_search', label: 'Product Search' },
    { value: 'building_analysis', label: 'Building Analysis' },
    { value: 'activity_enhancement', label: 'Activity Enhancement' },
    { value: 'action_suggestions', label: 'Action Suggestions' },
    { value: 'lead_generation', label: 'Lead Generation' },
    { value: 'competitor_analysis', label: 'Competitor Analysis' },
    { value: 'financial_analysis', label: 'Financial Analysis' },
    { value: 'planning_analysis', label: 'Planning Analysis' },
    { value: 'translation', label: 'Translation' }
  ];

  const quoteTypes = [
    { value: '', label: 'Generic (All Quote Types)' },
    { value: 'cabling', label: 'Structured Cabling' },
    { value: 'network_build', label: 'Network Infrastructure Build' },
    { value: 'server_build', label: 'Server Infrastructure Build' },
    { value: 'software_dev', label: 'Software Development' },
    { value: 'testing', label: 'Testing Services' },
    { value: 'design', label: 'Design Services' }
  ];

  useEffect(() => {
    loadPrompts();
    loadAvailableProviders();
  }, [selectedCategory]);

  const loadAvailableProviders = async () => {
    try {
      setLoadingProviders(true);
      const response = await promptsAPI.getAvailableProviders();
      setAvailableProviders(response.data || []);
    } catch (err: any) {
      console.error('Error loading providers:', err);
    } finally {
      setLoadingProviders(false);
    }
  };

  const loadAvailableModels = async (providerId: string) => {
    if (!providerId) {
      setAvailableModels([]);
      return;
    }
    try {
      const response = await promptsAPI.getAvailableModels(providerId);
      setAvailableModels(response.data || []);
    } catch (err: any) {
      console.error('Error loading models:', err);
      setAvailableModels([]);
    }
  };

  const loadPrompts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {
        // Don't filter by tenant_id - we want to see both system and tenant prompts
        is_active: true
      };
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      const response = await promptsAPI.list(params);
      setPrompts(response.data || []);
    } catch (err: any) {
      console.error('Error loading prompts:', err);
      setError(err.response?.data?.detail || 'Failed to load prompts');
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async (promptId: string) => {
    try {
      const response = await promptsAPI.getVersions(promptId);
      setVersions(response.data || []);
    } catch (err: any) {
      console.error('Error loading versions:', err);
      alert('Failed to load version history: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleEdit = async (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    setFormData({
      name: prompt.name,
      category: prompt.category,
      quote_type: prompt.quote_type || '',
      description: prompt.description || '',
      system_prompt: prompt.system_prompt,
      user_prompt_template: prompt.user_prompt_template,
      model: prompt.model,
      temperature: prompt.temperature,
      max_tokens: prompt.max_tokens,
      variables: prompt.variables || {},
      note: '',
      provider_id: prompt.provider_id || '',
      provider_model: prompt.provider_model || '',
      provider_settings: prompt.provider_settings || {},
      use_system_default: prompt.use_system_default !== undefined ? prompt.use_system_default : true
    });
    if (prompt.provider_id) {
      await loadAvailableModels(prompt.provider_id);
    }
    setShowEditDialog(true);
  };

  const handleViewVersions = async (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    await loadVersions(prompt.id);
    setShowVersionsDialog(true);
  };

  const handleRollback = async (promptId: string, version: number) => {
    if (!confirm(`Are you sure you want to rollback to version ${version}? This will create a new version with the old content.`)) {
      return;
    }
    
    try {
      await promptsAPI.rollback(promptId, version);
      alert('Prompt rolled back successfully!');
      setShowVersionsDialog(false);
      loadPrompts();
    } catch (err: any) {
      alert('Failed to rollback: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSave = async () => {
    if (!selectedPrompt) return;
    
    try {
      await promptsAPI.update(selectedPrompt.id, {
        name: formData.name,
        description: formData.description,
        quote_type: formData.quote_type || null,
        system_prompt: formData.system_prompt,
        user_prompt_template: formData.user_prompt_template,
        model: formData.model,
        temperature: formData.temperature,
        max_tokens: formData.max_tokens,
        variables: formData.variables,
        note: formData.note || 'Updated prompt',
        provider_id: formData.provider_id || null,
        provider_model: formData.provider_model || null,
        provider_settings: formData.provider_settings || null,
        use_system_default: formData.use_system_default
      });
      alert('Prompt updated successfully! A new version has been created.');
      setShowEditDialog(false);
      loadPrompts();
    } catch (err: any) {
      alert('Failed to update prompt: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreate = async () => {
    try {
      await promptsAPI.create({
        name: formData.name,
        category: formData.category,
        quote_type: formData.quote_type || null,
        description: formData.description,
        system_prompt: formData.system_prompt,
        user_prompt_template: formData.user_prompt_template,
        model: formData.model,
        temperature: formData.temperature,
        max_tokens: formData.max_tokens,
        variables: formData.variables,
        is_system: false, // Tenant-specific prompts only
        provider_id: formData.provider_id || null,
        provider_model: formData.provider_model || null,
        provider_settings: formData.provider_settings || null,
        use_system_default: formData.use_system_default
      });
      alert('Prompt created successfully!');
      setShowCreateDialog(false);
      setFormData({
        name: '',
        category: '',
        quote_type: '',
        description: '',
        system_prompt: '',
        user_prompt_template: '',
        model: 'gpt-5-mini',
        temperature: 0.7,
        max_tokens: 8000,
        variables: {},
        note: '',
        provider_id: '',
        provider_model: '',
        provider_settings: {},
        use_system_default: true
      });
      loadPrompts();
    } catch (err: any) {
      alert('Failed to create prompt: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (prompt: Prompt) => {
    if (!confirm(`Are you sure you want to deactivate "${prompt.name}"?`)) {
      return;
    }
    
    try {
      await promptsAPI.delete(prompt.id, true);
      alert('Prompt deactivated successfully!');
      loadPrompts();
    } catch (err: any) {
      alert('Failed to delete prompt: ' + (err.response?.data?.detail || err.message));
    }
  };

  const filteredPrompts = prompts.filter(p => {
    if (selectedCategory === 'all') return true;
    return p.category === selectedCategory;
  });

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            AI Prompt Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage AI prompts for your tenant. All changes are versioned and can be rolled back.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setFormData({
              name: '',
              category: '',
              quote_type: '',
              description: '',
              system_prompt: '',
              user_prompt_template: '',
              model: 'gpt-5-mini',
              temperature: 0.7,
              max_tokens: 8000,
              variables: {},
              note: ''
            });
            setShowCreateDialog(true);
          }}
        >
          Create Prompt
        </Button>
      </Box>

      <Alert severity="warning" sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'start' }}>
          <WarningIcon sx={{ mr: 1, mt: 0.5 }} />
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              <strong>Advanced Users Only</strong>
            </Typography>
            <Typography variant="body2">
              This feature is for advanced users only. Be very careful when editing prompts. 
              <strong> Do not modify JSON structure details in prompts</strong> unless you understand the impact. 
              All changes are versioned and can be rolled back, but incorrect prompts may affect AI functionality.
            </Typography>
          </Box>
        </Box>
      </Alert>

      <Paper sx={{ mb: 3, p: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Filter by Category</InputLabel>
          <Select
            value={selectedCategory}
            label="Filter by Category"
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map((cat) => (
              <MenuItem key={cat.value} value={cat.value}>
                {cat.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Quote Type</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredPrompts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No prompts found. Create your first prompt!
                  </TableCell>
                </TableRow>
              ) : (
                filteredPrompts.map((prompt) => {
                  const provider = availableProviders.find(p => p.id === prompt.provider_id);
                  return (
                    <TableRow key={prompt.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {prompt.name}
                        </Typography>
                        {prompt.description && (
                          <Typography variant="caption" color="text.secondary">
                            {prompt.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip label={prompt.category} size="small" />
                      </TableCell>
                      <TableCell>
                        {prompt.quote_type ? (
                          <Chip label={prompt.quote_type} size="small" color="primary" variant="outlined" />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip label={`v${prompt.version}`} size="small" />
                      </TableCell>
                      <TableCell>
                        {prompt.use_system_default ? (
                          <Chip label="System Default" size="small" color="default" variant="outlined" />
                        ) : provider ? (
                          <Chip label={provider.name} size="small" color="primary" />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {prompt.provider_model || prompt.model}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={prompt.is_active ? 'Active' : 'Inactive'}
                          color={prompt.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit Prompt">
                          <IconButton size="small" onClick={() => handleEdit(prompt)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Version History">
                          <IconButton size="small" onClick={() => handleViewVersions(prompt)}>
                            <HistoryIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Deactivate">
                          <IconButton size="small" color="error" onClick={() => handleDelete(prompt)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onClose={() => setShowEditDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EditIcon />
            Edit Prompt: {selectedPrompt?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Warning:</strong> Editing this prompt will create a new version. 
              The previous version will be saved in history and can be restored. 
              <strong> Do not modify JSON structure details</strong> unless you understand the impact.
            </Typography>
          </Alert>
          
          <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 2 }}>
            <Tab label="Basic Info" />
            <Tab label="System Prompt" />
            <Tab label="User Prompt Template" />
            <Tab label="Model Settings" />
          </Tabs>

          {currentTab === 0 && (
            <Box>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                sx={{ mb: 2 }}
                required
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  disabled
                >
                  {categories.filter(c => c.value !== 'all').map((cat) => (
                    <MenuItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {formData.category === 'quote_analysis' && (
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Quote Type</InputLabel>
                  <Select
                    value={formData.quote_type}
                    label="Quote Type"
                    onChange={(e) => setFormData({ ...formData, quote_type: e.target.value })}
                  >
                    {quoteTypes.map((qt) => (
                      <MenuItem key={qt.value} value={qt.value}>
                        {qt.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Change Note (optional)"
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                placeholder="Describe what you changed and why..."
                sx={{ mb: 2 }}
              />
            </Box>
          )}

          {currentTab === 1 && (
            <TextField
              fullWidth
              label="System Prompt"
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              multiline
              rows={10}
              required
              helperText="The system prompt defines the AI's role and behavior"
            />
          )}

          {currentTab === 2 && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Use {'{variable_name}'} for template variables. Available variables are shown below.
                  <strong> Do not modify JSON structure requirements</strong> unless you understand the impact.
                </Typography>
              </Alert>
              <TextField
                fullWidth
                label="User Prompt Template"
                value={formData.user_prompt_template}
                onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
                multiline
                rows={15}
                required
                helperText="This template will be filled with actual data when used"
              />
              {selectedPrompt?.variables && Object.keys(selectedPrompt.variables).length > 0 && (
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Available Template Variables</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {Object.entries(selectedPrompt.variables).map(([key, desc]: [string, any]) => (
                        <ListItem key={key}>
                          <ListItemText
                            primary={<code>{'{' + key + '}'}</code>}
                            secondary={typeof desc === 'string' ? desc : JSON.stringify(desc)}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}

          {currentTab === 3 && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Select an AI provider and model. If "Use System Default" is enabled, the system default provider will be used.
                    Only providers with valid API keys (tenant or system level) are shown.
                  </Typography>
                </Alert>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.use_system_default}
                      onChange={(e) => {
                        setFormData({ ...formData, use_system_default: e.target.checked });
                        if (e.target.checked) {
                          // Clear provider selection when using system default
                          setFormData(prev => ({ ...prev, provider_id: '', provider_model: '' }));
                          setAvailableModels([]);
                        }
                      }}
                    />
                  }
                  label="Use System Default Provider"
                />
              </Grid>
              {!formData.use_system_default && (
                <>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>AI Provider</InputLabel>
                      <Select
                        value={formData.provider_id}
                        label="AI Provider"
                        onChange={async (e) => {
                          const providerId = e.target.value as string;
                          setFormData({ ...formData, provider_id: providerId, provider_model: '' });
                          await loadAvailableModels(providerId);
                        }}
                        disabled={loadingProviders}
                      >
                        {availableProviders
                          .filter(p => p.has_valid_key)
                          .map((provider) => (
                            <MenuItem key={provider.id} value={provider.id}>
                              {provider.name} {provider.provider_type === 'on_premise' && '(On-Premise)'}
                            </MenuItem>
                          ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Provider Model</InputLabel>
                      <Select
                        value={formData.provider_model}
                        label="Provider Model"
                        onChange={(e) => setFormData({ ...formData, provider_model: e.target.value })}
                        disabled={!formData.provider_id || availableModels.length === 0}
                      >
                        {availableModels.map((model) => (
                          <MenuItem key={model} value={model}>
                            {model}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </>
              )}
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Model (Legacy)</InputLabel>
                  <Select
                    value={formData.model}
                    label="Model (Legacy)"
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  >
                    <MenuItem value="gpt-5-mini">GPT-5 Mini</MenuItem>
                    <MenuItem value="gpt-5">GPT-5</MenuItem>
                    <MenuItem value="gpt-4">GPT-4</MenuItem>
                    <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                  </Select>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    Legacy field - kept for backward compatibility
                  </Typography>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  label="Temperature"
                  type="number"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  inputProps={{ min: 0, max: 2, step: 0.1 }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  label="Max Tokens"
                  type="number"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  inputProps={{ min: 1, max: 100000 }}
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            Save (Create New Version)
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AddIcon />
            Create New Prompt
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Create a new tenant-specific prompt. This will override system prompts for your tenant.
          </Alert>
          
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
            required
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={formData.category}
              label="Category"
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
            >
              {categories.filter(c => c.value !== 'all').map((cat) => (
                <MenuItem key={cat.value} value={cat.value}>
                  {cat.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {formData.category === 'quote_analysis' && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Quote Type</InputLabel>
              <Select
                value={formData.quote_type}
                label="Quote Type"
                onChange={(e) => setFormData({ ...formData, quote_type: e.target.value })}
              >
                {quoteTypes.map((qt) => (
                  <MenuItem key={qt.value} value={qt.value}>
                    {qt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={2}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="System Prompt"
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            multiline
            rows={5}
            sx={{ mb: 2 }}
            required
          />
          <TextField
            fullWidth
            label="User Prompt Template"
            value={formData.user_prompt_template}
            onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
            multiline
            rows={10}
            required
            sx={{ mb: 2 }}
          />
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            AI Provider Settings
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={formData.use_system_default}
                onChange={(e) => {
                  setFormData({ ...formData, use_system_default: e.target.checked });
                  if (e.target.checked) {
                    setFormData(prev => ({ ...prev, provider_id: '', provider_model: '' }));
                    setAvailableModels([]);
                  }
                }}
              />
            }
            label="Use System Default Provider"
            sx={{ mb: 2 }}
          />
          {!formData.use_system_default && (
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>AI Provider</InputLabel>
                  <Select
                    value={formData.provider_id}
                    label="AI Provider"
                    onChange={async (e) => {
                      const providerId = e.target.value as string;
                      setFormData({ ...formData, provider_id: providerId, provider_model: '' });
                      await loadAvailableModels(providerId);
                    }}
                    disabled={loadingProviders}
                  >
                    {availableProviders
                      .filter(p => p.has_valid_key)
                      .map((provider) => (
                        <MenuItem key={provider.id} value={provider.id}>
                          {provider.name} {provider.provider_type === 'on_premise' && '(On-Premise)'}
                        </MenuItem>
                      ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Provider Model</InputLabel>
                  <Select
                    value={formData.provider_model}
                    label="Provider Model"
                    onChange={(e) => setFormData({ ...formData, provider_model: e.target.value })}
                    disabled={!formData.provider_id || availableModels.length === 0}
                  >
                    {availableModels.map((model) => (
                      <MenuItem key={model} value={model}>
                        {model}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" color="primary">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Versions Dialog */}
      <Dialog open={showVersionsDialog} onClose={() => setShowVersionsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon />
            Version History: {selectedPrompt?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            All versions are preserved. You can rollback to any previous version.
          </Alert>
          
          <List>
            {versions.length === 0 ? (
              <ListItem>
                <ListItemText primary="No version history available" />
              </ListItem>
            ) : (
              versions.map((version, index) => (
                <React.Fragment key={version.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip label={`Version ${version.version}`} size="small" color={index === 0 ? 'primary' : 'default'} />
                          {version.note && (
                            <Typography variant="body2" color="text.secondary">
                              {version.note}
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Created: {new Date(version.created_at).toLocaleString()}
                          </Typography>
                          {version.created_by && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                              By: {version.created_by}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      {index > 0 && (
                        <Tooltip title="Rollback to this version">
                          <IconButton
                            size="small"
                            onClick={() => handleRollback(version.prompt_id, version.version)}
                            color="primary"
                          >
                            <RestoreIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < versions.length - 1 && <Divider />}
                </React.Fragment>
              ))
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowVersionsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PromptManagement;

