"""
parsing_test7.pdf 구조 분석 - V 표시 인식 문제
"""

import pdfplumber
import re

def analyze_test7():
    """test7 PDF 구조 분석"""
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test7.pdf') as pdf:
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
    
    if interview_section_start >= 0:
        print("=== parsing_test7.pdf 구조 분석 ===\n")
        print(f"인터뷰 섹션 시작: {interview_section_start}번째 줄\n")
        
        # 처음 50줄 분석
        for i in range(interview_section_start, min(interview_section_start + 50, len(lines))):
            line = lines[i]
            
            # 다양한 패턴 체크
            slot_pattern = r'^(\d{1,2})\s+'
            time_pattern = r'(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})'
            
            slot_match = re.match(slot_pattern, line.strip())
            time_match = re.search(time_pattern, line)
            
            # 출력
            print(f"{i:3d}: {repr(line[:80])}")
            
            if slot_match:
                print(f"     → 슬롯 #{slot_match.group(1)}")
            if time_match:
                print(f"     → 시간: {time_match.group(0)}")
            
            # V 표시 확인
            if 'V' in line or 'v' in line:
                print(f"     → V 표시 발견! 위치: {line.find('V')}")
                # V 주변 문자 확인
                v_idx = line.find('V') if 'V' in line else line.find('v')
                if v_idx > 0:
                    before = line[max(0, v_idx-5):v_idx]
                    after = line[v_idx:min(len(line), v_idx+5)]
                    print(f"     → V 주변: '{before}' [V] '{after}'")
                    
            # 빈 줄이 아니고 위 패턴들에 해당 안 되면
            if line.strip() and not slot_match and not time_match and 'V' not in line and 'v' not in line:
                # 특수 문자 확인
                special_chars = [c for c in line if ord(c) > 127]
                if special_chars:
                    print(f"     → 특수문자: {special_chars[:10]}")
        
        print("\n=== V 표시가 있는 슬롯 요약 ===")
        v_slots = []
        for i in range(interview_section_start, min(interview_section_start + 100, len(lines))):
            line = lines[i].strip()
            if re.search(r'^\d{1,2}\s+\d{1,2}:\d{2}', line) and ('V' in line or 'v' in line):
                v_slots.append(line)
        
        print(f"V 표시가 있는 줄 수: {len(v_slots)}")
        for slot in v_slots[:5]:  # 처음 5개만
            print(f"  - {slot}")

if __name__ == "__main__":
    analyze_test7()