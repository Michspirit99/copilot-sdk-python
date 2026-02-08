#!/usr/bin/env python3
"""
Test data generator - generate realistic test data for databases, APIs, forms, etc.
"""
import asyncio
import sys
from copilot import CopilotClient


async def main():
    """Generate realistic test data using Copilot."""
    if len(sys.argv) < 3:
        print("Usage: python test_data_generator.py <schema> <count> [format]")
        print("\nFormats:")
        print("  json     - JSON array (default)")
        print("  sql      - SQL INSERT statements")
        print("  csv      - CSV format")
        print("  python   - Python list/dict")
        print("\nSchema examples:")
        print("  user, product, order, customer")
        print('  custom: "name:str,age:int,email:str"')
        print("\nExamples:")
        print("  python test_data_generator.py user 10")
        print("  python test_data_generator.py product 50 sql")
        print('  python test_data_generator.py "name:str,email:str" 20 json')
        sys.exit(1)
    
    schema = sys.argv[1]
    try:
        count = int(sys.argv[2])
    except ValueError:
        print("❌ Error: Count must be a number")
        sys.exit(1)
    
    format_type = sys.argv[3].lower() if len(sys.argv) > 3 else "json"
    
    print("🎲 Test Data Generator")
    print(f"📋 Schema: {schema}")
    print(f"🔢 Count: {count}")
    print(f"📄 Format: {format_type}\n")
    
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-5-mini"})

        format_specs = {
            'json': "JSON array of objects",
            'sql': "SQL INSERT statements for a table",
            'csv': "CSV format with header row",
            'python': "Python list of dictionaries"
        }

        prompt = f"""Generate {count} realistic test data records.

Schema: {schema}
Format: {format_type} ({format_specs.get(format_type, format_specs['json'])})

Requirements:
1. Realistic data (proper names, valid emails, reasonable values)
2. Diverse data (different ages, locations, etc.)
3. Proper formatting for {format_type}
4. No duplicates

Common schemas:
- user: id, name, email, age, country
- product: id, name, price, category, stock
- order: id, user_id, product_id, quantity, total, date
- customer: id, first_name, last_name, email, phone, address

Generate the data now:"""

        print("🤖 Generated Data:\n")
        print("-" * 80)
        response = await session.send_and_wait({"prompt": prompt})
        print(response.data.content)
        print("-" * 80)
        print("\n✅ Generation complete!")

        await session.destroy()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
