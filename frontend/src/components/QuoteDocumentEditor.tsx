import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Save as SaveIcon,
  History as HistoryIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { quoteAPI } from '../services/api';
import PartsListEditor from './PartsListEditor';

interface QuoteDocumentEditorProps {
  quoteId: string;
  documentType: string;
  onSave?: () => void;
  onCancel?: () => void;
}

const QuoteDocumentEditor: React.FC<QuoteDocumentEditorProps> = ({
  quoteId,
  documentType,
  onSave,
  onCancel
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [document, setDocument] = useState<any>(null);
  const [content, setContent] = useState<any>({ sections: [] });
  const [changesSummary, setChangesSummary] = useState('');
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);

  useEffect(() => {
    loadDocument();
  }, [quoteId, documentType]);

  const loadDocument = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await quoteAPI.getDocument(quoteId, documentType);
      if (response.data) {
        setDocument(response.data);
        setContent(response.data.content || { sections: [] });
      }
    } catch (error: any) {
      console.error('Error loading document:', error);
      setError(error.response?.data?.detail || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const loadVersionHistory = async () => {
    try {
      const response = await quoteAPI.getDocumentVersions(quoteId, documentType);
      if (response.data?.versions) {
        setVersions(response.data.versions);
      }
    } catch (error) {
      console.error('Error loading version history:', error);
    }
  };

  const handleSave = async () => {
    if (!changesSummary.trim()) {
      setError('Please enter a summary of changes');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await quoteAPI.updateDocument(quoteId, documentType, {
        content: content,
        changes_summary: changesSummary
      });
      
      if (onSave) {
        onSave();
      }
      
      // Reload document to get updated version
      await loadDocument();
      setChangesSummary('');
    } catch (error: any) {
      console.error('Error saving document:', error);
      setError(error.response?.data?.detail || 'Failed to save document');
    } finally {
      setSaving(false);
    }
  };

  const handleAddSection = () => {
    const newSection = {
      id: `section_${Date.now()}`,
      title: '',
      content: '',
      order: content.sections.length + 1
    };
    setContent({
      ...content,
      sections: [...content.sections, newSection]
    });
  };

  const handleUpdateSection = (sectionId: string, field: string, value: any) => {
    setContent({
      ...content,
      sections: content.sections.map((section: any) =>
        section.id === sectionId ? { ...section, [field]: value } : section
      )
    });
  };

  const handleDeleteSection = (sectionId: string) => {
    setContent({
      ...content,
      sections: content.sections.filter((section: any) => section.id !== sectionId)
    });
  };

  const handleRollback = async (targetVersion: number) => {
    if (!window.confirm(`Rollback to version ${targetVersion}? This will create a new version with the old content.`)) {
      return;
    }

    try {
      await quoteAPI.rollbackDocumentVersion(quoteId, documentType, targetVersion);
      await loadDocument();
      setShowVersionHistory(false);
    } catch (error: any) {
      console.error('Error rolling back:', error);
      setError(error.response?.data?.detail || 'Failed to rollback');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !document) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  // Use PartsListEditor for parts_list documents
  if (documentType === 'parts_list' && document) {
    return (
      <PartsListEditor
        quoteId={quoteId}
        documentType={documentType}
        document={document}
        onSave={onSave}
        onCancel={onCancel}
      />
    );
  }

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">
            {documentType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Document
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Version History">
              <IconButton onClick={() => {
                setShowVersionHistory(true);
                loadVersionHistory();
              }}>
                <HistoryIcon />
              </IconButton>
            </Tooltip>
            {onCancel && (
              <Button onClick={onCancel} variant="outlined">
                Cancel
              </Button>
            )}
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={saving}
            >
              Save
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Divider sx={{ mb: 3 }} />

        {/* Changes Summary */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Summary of Changes"
            placeholder="Describe what you changed in this version..."
            value={changesSummary}
            onChange={(e) => setChangesSummary(e.target.value)}
            required
            multiline
            rows={2}
            helperText="Required: Enter a summary of changes for version tracking"
          />
        </Box>

        {/* Document Sections */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Sections</Typography>
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddSection}
              variant="outlined"
              size="small"
            >
              Add Section
            </Button>
          </Box>

          {content.sections && content.sections.length > 0 ? (
            content.sections
              .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
              .map((section: any, index: number) => (
                <Paper key={section.id} sx={{ p: 2, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle1" color="primary">
                      Section {index + 1}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteSection(section.id)}
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <TextField
                    fullWidth
                    label="Section Title"
                    value={section.title || ''}
                    onChange={(e) => handleUpdateSection(section.id, 'title', e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    label="Section Content"
                    value={section.content || ''}
                    onChange={(e) => handleUpdateSection(section.id, 'content', e.target.value)}
                  />
                </Paper>
              ))
          ) : (
            <Alert severity="info">
              No sections yet. Click "Add Section" to start editing.
            </Alert>
          )}
        </Box>
      </Paper>

      {/* Version History Dialog */}
      <Dialog
        open={showVersionHistory}
        onClose={() => setShowVersionHistory(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Version History</DialogTitle>
        <DialogContent>
          <List>
            {versions.map((version) => (
              <ListItem
                key={version.id}
                secondaryAction={
                  version.version !== document?.version && (
                    <Button
                      size="small"
                      onClick={() => handleRollback(version.version)}
                      startIcon={<UndoIcon />}
                    >
                      Rollback
                    </Button>
                  )
                }
              >
                <ListItemText
                  primary={`Version ${version.version}`}
                  secondary={
                    <>
                      {version.changes_summary && (
                        <Typography variant="body2" component="div">
                          {version.changes_summary}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        {new Date(version.created_at).toLocaleString()}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowVersionHistory(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QuoteDocumentEditor;

