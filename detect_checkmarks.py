"""
PDF에서 체크마크 이모티콘 감지 스크립트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pdfplumber
import fitz  # PyMuPDF
import re
from collections import Counter

def detect_checkmarks(pdf_path):
    """PDF에서 체크마크 감지"""
    
    print("="*60)
    print("PDF 체크마크 감지")
    print("="*60)
    
    # 1. pdfplumber로 텍스트와 문자 추출
    print("\n1. pdfplumber로 텍스트 추출:")
    print("-"*40)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                if page_num > 5:  # 처음 5페이지만 검사
                    break
                    
                # 텍스트 추출
                text = page.extract_text()
                
                # 체크마크가 있을 만한 부분 찾기
                if "[인터뷰 가능 시간대]" in text or "시간대" in text:
                    print(f"\n페이지 {page_num}에서 시간대 섹션 발견")
                    
                    # 원시 문자 추출
                    chars = page.chars
                    
                    # 특수 문자 찾기
                    special_chars = []
                    for char in chars:
                        ch = char.get('text', '')
                        # ASCII가 아닌 문자 중 한글이 아닌 것
                        if ch and not ch.isascii() and not ('가' <= ch <= '힣'):
                            special_chars.append({
                                'char': ch,
                                'unicode': ord(ch),
                                'hex': hex(ord(ch)),
                                'x': char.get('x0'),
                                'y': char.get('top'),
                                'fontname': char.get('fontname', '')
                            })
                    
                    if special_chars:
                        print(f"  특수 문자 발견: {len(special_chars)}개")
                        # 빈도 분석
                        char_counter = Counter([c['char'] for c in special_chars])
                        for char, count in char_counter.most_common(10):
                            print(f"    '{char}' (U+{ord(char):04X}): {count}회")
                    
                    # 테이블 추출
                    tables = page.extract_tables()
                    if tables:
                        print(f"  테이블 발견: {len(tables)}개")
                        for t_idx, table in enumerate(tables):
                            print(f"    테이블 {t_idx+1}: {len(table)}행")
                            # 처음 몇 행만 출력
                            for row in table[:5]:
                                if row:
                                    # 각 셀의 내용과 특수문자 확인
                                    for cell in row:
                                        if cell and not cell.isascii():
                                            print(f"      셀: {repr(cell)}")
                                            for ch in cell:
                                                if not ch.isascii() and not ('가' <= ch <= '힣'):
                                                    print(f"        → '{ch}' (U+{ord(ch):04X})")
                    
    except Exception as e:
        print(f"pdfplumber 오류: {e}")
    
    # 2. PyMuPDF(fitz)로 추출
    print("\n\n2. PyMuPDF로 텍스트 추출:")
    print("-"*40)
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            
            if "[인터뷰 가능 시간대]" in text or "시간대" in text:
                print(f"\n페이지 {page_num+1}:")
                
                # 텍스트 블록 추출
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # 텍스트 블록
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                
                                # 시간대 패턴 근처의 텍스트 확인
                                if re.search(r'\d{1,2}:\d{2}', text):
                                    # 특수 문자 확인
                                    for ch in text:
                                        if not ch.isascii() and not ('가' <= ch <= '힣') and not ch.isspace():
                                            print(f"  시간대 근처 특수문자: '{ch}' (U+{ord(ch):04X})")
                                            print(f"    전체 텍스트: {repr(text)}")
                                            break
                
                # 폰트 정보 확인
                fonts = page.get_fonts()
                if fonts:
                    print(f"  사용된 폰트:")
                    for font in fonts[:5]:
                        print(f"    {font}")
        
        doc.close()
        
    except Exception as e:
        print(f"PyMuPDF 오류: {e}")
    
    # 3. 바이너리 레벨에서 체크마크 패턴 찾기
    print("\n\n3. 체크마크 유니코드 패턴 검색:")
    print("-"*40)
    
    # 가능한 체크마크 유니코드
    checkmarks = [
        ('✓', 0x2713, 'CHECK MARK'),
        ('✔', 0x2714, 'HEAVY CHECK MARK'),
        ('☑', 0x2611, 'BALLOT BOX WITH CHECK'),
        ('☒', 0x2612, 'BALLOT BOX WITH X'),
        ('✅', 0x2705, 'WHITE HEAVY CHECK MARK'),
        ('❌', 0x274C, 'CROSS MARK'),
        ('⭕', 0x2B55, 'HEAVY LARGE CIRCLE'),
        ('○', 0x25CB, 'WHITE CIRCLE'),
        ('●', 0x25CF, 'BLACK CIRCLE'),
        ('◯', 0x25EF, 'LARGE CIRCLE'),
        ('◉', 0x25C9, 'FISHEYE'),
        ('◎', 0x25CE, 'BULLSEYE'),
        ('Ｏ', 0xFF2F, 'FULLWIDTH LATIN CAPITAL LETTER O'),
        ('ｏ', 0xFF4F, 'FULLWIDTH LATIN SMALL LETTER O'),
        ('〇', 0x3007, 'IDEOGRAPHIC NUMBER ZERO'),
    ]
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text
            
            print("발견된 체크마크 패턴:")
            for mark, code, name in checkmarks:
                count = full_text.count(mark)
                if count > 0:
                    print(f"  {mark} (U+{code:04X} {name}): {count}개")
            
            # 깨진 문자 패턴 찾기
            print("\n깨진 문자 패턴 (�, ?, □ 등):")
            broken_patterns = ['�', '?', '□', '■', '▢', '▣', '\ufffd', '\x00']
            for pattern in broken_patterns:
                count = full_text.count(pattern)
                if count > 0:
                    print(f"  '{pattern}' (U+{ord(pattern):04X}): {count}개")
                    
    except Exception as e:
        print(f"패턴 검색 오류: {e}")

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    detect_checkmarks(pdf_path)