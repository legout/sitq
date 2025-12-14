# Backend Configuration

Learn how to configure and optimize different sitq backends for production use cases, including connection pooling, performance tuning, and high availability setups.

## What You'll Learn

- Backend selection criteria and configuration
- Connection pooling and optimization techniques
- Performance tuning parameters for different backends
- High availability and failover configurations
- Monitoring and maintenance strategies

## Prerequisites

- Complete all [Basic Examples](../basic/) first
- Understanding of database and messaging systems
- Knowledge of production deployment concepts

## Code Example

```python
import asyncio
import time
from typing import Dict, Any, Optional
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.backends.postgres import PostgreSQLBackend
from sitq.backends.redis import RedisBackend
from sitq.backends.nats import NATSBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Backend Configuration Classes
class BackendConfig:
    """Base configuration for sitq backends."""
    
    def __init__(self):
        self.metrics = {
            "connection_time": 0,
            "enqueue_time": 0,
            "dequeue_time": 0,
            "error_count": 0
        }
    
    async def measure_operation(self, operation_name: str, operation):
        """Measure operation performance."""
        start_time = time.time()
        try:
            result = await operation()
            duration = time.time() - start_time
            self.metrics[f"{operation_name}_time"] += duration
            return result
        except Exception as e:
            self.metrics["error_count"] += 1
            raise

class SQLiteConfig(BackendConfig):
    """Configuration for SQLite backend."""
    
    def __init__(self, db_path: str = "production_queue.db"):
        super().__init__()
        self.db_path = db_path
        self.wal_mode = True
        self.cache_size = 2000
        self.synchronous = "NORMAL"
        self.journal_mode = "WAL"
    
    def create_backend(self):
        """Create optimized SQLite backend."""
        backend = SQLiteBackend(self.db_path)
        
        # Apply optimizations (these would be backend-specific settings)
        print(f"🗄️  SQLite Backend Configuration:")
        print(f"   Database: {self.db_path}")
        print(f"   WAL Mode: {self.wal_mode}")
        print(f"   Cache Size: {self.cache_size}")
        
        return backend

class PostgreSQLConfig(BackendConfig):
    """Configuration for PostgreSQL backend."""
    
    def __init__(self, 
                 connection_string: str,
                 pool_size: int = 10,
                 max_overflow: int = 20):
        super().__init__()
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = 30
        self.pool_recycle = 3600
    
    def create_backend(self):
        """Create optimized PostgreSQL backend."""
        backend = PostgreSQLBackend(
            connection_string=self.connection_string,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle
        )
        
        print(f"🐘 PostgreSQL Backend Configuration:")
        print(f"   Connection: {self.connection_string[:20]}...")
        print(f"   Pool Size: {self.pool_size}")
        print(f"   Max Overflow: {self.max_overflow}")
        print(f"   Pool Timeout: {self.pool_timeout}s")
        
        return backend

class RedisConfig(BackendConfig):
    """Configuration for Redis backend."""
    
    def __init__(self,
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 max_connections: int = 20):
        super().__init__()
        self.host = host
        self.port = port
        self.db = db
        self.max_connections = max_connections
        self.socket_timeout = 5
        self.socket_connect_timeout = 5
    
    def create_backend(self):
        """Create optimized Redis backend."""
        backend = RedisBackend(
            host=self.host,
            port=self.port,
            db=self.db,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout
        )
        
        print(f"🔴 Redis Backend Configuration:")
        print(f"   Host: {self.host}:{self.port}")
        print(f"   Database: {self.db}")
        print(f"   Max Connections: {self.max_connections}")
        
        return backend

class NATSConfig(BackendConfig):
    """Configuration for NATS backend."""
    
    def __init__(self,
                 servers: list,
                 stream_name: str = "sitq_tasks",
                 max_reconnect_attempts: int = 5):
        super().__init__()
        self.servers = servers
        self.stream_name = stream_name
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_wait = 2
        self.ping_interval = 20
        self.max_pings_outstanding = 3
    
    def create_backend(self):
        """Create optimized NATS backend."""
        backend = NATSBackend(
            servers=self.servers,
            stream_name=self.stream_name,
            max_reconnect_attempts=self.max_reconnect_attempts,
            reconnect_wait=self.reconnect_wait,
            ping_interval=self.ping_interval,
            max_pings_outstanding=self.max_pings_outstanding
        )
        
        print(f"🚀 NATS Backend Configuration:")
        print(f"   Servers: {self.servers}")
        print(f"   Stream: {self.stream_name}")
        print(f"   Max Reconnect: {self.max_reconnect_attempts}")
        
        return backend

# Step 2: Performance Benchmarking
async def benchmark_backends():
    """Benchmark different backend configurations."""
    print("=" * 60)
    print("BACKEND PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Test data
    test_tasks = [
        ("simple_task", f"test_data_{i}")
        for i in range(100)
    ]
    
    backend_configs = [
        ("SQLite", SQLiteConfig("benchmark.db")),
        ("PostgreSQL", PostgreSQLConfig("postgresql://user:pass@localhost/sitq")),
        ("Redis", RedisConfig()),
        ("NATS", NATSConfig(["nats://localhost:4222"]))
    ]
    
    results = {}
    
    for backend_name, config in backend_configs:
        print(f"\n🧪 Benchmarking {backend_name} Backend:")
        
        try:
            backend = config.create_backend()
            serializer = CloudpickleSerializer()
            queue = TaskQueue(backend, serializer)
            
            # Measure connection time
            connect_time = await config.measure_operation(
                "connection",
                lambda: queue.connect()
            )
            
            # Start worker
            worker = Worker(backend, serializer, max_concurrency=5)
            await worker.start()
            
            # Measure enqueue performance
            enqueue_start = time.time()
            task_ids = []
            
            for task_name, data in test_tasks:
                task_id = await config.measure_operation(
                    "enqueue",
                    lambda: queue.enqueue(simple_task, data)
                )
                task_ids.append(task_id)
            
            enqueue_time = time.time() - enqueue_start
            
            # Wait for processing
            await asyncio.sleep(5)
            
            # Measure dequeue performance
            dequeue_start = time.time()
            completed_tasks = 0
            
            for task_id in task_ids:
                result = await queue.get_result(task_id, timeout=2)
                if result and result.is_success():
                    completed_tasks += 1
            
            dequeue_time = time.time() - dequeue_start
            
            # Store results
            results[backend_name] = {
                "connection_time": config.metrics["connection_time"],
                "enqueue_time": enqueue_time,
                "dequeue_time": dequeue_time,
                "completed_tasks": completed_tasks,
                "total_tasks": len(test_tasks),
                "throughput": completed_tasks / max(enqueue_time, dequeue_time),
                "error_count": config.metrics["error_count"]
            }
            
            await worker.stop()
            await queue.close()
            
            # Print results
            print(f"   ✅ Connection: {config.metrics['connection_time']:.3f}s")
            print(f"   ✅ Enqueue: {enqueue_time:.3f}s ({len(test_tasks)/enqueue_time:.1f} tasks/s)")
            print(f"   ✅ Dequeue: {dequeue_time:.3f}s ({completed_tasks/dequeue_time:.1f} tasks/s)")
            print(f"   ✅ Success Rate: {completed_tasks/len(test_tasks)*100:.1f}%")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results[backend_name] = {"error": str(e)}
    
    # Summary
    print(f"\n📊 Benchmark Summary:")
    for backend_name, result in results.items():
        if "error" not in result:
            print(f"   {backend_name}: {result['throughput']:.1f} tasks/s")
        else:
            print(f"   {backend_name}: FAILED")

# Step 3: High Availability Configuration
async def demo_high_availability():
    """Demonstrate high availability backend configurations."""
    print("\n" + "=" * 60)
    print("HIGH AVAILABILITY CONFIGURATION")
    print("=" * 60)
    
    # Redis Cluster Configuration
    print("\n🔴 Redis Cluster Setup:")
    redis_cluster_config = {
        "startup_nodes": [
            {"host": "redis-node-1", "port": 6379},
            {"host": "redis-node-2", "port": 6379},
            {"host": "redis-node-3", "port": 6379}
        ],
        "decode_responses": True,
        "skip_full_coverage_check": False,
        "max_connections_per_node": 16
    }
    
    print("   Cluster Nodes:")
    for node in redis_cluster_config["startup_nodes"]:
        print(f"     - {node['host']}:{node['port']}")
    
    # NATS Cluster Configuration
    print("\n🚀 NATS Cluster Setup:")
    nats_cluster_config = {
        "servers": [
            "nats://nats-1:4222",
            "nats://nats-2:4222", 
            "nats://nats-3:4222"
        ],
        "max_reconnect_attempts": 10,
        "reconnect_wait": 2,
        "ping_interval": 15,
        "max_pings_outstanding": 5
    }
    
    print("   NATS Servers:")
    for server in nats_cluster_config["servers"]:
        print(f"     - {server}")
    
    # PostgreSQL Replication Setup
    print("\n🐘 PostgreSQL Replication Setup:")
    pg_config = {
        "primary": "postgresql://user:pass@pg-primary:5432/sitq",
        "replicas": [
            "postgresql://user:pass@pg-replica-1:5432/sitq",
            "postgresql://user:pass@pg-replica-2:5432/sitq"
        ],
        "pool_size": 20,
        "max_overflow": 30,
        "failover_timeout": 5
    }
    
    print(f"   Primary: {pg_config['primary'][:30]}...")
    print("   Replicas:")
    for replica in pg_config["replicas"]:
        print(f"     - {replica[:30]}...")

# Step 4: Connection Pooling Optimization
async def demo_connection_pooling():
    """Demonstrate connection pooling optimization."""
    print("\n" + "=" * 60)
    print("CONNECTION POOLING OPTIMIZATION")
    print("=" * 60)
    
    pool_sizes = [1, 5, 10, 20, 50]
    test_concurrency = [5, 10, 20, 50]
    
    print("🔧 Testing different pool sizes:")
    
    for pool_size in pool_sizes:
        print(f"\n📊 Pool Size: {pool_size}")
        
        # Create backend with specific pool size
        config = PostgreSQLConfig(
            connection_string="postgresql://user:pass@localhost/sitq",
            pool_size=pool_size,
            max_overflow=pool_size // 2
        )
        
        try:
            backend = config.create_backend()
            queue = TaskQueue(backend, CloudpickleSerializer())
            await queue.connect()
            
            # Test with different concurrency levels
            for concurrency in test_concurrency:
                if concurrency <= pool_size * 2:  # Don't exceed reasonable limits
                    print(f"   Testing {concurrency} concurrent operations...")
                    
                    # Simulate concurrent operations
                    start_time = time.time()
                    
                    tasks = []
                    for i in range(concurrency):
                        task_id = await queue.enqueue(simple_task, f"pool_test_{i}")
                        tasks.append(task_id)
                    
                    duration = time.time() - start_time
                    print(f"     ✅ {concurrency} tasks in {duration:.3f}s")
            
            await queue.close()
            
        except Exception as e:
            print(f"   ❌ Pool size {pool_size} failed: {e}")

# Step 5: Monitoring and Maintenance
class BackendMonitor:
    """Monitor backend health and performance."""
    
    def __init__(self, backend, backend_name: str):
        self.backend = backend
        self.backend_name = backend_name
        self.metrics = {
            "connection_errors": 0,
            "slow_operations": 0,
            "total_operations": 0,
            "avg_response_time": 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform backend health check."""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            await self.backend._get_connection()
            
            response_time = time.time() - start_time
            
            health_status = {
                "backend": self.backend_name,
                "status": "healthy",
                "response_time": response_time,
                "timestamp": time.time()
            }
            
            if response_time > 1.0:
                health_status["status"] = "degraded"
                self.metrics["slow_operations"] += 1
            
            return health_status
            
        except Exception as e:
            self.metrics["connection_errors"] += 1
            return {
                "backend": self.backend_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            "backend": self.backend_name,
            "metrics": self.metrics,
            "health_score": self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate health score (0-100)."""
        total_ops = self.metrics["total_operations"]
        if total_ops == 0:
            return 100.0
        
        error_rate = self.metrics["connection_errors"] / total_ops
        slow_rate = self.metrics["slow_operations"] / total_ops
        
        health_score = 100.0 - (error_rate * 50) - (slow_rate * 20)
        return max(0.0, health_score)

async def demo_monitoring():
    """Demonstrate backend monitoring."""
    print("\n" + "=" * 60)
    print("BACKEND MONITORING")
    print("=" * 60)
    
    # Create backends to monitor
    backends_to_monitor = [
        (SQLiteConfig("monitor.db").create_backend(), "SQLite"),
        (RedisConfig().create_backend(), "Redis"),
    ]
    
    monitors = []
    
    for backend, name in backends_to_monitor:
        monitor = BackendMonitor(backend, name)
        monitors.append(monitor)
        print(f"🔍 Started monitoring {name} backend")
    
    # Simulate monitoring over time
    for i in range(5):
        print(f"\n📊 Health Check Round {i + 1}:")
        
        for monitor in monitors:
            health = await monitor.health_check()
            metrics = monitor.get_metrics()
            
            print(f"   {health['backend']}: {health['status']} "
                  f"({health['response_time']:.3f}s, "
                  f"score: {metrics['health_score']:.1f})")
        
        await asyncio.sleep(2)
    
    # Final metrics summary
    print(f"\n📈 Final Metrics Summary:")
    for monitor in monitors:
        metrics = monitor.get_metrics()
        print(f"   {metrics['backend']}:")
        print(f"     Health Score: {metrics['health_score']:.1f}/100")
        print(f"     Connection Errors: {metrics['metrics']['connection_errors']}")
        print(f"     Slow Operations: {metrics['metrics']['slow_operations']}")

# Helper task function
async def simple_task(data: str) -> str:
    """Simple task for testing."""
    await asyncio.sleep(0.01)  # Simulate minimal work
    return f"processed_{data}"

async def main():
    """Run all backend configuration demonstrations."""
    print("🔧 Backend Configuration Examples for sitq")
    print("This demo shows how to configure and optimize different backends.\n")
    
    await benchmark_backends()
    await demo_high_availability()
    await demo_connection_pooling()
    await demo_monitoring()
    
    print("\n✅ All backend configuration demos completed!")
    print("\n📚 Key Takeaways:")
    print("   • Choose backend based on your use case (performance vs reliability)")
    print("   • Optimize connection pooling for your expected load")
    print("   • Implement monitoring for production deployments")
    print("   • Consider high availability for critical applications")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Backend Selection

| Backend | Best For | Characteristics |
|---------|-----------|----------------|
| SQLite | Development, small applications | Simple, file-based, single-process |
| PostgreSQL | Production, relational data | ACID compliance, complex queries |
| Redis | High performance, caching | In-memory, fast, pub/sub |
| NATS | Distributed systems, messaging | Cloud-native, streaming, scalable |

### Performance Optimization

**Connection Pooling:**
- **Pool Size**: Match to expected concurrent load
- **Timeout Settings**: Balance responsiveness and reliability
- **Overflow Handling**: Handle traffic spikes gracefully

**Configuration Tuning:**
- **Batch Sizes**: Optimize for your workload
- **Timeout Values**: Set appropriate for your infrastructure
- **Retry Logic**: Handle transient failures

### High Availability

**Database Replication:**
- **Primary-Replica**: Read scaling and failover
- **Connection Failover**: Automatic replica promotion
- **Consistency**: Choose appropriate level

**Messaging Clusters:**
- **Multi-node**: Distribute load and increase reliability
- **Auto-reconnect**: Handle network partitions
- **Load Balancing**: Distribute client connections

## Best Practices

### Development
```python
# Use SQLite for development and testing
backend = SQLiteBackend("dev_queue.db")
```

### Production
```python
# Use PostgreSQL for production with connection pooling
backend = PostgreSQLBackend(
    connection_string="postgresql://user:pass@localhost/sitq",
    pool_size=20,
    max_overflow=30
)
```

### High Performance
```python
# Use Redis for high-throughput scenarios
backend = RedisBackend(
    host="redis-cluster",
    max_connections=50,
    socket_timeout=5
)
```

## Try It Yourself

1. **Benchmark different backends:**
   ```python
   # Test with your specific workload
   backends = [
       SQLiteConfig("test.db"),
       PostgreSQLConfig("postgresql://..."),
       RedisConfig()
   ]
   
   for config in backends:
       await benchmark_backend(config.create_backend())
   ```

2. **Optimize connection pooling:**
   ```python
   # Find optimal pool size for your load
   for pool_size in [5, 10, 20, 50]:
       config = PostgreSQLConfig(conn_str, pool_size=pool_size)
       await test_performance(config.create_backend())
   ```

3. **Set up monitoring:**
   ```python
   # Create custom monitoring for your backend
   monitor = BackendMonitor(backend, "MyBackend")
   
   # Schedule regular health checks
   asyncio.create_task(periodic_health_check(monitor))
   ```

## Next Steps

- Explore [CPU-bound Tasks](./cpu-bound-tasks.md) for performance optimization
- Learn about [Sync Wrapper](./sync-wrapper.md) for integration patterns
- Review [Basic Examples](../basic/) for foundational concepts

## Related Advanced Examples

- [CPU-bound Tasks](./cpu-bound-tasks.md) - Performance optimization
- [Sync Wrapper](./sync-wrapper.md) - Legacy integration