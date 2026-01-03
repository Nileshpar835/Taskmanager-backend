import json
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=False)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = None

# Initialize Supabase client only if credentials are available
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    print("Warning: SUPABASE_URL and/or SUPABASE_SERVICE_ROLE_KEY not set in environment variables")

def calculate_level_and_xp(completed_tasks_count):
    """Calculate XP and Level based on completed tasks"""
    xp = completed_tasks_count * 10
    level = (xp // 50) + 1
    return xp, level

@app.route('/api/tasks', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def tasks():
    """Handle all task operations"""
    
    if not supabase:
        return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."}), 500
    
    try:
        if request.method == 'GET':
            response = supabase.table("tasks").select("*").execute()
            tasks_list = response.data
            
            # Count completed tasks
            completed_count = sum(1 for task in tasks_list if task.get("completed", False))
            xp, level = calculate_level_and_xp(completed_count)
            
            return jsonify({
                "tasks": tasks_list,
                "xp": xp,
                "level": level
            })
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            title = data.get("title", "Untitled")
            
            new_task = {
                "title": title,
                "completed": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("tasks").insert(new_task).execute()
            
            # Recalculate stats
            all_tasks = supabase.table("tasks").select("*").execute().data
            completed_count = sum(1 for task in all_tasks if task.get("completed", False))
            xp, level = calculate_level_and_xp(completed_count)
            
            return jsonify({
                "task": response.data[0] if response.data else new_task,
                "xp": xp,
                "level": level
            }), 201
        
        elif request.method == 'PUT':
            data = request.get_json() or {}
            task_id = data.get("id")
            title = data.get("title")
            completed = data.get("completed")
            
            update_data = {
                "title": title,
                "completed": completed
            }
            
            response = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
            
            # Recalculate stats
            all_tasks = supabase.table("tasks").select("*").execute().data
            completed_count = sum(1 for task in all_tasks if task.get("completed", False))
            xp, level = calculate_level_and_xp(completed_count)
            
            return jsonify({
                "task": response.data[0] if response.data else None,
                "xp": xp,
                "level": level
            })
        
        elif request.method == 'DELETE':
            task_id = request.args.get("id") or (request.get_json() or {}).get("id")
            
            if task_id:
                supabase.table("tasks").delete().eq("id", task_id).execute()
            
            # Recalculate stats
            all_tasks = supabase.table("tasks").select("*").execute().data
            completed_count = sum(1 for task in all_tasks if task.get("completed", False))
            xp, level = calculate_level_and_xp(completed_count)
            
            return jsonify({
                "success": True,
                "xp": xp,
                "level": level
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    return jsonify({"message": "Task Manager API", "status": "running"}), 200

@app.route('/api', methods=['GET', 'OPTIONS'])
def api_index():
    return jsonify({"message": "Task Manager API", "status": "running"}), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

# Export app for Vercel
handler = app
