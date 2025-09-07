"""
체크 표시 문자 분석
"""

import pdfplumber
import re

def analyze_check_marks():
    """PDF에서 체크 표시나 특수 문자 분석"""
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test3.pdf') as pdf:
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
        section_lines = lines[interview_section_start:interview_section_start+50]
        
        print("=== 모든 시간 슬롯 분석 ===")
        
        for i, line in enumerate(section_lines):
            line_num = interview_section_start + i
            
            # 슬롯 번호 + 시간 패턴
            slot_time_pattern = r'^(\d{1,2})\s+(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})'
            match = re.match(slot_time_pattern, line.strip())
            
            if match:
                slot_num = match.group(1)
                time_str = match.group(2)
                after_time = line[match.end():].strip()
                
                # 모든 문자 분석 (공백 포함)
                print(f"슬롯 #{slot_num}: {time_str}")
                print(f"  원본: '{line}'")
                print(f"  시간 이후: '{after_time}'")
                
                # 바이트 분석
                if after_time:
                    print(f"  바이트: {[ord(c) for c in after_time]}")
                    print(f"  길이: {len(after_time)}")
                    
                    # 특수 문자 체크
                    special_chars = []
                    for c in after_time:
                        if ord(c) > 127 or c in 'O○●◯◉⚫⚪✓✔☑□■◼◻':
                            special_chars.append((c, ord(c)))
                    if special_chars:
                        print(f"  특수문자: {special_chars}")
                else:
                    print("  빈칸")
                print()

if __name__ == "__main__":
    analyze_check_marks()