"""
체크마크 파싱 수정 스크립트
Wingdings2 폰트의 U+F050 문자를 체크마크로 인식
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pdfplumber
import re

def parse_pdf_with_checkmark_fix(pdf_path):
    """수정된 PDF 파싱"""
    
    print("="*60)
    print("체크마크 인식 개선 파싱")
    print("="*60)
    
    # Wingdings2 체크마크 문자
    WINGDINGS_CHECK = '\uf050'  # U+F050
    
    teams = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_team = None
            
            for page in pdf.pages:
                text = page.extract_text()
                
                # 팀 정보 추출
                if "팀명" in text and "대표자명" in text:
                    # 팀명 추출
                    team_match = re.search(r'팀명\s+([^\s]+)\s+대표자명', text)
                    if team_match:
                        team_name = team_match.group(1)
                        
                        # 이메일 추출
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                        email = email_match.group(1) if email_match else ""
                        
                        current_team = {
                            'name': team_name,
                            'email': email,
                            'time_slots': []
                        }
                        teams.append(current_team)
                
                # 시간대 정보 추출
                if "[인터뷰 가능 시간대]" in text and current_team:
                    print(f"\n팀: {current_team['name']}")
                    print("-"*40)
                    
                    # 테이블 추출
                    tables = page.extract_tables()
                    
                    slot_number = 1
                    for table in tables:
                        for row in table:
                            # 시간대 패턴 찾기
                            time_pattern = r'(\d{1,2}:\d{2}~\d{1,2}:\d{2})'
                            
                            for cell in row:
                                if cell and re.search(time_pattern, str(cell)):
                                    time_match = re.search(time_pattern, str(cell))
                                    if time_match:
                                        time_slot = time_match.group(1)
                                        
                                        # 체크마크 확인
                                        has_checkmark = False
                                        
                                        # 같은 행에서 체크마크 찾기
                                        for check_cell in row:
                                            if check_cell:
                                                # Wingdings2 체크마크 확인
                                                if WINGDINGS_CHECK in str(check_cell):
                                                    has_checkmark = True
                                                    break
                                                # 일반 O/X 마크 확인
                                                if 'O' in str(check_cell).upper() or '○' in str(check_cell):
                                                    has_checkmark = True
                                                    break
                                        
                                        current_team['time_slots'].append({
                                            'number': slot_number,
                                            'time': time_slot,
                                            'available': has_checkmark
                                        })
                                        
                                        status = "✅ 가능" if has_checkmark else "❌ 불가능"
                                        print(f"  슬롯 {slot_number:2d}: {time_slot} → {status}")
                                        
                                        slot_number += 1
            
            # 결과 요약
            print("\n" + "="*60)
            print("파싱 결과 요약")
            print("="*60)
            
            for team in teams:
                available_count = sum(1 for slot in team['time_slots'] if slot['available'])
                total_count = len(team['time_slots'])
                
                print(f"\n팀: {team['name']}")
                print(f"  이메일: {team['email']}")
                print(f"  전체 시간대: {total_count}개")
                print(f"  가능한 시간대: {available_count}개")
                print(f"  불가능한 시간대: {total_count - available_count}개")
                
                if available_count > 0:
                    print(f"  가능한 시간대 목록:")
                    for slot in team['time_slots']:
                        if slot['available']:
                            print(f"    - 슬롯 {slot['number']}: {slot['time']}")
            
            return teams
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    teams = parse_pdf_with_checkmark_fix(pdf_path)