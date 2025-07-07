"""
Caching utilities for GenAI Contract Platform using Redis.
Provides caching for contracts, AI analysis results, and user sessions.
"""

import json
import hashlib
from typing import Optional, Any, Dict, List
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Cache key prefixes
CONTRACT_PREFIX = "contract:"
ANALYSIS_PREFIX = "analysis:"
CLAUSES_PREFIX = "clauses:"
USER_PREFIX = "user:"
METRICS_PREFIX = "metrics:"
CLIENT_PREFIX = "client:"

# Default cache timeouts (in seconds)
DEFAULT_TIMEOUT = getattr(settings, 'CACHE_TTL', 60 * 15)  # 15 minutes
ANALYSIS_TIMEOUT = 60 * 60 * 2  # 2 hours for AI analysis results
CLAUSES_TIMEOUT = 60 * 60 * 1  # 1 hour for clause extraction
METRICS_TIMEOUT = 60 * 5  # 5 minutes for metrics
USER_TIMEOUT = 60 * 30  # 30 minutes for user data


class CacheManager:
    """Manager class for all caching operations"""
    
    @staticmethod
    def generate_cache_key(prefix: str, identifier: str, *args) -> str:
        """
        Generate a consistent cache key with prefix and identifier.
        
        Args:
            prefix: Cache key prefix (e.g., "contract:", "analysis:")
            identifier: Main identifier (contract_id, user_id, etc.)
            *args: Additional arguments to include in key
            
        Returns:
            Formatted cache key string
        """
        key_parts = [prefix, str(identifier)]
        if args:
            key_parts.extend([str(arg) for arg in args])
        key = "_".join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key) > 250:
            key = f"{prefix}hash_{hashlib.md5(key.encode()).hexdigest()}"
        
        return key
    
    @staticmethod
    def set_cache(key: str, value: Any, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """
        Set cache value with error handling.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            cache.set(key, value, timeout)
            logger.info(f"Cached value for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            return False
    
    @staticmethod
    def get_cache(key: str, default: Any = None) -> Any:
        """
        Get cache value with error handling.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            value = cache.get(key, default)
            if value and isinstance(value, str):
                try:
                    # Try to deserialize JSON
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, return as string
                    pass
            
            if value is not default:
                logger.info(f"Cache hit for key: {key}")
            else:
                logger.info(f"Cache miss for key: {key}")
            
            return value
        except Exception as e:
            logger.error(f"Failed to get cache value for key {key}: {e}")
            return default
    
    @staticmethod
    def delete_cache(key: str) -> bool:
        """
        Delete cache entry.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache.delete(key)
            logger.info(f"Deleted cache key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """
        Delete cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "contract:user_123:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(pattern)
            if keys:
                deleted = redis_conn.delete(*keys)
                logger.info(f"Deleted {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to delete cache pattern {pattern}: {e}")
            return 0


class ContractCache:
    """Caching utilities specific to contracts"""
    
    @staticmethod
    def cache_contract(contract_id: str, contract_data: Dict) -> bool:
        """Cache contract data"""
        key = CacheManager.generate_cache_key(CONTRACT_PREFIX, contract_id)
        return CacheManager.set_cache(key, contract_data, DEFAULT_TIMEOUT)
    
    @staticmethod
    def get_contract(contract_id: str) -> Optional[Dict]:
        """Get cached contract data"""
        key = CacheManager.generate_cache_key(CONTRACT_PREFIX, contract_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def cache_user_contracts(user_id: str, contracts: List[Dict]) -> bool:
        """Cache user's contracts list"""
        key = CacheManager.generate_cache_key(CONTRACT_PREFIX, "user", user_id)
        return CacheManager.set_cache(key, contracts, DEFAULT_TIMEOUT)
    
    @staticmethod
    def get_user_contracts(user_id: str) -> Optional[List[Dict]]:
        """Get cached user contracts list"""
        key = CacheManager.generate_cache_key(CONTRACT_PREFIX, "user", user_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def invalidate_contract(contract_id: str) -> bool:
        """Invalidate all cache entries for a contract"""
        # Delete contract data
        contract_key = CacheManager.generate_cache_key(CONTRACT_PREFIX, contract_id)
        CacheManager.delete_cache(contract_key)
        
        # Delete related analysis and clauses
        analysis_key = CacheManager.generate_cache_key(ANALYSIS_PREFIX, contract_id)
        clauses_key = CacheManager.generate_cache_key(CLAUSES_PREFIX, contract_id)
        CacheManager.delete_cache(analysis_key)
        CacheManager.delete_cache(clauses_key)
        
        # Delete user contracts lists that might include this contract
        pattern = f"{CONTRACT_PREFIX}user:*"
        CacheManager.delete_pattern(pattern)
        
        logger.info(f"Invalidated cache for contract: {contract_id}")
        return True


class AnalysisCache:
    """Caching utilities for AI analysis results"""
    
    @staticmethod
    def cache_analysis(contract_id: str, analysis_data: Dict) -> bool:
        """Cache AI analysis result"""
        key = CacheManager.generate_cache_key(ANALYSIS_PREFIX, contract_id)
        return CacheManager.set_cache(key, analysis_data, ANALYSIS_TIMEOUT)
    
    @staticmethod
    def get_analysis(contract_id: str) -> Optional[Dict]:
        """Get cached AI analysis result"""
        key = CacheManager.generate_cache_key(ANALYSIS_PREFIX, contract_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def cache_clauses(contract_id: str, clauses_data: Dict) -> bool:
        """Cache clause extraction result"""
        key = CacheManager.generate_cache_key(CLAUSES_PREFIX, contract_id)
        return CacheManager.set_cache(key, clauses_data, CLAUSES_TIMEOUT)
    
    @staticmethod
    def get_clauses(contract_id: str) -> Optional[Dict]:
        """Get cached clause extraction result"""
        key = CacheManager.generate_cache_key(CLAUSES_PREFIX, contract_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def cache_contract_hash(contract_text: str, analysis_result: Dict) -> bool:
        """Cache analysis result by contract text hash (for duplicate detection)"""
        text_hash = hashlib.sha256(contract_text.encode()).hexdigest()
        key = CacheManager.generate_cache_key(ANALYSIS_PREFIX, "hash", text_hash)
        return CacheManager.set_cache(key, analysis_result, ANALYSIS_TIMEOUT)
    
    @staticmethod
    def get_analysis_by_hash(contract_text: str) -> Optional[Dict]:
        """Get cached analysis by contract text hash"""
        text_hash = hashlib.sha256(contract_text.encode()).hexdigest()
        key = CacheManager.generate_cache_key(ANALYSIS_PREFIX, "hash", text_hash)
        return CacheManager.get_cache(key)


class UserCache:
    """Caching utilities for user data"""
    
    @staticmethod
    def cache_user_session(user_id: str, session_data: Dict) -> bool:
        """Cache user session data"""
        key = CacheManager.generate_cache_key(USER_PREFIX, "session", user_id)
        return CacheManager.set_cache(key, session_data, USER_TIMEOUT)
    
    @staticmethod
    def get_user_session(user_id: str) -> Optional[Dict]:
        """Get cached user session data"""
        key = CacheManager.generate_cache_key(USER_PREFIX, "session", user_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def cache_user_preferences(user_id: str, preferences: Dict) -> bool:
        """Cache user preferences"""
        key = CacheManager.generate_cache_key(USER_PREFIX, "prefs", user_id)
        return CacheManager.set_cache(key, preferences, USER_TIMEOUT * 4)  # Longer timeout
    
    @staticmethod
    def get_user_preferences(user_id: str) -> Optional[Dict]:
        """Get cached user preferences"""
        key = CacheManager.generate_cache_key(USER_PREFIX, "prefs", user_id)
        return CacheManager.get_cache(key)


class MetricsCache:
    """Caching utilities for system metrics"""
    
    @staticmethod
    def cache_metrics(metrics_data: Dict) -> bool:
        """Cache system metrics"""
        key = CacheManager.generate_cache_key(METRICS_PREFIX, "system")
        return CacheManager.set_cache(key, metrics_data, METRICS_TIMEOUT)
    
    @staticmethod
    def get_metrics() -> Optional[Dict]:
        """Get cached system metrics"""
        key = CacheManager.generate_cache_key(METRICS_PREFIX, "system")
        return CacheManager.get_cache(key)
    
    @staticmethod
    def increment_counter(counter_name: str, increment: int = 1) -> int:
        """Increment a counter in cache"""
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            key = CacheManager.generate_cache_key(METRICS_PREFIX, "counter", counter_name)
            return redis_conn.incr(key, increment)
        except Exception as e:
            logger.error(f"Failed to increment counter {counter_name}: {e}")
            return 0
    
    @staticmethod
    def get_counter(counter_name: str) -> int:
        """Get counter value"""
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            key = CacheManager.generate_cache_key(METRICS_PREFIX, "counter", counter_name)
            value = redis_conn.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Failed to get counter {counter_name}: {e}")
            return 0


class ClientCache:
    """Caching utilities for client data"""
    
    @staticmethod
    def cache_client(client_id: str, client_data: Dict) -> bool:
        """Cache client data"""
        key = CacheManager.generate_cache_key(CLIENT_PREFIX, client_id)
        return CacheManager.set_cache(key, client_data, DEFAULT_TIMEOUT)
    
    @staticmethod
    def get_client(client_id: str) -> Optional[Dict]:
        """Get cached client data"""
        key = CacheManager.generate_cache_key(CLIENT_PREFIX, client_id)
        return CacheManager.get_cache(key)
    
    @staticmethod
    def cache_all_clients(clients: List[Dict]) -> bool:
        """Cache all clients list"""
        key = CacheManager.generate_cache_key(CLIENT_PREFIX, "all")
        return CacheManager.set_cache(key, clients, DEFAULT_TIMEOUT)
    
    @staticmethod
    def get_all_clients() -> Optional[List[Dict]]:
        """Get cached all clients list"""
        key = CacheManager.generate_cache_key(CLIENT_PREFIX, "all")
        return CacheManager.get_cache(key)
    
    @staticmethod
    def invalidate_client(client_id: str) -> bool:
        """Invalidate cache for a client"""
        client_key = CacheManager.generate_cache_key(CLIENT_PREFIX, client_id)
        all_clients_key = CacheManager.generate_cache_key(CLIENT_PREFIX, "all")
        
        CacheManager.delete_cache(client_key)
        CacheManager.delete_cache(all_clients_key)
        
        logger.info(f"Invalidated cache for client: {client_id}")
        return True


# Decorator for caching function results
def cache_result(timeout: int = DEFAULT_TIMEOUT, key_prefix: str = "func"):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            cache_key = CacheManager.generate_cache_key("", "_".join(key_parts))
            
            # Try to get from cache
            result = CacheManager.get_cache(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheManager.set_cache(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


# Utility functions for cache health monitoring
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics and health information"""
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        info = redis_conn.info()
        stats = {
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "used_memory_peak": info.get("used_memory_peak_human"),
        }
        
        # Calculate hit rate
        hits = stats["keyspace_hits"]
        misses = stats["keyspace_misses"]
        total = hits + misses
        if total > 0:
            stats["hit_rate"] = round((hits / total) * 100, 2)
        else:
            stats["hit_rate"] = 0
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e)}


def clear_all_cache() -> bool:
    """Clear all cache entries (use with caution)"""
    try:
        cache.clear()
        logger.warning("All cache entries cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return False 