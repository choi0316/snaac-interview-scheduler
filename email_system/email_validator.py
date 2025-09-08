"""
고도화된 이메일 검증 시스템

포괄적인 이메일 검증, DNS 확인, 도메인 분석, 중복 처리를 지원하는 모듈입니다.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
import dns.resolver
import socket
from email_validator import validate_email, EmailNotValidError
from dataclasses import dataclass
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..core.models import EmailValidationResult
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import EmailValidationResult

logger = logging.getLogger(__name__)


@dataclass
class DomainInfo:
    """도메인 정보"""
    domain: str
    is_valid: bool = False
    has_mx_record: bool = False
    mx_records: List[str] = None
    is_disposable: bool = False
    is_institutional: bool = False
    domain_age_days: Optional[int] = None
    trust_score: float = 0.0
    
    def __post_init__(self):
        if self.mx_records is None:
            self.mx_records = []


class EmailValidator:
    """포괄적 이메일 검증 시스템"""
    
    def __init__(self):
        self.validation_cache: Dict[str, EmailValidationResult] = {}
        self.domain_cache: Dict[str, DomainInfo] = {}
        
        # 임시/일회용 이메일 도메인 블랙리스트
        self.disposable_domains = {
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'trashmail.com', 'yopmail.com', 'maildrop.cc',
            'getnada.com', 'mohmal.com', 'fakeinbox.com'
        }
        
        # 교육기관 도메인 패턴
        self.institutional_patterns = [
            r'\.ac\.kr$',  # 한국 대학
            r'\.edu$',     # 미국 교육기관
            r'\.edu\..*$', # 기타 국가 교육기관
            r'university\.', # 대학교 키워드
            r'college\.', # 대학 키워드
            r'school\.', # 학교 키워드
        ]
        
        # 일반적인 오타 수정 매핑
        self.common_typo_fixes = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'gmail.co': 'gmail.com',
            'nave.com': 'naver.com',
            'naber.com': 'naver.com',
            'hanmial.net': 'hanmail.net',
            'hanmai.net': 'hanmail.net',
            'daim.net': 'daum.net',
            'yahooo.com': 'yahoo.com',
            'outllook.com': 'outlook.com',
            'hotmial.com': 'hotmail.com'
        }
        
        # 신뢰할 수 있는 도메인들 (높은 신뢰도)
        self.trusted_domains = {
            'gmail.com': 10.0,
            'naver.com': 9.5,
            'hanmail.net': 9.0,
            'daum.net': 9.0,
            'outlook.com': 9.5,
            'hotmail.com': 9.0,
            'yahoo.com': 8.5,
            'yahoo.co.kr': 8.5,
            'kakao.com': 9.0
        }
        
        # DNS 해석기 설정
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 10
    
    def comprehensive_email_validation(
        self, 
        email_list: List[str], 
        enable_dns_check: bool = True,
        max_workers: int = 10
    ) -> List[EmailValidationResult]:
        """포괄적 이메일 검증 - 병렬 처리 지원"""
        
        if not email_list:
            return []
        
        logger.info(f"이메일 검증 시작: {len(email_list)}개")
        
        results = []
        
        # 중복 이메일 사전 제거 (대소문자 무시)
        unique_emails = {}
        for email in email_list:
            normalized = email.lower().strip()
            if normalized not in unique_emails:
                unique_emails[normalized] = email
        
        # 병렬 처리로 검증
        if enable_dns_check and len(unique_emails) > 5:
            results = self._validate_emails_parallel(
                list(unique_emails.values()), max_workers
            )
        else:
            results = [
                self._validate_single_email(email, enable_dns_check) 
                for email in unique_emails.values()
            ]
        
        # 중복 검사 수행
        self._check_duplicates_in_results(results)
        
        logger.info(f"이메일 검증 완료: {len(results)}개 처리")
        return results
    
    def _validate_emails_parallel(
        self, 
        email_list: List[str], 
        max_workers: int
    ) -> List[EmailValidationResult]:
        """병렬 이메일 검증"""
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            future_to_email = {
                executor.submit(self._validate_single_email, email, True): email 
                for email in email_list
            }
            
            # 결과 수집
            for future in as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"이메일 검증 오류 {email}: {e}")
                    # 기본 검증 결과 생성
                    error_result = EmailValidationResult(
                        email=email,
                        is_valid=False,
                        validation_type="error"
                    )
                    error_result.add_issue(f"검증 오류: {str(e)}")
                    results.append(error_result)
        
        return results
    
    def _validate_single_email(
        self, 
        email: str, 
        enable_dns_check: bool = True
    ) -> EmailValidationResult:
        """단일 이메일 포괄 검증"""
        
        # 캐시 확인
        cache_key = f"{email.lower()}_{enable_dns_check}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        result = EmailValidationResult(email=email)
        
        try:
            # 1단계: 기본 형식 검증
            if not self._basic_format_validation(email):
                result.add_issue("기본 형식 오류")
                result.validation_type = "format_error"
                return result
            
            # 2단계: 고급 형식 검증 (email-validator 라이브러리)
            try:
                validation = validate_email(email)
                normalized_email = validation.email
                result.email = normalized_email  # 정규화된 이메일 사용
                result.domain = validation.domain
            except EmailNotValidError as e:
                result.add_issue(f"형식 검증 실패: {str(e)}")
                result.validation_type = "format_error"
                return result
            
            # 3단계: 도메인 검증
            domain_info = self._get_domain_info(result.domain, enable_dns_check)
            
            if not domain_info.is_valid:
                result.add_issue("도메인 해석 실패")
                result.validation_type = "domain_error"
            
            if not domain_info.has_mx_record and enable_dns_check:
                result.add_issue("MX 레코드 없음")
                result.validation_type = "mx_error"
            
            # 4단계: 일회용 이메일 검사
            if domain_info.is_disposable:
                result.add_issue("일회용 이메일 도메인")
                result.validation_type = "disposable"
            
            # 5단계: 교육기관 도메인 확인
            result.is_institutional = domain_info.is_institutional
            
            # 6단계: 오타 수정 제안
            suggestions = self._generate_typo_suggestions(email)
            for suggestion in suggestions:
                result.add_suggestion(suggestion)
            
            # 7단계: 신뢰도 점수 계산
            trust_score = self._calculate_trust_score(result.domain, domain_info)
            
            # 최종 유효성 판정
            result.is_valid = (
                len(result.issues) == 0 or 
                (len(result.issues) == 1 and "MX 레코드 없음" in result.issues)
            )
            
            if result.is_valid:
                result.validation_type = "valid"
            
            # 캐시 저장 (1시간 유효)
            self.validation_cache[cache_key] = result
            
        except Exception as e:
            logger.error(f"이메일 검증 중 오류 {email}: {e}")
            result.add_issue(f"검증 오류: {str(e)}")
            result.validation_type = "error"
        
        return result
    
    def _basic_format_validation(self, email: str) -> bool:
        """기본 이메일 형식 검증"""
        
        if not email or len(email) > 254:  # RFC 5321 제한
            return False
        
        # 기본 정규표현식 패턴
        pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            re.IGNORECASE | re.UNICODE
        )
        
        if not pattern.match(email):
            return False
        
        # @ 기호 검사
        at_count = email.count('@')
        if at_count != 1:
            return False
        
        local_part, domain_part = email.split('@')
        
        # 로컬 부분 검사
        if len(local_part) > 64 or len(local_part) == 0:  # RFC 5321 제한
            return False
        
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        if '..' in local_part:  # 연속 점 금지
            return False
        
        # 도메인 부분 검사  
        if len(domain_part) > 253 or len(domain_part) == 0:
            return False
        
        if domain_part.startswith('.') or domain_part.endswith('.'):
            return False
        
        if '..' in domain_part:  # 연속 점 금지
            return False
        
        return True
    
    def _get_domain_info(self, domain: str, enable_dns_check: bool) -> DomainInfo:
        """도메인 정보 수집"""
        
        # 캐시 확인
        cache_key = f"{domain.lower()}_{enable_dns_check}"
        if cache_key in self.domain_cache:
            return self.domain_cache[cache_key]
        
        domain_info = DomainInfo(domain=domain.lower())
        
        try:
            # 일회용 도메인 검사
            domain_info.is_disposable = domain.lower() in self.disposable_domains
            
            # 교육기관 도메인 검사
            domain_info.is_institutional = any(
                re.search(pattern, domain.lower(), re.IGNORECASE)
                for pattern in self.institutional_patterns
            )
            
            # DNS 검사
            if enable_dns_check:
                domain_info = self._perform_dns_checks(domain_info)
            else:
                domain_info.is_valid = True  # DNS 검사 스킵시 기본 유효
            
            # 신뢰도 점수 계산
            domain_info.trust_score = self.trusted_domains.get(domain.lower(), 5.0)
            
        except Exception as e:
            logger.warning(f"도메인 정보 수집 오류 {domain}: {e}")
            domain_info.is_valid = False
        
        # 캐시 저장
        self.domain_cache[cache_key] = domain_info
        return domain_info
    
    def _perform_dns_checks(self, domain_info: DomainInfo) -> DomainInfo:
        """DNS 검사 수행"""
        
        try:
            # MX 레코드 확인
            try:
                mx_records = dns.resolver.resolve(domain_info.domain, 'MX')
                domain_info.has_mx_record = len(mx_records) > 0
                domain_info.mx_records = [str(record.exchange) for record in mx_records]
                domain_info.is_valid = True
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                domain_info.has_mx_record = False
                # A 레코드 확인 (MX가 없어도 A 레코드가 있으면 메일 수신 가능)
                try:
                    a_records = dns.resolver.resolve(domain_info.domain, 'A')
                    domain_info.is_valid = len(a_records) > 0
                except:
                    domain_info.is_valid = False
            
        except Exception as e:
            logger.warning(f"DNS 검사 실패 {domain_info.domain}: {e}")
            domain_info.is_valid = False
            domain_info.has_mx_record = False
        
        return domain_info
    
    def _generate_typo_suggestions(self, email: str) -> List[str]:
        """오타 수정 제안 생성"""
        
        suggestions = []
        
        try:
            local_part, domain_part = email.split('@')
            domain_lower = domain_part.lower()
            
            # 일반적인 오타 수정
            for typo, correct in self.common_typo_fixes.items():
                if typo in domain_lower:
                    corrected_domain = domain_lower.replace(typo, correct)
                    suggested_email = f"{local_part}@{corrected_domain}"
                    suggestions.append(suggested_email)
            
            # 유사 도메인 제안 (편집 거리 기반)
            similar_domains = self._find_similar_domains(domain_part)
            for similar_domain in similar_domains:
                suggested_email = f"{local_part}@{similar_domain}"
                suggestions.append(suggested_email)
                
        except Exception as e:
            logger.warning(f"오타 제안 생성 오류 {email}: {e}")
        
        return suggestions[:3]  # 최대 3개 제안
    
    def _find_similar_domains(self, domain: str, max_distance: int = 2) -> List[str]:
        """유사한 도메인 찾기 (편집 거리 기반)"""
        
        similar_domains = []
        domain_lower = domain.lower()
        
        for trusted_domain in self.trusted_domains.keys():
            distance = self._levenshtein_distance(domain_lower, trusted_domain)
            if 0 < distance <= max_distance:
                similar_domains.append(trusted_domain)
        
        # 신뢰도 순으로 정렬
        similar_domains.sort(
            key=lambda d: self.trusted_domains.get(d, 0), 
            reverse=True
        )
        
        return similar_domains[:2]  # 최대 2개
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """레벤슈타인 거리 계산"""
        
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_trust_score(self, domain: str, domain_info: DomainInfo) -> float:
        """신뢰도 점수 계산"""
        
        base_score = self.trusted_domains.get(domain.lower(), 5.0)
        
        # 가산점/감점 적용
        if domain_info.is_disposable:
            base_score -= 5.0
        
        if domain_info.is_institutional:
            base_score += 1.0
        
        if not domain_info.has_mx_record:
            base_score -= 1.0
        
        return max(0.0, min(10.0, base_score))
    
    def _check_duplicates_in_results(self, results: List[EmailValidationResult]):
        """결과 내 중복 이메일 검사"""
        
        email_counts = {}
        
        for result in results:
            normalized_email = result.email.lower()
            email_counts[normalized_email] = email_counts.get(normalized_email, 0) + 1
        
        # 중복 이메일에 대한 경고 추가
        for result in results:
            normalized_email = result.email.lower()
            if email_counts[normalized_email] > 1:
                result.add_issue("중복 이메일 주소")
                result.add_suggestion("대체 이메일 주소 요청 필요")
    
    def get_validation_statistics(self, results: List[EmailValidationResult]) -> Dict:
        """검증 통계 생성"""
        
        if not results:
            return {}
        
        total_emails = len(results)
        valid_emails = len([r for r in results if r.is_valid])
        invalid_emails = total_emails - valid_emails
        
        # 오류 유형별 통계
        error_types = {}
        for result in results:
            if not result.is_valid and result.validation_type:
                error_types[result.validation_type] = error_types.get(result.validation_type, 0) + 1
        
        # 도메인별 통계
        domain_stats = {}
        for result in results:
            if result.domain:
                domain_stats[result.domain] = domain_stats.get(result.domain, 0) + 1
        
        # 교육기관 이메일 통계
        institutional_count = len([r for r in results if r.is_institutional])
        
        return {
            'total_emails': total_emails,
            'valid_emails': valid_emails,
            'invalid_emails': invalid_emails,
            'success_rate': (valid_emails / total_emails * 100) if total_emails > 0 else 0,
            'error_types': error_types,
            'domain_distribution': dict(sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            'institutional_emails': institutional_count,
            'institutional_rate': (institutional_count / total_emails * 100) if total_emails > 0 else 0,
        }
    
    def export_validation_report(
        self, 
        results: List[EmailValidationResult], 
        output_path: str
    ) -> str:
        """검증 결과 리포트 내보내기"""
        
        import pandas as pd
        
        # 결과를 DataFrame으로 변환
        report_data = []
        for result in results:
            report_data.append({
                '이메일': result.email,
                '유효성': '유효' if result.is_valid else '무효',
                '검증유형': result.validation_type,
                '도메인': result.domain,
                '교육기관': '예' if result.is_institutional else '아니오',
                '문제점': '; '.join(result.issues),
                '수정제안': '; '.join(result.suggestions)
            })
        
        df = pd.DataFrame(report_data)
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='검증결과', index=False)
            
            # 통계 시트 추가
            stats = self.get_validation_statistics(results)
            stats_df = pd.DataFrame([
                ['총 이메일 수', stats.get('total_emails', 0)],
                ['유효한 이메일', stats.get('valid_emails', 0)],
                ['무효한 이메일', stats.get('invalid_emails', 0)],
                ['성공률 (%)', f"{stats.get('success_rate', 0):.1f}"],
                ['교육기관 이메일', stats.get('institutional_emails', 0)],
            ], columns=['항목', '값'])
            
            stats_df.to_excel(writer, sheet_name='통계', index=False)
        
        logger.info(f"검증 리포트 생성 완료: {output_path}")
        return output_path
    
    def clear_cache(self):
        """캐시 정리"""
        self.validation_cache.clear()
        self.domain_cache.clear()
        logger.info("이메일 검증 캐시 정리 완료")
    
    def bulk_domain_precheck(self, domains: List[str]) -> Dict[str, DomainInfo]:
        """도메인 일괄 사전 검사"""
        
        logger.info(f"도메인 일괄 사전 검사: {len(domains)}개")
        
        domain_infos = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_domain = {
                executor.submit(self._get_domain_info, domain, True): domain 
                for domain in set(domains)  # 중복 제거
            }
            
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    domain_info = future.result(timeout=30)
                    domain_infos[domain] = domain_info
                except Exception as e:
                    logger.error(f"도메인 사전 검사 오류 {domain}: {e}")
                    domain_infos[domain] = DomainInfo(domain=domain, is_valid=False)
        
        return domain_infos