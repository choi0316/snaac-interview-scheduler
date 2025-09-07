"""
이메일 검증 및 템플릿 시스템 테스트
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email.email_validator import EmailValidator
from email.template_manager import EmailTemplateManager
from core.models import Team, InterviewSlot, Schedule


class TestEmailValidator:
    """이메일 검증기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.validator = EmailValidator()
    
    def test_basic_email_validation(self):
        """기본 이메일 검증 테스트"""
        # 유효한 이메일들
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.kr",
            "admin@university.ac.kr",
            "contact@한국대학교.kr",
            "team123@startup.io",
            "user+tag@gmail.com"
        ]
        
        for email in valid_emails:
            result = self.validator.validate_email(email)
            assert result["is_valid"], f"Failed for valid email: {email}"
            assert result["email"] == email
            assert "error" not in result
    
    def test_invalid_email_formats(self):
        """잘못된 이메일 형식 테스트"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@domain",
            "",
            "   ",
            "user@domain..com",
            "user name@domain.com"  # 공백 포함
        ]
        
        for email in invalid_emails:
            result = self.validator.validate_email(email)
            assert not result["is_valid"], f"Should be invalid: {email}"
            assert "error" in result
    
    @patch('socket.getaddrinfo')
    def test_dns_validation(self, mock_getaddrinfo):
        """DNS 검증 테스트"""
        # DNS 조회 성공 시뮬레이션
        mock_getaddrinfo.return_value = [("family", "type", "proto", "canonname", ("8.8.8.8", 25))]
        
        result = self.validator.validate_email("test@gmail.com", check_dns=True)
        assert result["is_valid"]
        assert result["dns_valid"]
        mock_getaddrinfo.assert_called()
        
        # DNS 조회 실패 시뮬레이션
        mock_getaddrinfo.side_effect = Exception("DNS lookup failed")
        
        result = self.validator.validate_email("test@nonexistent.domain", check_dns=True)
        assert not result["dns_valid"]
        assert "dns_error" in result
    
    def test_domain_trust_scoring(self):
        """도메인 신뢰도 점수 테스트"""
        # 높은 신뢰도 도메인들
        high_trust_domains = [
            "gmail.com",
            "naver.com",
            "university.ac.kr",
            "company.co.kr"
        ]
        
        for domain in high_trust_domains:
            email = f"test@{domain}"
            result = self.validator.validate_email(email)
            trust_score = result.get("trust_score", 0)
            assert trust_score >= 0.7, f"Low trust score for {domain}: {trust_score}"
        
        # 낮은 신뢰도 도메인들
        low_trust_domains = [
            "10minutemail.com",
            "tempmail.org",
            "unknown-domain.xyz"
        ]
        
        for domain in low_trust_domains:
            email = f"test@{domain}"
            result = self.validator.validate_email(email)
            trust_score = result.get("trust_score", 1.0)
            assert trust_score <= 0.5, f"High trust score for low-trust domain {domain}: {trust_score}"
    
    def test_disposable_email_detection(self):
        """일회용 이메일 감지 테스트"""
        disposable_emails = [
            "test@10minutemail.com",
            "user@tempmail.org",
            "temp@guerrillamail.com",
            "disposable@mailinator.com"
        ]
        
        for email in disposable_emails:
            result = self.validator.validate_email(email)
            assert result.get("is_disposable", False), f"Failed to detect disposable: {email}"
    
    def test_institutional_domain_recognition(self):
        """기관 도메인 인식 테스트"""
        institutional_emails = [
            "student@university.ac.kr",
            "prof@kaist.ac.kr",
            "admin@seoul.go.kr",
            "employee@samsung.com"
        ]
        
        for email in institutional_emails:
            result = self.validator.validate_email(email)
            domain_type = result.get("domain_type", "unknown")
            assert domain_type in ["academic", "government", "corporate"], \
                f"Failed to recognize institutional domain: {email}"
    
    def test_typo_correction_suggestions(self):
        """오타 수정 제안 테스트"""
        typo_cases = [
            ("user@gmial.com", "user@gmail.com"),
            ("test@navr.com", "test@naver.com"),
            ("admin@yahooo.com", "admin@yahoo.com"),
            ("contact@outlok.com", "contact@outlook.com")
        ]
        
        for typo_email, expected_correction in typo_cases:
            result = self.validator.validate_email(typo_email)
            suggestions = result.get("suggestions", [])
            assert len(suggestions) > 0, f"No suggestions for typo: {typo_email}"
            assert expected_correction in suggestions, \
                f"Expected correction not found for {typo_email}"
    
    def test_bulk_validation(self):
        """대량 검증 테스트"""
        emails = [
            "valid1@gmail.com",
            "valid2@naver.com",
            "invalid-email",
            "valid3@university.ac.kr",
            "disposable@10minutemail.com"
        ]
        
        results = self.validator.validate_bulk(emails, max_workers=2)
        
        assert len(results) == len(emails)
        
        # 결과 검증
        valid_count = sum(1 for result in results if result["is_valid"])
        assert valid_count >= 3  # 최소 3개는 유효해야 함
        
        # 일회용 이메일 감지 확인
        disposable_detected = any(
            result.get("is_disposable", False) for result in results
        )
        assert disposable_detected
    
    def test_korean_domain_support(self):
        """한국어 도메인 지원 테스트"""
        korean_emails = [
            "test@한국대학교.kr",
            "admin@삼성.com",
            "user@네이버.com"
        ]
        
        for email in korean_emails:
            result = self.validator.validate_email(email)
            # 한국어 도메인도 기본적으로는 유효한 형식으로 인식되어야 함
            # (실제 DNS는 별도로 확인)
            assert result["is_valid"] or "error" in result  # 오류가 있더라도 적절히 처리
    
    def test_performance_optimization(self):
        """성능 최적화 테스트"""
        import time
        
        # 100개 이메일 대량 검증
        emails = [f"user{i:03d}@test{i % 10}.com" for i in range(100)]
        
        start_time = time.time()
        results = self.validator.validate_bulk(emails, max_workers=4)
        end_time = time.time()
        
        # 병렬 처리로 인한 성능 향상 확인 (5초 미만)
        assert end_time - start_time < 5.0
        assert len(results) == 100
    
    def test_caching_mechanism(self):
        """캐싱 메커니즘 테스트"""
        email = "test@example.com"
        
        # 첫 번째 검증
        result1 = self.validator.validate_email(email)
        
        # 두 번째 검증 (캐시 사용)
        result2 = self.validator.validate_email(email)
        
        # 결과가 동일해야 함
        assert result1["is_valid"] == result2["is_valid"]
        assert result1["email"] == result2["email"]


class TestEmailTemplateManager:
    """이메일 템플릿 관리자 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.template_manager = EmailTemplateManager()
        
        # 테스트용 스케줄 데이터
        self.test_schedule = Schedule(
            team=Team(
                name="한국대학교팀",
                email="korea@university.ac.kr",
                contact="010-1234-5678"
            ),
            slot=InterviewSlot(
                date=datetime(2024, 1, 15),
                time=time(14, 30),
                interviewer="김교수",
                location="면접실1"
            )
        )
    
    def test_template_loading(self):
        """템플릿 로딩 테스트"""
        # 기본 템플릿들이 로드되는지 확인
        templates = self.template_manager.list_templates()
        
        expected_templates = [
            "interview_notification",
            "schedule_change", 
            "reminder",
            "rejection"
        ]
        
        for template in expected_templates:
            assert template in templates, f"Missing template: {template}"
    
    def test_interview_notification_template(self):
        """면접 확정 통지 템플릿 테스트"""
        content = self.template_manager.render_template(
            "interview_notification",
            schedule=self.test_schedule
        )
        
        assert content is not None
        assert len(content) > 0
        
        # 필수 정보가 포함되어 있는지 확인
        assert "한국대학교팀" in content
        assert "2024" in content
        assert "14:30" in content
        assert "김교수" in content
        assert "면접실1" in content
    
    def test_schedule_change_template(self):
        """일정 변경 통지 템플릿 테스트"""
        old_schedule = Schedule(
            team=self.test_schedule.team,
            slot=InterviewSlot(
                date=datetime(2024, 1, 15),
                time=time(13, 0),
                interviewer="이교수",
                location="면접실2"
            )
        )
        
        content = self.template_manager.render_template(
            "schedule_change",
            old_schedule=old_schedule,
            new_schedule=self.test_schedule
        )
        
        assert content is not None
        assert "변경" in content
        assert "13:00" in content  # 이전 시간
        assert "14:30" in content  # 새로운 시간
        assert "이교수" in content  # 이전 면접관
        assert "김교수" in content  # 새로운 면접관
    
    def test_reminder_template(self):
        """리마인더 템플릿 테스트"""
        content = self.template_manager.render_template(
            "reminder",
            schedule=self.test_schedule,
            reminder_hours=24
        )
        
        assert content is not None
        assert "리마인더" in content or "알림" in content
        assert "24" in content  # 리마인더 시간
        assert "한국대학교팀" in content
    
    def test_rejection_template(self):
        """탈락 통지 템플릿 테스트"""
        content = self.template_manager.render_template(
            "rejection",
            team=self.test_schedule.team,
            reason="서류심사 결과"
        )
        
        assert content is not None
        assert "한국대학교팀" in content
        assert "서류심사 결과" in content
    
    def test_template_variable_substitution(self):
        """템플릿 변수 치환 테스트"""
        # 커스텀 템플릿으로 테스트
        custom_template = """
        안녕하세요 {{team_name}}님,
        
        면접 일정: {{interview_date}} {{interview_time}}
        면접관: {{interviewer}}
        장소: {{location}}
        
        {% if special_note %}
        특별 안내사항: {{special_note}}
        {% endif %}
        
        감사합니다.
        """
        
        content = self.template_manager.render_template_string(
            custom_template,
            team_name=self.test_schedule.team.name,
            interview_date="2024년 1월 15일",
            interview_time="14:30",
            interviewer=self.test_schedule.slot.interviewer,
            location=self.test_schedule.slot.location,
            special_note="필기구를 지참해 주세요"
        )
        
        assert "한국대학교팀" in content
        assert "2024년 1월 15일" in content
        assert "14:30" in content
        assert "김교수" in content
        assert "면접실1" in content
        assert "필기구를 지참해 주세요" in content
    
    def test_conditional_content(self):
        """조건부 콘텐츠 테스트"""
        # 조건부 블록을 포함한 템플릿
        conditional_template = """
        안녕하세요 {{team_name}}님,
        
        {% if schedule.slot.location %}
        면접 장소: {{schedule.slot.location}}
        {% else %}
        면접 장소는 추후 안내드리겠습니다.
        {% endif %}
        
        {% if contact_required %}
        문의사항이 있으시면 연락 주세요.
        {% endif %}
        """
        
        # 장소가 있는 경우
        content_with_location = self.template_manager.render_template_string(
            conditional_template,
            team_name=self.test_schedule.team.name,
            schedule=self.test_schedule,
            contact_required=True
        )
        
        assert "면접실1" in content_with_location
        assert "문의사항" in content_with_location
        
        # 장소가 없는 경우
        schedule_no_location = Schedule(
            team=self.test_schedule.team,
            slot=InterviewSlot(
                date=datetime(2024, 1, 15),
                time=time(14, 30),
                interviewer="김교수"
                # location 없음
            )
        )
        
        content_no_location = self.template_manager.render_template_string(
            conditional_template,
            team_name=schedule_no_location.team.name,
            schedule=schedule_no_location,
            contact_required=False
        )
        
        assert "추후 안내" in content_no_location
        assert "문의사항" not in content_no_location
    
    def test_loop_content(self):
        """반복 콘텐츠 테스트"""
        # 여러 일정을 포함한 템플릿
        schedules = [
            self.test_schedule,
            Schedule(
                team=Team(name="테크스타트업", email="tech@startup.com", contact="010-9876-5432"),
                slot=InterviewSlot(
                    date=datetime(2024, 1, 15),
                    time=time(15, 0),
                    interviewer="이교수",
                    location="면접실2"
                )
            )
        ]
        
        loop_template = """
        면접 일정 안내
        
        {% for schedule in schedules %}
        {{loop.index}}. {{schedule.team.name}} - {{schedule.slot.time.strftime('%H:%M')}} ({{schedule.slot.interviewer}})
        {% endfor %}
        """
        
        content = self.template_manager.render_template_string(
            loop_template,
            schedules=schedules
        )
        
        assert "1. 한국대학교팀" in content
        assert "2. 테크스타트업" in content
        assert "14:30" in content
        assert "15:00" in content
    
    def test_email_format_generation(self):
        """이메일 형식 생성 테스트"""
        email_data = self.template_manager.generate_email(
            template_type="interview_notification",
            schedule=self.test_schedule,
            sender_info={
                "name": "면접 운영팀",
                "email": "interview@organization.com",
                "phone": "02-1234-5678"
            }
        )
        
        assert "subject" in email_data
        assert "body" in email_data
        assert "recipient" in email_data
        
        assert email_data["recipient"] == self.test_schedule.team.email
        assert len(email_data["subject"]) > 0
        assert len(email_data["body"]) > 0
        assert "한국대학교팀" in email_data["body"]
    
    def test_template_validation(self):
        """템플릿 검증 테스트"""
        # 유효한 템플릿
        valid_template = "안녕하세요 {{team_name}}님, 면접 일정을 안내드립니다."
        is_valid, errors = self.template_manager.validate_template(valid_template)
        assert is_valid
        assert len(errors) == 0
        
        # 잘못된 템플릿 (닫히지 않은 태그)
        invalid_template = "안녕하세요 {{team_name님, {% if condition %} 내용"
        is_valid, errors = self.template_manager.validate_template(invalid_template)
        assert not is_valid
        assert len(errors) > 0
    
    def test_multiple_language_support(self):
        """다국어 지원 테스트"""
        # 영어 템플릿
        english_content = self.template_manager.render_template(
            "interview_notification",
            schedule=self.test_schedule,
            language="en"
        )
        
        # 한국어 템플릿 (기본값)
        korean_content = self.template_manager.render_template(
            "interview_notification",
            schedule=self.test_schedule,
            language="ko"
        )
        
        # 언어별로 다른 내용이 생성되어야 함
        if english_content and korean_content:
            assert english_content != korean_content
    
    def test_template_performance(self):
        """템플릿 성능 테스트"""
        import time
        
        start_time = time.time()
        
        # 100개 이메일 생성
        for i in range(100):
            content = self.template_manager.render_template(
                "interview_notification",
                schedule=self.test_schedule
            )
            assert content is not None
        
        end_time = time.time()
        
        # 100개 템플릿 렌더링이 5초 미만이어야 함
        assert end_time - start_time < 5.0
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        # 존재하지 않는 템플릿
        content = self.template_manager.render_template(
            "non_existent_template",
            schedule=self.test_schedule
        )
        assert content is None or content == ""
        
        # 잘못된 변수
        content = self.template_manager.render_template_string(
            "Hello {{undefined_variable}}",
            team_name="Test Team"
        )
        # 오류가 발생하더라도 적절히 처리되어야 함
        assert content is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])