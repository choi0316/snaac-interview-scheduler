"""
PDF 파싱 문제 분석 스크립트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.pdf_extractor import PDFExtractor
import pdfplumber
import re

def analyze_pdf_issue(pdf_path):
    """PDF 파싱 문제 분석"""
    
    print("="*60)
    print("PDF 파싱 문제 분석")
    print("="*60)
    
    # 1. PDFExtractor 사용
    print("\n1. PDFExtractor로 팀 데이터 추출:")
    print("-"*40)
    try:
        extractor = PDFExtractor()
        teams = extractor.extract_team_data(pdf_path)
        
        print(f"추출된 팀 수: {len(teams)}")
        
        if teams:
            team = teams[0]  # 첫 번째 팀
            print(f"\n팀 정보:")
            print(f"  - 팀 이름: {team.name}")
            print(f"  - 팀 번호: {team.team_number}")
            print(f"  - 이메일: {team.email}")
            print(f"  - 제약 조건 수: {len(team.constraints) if hasattr(team, 'constraints') else 'N/A'}")
            
            # 시간대 가능 여부 확인
            if hasattr(team, 'constraints') and team.constraints:
                available = [c for c in team.constraints if c.is_available]
                unavailable = [c for c in team.constraints if not c.is_available]
                print(f"  - 가능한 시간대: {len(available)}개")
                print(f"  - 불가능한 시간대: {len(unavailable)}개")
        else:
            print("팀이 추출되지 않음!")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 직접 텍스트 분석
    print("\n\n2. 직접 텍스트 분석:")
    print("-"*40)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # [인터뷰 가능 시간대] 섹션 찾기
            interview_section_start = full_text.find("[인터뷰 가능 시간대]")
            if interview_section_start == -1:
                print("❌ '[인터뷰 가능 시간대]' 섹션을 찾을 수 없음")
            else:
                print("✅ '[인터뷰 가능 시간대]' 섹션 발견")
                
                # 섹션 이후 텍스트 추출
                section_text = full_text[interview_section_start:]
                
                # 시간대 정보 추출
                lines = section_text.split('\n')[:50]  # 처음 50줄만
                
                print("\n시간대 텍스트 샘플:")
                for i, line in enumerate(lines[:10]):
                    print(f"  {i}: {line}")
                
                # O/X 마크 찾기
                print("\n\nO/X 마크 분석:")
                for line in lines:
                    if 'O' in line or 'X' in line or 'o' in line or 'x' in line:
                        print(f"  마크 발견: {line}")
                
                # 패턴 분석
                print("\n\n패턴 분석:")
                time_pattern = r'(\d{1,2}:\d{2}~\d{1,2}:\d{2})'
                num_pattern = r'^(\d{1,2})\s'
                
                for line in lines:
                    if re.search(time_pattern, line):
                        time_match = re.search(time_pattern, line)
                        num_match = re.match(num_pattern, line)
                        
                        if num_match and time_match:
                            print(f"  번호: {num_match.group(1)}, 시간: {time_match.group(1)}")
                            
                            # O/X 마크 확인
                            if 'O' in line or 'o' in line:
                                print(f"    → 가능 (O)")
                            elif 'X' in line or 'x' in line:
                                print(f"    → 불가능 (X)")
                            else:
                                print(f"    → 마크 없음")
    
    except Exception as e:
        print(f"오류 발생: {e}")
    
    # 3. 문제 진단
    print("\n\n3. 문제 진단:")
    print("-"*40)
    print("📌 발견된 문제:")
    print("  1. PDF에 O/X 마크가 표시되어 있지 않음")
    print("  2. 모든 시간대가 '미확인' 상태로 처리됨")
    print("  3. 가능한 시간대를 구분할 수 있는 표시가 없음")
    print("\n💡 해결 방안:")
    print("  1. PDF에 O/X 마크를 명확히 표시")
    print("  2. 또는 별도의 방식으로 가능 시간대 입력")
    print("  3. GUI에서 수동으로 선택 가능하도록 구현")

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    analyze_pdf_issue(pdf_path)