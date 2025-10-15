import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Grid,
  Paper
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import WorkIcon from '@mui/icons-material/Work';
import PersonIcon from '@mui/icons-material/Person';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import BusinessIcon from '@mui/icons-material/Business';
import StarIcon from '@mui/icons-material/Star';

interface ContactDetailDialogProps {
  open: boolean;
  onClose: () => void;
  contact: any | null;
  onEdit?: () => void;
}

const ContactDetailDialog: React.FC<ContactDetailDialogProps> = ({
  open,
  onClose,
  contact,
  onEdit
}) => {
  if (!contact) return null;

  const getRoleLabel = (role: string) => {
    const roleMap: { [key: string]: string } = {
      'decision_maker': 'Decision Maker',
      'influencer': 'Influencer',
      'user': 'User',
      'technical_contact': 'Technical Contact',
      'other': 'Other'
    };
    return roleMap[role] || role;
  };

  const getTypeColor = (type: string) => {
    const colorMap: { [key: string]: 'primary' | 'secondary' | 'success' | 'warning' | 'info' } = {
      'work': 'primary',
      'personal': 'secondary',
      'mobile': 'success',
      'home': 'warning',
      'other': 'info'
    };
    return colorMap[type] || 'default';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PersonIcon color="primary" sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h5" component="div">
                {contact.first_name} {contact.last_name}
              </Typography>
              {contact.job_title && (
                <Typography variant="body2" color="text.secondary">
                  {contact.job_title}
                </Typography>
              )}
            </Box>
          </Box>
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Grid container spacing={3}>
          {/* Role & Status */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip 
                icon={<BusinessIcon />}
                label={getRoleLabel(contact.role)} 
                color="primary" 
                variant="outlined"
              />
              {contact.is_primary && (
                <Chip 
                  icon={<StarIcon />}
                  label="Primary Contact" 
                  color="success"
                />
              )}
            </Box>
          </Grid>

          {/* Primary Email */}
          {contact.email && (
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Primary Email
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <EmailIcon color="primary" />
                  <Typography variant="body1">
                    <a href={`mailto:${contact.email}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {contact.email}
                    </a>
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          )}

          {/* Additional Emails */}
          {contact.emails && contact.emails.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Additional Email Addresses
              </Typography>
              <List dense>
                {contact.emails.map((emailItem: any, index: number) => (
                  <ListItem 
                    key={index}
                    sx={{ 
                      bgcolor: 'background.paper',
                      mb: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1
                    }}
                  >
                    <ListItemIcon>
                      <EmailIcon color="action" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <a href={`mailto:${emailItem.email}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                          {emailItem.email}
                        </a>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip 
                            label={emailItem.type} 
                            size="small" 
                            color={getTypeColor(emailItem.type)}
                          />
                          {emailItem.is_primary && (
                            <Chip 
                              label="Primary" 
                              size="small" 
                              color="success"
                              icon={<StarIcon />}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          )}

          {/* Primary Phone */}
          {contact.phone && (
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                <Typography variant="subtitle2" color="success.main" gutterBottom>
                  Primary Phone
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PhoneIcon color="success" />
                  <Typography variant="body1">
                    <a href={`tel:${contact.phone}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {contact.phone}
                    </a>
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          )}

          {/* Additional Phones */}
          {contact.phones && contact.phones.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Additional Phone Numbers
              </Typography>
              <List dense>
                {contact.phones.map((phoneItem: any, index: number) => (
                  <ListItem 
                    key={index}
                    sx={{ 
                      bgcolor: 'background.paper',
                      mb: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1
                    }}
                  >
                    <ListItemIcon>
                      <PhoneIcon color="action" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <a href={`tel:${phoneItem.number}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                          {phoneItem.number}
                        </a>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip 
                            label={phoneItem.type} 
                            size="small" 
                            color={getTypeColor(phoneItem.type)}
                          />
                          {phoneItem.is_primary && (
                            <Chip 
                              label="Primary" 
                              size="small" 
                              color="success"
                              icon={<StarIcon />}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          )}

          {/* Notes */}
          {contact.notes && (
            <Grid item xs={12}>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Notes
              </Typography>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {contact.notes}
                </Typography>
              </Paper>
            </Grid>
          )}

          {/* Metadata */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {contact.created_at && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Created</Typography>
                  <Typography variant="body2">
                    {new Date(contact.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              )}
              {contact.updated_at && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Last Updated</Typography>
                  <Typography variant="body2">
                    {new Date(contact.updated_at).toLocaleDateString()}
                  </Typography>
                </Box>
              )}
            </Box>
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {onEdit && (
          <Button 
            onClick={onEdit} 
            variant="contained" 
            startIcon={<EditIcon />}
          >
            Edit Contact
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ContactDetailDialog;


