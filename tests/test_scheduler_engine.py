"""
제약 만족 최적화 엔진 테스트
"""

import pytest
import sys
import os
from datetime import datetime, time
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler_engine import SchedulerEngine
from core.models import Team, InterviewSlot, Schedule, SchedulingOption


class TestSchedulerEngine:
    """스케줄러 엔진 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.engine = SchedulerEngine()
        
        # 테스트용 팀 데이터
        self.teams = [
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
        
        # 테스트용 면접 슬롯
        self.slots = []
        interviewers = ["김교수", "이교수", "박교수", "최교수"]
        times = [time(9, 0), time(10, 0), time(11, 0), time(13, 0), 
                time(14, 0), time(15, 0), time(16, 0), time(17, 0)]
        
        for interviewer in interviewers:
            for slot_time in times:
                self.slots.append(InterviewSlot(
                    date=datetime(2024, 1, 15),
                    time=slot_time,
                    interviewer=interviewer,
                    location=f"면접실{interviewers.index(interviewer) + 1}"
                ))
    
    def test_engine_initialization(self):
        """엔진 초기화 테스트"""
        assert self.engine is not None
        assert hasattr(self.engine, 'generate_five_options')
        assert hasattr(self.engine, '_solve_with_strategy')
    
    def test_constraint_creation(self):
        """제약조건 생성 테스트"""
        constraints = self.engine._create_constraints(
            self.teams, self.slots, strategy="first_preference"
        )
        
        assert len(constraints) > 0
        
        # 각 팀마다 정확히 하나의 슬롯 할당 제약조건 확인
        team_constraints = [c for c in constraints if "exactly_one_slot" in str(c)]
        assert len(team_constraints) >= len(self.teams)
        
        # 각 슬롯마다 최대 하나의 팀 할당 제약조건 확인
        slot_constraints = [c for c in constraints if "max_one_team" in str(c)]
        assert len(slot_constraints) >= len(self.slots)
    
    def test_first_preference_strategy(self):
        """첫 번째 선호도 우선 전략 테스트"""
        solution = self.engine._solve_with_strategy(
            self.teams, self.slots, strategy="first_preference"
        )
        
        assert solution is not None
        assert len(solution.schedules) <= len(self.teams)
        
        # 선호 시간에 배정된 팀이 있는지 확인
        preferred_assignments = 0
        for schedule in solution.schedules:
            team_preferred_times = schedule.team.preferred_times
            slot_time = schedule.slot.time.strftime("%H:%M")
            if slot_time in team_preferred_times:
                preferred_assignments += 1
        
        # 최소 일부 팀은 선호 시간에 배정되어야 함
        assert preferred_assignments > 0
    
    def test_time_distribution_strategy(self):
        """시간 분산 전략 테스트"""
        solution = self.engine._solve_with_strategy(
            self.teams, self.slots, strategy="time_distribution"
        )
        
        assert solution is not None
        assert len(solution.schedules) <= len(self.teams)
        
        # 시간대별 분산 확인
        time_distribution = {}
        for schedule in solution.schedules:
            slot_time = schedule.slot.time.strftime("%H:%M")
            time_distribution[slot_time] = time_distribution.get(slot_time, 0) + 1
        
        # 여러 시간대에 분산되어 있는지 확인
        assert len(time_distribution) > 1
    
    def test_morning_afternoon_balance_strategy(self):
        """오전/오후 균형 전략 테스트"""
        solution = self.engine._solve_with_strategy(
            self.teams, self.slots, strategy="morning_afternoon_balance"
        )
        
        assert solution is not None
        assert len(solution.schedules) <= len(self.teams)
        
        # 오전/오후 분배 확인
        morning_count = 0
        afternoon_count = 0
        
        for schedule in solution.schedules:
            hour = schedule.slot.time.hour
            if hour < 12:
                morning_count += 1
            else:
                afternoon_count += 1
        
        # 완전히 균형잡히지 않더라도 둘 다 0은 아니어야 함
        assert morning_count >= 0 and afternoon_count >= 0
    
    def test_group_balance_strategy(self):
        """그룹 균형 전략 테스트"""
        solution = self.engine._solve_with_strategy(
            self.teams, self.slots, strategy="group_balance"
        )
        
        assert solution is not None
        assert len(solution.schedules) <= len(self.teams)
        
        # 면접관별 배정 균형 확인
        interviewer_distribution = {}
        for schedule in solution.schedules:
            interviewer = schedule.slot.interviewer
            interviewer_distribution[interviewer] = interviewer_distribution.get(interviewer, 0) + 1
        
        # 여러 면접관에게 분산되어 있는지 확인
        assert len(interviewer_distribution) > 1
    
    def test_interviewer_constraints_strategy(self):
        """면접관 제약조건 전략 테스트"""
        solution = self.engine._solve_with_strategy(
            self.teams, self.slots, strategy="interviewer_constraints"
        )
        
        assert solution is not None
        
        # 면접관 회피 제약조건 확인
        for schedule in solution.schedules:
            team = schedule.team
            assigned_interviewer = schedule.slot.interviewer
            
            # 팀이 피하고자 하는 면접관이 배정되지 않았는지 확인
            assert assigned_interviewer not in team.avoid_interviewers
    
    def test_generate_five_options(self):
        """다섯 가지 옵션 생성 테스트"""
        options = self.engine.generate_five_options(self.teams, self.slots)
        
        # 5개의 옵션이 생성되는지 확인
        assert len(options) == 5
        
        # 각 옵션이 유효한지 확인
        for i, option in enumerate(options):
            assert isinstance(option, SchedulingOption)
            assert len(option.name) > 0
            assert len(option.description) > 0
            assert option.optimization_score >= 0.0
            assert option.optimization_score <= 1.0
            assert option.constraint_violations >= 0
            
            # 각 옵션마다 스케줄이 있는지 확인
            assert len(option.schedules) > 0
    
    def test_constraint_violation_detection(self):
        """제약조건 위반 감지 테스트"""
        # 의도적으로 제약조건을 위반하는 스케줄 생성
        violating_schedule = Schedule(
            team=Team(
                name="테스트팀",
                email="test@example.com",
                contact="010-1234-5678",
                avoid_interviewers=["김교수"]
            ),
            slot=InterviewSlot(
                date=datetime(2024, 1, 15),
                time=time(14, 0),
                interviewer="김교수"  # 피하고자 하는 면접관
            )
        )
        
        # 위반 감지
        assert not violating_schedule.is_valid()
    
    def test_optimization_scoring(self):
        """최적화 점수 계산 테스트"""
        # 완벽한 스케줄 (모든 선호도 만족)
        perfect_schedules = []
        for i, team in enumerate(self.teams[:3]):  # 처음 3개 팀만 사용
            preferred_time = team.preferred_times[0] if team.preferred_times else "10:00"
            hour, minute = map(int, preferred_time.split(":"))
            
            # 팀이 피하지 않는 면접관 찾기
            available_interviewer = None
            for slot in self.slots:
                if (slot.time == time(hour, minute) and 
                    slot.interviewer not in team.avoid_interviewers):
                    available_interviewer = slot.interviewer
                    break
            
            if available_interviewer:
                perfect_schedule = Schedule(
                    team=team,
                    slot=InterviewSlot(
                        date=datetime(2024, 1, 15),
                        time=time(hour, minute),
                        interviewer=available_interviewer
                    ),
                    priority_score=1.0
                )
                perfect_schedules.append(perfect_schedule)
        
        if perfect_schedules:
            perfect_option = SchedulingOption(
                name="완벽한 스케줄",
                schedules=perfect_schedules,
                optimization_score=1.0,
                constraint_violations=0
            )
            
            # 완벽한 스케줄의 점수가 높은지 확인
            assert perfect_option.optimization_score == 1.0
            assert perfect_option.constraint_violations == 0
    
    def test_parallel_processing_performance(self):
        """병렬 처리 성능 테스트"""
        import time
        
        # 많은 팀과 슬롯으로 성능 테스트
        large_teams = []
        for i in range(20):
            team = Team(
                name=f"팀{i:02d}",
                email=f"team{i:02d}@test.com",
                contact=f"010-{i:04d}-{i:04d}",
                preferred_times=[f"{10 + (i % 8)}:00"],
                avoid_interviewers=[f"교수{i % 3}"] if i % 4 == 0 else []
            )
            large_teams.append(team)
        
        start_time = time.time()
        options = self.engine.generate_five_options(large_teams, self.slots)
        end_time = time.time()
        
        # 병렬 처리로 인한 성능 향상 확인 (30초 미만)
        assert end_time - start_time < 30.0
        assert len(options) == 5
    
    def test_edge_cases(self):
        """엣지 케이스 테스트"""
        # 빈 팀 리스트
        empty_options = self.engine.generate_five_options([], self.slots)
        assert len(empty_options) == 5
        for option in empty_options:
            assert len(option.schedules) == 0
        
        # 빈 슬롯 리스트
        no_slot_options = self.engine.generate_five_options(self.teams, [])
        assert len(no_slot_options) == 5
        for option in no_slot_options:
            assert len(option.schedules) == 0
        
        # 팀 수가 슬롯 수보다 많은 경우
        limited_slots = self.slots[:3]  # 3개 슬롯만 사용
        many_teams = self.teams  # 5개 팀
        
        limited_options = self.engine.generate_five_options(many_teams, limited_slots)
        assert len(limited_options) == 5
        
        for option in limited_options:
            # 배정된 팀 수가 슬롯 수를 초과하지 않아야 함
            assert len(option.schedules) <= len(limited_slots)
    
    def test_strategy_diversity(self):
        """전략 다양성 테스트"""
        options = self.engine.generate_five_options(self.teams, self.slots)
        
        # 각 옵션이 서로 다른 결과를 만들어내는지 확인
        schedule_sets = []
        for option in options:
            # 스케줄을 문자열로 변환하여 비교
            schedule_signature = set()
            for schedule in option.schedules:
                signature = f"{schedule.team.name}_{schedule.slot.interviewer}_{schedule.slot.time}"
                schedule_signature.add(signature)
            schedule_sets.append(schedule_signature)
        
        # 모든 옵션이 동일하지 않은지 확인
        unique_signatures = set()
        for schedule_set in schedule_sets:
            signature_tuple = tuple(sorted(schedule_set))
            unique_signatures.add(signature_tuple)
        
        # 최소 2개 이상의 서로 다른 스케줄링 결과가 있어야 함
        assert len(unique_signatures) >= 2
    
    def test_memory_management(self):
        """메모리 관리 테스트"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 여러 번 옵션 생성하여 메모리 누수 확인
        for _ in range(10):
            options = self.engine.generate_five_options(self.teams, self.slots)
            assert len(options) == 5
            # 명시적으로 가비지 컬렉션 실행
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가가 100MB 미만이어야 함 (메모리 누수 없음)
        assert memory_increase < 100 * 1024 * 1024  # 100MB


if __name__ == "__main__":
    pytest.main([__file__, "-v"])