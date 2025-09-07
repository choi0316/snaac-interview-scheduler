"""
parsing_test5.pdf 파싱 테스트
"""

import pdfplumber
import re
from typing import Dict, List, Tuple

def extract_time_slots_perfect(text: str) -> Dict[str, List[Tuple[str, bool]]]:
    """완벽한 파싱 로직"""
    slots = {"9/12": [], "9/13": [], "9/14": []}
    
    # 슬롯 매핑
    slot_mapping = {
        # 금요일 (9/12): 슬롯 1-4
        1: ("9/12", "19:00-19:45"), 2: ("9/12", "19:45-20:30"), 
        3: ("9/12", "20:30-21:15"), 4: ("9/12", "21:15-22:00"),
        # 토요일 (9/13): 슬롯 5-20
        5: ("9/13", "10:00-10:45"), 6: ("9/13", "10:45-11:30"), 7: ("9/13", "11:30-12:15"), 8: ("9/13", "12:15-13:00"),
        9: ("9/13", "13:00-13:45"), 10: ("9/13", "13:45-14:30"), 11: ("9/13", "14:30-15:15"), 12: ("9/13", "15:15-16:00"),
        13: ("9/13", "16:00-16:45"), 14: ("9/13", "16:45-17:30"), 15: ("9/13", "17:30-18:15"), 16: ("9/13", "18:15-19:00"),
        17: ("9/13", "19:00-19:45"), 18: ("9/13", "19:45-20:30"), 19: ("9/13", "20:30-21:15"), 20: ("9/13", "21:15-22:00"),
        # 일요일 (9/14): 슬롯 21-36
        21: ("9/14", "10:00-10:45"), 22: ("9/14", "10:45-11:30"), 23: ("9/14", "11:30-12:15"), 24: ("9/14", "12:15-13:00"),
        25: ("9/14", "13:00-13:45"), 26: ("9/14", "13:45-14:30"), 27: ("9/14", "14:30-15:15"), 28: ("9/14", "15:15-16:00"),
        29: ("9/14", "16:00-16:45"), 30: ("9/14", "16:45-17:30"), 31: ("9/14", "17:30-18:15"), 32: ("9/14", "18:15-19:00"),
        33: ("9/14", "19:00-19:45"), 34: ("9/14", "19:45-20:30"), 35: ("9/14", "20:30-21:15"), 36: ("9/14", "21:15-22:00"),
    }
    
    print("🔧 parsing_test5.pdf 파싱 시작\n")
    
    lines = text.split('\n')
    
    # 인터뷰 섹션 찾기
    interview_section_start = -1
    for i, line in enumerate(lines):
        if '인터뷰' in line and '가능' in line and '시간' in line:
            interview_section_start = i
            break
    
    if interview_section_start >= 0:
        print(f"✅ 인터뷰 섹션 발견: {interview_section_start}번째 줄\n")
        
        # 패턴별로 처리
        i = interview_section_start
        processed_slots = []
        
        while i < min(interview_section_start + 100, len(lines)):
            line = lines[i].strip()
            
            # 패턴 1: "1 19:00~19:45 O" (번호 시간 표시)
            pattern1 = r'^(\d{1,2})\s+(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})\s*(.*)$'
            match1 = re.match(pattern1, line)
            
            # 패턴 2: "26 9/14 (일)" (번호와 날짜만, 다음 줄에 시간)
            pattern2 = r'^(\d{1,2})\s+9/1[2-4]\s*\([월화수목금토일]\)\s*$'
            match2 = re.match(pattern2, line)
            
            # 패턴 3: "1" (번호만)
            pattern3 = r'^(\d{1,2})\s*$'
            match3 = re.match(pattern3, line)
            
            if match1:
                # 일반 패턴: 번호 시간 표시
                slot_num = int(match1.group(1))
                time_str = match1.group(2).replace('~', '-').replace('～', '-')
                mark = match1.group(3).strip()
                
                # 날짜 부분 제거 (만약 있다면)
                mark = re.sub(r'9/1[2-4]\s*\([월화수목금토일]\)', '', mark).strip()
                
                if slot_num in slot_mapping:
                    date, expected_time = slot_mapping[slot_num]
                    is_available = bool(mark and mark not in ['', ' '])
                    
                    processed_slots.append(slot_num)
                    print(f"슬롯 #{slot_num}: {expected_time} {'✅' if is_available else '❌'} (표시: '{mark}')")
                    
                    if is_available:
                        slots[date].append((expected_time, True))
                
                i += 1
                
            elif match2:
                # 특수 패턴: "26 9/14 (일)" - 다음 줄에 시간
                slot_num = int(match2.group(1))
                
                # 다음 줄에서 시간 찾기
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    time_pattern = r'(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})\s*(.*)$'
                    time_match = re.match(time_pattern, next_line)
                    
                    if time_match:
                        time_str = time_match.group(1).replace('~', '-').replace('～', '-')
                        mark = time_match.group(2).strip() if time_match.lastindex >= 2 else ''
                        
                        if slot_num in slot_mapping:
                            date, expected_time = slot_mapping[slot_num]
                            is_available = bool(mark and mark not in ['', ' '])
                            
                            processed_slots.append(slot_num)
                            print(f"슬롯 #{slot_num}: {expected_time} {'✅' if is_available else '❌'} (특수패턴, 표시: '{mark}')")
                            
                            if is_available:
                                slots[date].append((expected_time, True))
                        
                        i += 2  # 두 줄 처리했으므로
                    else:
                        i += 1
                else:
                    i += 1
                    
            elif match3:
                # 번호만 있는 경우
                slot_num = int(match3.group(1))
                
                # 다음 줄 확인
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # 다음 줄이 시간인지 확인
                    time_pattern = r'(\d{1,2}:\d{2}[~\-～]\d{1,2}:\d{2})\s*(.*)$'
                    time_match = re.match(time_pattern, next_line)
                    
                    if time_match:
                        time_str = time_match.group(1).replace('~', '-').replace('～', '-')
                        mark = time_match.group(2).strip() if time_match.lastindex >= 2 else ''
                        
                        if slot_num in slot_mapping:
                            date, expected_time = slot_mapping[slot_num]
                            is_available = bool(mark and mark not in ['', ' '])
                            
                            processed_slots.append(slot_num)
                            print(f"슬롯 #{slot_num}: {expected_time} {'✅' if is_available else '❌'} (분리패턴, 표시: '{mark}')")
                            
                            if is_available:
                                slots[date].append((expected_time, True))
                        
                        i += 2  # 두 줄 처리
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        # 처리되지 않은 슬롯 확인
        print("\n📋 미처리 슬롯 확인:")
        for slot_num in range(1, 37):
            if slot_num not in processed_slots:
                print(f"  슬롯 #{slot_num}: 파싱되지 않음")
    
    total = sum(len(day_slots) for day_slots in slots.values())
    print(f"\n📊 파싱 결과: {total}/36 슬롯")
    
    for date in ["9/12", "9/13", "9/14"]:
        count = len(slots[date])
        print(f"  {date}: {count}개")
    
    return slots

def test_parsing_test5():
    """parsing_test5.pdf 테스트"""
    from improved_pdf_processor import ImprovedPDFProcessor
    
    # PDF 텍스트 추출
    print("=" * 70)
    print("🎯 parsing_test5.pdf 파싱 테스트")
    print("=" * 70)
    
    try:
        with pdfplumber.open('/Users/choejinmyung/Downloads/parsing_test5.pdf') as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # PDF 구조 확인
            print("\n📄 PDF 구조 확인:")
            lines = full_text.split('\n')
            
            # 인터뷰 섹션 찾기
            for i, line in enumerate(lines):
                if '인터뷰' in line or '면접' in line:
                    print(f"  {i}: {line[:50]}...")
                    # 주변 몇 줄 표시
                    for j in range(max(0, i), min(i+10, len(lines))):
                        if re.search(r'\d{1,2}:\d{2}', lines[j]):
                            print(f"    {j}: {lines[j][:60]}...")
                    break
        
        # 원본 파싱
        print("\n1️⃣ 원본 파싱:")
        processor = ImprovedPDFProcessor()
        original_slots = processor._extract_time_slots(full_text)
        original_count = sum(len(day_slots) for day_slots in original_slots.values())
        print(f"결과: {original_count}/36 슬롯")
        
        # 완벽한 파싱
        print("\n2️⃣ 개선된 파싱:")
        perfect_slots = extract_time_slots_perfect(full_text)
        perfect_count = sum(len(day_slots) for day_slots in perfect_slots.values())
        
        print("\n📊 비교 결과:")
        print(f"원본 파싱: {original_count}/36 슬롯")
        print(f"개선 파싱: {perfect_count}/36 슬롯")
        print(f"개선도:    +{perfect_count - original_count} 슬롯")
        
        # 상세 분석
        if perfect_count > 0:
            print("\n✅ 체크된 시간대:")
            for date in ["9/12", "9/13", "9/14"]:
                if slots[date]:
                    print(f"  {date}:")
                    for time, _ in perfect_slots[date]:
                        print(f"    - {time}")
        
    except FileNotFoundError:
        print("\n❌ 파일을 찾을 수 없습니다: /Users/choejinmyung/Downloads/parsing_test5.pdf")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_parsing_test5()