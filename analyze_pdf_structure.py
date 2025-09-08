"""
PDF 구조 상세 분석
"""

import pdfplumber
import re

def analyze_pdf_structure(pdf_path):
    """PDF 구조 분석"""
    
    print("="*60)
    print("PDF 구조 상세 분석")
    print("="*60)
    
    WINGDINGS_CHECK = '\uf050'
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            # 페이지 4-5만 분석 (시간대 정보가 있는 페이지)
            if page_num in [4, 5]:
                print(f"\n페이지 {page_num}:")
                print("-"*40)
                
                # 텍스트의 처음 부분 출력
                lines = text.split('\n')
                for i, line in enumerate(lines[:40]):
                    # Wingdings 체크마크 포함 여부 확인
                    if WINGDINGS_CHECK in line:
                        print(f"{i:3d}: {repr(line)} ← 체크마크 발견!")
                    elif re.search(r'\d{1,2}:\d{2}~\d{1,2}:\d{2}', line):
                        print(f"{i:3d}: {repr(line)} ← 시간대")
                    elif re.search(r'^\d{1,2}\s', line):
                        print(f"{i:3d}: {repr(line)} ← 번호")
                    else:
                        print(f"{i:3d}: {line[:50]}")
                
                # 테이블 구조 분석
                print("\n테이블 구조:")
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    print(f"\n테이블 {t_idx+1} ({len(table)}행 x {len(table[0]) if table else 0}열):")
                    for r_idx, row in enumerate(table[:20]):  # 처음 20행만
                        row_str = " | ".join([str(cell)[:20] if cell else "---" for cell in row])
                        
                        # 체크마크가 있는 행 강조
                        if any(WINGDINGS_CHECK in str(cell) for cell in row if cell):
                            print(f"  행{r_idx:2d}: {row_str} ← ✓")
                        else:
                            print(f"  행{r_idx:2d}: {row_str}")

if __name__ == "__main__":
    pdf_path = "/Users/choejinmyung/Downloads/27.pdf"
    analyze_pdf_structure(pdf_path)