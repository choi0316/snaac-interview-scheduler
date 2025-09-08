"""
최종 해결책: Wingdings2 체크마크 인식
"""

import pdfplumber
import re

def parse_interview_slots(pdf_path):
    """인터뷰 가능 시간대 파싱"""
    
    print("="*60)
    print("인터뷰 가능 시간대 파싱 결과")
    print("="*60)
    
    WINGDINGS_CHECK = '\uf050'  # Wingdings2 체크마크
    
    # 팀 정보
    team_info = {
        'name': 'Read My Saju',
        'email': 'Parkjustin1019@gmail.com',
        'slots': []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        slot_number = 1
        
        for page_num, page in enumerate(pdf.pages, 1):
            # 페이지 4-5에 시간대 정보가 있음
            if page_num in [4, 5]:
                tables = page.extract_tables()
                
                for table in tables:
                    for row in table:
                        # 시간대 찾기
                        time_slot = None
                        has_check = False
                        
                        for cell in row:
                            if cell:
                                # 시간대 패턴
                                time_match = re.search(r'(\d{1,2}:\d{2}~\d{1,2}:\d{2})', str(cell))
                                if time_match:
                                    time_slot = time_match.group(1)
                                
                                # 체크마크 확인
                                if WINGDINGS_CHECK in str(cell):
                                    has_check = True
                        
                        # 시간대가 있으면 저장
                        if time_slot:
                            team_info['slots'].append({
                                'number': slot_number,
                                'time': time_slot,
                                'available': has_check
                            })
                            slot_number += 1
    
    # 결과 출력
    print(f"\n팀명: {team_info['name']}")
    print(f"이메일: {team_info['email']}")
    print(f"\n총 {len(team_info['slots'])}개 시간대 중:")
    
    available_slots = [s for s in team_info['slots'] if s['available']]
    unavailable_slots = [s for s in team_info['slots'] if not s['available']]
    
    print(f"  - 가능: {len(available_slots)}개")
    print(f"  - 불가능: {len(unavailable_slots)}개")
    
    print(f"\n가능한 시간대 (체크마크 있음):")
    for slot in available_slots:
        print(f"  슬롯 {slot['number']:2d}: {slot['time']}")
    
    print(f"\n불가능한 시간대 (체크마크 없음):")
    for slot in unavailable_slots[:10]:  # 처음 10개만 표시
        print(f"  슬롯 {slot['number']:2d}: {slot['time']}")
    if len(unavailable_slots) > 10:
        print(f"  ... 외 {len(unavailable_slots)-10}개")
    
    return team_info

def create_fixed_parser():
    """수정된 파서 생성"""
    
    code = '''
# core/pdf_extractor.py에 추가할 코드

# Wingdings2 체크마크 문자 상수 추가
WINGDINGS_CHECK = '\\uf050'  # U+F050

# _parse_availability_marks 메소드 수정
def _parse_availability_marks(self, text: str, slot_count: int) -> List[bool]:
    """가능 여부 마크 파싱 - Wingdings2 체크마크 지원"""
    marks = []
    
    # 기존 O/X 패턴
    ox_pattern = r'[OoXx○●◯◉]'
    
    # Wingdings2 체크마크 패턴 추가
    if WINGDINGS_CHECK in text:
        # Wingdings 체크마크가 있는 경우
        lines = text.split('\\n')
        for line in lines:
            if WINGDINGS_CHECK in line:
                marks.append(True)  # 체크마크 = 가능
            elif re.search(r'\\d{1,2}:\\d{2}~\\d{1,2}:\\d{2}', line):
                # 시간대는 있지만 체크마크가 없는 경우
                if WINGDINGS_CHECK not in line:
                    marks.append(False)  # 체크마크 없음 = 불가능
    else:
        # 기존 O/X 패턴 처리
        ox_matches = re.findall(ox_pattern, text)
        for match in ox_matches:
            if match.upper() in ['O', '○', '◯']:
                marks.append(True)
            elif match.upper() == 'X':
                marks.append(False)
    
    # 마크 수가 부족하면 False로 채우기
    while len(marks) < slot_count:
        marks.append(False)
    
    return marks[:slot_count]
'''
    
    print("\n" + "="*60)
    print("파서 수정 코드")
    print("="*60)
    print(code)

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    
    # 현재 상태 파싱
    team_info = parse_interview_slots(pdf_path)
    
    # 수정 코드 제공
    create_fixed_parser()