"""
날짜가 중간에 끼어있는 구조를 처리하는 개선된 파싱 로직
"""

import pdfplumber
import re
from typing import Dict, List, Tuple

def extract_time_slots_fixed(text: str) -> Dict[str, List[Tuple[str, bool]]]:
    """날짜 간섭 문제를 해결한 시간대 파싱"""
    slots = {"9/12": [], "9/13": [], "9/14": []}
    
    # 슬롯 매핑
    slot_mapping = {
        # 금요일 (9/12): 슬롯 1-4
        1: ("9/12", "19:00-19:45"), 2: ("9/12", "19:45-20:30"), 
        3: ("9/12", "20:30-21:15"), 4: ("9/12", "21:15-22:00"),
        # 토요일 (9/13): 슬롯 5-20
        5: ("9/13", "10:00-10:45"), 6: ("9/13", "10:45-11:30"), 7: ("9/13", "11:30-12:15"), 8: ("9/13", "12:15-13:00"),
        9: ("9/13", "13:00-13:45"), 10: ("9/13", "13:45-14:30"), 11: ("9/13", "14:30-15:15"), 12: ("9/13", "15:15-16:00"),
        13: ("9/13", "16:00-16:45"), 14: ("9/13", "16:45-17:30"), 15: ("9/13", "17:30-18:15"), 16: ("9/13", "18:15-19:00"),
        17: ("9/13", "19:00-19:45"), 18: ("9/13", "19:45-20:30"), 19: ("9/13", "20:30-21:15"), 20: ("9/13", "21:15-22:00"),
        # 일요일 (9/14): 슬롯 21-36
        21: ("9/14", "10:00-10:45"), 22: ("9/14", "10:45-11:30"), 23: ("9/14", "11:30-12:15"), 24: ("9/14", "12:15-13:00"),
        25: ("9/14", "13:00-13:45"), 26: ("9/14", "13:45-14:30"), 27: ("9/14", "14:30-15:15"), 28: ("9/14", "15:15-16:00"),
        29: ("9/14", "16:00-16:45"), 30: ("9/14", "16:45-17:30"), 31: ("9/14", "17:30-18:15"), 32: ("9/14", "18:15-19:00"),
        33: ("9/14", "19:00-19:45"), 34: ("9/14", "19:45-20:30"), 35: ("9/14", "20:30-21:15"), 36: ("9/14", "21:15-22:00"),
    }
    
    print("🔧 개선된 파싱 시작\n")
    
    lines = text.split('\n')
    
    # 인터뷰 섹션 찾기
    interview_section_start = -1
    for i, line in enumerate(lines):
        if '인터뷰' in line and '가능' in line and '시간' in line:
            interview_section_start = i
            break
    
    if interview_section_start >= 0:
        print(f"✅ 인터뷰 섹션 발견: {interview_section_start}번째 줄\n")
        
        # 모든 슬롯 정보를 먼저 수집
        slot_data = {}
        
        for i in range(interview_section_start, min(interview_section_start + 100, len(lines))):
            line = lines[i].strip()
            
            # 패턴 1: "1 19:00~19:45 O" (번호 시간 표시)
            pattern1 = r'^(\d{1,2})\s+(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})\s*(.*)$'
            match1 = re.match(pattern1, line)
            
            # 패턴 2: "1" (번호만) - 다음 줄에 시간
            pattern2 = r'^(\d{1,2})\s*$'
            match2 = re.match(pattern2, line)
            
            # 패턴 3: "3 20:30~21:15 O" 처럼 날짜가 같은 줄에 있는 경우
            # "3 9/12 (금) 20:30~21:15 O" 형태는 없지만, 처리 준비
            
            if match1:
                slot_num = int(match1.group(1))
                time_str = match1.group(2).replace('~', '-').replace('～', '-')
                mark = match1.group(3).strip()
                
                # 날짜 부분 제거 (만약 있다면)
                mark = re.sub(r'9/1[2-4]\s*\([월화수목금토일]\)', '', mark).strip()
                
                slot_data[slot_num] = {
                    'time': time_str,
                    'mark': mark,
                    'line_num': i
                }
                print(f"슬롯 #{slot_num}: {time_str} {'✅' if mark else '❌'} (표시: '{mark}')")
                
            elif match2:
                slot_num = int(match2.group(1))
                # 다음 줄에서 시간 찾기
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    time_pattern = r'(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})'
                    time_match = re.search(time_pattern, next_line)
                    if time_match:
                        time_str = time_match.group(1).replace('~', '-').replace('～', '-')
                        # 시간 이후 부분이 표시
                        after_time = next_line[time_match.end():].strip()
                        # 날짜 부분 제거
                        after_time = re.sub(r'9/1[2-4]\s*\([월화수목금토일]\)', '', after_time).strip()
                        
                        slot_data[slot_num] = {
                            'time': time_str,
                            'mark': after_time,
                            'line_num': i
                        }
                        print(f"슬롯 #{slot_num}: {time_str} {'✅' if after_time else '❌'} (표시: '{after_time}')")
        
        # 수집된 데이터로 최종 슬롯 생성
        for slot_num, data in slot_data.items():
            if slot_num in slot_mapping:
                date, expected_time = slot_mapping[slot_num]
                
                # 표시가 있으면 가능
                is_available = bool(data['mark'] and data['mark'] not in ['', ' '])
                
                if is_available:
                    slots[date].append((expected_time, True))
    
    total = sum(len(day_slots) for day_slots in slots.values())
    print(f"\n📊 파싱 결과: {total}/36 슬롯")
    
    for date in ["9/12", "9/13", "9/14"]:
        count = len(slots[date])
        print(f"  {date}: {count}개")
    
    return slots

def test_fixed_parsing():
    """개선된 파싱 테스트"""
    from improved_pdf_processor import ImprovedPDFProcessor
    
    # PDF 텍스트 추출
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test3.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print("=" * 70)
    print("🎯 날짜 간섭 문제 해결 테스트")
    print("=" * 70)
    
    # 원본 파싱
    print("\n1️⃣ 원본 파싱:")
    processor = ImprovedPDFProcessor()
    original_slots = processor._extract_time_slots(full_text)
    original_count = sum(len(day_slots) for day_slots in original_slots.values())
    print(f"결과: {original_count}/36 슬롯")
    
    # 개선된 파싱
    print("\n2️⃣ 개선된 파싱:")
    fixed_slots = extract_time_slots_fixed(full_text)
    fixed_count = sum(len(day_slots) for day_slots in fixed_slots.values())
    
    print("\n📊 비교 결과:")
    print(f"원본:   {original_count}/36 슬롯")
    print(f"개선:   {fixed_count}/36 슬롯")
    print(f"개선도: +{fixed_count - original_count} 슬롯")
    
    return original_count, fixed_count

if __name__ == "__main__":
    test_fixed_parsing()