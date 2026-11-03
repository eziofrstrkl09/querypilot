from src.llm import client, MODEL
import os
from dotenv import load_dotenv
from google import genai
from textwrap import dedent
from google.genai import types

response = client.models.generate_content(
    model=MODEL,
    contents="Reply with exactly: QueryPilot connected."
)

print(response.text)

def generate_sql(question, schema):
    prompt=dedent(f"""You're a PostgreSQL SQL query generator.
    
    Database schema: {schema}

    User Question: {question}
    
    Generate only the SQL query.
    Do not include any markdown or explanations.
""")

    response=client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0)
    )

    if not response.text:
        raise ValueError("Model returned an empty response.")

    sql = response.text.strip()

    if sql.startswith("```"):
        sql=sql.strip("`").removeprefix("sql").strip()

    return sql

question = "Show the number of customers"

schema = """
customers(customer_id, first_name, last_name)
orders(order_id, customer_id, status)
"""

sql = generate_sql(question, schema)

print(f"Question: {question}")
print(f"SQL: {sql}")