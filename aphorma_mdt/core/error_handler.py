"""
Error Handling Framework
Provides centralized error handling and logging
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Union, Dict, Any
import logging
import traceback
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = None, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, error_code="VALIDATION_ERROR", details=details)

class NotFoundError(AppError):
    def __init__(self, message: str, resource: str = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, error_code="NOT_FOUND", details={"resource": resource} if resource else {})

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, error_code="UNAUTHORIZED")

class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, error_code="FORBIDDEN")

class ConflictError(AppError):
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, error_code="CONFLICT", details=details)

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error(f"AppError: {exc.message}", extra={"error_code": exc.error_code, "status_code": exc.status_code, "path": request.url.path, "method": request.method})    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "error_code": exc.error_code, "message": exc.message, "details": exc.details, "timestamp": datetime.utcnow().isoformat()}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"ValidationError: {exc.errors()}", extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": True, "error_code": "VALIDATION_ERROR", "message": "Request validation failed", "details": exc.errors(), "timestamp": datetime.utcnow().isoformat()}
    )

async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"DatabaseError: {str(exc)}", extra={"path": request.url.path, "method": request.method, "error_type": type(exc).__name__})
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": True, "error_code": "DATABASE_ERROR", "message": "Database integrity error", "details": {"type": "integrity_error"}, "timestamp": datetime.utcnow().isoformat()}
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": True, "error_code": "DATABASE_ERROR", "message": "Database error occurred", "details": {}, "timestamp": datetime.utcnow().isoformat()}
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"UnhandledError: {str(exc)}", extra={"path": request.url.path, "method": request.method, "traceback": traceback.format_exc()})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": True, "error_code": "INTERNAL_ERROR", "message": "Internal server error", "details": {}, "timestamp": datetime.utcnow().isoformat()}
    )

def create_error_response(message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = None, details: Dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "error_code": error_code or f"ERR_{status_code}", "message": message, "details": details or {}, "timestamp": datetime.utcnow().isoformat()}
    )

def create_success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"error": False, "message": message, "data": data, "timestamp": datetime.utcnow().isoformat()}
    )
