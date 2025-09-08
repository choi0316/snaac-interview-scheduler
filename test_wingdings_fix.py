"""
Wingdings2 체크마크 수정 테스트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.pdf_extractor import PDFExtractor

def test_wingdings_parsing():
    """수정된 파서 테스트"""
    
    print("="*60)
    print("Wingdings2 체크마크 파싱 테스트")
    print("="*60)
    
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    extractor = PDFExtractor()
    
    # 새로운 메소드로 추출
    result = extractor.extract_interview_availability(pdf_path)
    
    print(f"\n팀 정보:")
    print(f"  팀명: {result['team_info'].get('name', 'N/A')}")
    print(f"  이메일: {result['team_info'].get('email', 'N/A')}")
    
    print(f"\n시간대 정보:")
    print(f"  전체 시간대: {len(result['time_slots'])}개")
    
    available = [s for s in result['time_slots'] if s['available']]
    unavailable = [s for s in result['time_slots'] if not s['available']]
    
    print(f"  가능한 시간대: {len(available)}개")
    print(f"  불가능한 시간대: {len(unavailable)}개")
    
    if available:
        print(f"\n가능한 시간대 목록:")
        for slot in available:
            print(f"  슬롯 {slot['number']:2d}: {slot['time']}")
    
    # 예상 결과와 비교
    expected_available_slots = list(range(23, 37))  # 23-36번
    actual_available_slots = [s['number'] for s in available]
    
    print(f"\n검증 결과:")
    print(f"  예상: 슬롯 {expected_available_slots[0]}-{expected_available_slots[-1]}번")
    print(f"  실제: 슬롯 {actual_available_slots[0] if actual_available_slots else 'N/A'}-{actual_available_slots[-1] if actual_available_slots else 'N/A'}번")
    
    if actual_available_slots == expected_available_slots:
        print("  ✅ 파싱 성공!")
    else:
        print("  ❌ 파싱 결과가 예상과 다름")

if __name__ == "__main__":
    test_wingdings_parsing()