# Web Application Background Tasks

> **Note: This is a conceptual example showing how sitq could be used for web application workflows.**
> 
> **Current Implementation Status:** Some features shown here are still under development.
> 
> **For working examples, see `examples/basic/` directory.**

## Overview

Web applications often need to perform time-consuming operations like:
- Sending emails
- Processing uploaded files
- Generating reports
- Calling external APIs
- Running data analysis

sitq is designed to orchestrate these workflows while providing reliability and scalability.

## Conceptual Web Integration

This example demonstrates how sitq could be used for web application workflows:

```python
# Note: This is a conceptual example
# Current API may differ from what's shown here

import asyncio
from typing import Dict

class WebTaskProcessor:
    """Conceptual web task processor using sitq."""
    
    def __init__(self):
        # Note: Backend initialization would use current API
        # backend = SQLiteBackend("web_tasks.db")
        # queue = TaskQueue(backend=backend)
        # worker = Worker(backend)
        print("WebTaskProcessor initialized (conceptual example)")
    
    def process_upload(self, file_data: Dict) -> Dict:
        """Process uploaded file in background."""
        print(f"Processing upload: {file_data}")
        
        # In real implementation, this would enqueue background task
        # task_id = await queue.enqueue(process_file_data, file_data)
        
        return {"status": "queued", "message": "File queued for processing"}
    
    def process_file_data(self, file_data: Dict) -> str:
        """Process file data."""
        # Simulate file processing
        return f"Processed: {file_data.get('filename', 'unknown')}"

## Current Implementation Notes

**Working Features:**
- Core task queue operations
- Worker with async/sync function support
- SQLite backend for persistence

**Under Development:**
- Full web integration examples
- Advanced worker configurations
- Additional backends (PostgreSQL, Redis, NATS)

**For Working Examples:**
See `examples/basic/` directory for current API demonstrations.

### Email Sending Example

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_task(to_email, subject, body):
    """Send email in background."""
    try:
        # Email configuration (use environment variables in production)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "your-email@gmail.com"
        smtp_password = "your-app-password"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return {
            "success": True,
            "message": f"Email sent to {to_email}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/send-email', methods=['POST'])
def send_email():
    """Queue email sending task."""
    data = request.json
    
    task = sitq.Task(
        function=send_email_task,
        args=[data['to'], data['subject'], data['body']]
    )
    
    task_id = queue.enqueue(task)
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Email queued for sending"
    })
```

## FastAPI Integration

### Async-Friendly Setup

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
import sitq
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="sitq Web App")

# Task queue setup
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend("fastapi_tasks.db"))
worker = sitq.Worker(queue)

# Thread pool for running worker
executor = ThreadPoolExecutor(max_workers=1)

# Start worker
async def start_worker():
    """Start worker in thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, worker.run)

@app.on_event("startup")
async def startup_event():
    """Start worker on app startup."""
    asyncio.create_task(start_worker())

class ProcessRequest(BaseModel):
    data: str
    priority: int = 5

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

@app.post("/process")
async def process_data(request: ProcessRequest):
    """Process data asynchronously."""
    
    def background_process(data):
        """Background processing."""
        import time
        time.sleep(3)  # Simulate work
        return f"Processed: {data}"
    
    task = sitq.Task(
        function=background_process,
        args=[request.data],
        priority=request.priority
    )
    
    task_id = queue.enqueue(task)
    
    return {
        "task_id": task_id,
        "status": "queued"
    }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Get task result."""
    try:
        result = queue.get_result(task_id)
        if result.is_error:
            raise HTTPException(status_code=500, detail=str(result.error))
        return {
            "task_id": task_id,
            "result": result.value,
            "status": "completed"
        }
    except sitq.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")

@app.post("/send-email")
async def send_email(request: EmailRequest):
    """Queue email sending."""
    
    def send_email_task(to, subject, body):
        """Send email task."""
        # Email sending logic here
        return f"Email sent to {to}"
    
    task = sitq.Task(
        function=send_email_task,
        args=[request.to, request.subject, request.body]
    )
    
    task_id = queue.enqueue(task)
    
    return {
        "task_id": task_id,
        "message": "Email queued"
    }
```

## File Processing Example

### Image Processing Pipeline

```python
from PIL import Image
import os
import uuid

def process_image_task(image_path, operations):
    """Process image with various operations."""
    try:
        # Open image
        with Image.open(image_path) as img:
            # Apply operations
            for op in operations:
                if op['type'] == 'resize':
                    img = img.resize((op['width'], op['height']))
                elif op['type'] == 'rotate':
                    img = img.rotate(op['degrees'])
                elif op['type'] == 'crop':
                    img = img.crop(op['box'])
            
            # Save processed image
            filename = f"processed_{uuid.uuid4()}.jpg"
            output_path = os.path.join('processed', filename)
            os.makedirs('processed', exist_ok=True)
            img.save(output_path)
            
            return {
                "success": True,
                "original_path": image_path,
                "processed_path": output_path,
                "operations": operations
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    operations = request.form.get('operations', '[]')
    operations = eval(operations)  # In production, use proper JSON parsing
    
    # Save uploaded file
    filename = f"upload_{uuid.uuid4()}.jpg"
    input_path = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(input_path)
    
    # Queue processing task
    task = sitq.Task(
        function=process_image_task,
        args=[input_path, operations]
    )
    
    task_id = queue.enqueue(task)
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "upload_path": input_path
    })
```

## Report Generation

### PDF Report Generation

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_report_task(data, report_type):
    """Generate PDF report."""
    try:
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph(f"{report_type} Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add content based on data
        for key, value in data.items():
            content = Paragraph(f"{key}: {value}", styles['Normal'])
            story.append(content)
            story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Save PDF
        filename = f"report_{uuid.uuid4()}.pdf"
        output_path = os.path.join('reports', filename)
        os.makedirs('reports', exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return {
            "success": True,
            "report_path": output_path,
            "report_type": report_type
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """Generate report in background."""
    data = request.json
    
    task = sitq.Task(
        function=generate_report_task,
        args=[data['data'], data['report_type']]
    )
    
    task_id = queue.enqueue(task)
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Report generation started"
    })
```

## Task Monitoring Dashboard

### Real-time Status Updates

```python
@app.route('/dashboard')
def dashboard():
    """Task monitoring dashboard."""
    # Get queue statistics
    stats = queue.get_stats()
    
    # Get recent tasks
    recent_tasks = []
    for status in ['queued', 'running', 'completed', 'failed']:
        tasks = queue.list_tasks(status=status, limit=5)
        recent_tasks.extend(tasks)
    
    return jsonify({
        "stats": {
            "total": stats.total_tasks,
            "queued": stats.queued_tasks,
            "running": stats.running_tasks,
            "completed": stats.completed_tasks,
            "failed": stats.failed_tasks
        },
        "recent_tasks": recent_tasks
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Check queue health
        queue_health = queue.health_check()
        
        # Check worker status
        worker_status = worker.get_status()
        
        return jsonify({
            "status": "healthy",
            "queue": queue_health.is_healthy,
            "worker": worker_status.is_running,
            "timestamp": time.time()
        })
    
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

## Best Practices

### Error Handling

```python
def robust_background_task(data):
    """Robust task with error handling."""
    try:
        # Validate input
        if not data:
            raise ValueError("No data provided")
        
        # Process data
        result = process_data(data)
        
        return {
            "success": True,
            "result": result
        }
    
    except ValueError as e:
        return {
            "success": False,
            "error": f"Validation error: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Processing error: {e}"
        }

# Task with retry configuration
task = sitq.Task(
    function=robust_background_task,
    args=[data],
    max_retries=3,
    retry_delay=1.0
)
```

### Resource Management

```python
# Configure worker for web applications
worker = sitq.Worker(
    queue=queue,
    max_workers=2,              # Limit concurrent tasks
    timeout=300.0,               # 5 minute timeout
    max_memory_mb=512,          # Memory limit
    graceful_shutdown=30.0       # Graceful shutdown
)
```

### Security Considerations

```python
def secure_task(user_id, data):
    """Secure task that validates user permissions."""
    # Validate user permissions
    if not user_has_permission(user_id, 'process_data'):
        raise PermissionError("User not authorized")
    
    # Sanitize input
    sanitized_data = sanitize_input(data)
    
    # Process data
    return process_data(sanitized_data)

@app.route('/secure-process', methods=['POST'])
def secure_process():
    """Secure processing endpoint."""
    user_id = get_current_user_id()
    data = request.json
    
    task = sitq.Task(
        function=secure_task,
        args=[user_id, data]
    )
    
    task_id = queue.enqueue(task)
    
    return jsonify({"task_id": task_id})
```

## Deployment Considerations

### Production Configuration

```python
# Production worker configuration
worker = sitq.Worker(
    queue=queue,
    max_workers=4,              # Scale based on CPU cores
    poll_interval=0.5,          # Responsive polling
    timeout=600.0,              # 10 minute timeout
    max_retries=5,              # Robust retry
    retry_delay=2.0,            # Exponential backoff
    log_level=logging.INFO      # Production logging
)

# Production backend configuration
backend = sitq.SQLiteBackend(
    database="production_tasks.db",
    connection_pool_size=20,
    enable_wal=True,
    synchronous="NORMAL"
)
```

### Monitoring and Alerting

```python
def monitor_tasks():
    """Monitor task health and send alerts."""
    while True:
        try:
            stats = queue.get_stats()
            
            # Alert on high failure rate
            if stats.failed_tasks > 10:
                send_alert(f"High failure rate: {stats.failed_tasks} failed tasks")
            
            # Alert on queue buildup
            if stats.queued_tasks > 100:
                send_alert(f"Queue buildup: {stats.queued_tasks} queued tasks")
            
            time.sleep(60)  # Check every minute
        
        except Exception as e:
            send_alert(f"Monitoring error: {e}")
            time.sleep(60)

# Start monitoring in production
monitor_thread = threading.Thread(target=monitor_tasks, daemon=True)
monitor_thread.start()
```

## Next Steps

- [Data Processing Example](data-processing.md) - Learn about data processing patterns
- [Microservices Example](microservices.md) - Explore microservices integration
- [Error Handling Guide](../error-handling.md) - Comprehensive error management
- [Performance Guide](../performance.md) - Optimization techniques