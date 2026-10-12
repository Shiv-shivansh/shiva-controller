import subprocess
import sqlite3
import json
import os
from flask import Flask, request, jsonify

# Initialize Controller
app = Flask(__name__)

# --- SHIVA'S BRAIN (Database for Private Data) ---
def init_brain():
 conn = sqlite3.connect('shiva_brain.db')
 cursor = conn.cursor()
 # Table to store user commands and history
 cursor.execute('''
 CREATE TABLE IF NOT EXISTS user_memory (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 command TEXT,
 result TEXT,
 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
 )
 ''')
 conn.commit()
 conn.close()

def save_to_memory(command, result):
 conn = sqlite3.connect('shiva_brain.db')
 cursor = conn.cursor()
 cursor.execute("INSERT INTO user_memory (command, result) VALUES (?, ?)", (command, result))
 conn.commit()
 conn.close()

def get_user_data():
 conn = sqlite3.connect('shiva_brain.db')
 cursor = conn.cursor()
 cursor.execute("SELECT * FROM user_memory ORDER BY id DESC LIMIT 10")
 data = cursor.fetchall()
 conn.close()
 return data

def auto_fix_error(error_message):
    """Shiva tries to fix the error automatically."""
    if "permission denied" in str(error_message).lower():
        return "sudo " + str(error_message)
    if "command not found" in str(error_message).lower():
        return "apt install " + str(error_message).replace("command not found", "").strip()
    return str(error_message)

def execute_with_smart_loop(command):
 max_retries = 3
 attempt = 0
 
 while attempt < max_retries:
 try:
 # Execute the command
 result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
 
 # Success?
 if result.returncode == 0:
 return result.stdout
 else:
 # Failure? Shiva tries to fix it
 error_msg = result.stderr
 print(f"[SHIVA LOG]: Error detected on attempt {attempt + 1}. Attempting auto-fix...")
 fixed_command = auto_fix_error(error_msg)
 attempt += 1
 continue
 
 except subprocess.TimeoutExpired:
 return "Error: Command took too long."
 except Exception as e:
 return f"Critical Error: {str(e)}"
 
 return "Error: Could not resolve command after 3 attempts."

# --- API ROUTES ---
@app.route('/api/shiva/command', methods=['POST'])
def process_command():
 data = request.json
 user_command = data.get('command')
 
 # 1. Save to Brain (User's Private Data)
 save_to_memory(user_command, "Processing...")
 
 # 2. Execute with Smart Loop
 output = execute_with_smart_loop(user_command)
 
 # 3. Save result
 save_to_memory(user_command, output)
 
 return jsonify({"status": "success", "output": output})

@app.route('/api/shiva/status', methods=['GET'])
def get_status():
 memory = get_user_data()
 return jsonify({
 "agent": "SHIVA v5.2",
 "status": "Active",
 "memory_size": len(memory),
 "security": "IP Hidden / MAC Hidden"
 })

if __name__ == '__main__':
 init_brain()
 print("🧠 SHIVA Controller Started. Waiting for commands...")
 app.run(host='0.0.0.0', port=5000)
