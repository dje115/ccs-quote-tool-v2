import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Button,
  IconButton,
  Tooltip,
  Alert,
  Divider,
  Grid,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { quoteAPI } from '../services/api';

interface PartsListEditorProps {
  quoteId: string;
  documentType: string;
  document: any;
  onSave?: () => void;
  onCancel?: () => void;
}

interface LineItem {
  id: string;
  line_number?: number;
  description: string;
  part_number: string;
  quantity: number;
  unit_price: number;
  cost_price: number;
  total_price: number;
  category?: string;
  supplier?: string;
  notes?: string;
}

const PartsListEditor: React.FC<PartsListEditorProps> = ({
  quoteId,
  documentType,
  document,
  onSave,
  onCancel
}) => {
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subtotal, setSubtotal] = useState(0);
  const [taxRate, setTaxRate] = useState(20); // Default 20% VAT
  const [taxAmount, setTaxAmount] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);

  useEffect(() => {
    loadLineItems();
  }, [document]);

  useEffect(() => {
    calculateTotals();
  }, [lineItems, taxRate]);

  const loadLineItems = () => {
    if (!document || !document.content) {
      setLineItems([]);
      return;
    }

    // Extract line items from document content
    const content = document.content;
    let items: LineItem[] = [];

    // Check if content has line_items array
    if (content.line_items && Array.isArray(content.line_items)) {
      items = content.line_items;
    } else if (content.sections && Array.isArray(content.sections)) {
      // Fallback: extract from sections
      const partsSection = content.sections.find((s: any) => s.id === 'parts_list');
      if (partsSection && Array.isArray(partsSection.content)) {
        items = partsSection.content;
      }
    }

    // Ensure all items have required fields
    items = items.map((item: any, index: number) => ({
      id: item.id || `item_${Date.now()}_${index}`,
      line_number: item.line_number || index + 1,
      description: item.description || item.category || '',
      part_number: item.part_number || '',
      quantity: typeof item.quantity === 'number' ? item.quantity : parseFloat(item.quantity) || 1,
      unit_price: typeof item.unit_price === 'number' ? item.unit_price : parseFloat(item.unit_price) || 0,
      cost_price: typeof item.cost_price === 'number' ? item.cost_price : parseFloat(item.cost_price) || 0,
      total_price: typeof item.total_price === 'number' ? item.total_price : parseFloat(item.total_price) || 0,
      category: item.category || '',
      supplier: item.supplier || '',
      notes: item.notes || ''
    }));

    setLineItems(items);
  };

  const calculateTotals = () => {
    const subtotal = lineItems.reduce((sum, item) => sum + (item.total_price || 0), 0);
    const tax = (subtotal * taxRate) / 100;
    const total = subtotal + tax;

    setSubtotal(subtotal);
    setTaxAmount(tax);
    setTotalAmount(total);
  };

  const handleAddLine = () => {
    const newItem: LineItem = {
      id: `item_${Date.now()}`,
      line_number: lineItems.length + 1,
      description: '',
      part_number: '',
      quantity: 1,
      unit_price: 0,
      cost_price: 0,
      total_price: 0,
      category: '',
      supplier: '',
      notes: ''
    };
    setLineItems([...lineItems, newItem]);
  };

  const handleDeleteLine = (id: string) => {
    setLineItems(lineItems.filter(item => item.id !== id));
  };

  const handleUpdateLine = (id: string, field: keyof LineItem, value: any) => {
    setLineItems(lineItems.map(item => {
      if (item.id === id) {
        const updated = { ...item, [field]: value };
        
        // Auto-calculate total_price when quantity or unit_price changes
        if (field === 'quantity' || field === 'unit_price') {
          updated.total_price = (updated.quantity || 0) * (updated.unit_price || 0);
        }
        
        return updated;
      }
      return item;
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      // Update document content with line items
      const updatedContent = {
        ...document.content,
        line_items: lineItems.map((item, index) => ({
          ...item,
          line_number: index + 1
        })),
        pricing_summary: {
          subtotal: subtotal,
          tax_rate: taxRate,
          tax_amount: taxAmount,
          total_amount: totalAmount
        },
        metadata: {
          ...document.content.metadata,
          last_edited: new Date().toISOString(),
          item_count: lineItems.length
        }
      };

      await quoteAPI.updateDocument(quoteId, documentType, {
        content: updatedContent,
        changes_summary: `Updated parts list: ${lineItems.length} line items`
      });

      if (onSave) {
        onSave();
      }
    } catch (error: any) {
      console.error('Error saving parts list:', error);
      setError(error.response?.data?.detail || 'Failed to save parts list');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Parts List Editor</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {onCancel && (
              <Button onClick={onCancel} variant="outlined" startIcon={<CancelIcon />}>
                Cancel
              </Button>
            )}
            <Button
              variant="contained"
              startIcon={saving ? <Box sx={{ width: 20, height: 20 }} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Divider sx={{ mb: 3 }} />

        {/* Line Items Table */}
        <TableContainer>
          <Table size="small" sx={{ minWidth: 1200 }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 50 }}>#</TableCell>
                <TableCell sx={{ minWidth: 300 }}>Description</TableCell>
                <TableCell sx={{ minWidth: 150 }}>Part Number</TableCell>
                <TableCell align="right" sx={{ width: 100 }}>Qty</TableCell>
                <TableCell align="right" sx={{ width: 120 }}>Unit Price</TableCell>
                <TableCell align="right" sx={{ width: 120 }}>Cost Price</TableCell>
                <TableCell align="right" sx={{ width: 120 }}>Total</TableCell>
                <TableCell sx={{ minWidth: 120 }}>Category</TableCell>
                <TableCell sx={{ minWidth: 150 }}>Supplier</TableCell>
                <TableCell sx={{ width: 80 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {lineItems.map((item, index) => (
                <TableRow key={item.id} hover>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      size="small"
                      value={item.description}
                      onChange={(e) => handleUpdateLine(item.id, 'description', e.target.value)}
                      placeholder="Item description"
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      size="small"
                      value={item.part_number}
                      onChange={(e) => handleUpdateLine(item.id, 'part_number', e.target.value)}
                      placeholder="Part #"
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      size="small"
                      value={item.quantity}
                      onChange={(e) => handleUpdateLine(item.id, 'quantity', parseFloat(e.target.value) || 0)}
                      inputProps={{ min: 0, step: 1 }}
                      sx={{ width: 80 }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      size="small"
                      value={item.unit_price}
                      onChange={(e) => handleUpdateLine(item.id, 'unit_price', parseFloat(e.target.value) || 0)}
                      inputProps={{ min: 0, step: 0.01 }}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">£</InputAdornment>
                      }}
                      sx={{ width: 120 }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      size="small"
                      value={item.cost_price}
                      onChange={(e) => handleUpdateLine(item.id, 'cost_price', parseFloat(e.target.value) || 0)}
                      inputProps={{ min: 0, step: 0.01 }}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">£</InputAdornment>
                      }}
                      sx={{ width: 120 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      £{item.total_price.toFixed(2)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      size="small"
                      value={item.category || ''}
                      onChange={(e) => handleUpdateLine(item.id, 'category', e.target.value)}
                      placeholder="Category"
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      size="small"
                      value={item.supplier || ''}
                      onChange={(e) => handleUpdateLine(item.id, 'supplier', e.target.value)}
                      placeholder="Supplier"
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Delete line">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteLine(item.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {lineItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No line items yet. Click "Add Line" to start.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            startIcon={<AddIcon />}
            onClick={handleAddLine}
            variant="outlined"
            size="small"
          >
            Add Line
          </Button>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Pricing Summary */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Tax Rate (%):</Typography>
              <TextField
                type="number"
                size="small"
                value={taxRate}
                onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                inputProps={{ min: 0, max: 100, step: 0.1 }}
                sx={{ width: 100 }}
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Subtotal:</Typography>
              <Typography variant="body2" fontWeight="medium">
                £{subtotal.toFixed(2)}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Tax ({taxRate}%):</Typography>
              <Typography variant="body2" fontWeight="medium">
                £{taxAmount.toFixed(2)}
              </Typography>
            </Box>
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="h6">Total:</Typography>
              <Typography variant="h6" fontWeight="bold" color="primary">
                £{totalAmount.toFixed(2)}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default PartsListEditor;

