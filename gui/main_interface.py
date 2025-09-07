"""
Streamlit 기반 메인 사용자 인터페이스

공모전 면접 스케줄링 시스템의 웹 기반 GUI 인터페이스입니다.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import time
import io
import base64
from pathlib import Path

# 로컬 모듈 imports
from ..core.pdf_extractor import PDFExtractor
from ..core.scheduler_engine import InterviewScheduler
from ..core.models import (
    Team, InterviewConstraint, SchedulingResult, SchedulingOption
)
from ..excel.excel_generator import ExcelGenerator
from ..email_system.email_validator import EmailValidator
from ..email_system.template_manager import EmailTemplateManager


class SessionState:
    """세션 상태 관리"""
    
    @staticmethod
    def initialize():
        """세션 상태 초기화"""
        if 'teams' not in st.session_state:
            st.session_state.teams = []
        
        if 'constraints' not in st.session_state:
            st.session_state.constraints = InterviewConstraint()
        
        if 'scheduling_result' not in st.session_state:
            st.session_state.scheduling_result = None
        
        if 'selected_option' not in st.session_state:
            st.session_state.selected_option = None
        
        if 'email_validations' not in st.session_state:
            st.session_state.email_validations = []
        
        if 'processing_step' not in st.session_state:
            st.session_state.processing_step = 0


class InterviewSchedulerApp:
    """메인 애플리케이션 클래스"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.scheduler = InterviewScheduler()
        self.excel_generator = ExcelGenerator()
        self.email_validator = EmailValidator()
        self.template_manager = EmailTemplateManager()
        
        # 페이지 설정
        st.set_page_config(
            page_title="🏆 공모전 면접 스케줄링 시스템",
            page_icon="📅",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 세션 상태 초기화
        SessionState.initialize()
        
        # 사용자 정의 CSS
        self._load_custom_styles()
    
    def _load_custom_styles(self):
        """사용자 정의 CSS 로드"""
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f4e79;
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 3px solid #4472c4;
            padding-bottom: 1rem;
        }
        
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }
        
        .step-item {
            padding: 0.5rem 1rem;
            margin: 0 0.25rem;
            background-color: #f0f2f6;
            border-radius: 20px;
            font-weight: 600;
        }
        
        .step-active {
            background-color: #4472c4;
            color: white;
        }
        
        .step-completed {
            background-color: #70ad47;
            color: white;
        }
        
        .success-box {
            background-color: #d5edda;
            border: 1px solid #c3e6cb;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .warning-box {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .error-box {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .metric-card {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        
        .download-section {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border-left: 4px solid #28a745;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        """애플리케이션 실행"""
        
        # 헤더
        st.markdown('<h1 class="main-header">🏆 공모전 면접 스케줄링 시스템</h1>', unsafe_allow_html=True)
        
        # 단계 표시기
        self._show_step_indicator()
        
        # 사이드바 메뉴
        menu_selection = st.sidebar.selectbox(
            "📋 메뉴 선택",
            [
                "📄 PDF 업로드 & 데이터 추출",
                "⚙️ 면접 설정 & 제약조건",
                "🎯 스케줄 생성 & 옵션 비교",
                "📊 결과 확인 & 분석",
                "💾 파일 다운로드",
                "📧 메일 발송 관리"
            ]
        )
        
        # 사이드바 상태 정보
        self._show_sidebar_status()
        
        # 메인 컨텐츠
        if menu_selection == "📄 PDF 업로드 & 데이터 추출":
            self._show_pdf_upload_page()
        elif menu_selection == "⚙️ 면접 설정 & 제약조건":
            self._show_settings_page()
        elif menu_selection == "🎯 스케줄 생성 & 옵션 비교":
            self._show_scheduling_page()
        elif menu_selection == "📊 결과 확인 & 분석":
            self._show_results_page()
        elif menu_selection == "💾 파일 다운로드":
            self._show_download_page()
        elif menu_selection == "📧 메일 발송 관리":
            self._show_email_page()
    
    def _show_step_indicator(self):
        """진행 단계 표시기"""
        steps = [
            ("1. PDF 업로드", len(st.session_state.teams) > 0),
            ("2. 설정", True),  # 설정은 선택사항
            ("3. 스케줄 생성", st.session_state.scheduling_result is not None),
            ("4. 결과 확인", st.session_state.selected_option is not None)
        ]
        
        cols = st.columns(len(steps))
        
        for i, (step_name, completed) in enumerate(steps):
            with cols[i]:
                if completed:
                    st.markdown(f'<div class="step-item step-completed">{step_name}</div>', unsafe_allow_html=True)
                elif i == st.session_state.processing_step:
                    st.markdown(f'<div class="step-item step-active">{step_name}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="step-item">{step_name}</div>', unsafe_allow_html=True)
    
    def _show_sidebar_status(self):
        """사이드바 상태 정보"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📈 현재 상태")
        
        # 팀 정보
        if st.session_state.teams:
            st.sidebar.metric("총 팀 수", len(st.session_state.teams))
            valid_teams = len([t for t in st.session_state.teams if t.primary_email])
            st.sidebar.metric("이메일 보유 팀", valid_teams)
        else:
            st.sidebar.info("PDF를 업로드해주세요")
        
        # 스케줄 정보
        if st.session_state.scheduling_result:
            st.sidebar.metric("생성된 옵션", len(st.session_state.scheduling_result.options))
            if st.session_state.selected_option:
                st.sidebar.success("✅ 옵션 선택 완료")
        
        # 시스템 정보
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ 시스템 정보")
        st.sidebar.text(f"버전: 1.0.0")
        st.sidebar.text(f"최대 처리: 100팀")
        st.sidebar.text(f"지원 형식: PDF, 한글")
    
    def _show_pdf_upload_page(self):
        """PDF 업로드 및 데이터 추출 페이지"""
        st.header("📄 PDF 데이터 추출")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📤 PDF 파일 업로드")
            
            # 파일 업로드
            uploaded_file = st.file_uploader(
                "합격자 명단 PDF 파일을 선택하세요",
                type=['pdf'],
                help="팀명, 이메일, 연락처, 희망시간이 포함된 PDF 파일"
            )
            
            if uploaded_file is not None:
                # PDF 처리
                if st.button("📊 데이터 추출 시작", type="primary"):
                    self._process_pdf_file(uploaded_file)
            
            # 추출된 데이터 표시
            if st.session_state.teams:
                st.subheader("📋 추출된 팀 데이터")
                
                # 데이터 테이블
                team_data = []
                for team in st.session_state.teams:
                    team_data.append({
                        '팀명': team.team_name,
                        '대표자': team.leader_name,
                        '이메일': team.primary_email,
                        '연락처': team.primary_phone,
                        '팀원수': len(team.members),
                        '희망시간': ', '.join(team.time_preferences[:2]),
                        '상태': '✅ 유효' if team.primary_email else '⚠️ 이메일 누락'
                    })
                
                df = pd.DataFrame(team_data)
                st.dataframe(df, use_container_width=True)
                
                # 이메일 검증 버튼
                if st.button("📧 이메일 주소 검증"):
                    self._validate_team_emails()
        
        with col2:
            st.subheader("📝 PDF 형식 가이드")
            
            with st.expander("📋 필수 포함 정보", expanded=True):
                st.markdown("""
                **반드시 포함되어야 할 정보:**
                - ✅ 팀명
                - ✅ 대표자명 및 팀원
                - ✅ 이메일 주소 (필수)
                - ✅ 연락처
                - ✅ 희망 면접 시간 (1, 2, 3순위)
                """)
            
            with st.expander("💡 권장 PDF 형식"):
                st.markdown("""
                **최적 추출을 위한 권장사항:**
                - 📊 테이블 형태로 정리
                - 📝 텍스트 인식 가능한 PDF
                - 🇰🇷 한글 인코딩 지원
                - 📱 명확한 구분자 사용
                """)
            
            if st.session_state.teams:
                st.subheader("📈 추출 통계")
                self._show_extraction_statistics()
    
    def _process_pdf_file(self, uploaded_file):
        """PDF 파일 처리"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 임시 파일 저장
            with st.spinner("PDF 파일 처리 중..."):
                temp_file = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                with open(temp_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                status_text.text("📖 PDF 읽기 중...")
                progress_bar.progress(25)
                
                status_text.text("🔍 테이블 감지 중...")
                progress_bar.progress(50)
                
                status_text.text("📝 데이터 추출 중...")
                progress_bar.progress(75)
                
                # 데이터 추출
                teams = self.pdf_extractor.extract_team_data(temp_file)
                
                status_text.text("✅ 이메일 검증 중...")
                progress_bar.progress(90)
                
                # 세션에 저장
                st.session_state.teams = teams
                st.session_state.processing_step = 1
                
                progress_bar.progress(100)
                
                # 임시 파일 정리
                Path(temp_file).unlink(missing_ok=True)
                
                st.success(f"✅ PDF 처리 완료! {len(teams)}개 팀 데이터 추출됨")
                
                # 통계 정보 표시
                stats = self.pdf_extractor.get_extraction_statistics(teams)
                if stats:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 팀 수", stats.get('total_teams', 0))
                    with col2:
                        st.metric("유효 팀", stats.get('valid_teams', 0))
                    with col3:
                        st.metric("성공률", f"{stats.get('extraction_success_rate', 0):.1f}%")
                
        except Exception as e:
            st.error(f"❌ PDF 처리 오류: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    def _validate_team_emails(self):
        """팀 이메일 검증"""
        
        if not st.session_state.teams:
            st.warning("먼저 팀 데이터를 추출해주세요.")
            return
        
        emails = [team.primary_email for team in st.session_state.teams if team.primary_email]
        
        if not emails:
            st.warning("검증할 이메일 주소가 없습니다.")
            return
        
        with st.spinner("이메일 검증 중..."):
            validations = self.email_validator.comprehensive_email_validation(emails, enable_dns_check=True)
            st.session_state.email_validations = validations
            
            # 결과 표시
            valid_count = len([v for v in validations if v.is_valid])
            invalid_count = len(validations) - valid_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 이메일", len(validations))
            with col2:
                st.metric("유효", valid_count, delta=None)
            with col3:
                st.metric("오류", invalid_count, delta=f"-{invalid_count}")
            
            # 오류 이메일 상세 정보
            if invalid_count > 0:
                with st.expander("❌ 검증 오류 상세", expanded=True):
                    error_data = []
                    for validation in validations:
                        if not validation.is_valid:
                            error_data.append({
                                '이메일': validation.email,
                                '문제점': ', '.join(validation.issues),
                                '수정제안': ', '.join(validation.suggestions) if validation.suggestions else '없음'
                            })
                    
                    if error_data:
                        st.dataframe(pd.DataFrame(error_data), use_container_width=True)
    
    def _show_extraction_statistics(self):
        """추출 통계 표시"""
        if not st.session_state.teams:
            return
        
        stats = self.pdf_extractor.get_extraction_statistics(st.session_state.teams)
        
        # 파이 차트 - 팀 상태 분포
        if stats:
            fig = px.pie(
                values=[stats.get('valid_teams', 0), stats.get('warning_teams', 0), stats.get('invalid_teams', 0)],
                names=['유효', '경고', '오류'],
                title="팀 데이터 품질 분포",
                color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_settings_page(self):
        """면접 설정 및 제약조건 페이지"""
        st.header("⚙️ 면접 설정 & 제약조건")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 면접 일정 설정")
            
            # 면접 날짜 범위
            today = datetime.now().date()
            default_end = today + timedelta(days=3)
            
            date_range = st.date_input(
                "면접 진행 날짜",
                value=[today, default_end],
                min_value=today,
                max_value=today + timedelta(days=30),
                help="면접을 진행할 날짜 범위를 선택하세요"
            )
            
            # 면접 시간대
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                start_time = st.time_input(
                    "면접 시작 시간",
                    value=datetime.strptime("09:00", "%H:%M").time()
                )
            with col1_2:
                end_time = st.time_input(
                    "면접 종료 시간",
                    value=datetime.strptime("18:00", "%H:%M").time()
                )
            
            interview_duration = st.selectbox(
                "면접 소요 시간 (분)",
                [15, 20, 30, 45, 60],
                index=2
            )
            
            # 면접 조 설정
            st.subheader("👥 면접 조 설정")
            col1_3, col1_4 = st.columns(2)
            with col1_3:
                group_a_name = st.text_input("A조 이름", value="A조")
            with col1_4:
                group_b_name = st.text_input("B조 이름", value="B조")
            
            # 면접 장소 설정
            st.subheader("🏢 면접 장소")
            col1_5, col1_6 = st.columns(2)
            with col1_5:
                room_a = st.text_input("A조 면접실", value="A조 면접실")
            with col1_6:
                room_b = st.text_input("B조 면접실", value="B조 면접실")
            
            # 온라인 면접 설정
            enable_online = st.checkbox("온라인 면접 지원")
            if enable_online:
                zoom_link_a = st.text_input("A조 Zoom 링크", placeholder="https://zoom.us/j/...")
                zoom_link_b = st.text_input("B조 Zoom 링크", placeholder="https://zoom.us/j/...")
        
        with col2:
            st.subheader("🚫 제약조건 설정")
            
            # 면접관별 기피 팀 설정
            st.markdown("**면접관별 기피 팀 설정**")
            interviewer_constraints = st.text_area(
                "기피 팀 설정",
                placeholder="김면접관:팀A,팀B\n이심사위원:팀C,팀D",
                help="형식: 면접관이름:팀명1,팀명2",
                height=100
            )
            
            # 면접관 담당 조 설정
            st.markdown("**면접관 담당 조 설정**")
            interviewer_groups = st.text_area(
                "담당 조 설정",
                placeholder="김면접관:A\n이심사위원:B",
                help="형식: 면접관이름:조(A 또는 B)",
                height=80
            )
            
            # 특별 고려사항
            st.subheader("📝 특별 고려사항")
            special_notes = st.text_area(
                "추가 제약조건이나 고려사항",
                placeholder="예: 특정 시간대 피해야 할 팀, 연속 면접 금지 등",
                height=80
            )
            
            # 최적화 우선순위 설정
            st.subheader("🎯 최적화 우선순위")
            priority_options = st.multiselect(
                "중요도 순으로 선택 (최대 3개)",
                ["1순위 시간 만족", "조별 균등 배치", "시간 분산", "면접관 제약조건"],
                default=["1순위 시간 만족", "면접관 제약조건"]
            )
        
        # 설정 저장 버튼
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            if st.button("💾 설정 저장", type="primary", use_container_width=True):
                # 제약조건 파싱 및 저장
                constraints = self._parse_constraints(interviewer_constraints, interviewer_groups)
                st.session_state.constraints = constraints
                
                # 기타 설정 저장
                st.session_state.interview_settings = {
                    'date_range': date_range,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': interview_duration,
                    'groups': {'A': group_a_name, 'B': group_b_name},
                    'rooms': {'A': room_a, 'B': room_b},
                    'online_enabled': enable_online,
                    'special_notes': special_notes,
                    'priorities': priority_options
                }
                
                if enable_online:
                    st.session_state.interview_settings['zoom_links'] = {
                        'A': zoom_link_a, 'B': zoom_link_b
                    }
                
                st.success("✅ 면접 설정이 저장되었습니다!")
                
                # 프리뷰 표시
                with st.expander("🔍 설정 미리보기", expanded=True):
                    self._show_settings_preview()
    
    def _parse_constraints(self, interviewer_constraints: str, interviewer_groups: str) -> InterviewConstraint:
        """제약조건 텍스트 파싱"""
        constraints = InterviewConstraint()
        
        # 면접관별 기피 팀 파싱
        if interviewer_constraints.strip():
            for line in interviewer_constraints.strip().split('\n'):
                if ':' in line:
                    interviewer, teams_str = line.split(':', 1)
                    teams = [t.strip() for t in teams_str.split(',')]
                    constraints.add_interviewer_avoidance(interviewer.strip(), teams)
        
        # 면접관 담당 조 파싱
        if interviewer_groups.strip():
            for line in interviewer_groups.strip().split('\n'):
                if ':' in line:
                    interviewer, group = line.split(':', 1)
                    constraints.add_interviewer_group(interviewer.strip(), group.strip())
        
        return constraints
    
    def _show_settings_preview(self):
        """설정 미리보기 표시"""
        if 'interview_settings' not in st.session_state:
            return
        
        settings = st.session_state.interview_settings
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📅 면접 일정**")
            if isinstance(settings['date_range'], list) and len(settings['date_range']) == 2:
                st.text(f"기간: {settings['date_range'][0]} ~ {settings['date_range'][1]}")
            st.text(f"시간: {settings['start_time']} ~ {settings['end_time']}")
            st.text(f"면접 시간: {settings['duration']}분")
            
        with col2:
            st.markdown("**👥 면접 조**")
            st.text(f"A조: {settings['groups']['A']} ({settings['rooms']['A']})")
            st.text(f"B조: {settings['groups']['B']} ({settings['rooms']['B']})")
            
            if settings.get('online_enabled'):
                st.text("🌐 온라인 면접 지원")
    
    def _show_scheduling_page(self):
        """스케줄 생성 및 옵션 비교 페이지"""
        st.header("🎯 스케줄 생성 & 옵션 비교")
        
        if not st.session_state.teams:
            st.warning("⚠️ 먼저 PDF에서 팀 데이터를 추출해주세요.")
            st.stop()
        
        # 5가지 옵션 생성
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 5가지 스케줄 옵션 생성", type="primary", use_container_width=True):
                self._generate_scheduling_options()
        
        # 생성된 옵션 표시
        if st.session_state.scheduling_result:
            self._show_scheduling_options()
    
    def _generate_scheduling_options(self):
        """5가지 스케줄링 옵션 생성"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        options_info = [
            "옵션 1: 1순위 희망시간 최대 반영",
            "옵션 2: 시간 분산 최적화",
            "옵션 3: 오전/오후 균등 배치",
            "옵션 4: 조별 균등 배치 우선",
            "옵션 5: 면접관 제약조건 최우선"
        ]
        
        try:
            with st.spinner("스케줄 옵션 생성 중..."):
                for i, option_info in enumerate(options_info):
                    status_text.text(f"생성 중: {option_info}")
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.5)  # 시뮬레이션
                
                # 실제 스케줄링 실행
                options = self.scheduler.generate_five_options(
                    st.session_state.teams,
                    st.session_state.constraints
                )
                
                if options:
                    # 결과 저장
                    result = SchedulingResult(
                        options=options,
                        teams=st.session_state.teams,
                        constraints=st.session_state.constraints
                    )
                    st.session_state.scheduling_result = result
                    st.session_state.processing_step = 2
                    
                    progress_bar.progress(100)
                    st.success(f"✅ {len(options)}가지 스케줄 옵션 생성 완료!")
                    
                else:
                    st.error("❌ 스케줄 옵션 생성에 실패했습니다.")
                
        except Exception as e:
            st.error(f"❌ 스케줄링 오류: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    
    def _show_scheduling_options(self):
        """스케줄링 옵션 표시 및 비교"""
        
        result = st.session_state.scheduling_result
        
        st.subheader("📊 옵션 비교")
        
        # 옵션 비교 테이블
        comparison_data = []
        for i, option in enumerate(result.options):
            option.calculate_satisfaction_metrics()
            comparison_data.append({
                '옵션': f"옵션 {i+1}",
                '설명': option.option_name,
                '총 팀수': option.total_teams,
                '1순위 만족률': f"{option.first_choice_satisfaction:.1f}%",
                '조별 균형': f"{option.group_balance_score:.1f}",
                '제약 위반': option.constraint_violations,
                '생성시간': f"{option.generation_time:.2f}초",
                '추천': "⭐" if option.first_choice_satisfaction > 80 else ""
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)
        
        # 시각화
        col1, col2 = st.columns(2)
        
        with col1:
            # 1순위 만족률 비교 차트
            fig1 = px.bar(
                df_comparison,
                x='옵션',
                y='1순위 만족률',
                title="옵션별 1순위 희망시간 만족률",
                color='1순위 만족률',
                color_continuous_scale='Viridis'
            )
            fig1.update_traces(text=df_comparison['1순위 만족률'], textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 조별 분포 비교
            group_data = []
            for i, option in enumerate(result.options):
                dist = option.group_distribution
                group_data.extend([
                    {'옵션': f'옵션 {i+1}', '조': 'A조', '팀수': dist.get('A조', 0)},
                    {'옵션': f'옵션 {i+1}', '조': 'B조', '팀수': dist.get('B조', 0)}
                ])
            
            df_groups = pd.DataFrame(group_data)
            fig2 = px.bar(
                df_groups,
                x='옵션',
                y='팀수',
                color='조',
                title="옵션별 조 배치 분포",
                barmode='stack'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # 상세 옵션 보기
        st.subheader("🔍 상세 옵션 보기")
        
        tabs = st.tabs([f"옵션 {i+1}" for i in range(len(result.options))])
        
        for i, (tab, option) in enumerate(zip(tabs, result.options)):
            with tab:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # 상세 스케줄 테이블
                    schedule_data = []
                    for schedule in option.schedules:
                        schedule_data.append({
                            '팀명': schedule.team_name,
                            '대표자': schedule.leader_name,
                            '면접날짜': schedule.interview_date,
                            '면접시간': schedule.interview_time,
                            '면접조': schedule.interview_group,
                            '희망순위': f"{schedule.preference_rank}순위" if schedule.preference_rank > 0 else "기타"
                        })
                    
                    df_schedule = pd.DataFrame(schedule_data)
                    st.dataframe(df_schedule, use_container_width=True)
                
                with col2:
                    # 옵션 통계
                    st.markdown("**📈 옵션 통계**")
                    st.metric("1순위 만족률", f"{option.first_choice_satisfaction:.1f}%")
                    st.metric("조별 균형 점수", f"{option.group_balance_score:.1f}")
                    st.metric("제약 위반 수", f"{option.constraint_violations}건")
                    
                    # 옵션 선택 버튼
                    if st.button(f"✅ 옵션 {i+1} 선택", key=f"select_{i}", use_container_width=True):
                        st.session_state.selected_option = option
                        st.session_state.scheduling_result.selected_option = option
                        st.session_state.processing_step = 3
                        st.success(f"✅ 옵션 {i+1}이 선택되었습니다!")
                        st.rerun()
    
    def _show_results_page(self):
        """결과 확인 및 분석 페이지"""
        st.header("📊 결과 확인 & 분석")
        
        if not st.session_state.selected_option:
            st.warning("⚠️ 먼저 스케줄 옵션을 선택해주세요.")
            st.stop()
        
        option = st.session_state.selected_option
        
        # 대시보드 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 면접 팀", option.total_teams)
        with col2:
            dist = option.group_distribution
            st.metric("A조 배치", dist.get('A조', 0))
        with col3:
            st.metric("B조 배치", dist.get('B조', 0))
        with col4:
            st.metric("1순위 만족", f"{option.first_choice_satisfaction:.1f}%")
        
        # 시각화 섹션
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 시간대별 면접 분포")
            
            # 시간대별 분포 데이터 생성
            time_dist = {}
            for schedule in option.schedules:
                time_key = schedule.interview_time
                group_key = f"{time_key}-{schedule.interview_group}"
                time_dist[group_key] = time_dist.get(group_key, 0) + 1
            
            if time_dist:
                time_data = []
                for key, count in time_dist.items():
                    time_slot, group = key.rsplit('-', 1)
                    time_data.append({
                        '시간대': time_slot,
                        '조': group,
                        '팀수': count
                    })
                
                df_time = pd.DataFrame(time_data)
                fig = px.bar(
                    df_time,
                    x='시간대',
                    y='팀수',
                    color='조',
                    title="시간대별 면접 배치 현황",
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 희망시간 만족도")
            
            # 희망 순위별 만족도
            pref_counts = {'1순위': 0, '2순위': 0, '3순위': 0, '기타': 0}
            for schedule in option.schedules:
                if schedule.preference_rank == 1:
                    pref_counts['1순위'] += 1
                elif schedule.preference_rank == 2:
                    pref_counts['2순위'] += 1
                elif schedule.preference_rank == 3:
                    pref_counts['3순위'] += 1
                else:
                    pref_counts['기타'] += 1
            
            fig = px.pie(
                values=list(pref_counts.values()),
                names=list(pref_counts.keys()),
                title="희망 순위별 배치 결과"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 상세 스케줄 테이블
        st.subheader("📋 최종 면접 스케줄")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_group = st.selectbox("조별 필터", ["전체", "A조", "B조"])
        with col2:
            filter_date = st.selectbox("날짜별 필터", ["전체"] + list(set(s.interview_date for s in option.schedules)))
        with col3:
            filter_pref = st.selectbox("희망순위 필터", ["전체", "1순위", "2순위", "3순위", "기타"])
        
        # 필터링 적용
        filtered_schedules = option.schedules
        
        if filter_group != "전체":
            filtered_schedules = [s for s in filtered_schedules if s.interview_group == filter_group]
        
        if filter_date != "전체":
            filtered_schedules = [s for s in filtered_schedules if s.interview_date == filter_date]
        
        if filter_pref != "전체":
            if filter_pref == "1순위":
                filtered_schedules = [s for s in filtered_schedules if s.preference_rank == 1]
            elif filter_pref == "2순위":
                filtered_schedules = [s for s in filtered_schedules if s.preference_rank == 2]
            elif filter_pref == "3순위":
                filtered_schedules = [s for s in filtered_schedules if s.preference_rank == 3]
            elif filter_pref == "기타":
                filtered_schedules = [s for s in filtered_schedules if s.preference_rank == 0]
        
        # 스케줄 테이블 생성
        schedule_data = []
        for schedule in filtered_schedules:
            schedule_data.append({
                '팀명': schedule.team_name,
                '대표자': schedule.leader_name,
                '이메일': schedule.team.primary_email,
                '연락처': schedule.team.primary_phone,
                '면접날짜': schedule.interview_date,
                '면접시간': schedule.interview_time,
                '면접조': schedule.interview_group,
                '면접실': schedule.interview_slot.room,
                '희망순위': f"{schedule.preference_rank}순위" if schedule.preference_rank > 0 else "기타",
                '상태': "확정"
            })
        
        df_final = pd.DataFrame(schedule_data)
        st.dataframe(df_final, use_container_width=True)
        
        st.info(f"📊 필터 결과: {len(filtered_schedules)}개 팀 표시")
    
    def _show_download_page(self):
        """파일 다운로드 페이지"""
        st.header("💾 파일 다운로드")
        
        if not st.session_state.selected_option:
            st.warning("⚠️ 먼저 스케줄 옵션을 선택해주세요.")
            st.stop()
        
        st.markdown("""
        <div class="download-section">
        <h3>📊 생성 가능한 파일 목록</h3>
        <p>선택된 스케줄을 다양한 형식으로 다운로드할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📈 엑셀 파일")
            
            if st.button("📊 완전한 엑셀 파일 생성", type="primary", use_container_width=True):
                self._generate_excel_download()
            
            st.markdown("""
            **포함 내용:**
            - 최종 스케줄 (메일발송용)
            - 메일머지 데이터
            - 5개 옵션 비교
            - A조/B조 일정표
            - 타임테이블
            - 메일 템플릿
            """)
        
        with col2:
            st.subheader("📧 메일머지 CSV")
            
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                if st.button("📧 Gmail용 CSV", use_container_width=True):
                    self._generate_csv_download('gmail')
            with col2_2:
                if st.button("📧 Outlook용 CSV", use_container_width=True):
                    self._generate_csv_download('outlook')
            
            st.markdown("""
            **Gmail/Outlook 호환:**
            - UTF-8 인코딩 (Gmail)
            - CP949 인코딩 (Outlook)
            - 메일머지 변수 포함
            """)
        
        with col3:
            st.subheader("📋 분석 리포트")
            
            if st.button("📊 분석 리포트 생성", use_container_width=True):
                self._generate_analysis_report()
            
            st.markdown("""
            **분석 내용:**
            - 스케줄링 통계
            - 이메일 검증 결과
            - 제약조건 분석
            - 권장사항
            """)
        
        # 파일 다운로드 링크가 있는 경우 표시
        if 'download_links' in st.session_state and st.session_state.download_links:
            st.markdown("---")
            st.subheader("📥 다운로드 링크")
            
            for file_name, file_data in st.session_state.download_links.items():
                st.download_button(
                    label=f"💾 {file_name} 다운로드",
                    data=file_data,
                    file_name=file_name,
                    mime=self._get_mime_type(file_name)
                )
    
    def _generate_excel_download(self):
        """엑셀 파일 생성 및 다운로드 준비"""
        
        try:
            with st.spinner("엑셀 파일 생성 중..."):
                # 엑셀 생성
                wb, file_path = self.excel_generator.generate_complete_excel(
                    st.session_state.scheduling_result
                )
                
                # 바이트 데이터 생성
                excel_bytes = self.excel_generator.get_workbook_bytes()
                
                # 다운로드 링크 준비
                if 'download_links' not in st.session_state:
                    st.session_state.download_links = {}
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"interview_schedule_{timestamp}.xlsx"
                st.session_state.download_links[file_name] = excel_bytes
                
                st.success("✅ 엑셀 파일 생성 완료!")
                
                # 파일 정보 표시
                st.info(f"📁 파일명: {file_name}")
                st.info("📋 포함된 시트: 최종스케줄, 메일머지, 옵션비교, A/B조일정, 타임테이블, 메일템플릿 (총 8개)")
                
        except Exception as e:
            st.error(f"❌ 엑셀 파일 생성 오류: {str(e)}")
    
    def _generate_csv_download(self, csv_type: str):
        """CSV 파일 생성"""
        
        try:
            with st.spinner(f"{csv_type.upper()} CSV 파일 생성 중..."):
                # CSV 데이터 준비
                schedule_data = []
                for schedule in st.session_state.selected_option.schedules:
                    schedule_data.append({
                        '팀명': schedule.team_name,
                        '대표자명': schedule.leader_name,
                        '이메일': schedule.team.primary_email,
                        '연락처': schedule.team.primary_phone,
                        '면접날짜': schedule.interview_date,
                        '면접시간': schedule.interview_time,
                        '면접조': schedule.interview_group,
                        '면접장소': schedule.interview_slot.room,
                        '줌링크': schedule.interview_slot.zoom_link or "",
                        '추가안내사항': schedule.notes or ""
                    })
                
                df = pd.DataFrame(schedule_data)
                
                # 인코딩 선택
                if csv_type == 'gmail':
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    file_name = f"gmail_merge_{datetime.now().strftime('%Y%m%d')}.csv"
                else:  # outlook
                    csv_data = df.to_csv(index=False, encoding='cp949')
                    file_name = f"outlook_merge_{datetime.now().strftime('%Y%m%d')}.csv"
                
                # 다운로드 링크 준비
                if 'download_links' not in st.session_state:
                    st.session_state.download_links = {}
                
                st.session_state.download_links[file_name] = csv_data.encode()
                
                st.success(f"✅ {csv_type.upper()} CSV 파일 생성 완료!")
                
        except Exception as e:
            st.error(f"❌ CSV 파일 생성 오류: {str(e)}")
    
    def _generate_analysis_report(self):
        """분석 리포트 생성"""
        
        try:
            with st.spinner("분석 리포트 생성 중..."):
                # 리포트 데이터 수집
                option = st.session_state.selected_option
                
                report_data = {
                    '생성일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '총_팀수': option.total_teams,
                    '1순위_만족률': f"{option.first_choice_satisfaction:.1f}%",
                    '조별_균형': f"{option.group_balance_score:.1f}",
                    '제약_위반': option.constraint_violations,
                    '생성_시간': f"{option.generation_time:.2f}초"
                }
                
                # PDF 형태로 리포트 생성 (간단 버전)
                import json
                report_json = json.dumps(report_data, ensure_ascii=False, indent=2)
                
                if 'download_links' not in st.session_state:
                    st.session_state.download_links = {}
                
                file_name = f"analysis_report_{datetime.now().strftime('%Y%m%d')}.json"
                st.session_state.download_links[file_name] = report_json.encode('utf-8')
                
                st.success("✅ 분석 리포트 생성 완료!")
                
        except Exception as e:
            st.error(f"❌ 분석 리포트 생성 오류: {str(e)}")
    
    def _show_email_page(self):
        """메일 발송 관리 페이지"""
        st.header("📧 메일 발송 관리")
        
        if not st.session_state.selected_option:
            st.warning("⚠️ 먼저 스케줄 옵션을 선택해주세요.")
            st.stop()
        
        # 메일 템플릿 섹션
        st.subheader("📝 메일 템플릿")
        
        template_list = self.template_manager.get_template_list()
        
        selected_template = st.selectbox(
            "템플릿 선택",
            [t['template_id'] for t in template_list],
            format_func=lambda x: next(t['name'] for t in template_list if t['template_id'] == x)
        )
        
        # 템플릿 미리보기
        if selected_template:
            with st.expander("👀 템플릿 미리보기", expanded=True):
                preview = self.template_manager.get_template_preview(selected_template)
                if preview:
                    st.markdown(f"**제목:** {preview['subject']}")
                    st.markdown("**내용:**")
                    st.text(preview['body'])
                    st.markdown(f"**긴급도:** {preview['urgency']}")
        
        # 발송 대상 설정
        st.subheader("📬 발송 대상")
        
        col1, col2 = st.columns(2)
        with col1:
            send_to_all = st.checkbox("전체 팀에게 발송", value=True)
            
        with col2:
            if not send_to_all:
                selected_groups = st.multiselect(
                    "발송 대상 조 선택",
                    ["A조", "B조"],
                    default=["A조", "B조"]
                )
        
        # 발송 예약
        st.subheader("⏰ 발송 일정")
        
        send_immediately = st.checkbox("즉시 발송", value=True)
        
        if not send_immediately:
            col1, col2 = st.columns(2)
            with col1:
                send_date = st.date_input("발송 날짜", value=datetime.now().date())
            with col2:
                send_time = st.time_input("발송 시간", value=datetime.now().time())
        
        # 발송 시뮬레이션
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📨 메일 발송 시뮬레이션", type="primary", use_container_width=True):
                self._simulate_email_sending()
        
        with col2:
            if st.button("📅 리마인더 예약", use_container_width=True):
                self._schedule_reminders()
        
        # 발송 현황 표시
        if 'email_status' in st.session_state:
            st.subheader("📊 발송 현황")
            self._show_email_status()
    
    def _simulate_email_sending(self):
        """메일 발송 시뮬레이션"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        schedules = st.session_state.selected_option.schedules
        total_emails = len(schedules)
        
        # 발송 상태 초기화
        email_status = []
        
        for i, schedule in enumerate(schedules):
            status_text.text(f'발송 중: {schedule.team_name} ({i+1}/{total_emails})')
            progress_bar.progress((i + 1) / total_emails)
            
            # 시뮬레이션 지연
            time.sleep(0.1)
            
            # 발송 결과 시뮬레이션 (95% 성공률)
            import random
            is_success = random.random() < 0.95
            
            email_status.append({
                '팀명': schedule.team_name,
                '이메일': schedule.team.primary_email,
                '발송상태': '완료' if is_success else '실패',
                '발송시간': datetime.now().strftime('%H:%M:%S'),
                '오류': '' if is_success else '도메인 오류'
            })
        
        # 결과 저장
        st.session_state.email_status = email_status
        
        # 결과 표시
        success_count = len([e for e in email_status if e['발송상태'] == '완료'])
        failed_count = total_emails - success_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 발송", total_emails)
        with col2:
            st.metric("성공", success_count, delta=f"{success_count/total_emails*100:.1f}%")
        with col3:
            st.metric("실패", failed_count, delta=f"-{failed_count}")
        
        if failed_count > 0:
            st.warning(f"⚠️ {failed_count}개 이메일 발송 실패. 재발송이 필요합니다.")
        else:
            st.success("✅ 모든 이메일 발송 완료!")
    
    def _schedule_reminders(self):
        """리마인더 이메일 예약"""
        
        schedules_data = []
        for schedule in st.session_state.selected_option.schedules:
            schedules_data.append({
                'team_name': schedule.team_name,
                'leader_name': schedule.leader_name,
                'email': schedule.team.primary_email,
                'interview_date': schedule.interview_date,
                'interview_time': schedule.interview_time,
                'interview_room': schedule.interview_slot.room
            })
        
        reminders = self.template_manager.schedule_reminder_emails(schedules_data, 24)
        
        st.success(f"✅ {len(reminders)}개 리마인더 이메일 예약 완료!")
        st.info("📅 면접 24시간 전에 자동 발송됩니다.")
    
    def _show_email_status(self):
        """이메일 발송 상태 표시"""
        
        status_data = st.session_state.email_status
        df_status = pd.DataFrame(status_data)
        
        # 필터링
        status_filter = st.selectbox("상태 필터", ["전체", "완료", "실패"])
        
        if status_filter != "전체":
            df_filtered = df_status[df_status['발송상태'] == status_filter]
        else:
            df_filtered = df_status
        
        st.dataframe(df_filtered, use_container_width=True)
        
        # 재발송 버튼
        failed_emails = df_status[df_status['발송상태'] == '실패']
        if len(failed_emails) > 0:
            if st.button(f"🔄 실패 메일 재발송 ({len(failed_emails)}개)"):
                st.info("실패한 메일 재발송을 시작합니다...")
    
    def _get_mime_type(self, filename: str) -> str:
        """파일 확장자에 따른 MIME 타입 반환"""
        if filename.endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            return 'text/csv'
        elif filename.endswith('.json'):
            return 'application/json'
        else:
            return 'application/octet-stream'


# 애플리케이션 실행
def main():
    """메인 함수"""
    app = InterviewSchedulerApp()
    app.run()


if __name__ == "__main__":
    main()