import streamlit as st
import mysql.connector
import requests
import pandas as pd
import matplotlib.pyplot as plt
import re

# --- MySQL connection ---
def connect_to_mysql():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='SalesDB'
    )

def query_mysql(query):
    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# --- Gemini API query ---
API_KEY = 'AIzaSyCx5zkde1v8rZ8nBZ4LAO2aIGA1UsVrmBA'

def query_gemini(user_question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={API_KEY}"

    headers = {"Content-Type": "application/json"}
    
    # Prompt Gemini with schema info
    prompt = f"""
Given the following MySQL database schema:
- ProductCatalog(ProductID, ProductName, AvailableQuantity, Price)
- UserInfo(UserID, Name, Email, Location)
- OrderDetails(OrderID, OrderDate, UserID, ProductID, Quantity, OrderValue)

Convert this natural language question into a valid MySQL query using only the tables and columns above:
"{user_question}"

Return only the SQL query without explanation.
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            sql = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Remove code formatting if present
            clean_sql = re.sub(r"```sql|```", "", sql).strip()
            return clean_sql
        except:
            return None
    else:
        st.error(f"Gemini API Error {response.status_code}: {response.text}")
        return None

# --- Graph Plotting ---
def plot_graph(df, x_column, y_column):
    fig, ax = plt.subplots()
    ax.plot(df[x_column], df[y_column], marker='o')
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.set_title(f"{x_column} vs {y_column}")
    st.pyplot(fig)

# --- Streamlit UI ---
st.title("🔍 Ask Gemini About Your MySQL SalesDB")

user_question = st.text_input("💬 Ask a question about your database:")

if user_question:
    # Step 1: Ask Gemini
    mysql_query = query_gemini(user_question)

    if mysql_query:
        st.subheader("💡 Gemini's Generated SQL Query:")
        st.code(mysql_query, language='sql')

        # Step 2: Run MySQL Query
        try:
            result = query_mysql(mysql_query)
            df = pd.DataFrame(result)
            st.subheader("📊 Query Result:")
            st.dataframe(df)

            # Step 3: Check if numeric columns exist for graphing
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

            if len(numeric_columns) >= 2:
                # Select first two numeric columns for graphing
                x_col, y_col = numeric_columns[0], numeric_columns[1]
                plot_graph(df, x_col, y_col)
            elif len(numeric_columns) == 1:
                # If only one numeric column, plot it against the index (row number)
                x_col = df.index
                y_col = numeric_columns[0]
                fig, ax = plt.subplots()
                ax.plot(x_col, df[y_col], marker='o')
                ax.set_xlabel('Index')
                ax.set_ylabel(y_col)
                ax.set_title(f"Index vs {y_col}")
                st.pyplot(fig)
            else:
                st.info("No numeric columns available to plot.")
        except Exception as e:
            st.error(f"MySQL Error: {e}")
    else:
        st.error("Failed to generate a valid SQL query from Gemini.")
