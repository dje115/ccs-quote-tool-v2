import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';
import CustomerFormSimple from '../components/CustomerFormSimple';

const CustomerNew: React.FC = () => {
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(true);

  const handleSaveCustomer = async (customerData: any) => {
    try {
      const response = await customerAPI.create(customerData);
      // Navigate to customer detail page so they can run AI analysis
      if (response.data && response.data.id) {
        navigate(`/customers/${response.data.id}`);
      } else {
        navigate('/customers');
      }
    } catch (error) {
      console.error('Error saving customer:', error);
      throw error;
    }
  };

  const handleClose = () => {
    navigate('/customers');
  };

  return (
    <CustomerFormSimple
      open={showForm}
      onClose={handleClose}
      onSave={handleSaveCustomer}
    />
  );
};

export default CustomerNew;
