"""
고급 면접 스케줄링 시스템
- A/B 두 조 동시 면접 지원
- 연속 배치 (중간 공백 최소화)
- 충돌 감지 및 미배치 팀 상세 보고
"""

import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

@dataclass
class Team:
    """팀 정보"""
    name: str
    available_slots: List[str]  # ["9/12 19:00-19:45", ...]
    email: str = ""
    phone: str = ""
    assigned_slot: Optional[str] = None
    assigned_group: Optional[str] = None  # "A" or "B"
    conflict_reason: Optional[str] = None  # 배치 실패 이유

@dataclass
class TimeSlot:
    """시간 슬롯 (A/B 그룹 지원)"""
    date: str
    time: str
    full_slot: str  # "9/12 19:00-19:45"
    group_a_team: Optional[str] = None
    group_b_team: Optional[str] = None
    
    def is_full(self) -> bool:
        """두 그룹 모두 차있는지 확인"""
        return self.group_a_team is not None and self.group_b_team is not None
    
    def has_space(self) -> bool:
        """빈 자리가 있는지 확인"""
        return self.group_a_team is None or self.group_b_team is None
    
    def get_available_group(self) -> Optional[str]:
        """사용 가능한 그룹 반환"""
        if self.group_a_team is None:
            return "A"
        elif self.group_b_team is None:
            return "B"
        return None

class AdvancedInterviewScheduler:
    """고급 면접 스케줄링 클래스"""
    
    def __init__(self, groups_per_slot: int = 2):
        """
        Args:
            groups_per_slot: 동시 면접 그룹 수 (기본값: 2 - A/B조)
        """
        self.groups_per_slot = groups_per_slot
        self.all_slots = self._generate_all_slots()
        self.teams: List[Team] = []
        self.time_slots: Dict[str, TimeSlot] = {}
        self._initialize_time_slots()
        
    def _generate_all_slots(self) -> List[str]:
        """모든 가능한 시간 슬롯 생성"""
        slots = []
        
        # 금요일 (9/12): 19:00~22:00
        friday_times = [
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ]
        for time in friday_times:
            slots.append(f"9/12 {time}")
        
        # 토요일 (9/13): 10:00~22:00
        saturday_times = [
            "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
            "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
            "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ]
        for time in saturday_times:
            slots.append(f"9/13 {time}")
        
        # 일요일 (9/14): 10:00~22:00
        sunday_times = saturday_times  # 같은 시간대
        for time in sunday_times:
            slots.append(f"9/14 {time}")
        
        return slots
    
    def _initialize_time_slots(self):
        """TimeSlot 객체 초기화"""
        for slot in self.all_slots:
            date, time = slot.split(" ", 1)
            self.time_slots[slot] = TimeSlot(date=date, time=time, full_slot=slot)
    
    def add_team(self, name: str, available_slots: List[str], 
                 email: str = "", phone: str = ""):
        """팀 추가"""
        team = Team(name=name, available_slots=available_slots, 
                   email=email, phone=phone)
        self.teams.append(team)
    
    def schedule_interviews_continuous(self) -> Dict[str, Dict[str, str]]:
        """
        연속 배치 알고리즘 - 중간 공백 최소화
        각 팀은 단 하나의 시간대에만 배치됨
        
        Returns:
            {"A": {slot: team_name}, "B": {slot: team_name}}
        """
        # 모든 time_slots 초기화 (중요!)
        for slot in self.time_slots:
            self.time_slots[slot].group_a_team = None
            self.time_slots[slot].group_b_team = None
        
        # 팀 상태 초기화
        for team in self.teams:
            team.assigned_slot = None
            team.assigned_group = None
            team.conflict_reason = None
        
        # 팀을 가능한 슬롯 수로 정렬 (제약이 많은 팀부터)
        sorted_teams = sorted(self.teams, key=lambda t: len(t.available_slots))
        
        # 연속 배치를 위한 슬롯 우선순위 설정
        slot_priority = self._get_continuous_slot_priority()
        
        for team in sorted_teams:
            # 이미 배치된 팀은 건너뛰기
            if team.assigned_slot:
                continue
                
            assigned = False
            
            # 우선순위에 따라 슬롯 시도 (한 팀은 한 시간대만!)
            for slot in slot_priority:
                if slot in team.available_slots:
                    time_slot = self.time_slots[slot]
                    
                    if time_slot.has_space():
                        group = time_slot.get_available_group()
                        if group == "A":
                            time_slot.group_a_team = team.name
                        else:
                            time_slot.group_b_team = team.name
                        
                        team.assigned_slot = slot
                        team.assigned_group = group
                        assigned = True
                        break  # 한 팀은 한 시간대만 배치하고 종료
            
            if not assigned:
                # 배치 실패 이유 분석
                team.conflict_reason = self._analyze_conflict(team)
        
        return self._get_schedule_by_group()
    
    def _get_continuous_slot_priority(self) -> List[str]:
        """
        연속 배치를 위한 슬롯 우선순위 반환
        날짜별로 시간순으로 정렬
        """
        priority_slots = []
        
        # 날짜별로 그룹화
        for date in ["9/12", "9/13", "9/14"]:
            date_slots = [s for s in self.all_slots if s.startswith(date)]
            priority_slots.extend(date_slots)
        
        return priority_slots
    
    def _analyze_conflict(self, team: Team) -> str:
        """팀이 배치되지 못한 이유 분석"""
        if not team.available_slots:
            return "가능한 시간대가 없음"
        
        # 모든 선택 가능 시간이 이미 꽉 찬 경우
        all_full = True
        for slot in team.available_slots:
            if slot in self.time_slots:
                if self.time_slots[slot].has_space():
                    all_full = False
                    break
        
        if all_full:
            conflicting_teams = []
            for slot in team.available_slots:
                if slot in self.time_slots:
                    ts = self.time_slots[slot]
                    if ts.group_a_team:
                        conflicting_teams.append(f"{ts.group_a_team}(A조)")
                    if ts.group_b_team:
                        conflicting_teams.append(f"{ts.group_b_team}(B조)")
            
            unique_teams = list(set(conflicting_teams))
            return f"모든 가능 시간대가 이미 배정됨. 충돌 팀: {', '.join(unique_teams[:3])}"
        
        return "알 수 없는 이유"
    
    def _get_schedule_by_group(self) -> Dict[str, Dict[str, str]]:
        """그룹별 스케줄 반환"""
        schedule = {"A": {}, "B": {}}
        
        for slot, time_slot in self.time_slots.items():
            if time_slot.group_a_team:
                schedule["A"][slot] = time_slot.group_a_team
            if time_slot.group_b_team:
                schedule["B"][slot] = time_slot.group_b_team
        
        return schedule
    
    def get_unassigned_teams_detail(self) -> List[Dict]:
        """배치되지 않은 팀의 상세 정보 반환"""
        unassigned = []
        for team in self.teams:
            if not team.assigned_slot:
                unassigned.append({
                    "팀명": team.name,
                    "이메일": team.email,
                    "전화번호": team.phone,
                    "가능 시간": ", ".join(team.available_slots[:3]) + ("..." if len(team.available_slots) > 3 else ""),
                    "미배치 이유": team.conflict_reason or "알 수 없음"
                })
        return unassigned
    
    def schedule_interviews_max_teams(self) -> Dict[str, Dict[str, str]]:
        """
        최대 팀 배치 알고리즘 - 가능한 많은 팀을 배치
        
        Returns:
            {"A": {slot: team_name}, "B": {slot: team_name}}
        """
        # 모든 time_slots 초기화
        for slot in self.time_slots:
            self.time_slots[slot].group_a_team = None
            self.time_slots[slot].group_b_team = None
        
        # 팀 상태 초기화
        for team in self.teams:
            team.assigned_slot = None
            team.assigned_group = None
            team.conflict_reason = None
        
        # 팀을 가능한 슬롯 수로 정렬 (제약이 많은 팀부터)
        sorted_teams = sorted(self.teams, key=lambda t: len(t.available_slots))
        
        for team in sorted_teams:
            # 이미 배치된 팀은 건너뛰기
            if team.assigned_slot:
                continue
                
            assigned = False
            
            # 모든 가능한 슬롯 시도
            for slot in team.available_slots:
                if slot in self.time_slots:
                    time_slot = self.time_slots[slot]
                    
                    if time_slot.has_space():
                        group = time_slot.get_available_group()
                        if group == "A":
                            time_slot.group_a_team = team.name
                        else:
                            time_slot.group_b_team = team.name
                        
                        team.assigned_slot = slot
                        team.assigned_group = group
                        assigned = True
                        break  # 한 팀은 한 시간대만 배치
            
            if not assigned:
                # 배치 실패 이유 분석
                team.conflict_reason = self._analyze_conflict(team)
        
        return self._get_schedule_by_group()
    
    def schedule_interviews_balanced(self) -> Dict[str, Dict[str, str]]:
        """
        균형 배치 알고리즘 - A/B조 균형있게 배치
        
        Returns:
            {"A": {slot: team_name}, "B": {slot: team_name}}
        """
        # 모든 time_slots 초기화
        for slot in self.time_slots:
            self.time_slots[slot].group_a_team = None
            self.time_slots[slot].group_b_team = None
        
        # 팀 상태 초기화
        for team in self.teams:
            team.assigned_slot = None
            team.assigned_group = None
            team.conflict_reason = None
        
        # 팀을 가능한 슬롯 수로 정렬 (제약이 많은 팀부터)
        sorted_teams = sorted(self.teams, key=lambda t: len(t.available_slots))
        
        # A/B 그룹 균형 카운터
        a_count = 0
        b_count = 0
        
        for team in sorted_teams:
            # 이미 배치된 팀은 건너뛰기
            if team.assigned_slot:
                continue
                
            assigned = False
            prefer_group = "A" if a_count <= b_count else "B"
            
            # 선호 그룹으로 먼저 시도
            for slot in team.available_slots:
                if slot in self.time_slots:
                    time_slot = self.time_slots[slot]
                    
                    if prefer_group == "A" and time_slot.group_a_team is None:
                        time_slot.group_a_team = team.name
                        team.assigned_slot = slot
                        team.assigned_group = "A"
                        a_count += 1
                        assigned = True
                        break
                    elif prefer_group == "B" and time_slot.group_b_team is None:
                        time_slot.group_b_team = team.name
                        team.assigned_slot = slot
                        team.assigned_group = "B"
                        b_count += 1
                        assigned = True
                        break
            
            # 선호 그룹으로 배치 실패시 다른 그룹으로 시도
            if not assigned:
                other_group = "B" if prefer_group == "A" else "A"
                for slot in team.available_slots:
                    if slot in self.time_slots:
                        time_slot = self.time_slots[slot]
                        
                        if other_group == "A" and time_slot.group_a_team is None:
                            time_slot.group_a_team = team.name
                            team.assigned_slot = slot
                            team.assigned_group = "A"
                            a_count += 1
                            assigned = True
                            break
                        elif other_group == "B" and time_slot.group_b_team is None:
                            time_slot.group_b_team = team.name
                            team.assigned_slot = slot
                            team.assigned_group = "B"
                            b_count += 1
                            assigned = True
                            break
            
            if not assigned:
                # 배치 실패 이유 분석
                team.conflict_reason = self._analyze_conflict(team)
        
        return self._get_schedule_by_group()
    
    def optimize_schedule(self, max_iterations: int = 100) -> Dict[str, Dict[str, str]]:
        """
        최적화된 연속 스케줄 찾기
        여러 번 시도하여 가장 많은 팀을 배치하고 공백을 최소화
        """
        best_schedule = {}
        best_count = 0
        best_gap_score = float('inf')
        best_team_assignments = []  # 최적 배치 상태 저장
        
        for iteration in range(max_iterations):
            # 팀 순서 섞기
            random.shuffle(self.teams)
            
            # 연속 배치 시도 (자동으로 초기화됨)
            schedule = self.schedule_interviews_continuous()
            
            # 배치된 팀 수 계산
            assigned_count = len([t for t in self.teams if t.assigned_slot])
            
            # 공백 점수 계산 (낮을수록 좋음)
            gap_score = self._calculate_gap_score()
            
            # 더 많은 팀을 배치했거나, 같은 수를 배치했지만 공백이 적은 경우
            if (assigned_count > best_count) or \
               (assigned_count == best_count and gap_score < best_gap_score):
                # 깊은 복사로 최적 상태 저장
                best_schedule = {"A": dict(schedule["A"]), "B": dict(schedule["B"])}
                best_count = assigned_count
                best_gap_score = gap_score
                
                # 팀 배치 상태도 저장
                best_team_assignments = [(t.name, t.assigned_slot, t.assigned_group, t.conflict_reason) 
                                        for t in self.teams]
                
                # 모든 팀이 배치되고 공백이 없으면 종료
                if best_count == len(self.teams) and best_gap_score == 0:
                    break
        
        # 최적 상태로 복원
        if best_team_assignments:
            # time_slots 재구성
            for slot in self.time_slots:
                self.time_slots[slot].group_a_team = None
                self.time_slots[slot].group_b_team = None
            
            for slot, team_name in best_schedule["A"].items():
                self.time_slots[slot].group_a_team = team_name
            for slot, team_name in best_schedule["B"].items():
                self.time_slots[slot].group_b_team = team_name
            
            # 팀 상태 복원
            for team in self.teams:
                for name, slot, group, reason in best_team_assignments:
                    if team.name == name:
                        team.assigned_slot = slot
                        team.assigned_group = group
                        team.conflict_reason = reason
                        break
        
        return best_schedule
    
    def _calculate_gap_score(self) -> int:
        """스케줄의 공백 점수 계산 (연속성 평가)"""
        gap_score = 0
        
        for group in ["A", "B"]:
            for date in ["9/12", "9/13", "9/14"]:
                date_slots = [s for s in self.all_slots if s.startswith(date)]
                
                in_session = False
                for slot in date_slots:
                    time_slot = self.time_slots[slot]
                    
                    if group == "A":
                        has_team = time_slot.group_a_team is not None
                    else:
                        has_team = time_slot.group_b_team is not None
                    
                    if has_team:
                        in_session = True
                    elif in_session:
                        # 세션 중간에 공백이 있으면 페널티
                        gap_score += 1
        
        return gap_score
    
    def get_schedule_statistics(self) -> Dict:
        """스케줄링 통계 반환"""
        total_teams = len(self.teams)
        assigned_teams = len([t for t in self.teams if t.assigned_slot])
        unassigned_teams = total_teams - assigned_teams
        
        # 그룹별 통계
        group_a_count = len([t for t in self.teams if t.assigned_group == "A"])
        group_b_count = len([t for t in self.teams if t.assigned_group == "B"])
        
        # 날짜별 배치 수
        date_stats = {"9/12": {"A": 0, "B": 0}, 
                     "9/13": {"A": 0, "B": 0}, 
                     "9/14": {"A": 0, "B": 0}}
        
        for slot, time_slot in self.time_slots.items():
            date = slot.split()[0]
            if time_slot.group_a_team:
                date_stats[date]["A"] += 1
            if time_slot.group_b_team:
                date_stats[date]["B"] += 1
        
        # 시간대별 사용률
        total_capacity = len(self.all_slots) * 2  # A/B 두 그룹
        used_capacity = group_a_count + group_b_count
        
        return {
            "총 팀 수": total_teams,
            "배치된 팀": assigned_teams,
            "미배치 팀": unassigned_teams,
            "배치율": f"{(assigned_teams/total_teams*100):.1f}%" if total_teams > 0 else "0%",
            "A조 배치": group_a_count,
            "B조 배치": group_b_count,
            "금요일 배치": f"A조:{date_stats['9/12']['A']}, B조:{date_stats['9/12']['B']}",
            "토요일 배치": f"A조:{date_stats['9/13']['A']}, B조:{date_stats['9/13']['B']}",
            "일요일 배치": f"A조:{date_stats['9/14']['A']}, B조:{date_stats['9/14']['B']}",
            "전체 수용률": f"{(used_capacity/total_capacity*100):.1f}%",
            "공백 점수": self._calculate_gap_score()
        }
    
    def export_schedule(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        스케줄을 DataFrame으로 변환
        
        Returns:
            (A조 DataFrame, B조 DataFrame)
        """
        data_a = []
        data_b = []
        
        for slot in sorted(self.time_slots.keys()):
            time_slot = self.time_slots[slot]
            date, time = slot.split(" ", 1)
            
            # A조
            if time_slot.group_a_team:
                team = next((t for t in self.teams if t.name == time_slot.group_a_team), None)
                data_a.append({
                    "날짜": date,
                    "시간": time,
                    "팀명": time_slot.group_a_team,
                    "이메일": team.email if team else "",
                    "전화번호": team.phone if team else ""
                })
            
            # B조
            if time_slot.group_b_team:
                team = next((t for t in self.teams if t.name == time_slot.group_b_team), None)
                data_b.append({
                    "날짜": date,
                    "시간": time,
                    "팀명": time_slot.group_b_team,
                    "이메일": team.email if team else "",
                    "전화번호": team.phone if team else ""
                })
        
        return pd.DataFrame(data_a), pd.DataFrame(data_b)
    
    def export_combined_schedule(self) -> pd.DataFrame:
        """통합 스케줄 DataFrame 반환"""
        data = []
        
        for slot in sorted(self.time_slots.keys()):
            time_slot = self.time_slots[slot]
            date, time = slot.split(" ", 1)
            
            row = {
                "날짜": date,
                "시간": time,
                "A조": "",
                "A조 이메일": "",
                "A조 전화": "",
                "B조": "",
                "B조 이메일": "",
                "B조 전화": ""
            }
            
            # A조 정보
            if time_slot.group_a_team:
                team = next((t for t in self.teams if t.name == time_slot.group_a_team), None)
                if team:
                    row["A조"] = team.name
                    row["A조 이메일"] = team.email
                    row["A조 전화"] = team.phone
            
            # B조 정보
            if time_slot.group_b_team:
                team = next((t for t in self.teams if t.name == time_slot.group_b_team), None)
                if team:
                    row["B조"] = team.name
                    row["B조 이메일"] = team.email
                    row["B조 전화"] = team.phone
            
            # 둘 중 하나라도 배치되어 있으면 추가
            if row["A조"] or row["B조"]:
                data.append(row)
        
        return pd.DataFrame(data)
    
    def calculate_gaps(self) -> List[Dict[str, str]]:
        """스케줄에서 빈 시간대 (갭) 계산"""
        gaps = []
        
        # 모든 시간 슬롯을 순서대로 확인
        all_slots = sorted(self.time_slots.keys())
        
        for slot in all_slots:
            time_slot = self.time_slots[slot]
            
            # 빈 자리가 있는 시간대 찾기
            if time_slot.has_space():
                gap_info = {
                    '시간대': slot,
                    '상태': '부분 빈 시간대'
                }
                
                if time_slot.group_a_team is None and time_slot.group_b_team is None:
                    gap_info['상태'] = '완전 빈 시간대'
                elif time_slot.group_a_team is None:
                    gap_info['상태'] = 'A조 빈 자리'
                elif time_slot.group_b_team is None:
                    gap_info['상태'] = 'B조 빈 자리'
                    
                gaps.append(gap_info)
        
        return gaps

def test_advanced_scheduler():
    """고급 스케줄러 테스트"""
    scheduler = AdvancedInterviewScheduler()
    
    # 테스트 데이터 추가 (많은 팀)
    test_teams = [
        ("필리데이", ["9/12 19:00-19:45", "9/12 19:45-20:30", "9/12 20:30-21:15"]),
        ("아뮤즈8", ["9/12 19:00-19:45", "9/13 10:00-10:45", "9/13 10:45-11:30"]),
        ("팀C", ["9/12 19:00-19:45", "9/12 19:45-20:30"]),
        ("팀D", ["9/13 10:00-10:45", "9/13 10:45-11:30"]),
        ("팀E", ["9/13 10:00-10:45", "9/13 11:30-12:15"]),
        ("팀F", ["9/13 10:45-11:30", "9/13 11:30-12:15"]),
        ("팀G", ["9/14 10:00-10:45", "9/14 10:45-11:30"]),
        ("팀H", ["9/14 10:00-10:45", "9/14 11:30-12:15"]),
    ]
    
    for name, slots in test_teams:
        scheduler.add_team(name, slots, f"{name.lower()}@gmail.com", "010-0000-0000")
    
    # 최적 스케줄 찾기
    print("=" * 80)
    print("🔍 고급 스케줄링 (A/B조 동시 면접, 연속 배치)...")
    schedule = scheduler.optimize_schedule()
    
    print("\n📅 A조 스케줄:")
    for slot in sorted(schedule["A"].keys()):
        print(f"  {slot}: {schedule['A'][slot]}")
    
    print("\n📅 B조 스케줄:")
    for slot in sorted(schedule["B"].keys()):
        print(f"  {slot}: {schedule['B'][slot]}")
    
    print("\n📊 스케줄링 통계:")
    stats = scheduler.get_schedule_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 미배치 팀 상세 정보
    unassigned = scheduler.get_unassigned_teams_detail()
    if unassigned:
        print("\n⚠️ 미배치 팀 상세:")
        for team_info in unassigned:
            print(f"  - {team_info['팀명']}: {team_info['미배치 이유']}")
            print(f"    가능 시간: {team_info['가능 시간']}")
    else:
        print("\n✅ 모든 팀이 성공적으로 배치되었습니다!")
    
    # DataFrame 출력
    df = scheduler.export_combined_schedule()
    print("\n📊 통합 스케줄 테이블:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    test_advanced_scheduler()