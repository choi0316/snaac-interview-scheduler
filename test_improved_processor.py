"""
improved_pdf_processor.py의 Wingdings2 체크마크 파싱 테스트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from improved_pdf_processor import ImprovedPDFProcessor

def test_improved_processor():
    """개선된 프로세서 테스트"""
    
    print("="*60)
    print("improved_pdf_processor.py Wingdings2 체크마크 테스트")
    print("="*60)
    
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    processor = ImprovedPDFProcessor()
    
    # PDF 파싱
    team_info = processor.extract_from_pdf(pdf_path)
    
    print(f"\n팀 정보:")
    print(f"  팀명: {team_info.team_name}")
    print(f"  대표자명: {team_info.representative_name}")
    print(f"  이메일: {team_info.email}")
    print(f"  전화번호: {team_info.phone}")
    
    print(f"\n시간대 정보:")
    total_slots = 0
    available_slots = 0
    
    for date, slots in team_info.available_slots.items():
        date_available = sum(1 for _, available in slots if available)
        date_total = len(slots)
        total_slots += date_total
        available_slots += date_available
        
        print(f"  {date}: {date_available}/{date_total} 가능")
        
        if date_available > 0:
            print(f"    가능한 시간대:")
            for time, available in slots:
                if available:
                    print(f"      - {time}")
    
    print(f"\n전체 통계:")
    print(f"  전체 시간대: {total_slots}개")
    print(f"  가능한 시간대: {available_slots}개")
    print(f"  불가능한 시간대: {total_slots - available_slots}개")
    
    # 예상 결과와 비교 (슬롯 23-36이 체크되어 있어야 함)
    # 9/14의 11:30-12:15부터 22:00까지 14개 슬롯
    expected_available = 14
    
    print(f"\n검증 결과:")
    print(f"  예상 가능 시간대: {expected_available}개")
    print(f"  실제 가능 시간대: {available_slots}개")
    
    if available_slots == expected_available:
        print("  ✅ Wingdings2 체크마크 파싱 성공!")
    else:
        print(f"  ❌ 파싱 결과가 예상과 다름 (차이: {abs(available_slots - expected_available)}개)")

if __name__ == "__main__":
    test_improved_processor()