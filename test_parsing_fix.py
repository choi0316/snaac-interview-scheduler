"""
parsing_test3.pdf 시간 파싱 문제 해결 테스트
날짜 라인 간섭 문제를 해결하는 개선된 파싱 로직 테스트
"""

import pdfplumber
import re
from typing import Dict, List, Tuple

def extract_time_slots_improved(text: str) -> Dict[str, List[Tuple[str, bool]]]:
    """개선된 시간대 파싱 - 날짜 라인 간섭 문제 해결"""
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
    
    print("🔧 개선된 파싱 시작")
    
    # 1단계: 날짜 라인 전처리 - 문제의 핵심!
    lines = text.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 날짜만 있는 라인 제거 (예: "9/12 (금)")
        if re.match(r'^9/1[2-4]\s*\([월화수목금토일]\)\s*$', line_stripped):
            print(f"🗓️ 날짜 라인 제거: '{line_stripped}'")
            continue
        
        # 슬롯번호 + 날짜 + 시간 패턴 분리 (예: "26 9/14 (일) 13:45~14:30")
        special_pattern = r'^(\d{1,2})\s+9/1[2-4]\s*\([월화수목금토일]\)\s+(.+)$'
        special_match = re.match(special_pattern, line_stripped)
        if special_match:
            slot_num = special_match.group(1)
            time_part = special_match.group(2)
            new_line = f"{slot_num} {time_part}"
            print(f"🔧 특수 패턴 수정: '{line_stripped}' → '{new_line}'")
            cleaned_lines.append(new_line)
            continue
        
        # 일반적인 날짜 정보 제거 (줄 중간에 있는 경우)
        line = re.sub(r'9/1[2-4]\s*\([월화수목금토일]\)', '', line)
        cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 2단계: 인터뷰 섹션 찾기
    interview_section_start = -1
    for i, line in enumerate(cleaned_lines):
        if '인터뷰' in line and '가능' in line and '시간' in line:
            interview_section_start = i
            break
        elif '면접' in line and '가능' in line:
            interview_section_start = i
            break
    
    if interview_section_start >= 0:
        section_lines = cleaned_lines[interview_section_start:]
        
        # 3단계: 각 줄 분석
        for line_idx, line in enumerate(section_lines):
            time_pattern = r'(\d{1,2}:\d{2})[~\-～](\d{1,2}:\d{2})'
            time_match = re.search(time_pattern, line)
            
            if time_match:
                time_str = f"{time_match.group(1)}-{time_match.group(2)}".replace('~', '-').replace('～', '-')
                
                # 줄 앞 번호 확인
                number_pattern = r'^(\d{1,2})\s+'
                number_match = re.match(number_pattern, line.strip())
                
                if number_match:
                    slot_num = int(number_match.group(1))
                    
                    if slot_num in slot_mapping:
                        date, expected_time = slot_mapping[slot_num]
                        
                        # 시간 다음 체크 표시 확인
                        after_time = line[time_match.end():].strip()
                        
                        is_available = False
                        if not after_time:
                            # 다음 줄 확인
                            if line_idx + 1 < len(section_lines):
                                next_line = section_lines[line_idx + 1].strip()
                                # 다음 줄이 숫자나 시간이 아니면 체크 표시
                                if next_line and not re.match(r'^\d+[\s\.]', next_line) and not re.search(r'\d{1,2}:\d{2}', next_line):
                                    is_available = True
                                    print(f"✅ 슬롯 #{slot_num}: {date} {time_str} - 가능 (다음줄: {next_line[:15]})")
                                else:
                                    print(f"❌ 슬롯 #{slot_num}: {date} {time_str} - 불가 (빈칸)")
                            else:
                                print(f"❌ 슬롯 #{slot_num}: {date} {time_str} - 불가 (빈칸)")
                        elif after_time.isdigit():
                            # 숫자는 다음 슬롯 번호
                            print(f"❌ 슬롯 #{slot_num}: {date} {time_str} - 불가 (다음 번호)")
                        else:
                            # 뭔가 표시가 있음
                            is_available = True
                            print(f"✅ 슬롯 #{slot_num}: {date} {time_str} - 가능 (표시: {after_time[:10]})")
                        
                        if is_available:
                            slots[date].append((time_str, True))
    
    total = sum(len(day_slots) for day_slots in slots.values())
    print(f"📊 개선 결과: {total}/36 슬롯 파싱")
    return slots

def test_comparison():
    """원래 vs 개선된 파싱 비교"""
    from improved_pdf_processor import ImprovedPDFProcessor
    
    # PDF 텍스트 추출
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test3.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print("=" * 60)
    print("🔍 파싱 비교 테스트")
    print("=" * 60)
    
    # 원래 방식
    print("\n1️⃣ 원래 파싱 방식:")
    processor = ImprovedPDFProcessor()
    original_slots = processor._extract_time_slots(full_text)
    original_count = sum(len(day_slots) for day_slots in original_slots.values())
    
    print("\n2️⃣ 개선된 파싱 방식:")
    improved_slots = extract_time_slots_improved(full_text)
    improved_count = sum(len(day_slots) for day_slots in improved_slots.values())
    
    print("\n📈 비교 결과:")
    print(f"원래:   {original_count}/36 슬롯")
    print(f"개선:   {improved_count}/36 슬롯")
    print(f"개선도: +{improved_count - original_count} 슬롯")
    
    # 날짜별 상세 비교
    print("\n📅 날짜별 비교:")
    for date in ["9/12", "9/13", "9/14"]:
        orig = len(original_slots[date])
        impr = len(improved_slots[date])
        print(f"{date}: 원래 {orig}개 → 개선 {impr}개 ({'+' if impr > orig else ''}{impr-orig})")
        
        if impr > orig:
            print(f"  추가 파싱된 시간: {[t[0] for t in improved_slots[date] if t not in original_slots[date]]}")
    
    return original_count, improved_count

if __name__ == "__main__":
    test_comparison()