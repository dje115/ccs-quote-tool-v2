import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
  IconButton,
  Box,
  Typography,
  Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

interface ContactDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (contactData: any) => Promise<void>;
  contact?: any; // If provided, we're editing; otherwise, creating new
  customerId: string;
}

const ContactDialog: React.FC<ContactDialogProps> = ({
  open,
  onClose,
  onSave,
  contact,
  customerId
}) => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    job_title: '',
    role: 'other',
    email: '',
    phone: '',
    is_primary: false,
    notes: ''
  });
  const [additionalEmails, setAdditionalEmails] = useState<Array<{email: string, type: string, is_primary: boolean}>>([]);
  const [additionalPhones, setAdditionalPhones] = useState<Array<{number: string, type: string, is_primary: boolean}>>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Populate form when editing
  useEffect(() => {
    if (contact) {
      setFormData({
        first_name: contact.first_name || '',
        last_name: contact.last_name || '',
        job_title: contact.job_title || '',
        role: contact.role || 'other',
        email: contact.email || '',
        phone: contact.phone || '',
        is_primary: contact.is_primary || false,
        notes: contact.notes || ''
      });
      setAdditionalEmails(contact.emails || []);
      setAdditionalPhones(contact.phones || []);
    } else {
      // Reset form for new contact
      setFormData({
        first_name: '',
        last_name: '',
        job_title: '',
        role: 'other',
        email: '',
        phone: '',
        is_primary: false,
        notes: ''
      });
      setAdditionalEmails([]);
      setAdditionalPhones([]);
    }
    setError(null);
  }, [contact, open]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      const dataToSave = {
        ...formData,
        customer_id: customerId,
        emails: additionalEmails.length > 0 ? additionalEmails : null,
        phones: additionalPhones.length > 0 ? additionalPhones : null
      };
      
      await onSave(dataToSave);
      onClose();
    } catch (err: any) {
      console.error('Error saving contact:', err);
      setError(err.response?.data?.detail || 'Failed to save contact');
    } finally {
      setSaving(false);
    }
  };

  const addEmail = () => {
    setAdditionalEmails([...additionalEmails, { email: '', type: 'work', is_primary: false }]);
  };

  const removeEmail = (index: number) => {
    setAdditionalEmails(additionalEmails.filter((_, i) => i !== index));
  };

  const updateEmail = (index: number, field: string, value: any) => {
    const updated = [...additionalEmails];
    updated[index] = { ...updated[index], [field]: value };
    setAdditionalEmails(updated);
  };

  const addPhone = () => {
    setAdditionalPhones([...additionalPhones, { number: '', type: 'mobile', is_primary: false }]);
  };

  const removePhone = (index: number) => {
    setAdditionalPhones(additionalPhones.filter((_, i) => i !== index));
  };

  const updatePhone = (index: number, field: string, value: any) => {
    const updated = [...additionalPhones];
    updated[index] = { ...updated[index], [field]: value };
    setAdditionalPhones(updated);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {contact ? 'Edit Contact' : 'Add New Contact'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                required
                label="First Name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                variant="outlined"
              />
            </Grid>
            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                required
                label="Last Name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                variant="outlined"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Job Title"
                name="job_title"
                value={formData.job_title}
                onChange={handleChange}
                variant="outlined"
                placeholder="e.g., Managing Director"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                select
                label="Role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                variant="outlined"
              >
                <MenuItem value="decision_maker">Decision Maker</MenuItem>
                <MenuItem value="influencer">Influencer</MenuItem>
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="technical_contact">Technical Contact</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </TextField>
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                variant="outlined"
                placeholder="contact@example.com"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                variant="outlined"
                placeholder="01234 567890 or 07700 123456"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_primary}
                    onChange={handleChange}
                    name="is_primary"
                  />
                }
                label="Primary Contact"
                sx={{ mt: 1 }}
              />
            </Grid>

            {/* Additional Emails Section */}
            <Grid size={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  Additional Email Addresses
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={addEmail}
                  variant="outlined"
                >
                  Add Email
                </Button>
              </Box>
              
              {additionalEmails.map((emailItem, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 5
                    }}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Email Address"
                      type="email"
                      value={emailItem.email}
                      onChange={(e) => updateEmail(index, 'email', e.target.value)}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 3
                    }}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Type"
                      value={emailItem.type}
                      onChange={(e) => updateEmail(index, 'type', e.target.value)}
                      variant="outlined"
                    >
                      <MenuItem value="work">Work</MenuItem>
                      <MenuItem value="personal">Personal</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 3
                    }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={emailItem.is_primary}
                          onChange={(e) => updateEmail(index, 'is_primary', e.target.checked)}
                        />
                      }
                      label="Primary"
                    />
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 1
                    }}>
                    <IconButton
                      color="error"
                      onClick={() => removeEmail(index)}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
            </Grid>

            {/* Additional Phones Section */}
            <Grid size={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  Additional Phone Numbers
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={addPhone}
                  variant="outlined"
                >
                  Add Phone
                </Button>
              </Box>
              
              {additionalPhones.map((phoneItem, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 5
                    }}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Phone Number"
                      value={phoneItem.number}
                      onChange={(e) => updatePhone(index, 'number', e.target.value)}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 3
                    }}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Type"
                      value={phoneItem.type}
                      onChange={(e) => updatePhone(index, 'type', e.target.value)}
                      variant="outlined"
                    >
                      <MenuItem value="mobile">Mobile</MenuItem>
                      <MenuItem value="work">Work</MenuItem>
                      <MenuItem value="home">Home</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 3
                    }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={phoneItem.is_primary}
                          onChange={(e) => updatePhone(index, 'is_primary', e.target.checked)}
                        />
                      }
                      label="Primary"
                    />
                  </Grid>
                  <Grid
                    size={{
                      xs: 12,
                      sm: 1
                    }}>
                    <IconButton
                      color="error"
                      onClick={() => removePhone(index)}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
            </Grid>

            <Grid size={12}>
              <Divider sx={{ my: 2 }} />
            </Grid>

            <Grid size={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                variant="outlined"
                placeholder="Additional information about this contact..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={saving || !formData.first_name || !formData.last_name}
          >
            {saving ? 'Saving...' : contact ? 'Update Contact' : 'Add Contact'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ContactDialog;
