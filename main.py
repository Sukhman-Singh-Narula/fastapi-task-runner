from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import os
import subprocess
import sqlite3
import json
import shutil
import requests
from PIL import Image
import pytesseract
import openai

app = FastAPI()
data_directory = "/data"
openai.api_key = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDI4NjVAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.w-7kDOHYhLb56Id40ZX6hxZ9KWzy9rb0IusG9msxL1s"
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/"

def validate_path(path: str):
    if not path.startswith(data_directory):
        raise HTTPException(status_code=400, detail="Access outside /data is restricted")

class TaskRequest(BaseModel):
    task: str

def parse_task(task_description: str):
    prompt = f"Extract the key operation from this task: '{task_description}'. Return only the operation name."
    response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response["choices"][0]["message"]["content"].strip().lower()

def execute_task(task_description: str):
    try:
        operation = parse_task(task_description)

        if "install uv" in operation:
            subprocess.run(["pip", "install", "uv"], check=True)
            return "Installed uv successfully"
        elif "format markdown" in operation:
            subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)
            return "Formatted /data/format.md using Prettier"
        elif "count wednesdays" in operation:
            with open("/data/dates.txt", "r") as file:
                dates = file.readlines()
            count = sum(1 for date in dates if "Wed" in date)
            with open("/data/dates-wednesdays.txt", "w") as file:
                file.write(str(count))
            return "Counted Wednesdays and saved to file"
        elif "sort contacts" in operation:
            with open("/data/contacts.json", "r") as file:
                contacts = json.load(file)
            sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))
            with open("/data/contacts-sorted.json", "w") as file:
                json.dump(sorted_contacts, file)
            return "Sorted contacts and saved to file"
        elif "extract first lines of logs" in operation:
            logs = sorted(os.listdir("/data/logs"), key=lambda x: os.path.getmtime(os.path.join("/data/logs", x)), reverse=True)
            recent_logs = logs[:10]
            with open("/data/logs-recent.txt", "w") as out_file:
                for log in recent_logs:
                    with open(os.path.join("/data/logs", log), "r") as file:
                        out_file.write(file.readline())
            return "Extracted first lines of recent logs"
        elif "extract markdown titles" in operation:
            index = {}
            for filename in os.listdir("/data/docs"):
                if filename.endswith(".md"):
                    with open(os.path.join("/data/docs", filename), "r") as file:
                        for line in file:
                            if line.startswith("# "):
                                index[filename] = line.strip("# ").strip()
                                break
            with open("/data/docs/index.json", "w") as file:
                json.dump(index, file)
            return "Extracted markdown titles and created index"
        elif "extract email sender" in operation:
            with open("/data/email.txt", "r") as file:
                email_content = file.read()
            response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"Extract sender email from: {email_content}"}])
            sender_email = response["choices"][0]["message"]["content"].strip()
            with open("/data/email-sender.txt", "w") as file:
                file.write(sender_email)
            return "Extracted sender email"
        elif "extract credit card number" in operation:
            image = Image.open("/data/credit-card.png")
            card_number = pytesseract.image_to_string(image).replace(" ", "").strip()
            with open("/data/credit-card.txt", "w") as file:
                file.write(card_number)
            return "Extracted credit card number"
        elif "calculate ticket sales" in operation:
            conn = sqlite3.connect("/data/ticket-sales.db")
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type='Gold'")
            total_sales = cursor.fetchone()[0]
            conn.close()
            with open("/data/ticket-sales-gold.txt", "w") as file:
                file.write(str(total_sales))
            return "Calculated total ticket sales"
        else:
            return f"Task '{task_description}' is not recognized."
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_task(request: TaskRequest):
    task_description = request.task.strip()
    if not task_description:
        raise HTTPException(status_code=400, detail="Task description is empty")
    
    result = execute_task(task_description)
    return {"message": "Task executed", "result": result}

@app.get("/read")
def read_file(path: str = Query(..., title="File Path")):
    validate_path(path)
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    
    return {"content": content}
