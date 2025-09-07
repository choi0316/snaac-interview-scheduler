"""
고급 면접 스케줄링 GUI
- A/B 두 조 동시 면접 지원
- 연속 배치 최적화
- 미배치 팀 상세 분석
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time
from io import BytesIO

# 모듈 임포트
from improved_pdf_processor import process_pdf_file
from advanced_scheduler import AdvancedInterviewScheduler

# Streamlit 설정
st.set_page_config(
    page_title="SNAAC 면접 스케줄링 시스템 Pro",
    page_icon="🗓️",
    layout="wide"
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
        font-size: 1.8rem;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #ecf0f1;
        border-radius: 5px;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
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
    .schedule-table {
        border: 2px solid #dee2e6;
        border-radius: 5px;
        overflow: hidden;
    }
    .group-a {
        background-color: #e3f2fd !important;
        color: #1565c0;
        font-weight: bold;
    }
    .group-b {
        background-color: #f3e5f5 !important;
        color: #7b1fa2;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 class='main-header'>🗓️ SNAAC 면접 스케줄링 시스템 Pro</h1>", unsafe_allow_html=True)
    st.markdown("### 💡 A/B조 동시 면접 | 연속 배치 최적화 | 충돌 분석")
    
    # 세션 상태 초기화
    if 'teams' not in st.session_state:
        st.session_state.teams = []
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = None
    if 'schedule_result' not in st.session_state:
        st.session_state.schedule_result = None
    
    # 탭 생성
    tabs = st.tabs([
        "📄 PDF 업로드", 
        "📊 추출된 데이터", 
        "📅 스케줄 보기",
        "🤖 자동 스케줄링",
        "⚠️ 미배치 팀 분석",
        "💾 데이터 내보내기"
    ])
    
    # Tab 1: PDF 업로드
    with tabs[0]:
        st.markdown("<h2 class='sub-header'>📄 PDF 파일 업로드</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "면접 신청서 PDF 파일을 선택하세요 (여러 개 가능)",
                type=['pdf'],
                accept_multiple_files=True,
                help="팀별 면접 신청서 PDF를 업로드하세요"
            )
        
        with col2:
            st.info("""
            📌 **자동 추출 정보**
            - 팀명 / 대표자명
            - 이메일 / 전화번호
            - 면접 가능 시간 (O 표시)
            
            **지원 날짜/시간**
            - 9/12 (금): 19:00~22:00
            - 9/13 (토): 10:00~22:00
            - 9/14 (일): 10:00~22:00
            """)
        
        if uploaded_files:
            if st.button("🔍 PDF 분석 시작", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                st.session_state.teams = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"📄 {uploaded_file.name} 분석 중...")
                    
                    # PDF를 임시 파일로 저장
                    with open(f"/tmp/{uploaded_file.name}", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # PDF 분석
                    result = process_pdf_file(f"/tmp/{uploaded_file.name}")
                    
                    # 결과를 세션에 저장
                    st.session_state.teams.append({
                        "파일명": uploaded_file.name,
                        "팀명": result["팀명"],
                        "대표자명": result["대표자명"],
                        "이메일": result["이메일"],
                        "전화번호": result["전화번호"],
                        "면접 가능 시간": result["면접 가능 시간"]
                    })
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty()
                st.success(f"✅ {len(uploaded_files)}개 파일 분석 완료!")
    
    # Tab 2: 추출된 데이터
    with tabs[1]:
        st.markdown("<h2 class='sub-header'>📊 추출된 팀 정보</h2>", unsafe_allow_html=True)
        
        if st.session_state.teams:
            # DataFrame 생성
            df_display = []
            for team in st.session_state.teams:
                df_display.append({
                    "파일명": team["파일명"],
                    "팀명": team["팀명"],
                    "대표자명": team["대표자명"],
                    "이메일": team["이메일"],
                    "전화번호": team["전화번호"],
                    "가능 시간 수": len(team["면접 가능 시간"]) if isinstance(team["면접 가능 시간"], list) else 0
                })
            
            df = pd.DataFrame(df_display)
            st.dataframe(df, use_container_width=True, height=400)
            
            # 통계
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 팀 수", len(df))
            with col2:
                valid_emails = df[df['이메일'] != '미확인']['이메일'].count()
                st.metric("유효 이메일", f"{valid_emails}/{len(df)}")
            with col3:
                valid_phones = df[df['전화번호'] != '미확인']['전화번호'].count()
                st.metric("유효 전화번호", f"{valid_phones}/{len(df)}")
            with col4:
                avg_slots = df['가능 시간 수'].mean()
                st.metric("평균 가능 시간", f"{avg_slots:.1f}개")
        else:
            st.info("📌 PDF를 업로드하고 분석을 실행하세요.")
    
    # Tab 3: 스케줄 보기
    with tabs[2]:
        st.markdown("<h2 class='sub-header'>📅 면접 스케줄 시간표</h2>", unsafe_allow_html=True)
        
        if st.session_state.schedule_result:
            schedule = st.session_state.schedule_result
            scheduler = st.session_state.scheduler
            
            # A/B조 선택
            view_option = st.radio(
                "보기 옵션",
                ["통합 시간표", "A조 시간표", "B조 시간표"],
                horizontal=True
            )
            
            if view_option == "통합 시간표":
                # 통합 시간표 생성
                df_combined = scheduler.export_combined_schedule()
                if not df_combined.empty:
                    st.dataframe(
                        df_combined.style.applymap(
                            lambda x: 'background-color: #e3f2fd' if 'A조' in str(x) else (
                                'background-color: #f3e5f5' if 'B조' in str(x) else ''
                            )
                        ),
                        use_container_width=True,
                        height=600
                    )
                else:
                    st.info("아직 스케줄이 생성되지 않았습니다.")
            
            elif view_option == "A조 시간표":
                df_a, _ = scheduler.export_schedule()
                if not df_a.empty:
                    st.markdown("### 🔵 A조 면접 스케줄")
                    st.dataframe(df_a, use_container_width=True, height=500)
                else:
                    st.info("A조 스케줄이 비어 있습니다.")
            
            else:  # B조 시간표
                _, df_b = scheduler.export_schedule()
                if not df_b.empty:
                    st.markdown("### 🟣 B조 면접 스케줄")
                    st.dataframe(df_b, use_container_width=True, height=500)
                else:
                    st.info("B조 스케줄이 비어 있습니다.")
        else:
            st.info("📌 자동 스케줄링을 실행하여 시간표를 생성하세요.")
    
    # Tab 4: 자동 스케줄링
    with tabs[3]:
        st.markdown("<h2 class='sub-header'>🤖 자동 스케줄링 실행</h2>", unsafe_allow_html=True)
        
        if st.session_state.teams:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### ⚙️ 스케줄링 옵션")
                
                algorithm = st.selectbox(
                    "알고리즘 선택",
                    ["연속 배치 최적화 (추천)", "기본 연속 배치", "랜덤 최적화"],
                    help="연속 배치: 중간 공백 최소화, 면접관 편의 극대화"
                )
                
                max_iterations = st.slider(
                    "최적화 반복 횟수",
                    min_value=10,
                    max_value=500,
                    value=100,
                    step=10,
                    help="반복 횟수가 많을수록 더 좋은 결과를 얻을 수 있습니다"
                )
            
            with col2:
                st.info("""
                **💡 A/B조 동시 면접**
                - 한 시간에 최대 2팀 면접
                - A조와 B조 별도 진행
                
                **🔄 연속 배치**
                - 중간 공백 최소화
                - 면접관 피로도 감소
                
                **⚠️ 충돌 분석**
                - 미배치 팀 원인 파악
                - 대안 시간 제안
                """)
            
            if st.button("🚀 스케줄링 시작", type="primary", use_container_width=True):
                with st.spinner("스케줄링 진행 중..."):
                    # 스케줄러 생성
                    scheduler = AdvancedInterviewScheduler()
                    
                    # 팀 추가
                    for team in st.session_state.teams:
                        if team["면접 가능 시간"] and isinstance(team["면접 가능 시간"], list):
                            scheduler.add_team(
                                name=team["팀명"],
                                available_slots=team["면접 가능 시간"],
                                email=team["이메일"],
                                phone=team["전화번호"]
                            )
                    
                    # 스케줄링 실행
                    if algorithm == "연속 배치 최적화 (추천)":
                        schedule = scheduler.optimize_schedule(max_iterations=max_iterations)
                    else:
                        schedule = scheduler.schedule_interviews_continuous()
                    
                    # 결과 저장
                    st.session_state.scheduler = scheduler
                    st.session_state.schedule_result = schedule
                    
                    # 통계 표시
                    stats = scheduler.get_schedule_statistics()
                    
                    st.success("✅ 스케줄링 완료!")
                    
                    # 결과 요약
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("배치율", stats["배치율"])
                        st.metric("A조 배치", stats["A조 배치"])
                    
                    with col2:
                        st.metric("미배치 팀", stats["미배치 팀"])
                        st.metric("B조 배치", stats["B조 배치"])
                    
                    with col3:
                        st.metric("전체 수용률", stats["전체 수용률"])
                        st.metric("공백 점수", stats["공백 점수"], 
                                help="낮을수록 연속성이 좋음")
                    
                    # 날짜별 통계
                    st.markdown("### 📊 날짜별 배치 현황")
                    date_cols = st.columns(3)
                    with date_cols[0]:
                        st.info(f"**9/12 (금)**: {stats['금요일 배치']}")
                    with date_cols[1]:
                        st.info(f"**9/13 (토)**: {stats['토요일 배치']}")
                    with date_cols[2]:
                        st.info(f"**9/14 (일)**: {stats['일요일 배치']}")
        else:
            st.warning("먼저 PDF 파일을 업로드하고 분석을 완료하세요.")
    
    # Tab 5: 미배치 팀 분석
    with tabs[4]:
        st.markdown("<h2 class='sub-header'>⚠️ 미배치 팀 상세 분석</h2>", unsafe_allow_html=True)
        
        if st.session_state.scheduler:
            scheduler = st.session_state.scheduler
            unassigned = scheduler.get_unassigned_teams_detail()
            
            if unassigned:
                st.warning(f"⚠️ {len(unassigned)}개 팀이 배치되지 못했습니다.")
                
                # 미배치 팀 상세 정보
                for i, team_info in enumerate(unassigned, 1):
                    with st.expander(f"📌 {team_info['팀명']}", expanded=(i <= 3)):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📧 연락처 정보**")
                            st.text(f"이메일: {team_info['이메일']}")
                            st.text(f"전화번호: {team_info['전화번호']}")
                        
                        with col2:
                            st.markdown("**⏰ 가능 시간**")
                            st.text(team_info['가능 시간'])
                        
                        st.markdown("**❌ 미배치 원인**")
                        st.error(team_info['미배치 이유'])
                        
                        st.markdown("**💡 해결 방안**")
                        if "모든 가능 시간대가 이미 배정됨" in team_info['미배치 이유']:
                            st.info("→ 다른 팀과 시간 조율이 필요합니다.")
                        elif "가능한 시간대가 없음" in team_info['미배치 이유']:
                            st.info("→ 팀에게 추가 가능 시간을 문의하세요.")
                        else:
                            st.info("→ 수동으로 배치를 조정해보세요.")
            else:
                st.success("✅ 모든 팀이 성공적으로 배치되었습니다!")
        else:
            st.info("📌 스케줄링을 실행하면 미배치 팀 분석을 확인할 수 있습니다.")
    
    # Tab 6: 데이터 내보내기
    with tabs[5]:
        st.markdown("<h2 class='sub-header'>💾 스케줄 데이터 내보내기</h2>", unsafe_allow_html=True)
        
        if st.session_state.scheduler and st.session_state.schedule_result:
            scheduler = st.session_state.scheduler
            
            # 엑셀 파일 생성
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # 통합 스케줄
                df_combined = scheduler.export_combined_schedule()
                df_combined.to_excel(writer, sheet_name='통합스케줄', index=False)
                
                # A조 스케줄
                df_a, df_b = scheduler.export_schedule()
                if not df_a.empty:
                    df_a.to_excel(writer, sheet_name='A조', index=False)
                if not df_b.empty:
                    df_b.to_excel(writer, sheet_name='B조', index=False)
                
                # 미배치 팀
                unassigned = scheduler.get_unassigned_teams_detail()
                if unassigned:
                    df_unassigned = pd.DataFrame(unassigned)
                    df_unassigned.to_excel(writer, sheet_name='미배치팀', index=False)
                
                # 통계
                stats = scheduler.get_schedule_statistics()
                df_stats = pd.DataFrame([stats])
                df_stats.to_excel(writer, sheet_name='통계', index=False)
            
            # 다운로드 버튼
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Excel 파일 다운로드",
                    data=buffer.getvalue(),
                    file_name=f"면접스케줄_AB조_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                # CSV 다운로드
                csv = df_combined.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 CSV 파일 다운로드",
                    data=csv,
                    file_name=f"면접스케줄_통합_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # 요약 정보
            st.markdown("### 📊 내보내기 요약")
            stats = scheduler.get_schedule_statistics()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**총 팀 수**: {stats['총 팀 수']}")
                st.info(f"**배치된 팀**: {stats['배치된 팀']}")
            
            with col2:
                st.info(f"**A조**: {stats['A조 배치']}팀")
                st.info(f"**B조**: {stats['B조 배치']}팀")
            
            with col3:
                st.info(f"**배치율**: {stats['배치율']}")
                st.info(f"**미배치**: {stats['미배치 팀']}팀")
        else:
            st.info("📌 스케줄링을 완료한 후 데이터를 내보낼 수 있습니다.")

if __name__ == "__main__":
    main()