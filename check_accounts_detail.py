import asyncio
import json
from app.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT companies_house_data FROM customers WHERE name ILIKE '%central technology%' LIMIT 1")
        )
        row = result.fetchone()
        if row and row[0]:
            data = row[0]
            print("Keys in companies_house_data:", list(data.keys()))
            if 'accounts_detail' in data:
                print("\naccounts_detail found!")
                print("Keys:", list(data['accounts_detail'].keys()))
                print("\nactive_directors:", data['accounts_detail'].get('active_directors'))
                print("\ndetailed_financials:", data['accounts_detail'].get('detailed_financials'))
            else:
                print("\nNo accounts_detail found")
        else:
            print("No data")

asyncio.run(check())






