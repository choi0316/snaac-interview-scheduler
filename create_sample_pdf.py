#!/usr/bin/env python3
"""
샘플 PDF 생성 스크립트
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import os

# 폰트 경로 설정
font_paths = [
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NanumGothic.ttf",
]

# 사용 가능한 폰트 찾기
font_registered = False
for font_path in font_paths:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Korean', font_path))
            font_registered = True
            break
        except:
            continue

def create_sample_pdf():
    """샘플 PDF 생성"""
    
    # PDF 파일 경로
    pdf_path = "/Users/choejinmyung/Downloads/1_필리데이_권준범_지원서.pdf"
    
    # Canvas 생성
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # 폰트 설정
    if font_registered:
        c.setFont('Korean', 12)
    else:
        c.setFont('Helvetica', 12)
    
    # 제목
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, height - 2*cm, "Team Application Form")
    
    # 팀 정보
    y_pos = height - 4*cm
    c.setFont('Helvetica', 12)
    
    # 팀명
    c.drawString(2*cm, y_pos, "Team Name: Philliday")
    y_pos -= 0.8*cm
    
    if font_registered:
        c.setFont('Korean', 12)
        c.drawString(2*cm, y_pos, "팀명: 필리데이")
        y_pos -= 0.8*cm
    
    # 대표자명
    c.setFont('Helvetica', 12)
    c.drawString(2*cm, y_pos, "Representative: Kwon Jun Beom")
    y_pos -= 0.8*cm
    
    if font_registered:
        c.setFont('Korean', 12)
        c.drawString(2*cm, y_pos, "대표자: 권준범")
        y_pos -= 0.8*cm
    
    # 이메일
    c.setFont('Helvetica', 12)
    c.drawString(2*cm, y_pos, "Email: kjb@philliday.com")
    y_pos -= 0.8*cm
    
    # 전화번호
    c.drawString(2*cm, y_pos, "Phone: 010-1234-5678")
    y_pos -= 0.8*cm
    
    if font_registered:
        c.setFont('Korean', 12)
        c.drawString(2*cm, y_pos, "전화번호: 010-1234-5678")
        y_pos -= 0.8*cm
    
    # 면접 가능 시간
    c.setFont('Helvetica-Bold', 12)
    c.drawString(2*cm, y_pos, "Available Interview Times:")
    y_pos -= 0.8*cm
    
    if font_registered:
        c.setFont('Korean', 12)
        c.drawString(2*cm, y_pos, "면접 가능 시간:")
        y_pos -= 0.8*cm
        c.drawString(3*cm, y_pos, "- 오전 10시")
        y_pos -= 0.6*cm
        c.drawString(3*cm, y_pos, "- 오후 2시")
        y_pos -= 0.6*cm
        c.drawString(3*cm, y_pos, "- 오후 4시")
    else:
        c.setFont('Helvetica', 12)
        c.drawString(3*cm, y_pos, "- 10:00 AM")
        y_pos -= 0.6*cm
        c.drawString(3*cm, y_pos, "- 2:00 PM")
        y_pos -= 0.6*cm
        c.drawString(3*cm, y_pos, "- 4:00 PM")
    
    # PDF 저장
    c.save()
    
    print(f"✅ PDF 생성 완료: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    pdf_file = create_sample_pdf()
    print(f"샘플 PDF가 생성되었습니다: {pdf_file}")