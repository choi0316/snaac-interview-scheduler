"""
공모전 2차 면접 스케줄링 시스템

70개 팀의 면접 일정을 자동으로 배치하고 
메일 발송이 용이한 엑셀 파일을 생성하는 시스템입니다.

Features:
- PDF 데이터 추출 (한글 지원)
- 제약 조건 기반 최적화 스케줄링
- 8개 시트 엑셀 생성 (메일머지 최적화)
- 이메일 검증 및 템플릿 시스템
- 실시간 웹 인터페이스
"""

__version__ = "1.0.0"
__author__ = "Interview Scheduler Team"
__email__ = "admin@interview-scheduler.com"

from .core.models import Team, Schedule, InterviewConstraint
from .core.pdf_extractor import PDFExtractor
from .core.scheduler_engine import InterviewScheduler
from .excel.excel_generator import ExcelGenerator
from .email.email_validator import EmailValidator

__all__ = [
    "Team",
    "Schedule", 
    "InterviewConstraint",
    "PDFExtractor",
    "InterviewScheduler",
    "ExcelGenerator",
    "EmailValidator",
]