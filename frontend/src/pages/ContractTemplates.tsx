import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  ContentCopy as CopyIcon,
  Psychology as AiIcon,
  Search as SearchIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { contractAPI } from '../services/api';

interface ContractTemplate {
  id: string;
  name: string;
  description?: string;
  contract_type: string;
  ai_generated: boolean;
  is_active: boolean;
  category?: string;
  tags?: string[];
  created_at: string;
  versions?: ContractTemplateVersion[];
}

interface ContractTemplateVersion {
  id: string;
  version_number: number;
  version_name?: string;
  is_current: boolean;
  created_at: string;
}

const ContractTemplates: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    contract_type: 'managed_services',
    category: ''
  });
  const [aiGeneration, setAiGeneration] = useState({
    contract_type: 'managed_services',
    description: '',
    requirements: {}
  });

  useEffect(() => {
    loadTemplates();
  }, [typeFilter]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (typeFilter !== 'all') {
        params.contract_type = typeFilter;
      }
      
      const response = await contractAPI.listTemplates(params);
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (template.description && template.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (template.category && template.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getTypeLabel = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const handleCreateTemplate = async () => {
    try {
      const response = await contractAPI.createTemplate(newTemplate);
      setCreateDialogOpen(false);
      setNewTemplate({ name: '', description: '', contract_type: 'managed_services', category: '' });
      navigate(`/contracts/templates/${response.data.id}/edit`);
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Failed to create template');
    }
  };

  const handleGenerateWithAI = async () => {
    try {
      setGenerating(true);
      const response = await contractAPI.generateTemplate({
        contract_type: aiGeneration.contract_type,
        description: aiGeneration.description,
        requirements: aiGeneration.requirements
      });
      
      // Create template with AI-generated content
      const templateResponse = await contractAPI.createTemplate({
        name: `AI Generated - ${aiGeneration.contract_type}`,
        description: aiGeneration.description,
        contract_type: aiGeneration.contract_type,
        category: ''
      });
      
      // Create first version with AI content
      await contractAPI.createVersion(templateResponse.data.id, {
        template_id: templateResponse.data.id,
        template_content: response.data.template_content,
        placeholder_schema: response.data.placeholder_schema,
        default_values: response.data.default_values,
        version_name: 'AI Generated v1.0'
      });
      
      setAiDialogOpen(false);
      setAiGeneration({ contract_type: 'managed_services', description: '', requirements: {} });
      loadTemplates();
      navigate(`/contracts/templates/${templateResponse.data.id}/edit`);
    } catch (error) {
      console.error('Error generating template:', error);
      alert('Failed to generate template with AI');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyTemplate = async (templateId: string) => {
    try {
      const newName = prompt('Enter name for copied template:');
      if (!newName) return;
      
      await contractAPI.copyTemplate(templateId, newName);
      loadTemplates();
    } catch (error) {
      console.error('Error copying template:', error);
      alert('Failed to copy template');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DescriptionIcon /> Contract Templates
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AiIcon />}
            onClick={() => setAiDialogOpen(true)}
          >
            Generate with AI
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Template
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 8 }}>
          <TextField
            fullWidth
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <FormControl fullWidth>
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              label="Type"
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="managed_services">Managed Services</MenuItem>
              <MenuItem value="software_license">Software License</MenuItem>
              <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
              <MenuItem value="maintenance">Maintenance</MenuItem>
              <MenuItem value="support_hours">Support Hours</MenuItem>
              <MenuItem value="consulting">Consulting</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Name</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell><strong>Category</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell><strong>Versions</strong></TableCell>
              <TableCell><strong>Created</strong></TableCell>
              <TableCell><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTemplates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {loading ? 'Loading templates...' : 'No templates found'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredTemplates.map((template) => (
                <TableRow key={template.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {template.name}
                      {template.ai_generated && (
                        <Chip label="AI" size="small" sx={{ ml: 1 }} color="primary" />
                      )}
                    </Typography>
                    {template.description && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {template.description.substring(0, 60)}...
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{getTypeLabel(template.contract_type)}</TableCell>
                  <TableCell>{template.category || 'N/A'}</TableCell>
                  <TableCell>
                    <Chip
                      label={template.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={template.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    {template.versions ? template.versions.length : 0} version(s)
                  </TableCell>
                  <TableCell>{new Date(template.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/contracts/templates/${template.id}/edit`)}
                      title="Edit"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleCopyTemplate(template.id)}
                      title="Copy"
                    >
                      <CopyIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Template Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Template</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Template Name *"
              fullWidth
              value={newTemplate.name}
              onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={newTemplate.description}
              onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Contract Type *</InputLabel>
              <Select
                value={newTemplate.contract_type}
                label="Contract Type *"
                onChange={(e) => setNewTemplate({ ...newTemplate, contract_type: e.target.value })}
              >
                <MenuItem value="managed_services">Managed Services</MenuItem>
                <MenuItem value="software_license">Software License</MenuItem>
                <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="support_hours">Support Hours</MenuItem>
                <MenuItem value="consulting">Consulting</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Category"
              fullWidth
              value={newTemplate.category}
              onChange={(e) => setNewTemplate({ ...newTemplate, category: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTemplate}
            variant="contained"
            disabled={!newTemplate.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Generation Dialog */}
      <Dialog open={aiDialogOpen} onClose={() => setAiDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AiIcon /> Generate Contract Template with AI
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert severity="info">
              Describe the contract you need, and AI will generate a professional template with JSON placeholders.
            </Alert>
            <FormControl fullWidth>
              <InputLabel>Contract Type *</InputLabel>
              <Select
                value={aiGeneration.contract_type}
                label="Contract Type *"
                onChange={(e) => setAiGeneration({ ...aiGeneration, contract_type: e.target.value })}
              >
                <MenuItem value="managed_services">Managed Services</MenuItem>
                <MenuItem value="software_license">Software License</MenuItem>
                <MenuItem value="saas_subscription">SaaS Subscription</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="support_hours">Support Hours</MenuItem>
                <MenuItem value="consulting">Consulting</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Description *"
              fullWidth
              multiline
              rows={6}
              value={aiGeneration.description}
              onChange={(e) => setAiGeneration({ ...aiGeneration, description: e.target.value })}
              placeholder="Describe the contract requirements, services included, SLA levels, pricing structure, etc."
            />
            {generating && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="body2">Generating contract template...</Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAiDialogOpen(false)} disabled={generating}>Cancel</Button>
          <Button
            onClick={handleGenerateWithAI}
            variant="contained"
            disabled={!aiGeneration.description || generating}
            startIcon={generating ? <CircularProgress size={16} /> : <AiIcon />}
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ContractTemplates;

