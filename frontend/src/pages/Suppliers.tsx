import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
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
  Grid,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Chip,
  Divider,
  CircularProgress,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  LocalShipping as SupplierIcon,
  Folder as FolderIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { supplierAPI } from '../services/api';

interface SupplierCategory {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

interface Supplier {
  id: string;
  name: string;
  website?: string;
  pricing_url?: string;
  api_key?: string;
  category_id: string;
  is_preferred: boolean;
  is_active: boolean;
  notes?: string;
  category?: SupplierCategory;
}

const Suppliers: React.FC = () => {
  const [categories, setCategories] = useState<SupplierCategory[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<SupplierCategory | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [refreshing, setRefreshing] = useState<string | null>(null);
  
  const [categoryFormData, setCategoryFormData] = useState({
    name: '',
    description: ''
  });
  
  const [supplierFormData, setSupplierFormData] = useState({
    name: '',
    website: '',
    pricing_url: '',
    api_key: '',
    category_id: '',
    is_preferred: false,
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [categoriesRes, suppliersRes] = await Promise.all([
        supplierAPI.listCategories(),
        supplierAPI.list()
      ]);
      setCategories(categoriesRes.data);
      setSuppliers(suppliersRes.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = () => {
    setSelectedCategory(null);
    setCategoryFormData({ name: '', description: '' });
    setCategoryDialogOpen(true);
  };

  const handleEditCategory = (category: SupplierCategory) => {
    setSelectedCategory(category);
    setCategoryFormData({
      name: category.name,
      description: category.description || ''
    });
    setCategoryDialogOpen(true);
  };

  const handleSaveCategory = async () => {
    try {
      setError('');
      if (selectedCategory) {
        await supplierAPI.updateCategory(selectedCategory.id, categoryFormData);
        setSuccess('Category updated successfully');
      } else {
        await supplierAPI.createCategory(categoryFormData);
        setSuccess('Category created successfully');
      }
      setCategoryDialogOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save category');
    }
  };

  const handleDeleteCategory = async () => {
    if (!selectedCategory) return;
    try {
      setError('');
      await supplierAPI.deleteCategory(selectedCategory.id);
      setSuccess('Category deleted successfully');
      setDeleteDialogOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete category');
    }
  };

  const handleAddSupplier = () => {
    setSelectedSupplier(null);
    setSupplierFormData({
      name: '',
      website: '',
      pricing_url: '',
      api_key: '',
      category_id: '',
      is_preferred: false,
      notes: ''
    });
    setSupplierDialogOpen(true);
  };

  const handleEditSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setSupplierFormData({
      name: supplier.name,
      website: supplier.website || '',
      pricing_url: supplier.pricing_url || '',
      api_key: supplier.api_key || '',
      category_id: supplier.category_id,
      is_preferred: supplier.is_preferred,
      notes: supplier.notes || ''
    });
    setSupplierDialogOpen(true);
  };

  const handleSaveSupplier = async () => {
    try {
      setError('');
      if (selectedSupplier) {
        await supplierAPI.update(selectedSupplier.id, supplierFormData);
        setSuccess('Supplier updated successfully');
      } else {
        await supplierAPI.create(supplierFormData);
        setSuccess('Supplier created successfully');
      }
      setSupplierDialogOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save supplier');
    }
  };

  const handleDeleteSupplier = async () => {
    if (!selectedSupplier) return;
    try {
      setError('');
      await supplierAPI.delete(selectedSupplier.id);
      setSuccess('Supplier deleted successfully');
      setDeleteDialogOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete supplier');
    }
  };

  const handleRefreshPricing = async (supplierId: string) => {
    try {
      setRefreshing(supplierId);
      await supplierAPI.refreshSupplierPricing(supplierId);
      setSuccess('Pricing refreshed successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to refresh pricing');
    } finally {
      setRefreshing(null);
    }
  };

  const handleRefreshAllPricing = async () => {
    try {
      setRefreshing('all');
      await supplierAPI.refreshAllPricing();
      setSuccess('All pricing refreshed successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to refresh all pricing');
    } finally {
      setRefreshing(null);
    }
  };

  const getSuppliersByCategory = (categoryId: string) => {
    return suppliers.filter(s => s.category_id === categoryId && s.is_active);
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="700" color="primary" gutterBottom>
            <SupplierIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Supplier Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage suppliers, categories, and pricing
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAllPricing}
            disabled={refreshing === 'all'}
          >
            {refreshing === 'all' ? 'Refreshing...' : 'Refresh All Pricing'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={handleAddCategory}
          >
            Add Category
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddSupplier}
          >
            Add Supplier
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {categories.filter(c => c.is_active).map((category) => {
        const categorySuppliers = getSuppliersByCategory(category.id);
        return (
          <Card key={category.id} sx={{ mb: 3 }}>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FolderIcon />
                  <Typography variant="h6">{category.name}</Typography>
                  {category.description && (
                    <Typography variant="body2" color="text.secondary">
                      {category.description}
                    </Typography>
                  )}
                </Box>
              }
              action={
                <Box>
                  <IconButton onClick={() => handleEditCategory(category)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => {
                    setSelectedCategory(category);
                    setDeleteDialogOpen(true);
                  }} size="small" color="error">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              }
            />
            <CardContent>
              {categorySuppliers.length > 0 ? (
                <Grid container spacing={2}>
                  {categorySuppliers.map((supplier) => (
                    <Grid item xs={12} sm={6} md={4} key={supplier.id}>
                      <Paper
                        variant="outlined"
                        sx={{
                          p: 2,
                          borderColor: supplier.is_preferred ? 'success.main' : 'divider',
                          borderWidth: supplier.is_preferred ? 2 : 1
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1" fontWeight="600">
                              {supplier.name}
                            </Typography>
                            {supplier.is_preferred && (
                              <Chip
                                icon={<StarIcon />}
                                label="Preferred"
                                color="success"
                                size="small"
                              />
                            )}
                          </Box>
                          <Box>
                            <Tooltip title="Edit">
                              <IconButton size="small" onClick={() => handleEditSupplier(supplier)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => {
                                  setSelectedSupplier(supplier);
                                  setDeleteDialogOpen(true);
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                        
                        {supplier.website && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <LinkIcon fontSize="small" />
                              <a href={supplier.website} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
                                {supplier.website}
                              </a>
                            </Typography>
                          </Box>
                        )}
                        
                        {supplier.pricing_url && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <LinkIcon fontSize="small" />
                              <a href={supplier.pricing_url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
                                Pricing Page
                              </a>
                            </Typography>
                          </Box>
                        )}
                        
                        {supplier.notes && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {supplier.notes}
                          </Typography>
                        )}
                        
                        <Button
                          size="small"
                          startIcon={refreshing === supplier.id ? <CircularProgress size={16} /> : <RefreshIcon />}
                          onClick={() => handleRefreshPricing(supplier.id)}
                          disabled={refreshing === supplier.id}
                          sx={{ mt: 1 }}
                        >
                          Refresh Pricing
                        </Button>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No suppliers in this category yet.
                </Typography>
              )}
            </CardContent>
          </Card>
        );
      })}

      {/* Category Dialog */}
      <Dialog open={categoryDialogOpen} onClose={() => setCategoryDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedCategory ? 'Edit Category' : 'Add Category'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Category Name"
            fullWidth
            variant="outlined"
            value={categoryFormData.name}
            onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={categoryFormData.description}
            onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCategoryDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveCategory} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Supplier Dialog */}
      <Dialog open={supplierDialogOpen} onClose={() => setSupplierDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedSupplier ? 'Edit Supplier' : 'Add Supplier'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Supplier Name"
                fullWidth
                required
                value={supplierFormData.name}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={supplierFormData.category_id}
                  onChange={(e) => setSupplierFormData({ ...supplierFormData, category_id: e.target.value })}
                  label="Category"
                >
                  {categories.filter(c => c.is_active).map((cat) => (
                    <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Website"
                fullWidth
                type="url"
                value={supplierFormData.website}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, website: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Pricing URL"
                fullWidth
                type="url"
                value={supplierFormData.pricing_url}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, pricing_url: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="API Key (optional)"
                fullWidth
                type="password"
                value={supplierFormData.api_key}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, api_key: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={supplierFormData.is_preferred}
                    onChange={(e) => setSupplierFormData({ ...supplierFormData, is_preferred: e.target.checked })}
                  />
                }
                label="Preferred Supplier"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Notes"
                fullWidth
                multiline
                rows={3}
                value={supplierFormData.notes}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSupplierDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveSupplier} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedCategory ? `category "${selectedCategory.name}"` : selectedSupplier ? `supplier "${selectedSupplier.name}"` : 'this item'}?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => {
              if (selectedCategory) {
                handleDeleteCategory();
              } else if (selectedSupplier) {
                handleDeleteSupplier();
              }
            }}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Suppliers;

