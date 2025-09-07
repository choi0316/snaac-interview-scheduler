"""
도메인 모델 정의 - 면접 스케줄링 시스템의 핵심 엔티티들
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, time
from enum import Enum
import uuid


class InterviewGroup(Enum):
    """면접 조 구분"""
    A = "A조"
    B = "B조"


class ScheduleStatus(Enum):
    """스케줄 상태"""
    PENDING = "대기중"
    CONFIRMED = "확정"
    CONFLICT = "충돌"
    FAILED = "실패"


class ValidationStatus(Enum):
    """검증 상태"""
    VALID = "유효"
    INVALID = "무효"
    WARNING = "경고"
    ERROR = "오류"


@dataclass
class TeamMember:
    """팀원 정보"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_leader: bool = False


@dataclass
class Team:
    """팀 정보 모델"""
    team_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    team_name: str = ""
    members: List[TeamMember] = field(default_factory=list)
    primary_email: str = ""
    primary_phone: str = ""
    
    # 희망 면접 시간 (1, 2, 3순위)
    time_preferences: List[str] = field(default_factory=list)
    
    # 추가 정보
    notes: str = ""
    special_requirements: str = ""
    
    # 검증 상태
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_messages: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """초기화 후 검증 수행"""
        if not self.primary_email and self.members:
            # 리더의 이메일을 기본 이메일로 설정
            leader = next((m for m in self.members if m.is_leader), None)
            if leader and leader.email:
                self.primary_email = leader.email
    
    @property
    def leader_name(self) -> str:
        """팀 리더 이름 반환"""
        leader = next((m for m in self.members if m.is_leader), None)
        return leader.name if leader else ""
    
    @property
    def member_count(self) -> int:
        """팀원 수"""
        return len(self.members)
    
    def add_member(self, name: str, email: str = None, phone: str = None, is_leader: bool = False):
        """팀원 추가"""
        member = TeamMember(name=name, email=email, phone=phone, is_leader=is_leader)
        self.members.append(member)
        
        if is_leader:
            # 기존 리더의 리더십 제거
            for m in self.members[:-1]:  # 방금 추가한 멤버 제외
                m.is_leader = False
    
    def get_email_list(self) -> List[str]:
        """모든 유효한 이메일 주소 반환"""
        emails = []
        if self.primary_email:
            emails.append(self.primary_email)
        for member in self.members:
            if member.email and member.email not in emails:
                emails.append(member.email)
        return emails


@dataclass
class InterviewSlot:
    """면접 시간 슬롯"""
    slot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    date: str = ""  # YYYY-MM-DD 형식
    start_time: str = ""  # HH:MM 형식
    end_time: str = ""  # HH:MM 형식
    group: InterviewGroup = InterviewGroup.A
    room: str = ""
    zoom_link: Optional[str] = None
    max_capacity: int = 1  # 일반적으로 한 시간에 한 팀
    
    @property
    def time_range(self) -> str:
        """시간 범위 문자열 반환"""
        return f"{self.start_time}-{self.end_time}"
    
    @property
    def datetime_start(self) -> datetime:
        """시작 시간을 datetime 객체로 반환"""
        return datetime.strptime(f"{self.date} {self.start_time}", "%Y-%m-%d %H:%M")
    
    @property
    def datetime_end(self) -> datetime:
        """종료 시간을 datetime 객체로 반환"""
        return datetime.strptime(f"{self.date} {self.end_time}", "%Y-%m-%d %H:%M")


@dataclass
class Schedule:
    """면접 스케줄"""
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    team: Team = field(default_factory=Team)
    interview_slot: InterviewSlot = field(default_factory=InterviewSlot)
    
    # 스케줄 상태
    status: ScheduleStatus = ScheduleStatus.PENDING
    
    # 희망 순위 (1순위 만족: 1, 2순위: 2, 3순위: 3, 기타: 0)
    preference_rank: int = 0
    
    # 추가 정보
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def team_name(self) -> str:
        """팀명"""
        return self.team.team_name
    
    @property
    def leader_name(self) -> str:
        """팀 리더명"""
        return self.team.leader_name
    
    @property
    def interview_date(self) -> str:
        """면접 날짜"""
        return self.interview_slot.date
    
    @property
    def interview_time(self) -> str:
        """면접 시간"""
        return self.interview_slot.time_range
    
    @property
    def interview_group(self) -> str:
        """면접 조"""
        return self.interview_slot.group.value
    
    def to_dict(self) -> Dict:
        """딕셔너리 형태로 변환 (엑셀 출력용)"""
        return {
            'team_name': self.team_name,
            'leader_name': self.leader_name,
            'email': self.team.primary_email,
            'phone': self.team.primary_phone,
            'interview_date': self.interview_date,
            'interview_time': self.interview_time,
            'interview_group': self.interview_group,
            'interview_room': self.interview_slot.room,
            'zoom_link': self.interview_slot.zoom_link or "",
            'status': self.status.value,
            'preference_rank': self.preference_rank,
            'notes': self.notes
        }


@dataclass
class InterviewConstraint:
    """면접 제약 조건"""
    constraint_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    constraint_type: str = ""  # "interviewer_avoidance", "time_restriction", etc.
    
    # 면접관별 기피 팀 (면접관ID: [팀ID 리스트])
    interviewer_avoidance: Dict[str, List[str]] = field(default_factory=dict)
    
    # 면접관별 담당 조
    interviewer_groups: Dict[str, str] = field(default_factory=dict)
    
    # 시간대별 제한사항
    time_restrictions: Dict[str, List[str]] = field(default_factory=dict)
    
    # 특별 요구사항
    special_requirements: Dict[str, str] = field(default_factory=dict)
    
    # 최대/최소 제약
    max_teams_per_slot: int = 1
    min_break_between_interviews: int = 15  # 분 단위
    
    def add_interviewer_avoidance(self, interviewer_id: str, avoided_teams: List[str]):
        """면접관 기피 팀 추가"""
        self.interviewer_avoidance[interviewer_id] = avoided_teams
    
    def add_interviewer_group(self, interviewer_id: str, group: str):
        """면접관 담당 조 설정"""
        self.interviewer_groups[interviewer_id] = group
    
    def get_avoided_teams_for_group(self, group: str) -> List[str]:
        """특정 조에서 기피해야 할 팀 목록 반환"""
        avoided_teams = []
        for interviewer_id, teams in self.interviewer_avoidance.items():
            if self.interviewer_groups.get(interviewer_id) == group:
                avoided_teams.extend(teams)
        return list(set(avoided_teams))  # 중복 제거


@dataclass 
class SchedulingOption:
    """스케줄링 옵션 (5가지 전략)"""
    option_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    option_name: str = ""
    strategy_type: str = ""  # "first_preference", "time_distribution", etc.
    schedules: List[Schedule] = field(default_factory=list)
    
    # 성과 지표
    first_choice_satisfaction: float = 0.0  # 1순위 만족률
    time_distribution_score: float = 0.0    # 시간 분산 점수
    constraint_violations: int = 0           # 제약 위반 수
    group_balance_score: float = 0.0        # 조별 균형 점수
    
    # 메타데이터
    generated_at: datetime = field(default_factory=datetime.now)
    generation_time: float = 0.0  # 생성 소요 시간 (초)
    
    @property
    def total_teams(self) -> int:
        """총 팀 수"""
        return len(self.schedules)
    
    @property
    def group_distribution(self) -> Dict[str, int]:
        """조별 팀 분포"""
        distribution = {"A조": 0, "B조": 0}
        for schedule in self.schedules:
            distribution[schedule.interview_group] += 1
        return distribution
    
    def calculate_satisfaction_metrics(self):
        """만족도 지표 계산"""
        if not self.schedules:
            return
        
        # 1순위 만족률 계산
        first_choice_count = sum(1 for s in self.schedules if s.preference_rank == 1)
        self.first_choice_satisfaction = (first_choice_count / len(self.schedules)) * 100
        
        # 조별 균형 점수 (50:50에 가까울수록 높은 점수)
        dist = self.group_distribution
        total = sum(dist.values())
        if total > 0:
            balance_ratio = min(dist.values()) / max(dist.values())
            self.group_balance_score = balance_ratio * 100


@dataclass
class EmailValidationResult:
    """이메일 검증 결과"""
    email: str = ""
    is_valid: bool = False
    validation_type: str = ""  # "format", "domain", "mx_record"
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    is_institutional: bool = False
    domain: str = ""
    
    def add_issue(self, issue: str):
        """문제점 추가"""
        self.issues.append(issue)
        self.is_valid = False
    
    def add_suggestion(self, suggestion: str):
        """수정 제안 추가"""
        self.suggestions.append(suggestion)


@dataclass
class SchedulingResult:
    """스케줄링 결과 전체"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    options: List[SchedulingOption] = field(default_factory=list)
    selected_option: Optional[SchedulingOption] = None
    
    # 입력 데이터
    teams: List[Team] = field(default_factory=list)
    constraints: InterviewConstraint = field(default_factory=InterviewConstraint)
    
    # 검증 결과
    email_validations: List[EmailValidationResult] = field(default_factory=list)
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    total_processing_time: float = 0.0  # 총 처리 시간
    
    @property
    def best_option(self) -> Optional[SchedulingOption]:
        """최적 옵션 추천"""
        if not self.options:
            return None
        
        # 종합 점수 계산 (1순위 만족률 40% + 조별 균형 30% + 제약 위반 -30%)
        best_score = -1
        best_option = None
        
        for option in self.options:
            score = (
                option.first_choice_satisfaction * 0.4 +
                option.group_balance_score * 0.3 -
                option.constraint_violations * 0.3
            )
            
            if score > best_score:
                best_score = score
                best_option = option
        
        return best_option