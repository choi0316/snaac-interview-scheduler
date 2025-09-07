"""
pytest 설정 및 공통 픽스처
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, time

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models import Team, InterviewSlot, Schedule, SchedulingOption


@pytest.fixture(scope="session")
def test_data_dir():
    """테스트 데이터 디렉토리 픽스처"""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_output_dir():
    """임시 출력 디렉토리 픽스처"""
    temp_dir = Path(__file__).parent / "temp_output"
    temp_dir.mkdir(exist_ok=True)
    
    yield temp_dir
    
    # 테스트 완료 후 정리
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_teams():
    """샘플 팀 데이터 픽스처"""
    return [
        Team(
            name="한국대학교팀",
            email="korea@university.ac.kr",
            contact="010-1234-5678",
            preferred_times=["14:00", "15:00"],
            avoid_interviewers=["김교수"]
        ),
        Team(
            name="테크스타트업",
            email="contact@techstartup.co.kr",
            contact="010-9876-5432",
            preferred_times=["10:00", "11:00"],
            avoid_interviewers=[]
        ),
        Team(
            name="창업동아리",
            email="startup@club.ac.kr",
            contact="010-5555-6666",
            preferred_times=["16:00", "17:00"],
            avoid_interviewers=["이교수"]
        ),
        Team(
            name="혁신팀",
            email="innovation@team.com",
            contact="010-7777-8888",
            preferred_times=["09:00", "10:00"],
            avoid_interviewers=[]
        ),
        Team(
            name="알고리즘팀",
            email="algo@team.com",
            contact="010-9999-0000",
            preferred_times=["13:00", "14:00"],
            avoid_interviewers=["김교수", "박교수"]
        )
    ]


@pytest.fixture
def sample_interview_slots():
    """샘플 면접 슬롯 픽스처"""
    slots = []
    interviewers = ["김교수", "이교수", "박교수", "최교수"]
    times = [
        time(9, 0), time(10, 0), time(11, 0), time(13, 0),
        time(14, 0), time(15, 0), time(16, 0), time(17, 0)
    ]
    
    for interviewer in interviewers:
        for slot_time in times:
            slots.append(InterviewSlot(
                date=datetime(2024, 1, 15),
                time=slot_time,
                interviewer=interviewer,
                location=f"면접실{interviewers.index(interviewer) + 1}"
            ))
    
    return slots


@pytest.fixture
def sample_schedules(sample_teams, sample_interview_slots):
    """샘플 스케줄 픽스처"""
    return [
        Schedule(
            team=sample_teams[0],
            slot=sample_interview_slots[20],  # 김교수가 아닌 슬롯
            priority_score=0.9
        ),
        Schedule(
            team=sample_teams[1],
            slot=sample_interview_slots[8],   # 10:00 슬롯
            priority_score=1.0
        ),
        Schedule(
            team=sample_teams[2],
            slot=sample_interview_slots[30],  # 이교수가 아닌 16:00 슬롯
            priority_score=0.8
        )
    ]


@pytest.fixture
def sample_scheduling_options(sample_schedules):
    """샘플 스케줄링 옵션 픽스처"""
    return [
        SchedulingOption(
            name="첫 번째 선호도 우선",
            description="팀의 첫 번째 선호 시간을 우선시합니다",
            schedules=sample_schedules,
            optimization_score=0.85,
            constraint_violations=0
        ),
        SchedulingOption(
            name="시간 분산",
            description="면접 시간을 고르게 분산시킵니다",
            schedules=sample_schedules,
            optimization_score=0.75,
            constraint_violations=1
        ),
        SchedulingOption(
            name="그룹 균형",
            description="면접관별 배정을 균등하게 합니다",
            schedules=sample_schedules,
            optimization_score=0.80,
            constraint_violations=0
        ),
        SchedulingOption(
            name="오전/오후 균형",
            description="오전과 오후 면접을 균등하게 배분합니다",
            schedules=sample_schedules,
            optimization_score=0.70,
            constraint_violations=2
        ),
        SchedulingOption(
            name="제약조건 우선",
            description="모든 제약조건을 최대한 만족시킵니다",
            schedules=sample_schedules,
            optimization_score=0.90,
            constraint_violations=0
        )
    ]


@pytest.fixture
def temp_pdf_file():
    """임시 PDF 파일 픽스처"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        pdf_path = tmp_file.name
        # 실제 PDF 내용은 테스트에서 모킹됨
        tmp_file.write(b"Mock PDF content")
    
    yield pdf_path
    
    # 정리
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


@pytest.fixture
def temp_excel_file():
    """임시 Excel 파일 픽스처"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        excel_path = tmp_file.name
    
    yield excel_path
    
    # 정리
    if os.path.exists(excel_path):
        os.unlink(excel_path)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """테스트 환경 설정 (모든 테스트에 자동 적용)"""
    # 테스트 시작 전 환경 변수 설정
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # 테스트 후 정리
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
    if 'LOG_LEVEL' in os.environ:
        del os.environ['LOG_LEVEL']


@pytest.fixture
def large_team_dataset():
    """대규모 팀 데이터셋 픽스처 (성능 테스트용)"""
    teams = []
    for i in range(70):  # 실제 요구사항에 맞는 70개 팀
        team = Team(
            name=f"팀{i+1:02d}호",
            email=f"team{i+1:02d}@test{(i % 10) + 1}.com",
            contact=f"010-{i+1:04d}-{i+1:04d}",
            preferred_times=[
                f"{9 + (i % 9)}:00", 
                f"{10 + (i % 9)}:00"
            ],
            avoid_interviewers=[f"교수{(i % 4) + 1}"] if i % 5 == 0 else []
        )
        teams.append(team)
    
    return teams


@pytest.fixture(scope="session")
def performance_baseline():
    """성능 기준선 픽스처"""
    return {
        "pdf_extraction_max_time": 10.0,      # PDF 추출 최대 시간 (초)
        "email_validation_max_time": 5.0,     # 이메일 검증 최대 시간 (초)  
        "scheduling_max_time": 60.0,          # 스케줄링 최대 시간 (초)
        "excel_generation_max_time": 30.0,    # Excel 생성 최대 시간 (초)
        "max_memory_usage_mb": 500,           # 최대 메모리 사용량 (MB)
        "large_dataset_teams": 70,            # 대규모 데이터셋 팀 수
        "expected_accuracy": 0.95             # 예상 정확도
    }


# pytest 설정
def pytest_configure(config):
    """pytest 설정"""
    # 커스텀 마커 등록
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "korean: mark test as Korean text processing test"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정"""
    # 통합 테스트와 성능 테스트 마커 자동 추가
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.nodeid or "large" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "korean" in item.nodeid or "한국" in str(item):
            item.add_marker(pytest.mark.korean)


def pytest_runtest_setup(item):
    """테스트 실행 전 설정"""
    # 느린 테스트 건너뛰기 (필요시)
    if item.get_closest_marker("slow"):
        if item.config.getoption("--fast"):
            pytest.skip("Skipping slow test in fast mode")


def pytest_addoption(parser):
    """pytest 명령행 옵션 추가"""
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help="Run fast tests only, skip slow tests"
    )
    parser.addoption(
        "--integration",
        action="store_true", 
        default=False,
        help="Run integration tests only"
    )
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="Run performance tests only"
    )


# 테스트 결과 요약 출력
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """테스트 완료 후 요약 정보 출력"""
    if hasattr(terminalreporter, 'stats'):
        passed = len(terminalreporter.stats.get('passed', []))
        failed = len(terminalreporter.stats.get('failed', []))
        skipped = len(terminalreporter.stats.get('skipped', []))
        
        print(f"\n{'='*60}")
        print(f"면접 스케줄링 시스템 테스트 결과 요약")
        print(f"{'='*60}")
        print(f"통과: {passed}개")
        print(f"실패: {failed}개") 
        print(f"건너뜀: {skipped}개")
        print(f"종료 상태: {'성공' if exitstatus == 0 else '실패'}")
        print(f"{'='*60}")
        
        if exitstatus == 0:
            print(f"🎉 모든 테스트가 성공적으로 완료되었습니다!")
            print(f"🚀 면접 스케줄링 시스템이 프로덕션 준비 상태입니다.")
        else:
            print(f"❌ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")