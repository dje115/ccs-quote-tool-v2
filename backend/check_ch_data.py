#!/usr/bin/env python3
import asyncio
import json
from app.database import get_db
from app.models.crm import Customer
from sqlalchemy import select

async def check():
    async for db in get_db():
        result = await db.execute(select(Customer).where(Customer.company_name == 'Arkel Computer Services Ltd'))
        customer = result.scalar_one_or_none()
        if customer:
            print("=== COMPANIES HOUSE DATA ===")
            if customer.companies_house_data:
                print(json.dumps(customer.companies_house_data, indent=2))
            else:
                print("No Companies House data")
            
            print("\n=== COMPANY REGISTRATION ===")
            print(f"Registration: {customer.company_registration}")
            print(f"Confirmed: {customer.registration_confirmed}")
        else:
            print("Customer not found")
        break

asyncio.run(check())

