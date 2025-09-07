"""
PDF 데이터 추출 모듈 테스트 (한국어 텍스트 지원)
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_extractor import PDFExtractor
from core.models import Team


class TestPDFExtractor:
    """PDF 추출기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.extractor = PDFExtractor()
        
        # 테스트용 샘플 데이터
        self.sample_text_data = """
        팀명: 한국대학교팀
        이메일: korea@university.ac.kr
        연락처: 010-1234-5678
        선호시간: 14:00, 15:00
        피하고싶은 면접관: 김교수
        
        팀명: 테크스타트업
        이메일: contact@techstartup.co.kr
        연락처: 010-9876-5432
        선호시간: 10:00, 11:00
        피하고싶은 면접관: 없음
        """
        
        self.sample_table_data = [
            ["팀명", "이메일", "연락처", "선호시간"],
            ["한국대학교팀", "korea@university.ac.kr", "010-1234-5678", "14:00, 15:00"],
            ["테크스타트업", "contact@techstartup.co.kr", "010-9876-5432", "10:00, 11:00"]
        ]
    
    def test_korean_text_validation(self):
        """한국어 텍스트 검증 테스트"""
        korean_text = "한국대학교팀"
        english_text = "KoreaUniversity"
        mixed_text = "한국대학교Team"
        
        assert self.extractor._contains_korean(korean_text)
        assert not self.extractor._contains_korean(english_text)
        assert self.extractor._contains_korean(mixed_text)
    
    def test_email_extraction_patterns(self):
        """이메일 추출 패턴 테스트"""
        test_cases = [
            ("이메일: korea@university.ac.kr 연락처", ["korea@university.ac.kr"]),
            ("Email: contact@techstartup.co.kr Phone", ["contact@techstartup.co.kr"]),
            ("test1@gmail.com, test2@naver.com", ["test1@gmail.com", "test2@naver.com"]),
            ("유효하지않은@이메일", []),
            ("admin@한국대학교.kr", ["admin@한국대학교.kr"])
        ]
        
        for text, expected in test_cases:
            emails = self.extractor._extract_emails_from_text(text)
            assert emails == expected, f"Failed for text: {text}"
    
    def test_phone_number_extraction(self):
        """전화번호 추출 테스트"""
        test_cases = [
            ("010-1234-5678", ["010-1234-5678"]),
            ("핸드폰: 010.1234.5678", ["010.1234.5678"]),
            ("연락처 01012345678", ["01012345678"]),
            ("02-123-4567", ["02-123-4567"]),
            ("070-1234-5678", ["070-1234-5678"]),
            ("유효하지않은번호", [])
        ]
        
        for text, expected in test_cases:
            phones = self.extractor._extract_phone_numbers(text)
            assert phones == expected, f"Failed for text: {text}"
    
    def test_time_preference_extraction(self):
        """시간 선호도 추출 테스트"""
        test_cases = [
            ("선호시간: 14:00, 15:00", ["14:00", "15:00"]),
            ("오전 10시, 오후 2시", ["10:00", "14:00"]),
            ("14시 30분, 15시", ["14:30", "15:00"]),
            ("아무 시간이나", []),
            ("9:00-12:00", ["9:00", "10:00", "11:00", "12:00"])
        ]
        
        for text, expected in test_cases:
            times = self.extractor._extract_time_preferences(text)
            # 시간 형식이 일치하는지 확인 (순서는 상관없음)
            assert set(times) == set(expected), f"Failed for text: {text}"
    
    def test_interviewer_avoidance_extraction(self):
        """면접관 회피 정보 추출 테스트"""
        test_cases = [
            ("피하고싶은 면접관: 김교수", ["김교수"]),
            ("면접관 회피: 이교수, 박교수", ["이교수", "박교수"]),
            ("피하고싶은 면접관: 없음", []),
            ("특별한 요청사항 없음", []),
            ("김교수님은 피하고싶습니다", ["김교수"])
        ]
        
        for text, expected in test_cases:
            interviewers = self.extractor._extract_interviewer_avoidance(text)
            assert set(interviewers) == set(expected), f"Failed for text: {text}"
    
    @patch('pdfplumber.open')
    def test_pdfplumber_extraction(self, mock_pdf_open):
        """pdfplumber 추출 전략 테스트"""
        # Mock PDF 페이지 설정
        mock_page = MagicMock()
        mock_page.extract_text.return_value = self.sample_text_data
        mock_page.extract_tables.return_value = [self.sample_table_data]
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf_open.return_value = mock_pdf
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            teams = self.extractor._extract_with_pdfplumber(tmp_path)
            
            assert len(teams) >= 2
            team_names = [team.name for team in teams]
            assert "한국대학교팀" in team_names
            assert "테크스타트업" in team_names
            
            # 첫 번째 팀 검증
            korea_team = next(team for team in teams if team.name == "한국대학교팀")
            assert korea_team.email == "korea@university.ac.kr"
            assert korea_team.contact == "010-1234-5678"
            assert "14:00" in korea_team.preferred_times
            assert "김교수" in korea_team.avoid_interviewers
            
        finally:
            os.unlink(tmp_path)
    
    def test_team_data_validation_and_cleaning(self):
        """팀 데이터 검증 및 정제 테스트"""
        # 유효한 팀 데이터
        valid_teams = [
            Team(
                name="한국대학교팀",
                email="korea@university.ac.kr",
                contact="010-1234-5678"
            )
        ]
        
        # 유효하지 않은 팀 데이터
        invalid_teams = [
            Team(name="", email="invalid-email", contact="wrong-phone"),
            Team(name="Valid팀", email="valid@test.com", contact="010-1234-5678"),
            Team(name="중복팀", email="dup1@test.com", contact="010-1111-1111"),
            Team(name="중복팀", email="dup2@test.com", contact="010-2222-2222")
        ]
        
        all_teams = valid_teams + invalid_teams
        cleaned_teams = self.extractor._validate_and_clean_teams(all_teams)
        
        # 유효한 팀만 남아있어야 함
        assert len(cleaned_teams) == 2  # valid_teams[0]과 invalid_teams[1]
        team_names = [team.name for team in cleaned_teams]
        assert "한국대학교팀" in team_names
        assert "Valid팀" in team_names
        assert "중복팀" in team_names  # 중복 중 하나는 남음
    
    def test_fallback_extraction_strategy(self):
        """대체 추출 전략 테스트"""
        with patch.object(self.extractor, '_extract_with_pdfplumber') as mock_pdfplumber, \
             patch.object(self.extractor, '_extract_with_pypdf2') as mock_pypdf2, \
             patch.object(self.extractor, '_extract_with_pymupdf') as mock_pymupdf:
            
            # pdfplumber 실패 시뮬레이션
            mock_pdfplumber.side_effect = Exception("pdfplumber failed")
            
            # pypdf2 성공 시뮬레이션
            mock_pypdf2.return_value = [
                Team(name="테스트팀", email="test@example.com", contact="010-1234-5678")
            ]
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                teams = self.extractor.extract_team_data(tmp_path)
                
                # pdfplumber 실패 후 pypdf2로 대체되었는지 확인
                mock_pdfplumber.assert_called_once()
                mock_pypdf2.assert_called_once()
                mock_pymupdf.assert_not_called()
                
                assert len(teams) == 1
                assert teams[0].name == "테스트팀"
                
            finally:
                os.unlink(tmp_path)
    
    def test_encoding_handling(self):
        """인코딩 처리 테스트"""
        # 다양한 인코딩 테스트 데이터
        test_texts = [
            "한국어 팀명",
            "English Team Name",
            "混合語言팀",
            "Émojis 👍 Team"
        ]
        
        for text in test_texts:
            # 한국어 감지가 올바르게 작동하는지 확인
            contains_korean = self.extractor._contains_korean(text)
            expected = any('가' <= char <= '힣' for char in text)
            assert contains_korean == expected, f"Failed for text: {text}"
    
    def test_performance_with_large_dataset(self):
        """대용량 데이터셋 성능 테스트"""
        # 100개 팀 데이터 시뮬레이션
        large_dataset = []
        for i in range(100):
            team = Team(
                name=f"팀{i:03d}",
                email=f"team{i:03d}@test.com",
                contact=f"010-{i:04d}-{i:04d}",
                preferred_times=[f"{10 + (i % 8)}:00"],
                avoid_interviewers=[f"교수{i % 5}"] if i % 3 == 0 else []
            )
            large_dataset.append(team)
        
        # 검증 및 정제 성능 테스트
        import time
        start_time = time.time()
        cleaned_teams = self.extractor._validate_and_clean_teams(large_dataset)
        end_time = time.time()
        
        # 처리 시간이 1초 미만이어야 함
        assert end_time - start_time < 1.0
        assert len(cleaned_teams) == 100  # 모든 팀이 유효해야 함
    
    def test_error_recovery_and_logging(self):
        """오류 복구 및 로깅 테스트"""
        with patch('builtins.print') as mock_print:  # 로깅 출력 캡처
            # 존재하지 않는 파일 처리
            non_existent_file = "/path/to/non/existent/file.pdf"
            teams = self.extractor.extract_team_data(non_existent_file)
            
            # 빈 리스트 반환되어야 함
            assert teams == []
            
            # 오류 로깅 확인
            mock_print.assert_called()
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("오류" in call or "error" in call.lower() for call in print_calls)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])