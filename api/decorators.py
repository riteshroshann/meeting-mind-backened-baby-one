import time
import functools
import logging
import traceback
from django.http import JsonResponse
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)

def measure_latency(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    return wrapper

def standardize_api(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs) -> JsonResponse:
        start_time = time.time()
        
        try:
            response_data = func(request, *args, **kwargs)
            
            # Handle direct JsonResponse returns (e.g. from existing views)
            if isinstance(response_data, JsonResponse):
                return response_data
                
            latency_ms = (time.time() - start_time) * 1000
            
            return JsonResponse({
                "success": True,
                "meta": {
                    "latency_ms": round(latency_ms, 2),
                    "method": request.method,
                    "path": request.path
                },
                "data": response_data
            }, status=200)
            
        except APIError as e:
            logger.warning(f"API Error: {e.message} ({e.code})")
            return JsonResponse({
                "success": False,
                "error": {
                    "code": e.code,
                    "message": e.message
                },
                "meta": {
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
            }, status=e.status_code)
            
        except Exception as e:
            logger.error(f"Unhandled Exception: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred."
                },
                "meta": {
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
            }, status=500)
            
    return wrapper

def cors_headers(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        return response
    return wrapper
