import mysql.connector
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Gemini API Key
GEMINI_API_KEY = "API_KEY"

# Connect to DB
def connect_to_db(host, user, password, database):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

# Get schema
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

# Gemini call
def generate_sql_query(user_question, schema):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-001:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""You are an AI that writes SQL queries for a MySQL database.
Here is the schema:
{schema}

Write a correct SQL query to answer: "{user_question}."
Only return the SQL query, no explanations, no markdown, no extra formatting.
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
        print(f"Failed to generate query: {res.status_code} - {res.text}")
        return None

# Run SQL
def run_sql_query(db, sql):
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return f"SQL Error: {e}"

# Visualize
def visualize_data(df):
    st.write("Query Result:")
    st.dataframe(df)

    # If there are exactly two columns, display a bar chart
    if df.shape[1] == 2:
        x, y = df.columns
        try:
            fig = px.bar(df, x=x, y=y, title=f"{y} vs {x}")
            fig.update_layout(width=800, height=400)  # Adjust size
            st.plotly_chart(fig)
        except Exception as e:
            st.warning(f"Couldn't generate bar chart: {e}")

    # If there are more than two columns, handle different types of graphs
    elif df.shape[1] > 2:
        # If columns are numeric, generate a scatter plot matrix (pair plot)
        if df.select_dtypes(include=['number']).shape[1] > 1:
            try:
                fig = px.scatter_matrix(df)
                fig.update_layout(width=1000, height=800)  # Adjust size
                st.plotly_chart(fig)
            except Exception as e:
                st.warning(f"Couldn't generate scatter matrix chart: {e}")
        # If there are string columns, generate a count plot for each category
        else:
            try:
                for col in df.columns:
                    if df[col].dtype == 'object':
                        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                        fig.update_layout(width=800, height=400)  # Adjust size
                        st.plotly_chart(fig)
            except Exception as e:
                st.warning(f"Couldn't generate count plot: {e}")

        # If there's a mix of numeric and categorical, try a line chart for numeric columns
        try:
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.shape[1] > 0:
                fig = px.line(numeric_df)
                fig.update_layout(width=1000, height=600)  # Adjust size
                st.plotly_chart(fig)
            else:
                st.warning("No numeric columns for line chart.")
        except Exception as e:
            st.warning(f"Couldn't generate line chart: {e}")
    else:
        st.warning("Not enough columns for a chart.")

# --- Streamlit UI ---
st.title("🧠 Gemini SQL Data Assistant")

# Sidebar connection
with st.sidebar:
    st.header("🔌 Connect to DB")
    host = st.text_input("Host", value="localhost")
    user = st.text_input("User", value="root")
    password = st.text_input("Password", type="password")
    database = st.text_input("Database")

    if st.button("Connect"):
        try:
            db = connect_to_db(host, user, password, database)
            st.session_state['db'] = db
            st.session_state['schema'] = get_schema(db)
            st.success("✅ Connected!")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# Only show query input if connected
if 'db' in st.session_state:
    st.subheader("💬 Ask your question")
    user_question = st.text_input("Ask about your data")
    if st.button("Ask"):
        with st.spinner("Gemini is thinking..."):
            sql = generate_sql_query(user_question, st.session_state['schema'])
            if sql:
                if not sql.strip().lower().startswith("select"):
                    st.warning("Gemini didn't generate a valid SELECT query.")
                    st.text("Output from Gemini:\n" + sql)
                else:
                    st.code(sql, language="sql")
                    result = run_sql_query(st.session_state['db'], sql)
                    if isinstance(result, pd.DataFrame):
                        visualize_data(result)
                    else:
                        st.error(result)
            else:
                st.error("Gemini failed to generate a SQL query.")
