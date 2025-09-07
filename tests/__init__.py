"""
종합적인 면접 일정 관리 시스템 테스트 모듈

이 모듈은 다음 영역에 대한 포괄적인 테스트를 제공합니다:
- PDF 데이터 추출 (한국어 텍스트 지원)
- 제약 만족 최적화 엔진
- Excel 생성 시스템
- 이메일 검증 및 템플릿 시스템
- Streamlit GUI 인터페이스
- 통합 워크플로우
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEMP_OUTPUT_DIR = Path(__file__).parent / "temp_output"

# Create test directories if they don't exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEMP_OUTPUT_DIR.mkdir(exist_ok=True)

# Test fixtures and utilities
__all__ = [
    "TEST_DATA_DIR",
    "TEMP_OUTPUT_DIR"
]