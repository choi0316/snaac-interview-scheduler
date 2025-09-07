"""
parsing_test5.pdf 구조 상세 분석
"""

import pdfplumber
import re

def analyze_test5_structure():
    """test5 PDF 구조 분석"""
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
    
    if interview_section_start >= 0:
        print("=== parsing_test5.pdf 구조 분석 ===\n")
        print(f"인터뷰 섹션 시작: {interview_section_start}번째 줄\n")
        
        # 처음 50줄 분석
        for i in range(interview_section_start, min(interview_section_start + 50, len(lines))):
            line = lines[i]
            
            # 다양한 패턴 체크
            slot_pattern = r'^(\d{1,2})\s+'
            time_pattern = r'(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})'
            check_pattern = r'[✓✔☑OoＯ○●◯◉⚫⚪]'
            
            slot_match = re.match(slot_pattern, line.strip())
            time_match = re.search(time_pattern, line)
            check_match = re.search(check_pattern, line)
            
            # 출력
            print(f"{i:3d}: {repr(line[:80])}")
            
            if slot_match:
                print(f"     → 슬롯 #{slot_match.group(1)}")
            if time_match:
                print(f"     → 시간: {time_match.group(0)}")
            if check_match:
                print(f"     → 체크: '{check_match.group(0)}' (유니코드: {ord(check_match.group(0))})")
            
            # 빈 줄이 아니고 위 패턴들에 해당 안 되면
            if line.strip() and not slot_match and not time_match and not check_match:
                # 특수 문자 확인
                special_chars = [c for c in line if ord(c) > 127]
                if special_chars:
                    print(f"     → 특수문자: {special_chars}")
        
        print("\n=== 패턴 요약 ===")
        print("이 PDF는 다음과 같은 구조로 보입니다:")
        print("- 줄 번호: 슬롯 번호 + 시간")
        print("- 다음 줄: 체크 표시 (✓)")
        print("- 빈 슬롯은 다음 줄이 빈 줄")

if __name__ == "__main__":
    analyze_test5_structure()