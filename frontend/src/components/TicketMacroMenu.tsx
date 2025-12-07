import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  ListItemText,
  ListItemIcon,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Close as CloseIcon,
  Build as BuildIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface TicketMacro {
  id: string;
  name: string;
  description?: string;
  actions: Array<{ type: string; [key: string]: any }>;
  is_shared: boolean;
}

interface TicketMacroMenuProps {
  ticketId: string;
  onMacroExecuted?: () => void;
  onError?: (error: string) => void;
}

const TicketMacroMenu: React.FC<TicketMacroMenuProps> = ({
  ticketId,
  onMacroExecuted,
  onError
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [macros, setMacros] = useState<TicketMacro[]>([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  useEffect(() => {
    if (anchorEl) {
      loadMacros();
    }
  }, [anchorEl]);

  const loadMacros = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await helpdeskAPI.getMacros();
      setMacros(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load macros');
      if (onError) {
        onError(err.response?.data?.detail || 'Failed to load macros');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteMacro = async (macroId: string) => {
    setAnchorEl(null);
    setExecuting(macroId);
    setError(null);
    try {
      const response = await helpdeskAPI.executeMacro(ticketId, macroId);
      setExecutionResult(response.data);
      setSuccessDialogOpen(true);
      if (onMacroExecuted) {
        onMacroExecuted();
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to execute macro';
      setError(errorMsg);
      if (onError) {
        onError(errorMsg);
      }
    } finally {
      setExecuting(null);
    }
  };

  const getActionDescription = (action: any): string => {
    switch (action.type) {
      case 'update_status':
        return `Set status to ${action.value}`;
      case 'update_priority':
        return `Set priority to ${action.value}`;
      case 'assign':
        return 'Assign ticket';
      case 'add_tags':
        return `Add tags: ${action.tags?.join(', ')}`;
      case 'add_comment':
        return 'Add comment';
      case 'update_npa':
        return 'Update NPA';
      default:
        return action.type;
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        startIcon={<BuildIcon />}
        onClick={(e) => setAnchorEl(e.currentTarget)}
        size="small"
      >
        Run Macro
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 500
          }
        }}
      >
        <Box sx={{ p: 2, pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" fontWeight="bold">
              Ticket Macros
            </Typography>
            <IconButton size="small" onClick={() => setAnchorEl(null)}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 1, mt: 1 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </Box>

        <Divider />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : macros.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No macros available. Create macros to automate common workflows.
            </Typography>
          </Box>
        ) : (
          <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
            {macros.map((macro) => (
              <MenuItem
                key={macro.id}
                onClick={() => handleExecuteMacro(macro.id)}
                disabled={executing === macro.id}
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
                  {executing === macro.id ? (
                    <CircularProgress size={20} />
                  ) : (
                    <PlayIcon fontSize="small" color="action" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {macro.name}
                      </Typography>
                      {macro.is_shared && (
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
                    <Box sx={{ mt: 0.5 }}>
                      {macro.description && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {macro.description}
                        </Typography>
                      )}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {macro.actions.slice(0, 3).map((action, idx) => (
                          <Chip
                            key={idx}
                            label={getActionDescription(action)}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {macro.actions.length > 3 && (
                          <Chip
                            label={`+${macro.actions.length - 3} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  }
                />
              </MenuItem>
            ))}
          </Box>
        )}
      </Menu>

      {/* Execution Result Dialog */}
      <Dialog open={successDialogOpen} onClose={() => setSuccessDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon color="success" />
            Macro Executed Successfully
          </Box>
        </DialogTitle>
        <DialogContent>
          {executionResult?.executed_actions && executionResult.executed_actions.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Actions Completed:
              </Typography>
              {executionResult.executed_actions.map((action: string, idx: number) => (
                <Typography key={idx} variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                  • {action}
                </Typography>
              ))}
            </Box>
          )}
          {executionResult?.errors && executionResult.errors.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Warnings:
              </Typography>
              {executionResult.errors.map((error: string, idx: number) => (
                <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                  • {error}
                </Typography>
              ))}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSuccessDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TicketMacroMenu;

