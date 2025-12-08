import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel
} from '@mui/material';
import {
  AccessTime as AccessTimeIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface TimeTrackingDialogProps {
  open: boolean;
  onClose: () => void;
  ticketId: string;
  onTimeEntryCreated: () => void;
  existingEntry?: any; // For editing
}

const ACTIVITY_TYPES = [
  { value: 'work', label: 'Work' },
  { value: 'research', label: 'Research' },
  { value: 'communication', label: 'Communication' },
  { value: 'meeting', label: 'Meeting' },
  { value: 'other', label: 'Other' }
];

const TimeTrackingDialog: React.FC<TimeTrackingDialogProps> = ({
  open,
  onClose,
  ticketId,
  onTimeEntryCreated,
  existingEntry
}) => {
  const [hours, setHours] = useState(existingEntry ? parseFloat(existingEntry.hours) : '');
  const [description, setDescription] = useState(existingEntry?.description || '');
  const [activityType, setActivityType] = useState(existingEntry?.activity_type || 'work');
  const [billable, setBillable] = useState(existingEntry?.billable || false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setError(null);

    // Validation
    if (!hours || parseFloat(hours.toString()) <= 0) {
      setError('Please enter a valid number of hours');
      return;
    }

    setSaving(true);
    try {
      const data = {
        hours: parseFloat(hours.toString()),
        description: description || undefined,
        activity_type: activityType,
        billable: billable
      };

      if (existingEntry) {
        await helpdeskAPI.updateTimeEntry(ticketId, existingEntry.id, data);
      } else {
        await helpdeskAPI.createTimeEntry(ticketId, data);
      }

      onTimeEntryCreated();
      onClose();
      
      // Reset form
      setHours('');
      setDescription('');
      setActivityType('work');
      setBillable(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save time entry');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccessTimeIcon color="primary" />
          <Typography variant="h6">
            {existingEntry ? 'Edit Time Entry' : 'Log Time'}
          </Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Hours"
          type="number"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
          inputProps={{ min: 0, step: 0.25 }}
          sx={{ mb: 2 }}
          helperText="Enter time in hours (e.g., 1.5 for 1 hour 30 minutes)"
          required
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Activity Type</InputLabel>
          <Select
            value={activityType}
            label="Activity Type"
            onChange={(e) => setActivityType(e.target.value)}
          >
            {ACTIVITY_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="Description"
          multiline
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What did you work on?"
          sx={{ mb: 2 }}
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={billable}
              onChange={(e) => setBillable(e.target.checked)}
            />
          }
          label="Billable"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={<AccessTimeIcon />}
          disabled={saving || !hours}
        >
          {saving ? 'Saving...' : existingEntry ? 'Update' : 'Log Time'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TimeTrackingDialog;

