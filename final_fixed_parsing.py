"""
최종 수정된 파싱 로직 - test3는 4개, test5는 36개
"""

import pdfplumber
import re
from typing import Dict, List, Tuple

def extract_time_slots_final(text: str) -> Dict[str, List[Tuple[str, bool]]]:
    """최종 수정된 시간대 파싱"""
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
    
    print("🔧 최종 파싱 시작\n")
    
    lines = text.split('\n')
    
    # 인터뷰 섹션 찾기
    interview_section_start = -1
    for i, line in enumerate(lines):
        if '인터뷰' in line and '가능' in line and '시간' in line:
            interview_section_start = i
            break
        elif '면접' in line and '가능' in line:
            interview_section_start = i
            break
    
    if interview_section_start >= 0:
        section_lines = lines[interview_section_start:]
        
        # 각 줄 분석
        for line_idx, line in enumerate(section_lines):
            # 시간 패턴 찾기
            time_pattern = r'(\d{1,2}:\d{2})[~\-～](\d{1,2}:\d{2})'
            time_match = re.search(time_pattern, line)
            
            if time_match:
                time_str = f"{time_match.group(1)}-{time_match.group(2)}"
                
                # 줄 앞 번호 확인
                number_pattern = r'^(\d{1,2})\s+'
                number_match = re.match(number_pattern, line.strip())
                
                if number_match:
                    slot_num = int(number_match.group(1))
                    
                    if slot_num in slot_mapping:
                        date, expected_time = slot_mapping[slot_num]
                        
                        # 가용성 체크 - 더 엄격한 로직
                        is_available = False
                        
                        # 1. 같은 줄에 체크가 있는가?
                        after_time = line[time_match.end():].strip()
                        if after_time and any(c in after_time for c in ['O', 'o', '○', '●', '✓', '✔', '☑']):
                            is_available = True
                            print(f"✅ 슬롯 #{slot_num}: {date} {expected_time} - 가능 (같은줄: {after_time[:20]})")
                        else:
                            # 2. 다음 줄 확인
                            if line_idx + 1 < len(section_lines):
                                next_line = section_lines[line_idx + 1].strip()
                                
                                # 다음 줄에 체크표시가 있는가?
                                if any(c in next_line for c in ['O', 'o', '○', '●', '✓', '✔', '☑']):
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
                            slots[date].append((expected_time, True))
    
    total = sum(len(day_slots) for day_slots in slots.values())
    print(f"\n📊 파싱 결과: {total}/36 슬롯")
    
    for date in ["9/12", "9/13", "9/14"]:
        count = len(slots[date])
        print(f"  {date}: {count}개")
    
    return slots

def test_both_pdfs():
    """test3와 test5 모두 테스트"""
    from improved_pdf_processor import ImprovedPDFProcessor
    
    print("=" * 70)
    print("🎯 최종 파싱 테스트 - test3는 4개, test5는 36개")
    print("=" * 70)
    
    # test3 테스트
    print("\n📄 parsing_test3.pdf 테스트:")
    print("-" * 50)
    
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test3.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print("\n원본 파싱:")
    processor = ImprovedPDFProcessor()
    original_slots3 = processor._extract_time_slots(full_text)
    original_count3 = sum(len(day_slots) for day_slots in original_slots3.values())
    print(f"결과: {original_count3}/36 슬롯")
    
    print("\n최종 수정 파싱:")
    fixed_slots3 = extract_time_slots_final(full_text)
    fixed_count3 = sum(len(day_slots) for day_slots in fixed_slots3.values())
    
    print(f"\n📊 test3 결과:")
    print(f"원본: {original_count3}/36")
    print(f"수정: {fixed_count3}/36 (실제 체크 수)")
    
    # test5 테스트
    print("\n\n📄 parsing_test5.pdf 테스트:")
    print("-" * 50)
    
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test5.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print("\n원본 파싱:")
    original_slots = processor._extract_time_slots(full_text)
    original_count = sum(len(day_slots) for day_slots in original_slots.values())
    print(f"결과: {original_count}/36 슬롯")
    
    print("\n최종 수정 파싱:")
    fixed_slots = extract_time_slots_final(full_text)
    fixed_count = sum(len(day_slots) for day_slots in fixed_slots.values())
    
    print(f"\n📊 test5 결과:")
    print(f"원본: {original_count}/36")
    print(f"수정: {fixed_count}/36")
    
    print("\n" + "=" * 70)
    print("📊 최종 결과:")
    print(f"test3: {original_count3} → {fixed_count3} ({'✅ 정확' if fixed_count3 == 4 else '❌ 오류'})")
    print(f"test5: {original_count} → {fixed_count} ({'✅ 완벽' if fixed_count == 36 else '❌ 오류'})")

if __name__ == "__main__":
    test_both_pdfs()