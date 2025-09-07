"""
PDF 텍스트 구조 분석용 스크립트
"""

import pdfplumber
import re

def analyze_pdf_structure():
    """PDF 텍스트 구조 분석"""
    with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test3.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print("=== PDF 전체 텍스트 구조 ===")
    lines = full_text.split('\n')
    
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
        print(f"\n🎯 인터뷰 섹션 시작: {interview_section_start}번째 줄")
        print(f"섹션 시작 라인: '{lines[interview_section_start]}'")
        
        # 인터뷰 섹션 이후 50줄 분석
        section_lines = lines[interview_section_start:interview_section_start+50]
        
        for i, line in enumerate(section_lines):
            line_num = interview_section_start + i
            
            # 시간 패턴 찾기
            time_pattern = r'(\d{1,2}:\d{2})[~\-～](\d{1,2}:\d{2})'
            time_match = re.search(time_pattern, line)
            
            # 슬롯 번호 패턴 찾기
            slot_pattern = r'^(\d{1,2})\s+'
            slot_match = re.match(slot_pattern, line.strip())
            
            # 날짜 패턴 찾기
            date_pattern = r'9/1[2-4]\s*\([월화수목금토일]\)'
            date_match = re.search(date_pattern, line)
            
            print(f"{line_num:3d}: '{line.strip()}'")
            if time_match:
                print(f"     ⏰ 시간: {time_match.group(1)}-{time_match.group(2)}")
            if slot_match:
                print(f"     🔢 슬롯: #{slot_match.group(1)}")
            if date_match:
                print(f"     📅 날짜: {date_match.group(0)}")
            print()
    else:
        print("❌ 인터뷰 섹션을 찾을 수 없습니다")
        
        # 전체 텍스트에서 시간 패턴이 있는 줄들 찾기
        print("\n🔍 시간 패턴이 있는 모든 줄:")
        time_pattern = r'(\d{1,2}:\d{2})[~\-～](\d{1,2}:\d{2})'
        for i, line in enumerate(lines):
            if re.search(time_pattern, line):
                print(f"{i:3d}: '{line.strip()}'")

if __name__ == "__main__":
    analyze_pdf_structure()