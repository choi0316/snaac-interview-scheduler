"""
parsing_test5.pdf에서 누락된 슬롯 찾기
"""

import pdfplumber
import re

def find_all_slots():
    """모든 슬롯 찾기"""
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test5.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    lines = full_text.split('\n')
    
    # 인터뷰 섹션 찾기
    interview_section_start = -1
    for i, line in enumerate(lines):
        if '인터뷰' in line and '가능' in line and '시간' in line:
            interview_section_start = i
            break
    
    print("=== 모든 슬롯 상태 확인 ===\n")
    
    found_slots = {}
    checked_slots = []
    
    if interview_section_start >= 0:
        i = interview_section_start
        
        while i < min(interview_section_start + 100, len(lines)):
            line = lines[i].strip()
            
            # 슬롯 번호와 시간 패턴
            slot_pattern = r'^(\d{1,2})\s+(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})'
            match = re.match(slot_pattern, line)
            
            if match:
                slot_num = int(match.group(1))
                time_str = match.group(2)
                
                # 다음 줄 확인
                next_line = ""
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                
                # 체크 표시 확인
                has_check = False
                check_location = ""
                
                # 같은 줄에 체크가 있는지
                if '✓' in line or 'O' in line or '○' in line:
                    has_check = True
                    check_location = "같은 줄"
                # 다음 줄에 체크가 있는지
                elif '✓' in next_line or 'O' in next_line or '○' in next_line:
                    has_check = True
                    check_location = "다음 줄"
                    # 날짜가 포함된 경우
                    if '9/1' in next_line:
                        check_location = "다음 줄 (날짜 포함)"
                
                found_slots[slot_num] = {
                    'time': time_str,
                    'has_check': has_check,
                    'check_location': check_location,
                    'line_num': i
                }
                
                if has_check:
                    checked_slots.append(slot_num)
                
                print(f"슬롯 #{slot_num:2d}: {time_str:15s} {'✅' if has_check else '❌'} {check_location}")
            
            i += 1
    
    print(f"\n📊 통계:")
    print(f"- 발견된 슬롯: {len(found_slots)}/36")
    print(f"- 체크된 슬롯: {len(checked_slots)}/36")
    
    # 누락된 슬롯 확인
    print(f"\n❌ 파싱되지 않은 슬롯:")
    for slot_num in range(1, 37):
        if slot_num not in found_slots:
            print(f"  - 슬롯 #{slot_num}")
    
    # 체크되지 않은 슬롯
    print(f"\n⚠️ 체크되지 않은 슬롯:")
    for slot_num, info in found_slots.items():
        if not info['has_check']:
            print(f"  - 슬롯 #{slot_num}: {info['time']}")
    
    # 특수 케이스 분석
    print(f"\n🔍 특수 케이스:")
    for slot_num, info in found_slots.items():
        if info['check_location'] == "다음 줄 (날짜 포함)":
            print(f"  - 슬롯 #{slot_num}: 날짜와 체크가 같은 줄에")
    
    return found_slots, checked_slots

def check_full_text():
    """전체 텍스트에서 26번 슬롯 직접 찾기"""
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test5.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    lines = full_text.split('\n')
    
    print("\n=== 26번 슬롯 주변 분석 ===")
    for i, line in enumerate(lines):
        if '26' in line and '13:45' in line:
            print(f"발견! 줄 {i}: {repr(line)}")
            # 주변 줄 표시
            for j in range(max(0, i-2), min(i+3, len(lines))):
                print(f"  {j}: {repr(lines[j])}")
            break
        elif line.strip() == '26':
            print(f"26번만 발견! 줄 {i}: {repr(line)}")
            # 주변 줄 표시
            for j in range(max(0, i-2), min(i+3, len(lines))):
                print(f"  {j}: {repr(lines[j])}")

if __name__ == "__main__":
    found_slots, checked_slots = find_all_slots()
    check_full_text()