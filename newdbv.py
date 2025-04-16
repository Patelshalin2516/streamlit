import mysql.connector
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Gemini API Key
GEMINI_API_KEY = "AIzaSyCx5zkde1v8rZ8nBZ4LAO2aIGA1UsVrmBA"  # Replace this with your actual API key

# --- Function to connect to MySQL database ---
def connect_to_db(host, user, password, database):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

# --- Get schema from DB ---
def get_schema(db):
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    schema = ""
    for (table,) in tables:
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        schema += f"\nTable: {table}\n"
        for col in columns:
            schema += f" - {col[0]} ({col[1]})\n"
    return schema.strip()

# --- Gemini API: Generate SQL Query ---
def generate_sql_query(user_question, schema):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""You are an AI that writes SQL queries for a MySQL database.
Here is the schema:
{schema}

Write a correct SQL query to answer: "{user_question}"
Only return SQL query, no explanations, no markdown, no extra formatting.
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, headers=headers, json=payload)

    if res.status_code == 200:
        reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        return reply.strip("```sql").strip("```").strip()
    else:
        return None

# --- Execute SQL query ---
def run_sql_query(db, sql):
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return f"SQL Error: {e}"

# --- Visualize DataFrame ---
def visualize_data(df):
    st.write("Query Result:")
    st.dataframe(df)

    if df.shape[1] == 2:
        x, y = df.columns
        try:
            fig = px.bar(df, x=x, y=y, title=f"{y} vs {x}")
            st.plotly_chart(fig)
        except:
            st.warning("Couldn't generate chart.")
    elif df.shape[1] >= 3:
        st.info("More than 2 columns found. Displaying table only.")
    else:
        st.warning("Not enough columns for a chart.")

# --- Streamlit UI ---
st.title("🧠 Gemini-Powered SQL Assistant")

with st.sidebar:
    st.header("📦 Connect to Your MySQL DB")
    host = st.text_input("Host", value="localhost")
    user = st.text_input("User", value="root")
    password = st.text_input("Password", type="password")
    database = st.text_input("Database")

    connect_btn = st.button("Connect")

if connect_btn:
    try:
        db = connect_to_db(host, user, password, database)
        st.success(f"Connected to `{database}`!")
        schema = get_schema(db)
        st.code(schema, language='text')

        user_question = st.text_input("Ask a question about your data:")

        if user_question:
            with st.spinner("Thinking with Gemini..."):
                sql = generate_sql_query(user_question, schema)
                if sql:
                    st.code(sql, language='sql')
                    result = run_sql_query(db, sql)
                    if isinstance(result, pd.DataFrame):
                        visualize_data(result)
                    else:
                        st.error(result)
                else:
                    st.error("Gemini couldn't generate a valid SQL query.")
    except Exception as e:
        st.error(f"Connection failed: {e}")
