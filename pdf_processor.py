"""
PDF 처리 전용 모듈
한국어 PDF에서 팀 정보 추출
"""

import pdfplumber
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TeamInfo:
    """팀 정보 데이터 클래스"""
    team_name: str = ""
    representative_name: str = ""
    email: str = ""
    phone: str = ""
    available_times: List[str] = None
    
    def __post_init__(self):
        if self.available_times is None:
            self.available_times = []

class PDFProcessor:
    """PDF 처리 클래스"""
    
    def __init__(self):
        self.patterns = {
            'team_name': [
                r'팀\s*명\s*[:：]\s*([^\n]+)',
                r'팀명\s*[:：]\s*([^\n]+)',
                r'프로젝트\s*명\s*[:：]\s*([^\n]+)',
                r'서비스\s*명\s*[:：]\s*([^\n]+)',
                r'사업\s*명\s*[:：]\s*([^\n]+)',
            ],
            'representative': [
                r'대표자\s*[:：]\s*([^\n]+)',
                r'대표\s*[:：]\s*([^\n]+)',
                r'팀장\s*[:：]\s*([^\n]+)',
                r'리더\s*[:：]\s*([^\n]+)',
                r'성명\s*[:：]\s*([^\n]+)',
                r'이름\s*[:：]\s*([^\n]+)',
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'이메일\s*[:：]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'E-mail\s*[:：]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            ],
            'phone': [
                r'010[-\s]?\d{4}[-\s]?\d{4}',
                r'연락처\s*[:：]\s*(010[-\s]?\d{4}[-\s]?\d{4})',
                r'전화\s*[:：]\s*(010[-\s]?\d{4}[-\s]?\d{4})',
                r'휴대폰\s*[:：]\s*(010[-\s]?\d{4}[-\s]?\d{4})',
            ],
            'time': [
                r'(\d{1,2}시)',
                r'(\d{1,2}:\d{2})',
                r'(\d{1,2}시\s*\d{2}분)',
                r'오전\s*(\d{1,2}시)',
                r'오후\s*(\d{1,2}시)',
                r'면접\s*가능\s*시간[：:]\s*([^\n]+)',
                r'선호\s*시간[：:]\s*([^\n]+)',
                r'희망\s*시간[：:]\s*([^\n]+)',
            ]
        }
    
    def extract_from_pdf(self, pdf_path: str) -> TeamInfo:
        """PDF 파일에서 팀 정보 추출"""
        team_info = TeamInfo()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 모든 페이지의 텍스트 추출
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                # 팀명 추출
                team_info.team_name = self._extract_pattern(full_text, self.patterns['team_name'])
                
                # 대표자명 추출
                team_info.representative_name = self._extract_pattern(full_text, self.patterns['representative'])
                
                # 이메일 추출
                team_info.email = self._extract_pattern(full_text, self.patterns['email'])
                
                # 전화번호 추출
                team_info.phone = self._extract_pattern(full_text, self.patterns['phone'])
                
                # 면접 가능 시간 추출
                team_info.available_times = self._extract_times(full_text)
                
                # 팀명이 없으면 파일명에서 추출 시도
                if not team_info.team_name:
                    import os
                    filename = os.path.basename(pdf_path)
                    # 파일명에서 팀명 추출 시도
                    if '_' in filename:
                        parts = filename.split('_')
                        if len(parts) > 1:
                            team_info.team_name = parts[1].replace('.pdf', '')
                
        except Exception as e:
            print(f"PDF 처리 오류: {e}")
        
        return team_info
    
    def _extract_pattern(self, text: str, patterns: List[str]) -> str:
        """패턴 매칭으로 정보 추출"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                if len(match.groups()) > 0:
                    return match.group(1).strip()
                else:
                    return match.group(0).strip()
        return ""
    
    def _extract_times(self, text: str) -> List[str]:
        """면접 가능 시간 추출"""
        times = []
        
        # 먼저 '면접 가능 시간' 섹션 찾기
        time_section_pattern = r'면접\s*가능\s*시간[：:]\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\n|\n[가-힣]+\s*[:：]|\Z)'
        section_match = re.search(time_section_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if section_match:
            time_text = section_match.group(1)
        else:
            time_text = text
        
        # 시간 패턴 추출
        time_patterns = [
            r'\d{1,2}시',
            r'\d{1,2}:\d{2}',
            r'\d{1,2}시\s*\d{2}분',
            r'오전\s*\d{1,2}시',
            r'오후\s*\d{1,2}시',
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, time_text)
            times.extend(matches)
        
        # 중복 제거
        times = list(set(times))
        
        # 시간 형식 정규화
        normalized_times = []
        for time in times:
            # 오전/오후 처리
            if '오전' in time:
                time = time.replace('오전', '').strip()
            elif '오후' in time:
                hour = re.search(r'\d+', time)
                if hour:
                    hour_int = int(hour.group())
                    if hour_int < 12:
                        hour_int += 12
                    time = f"{hour_int}시"
            
            # 시간 형식 통일
            time = time.replace('시간', '시').replace(' ', '')
            normalized_times.append(time)
        
        return normalized_times[:5]  # 최대 5개까지만 반환

def process_pdf_file(file_path: str) -> Dict:
    """PDF 파일 처리 메인 함수"""
    processor = PDFProcessor()
    team_info = processor.extract_from_pdf(file_path)
    
    return {
        "팀명": team_info.team_name or "미확인",
        "대표자명": team_info.representative_name or "미확인",
        "이메일": team_info.email or "미확인",
        "전화번호": team_info.phone or "미확인",
        "면접 가능 시간": ", ".join(team_info.available_times) if team_info.available_times else "미확인"
    }

if __name__ == "__main__":
    # 테스트
    import sys
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        result = process_pdf_file(pdf_file)
        print("\n=== PDF 분석 결과 ===")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("사용법: python pdf_processor.py [PDF 파일 경로]")