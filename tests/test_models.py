"""
핵심 모델 클래스들에 대한 단위 테스트
"""

import pytest
from datetime import datetime, time
from dataclasses import FrozenInstanceError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Team, Schedule, InterviewSlot, InterviewConstraint, SchedulingOption


class TestTeam:
    """팀 모델 테스트"""
    
    def test_team_creation(self):
        """팀 객체 생성 테스트"""
        team = Team(
            name="테스트팀",
            email="test@example.com",
            contact="010-1234-5678",
            preferred_times=["14:00", "15:00"],
            avoid_interviewers=["김교수"]
        )
        
        assert team.name == "테스트팀"
        assert team.email == "test@example.com"
        assert team.contact == "010-1234-5678"
        assert len(team.preferred_times) == 2
        assert len(team.avoid_interviewers) == 1
    
    def test_team_immutability(self):
        """팀 객체 불변성 테스트"""
        team = Team(
            name="테스트팀",
            email="test@example.com",
            contact="010-1234-5678"
        )
        
        with pytest.raises(FrozenInstanceError):
            team.name = "수정된팀"
    
    def test_team_validation(self):
        """팀 데이터 검증 테스트"""
        team = Team(
            name="테스트팀",
            email="invalid-email",
            contact="010-1234-5678"
        )
        
        errors = team.validate()
        assert len(errors) > 0
        assert any("이메일" in error for error in errors)
    
    def test_team_dict_conversion(self):
        """팀 객체 딕셔너리 변환 테스트"""
        team = Team(
            name="테스트팀",
            email="test@example.com",
            contact="010-1234-5678",
            preferred_times=["14:00", "15:00"]
        )
        
        team_dict = team.to_dict()
        assert team_dict["name"] == "테스트팀"
        assert team_dict["email"] == "test@example.com"
        assert isinstance(team_dict["preferred_times"], list)
        
        # 딕셔너리로부터 팀 객체 생성
        new_team = Team.from_dict(team_dict)
        assert new_team.name == team.name
        assert new_team.email == team.email


class TestInterviewSlot:
    """면접 슬롯 모델 테스트"""
    
    def test_slot_creation(self):
        """면접 슬롯 생성 테스트"""
        slot = InterviewSlot(
            date=datetime(2024, 1, 15),
            time=time(14, 0),
            interviewer="김교수",
            location="면접실1"
        )
        
        assert slot.date.year == 2024
        assert slot.time.hour == 14
        assert slot.interviewer == "김교수"
        assert slot.location == "면접실1"
    
    def test_slot_time_formatting(self):
        """시간 포맷팅 테스트"""
        slot = InterviewSlot(
            date=datetime(2024, 1, 15),
            time=time(14, 30),
            interviewer="김교수"
        )
        
        formatted = slot.format_time()
        assert "14:30" in formatted


class TestSchedule:
    """스케줄 모델 테스트"""
    
    def test_schedule_creation(self):
        """스케줄 생성 테스트"""
        team = Team(name="테스트팀", email="test@example.com", contact="010-1234-5678")
        slot = InterviewSlot(
            date=datetime(2024, 1, 15),
            time=time(14, 0),
            interviewer="김교수"
        )
        
        schedule = Schedule(team=team, slot=slot, priority_score=0.8)
        
        assert schedule.team.name == "테스트팀"
        assert schedule.slot.interviewer == "김교수"
        assert schedule.priority_score == 0.8
    
    def test_schedule_validation(self):
        """스케줄 검증 테스트"""
        team = Team(name="테스트팀", email="test@example.com", contact="010-1234-5678")
        slot = InterviewSlot(
            date=datetime(2024, 1, 15),
            time=time(14, 0),
            interviewer="김교수"
        )
        
        schedule = Schedule(team=team, slot=slot)
        assert schedule.is_valid()
        
        # 유효하지 않은 스케줄 (팀이 피하고자 하는 면접관)
        team_avoid = Team(
            name="테스트팀2", 
            email="test2@example.com", 
            contact="010-1234-5678",
            avoid_interviewers=["김교수"]
        )
        invalid_schedule = Schedule(team=team_avoid, slot=slot)
        assert not invalid_schedule.is_valid()


class TestInterviewConstraint:
    """면접 제약조건 모델 테스트"""
    
    def test_constraint_creation(self):
        """제약조건 생성 테스트"""
        constraint = InterviewConstraint(
            constraint_type="time_preference",
            target_value="14:00",
            weight=1.0,
            description="선호 시간대 제약"
        )
        
        assert constraint.constraint_type == "time_preference"
        assert constraint.target_value == "14:00"
        assert constraint.weight == 1.0
    
    def test_constraint_validation(self):
        """제약조건 검증 테스트"""
        # 유효한 제약조건
        valid_constraint = InterviewConstraint(
            constraint_type="time_preference",
            target_value="14:00",
            weight=0.5
        )
        assert valid_constraint.is_valid()
        
        # 유효하지 않은 제약조건 (잘못된 가중치)
        invalid_constraint = InterviewConstraint(
            constraint_type="time_preference",
            target_value="14:00",
            weight=2.0  # 1.0을 초과
        )
        assert not invalid_constraint.is_valid()


class TestSchedulingOption:
    """스케줄링 옵션 모델 테스트"""
    
    def test_option_creation(self):
        """스케줄링 옵션 생성 테스트"""
        team = Team(name="테스트팀", email="test@example.com", contact="010-1234-5678")
        slot = InterviewSlot(
            date=datetime(2024, 1, 15),
            time=time(14, 0),
            interviewer="김교수"
        )
        schedule = Schedule(team=team, slot=slot)
        
        option = SchedulingOption(
            name="최적화 옵션 1",
            description="첫 번째 선호도 우선",
            schedules=[schedule],
            optimization_score=0.85,
            constraint_violations=0
        )
        
        assert option.name == "최적화 옵션 1"
        assert len(option.schedules) == 1
        assert option.optimization_score == 0.85
        assert option.constraint_violations == 0
    
    def test_option_statistics(self):
        """옵션 통계 계산 테스트"""
        teams = [
            Team(name=f"팀{i}", email=f"team{i}@example.com", contact="010-1234-5678")
            for i in range(1, 6)
        ]
        slots = [
            InterviewSlot(
                date=datetime(2024, 1, 15),
                time=time(14 + i, 0),
                interviewer="김교수"
            )
            for i in range(5)
        ]
        schedules = [
            Schedule(team=team, slot=slot)
            for team, slot in zip(teams, slots)
        ]
        
        option = SchedulingOption(
            name="테스트 옵션",
            schedules=schedules,
            optimization_score=0.75
        )
        
        stats = option.get_statistics()
        assert stats["total_schedules"] == 5
        assert "average_score" in stats
        assert "time_distribution" in stats
    
    def test_option_comparison(self):
        """옵션 비교 테스트"""
        option1 = SchedulingOption(
            name="옵션 1",
            schedules=[],
            optimization_score=0.8,
            constraint_violations=1
        )
        
        option2 = SchedulingOption(
            name="옵션 2",
            schedules=[],
            optimization_score=0.7,
            constraint_violations=0
        )
        
        # 제약조건 위반이 더 중요하므로 option2가 더 좋음
        assert option2 > option1
        
        option3 = SchedulingOption(
            name="옵션 3",
            schedules=[],
            optimization_score=0.9,
            constraint_violations=0
        )
        
        # 제약조건 위반이 같으면 최적화 점수로 비교
        assert option3 > option2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])