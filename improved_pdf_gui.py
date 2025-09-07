"""
개선된 면접 스케줄링 시스템 - PDF 처리 GUI
정확한 팀 정보 추출 및 시간표 표시
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from improved_pdf_processor import ImprovedPDFProcessor, process_pdf_file
from schedule_optimizer import InterviewScheduler

# Streamlit 설정
st.set_page_config(
    page_title="면접 스케줄링 시스템 - 개선된 PDF 처리",
    page_icon="📄",
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
    .team-info-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .time-slot-available {
        background-color: #d4edda;
        color: #155724;
        padding: 0.3rem 0.5rem;
        border-radius: 3px;
        margin: 0.2rem;
        display: inline-block;
    }
    .time-slot-unavailable {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.3rem 0.5rem;
        border-radius: 3px;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 class='main-header'>📄 개선된 PDF 면접 스케줄링 시스템</h1>", unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'teams' not in st.session_state:
        st.session_state.teams = []
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    
    # 사이드바
    with st.sidebar:
        st.markdown("### 📊 처리 현황")
        st.metric("처리된 팀 수", len(st.session_state.teams))
        st.metric("처리된 파일 수", len(st.session_state.processed_files))
        
        if st.button("🗑️ 데이터 초기화", use_container_width=True):
            st.session_state.teams = []
            st.session_state.processed_files = set()
            st.rerun()
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 PDF 업로드", "📊 추출된 데이터", "📅 시간표 보기", "🎯 자동 스케줄링", "💾 데이터 저장"])
    
    with tab1:
        st.markdown("### PDF 파일 업로드 및 분석")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            📌 **자동 추출 항목**:
            - 팀명 (예: 필리데이, 아뮤즈8)
            - 대표자명 (예: 권준범, 신동민)
            - 이메일 주소
            - 전화번호
            - 면접 가능 시간 (9/12, 9/13, 9/14)
            """)
        
        with col2:
            st.success("""
            ✅ **지원 형식**:
            - NAACst STEP 지원서 형식
            - PDF 파일
            - 한글/영문 혼용 가능
            """)
        
        # 파일 업로더
        uploaded_files = st.file_uploader(
            "PDF 파일을 선택하세요 (여러 개 가능)",
            type=['pdf'],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            st.markdown(f"### 📁 업로드된 파일: {len(uploaded_files)}개")
            
            # 분석 버튼
            if st.button("🔍 PDF 분석 시작", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                processor = ImprovedPDFProcessor()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    # 이미 처리된 파일인지 확인
                    if uploaded_file.name in st.session_state.processed_files:
                        st.warning(f"⚠️ {uploaded_file.name}은 이미 처리되었습니다.")
                        continue
                    
                    st.markdown(f"#### 📄 분석 중: {uploaded_file.name}")
                    
                    # 임시 파일로 저장
                    temp_path = f"/tmp/{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # PDF 분석
                    try:
                        result = process_pdf_file(temp_path)
                        
                        # 결과를 카드 형식으로 표시
                        st.markdown("<div class='team-info-card'>", unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**📌 기본 정보**")
                            st.text(f"팀명: {result['팀명']}")
                            st.text(f"대표자: {result['대표자명']}")
                        
                        with col2:
                            st.markdown("**📧 연락처**")
                            st.text(f"이메일: {result['이메일']}")
                            st.text(f"전화: {result['전화번호']}")
                        
                        with col3:
                            st.markdown("**⏰ 면접 시간**")
                            if result['면접 가능 시간'] and result['면접 가능 시간'][0] != "미확인":
                                st.text(f"가능 슬롯: {len(result['면접 가능 시간'])}개")
                            else:
                                st.text("가능 슬롯: 미확인")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # 수동 수정 옵션
                        with st.expander("✏️ 정보 수정"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                team_name = st.text_input(
                                    f"팀명",
                                    value=result['팀명'],
                                    key=f"team_{i}"
                                )
                                rep_name = st.text_input(
                                    f"대표자명",
                                    value=result['대표자명'],
                                    key=f"rep_{i}"
                                )
                            
                            with col2:
                                email = st.text_input(
                                    f"이메일",
                                    value=result['이메일'],
                                    key=f"email_{i}"
                                )
                                phone = st.text_input(
                                    f"전화번호",
                                    value=result['전화번호'],
                                    key=f"phone_{i}"
                                )
                            
                            # 수정된 값 반영
                            result['팀명'] = team_name
                            result['대표자명'] = rep_name
                            result['이메일'] = email
                            result['전화번호'] = phone
                        
                        # 팀 정보 저장
                        team_data = {
                            "파일명": uploaded_file.name,
                            "팀명": result['팀명'],
                            "대표자명": result['대표자명'],
                            "이메일": result['이메일'],
                            "전화번호": result['전화번호'],
                            "면접 가능 시간": result['면접 가능 시간'],
                            "상세 시간표": result.get('상세 시간표', {})
                        }
                        
                        st.session_state.teams.append(team_data)
                        st.session_state.processed_files.add(uploaded_file.name)
                        
                        # 임시 파일 삭제
                        os.remove(temp_path)
                        
                    except Exception as e:
                        st.error(f"❌ 처리 오류: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ {len(uploaded_files)}개 파일 분석 완료!")
    
    with tab2:
        st.markdown("### 📊 추출된 팀 정보")
        
        if st.session_state.teams:
            # 데이터프레임 생성
            df_data = []
            for team in st.session_state.teams:
                df_data.append({
                    "파일명": team["파일명"],
                    "팀명": team["팀명"],
                    "대표자명": team["대표자명"],
                    "이메일": team["이메일"],
                    "전화번호": team["전화번호"],
                    "가능 시간 수": len(team["면접 가능 시간"]) if isinstance(team["면접 가능 시간"], list) else 0
                })
            
            df = pd.DataFrame(df_data)
            
            # 데이터프레임 표시
            st.dataframe(df, use_container_width=True, height=400)
            
            # 통계 표시
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
            st.info("아직 분석된 데이터가 없습니다. PDF를 업로드해주세요.")
    
    with tab3:
        st.markdown("### 📅 면접 가능 시간표")
        
        if st.session_state.teams:
            # 날짜별로 탭 생성
            date_tabs = st.tabs(["9/12 (금)", "9/13 (토)", "9/14 (일)"])
            
            dates = ["9/12", "9/13", "9/14"]
            
            # 날짜별 시간대 정의 (실제 PDF 구조에 맞게)
            date_time_slots = {
                "9/12": [  # 금요일: 19:00~22:00 (4개 슬롯)
                    "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
                ],
                "9/13": [  # 토요일: 10:00~22:00 (16개 슬롯)
                    "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
                    "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
                    "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
                    "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
                ],
                "9/14": [  # 일요일: 10:00~22:00 (16개 슬롯)
                    "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
                    "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
                    "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
                    "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
                ]
            }
            
            for date_idx, date_tab in enumerate(date_tabs):
                with date_tab:
                    date = dates[date_idx]
                    st.markdown(f"#### {date} 면접 가능 팀")
                    
                    # 해당 날짜의 시간대만 표시
                    time_slots = date_time_slots[date]
                    
                    # 시간대별로 가능한 팀 표시
                    for time_slot in time_slots:
                        available_teams = []
                        
                        for team in st.session_state.teams:
                            if '상세 시간표' in team and date in team['상세 시간표']:
                                for slot, is_available in team['상세 시간표'][date]:
                                    if slot == time_slot and is_available:
                                        available_teams.append(team['팀명'])
                                        break
                        
                        if available_teams:
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.markdown(f"**{time_slot}**")
                            with col2:
                                teams_str = ", ".join(available_teams)
                                st.markdown(f"<span class='time-slot-available'>가능 팀: {teams_str}</span>", unsafe_allow_html=True)
                        else:
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.markdown(f"**{time_slot}**")
                            with col2:
                                st.markdown("<span class='time-slot-unavailable'>가능한 팀 없음</span>", unsafe_allow_html=True)
        else:
            st.info("아직 분석된 데이터가 없습니다.")
    
    with tab4:
        st.markdown("### 🎯 자동 면접 스케줄링")
        
        if st.session_state.teams:
            st.info("""
            📌 **스케줄링 규칙**:
            - 한 시간대에는 한 팀만 배치됩니다
            - 팀의 가능한 시간 중에서 최적 시간을 선택합니다
            - 모든 팀이 면접을 볼 수 있도록 최적화합니다
            """)
            
            # 알고리즘 선택
            col1, col2 = st.columns([2, 1])
            
            with col1:
                algorithm = st.selectbox(
                    "스케줄링 알고리즘 선택",
                    ["백트래킹 (모든 팀 배치 우선)", "탐욕 알고리즘 (빠른 처리)", "최적화 (여러 시도)"],
                    help="백트래킹: 모든 팀 배치를 보장하려 시도\n탐욕: 빠르게 처리\n최적화: 여러 방법을 시도해 최선의 결과 찾기"
                )
            
            with col2:
                if algorithm == "최적화 (여러 시도)":
                    max_iterations = st.number_input("최대 시도 횟수", min_value=10, max_value=1000, value=100)
                else:
                    max_iterations = 100
            
            # 스케줄링 실행 버튼
            if st.button("🚀 스케줄링 실행", type="primary", use_container_width=True):
                with st.spinner("스케줄링 중..."):
                    # 스케줄러 생성
                    scheduler = InterviewScheduler()
                    
                    # 팀 데이터 추가
                    for team in st.session_state.teams:
                        available_times = []
                        if '상세 시간표' in team:
                            for date, slots in team['상세 시간표'].items():
                                for time_slot, is_available in slots:
                                    if is_available:
                                        available_times.append(f"{date} {time_slot}")
                        
                        if available_times:
                            scheduler.add_team(
                                name=team['팀명'],
                                available_slots=available_times,
                                email=team.get('이메일', ''),
                                phone=team.get('전화번호', '')
                            )
                    
                    # 스케줄링 실행
                    if algorithm == "백트래킹 (모든 팀 배치 우선)":
                        schedule = scheduler._backtrack_scheduling()
                    elif algorithm == "탐욕 알고리즘 (빠른 처리)":
                        schedule = scheduler._greedy_scheduling()
                    else:  # 최적화
                        schedule = scheduler.find_optimal_schedule(max_iterations)
                    
                    # 결과 저장
                    st.session_state.schedule = schedule
                    st.session_state.scheduler = scheduler
                
                # 결과 표시
                st.success("✅ 스케줄링 완료!")
                
                # 통계 표시
                stats = scheduler.get_schedule_statistics()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("총 팀 수", stats["총 팀 수"])
                
                with col2:
                    st.metric("배치된 팀", stats["배치된 팀"])
                
                with col3:
                    st.metric("배치율", stats["배치율"])
                
                with col4:
                    st.metric("슬롯 사용률", stats["슬롯 사용률"])
                
                # 미배치 팀 표시
                unassigned = scheduler.get_unassigned_teams()
                if unassigned:
                    st.warning(f"⚠️ 미배치 팀: {', '.join(unassigned)}")
                
                # 날짜별 배치 현황
                st.markdown("#### 📅 날짜별 배치 현황")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("9/12 (금)", f"{stats['금요일 배치']}팀")
                
                with col2:
                    st.metric("9/13 (토)", f"{stats['토요일 배치']}팀")
                
                with col3:
                    st.metric("9/14 (일)", f"{stats['일요일 배치']}팀")
            
            # 스케줄 결과 표시
            if hasattr(st.session_state, 'schedule') and st.session_state.schedule:
                st.markdown("#### 📋 최종 스케줄")
                
                # DataFrame 생성
                schedule_df = st.session_state.scheduler.export_schedule()
                
                # 스케줄 테이블 표시
                st.dataframe(schedule_df, use_container_width=True, height=400)
                
                # 날짜별 상세 보기
                st.markdown("#### 📅 날짜별 상세 스케줄")
                
                date_tabs = st.tabs(["9/12 (금)", "9/13 (토)", "9/14 (일)"])
                
                for idx, (date, tab) in enumerate(zip(["9/12", "9/13", "9/14"], date_tabs)):
                    with tab:
                        date_schedule = schedule_df[schedule_df['날짜'] == date]
                        if not date_schedule.empty:
                            for _, row in date_schedule.iterrows():
                                col1, col2, col3 = st.columns([2, 3, 3])
                                with col1:
                                    st.markdown(f"**{row['시간']}**")
                                with col2:
                                    st.markdown(f"📌 {row['팀명']}")
                                with col3:
                                    if row['이메일']:
                                        st.markdown(f"📧 {row['이메일']}")
                        else:
                            st.info("이 날짜에는 배치된 팀이 없습니다.")
        else:
            st.info("먼저 PDF를 업로드하고 팀 정보를 추출해주세요.")
    
    with tab5:
        st.markdown("### 💾 데이터 저장")
        
        if st.session_state.teams:
            # Excel 파일 생성
            df_export = []
            for team in st.session_state.teams:
                # 기본 정보
                row = {
                    "파일명": team["파일명"],
                    "팀명": team["팀명"],
                    "대표자명": team["대표자명"],
                    "이메일": team["이메일"],
                    "전화번호": team["전화번호"]
                }
                
                # 면접 가능 시간을 문자열로 변환
                if isinstance(team["면접 가능 시간"], list) and team["면접 가능 시간"][0] != "미확인":
                    row["면접 가능 시간"] = ", ".join(team["면접 가능 시간"][:5])  # 처음 5개만
                else:
                    row["면접 가능 시간"] = "미확인"
                
                df_export.append(row)
            
            df = pd.DataFrame(df_export)
            
            # Excel 다운로드
            from io import BytesIO
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='팀정보', index=False)
                
                # 열 너비 조정
                worksheet = writer.sheets['팀정보']
                for column in df:
                    column_width = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
            
            st.download_button(
                label="📥 Excel 파일 다운로드",
                data=buffer.getvalue(),
                file_name=f"면접팀정보_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # CSV 다운로드
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 파일 다운로드 (한글 지원)",
                data=csv,
                file_name=f"면접팀정보_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # 미리보기
            st.markdown("### 📋 데이터 미리보기")
            st.dataframe(df, use_container_width=True)
            
        else:
            st.info("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    main()