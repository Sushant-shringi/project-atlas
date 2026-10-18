"""
Test raw Gemini output for Q1 to observe exactly what Gemini generates.
"""
import os
import pymysql
import requests

conn = pymysql.connect(
    host="127.0.0.1", port=3307, user="atlas_app", password="atlas_app_secure_password", database="project_atlas", cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cur:
    cur.execute("SELECT api_key FROM clients WHERE id = 'C-01'")
    key = cur.fetchone()["api_key"]
conn.close()

resp = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"client_id": "C-01", "question": "What was the global smart water meter market size in 2024?"},
    headers={"X-Client-Key": key},
    timeout=30
)
print("Status:", resp.status_code)
data = resp.json()
print("llm_mode:", data.get("llm_mode"))
print("fallback_reason:", data.get("fallback_reason"))
print("confidence:", data.get("confidence"))
print("answer:", data.get("answer"))
