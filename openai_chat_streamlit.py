import pandas as pd
import json
from dotenv import load_dotenv
import os
import openai
from openai import AzureOpenAI
import mysql.connector
from sqlalchemy import create_engine
import mysql
import pymysql
import re
import streamlit as st

# openai prompt
OPENAI_PROMPT = """You are an AI assistant that is able to convert natural language into a properly formatted SQL query.

The database you will be querying is called "sakila". Here is the schema of the database:
{schema}

You must always output your answer in JSON format with the following key-value pairs (without the "json" text at the beginning of the output):
{{- "chain of thought": the reasoning or story behind the generated query, step by step. The reasoning should be 2-3 paragraph. This reasoning is for the non-technical user
- "query": the SQL query that you generated
- "error": an error message if the query is invalid, or null if the query is valid}}

here is the correct output, dont use anything other than this following output example:

{{"chain_of_thought": "The user is asking for the description of all tables in the sakila database. To achieve this, we would typically use the 'DESCRIBE' or 'SHOW COLUMNS FROM' command in SQL for each table. However, since the user is asking for the description of all tables, we would use the 'SHOW TABLES' command to get the list of tables and then describe each one. But as an AI, I can only generate a single SQL query at a time, so I will provide the SQL command to list all the tables, which is the first step in the process.""query": "SELECT title, length FROM film ORDER BY length DESC LIMIT 1;","error": null}}

"""


OPENAI_API_TYPE = "xxxx" 
OPENAI_API_VERSION = "xxxx" 
OPENAI_API_BASE = "xxxx" 
OPENAI_API_KEY = "xxxx" 
#GPT3.5 --> Deployment Name: gpt-35-turbo 
#Embeding Engine —> Deployment Name: text-embedding-ada-002

def get_completion_from_messages(system_message, user_message, model="gpt-35-turbo", temperature=0, max_tokens=500) -> str:
  client = AzureOpenAI(
    azure_endpoint = OPENAI_API_BASE, 
    api_key=OPENAI_API_KEY,  
    api_version=OPENAI_API_VERSION
  )

  response = client.chat.completions.create(
      model="gpt-35-turbo",
          messages = [
          {'role': 'system', 'content': system_message},
          {'role': 'user', 'content': f"{user_message}"}
      ]
  )

  return response.choices[0].message.content

# connecting database
cnx = mysql.connector.connect(
  host="xxxx",
  user="xxxx",
  password="xxxx",
  database="xxxx"
)

# take database schema
cursor=cnx.cursor()
query=("SELECT  TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_KEY FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='sakila';")
cursor.execute(query)
data = []
for row in cursor:
  data.append(row)
df = pd.DataFrame(data, columns=cursor.column_names)

# pass the database schema into prompt
formatted_system_message = OPENAI_PROMPT.format(schema=df)


# UI
st.title("Azure OpenAI SQL Generator")

# input field for the user to type message
user_message = st.text_input("Enter your message:")
tab_titles = ["Result","Query","Reason"]
tabs = st.tabs(tab_titles)

if user_message:
    try:
        # run the sql query and display the result
        response = get_completion_from_messages(formatted_system_message, user_message)
        json_response = json.loads(response)
        # print chain of thought
        with tabs [2]:
          st.write("Chain of Thought:")
          json_response["chain_of_thought"]
        # print sql query
        query = json_response['query']
        with tabs [1]:
          st.write("Generated SQL Query:")
          st.code(query, language="sql")
        with tabs [0]:
          st.write("Answer:")
        # pass the generated query into database connector
          cursor=cnx.cursor()
          querys=(json_response['query'])
          cursor.execute(querys)
          data = []
          for row in cursor:
            data.append(row)
          df = pd.DataFrame(data, columns=cursor.column_names)
          df
    except Exception as e:
       st.write(f"An error occured: {e}")
