"""
이메일 검증 및 템플릿 관리 모듈
"""

from .email_validator import EmailValidator
from .template_manager import EmailTemplateManager

__all__ = [
    "EmailValidator",
    "EmailTemplateManager"
]