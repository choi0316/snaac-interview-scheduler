"""
69.pdf 체크마크 문자 분석
"""

import pdfplumber
import unicodedata

def analyze_checkmarks(pdf_path):
    """PDF에서 체크마크 문자 분석"""
    
    print(f"="*60)
    print(f"PDF 분석: {pdf_path}")
    print(f"="*60)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                print(f"\n페이지 {page_num} 텍스트 (처음 1000자):")
                print(text[:1000])
                
                # 인터뷰 가능 시간대 섹션 찾기
                if '인터뷰' in text and '가능' in text:
                    print("\n[인터뷰 가능 시간대] 섹션 발견!")
                    
                    # 시간대 라인 추출
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if '19:00~19:45' in line or '19:45~20:30' in line or '20:30~21:15' in line or '21:15~22:00' in line:
                            print(f"\n시간대 라인 {i}: {line}")
                            
                            # 각 문자 분석
                            print("문자 분석:")
                            for j, char in enumerate(line):
                                if char not in '0123456789:~- \t\n금토일월화수목()/' and not char.isalnum():
                                    try:
                                        name = unicodedata.name(char)
                                        print(f"  위치 {j}: '{char}' -> Unicode: U+{ord(char):04X}, Name: {name}")
                                    except:
                                        print(f"  위치 {j}: '{char}' -> Unicode: U+{ord(char):04X}, Name: Unknown")
                            
                            # 다음 줄도 확인
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                if any(char not in '0123456789:~- \t\n금토일월화수목()/' and not char.isalnum() for char in next_line):
                                    print(f"  다음 줄: {next_line}")
                                    for j, char in enumerate(next_line):
                                        if char not in '0123456789:~- \t\n금토일월화수목()/' and not char.isalnum():
                                            try:
                                                name = unicodedata.name(char)
                                                print(f"    위치 {j}: '{char}' -> Unicode: U+{ord(char):04X}, Name: {name}")
                                            except:
                                                print(f"    위치 {j}: '{char}' -> Unicode: U+{ord(char):04X}, Name: Unknown")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    analyze_checkmarks("/Users/choejinmyung/Downloads/69.pdf")