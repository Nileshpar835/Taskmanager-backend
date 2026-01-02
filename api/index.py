import json
import os
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def calculate_level_and_xp(completed_tasks_count):
    """Calculate XP and Level based on completed tasks"""
    xp = completed_tasks_count * 10
    level = (xp // 50) + 1
    return xp, level

def get_tasks():
    """GET /api/tasks - Fetch all tasks with XP and Level"""
    try:
        response = supabase.table("tasks").select("*").execute()
        tasks = response.data
        
        # Count completed tasks
        completed_count = sum(1 for task in tasks if task["completed"])
        xp, level = calculate_level_and_xp(completed_count)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "tasks": tasks,
                "xp": xp,
                "level": level
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def create_task(title):
    """POST /api/tasks - Create a new task"""
    try:
        new_task = {
            "title": title,
            "completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("tasks").insert(new_task).execute()
        
        # Recalculate stats
        all_tasks = supabase.table("tasks").select("*").execute().data
        completed_count = sum(1 for task in all_tasks if task["completed"])
        xp, level = calculate_level_and_xp(completed_count)
        
        return {
            "statusCode": 201,
            "body": json.dumps({
                "task": response.data[0] if response.data else new_task,
                "xp": xp,
                "level": level
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def update_task(task_id, title, completed):
    """PUT /api/tasks - Update a task"""
    try:
        update_data = {
            "title": title,
            "completed": completed
        }
        
        response = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
        
        # Recalculate stats
        all_tasks = supabase.table("tasks").select("*").execute().data
        completed_count = sum(1 for task in all_tasks if task["completed"])
        xp, level = calculate_level_and_xp(completed_count)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "task": response.data[0] if response.data else None,
                "xp": xp,
                "level": level
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def delete_task(task_id):
    """DELETE /api/tasks - Delete a task"""
    try:
        supabase.table("tasks").delete().eq("id", task_id).execute()
        
        # Recalculate stats
        all_tasks = supabase.table("tasks").select("*").execute().data
        completed_count = sum(1 for task in all_tasks if task["completed"])
        xp, level = calculate_level_and_xp(completed_count)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "xp": xp,
                "level": level
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def handler(request):
    """Main Vercel serverless handler"""
    method = request.method
    path = request.path
    
    # Enable CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }
    
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }
    
    try:
        if path == "/api/tasks" or path == "/api/tasks/":
            if method == "GET":
                response = get_tasks()
            elif method == "POST":
                body = json.loads(request.body or "{}")
                title = body.get("title", "Untitled")
                response = create_task(title)
            elif method == "PUT":
                body = json.loads(request.body or "{}")
                response = update_task(
                    body.get("id"),
                    body.get("title"),
                    body.get("completed")
                )
            elif method == "DELETE":
                task_id = request.args.get("id")
                response = delete_task(task_id)
            else:
                response = {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
        else:
            response = {"statusCode": 404, "body": json.dumps({"error": "Not found"})}
        
        response["headers"] = headers
        return response
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }
