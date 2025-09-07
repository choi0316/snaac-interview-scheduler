# 면접 스케줄링 시스템 테스트 가이드

## 개요

이 문서는 면접 스케줄링 시스템의 종합적인 테스트 가이드입니다. 시스템의 모든 구성요소에 대한 단위 테스트, 통합 테스트, 성능 테스트를 포함합니다.

## 테스트 구조

```
tests/
├── __init__.py                 # 테스트 모듈 초기화
├── conftest.py                 # pytest 설정 및 픽스처
├── test_models.py             # 핵심 모델 테스트
├── test_pdf_extractor.py      # PDF 추출 모듈 테스트
├── test_scheduler_engine.py   # 스케줄링 엔진 테스트
├── test_excel_generator.py    # Excel 생성 시스템 테스트
├── test_email_system.py       # 이메일 시스템 테스트
├── test_integration.py        # 통합 테스트
└── test_data/                 # 테스트용 데이터 파일
```

## 테스트 실행 방법

### 1. 기본 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 추가 테스트 도구 설치
pip install pytest pytest-cov pytest-html pytest-xdist psutil
```

### 2. 테스트 실행 옵션

#### 전체 테스트 실행
```bash
# 방법 1: 테스트 실행기 사용 (권장)
python run_tests.py

# 방법 2: pytest 직접 사용
python -m pytest tests/ -v
```

#### 특정 테스트 실행
```bash
# 단위 테스트만
python run_tests.py --fast

# 통합 테스트만
python run_tests.py --integration

# 성능 테스트만
python run_tests.py --performance

# 커버리지 포함
python run_tests.py --coverage
```

#### 개별 모듈 테스트
```bash
# 모델 테스트
python -m pytest tests/test_models.py -v

# PDF 추출 테스트
python -m pytest tests/test_pdf_extractor.py -v

# 스케줄링 엔진 테스트
python -m pytest tests/test_scheduler_engine.py -v

# Excel 생성 테스트
python -m pytest tests/test_excel_generator.py -v

# 이메일 시스템 테스트
python -m pytest tests/test_email_system.py -v

# 통합 테스트
python -m pytest tests/test_integration.py -v -s
```

### 3. 고급 테스트 옵션

#### 병렬 테스트 실행
```bash
# CPU 코어 수만큼 병렬 실행
python -m pytest tests/ -n auto

# 지정된 개수만큼 병렬 실행
python -m pytest tests/ -n 4
```

#### 특정 마커 테스트
```bash
# 느린 테스트만
python -m pytest tests/ -m slow

# 한국어 처리 테스트만
python -m pytest tests/ -m korean

# 성능 테스트만
python -m pytest tests/ -m performance

# 통합 테스트만
python -m pytest tests/ -m integration
```

#### 실패한 테스트만 재실행
```bash
python -m pytest tests/ --lf
```

#### 테스트 결과 HTML 리포트
```bash
python -m pytest tests/ --html=test_report.html --self-contained-html
```

## 테스트 범위 및 내용

### 1. 단위 테스트 (Unit Tests)

#### 핵심 모델 테스트 (`test_models.py`)
- **Team 모델**: 팀 데이터 생성, 불변성, 검증, 딕셔너리 변환
- **InterviewSlot 모델**: 면접 슬롯 생성, 시간 포맷팅
- **Schedule 모델**: 스케줄 생성, 유효성 검증, 제약조건 확인
- **InterviewConstraint 모델**: 제약조건 생성, 검증
- **SchedulingOption 모델**: 옵션 생성, 통계, 비교

#### PDF 추출 모듈 테스트 (`test_pdf_extractor.py`)
- **한국어 텍스트 검증**: 한국어 문자 감지 알고리즘
- **이메일 추출**: 다양한 형식의 이메일 패턴 매칭
- **전화번호 추출**: 한국 전화번호 형식 인식
- **시간 선호도 추출**: 자연어 시간 표현 파싱
- **면접관 회피 정보**: 자연어 처리를 통한 회피 의도 파악
- **대체 추출 전략**: pdfplumber → PyPDF2 → PyMuPDF 순서
- **성능 최적화**: 대용량 데이터 처리 시간 측정
- **인코딩 처리**: UTF-8, CP949 등 다양한 인코딩 지원

#### 스케줄링 엔진 테스트 (`test_scheduler_engine.py`)
- **제약조건 생성**: OR-Tools 제약조건 정의
- **5가지 최적화 전략**:
  - 첫 번째 선호도 우선
  - 시간 분산
  - 오전/오후 균형
  - 그룹 균형
  - 면접관 제약조건 우선
- **병렬 처리 성능**: 다중 전략 동시 실행
- **엣지 케이스 처리**: 빈 데이터, 제약조건 충돌
- **메모리 관리**: 메모리 누수 방지

#### Excel 생성 시스템 테스트 (`test_excel_generator.py`)
- **8-시트 구조 생성**: 
  - 메인 스케줄, Gmail/Outlook 메일머지
  - 옵션 비교, 그룹별 스케줄, 시간표
  - 이메일 템플릿, 분석 데이터
- **조건부 서식**: 시각적 데이터 표현
- **데이터 검증**: Excel 내 데이터 유효성
- **CSV 내보내기**: UTF-8, CP949 인코딩
- **성능 최적화**: 대용량 데이터 처리

#### 이메일 시스템 테스트 (`test_email_system.py`)
- **이메일 검증**:
  - 기본 형식 검증
  - DNS 검증 (MX 레코드)
  - 도메인 신뢰도 점수
  - 일회용 이메일 감지
  - 기관 도메인 인식
  - 오타 수정 제안
- **템플릿 시스템**:
  - Jinja2 템플릿 렌더링
  - 조건부 콘텐츠
  - 반복 콘텐츠
  - 다국어 지원
  - 변수 치환

### 2. 통합 테스트 (Integration Tests)

#### 전체 워크플로우 테스트 (`test_integration.py`)
- **완전한 파이프라인**: PDF → 스케줄링 → Excel → 이메일
- **오류 복구**: 각 단계에서의 예외 처리
- **대규모 데이터**: 70개 팀 실제 요구사항
- **제약조건 만족도**: 복잡한 제약조건 시나리오
- **성능 벤치마킹**: 실제 사용 환경 시뮬레이션
- **데이터 일관성**: 모듈 간 데이터 무결성

### 3. 성능 테스트 (Performance Tests)

#### 성능 기준점
- **PDF 추출**: 10초 이내
- **이메일 검증**: 100개 이메일 5초 이내
- **스케줄링**: 70개 팀 60초 이내
- **Excel 생성**: 30초 이내
- **메모리 사용량**: 500MB 이하

#### 부하 테스트
- **동시 사용자**: 여러 사용자 동시 접속
- **대용량 파일**: 큰 PDF 파일 처리
- **복잡한 제약조건**: 많은 제약조건이 있는 시나리오

## 테스트 환경 설정

### 환경 변수
```bash
# 테스트 모드 활성화
export TESTING=true

# 로그 레벨 설정
export LOG_LEVEL=DEBUG

# 테스트 데이터 경로
export TEST_DATA_PATH=tests/test_data
```

### 임시 파일 정리
테스트는 자동으로 임시 파일을 정리하지만, 수동 정리가 필요한 경우:

```bash
# 임시 테스트 파일 정리
rm -rf tests/temp_output/
rm -rf htmlcov/
rm tests/test.log
```

## 코드 커버리지

### 커버리지 실행
```bash
# HTML 리포트 포함
python -m pytest tests/ --cov=core --cov=excel --cov=email --cov=gui --cov-report=html

# 터미널 리포트
python -m pytest tests/ --cov=core --cov=excel --cov=email --cov=gui --cov-report=term

# 최소 커버리지 요구사항 (80%)
python -m pytest tests/ --cov=core --cov-fail-under=80
```

### 커버리지 목표
- **전체 커버리지**: 80% 이상
- **핵심 모듈**: 90% 이상
- **크리티컬 패스**: 95% 이상

## 테스트 데이터

### 샘플 데이터
테스트는 다음과 같은 샘플 데이터를 사용합니다:

- **팀 데이터**: 5-70개의 다양한 팀
- **면접관**: 4명의 면접관 (김교수, 이교수, 박교수, 최교수)
- **시간대**: 9:00-17:00 (8개 시간대)
- **제약조건**: 선호 시간, 면접관 회피

### 실제 데이터 테스트
실제 PDF 파일로 테스트하려면:

1. `tests/test_data/` 디렉토리에 PDF 파일 배치
2. `test_integration.py`에서 실제 파일 경로 지정
3. 테스트 실행

## 지속적 통합 (CI/CD)

### GitHub Actions 설정 예시
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: python run_tests.py --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 문제 해결

### 일반적인 문제들

#### 1. 의존성 설치 오류
```bash
# 의존성 강제 재설치
pip install -r requirements.txt --force-reinstall
```

#### 2. 테스트 실행 권한 오류
```bash
# 실행 권한 부여
chmod +x run_tests.py
```

#### 3. 메모리 부족 오류
```bash
# 병렬 실행 수 줄이기
python -m pytest tests/ -n 2

# 또는 순차 실행
python -m pytest tests/
```

#### 4. 한글 인코딩 오류
```bash
# 환경 변수 설정
export PYTHONIOENCODING=utf-8
export LANG=ko_KR.UTF-8
```

### 테스트 디버깅

#### 상세한 로그 확인
```bash
# 상세 로그 출력
python -m pytest tests/ -v -s --log-cli-level=DEBUG

# 특정 테스트 디버깅
python -m pytest tests/test_models.py::TestTeam::test_team_creation -v -s
```

#### pdb 디버거 사용
```python
import pdb; pdb.set_trace()  # 테스트 코드에 삽입
```

## 테스트 작성 가이드라인

### 1. 테스트 명명 규칙
- 테스트 함수: `test_기능명_시나리오`
- 테스트 클래스: `Test클래스명`
- 파일명: `test_모듈명.py`

### 2. 테스트 구조
```python
def test_feature_scenario():
    # Arrange (준비)
    data = create_test_data()
    
    # Act (실행)
    result = function_to_test(data)
    
    # Assert (검증)
    assert result == expected_value
```

### 3. 픽스처 활용
```python
@pytest.fixture
def sample_data():
    return create_sample_data()

def test_with_fixture(sample_data):
    result = process(sample_data)
    assert result.is_valid()
```

### 4. 모킹 사용
```python
@patch('module.external_function')
def test_with_mock(mock_func):
    mock_func.return_value = "mocked_result"
    result = function_under_test()
    assert result == "expected_result"
```

## 결론

이 테스트 시스템은 면접 스케줄링 시스템의 품질과 안정성을 보장합니다. 정기적인 테스트 실행을 통해 버그를 조기에 발견하고, 시스템의 신뢰성을 유지할 수 있습니다.

### 테스트 실행 체크리스트
- [ ] 전체 단위 테스트 통과
- [ ] 통합 테스트 통과  
- [ ] 성능 테스트 기준 만족
- [ ] 코드 커버리지 80% 이상
- [ ] 실제 데이터 테스트 완료
- [ ] 문서화 업데이트

### 배포 전 필수 테스트
```bash
# 전체 테스트 실행
python run_tests.py --coverage

# 성능 테스트 포함
python run_tests.py --performance

# 실제 데이터 테스트
python -m pytest tests/test_integration.py -v -s
```

모든 테스트가 통과하면 시스템이 프로덕션 배포 준비 상태입니다! 🚀