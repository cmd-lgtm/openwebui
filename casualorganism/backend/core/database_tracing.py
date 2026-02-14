"""
Custom OpenTelemetry instrumentation for database operations.

This module provides tracing instrumentation for:
- Neo4j driver (graph database)
- Redis client (cache and message queue)
- asyncpg (TimescaleDB/PostgreSQL)

Requirements:
- 16.4: System SHALL include database query timing in traces
"""

from typing import Optional, Any, Callable
from functools import wraps
import asyncio
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes


class Neo4jInstrumentation:
    """
    Custom instrumentation for Neo4j driver operations.
    
    Wraps Neo4j session operations to emit OpenTelemetry spans.
    """
    
    @staticmethod
    def instrument_session(session, tracer: trace.Tracer):
        """
        Instrument a Neo4j session to emit traces for queries.
        
        Args:
            session: Neo4j session instance
            tracer: OpenTelemetry tracer
        
        Returns:
            Instrumented session
        """
        original_run = session.run
        
        def traced_run(query: str, parameters: dict = None, **kwargs):
            """Traced version of session.run()"""
            with tracer.start_as_current_span(
                "neo4j.query",
                kind=trace.SpanKind.CLIENT
            ) as span:
                # Add span attributes
                span.set_attribute(SpanAttributes.DB_SYSTEM, "neo4j")
                span.set_attribute(SpanAttributes.DB_STATEMENT, query)
                span.set_attribute(SpanAttributes.DB_OPERATION, _extract_operation(query))
                
                if parameters:
                    span.set_attribute("db.parameters.count", len(parameters))
                
                try:
                    result = original_run(query, parameters, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        session.run = traced_run
        return session
    
    @staticmethod
    def trace_query(tracer: trace.Tracer):
        """
        Decorator to trace Neo4j query execution.
        
        Usage:
            @Neo4jInstrumentation.trace_query(tracer)
            async def execute_query(self, query: str, params: dict):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract query from args if available
                query = kwargs.get('query') or (args[1] if len(args) > 1 else "unknown")
                
                with tracer.start_as_current_span(
                    "neo4j.query",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute(SpanAttributes.DB_SYSTEM, "neo4j")
                    span.set_attribute(SpanAttributes.DB_STATEMENT, str(query)[:500])  # Truncate long queries
                    span.set_attribute(SpanAttributes.DB_OPERATION, _extract_operation(str(query)))
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                query = kwargs.get('query') or (args[1] if len(args) > 1 else "unknown")
                
                with tracer.start_as_current_span(
                    "neo4j.query",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute(SpanAttributes.DB_SYSTEM, "neo4j")
                    span.set_attribute(SpanAttributes.DB_STATEMENT, str(query)[:500])
                    span.set_attribute(SpanAttributes.DB_OPERATION, _extract_operation(str(query)))
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


class RedisInstrumentation:
    """
    Custom instrumentation for Redis operations.
    
    Note: opentelemetry-instrumentation-redis provides automatic instrumentation,
    but this class provides additional manual instrumentation capabilities.
    """
    
    @staticmethod
    def trace_operation(tracer: trace.Tracer, operation: str):
        """
        Decorator to trace Redis operations.
        
        Args:
            tracer: OpenTelemetry tracer
            operation: Redis operation name (e.g., "get", "set", "xadd")
        
        Usage:
            @RedisInstrumentation.trace_operation(tracer, "get")
            async def get(self, key: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(
                    f"redis.{operation}",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute(SpanAttributes.DB_SYSTEM, "redis")
                    span.set_attribute(SpanAttributes.DB_OPERATION, operation)
                    
                    # Add key if available
                    key = kwargs.get('key') or (args[1] if len(args) > 1 else None)
                    if key:
                        span.set_attribute("db.redis.key", str(key))
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(
                    f"redis.{operation}",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute(SpanAttributes.DB_SYSTEM, "redis")
                    span.set_attribute(SpanAttributes.DB_OPERATION, operation)
                    
                    key = kwargs.get('key') or (args[1] if len(args) > 1 else None)
                    if key:
                        span.set_attribute("db.redis.key", str(key))
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


class AsyncpgInstrumentation:
    """
    Custom instrumentation for asyncpg (PostgreSQL/TimescaleDB) operations.
    """
    
    @staticmethod
    def trace_query(tracer: trace.Tracer):
        """
        Decorator to trace asyncpg query execution.
        
        Usage:
            @AsyncpgInstrumentation.trace_query(tracer)
            async def execute(self, query: str, *args):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract query from args
                query = kwargs.get('query') or (args[1] if len(args) > 1 else "unknown")
                
                with tracer.start_as_current_span(
                    "postgresql.query",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
                    span.set_attribute(SpanAttributes.DB_STATEMENT, str(query)[:500])  # Truncate long queries
                    span.set_attribute(SpanAttributes.DB_OPERATION, _extract_sql_operation(str(query)))
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        
                        # Add result count if available
                        if hasattr(result, '__len__'):
                            span.set_attribute("db.result.count", len(result))
                        
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            return wrapper
        
        return decorator
    
    @staticmethod
    async def instrument_connection(connection, tracer: trace.Tracer):
        """
        Instrument an asyncpg connection to emit traces for queries.
        
        Args:
            connection: asyncpg connection instance
            tracer: OpenTelemetry tracer
        
        Returns:
            Instrumented connection
        """
        original_execute = connection.execute
        original_fetch = connection.fetch
        original_fetchrow = connection.fetchrow
        
        async def traced_execute(query: str, *args, **kwargs):
            """Traced version of connection.execute()"""
            with tracer.start_as_current_span(
                "postgresql.execute",
                kind=trace.SpanKind.CLIENT
            ) as span:
                span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
                span.set_attribute(SpanAttributes.DB_STATEMENT, query[:500])
                span.set_attribute(SpanAttributes.DB_OPERATION, _extract_sql_operation(query))
                
                try:
                    result = await original_execute(query, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        async def traced_fetch(query: str, *args, **kwargs):
            """Traced version of connection.fetch()"""
            with tracer.start_as_current_span(
                "postgresql.fetch",
                kind=trace.SpanKind.CLIENT
            ) as span:
                span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
                span.set_attribute(SpanAttributes.DB_STATEMENT, query[:500])
                span.set_attribute(SpanAttributes.DB_OPERATION, _extract_sql_operation(query))
                
                try:
                    result = await original_fetch(query, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("db.result.count", len(result))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        async def traced_fetchrow(query: str, *args, **kwargs):
            """Traced version of connection.fetchrow()"""
            with tracer.start_as_current_span(
                "postgresql.fetchrow",
                kind=trace.SpanKind.CLIENT
            ) as span:
                span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
                span.set_attribute(SpanAttributes.DB_STATEMENT, query[:500])
                span.set_attribute(SpanAttributes.DB_OPERATION, _extract_sql_operation(query))
                
                try:
                    result = await original_fetchrow(query, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        connection.execute = traced_execute
        connection.fetch = traced_fetch
        connection.fetchrow = traced_fetchrow
        
        return connection


def _extract_operation(query: str) -> str:
    """
    Extract operation type from Cypher query.
    
    Args:
        query: Cypher query string
    
    Returns:
        Operation type (e.g., "MATCH", "CREATE", "MERGE")
    """
    query_upper = query.strip().upper()
    
    # Common Cypher operations
    operations = ["MATCH", "CREATE", "MERGE", "DELETE", "SET", "REMOVE", "RETURN", "WITH", "CALL"]
    
    for op in operations:
        if query_upper.startswith(op):
            return op
    
    return "UNKNOWN"


def _extract_sql_operation(query: str) -> str:
    """
    Extract operation type from SQL query.
    
    Args:
        query: SQL query string
    
    Returns:
        Operation type (e.g., "SELECT", "INSERT", "UPDATE")
    """
    query_upper = query.strip().upper()
    
    # Common SQL operations
    operations = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"]
    
    for op in operations:
        if query_upper.startswith(op):
            return op
    
    return "UNKNOWN"
