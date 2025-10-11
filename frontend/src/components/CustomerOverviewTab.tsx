import React, { useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Chip,
  Button,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Alert
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Place as PlaceIcon,
  Business as BusinessIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Add as AddIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import ContactDetailDialog from './ContactDetailDialog';
import { useNavigate } from 'react-router-dom';

interface CustomerOverviewTabProps {
  customer: any;
  contacts: any[];
  onAddContact: () => void;
  onEditContact: (contact: any) => void;
  onConfirmRegistration: (confirmed: boolean) => void;
}

const CustomerOverviewTab: React.FC<CustomerOverviewTabProps> = ({
  customer,
  contacts,
  onAddContact,
  onEditContact,
  onConfirmRegistration
}) => {
  const navigate = useNavigate();
  const [selectedContact, setSelectedContact] = useState<any>(null);
  const [contactDetailOpen, setContactDetailOpen] = useState(false);

  const handleContactClick = (contact: any) => {
    setSelectedContact(contact);
    setContactDetailOpen(true);
  };

  const handleContactDetailClose = () => {
    setContactDetailOpen(false);
    setSelectedContact(null);
  };

  const handleEditFromDetail = () => {
    setContactDetailOpen(false);
    onEditContact(selectedContact);
  };

  // Get primary address from Google Maps locations
  const getPrimaryAddress = () => {
    if (customer?.google_maps_data?.locations && Array.isArray(customer.google_maps_data.locations)) {
      const excludedAddresses = customer.excluded_addresses || [];
      const activeLocations = customer.google_maps_data.locations.filter(
        (loc: any) => !excludedAddresses.includes(loc.place_id)
      );
      // For now, return the first active location
      // TODO: Allow user to set primary address
      return activeLocations[0] || null;
    }
    return null;
  };

  const primaryAddress = getPrimaryAddress();

  // Calculate health score based on data completeness and lead score
  const calculateHealthScore = () => {
    let score = 0;
    if (customer?.website) score += 8;
    if (customer?.main_email) score += 8;
    if (customer?.main_phone) score += 8;
    if (customer?.company_registration && customer?.registration_confirmed) score += 18;
    if (contacts?.length > 0) score += 12;
    if (customer?.ai_analysis_raw) score += 18;
    if (customer?.lead_score && customer.lead_score > 50) score += 12;
    if (customer?.website_data) score += 8; // Website scraped & analyzed
    if (customer?.linkedin_url || customer?.linkedin_data) score += 8; // LinkedIn found
    return Math.min(score, 100);
  };

  const healthScore = calculateHealthScore();

  return (
    <>
    <Grid container spacing={3}>
      {/* Left Column: Main Information */}
      <Grid item xs={12} md={8}>
        
        {/* Key Stats Dashboard */}
        <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight="bold">{customer?.lead_score || 0}</Typography>
                <Typography variant="caption">Lead Score</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight="bold">{healthScore}%</Typography>
                <Typography variant="caption">Health Score</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight="bold">{contacts?.length || 0}</Typography>
                <Typography variant="caption">Contacts</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Chip 
                  label={customer?.status || 'Unknown'} 
                  sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.2)', 
                    color: 'white',
                    fontWeight: 'bold'
                  }} 
                />
                <Typography variant="caption" display="block">Status</Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Company Information */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#1976d2' }}>
            <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Company Information
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Grid container spacing={2}>
            {/* Website */}
            {customer?.website && (
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <WebsiteIcon color="primary" />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="caption" color="text.secondary">Website</Typography>
                    <Typography>
                      <a href={customer.website} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2', textDecoration: 'none' }}>
                        {customer.website}
                      </a>
                    </Typography>
                  </Box>
                  <Button variant="outlined" size="small" href={customer.website} target="_blank">
                    Visit
                  </Button>
                </Box>
              </Grid>
            )}

            {/* Email */}
            {customer?.main_email && (
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <EmailIcon color="primary" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Email</Typography>
                    <Typography>{customer.main_email}</Typography>
                  </Box>
                </Box>
              </Grid>
            )}

            {/* Phone */}
            {customer?.main_phone && (
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PhoneIcon color="primary" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Phone</Typography>
                    <Typography>{customer.main_phone}</Typography>
                  </Box>
                </Box>
              </Grid>
            )}

            {/* Company Registration */}
            {customer?.company_registration && (
              <Grid item xs={12}>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Company Registration
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Chip 
                      label={customer.company_registration}
                      color={customer?.registration_confirmed ? 'success' : 'warning'}
                      size="medium"
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <input 
                        type="checkbox" 
                        id="registration_confirmed"
                        checked={customer?.registration_confirmed || false}
                        onChange={(e) => onConfirmRegistration(e.target.checked)}
                        style={{ cursor: 'pointer' }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Confirmed by human
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Grid>
            )}

            {/* Created & Updated Dates */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 3, justifyContent: 'space-between', flexWrap: 'wrap' }}>
                {customer?.created_at && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">Created</Typography>
                    <Typography variant="body2" fontWeight="600">
                      {new Date(customer.created_at).toLocaleDateString('en-GB', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </Typography>
                  </Box>
                )}
                {customer?.updated_at && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">Last Updated</Typography>
                    <Typography variant="body2" fontWeight="600">
                      {new Date(customer.updated_at).toLocaleDateString('en-GB', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Primary Address */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ color: '#1976d2' }}>
              <PlaceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Primary Address
            </Typography>
            <Button 
              variant="outlined" 
              size="small" 
              onClick={() => navigate(`/customers/${customer?.id}/edit`)}
              startIcon={<EditIcon />}
            >
              Manage Addresses
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />

          {primaryAddress ? (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'start', gap: 1, mb: 2 }}>
                <CheckCircleIcon color="success" sx={{ mt: 0.5 }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body1" fontWeight="600">{primaryAddress.name}</Typography>
                  <Typography variant="body2" color="text.secondary">{primaryAddress.formatted_address}</Typography>
                  {primaryAddress.phone && (
                    <Typography variant="body2" color="text.secondary">
                      <PhoneIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                      {primaryAddress.phone}
                    </Typography>
                  )}
                </Box>
              </Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={<PlaceIcon />}
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(primaryAddress.formatted_address)}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open in Google Maps
              </Button>
            </Box>
          ) : customer?.billing_address ? (
            <Box>
              <Typography variant="body1" fontWeight="600">Billing Address</Typography>
              <Typography variant="body2" color="text.secondary">{customer.billing_address}</Typography>
              {customer.billing_postcode && (
                <Typography variant="body2" color="text.secondary">{customer.billing_postcode}</Typography>
              )}
              <Button
                variant="outlined"
                size="small"
                startIcon={<PlaceIcon />}
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(customer.billing_address)}${customer.billing_postcode ? ' ' + encodeURIComponent(customer.billing_postcode) : ''}`}
                target="_blank"
                rel="noopener noreferrer"
                sx={{ mt: 1 }}
              >
                Open in Google Maps
              </Button>
            </Box>
          ) : (
            <Alert severity="info">
              No primary address set. Run AI Analysis to discover company locations, or add manually in the Addresses tab.
            </Alert>
          )}
        </Paper>

        {/* Website & Social Media Analysis */}
        {(customer?.website_data || customer?.linkedin_url || customer?.linkedin_data) && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#1976d2' }}>
              <WebsiteIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Website & Social Media
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* LinkedIn */}
            {(customer.linkedin_url || customer.linkedin_data) && (
              <Box sx={{ mb: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="subtitle2" fontWeight="600" gutterBottom sx={{ color: '#0077b5' }}>
                  🔗 LinkedIn Profile
                </Typography>
                {customer.linkedin_url && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <a href={customer.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: '#0077b5', textDecoration: 'none' }}>
                      {customer.linkedin_url} ↗
                    </a>
                  </Typography>
                )}
                {customer.linkedin_data && (
                  <Box sx={{ mt: 1 }}>
                    {customer.linkedin_data.linkedin_industry && (
                      <Chip label={customer.linkedin_data.linkedin_industry} size="small" sx={{ mr: 1, mb: 1 }} color="primary" />
                    )}
                    {customer.linkedin_data.linkedin_company_size && (
                      <Chip label={`Size: ${customer.linkedin_data.linkedin_company_size}`} size="small" sx={{ mr: 1, mb: 1 }} />
                    )}
                    {customer.linkedin_data.linkedin_founded && (
                      <Chip label={`Founded: ${customer.linkedin_data.linkedin_founded}`} size="small" sx={{ mb: 1 }} />
                    )}
                    {customer.linkedin_data.linkedin_description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                        "{customer.linkedin_data.linkedin_description}"
                      </Typography>
                    )}
                  </Box>
                )}
              </Box>
            )}

            {/* Website Analysis */}
            {customer.website_data && (
              <Box>
                {customer.website_data.website_title && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">Website Title</Typography>
                    <Typography variant="body1" fontWeight="600">{customer.website_data.website_title}</Typography>
                  </Box>
                )}
                
                {customer.website_data.website_description && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">Description</Typography>
                    <Typography variant="body2">{customer.website_data.website_description}</Typography>
                  </Box>
                )}

                {customer.website_data.key_phrases && Array.isArray(customer.website_data.key_phrases) && customer.website_data.key_phrases.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Key Topics & Keywords (AI-Extracted)
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {customer.website_data.key_phrases.slice(0, 15).map((phrase: any, idx: number) => (
                        <Chip 
                          key={idx}
                          label={Array.isArray(phrase) ? phrase[0] : phrase}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {customer.website_data.social_media && Array.isArray(customer.website_data.social_media) && customer.website_data.social_media.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Social Media & Links
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      {customer.website_data.social_media.slice(0, 5).map((link: string, idx: number) => (
                        <Typography key={idx} variant="body2">
                          <a href={link} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2', textDecoration: 'none' }}>
                            {link} ↗
                          </a>
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}

                {customer.website_data.contact_info && Array.isArray(customer.website_data.contact_info) && customer.website_data.contact_info.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Contact Info Found on Website
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      {customer.website_data.contact_info.slice(0, 5).map((contact: string, idx: number) => (
                        <Typography key={idx} variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {contact.includes('@') ? <EmailIcon sx={{ fontSize: 16 }} color="action" /> : 
                           contact.match(/\d/) ? <PhoneIcon sx={{ fontSize: 16 }} color="action" /> : null}
                          {contact}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}

                {customer.website_data.locations && Array.isArray(customer.website_data.locations) && customer.website_data.locations.length > 0 && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Locations Mentioned on Website
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {customer.website_data.locations.slice(0, 10).join(', ')}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        )}

        {/* Key Contacts */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ color: '#1976d2' }}>
              Key Contacts ({contacts?.length || 0})
            </Typography>
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={onAddContact}
              variant="outlined"
            >
              Add Contact
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />

          {!Array.isArray(contacts) || contacts.length === 0 ? (
            <Alert severity="info">No contacts yet. Add key contacts to improve relationship management.</Alert>
          ) : (
            <List>
              {contacts.slice(0, 5).map((contact) => (
                <ListItem 
                  key={contact.id} 
                  sx={{ 
                    border: '1px solid #e0e0e0', 
                    borderRadius: 1, 
                    mb: 1,
                    cursor: 'pointer',
                    '&:hover': { 
                      backgroundColor: '#f5f5f5',
                      borderColor: '#1976d2',
                      boxShadow: 1
                    }
                  }}
                  onClick={() => handleContactClick(contact)}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography fontWeight="600">
                          {contact.first_name} {contact.last_name}
                        </Typography>
                        {contact.is_primary && <Chip label="Primary" size="small" color="primary" />}
                        {/* Show indicator if there are additional emails/phones */}
                        {((contact.emails && contact.emails.length > 0) || (contact.phones && contact.phones.length > 0)) && (
                          <Chip label="Multiple contacts" size="small" variant="outlined" color="info" />
                        )}
                      </Box>
                    }
                    secondary={
                      <>
                        {contact.job_title && <Typography variant="body2" color="text.secondary">{contact.job_title}</Typography>}
                        {contact.email && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                            <EmailIcon sx={{ fontSize: 14 }} color="action" />
                            <Typography variant="body2">{contact.email}</Typography>
                          </Box>
                        )}
                        {contact.phone && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                            <PhoneIcon sx={{ fontSize: 14 }} color="action" />
                            <Typography variant="body2">{contact.phone}</Typography>
                          </Box>
                        )}
                      </>
                    }
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {contact.email && (
                      <IconButton 
                        size="small" 
                        href={`mailto:${contact.email}`} 
                        color="primary"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <EmailIcon />
                      </IconButton>
                    )}
                    {contact.phone && (
                      <IconButton 
                        size="small" 
                        href={`tel:${contact.phone}`} 
                        color="primary"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <PhoneIcon />
                      </IconButton>
                    )}
                    <IconButton 
                      size="small" 
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditContact(contact);
                      }} 
                      color="default"
                      title="Edit Contact"
                    >
                      <EditIcon />
                    </IconButton>
                  </Box>
                </ListItem>
              ))}
            </List>
          )}
        </Paper>

      </Grid>

      {/* Right Column: Sidebar */}
      <Grid item xs={12} md={4}>
        
        {/* AI Insights */}
        {customer?.ai_analysis_raw && (
          <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon /> AI Insights
              </Typography>
              <Divider sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.3)' }} />
              
              {customer.ai_analysis_raw.business_sector && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>Business Sector</Typography>
                  <Chip 
                    label={customer.ai_analysis_raw.business_sector} 
                    size="small"
                    sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white', mt: 0.5 }}
                  />
                </Box>
              )}
              
              {customer.ai_analysis_raw.business_size_category && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>Company Size</Typography>
                  <Typography variant="body2" fontWeight="600">{customer.ai_analysis_raw.business_size_category}</Typography>
                </Box>
              )}
              
              {customer.ai_analysis_raw.it_budget_estimate && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>IT Budget Estimate</Typography>
                  <Typography variant="body2" fontWeight="600">{customer.ai_analysis_raw.it_budget_estimate}</Typography>
                </Box>
              )}
              
              {customer.ai_analysis_raw.growth_potential && (
                <Box>
                  <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>Growth Potential</Typography>
                  <Chip 
                    label={customer.ai_analysis_raw.growth_potential} 
                    size="small"
                    sx={{ 
                      backgroundColor: String(customer.ai_analysis_raw.growth_potential).toLowerCase() === 'high' ? '#4caf50' : 
                                       String(customer.ai_analysis_raw.growth_potential).toLowerCase() === 'medium' ? '#ff9800' : 'rgba(255,255,255,0.2)',
                      color: 'white',
                      mt: 0.5
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Quick Actions</Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Button
              fullWidth
              variant="contained"
              sx={{ mb: 1 }}
              startIcon={<AddIcon />}
              onClick={() => navigate(`/quotes/new?customer=${customer?.id}`)}
            >
              Create Quote
            </Button>
            
            {customer?.main_phone && (
              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1 }}
                startIcon={<PhoneIcon />}
                href={`tel:${customer.main_phone}`}
              >
                Call Customer
              </Button>
            )}
            
            {customer?.main_email && (
              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1 }}
                startIcon={<EmailIcon />}
                href={`mailto:${customer.main_email}`}
              >
                Send Email
              </Button>
            )}
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => navigate(`/customers/${customer?.id}/edit`)}
              startIcon={<EditIcon />}
            >
              Edit Customer
            </Button>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Next Steps</Typography>
            <Divider sx={{ mb: 2 }} />
            
            {!customer?.ai_analysis_raw && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Run AI Analysis to unlock insights
              </Alert>
            )}
            
            {(!contacts || contacts.length === 0) && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Add key contacts to improve relationship management
              </Alert>
            )}
            
            {!customer?.company_registration && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Find company registration number via AI Analysis
              </Alert>
            )}
            
            {customer?.company_registration && !customer?.registration_confirmed && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Confirm company registration number
              </Alert>
            )}
            
            {customer?.ai_analysis_raw && customer?.lead_score && customer?.lead_score > 70 && (
              <Alert severity="success" icon={<StarIcon />}>
                High-value lead! Consider prioritizing outreach.
              </Alert>
            )}
          </CardContent>
        </Card>

      </Grid>
    </Grid>

    {/* Contact Detail Dialog */}
    <ContactDetailDialog
      open={contactDetailOpen}
      onClose={handleContactDetailClose}
      contact={selectedContact}
      onEdit={handleEditFromDetail}
    />
  </>
  );
};

export default CustomerOverviewTab;

