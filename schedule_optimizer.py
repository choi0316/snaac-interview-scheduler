"""
면접 스케줄링 최적화 알고리즘
제약 만족 문제(CSP) 기반 스케줄러
"""

import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
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

@dataclass
class TimeSlot:
    """시간 슬롯"""
    date: str
    time: str
    full_slot: str  # "9/12 19:00-19:45"
    assigned_team: Optional[str] = None
    
class InterviewScheduler:
    """면접 스케줄링 최적화 클래스"""
    
    def __init__(self):
        # 전체 가능한 시간 슬롯 정의
        self.all_slots = self._generate_all_slots()
        self.teams: List[Team] = []
        self.schedule: Dict[str, str] = {}  # {slot: team_name}
        
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
    
    def add_team(self, name: str, available_slots: List[str], 
                 email: str = "", phone: str = ""):
        """팀 추가"""
        team = Team(name=name, available_slots=available_slots, 
                   email=email, phone=phone)
        self.teams.append(team)
    
    def schedule_interviews(self, method: str = "greedy") -> Dict[str, str]:
        """
        면접 스케줄링 실행
        
        Args:
            method: 스케줄링 방법 
                   - "greedy": 탐욕 알고리즘 (가장 적은 선택지를 가진 팀부터)
                   - "backtrack": 백트래킹 알고리즘 (모든 팀 배치 보장)
                   - "random": 랜덤 배치
        
        Returns:
            스케줄 딕셔너리 {slot: team_name}
        """
        if method == "greedy":
            return self._greedy_scheduling()
        elif method == "backtrack":
            return self._backtrack_scheduling()
        elif method == "random":
            return self._random_scheduling()
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _greedy_scheduling(self) -> Dict[str, str]:
        """탐욕 알고리즘: 선택지가 적은 팀부터 배치"""
        self.schedule = {}
        
        # 팀을 가능한 슬롯 수로 정렬 (적은 것부터)
        sorted_teams = sorted(self.teams, key=lambda t: len(t.available_slots))
        
        for team in sorted_teams:
            # 아직 배정되지 않은 슬롯 중에서 선택
            for slot in team.available_slots:
                if slot not in self.schedule:
                    self.schedule[slot] = team.name
                    team.assigned_slot = slot
                    break
        
        return self.schedule
    
    def _backtrack_scheduling(self) -> Dict[str, str]:
        """백트래킹 알고리즘: 모든 팀이 배치될 때까지 시도"""
        self.schedule = {}
        assigned_teams = set()
        
        def backtrack(team_idx: int) -> bool:
            # 모든 팀이 배치되면 성공
            if team_idx >= len(self.teams):
                return True
            
            team = self.teams[team_idx]
            
            # 이미 배치된 팀은 건너뛰기
            if team.name in assigned_teams:
                return backtrack(team_idx + 1)
            
            # 가능한 모든 슬롯 시도
            for slot in team.available_slots:
                if slot not in self.schedule:
                    # 슬롯 배치 시도
                    self.schedule[slot] = team.name
                    team.assigned_slot = slot
                    assigned_teams.add(team.name)
                    
                    # 다음 팀 배치 시도
                    if backtrack(team_idx + 1):
                        return True
                    
                    # 실패하면 되돌리기
                    del self.schedule[slot]
                    team.assigned_slot = None
                    assigned_teams.remove(team.name)
            
            return False
        
        # MRV (Minimum Remaining Values) 휴리스틱 적용
        self.teams.sort(key=lambda t: len(t.available_slots))
        
        if backtrack(0):
            return self.schedule
        else:
            # 모든 팀을 배치할 수 없는 경우 최대한 많이 배치
            return self._greedy_scheduling()
    
    def _random_scheduling(self) -> Dict[str, str]:
        """랜덤 스케줄링"""
        self.schedule = {}
        teams_copy = self.teams.copy()
        random.shuffle(teams_copy)
        
        for team in teams_copy:
            available = [s for s in team.available_slots if s not in self.schedule]
            if available:
                slot = random.choice(available)
                self.schedule[slot] = team.name
                team.assigned_slot = slot
        
        return self.schedule
    
    def get_unassigned_teams(self) -> List[str]:
        """배치되지 않은 팀 목록 반환"""
        assigned = {team.name for team in self.teams if team.assigned_slot}
        all_teams = {team.name for team in self.teams}
        return list(all_teams - assigned)
    
    def get_schedule_statistics(self) -> Dict:
        """스케줄링 통계 반환"""
        total_teams = len(self.teams)
        assigned_teams = len([t for t in self.teams if t.assigned_slot])
        unassigned_teams = total_teams - assigned_teams
        
        # 날짜별 배치 수
        date_stats = {"9/12": 0, "9/13": 0, "9/14": 0}
        for slot in self.schedule:
            date = slot.split()[0]
            date_stats[date] += 1
        
        # 시간대별 사용률
        total_slots = len(self.all_slots)
        used_slots = len(self.schedule)
        
        return {
            "총 팀 수": total_teams,
            "배치된 팀": assigned_teams,
            "미배치 팀": unassigned_teams,
            "배치율": f"{(assigned_teams/total_teams*100):.1f}%" if total_teams > 0 else "0%",
            "금요일 배치": date_stats["9/12"],
            "토요일 배치": date_stats["9/13"],
            "일요일 배치": date_stats["9/14"],
            "슬롯 사용률": f"{(used_slots/total_slots*100):.1f}%"
        }
    
    def export_schedule(self) -> pd.DataFrame:
        """스케줄을 DataFrame으로 변환"""
        data = []
        for slot, team_name in sorted(self.schedule.items()):
            date, time = slot.split(" ", 1)
            team = next((t for t in self.teams if t.name == team_name), None)
            
            data.append({
                "날짜": date,
                "시간": time,
                "팀명": team_name,
                "이메일": team.email if team else "",
                "전화번호": team.phone if team else ""
            })
        
        return pd.DataFrame(data)
    
    def find_optimal_schedule(self, max_iterations: int = 100) -> Dict[str, str]:
        """
        최적 스케줄 찾기 (여러 방법 시도)
        
        Args:
            max_iterations: 최대 시도 횟수
        
        Returns:
            가장 많은 팀을 배치한 스케줄
        """
        best_schedule = {}
        best_count = 0
        
        # 백트래킹 시도
        schedule = self._backtrack_scheduling()
        assigned_count = len([t for t in self.teams if t.assigned_slot])
        if assigned_count > best_count:
            best_schedule = schedule.copy()
            best_count = assigned_count
        
        # 모든 팀이 배치되면 바로 반환
        if best_count == len(self.teams):
            return best_schedule
        
        # 랜덤 시도로 더 나은 해 찾기
        for _ in range(max_iterations):
            # 팀 순서 섞기
            random.shuffle(self.teams)
            schedule = self._greedy_scheduling()
            
            assigned_count = len([t for t in self.teams if t.assigned_slot])
            if assigned_count > best_count:
                best_schedule = schedule.copy()
                best_count = assigned_count
                
                # 모든 팀이 배치되면 종료
                if best_count == len(self.teams):
                    break
        
        self.schedule = best_schedule
        return best_schedule

def test_scheduler():
    """스케줄러 테스트"""
    scheduler = InterviewScheduler()
    
    # 테스트 데이터 추가
    scheduler.add_team("필리데이", [
        "9/12 19:00-19:45", "9/12 19:45-20:30", 
        "9/12 20:30-21:15", "9/12 21:15-22:00"
    ], "pilleday@gmail.com", "010-4309-7377")
    
    scheduler.add_team("아뮤즈8", [
        "9/12 19:00-19:45", "9/12 19:45-20:30",
        "9/13 12:15-13:00", "9/13 13:00-13:45", "9/13 13:45-14:30",
        "9/13 14:30-15:15", "9/13 15:15-16:00", "9/13 16:00-16:45",
        "9/13 16:45-17:30", "9/14 11:30-12:15", "9/14 12:15-13:00",
        "9/14 13:00-13:45", "9/14 13:45-14:30", "9/14 14:30-15:15",
        "9/14 15:15-16:00", "9/14 16:00-16:45"
    ], "ka4697@gmail.com", "010-3051-2939")
    
    # 추가 팀 예시 (겹치는 시간대로 테스트)
    scheduler.add_team("팀C", [
        "9/12 19:00-19:45", "9/12 19:45-20:30", "9/13 10:00-10:45"
    ])
    
    scheduler.add_team("팀D", [
        "9/12 19:00-19:45", "9/13 10:00-10:45", "9/13 10:45-11:30"
    ])
    
    # 최적 스케줄 찾기
    print("=" * 60)
    print("🔍 최적 스케줄 찾기...")
    schedule = scheduler.find_optimal_schedule()
    
    print("\n📅 최종 스케줄:")
    for slot in sorted(schedule.keys()):
        print(f"  {slot}: {schedule[slot]}")
    
    print("\n📊 스케줄링 통계:")
    stats = scheduler.get_schedule_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    unassigned = scheduler.get_unassigned_teams()
    if unassigned:
        print(f"\n⚠️ 미배치 팀: {', '.join(unassigned)}")
    else:
        print("\n✅ 모든 팀이 성공적으로 배치되었습니다!")
    
    # DataFrame 출력
    df = scheduler.export_schedule()
    print("\n📊 스케줄 테이블:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    test_scheduler()