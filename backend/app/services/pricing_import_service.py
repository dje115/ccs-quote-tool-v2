#!/usr/bin/env python3
"""
Pricing Import Service
AI-powered pricing import from Excel/CSV files
Handles any format with AI extraction
"""

import json
import uuid
import pandas as pd
from typing import List, Dict, Any, Optional, BinaryIO
from sqlalchemy.orm import Session
import httpx
from io import BytesIO

from app.models.product import Product
from app.core.api_keys import get_api_keys
from app.models.tenant import Tenant


class PricingImportService:
    """Service for importing pricing from Excel/CSV files with AI extraction"""
    
    def __init__(self, db: Session, tenant_id: str, openai_api_key: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.openai_api_key = openai_api_key
        
        # Resolve API keys if not provided
        if not self.openai_api_key:
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                api_keys = get_api_keys(self.db, tenant)
                self.openai_api_key = api_keys.openai
    
    async def import_pricing_from_file(
        self,
        file_content: bytes,
        filename: str,
        use_ai_extraction: bool = True
    ) -> Dict[str, Any]:
        """
        Import pricing from Excel or CSV file
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            use_ai_extraction: Whether to use AI for extraction (handles any format)
        
        Returns:
            Dict with import results: {
                'success': bool,
                'imported_count': int,
                'skipped_count': int,
                'errors': List[str],
                'products': List[Dict]
            }
        """
        try:
            # Determine file type
            file_ext = filename.lower().split('.')[-1]
            
            # Read file into DataFrame
            if file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            elif file_ext == 'csv':
                df = pd.read_csv(BytesIO(file_content))
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}'
                }
            
            # Use AI extraction if requested
            if use_ai_extraction and self.openai_api_key:
                products = await self._extract_with_ai(df, filename)
            else:
                products = self._extract_standard_format(df)
            
            # Import products
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for product_data in products:
                try:
                    # Check for duplicates
                    existing = self.db.query(Product).filter(
                        Product.tenant_id == self.tenant_id,
                        Product.code == product_data.get('code')
                    ).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create product
                    product = Product(
                        id=str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        code=product_data.get('code'),
                        name=product_data.get('name', ''),
                        description=product_data.get('description'),
                        category=product_data.get('category'),
                        subcategory=product_data.get('subcategory'),
                        unit=product_data.get('unit', 'each'),
                        base_price=float(product_data.get('price', 0)),
                        cost_price=float(product_data.get('cost_price', 0)) if product_data.get('cost_price') else None,
                        supplier=product_data.get('supplier'),
                        part_number=product_data.get('part_number'),
                        is_active=True,
                        is_service=product_data.get('is_service', False)
                    )
                    
                    self.db.add(product)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importing {product_data.get('name', 'unknown')}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors,
                'products': products[:10]  # Return first 10 as sample
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"[PRICING IMPORT] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_standard_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract products from standard format (column names match expected)"""
        products = []
        
        # Common column name mappings
        column_mappings = {
            'name': ['name', 'product', 'product_name', 'item', 'description'],
            'code': ['code', 'sku', 'part_number', 'product_code', 'item_code'],
            'price': ['price', 'unit_price', 'cost', 'base_price', 'selling_price'],
            'category': ['category', 'type', 'product_type'],
            'supplier': ['supplier', 'vendor', 'manufacturer'],
            'unit': ['unit', 'uom', 'unit_of_measure']
        }
        
        # Find matching columns
        found_columns = {}
        for key, possible_names in column_mappings.items():
            for col in df.columns:
                if col.lower() in [n.lower() for n in possible_names]:
                    found_columns[key] = col
                    break
        
        # Extract products
        for _, row in df.iterrows():
            product = {
                'name': str(row.get(found_columns.get('name', df.columns[0]), '')),
                'code': str(row.get(found_columns.get('code', ''), '')),
                'price': float(row.get(found_columns.get('price', df.columns[-1]), 0)),
                'category': str(row.get(found_columns.get('category', ''), '')),
                'supplier': str(row.get(found_columns.get('supplier', ''), '')),
                'unit': str(row.get(found_columns.get('unit', 'each'), 'each'))
            }
            
            if product['name'] and product['price'] > 0:
                products.append(product)
        
        return products
    
    async def _extract_with_ai(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        """Extract products using AI (handles any format)"""
        try:
            # Convert DataFrame to JSON for AI analysis
            # Limit to first 100 rows for AI processing
            sample_df = df.head(100)
            df_json = sample_df.to_json(orient='records')
            
            # Build AI prompt
            prompt = f"""Analyze this pricing data from a file named "{filename}" and extract product information.

The data is in JSON format with these columns: {list(df.columns)}

Extract the following information for each product:
- name: Product name
- code: Product code/SKU/part number (if available)
- price: Unit price (in GBP)
- cost_price: Cost price (if available)
- category: Product category
- subcategory: Subcategory (if available)
- supplier: Supplier/vendor name (if available)
- part_number: Manufacturer part number (if available)
- unit: Unit of measure (each, meter, box, etc.)
- is_service: Boolean indicating if this is a service (default: false)

Data:
{df_json}

Return a JSON array of products. For each product, only include fields that have actual values.
Standardize product names and categorize appropriately.
If price information is missing or unclear, set price to 0.
If category is unclear, use "General" as default.

Example output format:
[
  {{
    "name": "Cat6 Ethernet Cable",
    "code": "CAT6-305M",
    "price": 125.50,
    "category": "Cabling",
    "subcategory": "Cable",
    "supplier": "Supplier Name",
    "part_number": "PART123",
    "unit": "box",
    "is_service": false
  }}
]"""
            
            # Call OpenAI API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-5-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at extracting and standardizing product pricing data from various file formats. Always return valid JSON arrays."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_completion_tokens": 8000,
                        "temperature": 0.3
                    }
                )
            
            if response.status_code != 200:
                # Fallback to standard extraction
                return self._extract_standard_format(df)
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            # Parse JSON response
            try:
                # Extract JSON from response
                if '[' in response_text:
                    json_start = response_text.find('[')
                    json_end = response_text.rfind(']') + 1
                    json_text = response_text[json_start:json_end]
                    products = json.loads(json_text)
                    
                    # Process remaining rows if any (beyond 100)
                    if len(df) > 100:
                        remaining_df = df.iloc[100:]
                        remaining_products = self._extract_standard_format(remaining_df)
                        products.extend(remaining_products)
                    
                    return products
            except json.JSONDecodeError:
                pass
            
            # Fallback to standard extraction
            return self._extract_standard_format(df)
            
        except Exception as e:
            print(f"[PRICING IMPORT] AI extraction error: {e}")
            # Fallback to standard extraction
            return self._extract_standard_format(df)
    
    def get_import_template(self) -> Dict[str, Any]:
        """Get import template structure"""
        return {
            'columns': [
                'name',
                'code',
                'price',
                'category',
                'subcategory',
                'supplier',
                'part_number',
                'unit',
                'cost_price',
                'description'
            ],
            'required': ['name', 'price'],
            'optional': ['code', 'category', 'subcategory', 'supplier', 'part_number', 'unit', 'cost_price', 'description'],
            'example': [
                {
                    'name': 'Cat6 Ethernet Cable',
                    'code': 'CAT6-305M',
                    'price': 125.50,
                    'category': 'Cabling',
                    'subcategory': 'Cable',
                    'supplier': 'Supplier Name',
                    'part_number': 'PART123',
                    'unit': 'box',
                    'cost_price': 100.00,
                    'description': '305m box of Cat6 cable'
                }
            ],
            'notes': [
                'File can be Excel (.xlsx, .xls) or CSV format',
                'Column names can be in any order',
                'AI extraction will handle non-standard formats',
                'Required columns: name, price',
                'All other columns are optional'
            ]
        }

