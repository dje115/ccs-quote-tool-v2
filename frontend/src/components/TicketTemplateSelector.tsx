import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Chip,
  TextField,
  Typography,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Description as TemplateIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Category as CategoryIcon
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
}

interface TicketTemplateSelectorProps {
  ticketId: string;
  onTemplateApplied?: (template: TicketTemplate) => void;
  onClose?: () => void;
}

const TicketTemplateSelector: React.FC<TicketTemplateSelectorProps> = ({
  ticketId,
  onTemplateApplied,
  onClose
}) => {
  const [open, setOpen] = useState(false);
  const [templates, setTemplates] = useState<TicketTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Get unique categories
  const categories = Array.from(new Set(templates.map(t => t.category).filter(Boolean))) as string[];

  // Filter templates
  const filteredTemplates = templates.filter(template => {
    const matchesCategory = !selectedCategory || template.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.category?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch && template.is_active;
  });

  useEffect(() => {
    if (open) {
      loadTemplates();
    }
  }, [open]);

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await helpdeskAPI.getTemplates();
      setTemplates(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async (templateId: string) => {
    setApplying(templateId);
    setError(null);
    try {
      await helpdeskAPI.applyTemplate(ticketId, templateId);
      const template = templates.find(t => t.id === templateId);
      if (template && onTemplateApplied) {
        onTemplateApplied(template);
      }
      setOpen(false);
      if (onClose) {
        onClose();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply template');
    } finally {
      setApplying(null);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    setSelectedCategory(null);
    setSearchQuery('');
  };

  const handleClose = () => {
    setOpen(false);
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        startIcon={<TemplateIcon />}
        onClick={handleOpen}
        size="small"
      >
        Apply Template
      </Button>

      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TemplateIcon />
              <Typography variant="h6">Select Ticket Template</Typography>
            </Box>
            <IconButton onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Search and Filter */}
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
              sx={{ mb: 1 }}
            />
            {categories.length > 0 && (
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label="All"
                  onClick={() => setSelectedCategory(null)}
                  color={selectedCategory === null ? 'primary' : 'default'}
                  size="small"
                />
                {categories.map(category => (
                  <Chip
                    key={category}
                    label={category}
                    onClick={() => setSelectedCategory(category)}
                    color={selectedCategory === category ? 'primary' : 'default'}
                    size="small"
                    icon={<CategoryIcon />}
                  />
                ))}
              </Box>
            )}
          </Box>

          <Divider sx={{ mb: 2 }} />

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredTemplates.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary">
                {searchQuery || selectedCategory
                  ? 'No templates found matching your criteria'
                  : 'No templates available. Create templates to speed up ticket creation.'}
              </Typography>
            </Box>
          ) : (
            <List>
              {filteredTemplates.map((template) => (
                <ListItem
                  key={template.id}
                  disablePadding
                  sx={{ mb: 1 }}
                >
                  <ListItemButton
                    onClick={() => handleApplyTemplate(template.id)}
                    disabled={applying === template.id}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
                      <TemplateIcon color="action" />
                      <Box sx={{ flex: 1 }}>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1">{template.name}</Typography>
                              {template.category && (
                                <Chip
                                  label={template.category}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              {template.subject_template && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  Subject: {template.subject_template.substring(0, 60)}
                                  {template.subject_template.length > 60 ? '...' : ''}
                                </Typography>
                              )}
                              {template.description_template && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  Description: {template.description_template.substring(0, 80)}
                                  {template.description_template.length > 80 ? '...' : ''}
                                </Typography>
                              )}
                              {template.tags && template.tags.length > 0 && (
                                <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                                  {template.tags.slice(0, 3).map((tag, idx) => (
                                    <Chip
                                      key={idx}
                                      label={tag}
                                      size="small"
                                      variant="outlined"
                                    />
                                  ))}
                                  {template.tags.length > 3 && (
                                    <Chip
                                      label={`+${template.tags.length - 3}`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  )}
                                </Box>
                              )}
                            </Box>
                          }
                        />
                      </Box>
                      {applying === template.id ? (
                        <CircularProgress size={20} />
                      ) : (
                        <CheckCircleIcon color="primary" />
                      )}
                    </Box>
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TicketTemplateSelector;

