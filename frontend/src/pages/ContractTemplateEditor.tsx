import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  Tabs,
  Tab,
  Grid
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Save as SaveIcon,
  Add as AddIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { contractAPI } from '../services/api';

const ContractTemplateEditor: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [template, setTemplate] = useState<any>(null);
  const [currentVersion, setCurrentVersion] = useState<any>(null);
  const [templateContent, setTemplateContent] = useState('');
  const [versionName, setVersionName] = useState('');
  const [versionDescription, setVersionDescription] = useState('');
  const [saveVersionDialogOpen, setSaveVersionDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadTemplate();
    }
  }, [id]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      const response = await contractAPI.getTemplate(id!);
      const templateData = response.data;
      setTemplate(templateData);
      
      // Get current version
      if (templateData.versions && templateData.versions.length > 0) {
        const current = templateData.versions.find((v: any) => v.is_current) || templateData.versions[0];
        setCurrentVersion(current);
        setTemplateContent(current.template_content || '');
      }
    } catch (error) {
      console.error('Error loading template:', error);
      alert('Failed to load template');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveVersion = async () => {
    try {
      await contractAPI.createVersion(id!, {
        template_id: id!,
        template_content: templateContent,
        version_name: versionName || undefined,
        description: versionDescription || undefined
      });
      setSaveVersionDialogOpen(false);
      setVersionName('');
      setVersionDescription('');
      loadTemplate();
      alert('New version created successfully!');
    } catch (error) {
      console.error('Error saving version:', error);
      alert('Failed to save version');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Typography>Loading template...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/contracts/templates')}>
          Back
        </Button>
        <Typography variant="h4">{template?.name || 'Edit Template'}</Typography>
        {currentVersion && (
          <Chip label={`Version ${currentVersion.version_number}`} color="primary" />
        )}
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 9 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Template Content</Typography>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={() => setSaveVersionDialogOpen(true)}
              >
                Save as New Version
              </Button>
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              Use placeholders like {'{{customer_name}}'} or {'{{monthly_fee|0}}'} for dynamic content.
              The system will automatically extract and validate placeholders.
            </Alert>

            <TextField
              fullWidth
              multiline
              rows={20}
              value={templateContent}
              onChange={(e) => setTemplateContent(e.target.value)}
              placeholder="Enter contract template content with placeholders..."
              sx={{
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace',
                  fontSize: '0.9rem'
                }
              }}
            />
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Template Info</Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">Type</Typography>
              <Typography variant="body2">{template?.contract_type}</Typography>
            </Box>
            {template?.category && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">Category</Typography>
                <Typography variant="body2">{template.category}</Typography>
              </Box>
            )}
            {template?.description && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">Description</Typography>
                <Typography variant="body2">{template.description}</Typography>
              </Box>
            )}
            
            {currentVersion && (
              <>
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Current Version</Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Version</Typography>
                  <Typography variant="body2">v{currentVersion.version_number}</Typography>
                </Box>
                {currentVersion.version_name && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">Name</Typography>
                    <Typography variant="body2">{currentVersion.version_name}</Typography>
                  </Box>
                )}
                {currentVersion.description && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">Description</Typography>
                    <Typography variant="body2">{currentVersion.description}</Typography>
                  </Box>
                )}
              </>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Save Version Dialog */}
      <Dialog open={saveVersionDialogOpen} onClose={() => setSaveVersionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save as New Version</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Version Name (optional)"
              fullWidth
              value={versionName}
              onChange={(e) => setVersionName(e.target.value)}
              placeholder="e.g., v2.1 - Updated SLA terms"
            />
            <TextField
              label="Description (optional)"
              fullWidth
              multiline
              rows={3}
              value={versionDescription}
              onChange={(e) => setVersionDescription(e.target.value)}
              placeholder="What changed in this version?"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveVersionDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveVersion} variant="contained">
            Save Version
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ContractTemplateEditor;

