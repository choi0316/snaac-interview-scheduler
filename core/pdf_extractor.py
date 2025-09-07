"""
PDF 데이터 추출 모듈 - 한글 텍스트 지원 최적화

공모전 합격자 명단 PDF에서 팀 정보를 추출하는 모듈입니다.
한글 텍스트 처리, 이메일 추출, 시간 선호도 파싱을 지원합니다.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
from dataclasses import dataclass

from .models import Team, TeamMember, ValidationStatus

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """PDF 추출 설정"""
    encoding: str = 'utf-8'
    extract_words: bool = True
    keep_blank_chars: bool = True
    word_sep_re: str = r'[\s\u3000]+'  # 한글 공백 포함
    line_margin: float = 0.5
    char_margin: float = 2.0
    min_confidence: float = 0.8


class PDFExtractor:
    """PDF 데이터 추출기 - 한글 최적화"""
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        
        # 정규표현식 패턴들
        self.patterns = {
            # 이메일 패턴 (한글 도메인 지원)
            'email': re.compile(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z가-힣]{2,}',
                re.IGNORECASE | re.UNICODE
            ),
            
            # 전화번호 패턴
            'phone': re.compile(
                r'(?:01[0-9]|02|0[3-9][0-9]?)[-\s]?\d{3,4}[-\s]?\d{4}',
                re.UNICODE
            ),
            
            # 팀명 패턴
            'team_name': re.compile(
                r'(?:팀명|팀\s*명|Team\s*Name)[:：\s]*([가-힣a-zA-Z0-9\s\-_]+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # 시간 선호도 패턴
            'time_preference': re.compile(
                r'([1-3])순위[:：\s]*(\d{1,2}:\d{2}[-~]\d{1,2}:\d{2}|\d{1,2}시\s*[-~]\s*\d{1,2}시)',
                re.UNICODE
            ),
            
            # 한글 이름 패턴
            'korean_name': re.compile(
                r'[가-힣]{2,4}',
                re.UNICODE
            ),
            
            # 대표자 패턴
            'leader': re.compile(
                r'(?:대표자?|리더|팀장|팀\s*대표)[:：\s]*([가-힣]{2,4})',
                re.UNICODE
            )
        }
        
        # 한글 도메인 매핑
        self.korean_domains = {
            '네이버': 'naver.com',
            '다음': 'daum.net', 
            '구글': 'gmail.com',
            '야후': 'yahoo.co.kr'
        }
        
    def extract_team_data(self, pdf_path: Union[str, Path]) -> List[Team]:
        """PDF에서 팀 데이터 추출 - 메인 진입점"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        logger.info(f"PDF 추출 시작: {pdf_path}")
        
        # 다중 전략으로 추출 시도
        extraction_methods = [
            self._extract_with_pdfplumber,
            self._extract_with_pymupdf, 
            self._extract_with_pypdf2
        ]
        
        teams = []
        for method in extraction_methods:
            try:
                teams = method(pdf_path)
                if teams and len(teams) > 0:
                    logger.info(f"성공: {method.__name__}으로 {len(teams)}개 팀 추출")
                    break
            except Exception as e:
                logger.warning(f"{method.__name__} 실패: {e}")
                continue
        
        if not teams:
            raise RuntimeError("모든 PDF 추출 방법이 실패했습니다.")
        
        # 데이터 후처리 및 검증
        validated_teams = self._validate_and_clean_teams(teams)
        
        logger.info(f"최종 추출 완료: {len(validated_teams)}개 팀")
        return validated_teams
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[Team]:
        """pdfplumber를 사용한 추출 (한글 최적화)"""
        teams = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                logger.debug(f"페이지 {page_num + 1} 처리 중...")
                
                # 테이블 우선 추출 시도
                tables = page.extract_tables()
                if tables:
                    page_teams = self._extract_from_tables(tables, page_num)
                    teams.extend(page_teams)
                
                # 텍스트 기반 추출
                text = page.extract_text()
                if text:
                    page_teams = self._extract_from_text(text, page_num)
                    teams.extend(page_teams)
        
        return teams
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> List[Team]:
        """PyMuPDF를 사용한 추출 (테이블 감지 우수)"""
        teams = []
        
        doc = fitz.open(pdf_path)
        try:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # 테이블 감지 및 추출
                tables = page.find_tables()
                if tables:
                    for table in tables:
                        table_data = table.extract()
                        page_teams = self._extract_from_table_data(table_data, page_num)
                        teams.extend(page_teams)
                
                # 텍스트 추출 (폰트 정보 포함)
                text_dict = page.get_text("dict")
                if text_dict:
                    text = self._extract_text_from_dict(text_dict)
                    page_teams = self._extract_from_text(text, page_num)
                    teams.extend(page_teams)
                    
        finally:
            doc.close()
        
        return teams
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> List[Team]:
        """PyPDF2를 사용한 기본 추출 (폴백 용도)"""
        teams = []
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    page_teams = self._extract_from_text(text, page_num)
                    teams.extend(page_teams)
        
        return teams
    
    def _extract_from_tables(self, tables: List[List[List[str]]], page_num: int) -> List[Team]:
        """테이블에서 팀 데이터 추출"""
        teams = []
        
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:  # 헤더 + 최소 1개 데이터 행
                continue
                
            logger.debug(f"페이지 {page_num + 1}, 테이블 {table_idx + 1} 분석 중...")
            
            # 헤더 분석으로 컬럼 매핑
            header = table[0] if table else []
            column_mapping = self._analyze_table_headers(header)
            
            # 데이터 행 처리
            for row_idx, row in enumerate(table[1:], 1):
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue
                
                team = self._extract_team_from_row(row, column_mapping, f"{page_num+1}-{table_idx+1}-{row_idx}")
                if team:
                    teams.append(team)
        
        return teams
    
    def _extract_from_table_data(self, table_data: List[List], page_num: int) -> List[Team]:
        """PyMuPDF 테이블 데이터에서 팀 추출"""
        if not table_data or len(table_data) < 2:
            return []
        
        teams = []
        header = table_data[0]
        column_mapping = self._analyze_table_headers(header)
        
        for row_idx, row in enumerate(table_data[1:], 1):
            team = self._extract_team_from_row(row, column_mapping, f"{page_num+1}-{row_idx}")
            if team:
                teams.append(team)
                
        return teams
    
    def _analyze_table_headers(self, headers: List[str]) -> Dict[str, int]:
        """테이블 헤더 분석으로 컬럼 매핑 생성"""
        mapping = {}
        
        header_patterns = {
            'team_name': [r'팀명', r'팀\s*이름', r'team.*name'],
            'leader_name': [r'대표자?', r'리더', r'팀장', r'leader'],
            'members': [r'팀원', r'구성원', r'멤버', r'member'],
            'email': [r'이메일', r'메일', r'e[-\s]?mail'],
            'phone': [r'연락처', r'전화', r'phone', r'contact'],
            'preference_1': [r'1순위', r'첫.?번째', r'first'],
            'preference_2': [r'2순위', r'두.?번째', r'second'],
            'preference_3': [r'3순위', r'세.?번째', r'third']
        }
        
        for col_idx, header in enumerate(headers):
            if not header:
                continue
                
            header_clean = str(header).strip().lower()
            
            for field, patterns in header_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, header_clean, re.IGNORECASE | re.UNICODE):
                        mapping[field] = col_idx
                        break
        
        return mapping
    
    def _extract_team_from_row(self, row: List[str], column_mapping: Dict[str, int], row_id: str) -> Optional[Team]:
        """테이블 행에서 팀 정보 추출"""
        try:
            team = Team(team_id=f"team_{row_id}")
            
            # 팀명 추출
            if 'team_name' in column_mapping:
                team_name = self._safe_get_cell(row, column_mapping['team_name'])
                if team_name:
                    team.team_name = team_name.strip()
            
            # 대표자 추출
            leader_name = ""
            if 'leader_name' in column_mapping:
                leader_name = self._safe_get_cell(row, column_mapping['leader_name'])
            
            # 팀원 추출
            members_text = ""
            if 'members' in column_mapping:
                members_text = self._safe_get_cell(row, column_mapping['members']) or ""
            
            # 이메일 추출
            email = ""
            if 'email' in column_mapping:
                email_text = self._safe_get_cell(row, column_mapping['email'])
                if email_text:
                    emails = self._extract_emails(email_text)
                    email = emails[0] if emails else ""
            
            # 연락처 추출
            phone = ""
            if 'phone' in column_mapping:
                phone_text = self._safe_get_cell(row, column_mapping['phone'])
                if phone_text:
                    phones = self._extract_phone_numbers(phone_text)
                    phone = phones[0] if phones else ""
            
            # 시간 선호도 추출
            preferences = []
            for i in range(1, 4):
                pref_key = f'preference_{i}'
                if pref_key in column_mapping:
                    pref_text = self._safe_get_cell(row, column_mapping[pref_key])
                    if pref_text:
                        normalized_time = self._normalize_time_format(pref_text.strip())
                        if normalized_time:
                            preferences.append(normalized_time)
            
            # 팀 정보 설정
            team.primary_email = email
            team.primary_phone = phone
            team.time_preferences = preferences
            
            # 팀원 정보 설정
            if leader_name:
                team.add_member(leader_name.strip(), email, phone, is_leader=True)
            
            # 추가 팀원 파싱
            if members_text:
                additional_members = self._parse_members_text(members_text)
                for member_name in additional_members:
                    if member_name != leader_name:
                        team.add_member(member_name)
            
            # 기본 검증
            if not team.team_name or not email:
                logger.warning(f"불완전한 팀 데이터: {row_id}")
                team.validation_status = ValidationStatus.WARNING
                team.validation_messages.append("팀명 또는 이메일 누락")
            
            return team
            
        except Exception as e:
            logger.error(f"행 파싱 오류 {row_id}: {e}")
            return None
    
    def _extract_from_text(self, text: str, page_num: int) -> List[Team]:
        """자유형식 텍스트에서 팀 데이터 추출"""
        teams = []
        
        # 텍스트를 논리적 블록으로 분할
        blocks = self._split_text_into_blocks(text)
        
        for block_idx, block in enumerate(blocks):
            if len(block.strip()) < 20:  # 너무 짧은 블록은 스킵
                continue
                
            team = self._extract_team_from_text_block(block, f"{page_num+1}-text-{block_idx+1}")
            if team:
                teams.append(team)
        
        return teams
    
    def _split_text_into_blocks(self, text: str) -> List[str]:
        """텍스트를 팀 단위 블록으로 분할"""
        # 일반적인 구분 패턴들
        separators = [
            r'\n\s*\n',  # 빈 줄
            r'(?=팀명[:：])',  # 팀명 앞
            r'(?=\d+\.\s)',  # 번호 매김
            r'(?=[가-힣]{2,4}팀)',  # 팀명 패턴
        ]
        
        blocks = [text]
        for separator in separators:
            new_blocks = []
            for block in blocks:
                new_blocks.extend(re.split(separator, block))
            blocks = [b.strip() for b in new_blocks if b.strip()]
        
        return blocks
    
    def _extract_team_from_text_block(self, block: str, block_id: str) -> Optional[Team]:
        """텍스트 블록에서 팀 정보 추출"""
        try:
            team = Team(team_id=f"team_{block_id}")
            
            # 팀명 추출
            team_match = self.patterns['team_name'].search(block)
            if team_match:
                team.team_name = team_match.group(1).strip()
            
            # 대표자 추출
            leader_match = self.patterns['leader'].search(block)
            leader_name = leader_match.group(1).strip() if leader_match else ""
            
            # 이메일 추출
            emails = self._extract_emails(block)
            email = emails[0] if emails else ""
            
            # 전화번호 추출
            phones = self._extract_phone_numbers(block)
            phone = phones[0] if phones else ""
            
            # 시간 선호도 추출
            preferences = self._extract_time_preferences(block)
            
            # 팀원 이름 추출
            korean_names = self.patterns['korean_name'].findall(block)
            unique_names = list(dict.fromkeys(korean_names))  # 중복 제거하면서 순서 유지
            
            # 팀 정보 설정
            team.primary_email = email
            team.primary_phone = phone
            team.time_preferences = preferences[:3]  # 최대 3순위까지
            
            # 팀원 추가
            if leader_name:
                team.add_member(leader_name, email, phone, is_leader=True)
                
            # 나머지 팀원 추가
            for name in unique_names:
                if name != leader_name and len(name) >= 2:
                    team.add_member(name)
            
            # 기본 검증
            if not team.team_name and not email:
                return None
                
            return team
            
        except Exception as e:
            logger.error(f"텍스트 블록 파싱 오류 {block_id}: {e}")
            return None
    
    def _extract_emails(self, text: str) -> List[str]:
        """텍스트에서 이메일 주소 추출"""
        emails = self.patterns['email'].findall(text)
        
        # 한글 도메인 처리
        processed_emails = []
        for email in emails:
            # 한글 도메인을 영문으로 변환
            for korean, english in self.korean_domains.items():
                if korean in email:
                    email = email.replace(korean, english)
            processed_emails.append(email.lower())
        
        return list(set(processed_emails))  # 중복 제거
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """텍스트에서 전화번호 추출"""
        phones = self.patterns['phone'].findall(text)
        
        # 전화번호 정규화
        normalized_phones = []
        for phone in phones:
            # 공백과 하이픈 정리
            clean_phone = re.sub(r'[-\s]', '-', phone.strip())
            if len(clean_phone) >= 10:
                normalized_phones.append(clean_phone)
        
        return normalized_phones
    
    def _extract_time_preferences(self, text: str) -> List[str]:
        """시간 선호도 추출 및 정규화"""
        preferences = []
        
        matches = self.patterns['time_preference'].findall(text)
        for rank, time_text in matches:
            normalized_time = self._normalize_time_format(time_text)
            if normalized_time:
                preferences.append(normalized_time)
        
        return preferences
    
    def _normalize_time_format(self, time_text: str) -> Optional[str]:
        """시간 형식 정규화 (HH:MM-HH:MM)"""
        if not time_text:
            return None
            
        # 다양한 시간 형식 패턴
        time_patterns = [
            r'(\d{1,2}):(\d{2})[-~](\d{1,2}):(\d{2})',  # 09:00-10:00
            r'(\d{1,2})시\s*[-~]\s*(\d{1,2})시',       # 9시-10시
            r'(\d{1,2})시\s*(\d{1,2})분[-~](\d{1,2})시\s*(\d{1,2})분',  # 9시30분-10시30분
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_text)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    start_hour, start_min, end_hour, end_min = groups
                    return f"{int(start_hour):02d}:{int(start_min):02d}-{int(end_hour):02d}:{int(end_min):02d}"
                elif len(groups) == 2:
                    start_hour, end_hour = groups
                    return f"{int(start_hour):02d}:00-{int(end_hour):02d}:00"
        
        return None
    
    def _parse_members_text(self, text: str) -> List[str]:
        """팀원 텍스트에서 개별 이름 추출"""
        # 구분자로 분할
        separators = [',', '/', '\\|', '·', '&', 'and', '그리고']
        
        names = [text]
        for sep in separators:
            new_names = []
            for name in names:
                new_names.extend(re.split(sep, name))
            names = new_names
        
        # 한글 이름만 필터링 후 정리
        korean_names = []
        for name in names:
            clean_name = re.sub(r'[^\가-힣]', '', name.strip())
            if 2 <= len(clean_name) <= 4:
                korean_names.append(clean_name)
        
        return korean_names
    
    def _safe_get_cell(self, row: List[str], index: int) -> Optional[str]:
        """안전한 셀 값 추출"""
        if 0 <= index < len(row) and row[index] is not None:
            return str(row[index]).strip()
        return None
    
    def _validate_and_clean_teams(self, teams: List[Team]) -> List[Team]:
        """팀 데이터 검증 및 정리"""
        validated_teams = []
        
        for team in teams:
            # 중복 제거
            if any(existing.team_name == team.team_name and existing.primary_email == team.primary_email 
                   for existing in validated_teams):
                continue
            
            # 기본 검증
            issues = []
            
            if not team.team_name:
                issues.append("팀명 누락")
            
            if not team.primary_email:
                issues.append("이메일 누락")
            elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', team.primary_email):
                issues.append("이메일 형식 오류")
            
            if not team.members:
                issues.append("팀원 정보 누락")
            
            if len(team.time_preferences) == 0:
                issues.append("희망 시간 누락")
            
            # 검증 결과 반영
            if issues:
                team.validation_status = ValidationStatus.WARNING if len(issues) <= 2 else ValidationStatus.INVALID
                team.validation_messages = issues
            
            # 유효한 팀만 추가 (경고는 포함)
            if team.validation_status != ValidationStatus.INVALID:
                validated_teams.append(team)
                
        return validated_teams
    
    def _extract_text_from_dict(self, text_dict: Dict) -> str:
        """PyMuPDF 텍스트 딕셔너리에서 텍스트 추출"""
        text_content = ""
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text_content += span.get("text", "") + " "
                    text_content += "\n"
        
        return text_content
    
    def get_extraction_statistics(self, teams: List[Team]) -> Dict:
        """추출 통계 생성"""
        if not teams:
            return {}
            
        stats = {
            'total_teams': len(teams),
            'valid_teams': len([t for t in teams if t.validation_status == ValidationStatus.VALID]),
            'warning_teams': len([t for t in teams if t.validation_status == ValidationStatus.WARNING]),
            'invalid_teams': len([t for t in teams if t.validation_status == ValidationStatus.INVALID]),
            'teams_with_email': len([t for t in teams if t.primary_email]),
            'teams_with_phone': len([t for t in teams if t.primary_phone]),
            'teams_with_preferences': len([t for t in teams if t.time_preferences]),
            'avg_members_per_team': sum(len(t.members) for t in teams) / len(teams),
            'extraction_success_rate': len([t for t in teams if t.validation_status != ValidationStatus.INVALID]) / len(teams) * 100
        }
        
        return stats