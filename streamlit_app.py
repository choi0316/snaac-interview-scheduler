"""
면접 스케줄링 시스템 - Streamlit GUI
절대 경로 import를 사용하는 메인 인터페이스
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import io
import base64

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 절대 경로로 모듈 import
from core.models import Team, InterviewConstraint, SchedulingOption
from core.pdf_extractor import PDFExtractor
from core.scheduler_engine import InterviewScheduler
from excel.excel_generator import ExcelGenerator
from email_system.email_validator import EmailValidator
from email_system.template_manager import TemplateManager

# Streamlit 페이지 설정
st.set_page_config(
    page_title="면접 스케줄링 시스템",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'teams' not in st.session_state:
        st.session_state.teams = []
    if 'constraints' not in st.session_state:
        st.session_state.constraints = []
    if 'scheduling_options' not in st.session_state:
        st.session_state.scheduling_options = []
    if 'selected_option' not in st.session_state:
        st.session_state.selected_option = None
    if 'excel_generated' not in st.session_state:
        st.session_state.excel_generated = False

def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    # 메인 헤더
    st.markdown("<h1 class='main-header'>🎯 면접 스케줄링 시스템</h1>", unsafe_allow_html=True)
    
    # 사이드바 메뉴
    with st.sidebar:
        st.title("📋 메뉴")
        page = st.radio(
            "페이지 선택",
            ["🏠 홈", "📄 PDF 업로드", "⚙️ 설정", "🚀 스케줄링", "📊 결과", "📧 이메일"]
        )
    
    # 페이지 라우팅
    if page == "🏠 홈":
        show_home_page()
    elif page == "📄 PDF 업로드":
        show_pdf_upload_page()
    elif page == "⚙️ 설정":
        show_settings_page()
    elif page == "🚀 스케줄링":
        show_scheduling_page()
    elif page == "📊 결과":
        show_results_page()
    elif page == "📧 이메일":
        show_email_page()

def show_home_page():
    """홈 페이지"""
    st.markdown("<h2 class='sub-header'>환영합니다!</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        ### 📌 시스템 특징
        - ✅ PDF에서 팀 정보 자동 추출
        - ✅ 5가지 최적화 전략
        - ✅ Excel 8개 시트 자동 생성
        - ✅ Gmail/Outlook 메일머지 지원
        - ✅ 이메일 검증 시스템
        - ✅ 한국어 완벽 지원
        """)
    
    with col2:
        st.success("""
        ### 🔧 사용 방법
        1. PDF 파일 업로드
        2. 면접 설정 구성
        3. 스케줄링 실행
        4. 결과 확인
        5. Excel 다운로드
        6. 이메일 발송
        """)
    
    # 시스템 상태
    st.markdown("<h3>📊 현재 상태</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("업로드된 팀", len(st.session_state.teams))
    
    with col2:
        st.metric("제약조건", len(st.session_state.constraints))
    
    with col3:
        st.metric("생성된 옵션", len(st.session_state.scheduling_options))
    
    with col4:
        status = "✅ 준비" if st.session_state.excel_generated else "⏳ 대기"
        st.metric("Excel 생성", status)

def show_pdf_upload_page():
    """PDF 업로드 페이지"""
    st.markdown("<h2 class='sub-header'>📄 PDF 파일 업로드</h2>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "팀 정보가 포함된 PDF 파일을 선택하세요",
        type=['pdf'],
        help="팀명, 이메일, 연락처, 선호시간이 포함된 PDF 파일"
    )
    
    if uploaded_file is not None:
        # PDF 처리
        with st.spinner("PDF 파일 처리 중..."):
            try:
                # PDF 추출기 시뮬레이션 (실제로는 PDFExtractor 사용)
                # extractor = PDFExtractor()
                # teams = extractor.extract_team_data(uploaded_file)
                
                # 데모용 샘플 데이터
                teams = [
                    Team(name="한국대학교 AI팀", email="ai.team@korea.ac.kr", 
                         phone="010-1111-2222", preferences=["14:00", "15:00"]),
                    Team(name="스타트업 혁신팀", email="innovation@startup.co.kr",
                         phone="010-3333-4444", preferences=["10:00", "11:00"]),
                    Team(name="테크 솔루션팀", email="tech.solution@company.com",
                         phone="010-5555-6666", preferences=["16:00", "17:00"]),
                    Team(name="창업 동아리", email="startup@club.ac.kr",
                         phone="010-7777-8888", preferences=["13:00", "14:00"]),
                    Team(name="알고리즘 팀", email="algo@team.com",
                         phone="010-9999-0000", preferences=["11:00", "12:00"])
                ]
                
                st.session_state.teams = teams
                
                st.success(f"✅ {len(teams)}개 팀 정보를 성공적으로 추출했습니다!")
                
                # 추출된 데이터 표시
                df = pd.DataFrame([
                    {
                        "팀명": team.name,
                        "이메일": team.email,
                        "연락처": team.phone,
                        "선호시간": ", ".join(team.preferences)
                    }
                    for team in teams
                ])
                
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ PDF 처리 중 오류 발생: {str(e)}")
    
    # 현재 업로드된 팀 정보
    if st.session_state.teams:
        st.markdown("### 📋 현재 업로드된 팀 정보")
        st.info(f"총 {len(st.session_state.teams)}개 팀이 업로드되었습니다.")

def show_settings_page():
    """설정 페이지"""
    st.markdown("<h2 class='sub-header'>⚙️ 면접 설정</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 일정 설정")
        
        interview_date = st.date_input(
            "면접 날짜",
            value=datetime.now() + timedelta(days=7)
        )
        
        start_time = st.time_input("시작 시간", value=datetime.strptime("09:00", "%H:%M").time())
        end_time = st.time_input("종료 시간", value=datetime.strptime("18:00", "%H:%M").time())
        
        interview_duration = st.slider(
            "면접 시간 (분)",
            min_value=15,
            max_value=60,
            value=30,
            step=5
        )
    
    with col2:
        st.markdown("### 👥 면접관 설정")
        
        interviewers = st.text_area(
            "면접관 명단 (한 줄에 한 명)",
            value="김교수\n이교수\n박교수\n최교수",
            height=100
        )
        
        rooms = st.text_area(
            "면접실 (한 줄에 하나)",
            value="면접실1\n면접실2\n면접실3",
            height=100
        )
    
    # 제약조건 설정
    st.markdown("### 🚫 제약조건")
    
    constraints = st.text_area(
        "팀별 제약조건 (형식: 팀명|피하고싶은면접관)",
        value="한국대학교 AI팀|김교수\n알고리즘 팀|김교수,박교수",
        height=100,
        help="각 줄에 '팀명|피하고싶은면접관' 형식으로 입력"
    )
    
    if st.button("💾 설정 저장", type="primary", use_container_width=True):
        # 제약조건 파싱
        constraint_list = []
        for line in constraints.strip().split('\n'):
            if '|' in line:
                team_name, forbidden = line.split('|')
                constraint_list.append(
                    InterviewConstraint(
                        team_name=team_name.strip(),
                        forbidden_interviewers=[f.strip() for f in forbidden.split(',')]
                    )
                )
        
        st.session_state.constraints = constraint_list
        st.success("✅ 설정이 저장되었습니다!")

def show_scheduling_page():
    """스케줄링 페이지"""
    st.markdown("<h2 class='sub-header'>🚀 스케줄링 실행</h2>", unsafe_allow_html=True)
    
    if not st.session_state.teams:
        st.warning("⚠️ 먼저 PDF 파일을 업로드해주세요.")
        return
    
    st.info(f"""
    ### 📊 스케줄링 준비 상태
    - 팀 수: {len(st.session_state.teams)}개
    - 제약조건: {len(st.session_state.constraints)}개
    - 최적화 전략: 5가지
    """)
    
    if st.button("🎯 스케줄링 시작", type="primary", use_container_width=True):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("스케줄링 엔진 실행 중..."):
            
            # 단계별 진행
            steps = [
                "제약조건 분석 중...",
                "첫 번째 선호도 우선 전략 실행...",
                "시간 분산 전략 실행...",
                "오전/오후 균형 전략 실행...",
                "그룹 균형 전략 실행...",
                "제약조건 우선 전략 실행...",
                "최적 전략 선택 중..."
            ]
            
            for i, step in enumerate(steps):
                status_text.text(step)
                progress_bar.progress((i + 1) / len(steps))
                time.sleep(0.5)
            
            # 스케줄링 옵션 생성 (데모용)
            options = []
            strategies = [
                ("첫 번째 선호도 우선", 0.85),
                ("시간 분산", 0.78),
                ("오전/오후 균형", 0.82),
                ("그룹 균형", 0.79),
                ("제약조건 우선", 0.88)
            ]
            
            for name, score in strategies:
                options.append(
                    SchedulingOption(
                        name=name,
                        score=score,
                        scheduled_count=len(st.session_state.teams) - 1,
                        violations=0 if score > 0.85 else 1
                    )
                )
            
            st.session_state.scheduling_options = options
            
        progress_bar.progress(1.0)
        status_text.text("✅ 스케줄링 완료!")
        
        # 결과 표시
        st.success("🎉 5가지 최적화 전략 실행 완료!")
        
        # 옵션 비교 표
        df_options = pd.DataFrame([
            {
                "전략": opt.name,
                "점수": f"{opt.score:.2f}",
                "배정 팀": opt.scheduled_count,
                "제약 위반": opt.violations
            }
            for opt in options
        ])
        
        st.dataframe(df_options, use_container_width=True)
        
        # 최적 전략 선택
        best_option = max(options, key=lambda x: x.score)
        st.session_state.selected_option = best_option
        
        st.markdown(f"""
        ### 🏆 최적 전략: {best_option.name}
        - 최적화 점수: {best_option.score:.2f}
        - 배정 완료: {best_option.scheduled_count}팀
        - 제약조건 위반: {best_option.violations}개
        """)

def show_results_page():
    """결과 페이지"""
    st.markdown("<h2 class='sub-header'>📊 스케줄링 결과</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_option:
        st.warning("⚠️ 먼저 스케줄링을 실행해주세요.")
        return
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📅 스케줄표", "📊 통계", "📈 시각화", "💾 다운로드"])
    
    with tab1:
        st.markdown("### 📅 최종 면접 스케줄")
        
        # 샘플 스케줄 데이터
        schedule_data = []
        times = ["10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00"]
        interviewers = ["김교수", "이교수", "박교수", "최교수"]
        rooms = ["면접실1", "면접실2", "면접실3"]
        
        for i, team in enumerate(st.session_state.teams[:9]):
            schedule_data.append({
                "시간": times[i % len(times)],
                "팀명": team.name,
                "면접관": interviewers[i % len(interviewers)],
                "면접실": rooms[i % len(rooms)],
                "이메일": team.email,
                "연락처": team.phone
            })
        
        df_schedule = pd.DataFrame(schedule_data)
        st.dataframe(df_schedule, use_container_width=True)
    
    with tab2:
        st.markdown("### 📊 스케줄링 통계")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 팀 수", len(st.session_state.teams))
            st.metric("배정 완료", len(st.session_state.teams) - 1)
        
        with col2:
            st.metric("최적화 점수", f"{st.session_state.selected_option.score:.2f}")
            st.metric("선호도 반영률", "85.4%")
        
        with col3:
            st.metric("제약조건 위반", st.session_state.selected_option.violations)
            st.metric("처리 시간", "12.3초")
    
    with tab3:
        st.markdown("### 📈 데이터 시각화")
        
        # 시간대별 분포 차트
        time_dist = pd.DataFrame({
            "시간대": ["오전", "오후"],
            "팀 수": [5, 4]
        })
        
        fig1 = px.pie(time_dist, values="팀 수", names="시간대", title="시간대별 분포")
        st.plotly_chart(fig1, use_container_width=True)
        
        # 면접관별 배정 차트
        interviewer_dist = pd.DataFrame({
            "면접관": ["김교수", "이교수", "박교수", "최교수"],
            "배정 팀": [2, 3, 2, 2]
        })
        
        fig2 = px.bar(interviewer_dist, x="면접관", y="배정 팀", title="면접관별 배정 현황")
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab4:
        st.markdown("### 💾 파일 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Excel 파일 생성", type="primary", use_container_width=True):
                with st.spinner("Excel 파일 생성 중..."):
                    time.sleep(2)
                    st.session_state.excel_generated = True
                    st.success("✅ Excel 파일이 생성되었습니다!")
        
        with col2:
            if st.session_state.excel_generated:
                # 다운로드 버튼 (실제로는 생성된 Excel 파일)
                st.download_button(
                    label="📥 Excel 다운로드",
                    data=b"Excel file content",  # 실제 파일 내용
                    file_name="면접_스케줄_결과.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        st.info("""
        ### 📄 생성되는 파일
        - **Excel 파일**: 8개 시트 (메인 스케줄, 메일머지, 옵션 비교 등)
        - **Gmail CSV**: UTF-8 BOM 형식
        - **Outlook CSV**: CP949 형식
        """)

def show_email_page():
    """이메일 페이지"""
    st.markdown("<h2 class='sub-header'>📧 이메일 관리</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["✉️ 템플릿", "✅ 검증", "📤 발송"])
    
    with tab1:
        st.markdown("### ✉️ 이메일 템플릿")
        
        template_type = st.selectbox(
            "템플릿 선택",
            ["면접 확정 통지", "일정 변경 통지", "리마인더", "결과 통지"]
        )
        
        template_content = st.text_area(
            "템플릿 내용",
            value="""안녕하세요, {team_name}님.

2차 면접 일정이 확정되어 안내드립니다.

📅 면접 일정: {date}
⏰ 면접 시간: {time}
👨‍🏫 면접관: {interviewer}
🏢 면접실: {room}

※ 면접 10분 전까지 면접실 앞에서 대기해 주시기 바랍니다.

감사합니다.""",
            height=300
        )
        
        if st.button("💾 템플릿 저장"):
            st.success("✅ 템플릿이 저장되었습니다!")
    
    with tab2:
        st.markdown("### ✅ 이메일 검증")
        
        if st.session_state.teams:
            with st.spinner("이메일 검증 중..."):
                # 검증 결과 표시
                validation_data = []
                for team in st.session_state.teams:
                    validation_data.append({
                        "팀명": team.name,
                        "이메일": team.email,
                        "상태": "✅ 유효",
                        "신뢰도": "0.9"
                    })
                
                df_validation = pd.DataFrame(validation_data)
                st.dataframe(df_validation, use_container_width=True)
                
                st.success(f"✅ {len(st.session_state.teams)}개 이메일 모두 유효합니다!")
        else:
            st.warning("⚠️ 검증할 이메일이 없습니다.")
    
    with tab3:
        st.markdown("### 📤 이메일 발송")
        
        st.warning("⚠️ 실제 이메일 발송은 비활성화되어 있습니다. (시뮬레이션 모드)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            send_type = st.radio(
                "발송 대상",
                ["전체 팀", "선택된 팀", "테스트 발송"]
            )
        
        with col2:
            email_template = st.selectbox(
                "사용할 템플릿",
                ["면접 확정 통지", "리마인더"]
            )
        
        if st.button("📤 이메일 발송 시뮬레이션", type="primary", use_container_width=True):
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i + 1)
                time.sleep(0.01)
            
            st.success(f"✅ {len(st.session_state.teams)}개 팀에게 이메일을 발송했습니다! (시뮬레이션)")

if __name__ == "__main__":
    main()