#!/usr/bin/env python3
"""
PDF 테스트 스크립트
"""

import os
import sys
from pdf_processor import process_pdf_file

# Downloads 폴더의 PDF 파일 찾기
downloads_path = "/Users/choejinmyung/Downloads"
pdf_files = []

for file in os.listdir(downloads_path):
    if file.endswith('.pdf'):
        pdf_files.append(os.path.join(downloads_path, file))

print("=" * 60)
print("📄 PDF 파일 목록")
print("=" * 60)

for i, pdf in enumerate(pdf_files[:10], 1):
    filename = os.path.basename(pdf)
    print(f"{i}. {filename}")

print("\n테스트할 PDF 파일 번호를 입력하세요 (1-10): ", end="")
try:
    choice = int(input())
    if 1 <= choice <= len(pdf_files):
        selected_pdf = pdf_files[choice - 1]
        print(f"\n선택된 파일: {os.path.basename(selected_pdf)}")
        print("\n분석 중...")
        
        result = process_pdf_file(selected_pdf)
        
        print("\n" + "=" * 60)
        print("📊 PDF 분석 결과")
        print("=" * 60)
        
        for key, value in result.items():
            print(f"• {key}: {value}")
        
        print("=" * 60)
    else:
        print("잘못된 선택입니다.")
except Exception as e:
    print(f"오류 발생: {e}")