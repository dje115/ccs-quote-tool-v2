import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import {
  AddCircleOutline as AddIcon,
  ContentCopy as DuplicateIcon,
  DeleteOutline as DeleteIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { quoteAPI } from '../services/api';
import PsychologyIcon from '@mui/icons-material/Psychology';
import ManualQuoteReviewDialog from './ManualQuoteReviewDialog';
import ManualQuoteAIBuildDialog from './ManualQuoteAIBuildDialog';

interface ManualQuoteBuilderProps {
  quoteId: string;
  initialTaxRate?: number | null;
  onTotalsChange?: (totals: {
    subtotal: number;
    tax_rate?: number;
    tax_amount?: number;
    total_amount?: number;
  }) => void;
}

interface ManualQuoteItem {
  id?: string;
  description: string;
  category?: string;
  section_name?: string;
  part_number?: string;
  supplier?: string;
  item_type: string;
  unit_type: string;
  quantity: number;
  unit_cost: number | null;
  unit_price: number;
  discount_rate: number;
  discount_amount: number;
  total_price: number;
  margin_percent?: number;
  tax_rate?: number;
  supplier_id?: string;
  is_optional: boolean;
  is_alternate: boolean;
  alternate_group?: string;
  bundle_parent_id?: string;
  metadata?: Record<string, any>;
  notes?: string;
  sort_order: number;
}

const toCurrency = (value: number) => `£${(value || 0).toFixed(2)}`;

const defaultLineItem = (sortOrder: number): ManualQuoteItem => ({
  description: '',
  category: '',
  section_name: '',
  part_number: '',
  supplier: '',
  item_type: 'standard',
  unit_type: 'each',
  quantity: 1,
  unit_cost: 0,
  unit_price: 0,
  discount_rate: 0,
  discount_amount: 0,
  total_price: 0,
  is_optional: false,
  is_alternate: false,
  alternate_group: '',
  bundle_parent_id: '',
  metadata: {},
  sort_order: sortOrder
});

const numberInputSx = {
  '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
    WebkitAppearance: 'none',
    margin: 0
  },
  '& input[type=number]': {
    MozAppearance: 'textfield'
  }
};

const normalizeItem = (item: any, sortOrder: number): ManualQuoteItem => {
  const quantity = Number(item.quantity ?? 1) || 0;
  const unitPrice = Number(item.unit_price ?? 0) || 0;
  const discountRate = Number(item.discount_rate ?? 0) || 0;
  const hasExplicitDiscountAmount = item.discount_amount !== undefined && item.discount_amount !== null;
  const discountAmount = hasExplicitDiscountAmount
    ? Number(item.discount_amount) || 0
    : quantity * unitPrice * discountRate;
  const metadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};

  return {
    id: item.id,
    description: item.description || '',
    category: item.category || '',
    section_name: item.section_name || '',
    part_number: metadata.part_number || '',
    supplier: metadata.supplier || '',
    item_type: item.item_type || 'standard',
    unit_type: item.unit_type || 'each',
    quantity,
    unit_cost: item.unit_cost !== undefined && item.unit_cost !== null ? Number(item.unit_cost) : null,
    unit_price: unitPrice,
    discount_rate: discountRate,
    discount_amount: discountAmount,
    total_price: Number(item.total_price ?? quantity * unitPrice - discountAmount) || 0,
    margin_percent: item.margin_percent ?? undefined,
    tax_rate: item.tax_rate ?? undefined,
    supplier_id: item.supplier_id ?? undefined,
    is_optional: Boolean(item.is_optional),
    is_alternate: Boolean(item.is_alternate),
    alternate_group: item.alternate_group ?? undefined,
    bundle_parent_id: item.bundle_parent_id ?? undefined,
    metadata: item.metadata || {},
    notes: item.notes ?? '',
    sort_order: item.sort_order ?? sortOrder
  };
};

const ManualQuoteBuilder: React.FC<ManualQuoteBuilderProps> = ({
  quoteId,
  initialTaxRate,
  onTotalsChange
}) => {
  const [items, setItems] = useState<ManualQuoteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [taxRate, setTaxRate] = useState<number>(initialTaxRate ?? 0.2);
  const baselineSignature = useRef<string>('');
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [buildDialogOpen, setBuildDialogOpen] = useState(false);

  const syncBaseline = (nextItems: ManualQuoteItem[], rate: number) => {
    baselineSignature.current = JSON.stringify({
      items: nextItems.map((item) => ({
        ...item,
        // remove transient props for stable signature
        total_price: Number(item.total_price || 0)
      })),
      rate
    });
  };

  const computeSignature = (nextItems: ManualQuoteItem[], rate: number) =>
    JSON.stringify({
      items: nextItems.map((item) => ({
        ...item,
        total_price: Number(item.total_price || 0)
      })),
      rate
    });

  const isDirty = useMemo(
    () => computeSignature(items, taxRate) !== baselineSignature.current,
    [items, taxRate]
  );

  const totals = useMemo(() => {
    const subtotal = items.reduce((sum, item) => sum + (item.total_price || 0), 0);
    const taxAmount = subtotal * (taxRate || 0);
    const totalAmount = subtotal + taxAmount;
    return { subtotal, taxAmount, totalAmount };
  }, [items, taxRate]);

  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await quoteAPI.getItems(quoteId);
      const data = (response.data || []).map((item: any, index: number) =>
        normalizeItem(item, index + 1)
      );
      const initialItems = data.length ? data : [defaultLineItem(1)];
      setItems(initialItems);
      setTaxRate(initialTaxRate ?? 0.2);
      syncBaseline(initialItems, initialTaxRate ?? 0.2);
    } catch (error) {
      console.error('Failed to load quote items', error);
    } finally {
      setLoading(false);
    }
  }, [quoteId, initialTaxRate]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const recalcLine = (line: ManualQuoteItem, changedField?: keyof ManualQuoteItem): ManualQuoteItem => {
    const qty = Number(line.quantity) || 0;
    const unitPrice = Number(line.unit_price) || 0;
    let discountRate = Number(line.discount_rate) || 0;
    let discountAmount = Number(line.discount_amount) || 0;

    if (['quantity', 'unit_price', 'discount_rate'].includes(changedField || '')) {
      discountAmount = qty * unitPrice * discountRate;
    }

    const total = Math.max(qty * unitPrice - discountAmount, 0);
    return {
      ...line,
      quantity: qty,
      unit_price: unitPrice,
      discount_rate: discountRate,
      discount_amount: discountAmount,
      total_price: total
    };
  };

  const updateLine = (index: number, updater: (current: ManualQuoteItem) => ManualQuoteItem) => {
    setItems((prev) => {
      const clone = [...prev];
      const nextLine = updater(clone[index]);
      clone[index] = nextLine;
      return clone;
    });
  };

  const handleFieldChange = (
    index: number,
    field: keyof ManualQuoteItem,
    value: string | number | boolean
  ) => {
    updateLine(index, (line) => {
      let nextValue: any = value;
      if (field === 'quantity' || field === 'unit_price' || field === 'unit_cost' || field === 'discount_amount') {
        nextValue = Number(value) || 0;
      }
      if (field === 'discount_rate') {
        nextValue = Number(value) || 0;
      }
      const updated = {
        ...line,
        [field]: nextValue
      } as ManualQuoteItem;
      return recalcLine(updated, field);
    });
  };

  const handleDiscountPercentChange = (index: number, percent: number) => {
    const decimal = (Number(percent) || 0) / 100;
    updateLine(index, (line) => recalcLine({ ...line, discount_rate: decimal }, 'discount_rate'));
  };

  const handleAddLine = () => {
    setItems((prev) => [...prev, defaultLineItem(prev.length + 1)]);
  };

  const handleDuplicateLine = (index: number) => {
    setItems((prev) => {
      const clone = [...prev];
      const source = clone[index];
      const duplicated: ManualQuoteItem = {
        ...source,
        id: undefined,
        sort_order: clone.length + 1
      };
      clone.splice(index + 1, 0, duplicated);
      return clone;
    });
  };

  const handleDeleteLine = (index: number) => {
    setItems((prev) => {
      if (prev.length === 1) {
        return [defaultLineItem(1)];
      }
      return prev.filter((_, idx) => idx !== index).map((item, idx) => ({ ...item, sort_order: idx + 1 }));
    });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const payloadItems = items.map((item, index) => ({
        id: item.id,
        description: item.description,
        category: item.category,
        item_type: item.item_type,
        unit_type: item.unit_type,
        section_name: item.section_name,
        quantity: item.quantity,
        unit_cost: item.unit_cost,
        unit_price: item.unit_price,
        discount_rate: item.discount_rate,
        discount_amount: item.discount_amount,
        margin_percent: item.margin_percent,
        tax_rate: item.tax_rate,
        supplier_id: item.supplier_id,
        is_optional: item.is_optional,
        is_alternate: item.is_alternate,
        alternate_group: item.alternate_group || null,
        bundle_parent_id: item.bundle_parent_id || null,
        metadata: {
          ...(item.metadata || {}),
          part_number: item.part_number || undefined,
          supplier: item.supplier || undefined
        },
        notes: item.notes,
        sort_order: index + 1
      }));

      const response = await quoteAPI.bulkUpdateItems(quoteId, {
        items: payloadItems,
        tax_rate: taxRate
      });

      const updatedItems = (response.data?.items || payloadItems).map((item: any, idx: number) =>
        normalizeItem(item, idx + 1)
      );
      setItems(updatedItems);
      const appliedTaxRate =
        response.data?.tax_rate !== undefined && response.data?.tax_rate !== null
          ? response.data.tax_rate
          : taxRate;
      setTaxRate(appliedTaxRate);
      syncBaseline(updatedItems, appliedTaxRate);
      onTotalsChange?.({
        subtotal: response.data?.subtotal ?? totals.subtotal,
        tax_rate: appliedTaxRate,
        tax_amount: response.data?.tax_amount,
        total_amount: response.data?.total_amount
      });
    } catch (error) {
      console.error('Failed to save quote items', error);
      alert('Unable to save line items. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    void loadItems();
  };

  const handleTaxRateChange = (value: number) => {
    const decimal = Math.max(0, value) / 100;
    setTaxRate(decimal);
  };

  const toggleRowSelection = (rowIndex: number, additive: boolean) => {
    setSelectedRows((prev) => {
      if (additive) {
        if (prev.includes(rowIndex)) {
          return prev.filter((idx) => idx !== rowIndex);
        }
        return [...prev, rowIndex];
      }
      return [rowIndex];
    });
  };

  const handleRowClick = (rowIndex: number, event: React.MouseEvent) => {
    toggleRowSelection(rowIndex, event.metaKey || event.ctrlKey);
  };

  const focusRow = (rowIndex: number) => {
    const targetRow = rowRefs.current[rowIndex];
    if (targetRow) {
      const input = targetRow.querySelector<HTMLInputElement | HTMLTextAreaElement>('input, textarea');
      input?.focus();
      setSelectedRows([rowIndex]);
    }
  };

  const handleRowKeyDown = (event: React.KeyboardEvent, rowIndex: number) => {
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
      event.preventDefault();
      const direction = event.key === 'ArrowUp' ? -1 : 1;
      const nextIndex = Math.min(Math.max(rowIndex + direction, 0), items.length - 1);
      focusRow(nextIndex);
    }

    if (event.key === 'Delete') {
      event.preventDefault();
      const targets = selectedRows.length ? selectedRows : [rowIndex];
      setItems((prev) => {
        const filtered = prev.filter((_item, idx) => !targets.includes(idx));
        return filtered.length ? filtered : [defaultLineItem(1)];
      });
      setSelectedRows([]);
      return;
    }

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'd') {
      event.preventDefault();
      const targets = selectedRows.length ? selectedRows : [rowIndex];
      setItems((prev) => {
        const clone = [...prev];
        targets
          .sort((a, b) => a - b)
          .forEach((idx, offset) => {
            const source = clone[idx + offset];
            const duplicated: ManualQuoteItem = {
              ...source,
              id: undefined,
              sort_order: clone.length + 1
            };
            clone.splice(idx + offset + 1, 0, duplicated);
          });
        return clone;
      });
    }

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      handleSave();
    }
  };

  const isRowSelected = (rowIndex: number) => selectedRows.includes(rowIndex);

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2} flexWrap="wrap" gap={2}>
        <Stack direction="row" spacing={1}>
          <Button startIcon={<AddIcon />} variant="outlined" onClick={handleAddLine}>
            Add Line
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            variant="text"
            onClick={handleReset}
            disabled={loading || saving}
          >
            Reset
          </Button>
          <Button
            startIcon={<PsychologyIcon />}
            variant="text"
            onClick={() => setReviewDialogOpen(true)}
            disabled={loading}
          >
            AI Quote Review
          </Button>
          <Button
            startIcon={<AutoAwesomeIcon />}
            variant="text"
            onClick={() => setBuildDialogOpen(true)}
            disabled={loading}
          >
            AI Build Quote
          </Button>
        </Stack>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            label="Tax Rate (%)"
            type="number"
            size="small"
            value={((taxRate || 0) * 100).toFixed(2)}
            onChange={(event) => handleTaxRateChange(Number(event.target.value))}
            InputLabelProps={{ shrink: true }}
          />
          <Tooltip title={isDirty ? 'Save changes' : 'No pending changes'}>
            <span>
              <Button
                startIcon={<SaveIcon />}
                variant="contained"
                disabled={!isDirty || saving}
                onClick={handleSave}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </span>
          </Tooltip>
        </Stack>
      </Box>

      <Box sx={{ position: 'relative', minHeight: items.length ? undefined : 200 }}>
        {loading ? (
          <Box display="flex" alignItems="center" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        ) : (
          <Table size="small" sx={{ minWidth: 1200 }}>
            <TableHead>
              <TableRow>
                <TableCell rowSpan={2}>Section</TableCell>
                <TableCell colSpan={7}>Description &amp; Pricing</TableCell>
                <TableCell rowSpan={2}>Optional</TableCell>
                <TableCell rowSpan={2}>Alternate</TableCell>
                <TableCell rowSpan={2}>Grouping</TableCell>
                <TableCell rowSpan={2}>Actions</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Part #</TableCell>
                <TableCell>Supplier</TableCell>
                <TableCell>Qty</TableCell>
                <TableCell>Unit Cost</TableCell>
                <TableCell>Unit Price</TableCell>
                <TableCell>Discount %</TableCell>
                <TableCell>Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item, index) => (
                <React.Fragment key={item.id || `new-${index}`}>
                  <TableRow
                    ref={(ref) => (rowRefs.current[index] = ref)}
                    hover
                    selected={isRowSelected(index)}
                    onClick={(event) => handleRowClick(index, event)}
                    tabIndex={0}
                    onKeyDown={(event) => handleRowKeyDown(event, index)}
                  >
                    <TableCell rowSpan={2} sx={{ verticalAlign: 'top' }}>
                      <TextField
                        size="small"
                        placeholder="Section"
                        fullWidth
                        value={item.section_name || ''}
                        onChange={(event) => handleFieldChange(index, 'section_name', event.target.value)}
                      />
                    </TableCell>
                    <TableCell colSpan={7}>
                      <TextField
                        size="small"
                        placeholder="Description"
                        fullWidth
                        multiline
                        minRows={3}
                        value={item.description}
                        onChange={(event) => handleFieldChange(index, 'description', event.target.value)}
                      />
                    </TableCell>
                    <TableCell rowSpan={2} align="center">
                      <Checkbox
                        checked={item.is_optional}
                        onChange={(event) => handleFieldChange(index, 'is_optional', event.target.checked)}
                      />
                    </TableCell>
                    <TableCell rowSpan={2} align="center">
                      <Checkbox
                        checked={item.is_alternate}
                        onChange={(event) => handleFieldChange(index, 'is_alternate', event.target.checked)}
                      />
                    </TableCell>
                    <TableCell rowSpan={2}>
                      <Stack spacing={1}>
                        <TextField
                          size="small"
                          label="Alt Group"
                          value={item.alternate_group || ''}
                          onChange={(event) => handleFieldChange(index, 'alternate_group', event.target.value)}
                        />
                        <TextField
                          size="small"
                          label="Bundle ID"
                          value={item.bundle_parent_id || ''}
                          onChange={(event) => handleFieldChange(index, 'bundle_parent_id', event.target.value)}
                        />
                      </Stack>
                    </TableCell>
                    <TableCell rowSpan={2}>
                      <Tooltip title="Duplicate line">
                        <IconButton onClick={() => handleDuplicateLine(index)} size="small">
                          <DuplicateIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete line">
                        <IconButton onClick={() => handleDeleteLine(index)} size="small">
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  <TableRow
                    hover
                    selected={isRowSelected(index)}
                    onClick={(event) => handleRowClick(index, event)}
                    sx={{ '& td': { borderTop: 'none' } }}
                  >
                    <TableCell sx={{ width: '120px', minWidth: '120px' }}>
                      <TextField
                        size="small"
                        placeholder="Part number"
                        fullWidth
                        value={item.part_number || ''}
                        onChange={(event) => handleFieldChange(index, 'part_number', event.target.value)}
                        inputProps={{ style: { fontSize: '0.875rem' } }}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '6px 8px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ width: '140px', minWidth: '140px' }}>
                      <TextField
                        size="small"
                        placeholder="Supplier"
                        fullWidth
                        value={item.supplier || ''}
                        onChange={(event) => handleFieldChange(index, 'supplier', event.target.value)}
                        inputProps={{ style: { fontSize: '0.875rem' } }}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '6px 8px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ width: '80px', minWidth: '80px' }}>
                      <TextField
                        size="small"
                        type="number"
                        fullWidth
                        inputProps={{ min: 0, step: 1, style: { fontSize: '0.875rem', textAlign: 'center' } }}
                        sx={{
                          ...numberInputSx,
                          '& .MuiInputBase-input': {
                            padding: '6px 8px'
                          }
                        }}
                        value={item.quantity}
                        onChange={(event) => handleFieldChange(index, 'quantity', Number(event.target.value))}
                      />
                    </TableCell>
                    <TableCell sx={{ width: '100px', minWidth: '100px' }}>
                      <TextField
                        size="small"
                        type="number"
                        fullWidth
                        inputProps={{ min: 0, step: 0.01, style: { fontSize: '0.875rem', textAlign: 'right' } }}
                        sx={{
                          ...numberInputSx,
                          '& .MuiInputBase-input': {
                            padding: '6px 8px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }
                        }}
                        value={item.unit_cost ?? 0}
                        onChange={(event) => handleFieldChange(index, 'unit_cost', Number(event.target.value))}
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="number"
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                        sx={numberInputSx}
                        value={item.unit_price}
                        onChange={(event) => handleFieldChange(index, 'unit_price', Number(event.target.value))}
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="number"
                        fullWidth
                        inputProps={{ min: 0, step: 0.5 }}
                        sx={numberInputSx}
                        value={((item.discount_rate || 0) * 100).toFixed(2)}
                        onChange={(event) => handleDiscountPercentChange(index, Number(event.target.value))}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography fontWeight={600}>{toCurrency(item.total_price)}</Typography>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        )}
      </Box>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" mt={3}>
        <Box>
          <Typography variant="subtitle2" color="text.secondary">
            Summary
          </Typography>
          <Typography variant="body1">Subtotal: {toCurrency(totals.subtotal)}</Typography>
          <Typography variant="body1">
            Tax ({((taxRate || 0) * 100).toFixed(2)}%): {toCurrency(totals.taxAmount)}
          </Typography>
          <Typography variant="h6" mt={1}>
            Total: {toCurrency(totals.totalAmount)}
          </Typography>
        </Box>
        {!items.length && (
          <Alert severity="info" sx={{ flex: 1 }}>
            No line items yet. Use “Add Line” to start building your manual quote.
          </Alert>
        )}
      </Stack>
      <ManualQuoteReviewDialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        quoteId={quoteId}
      />
      <ManualQuoteAIBuildDialog
        open={buildDialogOpen}
        onClose={() => setBuildDialogOpen(false)}
        quoteId={quoteId}
        taxRate={taxRate}
        onCompleted={async () => {
          await loadItems();
        }}
      />
    </Paper>
  );
};

export default ManualQuoteBuilder;
