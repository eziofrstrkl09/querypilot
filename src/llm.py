import os
from dotenv import load_dotenv
from google import genai
from textwrap import dedent
from google.genai import types

load_dotenv()

client=genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL="gemini-3.5-flash-lite"

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