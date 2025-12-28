# Microservices Integration

> **Note: This is a conceptual example showing how sitq could be used for microservices workflows.**
> 
> **Current Implementation Status:** Some features shown here are still under development.
> 
> **For working examples, see `examples/basic/` directory.**

## Overview

In microservices architectures, sitq could serve as:
- Inter-service communication layer
- Asynchronous task processing
- Event-driven architecture backbone
- Service orchestration tool
- Load balancing mechanism

## Conceptual Service Communication

This example demonstrates how sitq could be used for microservices workflows:

```python
# Note: This is a conceptual example
# Current API may differ from what's shown here

import asyncio
from typing import Dict

class MicroserviceOrchestrator:
    """Conceptual microservice orchestrator using sitq."""
    
    def __init__(self):
        # Note: Backend initialization would use current API
        # backend = SQLiteBackend("microservices.db")
        # queue = TaskQueue(backend=backend)
        # worker = Worker(backend)
        print("MicroserviceOrchestrator initialized (conceptual example)")
    
    def process_order(self, order_data: Dict) -> Dict:
        """Process order and coordinate other services."""
        print(f"Processing order: {order_data}")
        
        # In real implementation, this would enqueue tasks for:
        # - Inventory service notification
        # - Shipping service notification  
        # - Billing service notification
        
        # Simulate order processing
        return {"status": "processed", "order_id": order_data.get("id")}
    
    def notify_service(self, service_name: str, data: Dict) -> Dict:
        """Notify another microservice."""
        print(f"Notifying {service_name}: {data}")
        
        # In real implementation, this would use HTTP requests, other queues, etc.
        # Simulate service communication
        return {"status": "notified", "service": service_name}
```
        print(f"Notifying billing service: {order}")
        # Simulate API call to billing service
        time.sleep(0.7)
        return {"status": "billing_processed", "order_id": order["id"]}
    
    # Create tasks for each service
    tasks = [
        sitq.Task(function=notify_inventory_service, args=[order_data]),
        sitq.Task(function=notify_shipping_service, args=[order_data]),
        sitq.Task(function=notify_billing_service, args=[order_data])
    ]
    
    # Enqueue all tasks
    task_ids = queue.enqueue_batch(tasks)
    
    return jsonify({
        "order_id": order_data["id"],
        "status": "processing",
        "task_ids": task_ids
    })

@app.route('/order-status/<order_id>')
def get_order_status(order_id):
    """Get order processing status."""
    # In real implementation, you'd track order status
    return jsonify({
        "order_id": order_id,
        "status": "completed"
    })

if __name__ == '__main__':
    app.run(port=5001)
```

```python
# service_b.py - Consumer Service
import sitq
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Task queue and worker
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend("microservices.db"))
worker = sitq.Worker(queue, worker_id="service_b_worker")

def inventory_update_handler(order):
    """Handle inventory update requests."""
    print(f"Service B: Processing inventory update for order {order['id']}")
    
    # Simulate inventory processing
    time.sleep(1)
    
    # Update inventory
    inventory_changes = []
    for item in order.get("items", []):
        inventory_changes.append({
            "product_id": item["product_id"],
            "quantity_change": -item["quantity"],
            "timestamp": time.time()
        })
    
    return {
        "service": "inventory",
        "order_id": order["id"],
        "inventory_changes": inventory_changes,
        "status": "completed"
    }

def shipping_handler(order):
    """Handle shipping requests."""
    print(f"Service B: Processing shipping for order {order['id']}")
    
    # Simulate shipping processing
    time.sleep(0.8)
    
    return {
        "service": "shipping",
        "order_id": order["id"],
        "shipping_method": "standard",
        "estimated_delivery": time.time() + 86400 * 3,  # 3 days
        "status": "scheduled"
    }

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "service": "service_b",
        "status": "healthy",
        "worker_running": worker.get_status().is_running
    })

def start_worker():
    """Start the worker to process tasks."""
    print("Service B: Starting worker...")
    worker.run()

if __name__ == '__main__':
    # Start worker in background
    import threading
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    
    app.run(port=5002)
```

## Event-Driven Architecture

### Event Processing Pipeline

```python
# event_bus.py - Central Event Bus
import sitq
import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_PROCESSED = "payment_processed"
    INVENTORY_UPDATED = "inventory_updated"
    SHIPPING_SCHEDULED = "shipping_scheduled"
    ORDER_COMPLETED = "order_completed"

@dataclass
class Event:
    """Event data structure."""
    event_id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float
    source_service: str
    correlation_id: str = None

class EventBus:
    """Event bus using sitq for reliable event delivery."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("event_bus.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.subscribers = {}
    
    def publish_event(self, event: Event) -> str:
        """Publish event to the bus."""
        print(f"Publishing event: {event.event_type.value}")
        
        def deliver_event(event_data):
            """Deliver event to all subscribers."""
            event_type = event_data["event_type"]
            
            if event_type in self.subscribers:
                results = []
                for subscriber in self.subscribers[event_type]:
                    try:
                        result = subscriber(event_data)
                        results.append({
                            "subscriber": subscriber.__name__,
                            "result": result
                        })
                    except Exception as e:
                        results.append({
                            "subscriber": subscriber.__name__,
                            "error": str(e)
                        })
                
                return {
                    "event_id": event_data["event_id"],
                    "delivered_to": len(results),
                    "results": results
                }
            else:
                return {
                    "event_id": event_data["event_id"],
                    "delivered_to": 0,
                    "message": "No subscribers"
                }
        
        # Create event delivery task
        task = sitq.Task(
            function=deliver_event,
            args=[{
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp,
                "source_service": event.source_service,
                "correlation_id": event.correlation_id
            }]
        )
        
        task_id = self.queue.enqueue(task)
        return task_id
    
    def subscribe(self, event_type: EventType, handler):
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        print(f"Subscribed {handler.__name__} to {event_type.value}")
    
    def start_processing(self):
        """Start event processing."""
        print("Starting event bus processing...")
        self.worker.run()

# Event handlers
def inventory_event_handler(event_data):
    """Handle inventory-related events."""
    print(f"Inventory service processing: {event_data['event_type']}")
    time.sleep(0.5)
    
    if event_data["event_type"] == EventType.ORDER_CREATED.value:
        # Reserve inventory
        return {"action": "inventory_reserved", "order_id": event_data["data"]["order_id"]}
    
    return {"action": "processed", "event": event_data["event_type"]}

def shipping_event_handler(event_data):
    """Handle shipping-related events."""
    print(f"Shipping service processing: {event_data['event_type']}")
    time.sleep(0.3)
    
    if event_data["event_type"] == EventType.PAYMENT_PROCESSED.value:
        # Schedule shipping
        return {"action": "shipping_scheduled", "order_id": event_data["data"]["order_id"]}
    
    return {"action": "processed", "event": event_data["event_type"]}

def notification_event_handler(event_data):
    """Handle notification events."""
    print(f"Notification service processing: {event_data['event_type']}")
    time.sleep(0.2)
    
    # Send notification
    return {
        "action": "notification_sent",
        "event": event_data["event_type"],
        "customer_id": event_data["data"].get("customer_id")
    }

# Use event bus
def setup_event_bus():
    """Set up and configure event bus."""
    event_bus = EventBus()
    
    # Subscribe handlers
    event_bus.subscribe(EventType.ORDER_CREATED, inventory_event_handler)
    event_bus.subscribe(EventType.PAYMENT_PROCESSED, shipping_event_handler)
    event_bus.subscribe(EventType.INVENTORY_UPDATED, notification_event_handler)
    event_bus.subscribe(EventType.SHIPPING_SCHEDULED, notification_event_handler)
    
    return event_bus

if __name__ == '__main__':
    event_bus = setup_event_bus()
    
    # Start event processing in background
    import threading
    processor_thread = threading.Thread(target=event_bus.start_processing, daemon=True)
    processor_thread.start()
    
    # Simulate order flow
    import uuid
    
    # Create order
    order_event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CREATED,
        data={
            "order_id": "ORD-123",
            "customer_id": "CUST-456",
            "items": [{"product_id": "PROD-1", "quantity": 2}]
        },
        timestamp=time.time(),
        source_service="order_service",
        correlation_id=str(uuid.uuid4())
    )
    
    event_bus.publish_event(order_event)
    time.sleep(2)
    
    # Process payment
    payment_event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.PAYMENT_PROCESSED,
        data={
            "order_id": "ORD-123",
            "amount": 99.99,
            "payment_method": "credit_card"
        },
        timestamp=time.time(),
        source_service="payment_service",
        correlation_id=order_event.correlation_id
    )
    
    event_bus.publish_event(payment_event)
    
    # Keep running
    time.sleep(5)
```

## Service Orchestration

### Orchestrator Pattern

```python
# orchestrator.py - Service Orchestrator
import sitq
import time
import uuid
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """Workflow step definition."""
    step_id: str
    service_name: str
    action: str
    parameters: Dict[str, Any]
    depends_on: List[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Workflow:
    """Workflow definition."""
    workflow_id: str
    name: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: float = None
    started_at: float = None
    completed_at: float = None

class ServiceOrchestrator:
    """Service orchestrator using sitq."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("orchestrator.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.workflows = {}
    
    def create_workflow(self, name: str, steps: List[WorkflowStep]) -> str:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            steps=steps,
            created_at=time.time()
        )
        
        self.workflows[workflow_id] = workflow
        print(f"Created workflow {workflow_id}: {name}")
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str) -> str:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = time.time()
        
        def execute_workflow_steps(wf_id):
            """Execute all workflow steps."""
            workflow = self.workflows[wf_id]
            step_results = {}
            
            # Execute steps in dependency order
            for step in workflow.steps:
                # Check dependencies
                if step.depends_on:
                    for dep_id in step.depends_on:
                        if dep_id not in step_results or step_results[dep_id].get("status") != "completed":
                            raise Exception(f"Dependency {dep_id} not completed")
                
                # Execute step
                try:
                    print(f"Executing step {step.step_id}: {step.service_name}.{step.action}")
                    result = self.execute_service_step(step)
                    step_results[step.step_id] = {
                        "status": "completed",
                        "result": result,
                        "timestamp": time.time()
                    }
                except Exception as e:
                    if step.retry_count < step.max_retries:
                        print(f"Step {step.step_id} failed, retrying... ({step.retry_count + 1}/{step.max_retries})")
                        step.retry_count += 1
                        # Retry by re-queuing the workflow
                        retry_task = sitq.Task(
                            function=execute_workflow_steps,
                            args=[wf_id]
                        )
                        self.queue.enqueue(retry_task)
                        return {"status": "retrying", "step": step.step_id}
                    else:
                        step_results[step.step_id] = {
                            "status": "failed",
                            "error": str(e),
                            "timestamp": time.time()
                        }
                        workflow.status = WorkflowStatus.FAILED
                        workflow.completed_at = time.time()
                        return {"status": "failed", "step": step.step_id, "error": str(e)}
            
            # All steps completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = time.time()
            
            return {
                "status": "completed",
                "workflow_id": wf_id,
                "step_results": step_results
            }
        
        # Create workflow execution task
        task = sitq.Task(
            function=execute_workflow_steps,
            args=[workflow_id]
        )
        
        task_id = self.queue.enqueue(task)
        return task_id
    
    def execute_service_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single service step."""
        # Simulate service call
        time.sleep(0.5)
        
        # In real implementation, this would make HTTP/gRPC calls to services
        service_responses = {
            "inventory": {"status": "success", "reserved": True},
            "payment": {"status": "success", "transaction_id": str(uuid.uuid4())},
            "shipping": {"status": "success", "tracking_id": str(uuid.uuid4())},
            "notification": {"status": "success", "sent": True}
        }
        
        if step.service_name in service_responses:
            return service_responses[step.service_name]
        else:
            raise Exception(f"Unknown service: {step.service_name}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "duration": (workflow.completed_at or time.time()) - workflow.started_at if workflow.started_at else None
        }
    
    def start_orchestrator(self):
        """Start the orchestrator worker."""
        print("Starting service orchestrator...")
        self.worker.run()

# Define order processing workflow
def create_order_workflow():
    """Create order processing workflow."""
    steps = [
        WorkflowStep(
            step_id="reserve_inventory",
            service_name="inventory",
            action="reserve",
            parameters={"items": []}
        ),
        WorkflowStep(
            step_id="process_payment",
            service_name="payment",
            action="charge",
            parameters={"amount": 0},
            depends_on=["reserve_inventory"]
        ),
        WorkflowStep(
            step_id="schedule_shipping",
            service_name="shipping",
            action="schedule",
            parameters={"address": ""},
            depends_on=["process_payment"]
        ),
        WorkflowStep(
            step_id="send_confirmation",
            service_name="notification",
            action="send_email",
            parameters={"template": "order_confirmation"},
            depends_on=["schedule_shipping"]
        )
    ]
    
    return steps

# Use orchestrator
def main():
    orchestrator = ServiceOrchestrator()
    
    # Start orchestrator in background
    import threading
    orchestrator_thread = threading.Thread(target=orchestrator.start_orchestrator, daemon=True)
    orchestrator_thread.start()
    
    # Create and execute workflow
    workflow_id = orchestrator.create_workflow(
        "order_processing",
        create_order_workflow()
    )
    
    task_id = orchestrator.execute_workflow(workflow_id)
    print(f"Started workflow execution: {task_id}")
    
    # Monitor workflow
    time.sleep(5)
    status = orchestrator.get_workflow_status(workflow_id)
    print(f"Workflow status: {status}")

if __name__ == '__main__':
    main()
```

## Load Balancing

### Task Distribution Across Services

```python
# load_balancer.py - Load Balancer
import sitq
import time
import random
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ServiceInstance:
    """Service instance information."""
    instance_id: str
    service_name: str
    host: str
    port: int
    current_load: int = 0
    max_capacity: int = 100
    healthy: bool = True
    last_heartbeat: float = 0

class LoadBalancer:
    """Load balancer for distributing tasks across service instances."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("load_balancer.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.instances = {}
        self.round_robin_index = {}
    
    def register_instance(self, instance: ServiceInstance):
        """Register a service instance."""
        self.instances[instance.instance_id] = instance
        if instance.service_name not in self.round_robin_index:
            self.round_robin_index[instance.service_name] = 0
        print(f"Registered instance {instance.instance_id} for service {instance.service_name}")
    
    def select_instance(self, service_name: str, strategy: str = "least_loaded") -> ServiceInstance:
        """Select instance based on load balancing strategy."""
        service_instances = [
            instance for instance in self.instances.values()
            if instance.service_name == service_name and instance.healthy
        ]
        
        if not service_instances:
            raise Exception(f"No healthy instances available for service {service_name}")
        
        if strategy == "least_loaded":
            return min(service_instances, key=lambda x: x.current_load / x.max_capacity)
        elif strategy == "round_robin":
            index = self.round_robin_index[service_name] % len(service_instances)
            self.round_robin_index[service_name] += 1
            return service_instances[index]
        elif strategy == "random":
            return random.choice(service_instances)
        else:
            return service_instances[0]
    
    def distribute_task(self, service_name: str, task_data: Dict[str, Any], strategy: str = "least_loaded") -> str:
        """Distribute task to appropriate service instance."""
        def execute_task_on_instance(task_info):
            """Execute task on selected instance."""
            service_name = task_info["service_name"]
            task_data = task_info["task_data"]
            strategy = task_info["strategy"]
            
            # Select instance
            instance = self.select_instance(service_name, strategy)
            
            # Update load
            instance.current_load += 1
            
            try:
                # Simulate task execution
                print(f"Executing task on {instance.instance_id} ({instance.host}:{instance.port})")
                time.sleep(0.5)
                
                # Simulate task result
                result = {
                    "instance_id": instance.instance_id,
                    "service_name": service_name,
                    "task_data": task_data,
                    "result": f"Task completed on {instance.instance_id}",
                    "execution_time": 0.5
                }
                
                return result
            
            finally:
                # Update load
                instance.current_load -= 1
        
        # Create task
        task = sitq.Task(
            function=execute_task_on_instance,
            args=[{
                "service_name": service_name,
                "task_data": task_data,
                "strategy": strategy
            }]
        )
        
        task_id = self.queue.enqueue(task)
        return task_id
    
    def health_check(self):
        """Perform health check on all instances."""
        def check_instance_health(instance_id):
            """Check health of a single instance."""
            instance = self.instances[instance_id]
            
            # Simulate health check
            time.sleep(0.1)
            
            # Randomly mark instances as unhealthy for demo
            if random.random() < 0.1:  # 10% chance of being unhealthy
                instance.healthy = False
                print(f"Instance {instance_id} marked as unhealthy")
            else:
                instance.healthy = True
                instance.last_heartbeat = time.time()
            
            return {
                "instance_id": instance_id,
                "healthy": instance.healthy,
                "current_load": instance.current_load,
                "max_capacity": instance.max_capacity
            }
        
        # Create health check tasks
        health_tasks = []
        for instance_id in self.instances:
            task = sitq.Task(function=check_instance_health, args=[instance_id])
            health_tasks.append(task)
        
        task_ids = self.queue.enqueue_batch(health_tasks)
        
        # Wait for results
        results = []
        for task_id in task_ids:
            result = self.worker.process_task(task_id)
            results.append(result.value)
        
        return results
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get load balancing statistics."""
        stats = {}
        
        for service_name in set(instance.service_name for instance in self.instances.values()):
            service_instances = [
                instance for instance in self.instances.values()
                if instance.service_name == service_name
            ]
            
            total_capacity = sum(instance.max_capacity for instance in service_instances)
            current_load = sum(instance.current_load for instance in service_instances)
            healthy_instances = sum(1 for instance in service_instances if instance.healthy)
            
            stats[service_name] = {
                "total_instances": len(service_instances),
                "healthy_instances": healthy_instances,
                "total_capacity": total_capacity,
                "current_load": current_load,
                "utilization": current_load / total_capacity if total_capacity > 0 else 0
            }
        
        return stats
    
    def start_load_balancer(self):
        """Start the load balancer worker."""
        print("Starting load balancer...")
        self.worker.run()

# Use load balancer
def main():
    load_balancer = LoadBalancer()
    
    # Register service instances
    instances = [
        ServiceInstance("web_1", "web", "192.168.1.10", 8080),
        ServiceInstance("web_2", "web", "192.168.1.11", 8080),
        ServiceInstance("api_1", "api", "192.168.1.20", 8080),
        ServiceInstance("api_2", "api", "192.168.1.21", 8080),
        ServiceInstance("api_3", "api", "192.168.1.22", 8080),
    ]
    
    for instance in instances:
        load_balancer.register_instance(instance)
    
    # Start load balancer in background
    import threading
    lb_thread = threading.Thread(target=load_balancer.start_load_balancer, daemon=True)
    lb_thread.start()
    
    # Distribute some tasks
    for i in range(10):
        task_id = load_balancer.distribute_task(
            "web",
            {"request_id": f"req_{i}", "data": f"request_data_{i}"},
            strategy="least_loaded"
        )
        print(f"Distributed web task {i}: {task_id}")
    
    for i in range(15):
        task_id = load_balancer.distribute_task(
            "api",
            {"request_id": f"api_req_{i}", "data": f"api_data_{i}"},
            strategy="round_robin"
        )
        print(f"Distributed API task {i}: {task_id}")
    
    # Wait for tasks to complete
    time.sleep(5)
    
    # Get statistics
    stats = load_balancer.get_load_statistics()
    print(f"Load statistics: {stats}")
    
    # Perform health check
    health_results = load_balancer.health_check()
    print(f"Health check results: {health_results}")

if __name__ == '__main__':
    main()
```

## Best Practices

### Service Discovery

```python
# service_discovery.py - Service Discovery Integration
import sitq
import time
import json
from typing import Dict, List, Any

class ServiceDiscovery:
    """Service discovery with sitq."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("service_discovery.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.services = {}
    
    def register_service(self, service_name: str, instance_id: str, address: str, metadata: Dict = None):
        """Register a service instance."""
        def register(service_info):
            """Register service in discovery."""
            service_name = service_info["service_name"]
            instance_id = service_info["instance_id"]
            address = service_info["address"]
            metadata = service_info.get("metadata", {})
            
            if service_name not in self.services:
                self.services[service_name] = {}
            
            self.services[service_name][instance_id] = {
                "address": address,
                "metadata": metadata,
                "registered_at": time.time(),
                "last_heartbeat": time.time()
            }
            
            return {
                "service_name": service_name,
                "instance_id": instance_id,
                "status": "registered"
            }
        
        task = sitq.Task(
            function=register,
            args=[{
                "service_name": service_name,
                "instance_id": instance_id,
                "address": address,
                "metadata": metadata
            }]
        )
        
        return self.queue.enqueue(task)
    
    def discover_service(self, service_name: str) -> List[Dict]:
        """Discover service instances."""
        if service_name in self.services:
            return list(self.services[service_name].values())
        return []
    
    def start_discovery_service(self):
        """Start the discovery service."""
        self.worker.run()
```

## Next Steps

- [Web Application Example](web-app.md) - Learn about web app integration
- [Data Processing Example](data-processing.md) - Explore data processing patterns
- [Error Handling Guide](../error-handling.md) - Comprehensive error management
- [Performance Guide](../performance.md) - Optimization techniques