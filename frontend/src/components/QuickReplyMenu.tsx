import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  ListItemText,
  ListItemIcon,
  TextField,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Reply as ReplyIcon,
  Category as CategoryIcon,
  Close as CloseIcon,
  Search as SearchIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface QuickReplyTemplate {
  id: string;
  name: string;
  content: string;
  category?: string;
  is_shared: boolean;
}

interface QuickReplyMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
  onSelect: (content: string) => void;
  ticketId?: string;
}

const QuickReplyMenu: React.FC<QuickReplyMenuProps> = ({
  anchorEl,
  open,
  onClose,
  onSelect,
  ticketId
}) => {
  const [templates, setTemplates] = useState<QuickReplyTemplate[]>([]);
  const [loading, setLoading] = useState(false);
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
      template.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.category?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
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
      const response = await helpdeskAPI.getQuickReplies();
      setTemplates(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load quick replies');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = (template: QuickReplyTemplate) => {
    // Substitute variables if ticketId is available
    let content = template.content;
    if (ticketId) {
      // Basic variable substitution - can be enhanced later
      content = content.replace(/\{\{ticket_number\}\}/g, ticketId);
    }
    
    onSelect(content);
    onClose();
  };

  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'left',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'left',
      }}
      PaperProps={{
        sx: {
          width: 400,
          maxHeight: 500,
          mt: 1
        }
      }}
    >
      <Box sx={{ p: 2, pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle2" fontWeight="bold">
            Quick Replies
          </Typography>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 1, mt: 1 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          size="small"
          placeholder="Search quick replies..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} fontSize="small" />
          }}
          sx={{ mb: 1 }}
        />

        {categories.length > 0 && (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            <Chip
              label="All"
              onClick={() => setSelectedCategory(null)}
              color={selectedCategory === null ? 'primary' : 'default'}
              size="small"
              variant={selectedCategory === null ? 'filled' : 'outlined'}
            />
            {categories.map(category => (
              <Chip
                key={category}
                label={category}
                onClick={() => setSelectedCategory(category)}
                color={selectedCategory === category ? 'primary' : 'default'}
                size="small"
                variant={selectedCategory === category ? 'filled' : 'outlined'}
                icon={<CategoryIcon />}
              />
            ))}
          </Box>
        )}
      </Box>

      <Divider />

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={24} />
        </Box>
      ) : filteredTemplates.length === 0 ? (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {searchQuery || selectedCategory
              ? 'No quick replies found'
              : 'No quick replies available. Create templates to speed up responses.'}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
          {filteredTemplates.map((template) => (
            <MenuItem
              key={template.id}
              onClick={() => handleSelectTemplate(template)}
              sx={{
                py: 1.5,
                borderBottom: '1px solid',
                borderColor: 'divider',
                '&:last-child': {
                  borderBottom: 'none'
                }
              }}
            >
              <ListItemIcon>
                <ReplyIcon fontSize="small" color="action" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" fontWeight="medium">
                      {template.name}
                    </Typography>
                    {template.category && (
                      <Chip
                        label={template.category}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {template.is_shared && (
                      <Chip
                        label="Shared"
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    )}
                  </Box>
                }
                secondary={
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      mt: 0.5
                    }}
                  >
                    {template.content}
                  </Typography>
                }
              />
            </MenuItem>
          ))}
        </Box>
      )}
    </Menu>
  );
};

export default QuickReplyMenu;

