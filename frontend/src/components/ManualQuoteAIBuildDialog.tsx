import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Alert
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { quoteAPI } from '../services/api';

interface ManualQuoteAIBuildDialogProps {
  open: boolean;
  onClose: () => void;
  quoteId: string;
  taxRate?: number | null;
  onCompleted?: () => void | Promise<void>;
}

interface AiBuildResponse {
  summary: string;
  assumptions: string[];
  append: boolean;
  items_added: number;
  totals: {
    subtotal: number;
    tax_rate: number;
    tax_amount: number;
    total_amount: number;
  };
  items_preview: Array<{
    section?: string | null;
    description: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    is_optional: boolean;
    category?: string | null;
    notes?: string | null;
  }>;
}

const ManualQuoteAIBuildDialog: React.FC<ManualQuoteAIBuildDialogProps> = ({
  open,
  onClose,
  quoteId,
  taxRate,
  onCompleted
}) => {
  const [prompt, setPrompt] = useState('');
  const [append, setAppend] = useState(false);
  const [targetMargin, setTargetMargin] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AiBuildResponse | null>(null);

  useEffect(() => {
    if (!open) {
      setPrompt('');
      setAppend(false);
      setTargetMargin('');
      setResult(null);
      setError(null);
      setLoading(false);
    }
  }, [open]);

  const handleBuild = async () => {
    if (!prompt.trim() || loading) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload: {
        prompt: string;
        append: boolean;
        tax_rate?: number;
        target_margin_percent?: number;
      } = {
        prompt: prompt.trim(),
        append
      };
      if (typeof taxRate === 'number') {
        payload.tax_rate = taxRate;
      }
      if (targetMargin !== '') {
        const marginValue = Number(targetMargin);
        if (!Number.isNaN(marginValue)) {
          payload.target_margin_percent = marginValue;
        }
      }

      const response = await quoteAPI.aiManualBuild(quoteId, payload);
      setResult(response.data);
      await onCompleted?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to build quote with AI.');
    } finally {
      setLoading(false);
    }
  };

  const disableSubmit = !prompt.trim() || loading;
  const taxPercent =
    typeof (result?.totals?.tax_rate ?? taxRate) === 'number'
      ? ((result?.totals?.tax_rate ?? taxRate) || 0) * 100
      : 0;

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesomeIcon color="primary" />
        AI Quote Builder
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Describe what you need and QuoteBuilderAI will create structured line items (hardware, software, labour)
          and apply them to this quote. The existing manual builder can then refine the details.
        </Typography>

        <Stack spacing={2}>
          <TextField
            label="What should we build?"
            placeholder="e.g. Design an HP ProLiant server refresh for 200 users with backup storage and install services."
            multiline
            minRows={3}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            disabled={loading}
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <FormControlLabel
              control={<Checkbox checked={append} onChange={(event) => setAppend(event.target.checked)} />}
              disabled={loading}
              label="Append to existing manual line items"
            />
            <TextField
              label="Target margin % (optional)"
              type="number"
              size="small"
              value={targetMargin}
              onChange={(event) => setTargetMargin(event.target.value)}
              disabled={loading}
              sx={{ width: 200 }}
            />
          </Stack>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Box sx={{ mt: 3 }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {result.summary}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Added {result.items_added} line item{result.items_added === 1 ? '' : 's'} (
                {result.append ? 'appended to existing items' : 'replaced previous manual items'}).
              </Typography>
              <Typography variant="body2">
                Subtotal: £{(result.totals?.subtotal ?? 0).toFixed(2)} • Tax ({taxPercent.toFixed(2)}%): £
                {(result.totals?.tax_amount ?? 0).toFixed(2)} • Total: £{(result.totals?.total_amount ?? 0).toFixed(2)}
              </Typography>
            </Alert>

            {result.assumptions?.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Assumptions</Typography>
                <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                  {result.assumptions.map((item, index) => (
                    <li key={index}>
                      <Typography variant="body2">{item}</Typography>
                    </li>
                  ))}
                </ul>
              </Box>
            )}

            {result.items_preview?.length > 0 && (
              <Box sx={{ maxHeight: 240, overflow: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Section</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Qty</TableCell>
                      <TableCell align="right">Unit Price</TableCell>
                      <TableCell align="right">Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.items_preview.map((item, index) => (
                      <TableRow key={`${item.description}-${index}`}>
                        <TableCell>{item.section || 'General'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {item.description}
                          </Typography>
                          {item.notes && (
                            <Typography variant="caption" color="text.secondary">
                              {item.notes}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">{item.quantity.toFixed(2)}</TableCell>
                        <TableCell align="right">£{item.unit_price.toFixed(2)}</TableCell>
                        <TableCell align="right">£{item.total_price.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Close
        </Button>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <AutoAwesomeIcon fontSize="small" />}
          onClick={handleBuild}
          disabled={disableSubmit}
        >
          {loading ? 'Building...' : result ? 'Build Again' : 'Build Quote'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManualQuoteAIBuildDialog;
