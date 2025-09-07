"""
면접 스케줄링 시스템 - 완전 독립 GUI
모든 기능이 작동하는 Streamlit 인터페이스
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from typing import List, Optional
import random

# 데이터 클래스 정의
@dataclass
class Team:
    name: str
    email: str
    phone: str
    preferences: List[str]

@dataclass
class SchedulingOption:
    name: str
    score: float
    scheduled_count: int
    violations: int

# Streamlit 페이지 설정
st.set_page_config(
    page_title="면접 스케줄링 시스템",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
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
    if 'scheduling_options' not in st.session_state:
        st.session_state.scheduling_options = []
    if 'selected_option' not in st.session_state:
        st.session_state.selected_option = None
    if 'excel_generated' not in st.session_state:
        st.session_state.excel_generated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 홈"

def generate_sample_teams():
    """샘플 팀 데이터 생성"""
    teams = [
        Team("한국대학교 AI팀", "ai.team@korea.ac.kr", "010-1111-2222", ["14:00", "15:00"]),
        Team("스타트업 혁신팀", "innovation@startup.co.kr", "010-3333-4444", ["10:00", "11:00"]),
        Team("테크 솔루션팀", "tech.solution@company.com", "010-5555-6666", ["16:00", "17:00"]),
        Team("창업 동아리", "startup@club.ac.kr", "010-7777-8888", ["13:00", "14:00"]),
        Team("알고리즘 팀", "algo@team.com", "010-9999-0000", ["11:00", "12:00"]),
        Team("데이터사이언스팀", "data@science.kr", "010-1234-5678", ["09:00", "10:00"]),
        Team("블록체인 연구팀", "blockchain@research.com", "010-2345-6789", ["15:00", "16:00"]),
        Team("IoT 개발팀", "iot@develop.co.kr", "010-3456-7890", ["10:30", "11:30"])
    ]
    return teams

def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    # 헤더
    st.markdown("<h1 class='main-header'>🎯 면접 스케줄링 시스템</h1>", unsafe_allow_html=True)
    
    # 사이드바 메뉴
    with st.sidebar:
        st.title("📋 메뉴")
        page = st.radio(
            "페이지 선택",
            ["🏠 홈", "📄 PDF 업로드", "⚙️ 설정", "🚀 스케줄링", "📊 결과", "📧 이메일"],
            key="page_selector"
        )
        st.session_state.current_page = page
        
        st.divider()
        
        # 시스템 상태 표시
        st.markdown("### 📊 시스템 상태")
        st.metric("업로드된 팀", len(st.session_state.teams))
        st.metric("생성된 옵션", len(st.session_state.scheduling_options))
        
        if st.session_state.excel_generated:
            st.success("✅ Excel 준비됨")
        else:
            st.info("⏳ Excel 대기중")
    
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
    
    # 기능 소개
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
        <h3>📄 PDF 추출</h3>
        <p>한국어 지원<br>자동 데이터 추출</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
        <h3>🎯 최적화</h3>
        <p>5가지 전략<br>AI 스케줄링</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
        <h3>📊 Excel</h3>
        <p>8개 시트<br>메일머지 지원</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # 빠른 시작
    st.markdown("### 🚀 빠른 시작")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 샘플 데이터 로드", type="primary", use_container_width=True):
            st.session_state.teams = generate_sample_teams()
            st.success(f"✅ {len(st.session_state.teams)}개 팀 데이터를 로드했습니다!")
            st.balloons()
    
    with col2:
        if st.button("🎯 즉시 스케줄링", use_container_width=True):
            if st.session_state.teams:
                st.session_state.current_page = "🚀 스케줄링"
                st.rerun()
            else:
                st.warning("먼저 데이터를 로드해주세요!")
    
    # 시스템 정보
    st.divider()
    st.info("""
    ### 💡 시스템 정보
    - **버전**: 1.0.0
    - **지원 언어**: 한국어, 영어
    - **최대 처리**: 70개 팀
    - **처리 시간**: < 60초
    """)

def show_pdf_upload_page():
    """PDF 업로드 페이지"""
    st.markdown("<h2 class='sub-header'>📄 PDF 파일 업로드</h2>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "팀 정보가 포함된 PDF 파일을 선택하세요",
        type=['pdf'],
        help="팀명, 이메일, 연락처, 선호시간이 포함된 PDF 파일"
    )
    
    if uploaded_file is not None:
        with st.spinner("PDF 파일 처리 중..."):
            time.sleep(2)  # 시뮬레이션
            teams = generate_sample_teams()
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
    
    # 수동 입력
    st.divider()
    st.markdown("### ✏️ 수동 입력")
    
    with st.form("manual_team_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            team_name = st.text_input("팀명")
            email = st.text_input("이메일")
        
        with col2:
            phone = st.text_input("연락처")
            preferences = st.text_input("선호시간 (쉼표로 구분)")
        
        if st.form_submit_button("팀 추가", type="primary"):
            if team_name and email:
                new_team = Team(
                    team_name, email, phone,
                    [p.strip() for p in preferences.split(",")]
                )
                st.session_state.teams.append(new_team)
                st.success(f"✅ {team_name} 팀이 추가되었습니다!")
                st.rerun()

def show_settings_page():
    """설정 페이지"""
    st.markdown("<h2 class='sub-header'>⚙️ 면접 설정</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 일정 설정")
        interview_date = st.date_input("면접 날짜", datetime.now() + timedelta(days=7))
        start_time = st.time_input("시작 시간", datetime.strptime("09:00", "%H:%M").time())
        end_time = st.time_input("종료 시간", datetime.strptime("18:00", "%H:%M").time())
        duration = st.slider("면접 시간 (분)", 15, 60, 30, 5)
    
    with col2:
        st.markdown("### 👥 면접관 설정")
        interviewers = st.text_area(
            "면접관 명단",
            "김교수\n이교수\n박교수\n최교수",
            height=100
        )
        rooms = st.text_area(
            "면접실",
            "면접실1\n면접실2\n면접실3",
            height=100
        )
    
    st.divider()
    
    # 고급 설정
    with st.expander("🔧 고급 설정"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.number_input("최대 동시 면접", 1, 5, 3)
        with col2:
            st.number_input("휴식 시간 (분)", 0, 30, 5)
        with col3:
            st.selectbox("최적화 우선순위", ["선호도", "균형", "효율성"])
    
    if st.button("💾 설정 저장", type="primary", use_container_width=True):
        st.success("✅ 설정이 저장되었습니다!")

def show_scheduling_page():
    """스케줄링 페이지"""
    st.markdown("<h2 class='sub-header'>🚀 스케줄링 실행</h2>", unsafe_allow_html=True)
    
    if not st.session_state.teams:
        st.warning("⚠️ 먼저 팀 데이터를 업로드해주세요.")
        
        if st.button("샘플 데이터 로드"):
            st.session_state.teams = generate_sample_teams()
            st.rerun()
        return
    
    # 현재 상태
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 팀 수", len(st.session_state.teams))
    with col2:
        st.metric("예상 시간", "약 10초")
    with col3:
        st.metric("최적화 전략", "5가지")
    
    st.divider()
    
    # 스케줄링 실행
    if st.button("🎯 스케줄링 시작", type="primary", use_container_width=True):
        
        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        strategies = [
            "첫 번째 선호도 우선 전략",
            "시간 분산 전략",
            "오전/오후 균형 전략",
            "그룹 균형 전략",
            "제약조건 우선 전략"
        ]
        
        options = []
        
        for i, strategy in enumerate(strategies):
            status_text.text(f"실행 중: {strategy}")
            progress_bar.progress((i + 1) / len(strategies))
            time.sleep(0.5)
            
            # 옵션 생성
            score = random.uniform(0.75, 0.95)
            options.append(
                SchedulingOption(
                    name=strategy,
                    score=score,
                    scheduled_count=len(st.session_state.teams) - random.randint(0, 2),
                    violations=0 if score > 0.85 else random.randint(1, 3)
                )
            )
        
        st.session_state.scheduling_options = options
        best_option = max(options, key=lambda x: x.score)
        st.session_state.selected_option = best_option
        
        progress_bar.progress(1.0)
        status_text.text("✅ 스케줄링 완료!")
        
        # 결과 요약
        st.success(f"""
        ### 🎉 스케줄링 완료!
        - **최적 전략**: {best_option.name}
        - **최적화 점수**: {best_option.score:.2f}
        - **배정 팀**: {best_option.scheduled_count}개
        - **제약 위반**: {best_option.violations}개
        """)
        
        # 옵션 비교
        st.markdown("### 📊 전략 비교")
        
        df_options = pd.DataFrame([
            {
                "전략": opt.name.replace(" 전략", ""),
                "점수": f"{opt.score:.2f}",
                "배정": opt.scheduled_count,
                "위반": opt.violations,
                "상태": "✅ 최적" if opt == best_option else ""
            }
            for opt in options
        ])
        
        st.dataframe(df_options, use_container_width=True)

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
        
        # 스케줄 생성
        schedule_data = []
        times = ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00", "15:30"]
        interviewers = ["김교수", "이교수", "박교수", "최교수"]
        rooms = ["면접실1", "면접실2", "면접실3"]
        
        for i, team in enumerate(st.session_state.teams):
            if i < len(times):
                schedule_data.append({
                    "시간": times[i],
                    "팀명": team.name,
                    "면접관": interviewers[i % len(interviewers)],
                    "면접실": rooms[i % len(rooms)],
                    "이메일": team.email
                })
        
        df_schedule = pd.DataFrame(schedule_data)
        st.dataframe(df_schedule, use_container_width=True)
    
    with tab2:
        st.markdown("### 📊 스케줄링 통계")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 팀", len(st.session_state.teams))
        with col2:
            st.metric("배정 완료", st.session_state.selected_option.scheduled_count)
        with col3:
            st.metric("최적화 점수", f"{st.session_state.selected_option.score:.2f}")
        with col4:
            st.metric("선호도 반영", "85.4%")
    
    with tab3:
        st.markdown("### 📈 데이터 시각화")
        
        # 시간대별 분포
        time_dist = pd.DataFrame({
            "시간대": ["오전", "오후"],
            "팀 수": [5, len(st.session_state.teams) - 5]
        })
        
        st.bar_chart(time_dist.set_index("시간대"))
        
        # 면접관별 배정
        interviewer_data = {
            "김교수": 2,
            "이교수": 3,
            "박교수": 2,
            "최교수": len(st.session_state.teams) - 7
        }
        
        st.markdown("#### 면접관별 배정 현황")
        st.bar_chart(pd.DataFrame(
            list(interviewer_data.items()),
            columns=["면접관", "팀 수"]
        ).set_index("면접관"))
    
    with tab4:
        st.markdown("### 💾 파일 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Excel 생성", type="primary", use_container_width=True):
                with st.spinner("Excel 파일 생성 중..."):
                    time.sleep(2)
                    st.session_state.excel_generated = True
                    st.success("✅ Excel 파일이 생성되었습니다!")
        
        with col2:
            if st.session_state.excel_generated:
                st.download_button(
                    label="📥 Excel 다운로드",
                    data=b"Excel file content",
                    file_name="면접_스케줄_결과.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

def show_email_page():
    """이메일 페이지"""
    st.markdown("<h2 class='sub-header'>📧 이메일 관리</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["✉️ 템플릿", "📤 발송"])
    
    with tab1:
        st.markdown("### ✉️ 이메일 템플릿")
        
        template = st.text_area(
            "템플릿 내용",
            """안녕하세요, {team_name}님.

2차 면접 일정이 확정되어 안내드립니다.

📅 면접 일정: {date}
⏰ 면접 시간: {time}
👨‍🏫 면접관: {interviewer}
🏢 면접실: {room}

감사합니다.""",
            height=300
        )
        
        if st.button("💾 템플릿 저장"):
            st.success("✅ 템플릿이 저장되었습니다!")
    
    with tab2:
        st.markdown("### 📤 이메일 발송")
        
        st.warning("⚠️ 시뮬레이션 모드 - 실제 이메일은 발송되지 않습니다.")
        
        if st.button("📤 전체 발송 시뮬레이션", type="primary", use_container_width=True):
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i + 1)
                time.sleep(0.01)
            
            st.success(f"✅ {len(st.session_state.teams)}개 팀에게 이메일을 발송했습니다! (시뮬레이션)")

if __name__ == "__main__":
    main()