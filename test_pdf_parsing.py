"""
PDF 파싱 테스트 및 디버그 스크립트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.pdf_extractor import PDFExtractor
import pdfplumber

def test_pdf_parsing(pdf_path):
    """PDF 파싱 테스트"""
    print("="*60)
    print(f"PDF 파일 테스트: {pdf_path}")
    print("="*60)
    
    # 1. pdfplumber로 직접 텍스트 추출
    print("\n1. pdfplumber로 직접 텍스트 추출:")
    print("-"*40)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    print(f"\n페이지 {page_num}:")
                    print(text[:500])  # 처음 500자만 출력
                    print("...")
    except Exception as e:
        print(f"오류 발생: {e}")
    
    # 2. PDFExtractor 사용
    print("\n\n2. PDFExtractor로 파싱:")
    print("-"*40)
    try:
        extractor = PDFExtractor()
        teams = extractor.extract_teams_from_pdf(pdf_path)
        
        print(f"추출된 팀 수: {len(teams)}")
        
        for team in teams[:3]:  # 처음 3개 팀만 출력
            print(f"\n팀 이름: {team.name}")
            print(f"팀 번호: {team.team_number}")
            print(f"이메일: {team.email}")
            print(f"제약 조건 수: {len(team.constraints)}")
            
            if team.constraints:
                print("제약 조건:")
                for constraint in team.constraints[:5]:  # 처음 5개만
                    print(f"  - {constraint}")
            
            # 가능한 시간대와 불가능한 시간대 확인
            available_slots = [c.slot_number for c in team.constraints if c.is_available]
            unavailable_slots = [c.slot_number for c in team.constraints if not c.is_available]
            
            print(f"가능한 시간대: {available_slots[:10]}...")
            print(f"불가능한 시간대: {unavailable_slots[:10]}...")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 원본 텍스트에서 시간대 패턴 찾기
    print("\n\n3. 원본 텍스트에서 시간대 패턴 분석:")
    print("-"*40)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # 시간대 패턴 찾기
            import re
            
            # 날짜 패턴
            date_pattern = r'9/\d{1,2}'
            dates = re.findall(date_pattern, full_text)
            print(f"발견된 날짜: {set(dates)}")
            
            # 시간대 패턴
            time_pattern = r'\d{1,2}:\d{2}~\d{1,2}:\d{2}'
            times = re.findall(time_pattern, full_text)
            print(f"발견된 시간대 수: {len(times)}")
            print(f"처음 10개 시간대: {times[:10]}")
            
            # 번호 패턴
            number_pattern = r'^\s*(\d{1,2})\s+'
            numbers = re.findall(number_pattern, full_text, re.MULTILINE)
            print(f"발견된 번호: {numbers[:20]}")
            
            # O/X 패턴
            ox_pattern = r'[OoXx]'
            ox_marks = re.findall(ox_pattern, full_text)
            print(f"O/X 마크 수: {len(ox_marks)}")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    test_pdf_parsing(pdf_path)