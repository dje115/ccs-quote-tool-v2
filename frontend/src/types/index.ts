/**
 * Shared TypeScript type definitions for the application
 */

// Quote Types
export interface Quote {
  id: string;
  customer_id: string;
  quote_number: string;
  title: string;
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired';
  total_amount?: number;
  valid_until?: string;
  created_at: string;
  updated_at?: string;
  project_title?: string;
}

export interface PaginatedQuoteResponse {
  items: Quote[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Customer Types
export interface Customer {
  id: string;
  company_name: string;
  status?: string;
  lead_score?: number;
  companies_house_data?: CompaniesHouseData;
  google_maps_data?: GoogleMapsData;
  website_data?: WebsiteData;
  created_at: string;
  updated_at?: string;
}

export interface CompaniesHouseData {
  accounts_detail?: {
    detailed_financials?: FinancialYearData[];
    active_directors?: Director[];
  };
  accounts_documents?: AccountsDocument[];
}

export interface FinancialYearData {
  year: number;
  turnover?: number;
  profit?: number;
  [key: string]: unknown;
}

export interface Director {
  name: string;
  role?: string;
  [key: string]: unknown;
}

export interface AccountsDocument {
  id: string;
  year: number;
  document_url?: string;
  [key: string]: unknown;
}

export interface GoogleMapsData {
  locations?: Location[];
}

export interface Location {
  id: string;
  address: string;
  [key: string]: unknown;
}

export interface WebsiteData {
  key_phrases?: string[];
  [key: string]: unknown;
}

// Contact Types
export interface Contact {
  id: string;
  customer_id: string;
  name: string;
  email?: string;
  phone?: string;
  is_primary?: boolean;
  [key: string]: unknown;
}

// Ticket Types
export interface Ticket {
  id: string;
  customer_id?: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at?: string;
  [key: string]: unknown;
}

// Lead Types
export interface Lead {
  id: string;
  company_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  address?: string;
  postcode: string;
  business_sector?: string;
  company_size?: string;
  lead_score: number;
  status: string;
  source: string;
  campaign_id: string;
  campaign_name?: string;
  description?: string;
  qualification_reason?: string;
  project_value?: string;
  timeline?: string;
  created_at: string;
  external_data?: Record<string, unknown>;
  ai_analysis?: Record<string, unknown>;
}

// Campaign Types
export interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'running' | 'completed' | 'stopped';
  created_at: string;
  completed_at?: string;
  [key: string]: unknown;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  status?: number;
  statusText?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}





