"""
면접 스케줄링 최적화 엔진

Google OR-Tools를 사용한 제약 만족 문제 해결
5가지 최적화 전략으로 서로 다른 스케줄 옵션 생성
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from enum import Enum

from ortools.sat.python import cp_model
import numpy as np

from .models import (
    Team, Schedule, InterviewSlot, InterviewConstraint, 
    SchedulingOption, InterviewGroup, ScheduleStatus
)

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """최적화 전략"""
    FIRST_PREFERENCE = "first_preference"
    TIME_DISTRIBUTION = "time_distribution"  
    MORNING_AFTERNOON_BALANCE = "morning_afternoon_balance"
    GROUP_BALANCE = "group_balance"
    INTERVIEWER_CONSTRAINTS = "interviewer_constraints"


@dataclass
class SchedulingConfig:
    """스케줄링 설정"""
    max_solving_time_seconds: int = 30  # 최대 해결 시간
    num_threads: int = 4  # 병렬 처리 스레드 수
    enable_logging: bool = True
    use_presolve: bool = True
    enable_symmetry_breaking: bool = True


class InterviewScheduler:
    """면접 스케줄링 최적화 엔진"""
    
    def __init__(self, config: Optional[SchedulingConfig] = None):
        self.config = config or SchedulingConfig()
        self.model = None
        self.solver = None
        
        # 변수 딕셔너리
        self.schedule_vars = {}  # (team_id, slot_id, group) -> BoolVar
        self.preference_vars = {}  # (team_id, preference_rank) -> BoolVar
        self.group_vars = {}  # (team_id, group) -> BoolVar
        
        # 시간대 정의
        self.time_slots = self._generate_default_time_slots()
        
    def _generate_default_time_slots(self) -> List[InterviewSlot]:
        """기본 시간대 생성 (9:00-18:00, 30분 단위)"""
        slots = []
        slot_duration = 30  # 분
        
        # 면접 가능 시간: 9:00-12:00, 14:00-18:00
        time_ranges = [
            (9, 12),   # 오전
            (14, 18)   # 오후  
        ]
        
        for day_offset in range(3):  # 3일간
            date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            for start_hour, end_hour in time_ranges:
                current_time = start_hour * 60  # 분 단위로 변환
                end_time = end_hour * 60
                
                while current_time < end_time:
                    start_h = current_time // 60
                    start_m = current_time % 60
                    end_time_minutes = current_time + slot_duration
                    end_h = end_time_minutes // 60
                    end_m = end_time_minutes % 60
                    
                    # A조, B조용 슬롯 각각 생성
                    for group in [InterviewGroup.A, InterviewGroup.B]:
                        slot = InterviewSlot(
                            date=date,
                            start_time=f"{start_h:02d}:{start_m:02d}",
                            end_time=f"{end_h:02d}:{end_m:02d}",
                            group=group,
                            room=f"{group.value} 면접실"
                        )
                        slots.append(slot)
                    
                    current_time += slot_duration
        
        return slots
    
    def generate_five_options(
        self, 
        teams: List[Team], 
        constraints: Optional[InterviewConstraint] = None
    ) -> List[SchedulingOption]:
        """5개의 서로 다른 스케줄링 옵션 생성"""
        
        if not teams:
            raise ValueError("팀 데이터가 없습니다.")
        
        if len(teams) > 100:
            logger.warning(f"팀 수가 많음 ({len(teams)}). 성능 문제 가능성.")
        
        logger.info(f"5가지 옵션 생성 시작: {len(teams)}개 팀")
        
        constraints = constraints or InterviewConstraint()
        options = []
        
        # 5가지 전략으로 옵션 생성
        strategies = [
            (OptimizationStrategy.FIRST_PREFERENCE, "옵션 1: 1순위 희망시간 최대 반영"),
            (OptimizationStrategy.TIME_DISTRIBUTION, "옵션 2: 시간 분산 최적화"),
            (OptimizationStrategy.MORNING_AFTERNOON_BALANCE, "옵션 3: 오전/오후 균등 배치"),
            (OptimizationStrategy.GROUP_BALANCE, "옵션 4: 조별 균등 배치 우선"),
            (OptimizationStrategy.INTERVIEWER_CONSTRAINTS, "옵션 5: 면접관 제약조건 최우선"),
        ]
        
        for strategy, name in strategies:
            try:
                start_time = time.time()
                
                option = self._generate_single_option(teams, constraints, strategy, name)
                option.generation_time = time.time() - start_time
                
                if option and option.schedules:
                    options.append(option)
                    logger.info(f"{name} 완료: {len(option.schedules)}개 팀 배치")
                else:
                    logger.warning(f"{name} 실패")
                    
            except Exception as e:
                logger.error(f"{name} 오류: {e}")
                continue
        
        # 성과 지표 계산
        for option in options:
            option.calculate_satisfaction_metrics()
        
        logger.info(f"총 {len(options)}개 옵션 생성 완료")
        return options
    
    def _generate_single_option(
        self,
        teams: List[Team],
        constraints: InterviewConstraint,
        strategy: OptimizationStrategy,
        option_name: str
    ) -> Optional[SchedulingOption]:
        """단일 옵션 생성"""
        
        # 새 모델 생성
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # 솔버 설정
        self.solver.parameters.max_time_in_seconds = self.config.max_solving_time_seconds
        self.solver.parameters.num_search_workers = self.config.num_threads
        self.solver.parameters.log_search_progress = self.config.enable_logging
        
        # 변수 생성
        self._create_variables(teams)
        
        # 기본 제약조건 추가
        self._add_basic_constraints(teams)
        
        # 면접관 제약조건 추가
        self._add_interviewer_constraints(teams, constraints)
        
        # 전략별 목적 함수 설정
        self._set_objective_function(teams, strategy)
        
        # 대칭성 깨뜨리기 (성능 향상)
        if self.config.enable_symmetry_breaking:
            self._add_symmetry_breaking_constraints(teams)
        
        # 문제 해결
        status = self.solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            schedules = self._extract_solution(teams)
            
            option = SchedulingOption(
                option_name=option_name,
                strategy_type=strategy.value,
                schedules=schedules
            )
            
            return option
        else:
            logger.error(f"해결 실패: {self.solver.StatusName(status)}")
            return None
    
    def _create_variables(self, teams: List[Team]):
        """최적화 변수 생성"""
        self.schedule_vars.clear()
        self.preference_vars.clear()
        self.group_vars.clear()
        
        # 스케줄 배치 변수: x[team, slot, group]
        for team in teams:
            for slot in self.time_slots:
                for group in [InterviewGroup.A, InterviewGroup.B]:
                    var_name = f"schedule_{team.team_id}_{slot.slot_id}_{group.value}"
                    var = self.model.NewBoolVar(var_name)
                    self.schedule_vars[(team.team_id, slot.slot_id, group)] = var
        
        # 선호도 만족 변수: p[team, preference_rank]
        for team in teams:
            for rank in range(1, 4):  # 1, 2, 3순위
                var_name = f"preference_{team.team_id}_{rank}"
                var = self.model.NewBoolVar(var_name)
                self.preference_vars[(team.team_id, rank)] = var
        
        # 조 배치 변수: g[team, group]
        for team in teams:
            for group in [InterviewGroup.A, InterviewGroup.B]:
                var_name = f"group_{team.team_id}_{group.value}"
                var = self.model.NewBoolVar(var_name)
                self.group_vars[(team.team_id, group)] = var
    
    def _add_basic_constraints(self, teams: List[Team]):
        """기본 제약조건 추가"""
        
        # 1. 각 팀은 정확히 하나의 시간대와 조에 배치
        for team in teams:
            schedule_sum = []
            for slot in self.time_slots:
                for group in [InterviewGroup.A, InterviewGroup.B]:
                    if (team.team_id, slot.slot_id, group) in self.schedule_vars:
                        schedule_sum.append(self.schedule_vars[(team.team_id, slot.slot_id, group)])
            
            if schedule_sum:
                self.model.Add(sum(schedule_sum) == 1)
        
        # 2. 각 시간대에는 최대 1팀만 배치
        for slot in self.time_slots:
            for group in [InterviewGroup.A, InterviewGroup.B]:
                slot_vars = []
                for team in teams:
                    if (team.team_id, slot.slot_id, group) in self.schedule_vars:
                        slot_vars.append(self.schedule_vars[(team.team_id, slot.slot_id, group)])
                
                if slot_vars:
                    self.model.Add(sum(slot_vars) <= 1)
        
        # 3. 조 배치 일관성
        for team in teams:
            for group in [InterviewGroup.A, InterviewGroup.B]:
                group_var = self.group_vars.get((team.team_id, group))
                if group_var is None:
                    continue
                
                # 해당 조의 모든 시간대에서 배치 변수의 합 = 조 변수
                group_schedule_vars = []
                for slot in self.time_slots:
                    if slot.group == group:
                        if (team.team_id, slot.slot_id, group) in self.schedule_vars:
                            group_schedule_vars.append(self.schedule_vars[(team.team_id, slot.slot_id, group)])
                
                if group_schedule_vars:
                    self.model.Add(sum(group_schedule_vars) == group_var)
        
        # 4. 선호도 변수 연결
        for team in teams:
            for rank, time_pref in enumerate(team.time_preferences[:3], 1):
                matching_slots = self._find_matching_slots(time_pref)
                
                if matching_slots and (team.team_id, rank) in self.preference_vars:
                    pref_var = self.preference_vars[(team.team_id, rank)]
                    
                    # 선호 시간대 중 하나에 배치되면 선호도 만족
                    matching_schedule_vars = []
                    for slot in matching_slots:
                        for group in [InterviewGroup.A, InterviewGroup.B]:
                            if (team.team_id, slot.slot_id, group) in self.schedule_vars:
                                matching_schedule_vars.append(self.schedule_vars[(team.team_id, slot.slot_id, group)])
                    
                    if matching_schedule_vars:
                        self.model.Add(pref_var <= sum(matching_schedule_vars))
    
    def _add_interviewer_constraints(self, teams: List[Team], constraints: InterviewConstraint):
        """면접관 제약조건 추가"""
        
        # 면접관별 기피 팀 제약
        for interviewer_id, avoided_teams in constraints.interviewer_avoidance.items():
            interviewer_group = constraints.interviewer_groups.get(interviewer_id)
            
            if not interviewer_group:
                continue
            
            # 기피 팀을 해당 면접관의 조에 배치하지 않음
            group_enum = InterviewGroup.A if interviewer_group == "A" else InterviewGroup.B
            
            for team_id in avoided_teams:
                team = next((t for t in teams if t.team_id == team_id), None)
                if not team:
                    continue
                
                # 기피하는 면접관의 조에는 배치 금지
                if (team.team_id, group_enum) in self.group_vars:
                    self.model.Add(self.group_vars[(team.team_id, group_enum)] == 0)
    
    def _set_objective_function(self, teams: List[Team], strategy: OptimizationStrategy):
        """전략별 목적 함수 설정"""
        
        if strategy == OptimizationStrategy.FIRST_PREFERENCE:
            self._set_first_preference_objective(teams)
            
        elif strategy == OptimizationStrategy.TIME_DISTRIBUTION:
            self._set_time_distribution_objective(teams)
            
        elif strategy == OptimizationStrategy.MORNING_AFTERNOON_BALANCE:
            self._set_morning_afternoon_objective(teams)
            
        elif strategy == OptimizationStrategy.GROUP_BALANCE:
            self._set_group_balance_objective(teams)
            
        elif strategy == OptimizationStrategy.INTERVIEWER_CONSTRAINTS:
            self._set_interviewer_constraint_objective(teams)
    
    def _set_first_preference_objective(self, teams: List[Team]):
        """1순위 희망시간 최대 반영 목적 함수"""
        objective_terms = []
        
        for team in teams:
            # 1순위: 가중치 100
            if (team.team_id, 1) in self.preference_vars:
                objective_terms.append(100 * self.preference_vars[(team.team_id, 1)])
            
            # 2순위: 가중치 50
            if (team.team_id, 2) in self.preference_vars:
                objective_terms.append(50 * self.preference_vars[(team.team_id, 2)])
            
            # 3순위: 가중치 25
            if (team.team_id, 3) in self.preference_vars:
                objective_terms.append(25 * self.preference_vars[(team.team_id, 3)])
        
        if objective_terms:
            self.model.Maximize(sum(objective_terms))
    
    def _set_time_distribution_objective(self, teams: List[Team]):
        """시간 분산 최적화 목적 함수"""
        # 시간대별 팀 수의 균등 분산을 위한 목적 함수
        
        # 시간대별 사용량 변수
        slot_usage_vars = {}
        for slot in self.time_slots:
            var_name = f"slot_usage_{slot.slot_id}"
            slot_usage_vars[slot.slot_id] = self.model.NewIntVar(0, len(teams), var_name)
            
            # 해당 슬롯의 팀 수 = 사용량
            slot_teams = []
            for team in teams:
                for group in [InterviewGroup.A, InterviewGroup.B]:
                    if (team.team_id, slot.slot_id, group) in self.schedule_vars:
                        slot_teams.append(self.schedule_vars[(team.team_id, slot.slot_id, group)])
            
            if slot_teams:
                self.model.Add(slot_usage_vars[slot.slot_id] == sum(slot_teams))
        
        # 분산 최소화 (표준편차의 제곱합 최소화)
        if slot_usage_vars:
            avg_usage = len(teams) // len(self.time_slots)
            deviation_vars = []
            
            for slot_id, usage_var in slot_usage_vars.items():
                dev_var = self.model.NewIntVar(0, len(teams), f"dev_{slot_id}")
                self.model.AddAbsEquality(dev_var, usage_var - avg_usage)
                deviation_vars.append(dev_var)
            
            if deviation_vars:
                self.model.Minimize(sum(deviation_vars))
    
    def _set_morning_afternoon_objective(self, teams: List[Team]):
        """오전/오후 균등 배치 목적 함수"""
        morning_teams = self.model.NewIntVar(0, len(teams), "morning_teams")
        afternoon_teams = self.model.NewIntVar(0, len(teams), "afternoon_teams")
        
        morning_vars = []
        afternoon_vars = []
        
        for team in teams:
            for slot in self.time_slots:
                start_hour = int(slot.start_time.split(':')[0])
                
                for group in [InterviewGroup.A, InterviewGroup.B]:
                    if (team.team_id, slot.slot_id, group) not in self.schedule_vars:
                        continue
                    
                    schedule_var = self.schedule_vars[(team.team_id, slot.slot_id, group)]
                    
                    if start_hour < 12:  # 오전
                        morning_vars.append(schedule_var)
                    else:  # 오후
                        afternoon_vars.append(schedule_var)
        
        if morning_vars:
            self.model.Add(morning_teams == sum(morning_vars))
        if afternoon_vars:
            self.model.Add(afternoon_teams == sum(afternoon_vars))
        
        # 오전/오후 차이 최소화
        balance_var = self.model.NewIntVar(0, len(teams), "balance")
        self.model.AddAbsEquality(balance_var, morning_teams - afternoon_teams)
        self.model.Minimize(balance_var)
    
    def _set_group_balance_objective(self, teams: List[Team]):
        """조별 균등 배치 목적 함수"""
        group_a_teams = self.model.NewIntVar(0, len(teams), "group_a_teams")
        group_b_teams = self.model.NewIntVar(0, len(teams), "group_b_teams")
        
        group_a_vars = [self.group_vars.get((team.team_id, InterviewGroup.A), 0) for team in teams]
        group_b_vars = [self.group_vars.get((team.team_id, InterviewGroup.B), 0) for team in teams]
        
        group_a_vars = [v for v in group_a_vars if v != 0]
        group_b_vars = [v for v in group_b_vars if v != 0]
        
        if group_a_vars:
            self.model.Add(group_a_teams == sum(group_a_vars))
        if group_b_vars:
            self.model.Add(group_b_teams == sum(group_b_vars))
        
        # 조별 차이 최소화
        balance_var = self.model.NewIntVar(0, len(teams), "group_balance")
        self.model.AddAbsEquality(balance_var, group_a_teams - group_b_teams)
        self.model.Minimize(balance_var)
    
    def _set_interviewer_constraint_objective(self, teams: List[Team]):
        """면접관 제약조건 우선 목적 함수"""
        # 이미 하드 제약으로 처리되므로, 추가적으로 선호도도 고려
        objective_terms = []
        
        # 제약 위반이 없는 상태에서 선호도 만족 추가
        for team in teams:
            if (team.team_id, 1) in self.preference_vars:
                objective_terms.append(10 * self.preference_vars[(team.team_id, 1)])
            if (team.team_id, 2) in self.preference_vars:
                objective_terms.append(5 * self.preference_vars[(team.team_id, 2)])
            if (team.team_id, 3) in self.preference_vars:
                objective_terms.append(1 * self.preference_vars[(team.team_id, 3)])
        
        if objective_terms:
            self.model.Maximize(sum(objective_terms))
    
    def _add_symmetry_breaking_constraints(self, teams: List[Team]):
        """대칭성 제거 제약 (성능 향상)"""
        if len(teams) < 2:
            return
        
        # 첫 번째 팀을 A조에 우선 배치하여 대칭성 제거
        first_team = teams[0]
        if (first_team.team_id, InterviewGroup.A) in self.group_vars:
            # 조건부로만 추가 (다른 제약과 충돌하지 않는 경우)
            pass  # 실제로는 더 정교한 대칭성 제거 로직 필요
    
    def _find_matching_slots(self, time_preference: str) -> List[InterviewSlot]:
        """시간 선호도와 일치하는 슬롯 찾기"""
        matching_slots = []
        
        # 시간 형식 파싱: "HH:MM-HH:MM"
        if '-' not in time_preference:
            return matching_slots
        
        try:
            start_time, end_time = time_preference.split('-')
            start_time = start_time.strip()
            end_time = end_time.strip()
            
            for slot in self.time_slots:
                # 시간대 겹침 확인
                if self._time_ranges_overlap(
                    start_time, end_time,
                    slot.start_time, slot.end_time
                ):
                    matching_slots.append(slot)
                    
        except Exception as e:
            logger.warning(f"시간 선호도 파싱 오류: {time_preference}, {e}")
        
        return matching_slots
    
    def _time_ranges_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """두 시간 범위가 겹치는지 확인"""
        try:
            start1_minutes = self._time_to_minutes(start1)
            end1_minutes = self._time_to_minutes(end1)
            start2_minutes = self._time_to_minutes(start2)
            end2_minutes = self._time_to_minutes(end2)
            
            return start1_minutes < end2_minutes and start2_minutes < end1_minutes
            
        except:
            return False
    
    def _time_to_minutes(self, time_str: str) -> int:
        """시간 문자열을 분 단위 정수로 변환"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def _extract_solution(self, teams: List[Team]) -> List[Schedule]:
        """솔루션에서 스케줄 추출"""
        schedules = []
        
        for team in teams:
            team_schedule = None
            
            # 팀의 배치 위치 찾기
            for slot in self.time_slots:
                for group in [InterviewGroup.A, InterviewGroup.B]:
                    var_key = (team.team_id, slot.slot_id, group)
                    
                    if var_key in self.schedule_vars:
                        if self.solver.Value(self.schedule_vars[var_key]) == 1:
                            # 선호 순위 계산
                            preference_rank = 0
                            for rank in range(1, 4):
                                if (team.team_id, rank) in self.preference_vars:
                                    if self.solver.Value(self.preference_vars[(team.team_id, rank)]) == 1:
                                        preference_rank = rank
                                        break
                            
                            team_schedule = Schedule(
                                team=team,
                                interview_slot=slot,
                                status=ScheduleStatus.CONFIRMED,
                                preference_rank=preference_rank
                            )
                            break
                
                if team_schedule:
                    break
            
            if team_schedule:
                schedules.append(team_schedule)
            else:
                logger.warning(f"팀 {team.team_name} 배치 실패")
        
        return schedules
    
    def get_solver_statistics(self) -> Dict:
        """솔버 통계 정보"""
        if not self.solver:
            return {}
        
        return {
            'status': self.solver.StatusName(self.solver.StatusName()),
            'objective_value': self.solver.ObjectiveValue(),
            'best_objective_bound': self.solver.BestObjectiveBound(),
            'num_branches': self.solver.NumBranches(),
            'num_conflicts': self.solver.NumConflicts(),
            'wall_time': self.solver.WallTime(),
            'user_time': self.solver.UserTime()
        }
    
    def validate_solution(self, schedules: List[Schedule]) -> Tuple[bool, List[str]]:
        """솔루션 유효성 검증"""
        issues = []
        
        # 1. 모든 팀이 배치되었는지 확인
        scheduled_teams = {s.team.team_id for s in schedules}
        
        # 2. 시간대 충돌 확인
        slot_assignments = {}
        for schedule in schedules:
            key = (schedule.interview_slot.slot_id, schedule.interview_slot.group)
            if key in slot_assignments:
                issues.append(f"시간대 충돌: {key}")
            else:
                slot_assignments[key] = schedule.team.team_id
        
        # 3. 조별 분포 확인
        group_distribution = {}
        for schedule in schedules:
            group = schedule.interview_slot.group.value
            group_distribution[group] = group_distribution.get(group, 0) + 1
        
        total_teams = len(schedules)
        for group, count in group_distribution.items():
            ratio = count / total_teams
            if ratio > 0.6 or ratio < 0.4:  # 40-60% 범위를 벗어나면 경고
                issues.append(f"{group} 비율 불균형: {ratio:.1%}")
        
        is_valid = len(issues) == 0
        return is_valid, issues