"""
Security Module - Input validation, sanitization, and security utilities
"""
import re
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PromptSecurityValidator:
    """Validates and sanitizes user inputs to prevent prompt injection"""
    
    # Patterns that indicate potential prompt injection attacks
    BLOCKED_PATTERNS = [
        r'ignore previous instructions',
        r'ignore all previous',
        r'forget everything',
        r'system:',
        r'admin:',
        r'<script',
        r'javascript:',
        r'onclick=',
        r'onerror=',
        r'onload=',
        r'\beval\b',
        r'\bexec\b',
        r'__import__',
        r'system\(',
        r'subprocess',
        r'os\.system',
        r'os\.exec',
    ]
    
    # Suspicious SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"('\s*or\s*'.*'=')",
        r'"\s*or\s*".*"="',
        r';\s*drop',
        r';\s*delete',
        r';\s*update',
        r'union\s+select',
        r'insert\s+into',
    ]
    
    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 1000) -> str:
        """
        Sanitize user input
        
        Args:
            user_input: User-provided input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized input
            
        Raises:
            ValueError: If suspicious patterns detected
        """
        if not user_input:
            return ""
        
        # Check length
        if len(user_input) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")
        
        # Check for blocked patterns
        for pattern in PromptSecurityValidator.BLOCKED_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Blocked pattern detected in input: {pattern}")
                raise ValueError("Malicious input pattern detected")
        
        # Check for SQL injection patterns
        for pattern in PromptSecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                raise ValueError("Suspicious SQL pattern detected")
        
        return user_input.strip()
    
    @staticmethod
    def validate_repository_url(url: str) -> str:
        """
        Validate repository URL
        
        Args:
            url: Repository URL
            
        Returns:
            Validated URL
            
        Raises:
            ValueError: If URL is invalid
        """
        # Only allow HTTPS or SSH git URLs
        valid_patterns = [
            r'^https://github\.com/[\w\-\.]+/[\w\-\.]+\.git$',
            r'^https://gitlab\.com/[\w\-\.]+/[\w\-\.]+\.git$',
            r'^https://bitbucket\.org/[\w\-\.]+/[\w\-\.]+\.git$',
            r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$',
            r'^git@gitlab\.com:[\w\-\.]+/[\w\-\.]+\.git$',
        ]
        
        if not any(re.match(pattern, url) for pattern in valid_patterns):
            raise ValueError("Invalid repository URL. Only GitHub, GitLab, and Bitbucket are supported.")
        
        return url
    
    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """
        Validate file path to prevent directory traversal
        
        Args:
            file_path: File path
            
        Returns:
            Validated file path
            
        Raises:
            ValueError: If path is invalid
        """
        # Reject paths with ../ or absolute paths starting with /
        if ".." in file_path or file_path.startswith("/"):
            raise ValueError("Invalid file path")
        
        # Reject suspicious patterns
        if re.search(r'[<>:"|?*]', file_path):
            raise ValueError("File path contains invalid characters")
        
        return file_path


class ImpactAnalysisRequest(BaseModel):
    """Validated request model for impact analysis"""
    
    change_description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Description of code changes"
    )
    affected_files: list[str] = Field(
        default=[],
        max_items=100,
        description="List of affected files"
    )
    repo_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex='^[a-zA-Z0-9\-_]+$',
        description="Repository identifier"
    )
    branch: str = Field(
        default="main",
        min_length=1,
        max_length=100,
        description="Git branch name"
    )
    
    @validator('change_description')
    def validate_change_description(cls, v):
        """Validate change description"""
        try:
            PromptSecurityValidator.sanitize_input(v)
        except ValueError as e:
            raise ValueError(f"Invalid change description: {str(e)}")
        return v
    
    @validator('affected_files', each_item=True)
    def validate_file(cls, v):
        """Validate each file path"""
        try:
            PromptSecurityValidator.validate_file_path(v)
        except ValueError as e:
            raise ValueError(f"Invalid file path: {str(e)}")
        return v


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """Simple rate limiter based on IP address"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 500):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_history: Dict[str, list] = {}
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if within limits, False if exceeded
        """
        import time
        
        current_time = time.time()
        
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Remove old entries (older than 1 hour)
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 3600
        ]
        
        # Check rate limits
        requests_last_minute = len([
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 60
        ])
        
        if requests_last_minute >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {requests_last_minute} requests/min")
            return False
        
        if len(self.request_history[client_ip]) >= self.requests_per_hour:
            logger.warning(f"Hourly rate limit exceeded for IP {client_ip}")
            return False
        
        # Record this request
        self.request_history[client_ip].append(current_time)
        return True
    
    def get_remaining_requests(self, client_ip: str) -> Dict[str, int]:
        """Get remaining requests for client"""
        import time
        
        current_time = time.time()
        
        if client_ip not in self.request_history:
            return {
                "remaining_per_minute": self.requests_per_minute,
                "remaining_per_hour": self.requests_per_hour
            }
        
        # Remove old entries
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 3600
        ]
        
        requests_last_minute = len([
            req_time for req_time in self.request_history[client_ip]
            if current_time - req_time < 60
        ])
        
        return {
            "remaining_per_minute": max(0, self.requests_per_minute - requests_last_minute),
            "remaining_per_hour": max(0, self.requests_per_hour - len(self.request_history[client_ip]))
        }


class DataEncryption:
    """Basic encryption utilities for sensitive data"""
    
    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """
        Mask API key for logging
        
        Args:
            api_key: API key to mask
            
        Returns:
            Masked API key
        """
        if len(api_key) <= 8:
            return "*" * len(api_key)
        
        visible_chars = 4
        return api_key[:visible_chars] + "*" * (len(api_key) - 2 * visible_chars) + api_key[-visible_chars:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for logging"""
        if "@" not in email:
            return "***"
        
        local, domain = email.split("@")
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1] if len(local) > 2 else "*" * len(local)
        return f"{masked_local}@{domain}"


# Global rate limiter instance
_rate_limiter = RateLimiter(
    requests_per_minute=100,
    requests_per_hour=500
)


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter
