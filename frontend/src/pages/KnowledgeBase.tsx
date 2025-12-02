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
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Grid,
  Menu,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface KnowledgeBaseArticle {
  id: string;
  title: string;
  summary?: string;
  content: string;
  category?: string;
  tags?: string[];
  is_published: boolean;
  is_featured: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
  author_id?: string;
}

const KnowledgeBase: React.FC = () => {
  const [articles, setArticles] = useState<KnowledgeBaseArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<KnowledgeBaseArticle | null>(null);
  const [editingArticle, setEditingArticle] = useState<KnowledgeBaseArticle | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [categories, setCategories] = useState<string[]>([]);

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    summary: '',
    category: '',
    tags: [] as string[],
    is_published: false,
    is_featured: false
  });

  useEffect(() => {
    loadArticles();
  }, [categoryFilter]);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await helpdeskAPI.listKnowledgeBaseArticles(
        categoryFilter === 'all' ? undefined : categoryFilter,
        false // Show all articles, not just published
      );
      
      if (response.data && response.data.articles) {
        setArticles(response.data.articles);
        // Extract unique categories
        const uniqueCategories = Array.from(
          new Set(
            response.data.articles
              .map((a: KnowledgeBaseArticle) => a.category)
              .filter((c: string | undefined) => c)
          )
        ) as string[];
        setCategories(uniqueCategories);
      }
    } catch (err: any) {
      console.error('Error loading articles:', err);
      setError(err.response?.data?.detail || 'Failed to load knowledge base articles');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingArticle(null);
    setFormData({
      title: '',
      content: '',
      summary: '',
      category: '',
      tags: [],
      is_published: false,
      is_featured: false
    });
    setOpenDialog(true);
  };

  const handleEdit = (article: KnowledgeBaseArticle) => {
    setEditingArticle(article);
    setFormData({
      title: article.title,
      content: article.content,
      summary: article.summary || '',
      category: article.category || '',
      tags: article.tags || [],
      is_published: article.is_published,
      is_featured: article.is_featured
    });
    setOpenDialog(true);
  };

  const handleView = (article: KnowledgeBaseArticle) => {
    setSelectedArticle(article);
    setOpenViewDialog(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this article?')) {
      return;
    }

    try {
      await helpdeskAPI.deleteKnowledgeBaseArticle(id);
      await loadArticles();
    } catch (err: any) {
      console.error('Error deleting article:', err);
      alert(err.response?.data?.detail || 'Failed to delete article');
    }
  };

  const handleSave = async () => {
    try {
      setError(null);
      if (editingArticle) {
        await helpdeskAPI.updateKnowledgeBaseArticle(editingArticle.id, formData);
      } else {
        await helpdeskAPI.createKnowledgeBaseArticle(formData);
      }
      setOpenDialog(false);
      await loadArticles();
    } catch (err: any) {
      console.error('Error saving article:', err);
      setError(err.response?.data?.detail || 'Failed to save article');
    }
  };

  const handleTagInput = (value: string) => {
    const tags = value.split(',').map(t => t.trim()).filter(t => t);
    setFormData({ ...formData, tags });
  };

  const filteredArticles = articles.filter(article => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        article.title.toLowerCase().includes(query) ||
        article.summary?.toLowerCase().includes(query) ||
        article.content.toLowerCase().includes(query) ||
        article.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }
    return true;
  });

  if (loading && articles.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Knowledge Base
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create Article
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Articles"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="all">All Categories</MenuItem>
                {categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Tags</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Views</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredArticles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                      {searchQuery ? 'No articles found matching your search.' : 'No knowledge base articles yet. Create your first article!'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredArticles.map((article) => (
                  <TableRow key={article.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {article.title}
                      </Typography>
                      {article.summary && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {article.summary.substring(0, 60)}...
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {article.category && (
                        <Chip label={article.category} size="small" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={0.5} flexWrap="wrap">
                        {article.tags?.slice(0, 2).map((tag, idx) => (
                          <Chip key={idx} label={tag} size="small" />
                        ))}
                        {article.tags && article.tags.length > 2 && (
                          <Chip label={`+${article.tags.length - 2}`} size="small" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={0.5} flexDirection="column">
                        {article.is_published ? (
                          <Chip label="Published" color="success" size="small" />
                        ) : (
                          <Chip label="Draft" color="default" size="small" />
                        )}
                        {article.is_featured && (
                          <Chip label="Featured" color="primary" size="small" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>{article.view_count || 0}</TableCell>
                    <TableCell>
                      {new Date(article.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleView(article)}
                        title="View"
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(article)}
                        title="Edit"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(article.id)}
                        title="Delete"
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
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingArticle ? 'Edit Article' : 'Create New Article'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Summary"
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              multiline
              rows={2}
              sx={{ mb: 2 }}
              helperText="Brief summary of the article"
            />
            <TextField
              fullWidth
              label="Content"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              multiline
              rows={10}
              required
              sx={{ mb: 2 }}
            />
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="e.g., Technical, FAQ, Troubleshooting"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Tags (comma-separated)"
                  value={formData.tags.join(', ')}
                  onChange={(e) => handleTagInput(e.target.value)}
                  placeholder="e.g., wifi, network, troubleshooting"
                />
              </Grid>
            </Grid>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_published}
                    onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                  />
                }
                label="Published"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_featured}
                    onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                  />
                }
                label="Featured"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={!formData.title || !formData.content}
          >
            {editingArticle ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedArticle?.title}</DialogTitle>
        <DialogContent>
          {selectedArticle && (
            <Box sx={{ pt: 2 }}>
              {selectedArticle.category && (
                <Chip label={selectedArticle.category} sx={{ mb: 2 }} />
              )}
              {selectedArticle.tags && selectedArticle.tags.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  {selectedArticle.tags.map((tag, idx) => (
                    <Chip key={idx} label={tag} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </Box>
              )}
              {selectedArticle.summary && (
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
                  {selectedArticle.summary}
                </Typography>
              )}
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {selectedArticle.content}
              </Typography>
              <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary">
                  Created: {new Date(selectedArticle.created_at).toLocaleString()} | 
                  Updated: {new Date(selectedArticle.updated_at).toLocaleString()} | 
                  Views: {selectedArticle.view_count || 0}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Close</Button>
          {selectedArticle && (
            <Button
              onClick={() => {
                setOpenViewDialog(false);
                handleEdit(selectedArticle);
              }}
              variant="contained"
            >
              Edit
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default KnowledgeBase;

