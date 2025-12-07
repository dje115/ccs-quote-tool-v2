import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Divider,
  Grid,
  Chip
} from '@mui/material';
import {
  Keyboard as KeyboardIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { COMMON_SHORTCUTS } from '../hooks/useKeyboardShortcuts';

interface KeyboardShortcutsHelpProps {
  open: boolean;
  onClose: () => void;
  customShortcuts?: Array<{ key: string; ctrl?: boolean; shift?: boolean; alt?: boolean; description: string }>;
}

const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  open,
  onClose,
  customShortcuts = []
}) => {
  const formatKey = (shortcut: { key: string; ctrl?: boolean; shift?: boolean; alt?: boolean }) => {
    const parts: string[] = [];
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.shift) parts.push('Shift');
    if (shortcut.alt) parts.push('Alt');
    
    // Format the key
    let key = shortcut.key;
    if (key === ' ') key = 'Space';
    if (key === '/') key = '/';
    if (key.length === 1 && key.match(/[a-z]/i)) {
      key = key.toUpperCase();
    }
    parts.push(key);
    
    return parts.join(' + ');
  };

  const allShortcuts = [
    ...Object.values(COMMON_SHORTCUTS).map(s => ({ ...s, category: 'Common' })),
    ...customShortcuts.map(s => ({ ...s, category: 'Custom' }))
  ];

  const groupedShortcuts = allShortcuts.reduce((acc, shortcut) => {
    const category = (shortcut as any).category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<string, typeof allShortcuts>);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <KeyboardIcon />
          <Typography variant="h6">Keyboard Shortcuts</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {Object.entries(groupedShortcuts).map(([category, shortcuts]) => (
          <Box key={category} sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
              {category}
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {shortcuts.map((shortcut, index) => (
                <Grid size={{ xs: 12, sm: 6 }} key={index}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
                    <Typography variant="body2">{shortcut.description}</Typography>
                    <Chip
                      label={formatKey(shortcut)}
                      size="small"
                      variant="outlined"
                      sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}
                    />
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Box>
        ))}
        
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Note:</strong> Shortcuts work globally except when typing in input fields. 
            Ctrl/Cmd shortcuts (like Ctrl+S) work even in input fields.
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} startIcon={<CloseIcon />}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default KeyboardShortcutsHelp;

