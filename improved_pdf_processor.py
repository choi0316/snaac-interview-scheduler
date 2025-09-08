"""
개선된 PDF 처리 모듈
면접 신청서 형식에 맞춘 정확한 파싱
Wingdings2 체크마크 지원 추가
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 특수 체크마크 문자들
WINGDINGS_CHECK = '\uf050'  # Wingdings2 체크마크
LARGE_CIRCLE = '\u25ef'  # ◯ (U+25EF) - 큰 원

@dataclass
class TeamInfo:
    """팀 정보 데이터 클래스"""
    team_name: str = ""
    representative_name: str = ""
    email: str = ""
    phone: str = ""
    available_slots: Dict[str, List[Tuple[str, bool]]] = field(default_factory=dict)
    # 날짜별 (시간, 가능여부) 리스트
    
    def __post_init__(self):
        if not self.available_slots:
            self.available_slots = {}

class ImprovedPDFProcessor:
    """개선된 PDF 처리 클래스"""
    
    def __init__(self):
        # 날짜와 시간 슬롯 정의
        self.dates = ["9/12", "9/13", "9/14"]
        self.time_slots = [
            "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
            "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ]
    
    def extract_from_pdf(self, pdf_path: str) -> TeamInfo:
        """PDF 파일에서 팀 정보 추출"""
        team_info = TeamInfo()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 모든 페이지의 텍스트 추출
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                # 디버깅용 출력
                print("=" * 60)
                print("📄 PDF 전체 텍스트 (처음 500자)")
                print("=" * 60)
                print(full_text[:500])
                print("=" * 60)
                
                # 1. 처음 부분에서 기본 정보 추출 (처음 300자 정도에서)
                header_text = full_text[:300]
                team_info = self._extract_basic_info(header_text, team_info)
                
                # 2. 전체 텍스트에서 누락된 정보 보완
                if not team_info.email:
                    team_info.email = self._extract_email(full_text)
                if not team_info.phone:
                    team_info.phone = self._extract_phone(full_text)
                
                # 3. 면접 가능 시간 추출 (뒤에서부터 파싱)
                team_info.available_slots = self._extract_time_slots(full_text)
                
        except Exception as e:
            print(f"PDF 처리 오류: {e}")
        
        return team_info
    
    def _extract_basic_info(self, text: str, team_info: TeamInfo) -> TeamInfo:
        """처음 부분에서 기본 정보 추출"""
        lines = text.split('\n')
        
        # 레이블과 값을 찾는 더 정확한 방법
        for i, line in enumerate(lines[:20]):  # 처음 20줄 확인
            line_clean = line.strip()
            
            # 팀명 찾기
            if not team_info.team_name:
                if '팀명' in line_clean:
                    # "팀명" 레이블 다음의 값 추출
                    team_match = re.search(r'팀명[\s:：]*([^\s대표자]+)', line_clean)
                    if team_match:
                        team_name = team_match.group(1).strip()
                        # 팀명이 유효한지 확인
                        if team_name and not team_name.startswith('대표'):
                            team_info.team_name = team_name
                            print(f"팀명 발견: {team_name}")
            
            # 대표자명 찾기
            if not team_info.representative_name:
                if '대표자' in line_clean:
                    # "대표자명" 레이블 다음의 값 추출
                    rep_match = re.search(r'대표자명[\s:：]*([가-힣\s]+)', line_clean)
                    if rep_match:
                        rep_name = rep_match.group(1).strip()
                        # 이름 형식 검증 (2-5글자)
                        if 2 <= len(rep_name.replace(' ', '')) <= 5:
                            team_info.representative_name = rep_name
                            print(f"대표자명 발견: {rep_name}")
            
            # 이메일 찾기
            if not team_info.email:
                if '이메일' in line_clean or '@' in line_clean:
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line_clean)
                    if email_match:
                        team_info.email = email_match.group(0)
                        print(f"이메일 발견: {team_info.email}")
            
            # 전화번호 찾기
            if not team_info.phone:
                if '연락처' in line_clean or '전화' in line_clean or '010' in line_clean:
                    phone_match = re.search(r'010[-\s]?\d{4}[-\s]?\d{4}', line_clean)
                    if phone_match:
                        team_info.phone = phone_match.group(0).replace(' ', '-')
                        print(f"전화번호 발견: {team_info.phone}")
        
        return team_info
    
    def _extract_email(self, text: str) -> str:
        """전체 텍스트에서 이메일 추출"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text)
        if matches:
            return matches[0]  # 첫 번째 이메일 반환
        return ""
    
    def _extract_phone(self, text: str) -> str:
        """전체 텍스트에서 전화번호 추출"""
        phone_patterns = [
            r'010[-\s]?\d{4}[-\s]?\d{4}',
            r'010\d{8}',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # 포맷 정규화
                phone = re.sub(r'[-\s]', '', phone)
                if len(phone) == 11:
                    return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return ""
    
    def _extract_time_slots(self, text: str) -> Dict[str, List[Tuple[str, bool]]]:
        """면접 가능 시간대 추출 - O 표시가 있는 시간만 추출"""
        slots = {"9/12": [], "9/13": [], "9/14": []}
        
        # "[인터뷰 가능 시간대]" 또는 유사한 섹션 찾기
        interview_section_start = -1
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if '인터뷰' in line and '가능' in line and '시간' in line:
                interview_section_start = i
                break
            elif '면접' in line and '가능' in line:
                interview_section_start = i
                break
        
        if interview_section_start == -1:
            # 시간 패턴으로 섹션 찾기
            for i, line in enumerate(lines):
                if re.search(r'\d{1,2}:\d{2}[~\-]\d{1,2}:\d{2}', line):
                    interview_section_start = max(0, i - 2)
                    break
        
        if interview_section_start >= 0:
            # 인터뷰 섹션부터 끝까지 분석
            section_lines = lines[interview_section_start:]
            
            # 슬롯 번호와 시간대 매핑 (PDF 테이블 구조 기반)
            slot_mapping = {
                # 금요일 (9/12): 슬롯 1-4 (19:00~22:00)
                1: ("9/12", "19:00-19:45"),
                2: ("9/12", "19:45-20:30"),
                3: ("9/12", "20:30-21:15"),
                4: ("9/12", "21:15-22:00"),
                # 토요일 (9/13): 슬롯 5-20 (10:00~22:00)
                5: ("9/13", "10:00-10:45"),
                6: ("9/13", "10:45-11:30"),
                7: ("9/13", "11:30-12:15"),
                8: ("9/13", "12:15-13:00"),
                9: ("9/13", "13:00-13:45"),
                10: ("9/13", "13:45-14:30"),
                11: ("9/13", "14:30-15:15"),
                12: ("9/13", "15:15-16:00"),
                13: ("9/13", "16:00-16:45"),
                14: ("9/13", "16:45-17:30"),
                15: ("9/13", "17:30-18:15"),
                16: ("9/13", "18:15-19:00"),
                17: ("9/13", "19:00-19:45"),
                18: ("9/13", "19:45-20:30"),
                19: ("9/13", "20:30-21:15"),
                20: ("9/13", "21:15-22:00"),
                # 일요일 (9/14): 슬롯 21-36 (10:00~22:00)
                21: ("9/14", "10:00-10:45"),
                22: ("9/14", "10:45-11:30"),
                23: ("9/14", "11:30-12:15"),
                24: ("9/14", "12:15-13:00"),
                25: ("9/14", "13:00-13:45"),
                26: ("9/14", "13:45-14:30"),
                27: ("9/14", "14:30-15:15"),
                28: ("9/14", "15:15-16:00"),
                29: ("9/14", "16:00-16:45"),
                30: ("9/14", "16:45-17:30"),
                31: ("9/14", "17:30-18:15"),
                32: ("9/14", "18:15-19:00"),
                33: ("9/14", "19:00-19:45"),
                34: ("9/14", "19:45-20:30"),
                35: ("9/14", "20:30-21:15"),
                36: ("9/14", "21:15-22:00"),
            }
            
            # 각 줄을 순차적으로 분석 (다음 줄까지 확인하기 위해 인덱스 사용)
            for line_idx, line in enumerate(section_lines):
                # 여러 패턴 시도
                # 패턴 1: 번호 + 시간대 + 표시 (예: "22 10:45~11:30 ✓")
                # 패턴 2: 번호만 있는 경우 (다음 줄에 시간대)
                # 패턴 3: 시간대만 있는 경우
                
                # 먼저 시간대 패턴 찾기
                time_pattern = r'(\d{1,2}:\d{2})[~\-～](\d{1,2}:\d{2})'
                time_match = re.search(time_pattern, line)
                
                if time_match:
                    # 시간대가 있는 경우
                    time_str = f"{time_match.group(1)}-{time_match.group(2)}".replace('~', '-').replace('～', '-')
                    
                    # 줄 앞에 번호가 있는지 확인
                    number_pattern = r'^(\d{1,2})\s+'
                    number_match = re.match(number_pattern, line.strip())
                    
                    if number_match:
                        slot_num = int(number_match.group(1))
                        
                        # 번호와 매핑이 있는 경우
                        if slot_num in slot_mapping:
                            date, expected_time = slot_mapping[slot_num]
                            
                            # 가용성 체크 - 더 정확한 로직
                            is_available = False
                            
                            # 1. 같은 줄에 체크가 있는가? (V, 0, ㅇ, Wingdings2 추가)
                            after_time = line[time_match.end():].strip()
                            if after_time and any(c in after_time for c in ['O', 'o', '○', '●', '✓', '✔', '☑', 'V', 'v', '0', 'ㅇ', '◯', WINGDINGS_CHECK, LARGE_CIRCLE]):
                                is_available = True
                                print(f"✅ 슬롯 #{slot_num}: {date} {expected_time} - 가능 (같은줄: {after_time[:20]})")
                            else:
                                # 2. 다음 줄 확인
                                if line_idx + 1 < len(section_lines):
                                    next_line = section_lines[line_idx + 1].strip()
                                    
                                    # 다음 줄에 체크표시가 있는가? (V, 0, ㅇ, Wingdings2 추가)
                                    # 단, 다음 줄이 숫자로 시작하면 다음 슬롯이므로 체크 아님
                                    if not re.match(r'^\d+\s', next_line) and any(c in next_line for c in ['O', 'o', '○', '●', '✓', '✔', '☑', 'V', 'v', '0', 'ㅇ', '◯', WINGDINGS_CHECK, LARGE_CIRCLE]):
                                        is_available = True
                                        # 날짜가 포함된 경우도 처리
                                        if '9/1' in next_line:
                                            print(f"✅ 슬롯 #{slot_num}: {date} {expected_time} - 가능 (날짜+체크: {next_line[:30]})")
                                        else:
                                            print(f"✅ 슬롯 #{slot_num}: {date} {expected_time} - 가능 (다음줄: {next_line[:20]})")
                                    # 다음 줄이 날짜만 있는 경우는 체크 아님
                                    elif re.match(r'^9/1[2-4]\s*\([월화수목금토일]\)\s*$', next_line):
                                        print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (날짜만)")
                                    # 다음 줄이 숫자로 시작하면 다음 슬롯
                                    elif re.match(r'^\d+[\s\.]', next_line):
                                        print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (다음슬롯)")
                                    # 다음 줄에 시간이 있으면 다음 슬롯
                                    elif re.search(r'\d{1,2}:\d{2}', next_line):
                                        print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (다음시간)")
                                    # 빈 줄
                                    elif not next_line:
                                        print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (빈칸)")
                                    # 기타 텍스트
                                    else:
                                        # 설명 텍스트인지 확인
                                        if '가능' in next_line or '시간' in next_line or '페이지' in next_line or '*' in next_line:
                                            print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (설명텍스트)")
                                        else:
                                            print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (기타: {next_line[:20]})")
                                else:
                                    print(f"❌ 슬롯 #{slot_num}: {date} {expected_time} - 불가 (마지막)")
                            
                            if is_available:
                                slots[date].append((time_str, True))
                    else:
                        # 번호가 없지만 시간대가 있는 경우 (예: "16:00~16:45 V")
                        # 시간대로 슬롯 번호 역추적
                        for slot_num, (date, expected_time) in slot_mapping.items():
                            if expected_time == time_str or expected_time.replace('-', '~') in line:
                                after_time = line[time_match.end():]
                                after_time_stripped = after_time.strip()
                                
                                if after_time_stripped:
                                    # 간단한 체크 여부 판단 (번호 없는 경우도 동일한 로직)
                                    # 0, ㅇ은 체크 표시로 간주, 다른 숫자는 다음 슬롯 번호
                                    if after_time_stripped == '0' or any(c in after_time_stripped for c in ['O', 'o', '○', '●', '✓', '✔', '☑', 'V', 'v', 'ㅇ']):
                                        # 0이거나 다른 체크 표시가 있음
                                        slots[date].append((time_str, True))
                                        print(f"✅ {date} {time_str} - 가능 (번호 없이 시간과 표시: {after_time_stripped[:20]})")
                                        break
                                    elif after_time_stripped.strip().isdigit():
                                        # 0이 아닌 숫자만 있으면 다음 항목 번호
                                        print(f"❌ {date} {time_str} - 불가 (다음 항목 번호)")
                                    else:
                                        # 기타 텍스트 (체크로 간주)
                                        slots[date].append((time_str, True))
                                        print(f"✅ {date} {time_str} - 가능 (기타 표시: {after_time_stripped[:20]})")
                                        break
        
        return slots

def process_pdf_file(file_path: str) -> Dict:
    """PDF 파일 처리 메인 함수"""
    processor = ImprovedPDFProcessor()
    team_info = processor.extract_from_pdf(file_path)
    
    # 면접 가능 시간을 문자열로 변환
    available_times = []
    for date, time_slots in team_info.available_slots.items():
        for time_slot, is_available in time_slots:
            if is_available:
                available_times.append(f"{date} {time_slot}")
    
    return {
        "팀명": team_info.team_name or "미확인",
        "대표자명": team_info.representative_name or "미확인",
        "이메일": team_info.email or "미확인",
        "전화번호": team_info.phone or "미확인",
        "가능시간": available_times if available_times else ["미확인"],
        "면접 가능 시간": available_times if available_times else ["미확인"],
        "상세 시간표": team_info.available_slots
    }

def test_pdf_files():
    """테스트 파일들 처리"""
    test_files = [
        "/Users/choejinmyung/Downloads/parsing_test1.pdf",
        "/Users/choejinmyung/Downloads/parsing_test2.pdf"
    ]
    
    for pdf_file in test_files:
        print("\n" + "=" * 60)
        print(f"📄 파일: {pdf_file}")
        print("=" * 60)
        
        try:
            result = process_pdf_file(pdf_file)
            
            print("\n📊 추출 결과:")
            print(f"  팀명: {result['팀명']}")
            print(f"  대표자명: {result['대표자명']}")
            print(f"  이메일: {result['이메일']}")
            print(f"  전화번호: {result['전화번호']}")
            
            print("\n📅 면접 가능 시간:")
            if result['면접 가능 시간'] and result['면접 가능 시간'][0] != "미확인":
                for time in result['면접 가능 시간']:
                    print(f"    - {time}")
            else:
                print("    미확인")
            
            if result['상세 시간표']:
                print("\n📋 상세 시간표:")
                for date, slots in result['상세 시간표'].items():
                    if slots:
                        print(f"  {date}:")
                        for time, available in slots:
                            status = "⭕ 가능" if available else "❌ 불가"
                            print(f"    {time}: {status}")
            
        except Exception as e:
            print(f"❌ 오류: {e}")
        
        print("=" * 60)

if __name__ == "__main__":
    test_pdf_files()