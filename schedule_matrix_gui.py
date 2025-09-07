"""
면접 스케줄 매트릭스 GUI
시간대별 가능 팀 한눈에 보기
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from io import BytesIO

# 모듈 임포트
from improved_pdf_processor import process_pdf_file
from advanced_scheduler import AdvancedInterviewScheduler

# Streamlit 설정
st.set_page_config(
    page_title="SNAAC 면접 스케줄 매트릭스",
    page_icon="📊",
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
    .matrix-cell {
        padding: 5px;
        border: 1px solid #ddd;
        text-align: center;
    }
    .available {
        background-color: #d4edda;
        color: #155724;
    }
    .unavailable {
        background-color: #f8f9fa;
        color: #6c757d;
    }
    .assigned-a {
        background-color: #e3f2fd;
        color: #1565c0;
        font-weight: bold;
    }
    .assigned-b {
        background-color: #f3e5f5;
        color: #7b1fa2;
        font-weight: bold;
    }
    .conflict {
        background-color: #fff3cd;
        color: #856404;
    }
    .debug-box {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

def generate_all_time_slots():
    """모든 시간 슬롯 생성"""
    slots = []
    
    # 금요일 (9/12): 19:00~22:00
    friday_times = [
        "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
    ]
    for time in friday_times:
        slots.append(f"9/12 {time}")
    
    # 토요일 (9/13): 10:00~22:00
    saturday_times = [
        "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
        "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
        "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
        "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
    ]
    for time in saturday_times:
        slots.append(f"9/13 {time}")
    
    # 일요일 (9/14): 10:00~22:00
    sunday_times = saturday_times  # 같은 시간대
    for time in sunday_times:
        slots.append(f"9/14 {time}")
    
    return slots

def create_availability_matrix(teams_data):
    """팀별 가능 시간 매트릭스 생성"""
    all_slots = generate_all_time_slots()
    
    # 매트릭스 초기화
    matrix_data = {}
    
    for team in teams_data:
        team_name = team.get("팀명", "미확인")
        available_times = team.get("면접 가능 시간", [])
        
        # 가능 시간이 문자열인 경우 리스트로 변환
        if isinstance(available_times, str):
            if available_times == "미확인":
                available_times = []
            else:
                available_times = [available_times]
        
        # 각 슬롯에 대해 가능 여부 체크
        team_availability = []
        for slot in all_slots:
            if slot in available_times:
                team_availability.append("⭕")
            else:
                team_availability.append("")
        
        matrix_data[team_name] = team_availability
    
    # DataFrame 생성
    df = pd.DataFrame(matrix_data, index=all_slots)
    return df.T  # 행과 열 전치 (팀을 행으로)

def create_time_slot_summary(teams_data):
    """시간대별 가능 팀 수 요약"""
    all_slots = generate_all_time_slots()
    slot_counts = {}
    slot_teams = {}
    
    for slot in all_slots:
        slot_counts[slot] = 0
        slot_teams[slot] = []
        
        for team in teams_data:
            team_name = team.get("팀명", "미확인")
            available_times = team.get("면접 가능 시간", [])
            
            if isinstance(available_times, str):
                if available_times != "미확인":
                    available_times = [available_times]
                else:
                    available_times = []
            
            if slot in available_times:
                slot_counts[slot] += 1
                slot_teams[slot].append(team_name)
    
    return slot_counts, slot_teams

def main():
    st.markdown("<h1 class='main-header'>📊 SNAAC 면접 스케줄 매트릭스</h1>", unsafe_allow_html=True)
    st.markdown("### 시간대별 팀 가능 여부 한눈에 보기")
    
    # 세션 상태 초기화
    if 'teams' not in st.session_state:
        st.session_state.teams = []
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = []
    
    # 탭 생성
    tabs = st.tabs([
        "📄 PDF 업로드 & 디버깅",
        "📊 가용성 매트릭스",
        "📈 시간대별 통계",
        "🔍 충돌 분석",
        "💾 데이터 검증"
    ])
    
    # Tab 1: PDF 업로드 & 디버깅
    with tabs[0]:
        st.markdown("## 📄 PDF 파일 업로드 및 파싱 디버깅")
        
        uploaded_files = st.file_uploader(
            "PDF 파일을 선택하세요 (여러 개 가능)",
            type=['pdf'],
            accept_multiple_files=True,
            help="각 팀의 면접 신청서 PDF를 업로드하세요"
        )
        
        if uploaded_files:
            if st.button("🔍 PDF 분석 시작 (디버그 모드)", type="primary"):
                st.session_state.teams = []
                st.session_state.debug_info = []
                
                for uploaded_file in uploaded_files:
                    with st.expander(f"📄 {uploaded_file.name} 분석 과정", expanded=True):
                        # PDF를 임시 파일로 저장
                        temp_path = f"/tmp/{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # PDF 텍스트 추출 (디버깅용)
                        st.markdown("#### 🔬 PDF 원본 텍스트 (처음 2000자)")
                        import pdfplumber
                        with pdfplumber.open(temp_path) as pdf:
                            full_text = ""
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    full_text += text + "\n"
                            
                            st.text_area("원본 텍스트", full_text[:2000], height=200, key=f"raw_text_{uploaded_file.name}")
                        
                        # PDF 분석
                        result = process_pdf_file(temp_path)
                        
                        # 파싱 결과 표시
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📋 추출된 정보**")
                            st.json({
                                "팀명": result["팀명"],
                                "대표자명": result["대표자명"],
                                "이메일": result["이메일"],
                                "전화번호": result["전화번호"]
                            })
                        
                        with col2:
                            st.markdown("**⏰ 가능 시간**")
                            times = result["면접 가능 시간"]
                            if isinstance(times, list):
                                st.write(f"총 {len(times)}개 시간대")
                                if len(times) > 10:
                                    st.text_area("가능 시간 목록", "\n".join(times[:10]) + f"\n... 외 {len(times)-10}개", 
                                               height=200, key=f"times_list_{uploaded_file.name}")
                                else:
                                    st.text_area("가능 시간 목록", "\n".join(times) if times else "없음", 
                                               height=200, key=f"times_full_{uploaded_file.name}")
                            else:
                                st.write(times)
                        
                        # 세션에 저장
                        st.session_state.teams.append({
                            "파일명": uploaded_file.name,
                            "팀명": result["팀명"],
                            "대표자명": result["대표자명"],
                            "이메일": result["이메일"],
                            "전화번호": result["전화번호"],
                            "면접 가능 시간": result["면접 가능 시간"]
                        })
                        
                        # 디버그 정보 저장
                        debug_entry = {
                            "파일명": uploaded_file.name,
                            "텍스트 길이": len(full_text),
                            "추출된 시간 수": len(times) if isinstance(times, list) else 0,
                            "원본 텍스트 샘플": full_text[1500:2000] if len(full_text) > 1500 else full_text[-500:]
                        }
                        st.session_state.debug_info.append(debug_entry)
                
                st.success(f"✅ {len(uploaded_files)}개 파일 분석 완료!")
    
    # Tab 2: 가용성 매트릭스
    with tabs[1]:
        st.markdown("## 📊 팀별 면접 가능 시간 매트릭스")
        
        if st.session_state.teams:
            # 매트릭스 생성
            matrix_df = create_availability_matrix(st.session_state.teams)
            
            # 통계
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 팀 수", len(st.session_state.teams))
            with col2:
                total_slots = 36  # 전체 시간 슬롯 수
                st.metric("총 시간 슬롯", total_slots)
            with col3:
                avg_availability = sum(len(t["면접 가능 시간"]) if isinstance(t["면접 가능 시간"], list) else 0 
                                      for t in st.session_state.teams) / len(st.session_state.teams)
                st.metric("평균 가능 시간", f"{avg_availability:.1f}개")
            
            # 매트릭스 표시
            st.markdown("### 🗓️ 시간대별 가능 여부 (⭕ = 가능)")
            
            # 스타일링된 DataFrame
            def style_matrix(val):
                if val == "⭕":
                    return 'background-color: #d4edda; color: #155724;'
                return ''
            
            styled_df = matrix_df.style.applymap(style_matrix)
            st.dataframe(styled_df, use_container_width=True, height=600)
            
            # 문제 진단
            st.markdown("### 🔍 문제 진단")
            for team in st.session_state.teams:
                times = team["면접 가능 시간"]
                if isinstance(times, list):
                    if len(times) > 30:  # 거의 모든 시간 가능
                        st.warning(f"⚠️ **{team['팀명']}**: {len(times)}개 시간 가능 (거의 모든 시간)")
                    elif len(times) == 0:
                        st.error(f"❌ **{team['팀명']}**: 가능 시간 없음")
                    elif len(times) == 1:
                        st.info(f"ℹ️ **{team['팀명']}**: 단 1개 시간만 가능 - {times[0] if times else '없음'}")
        else:
            st.info("PDF를 업로드하고 분석을 실행하세요.")
    
    # Tab 3: 시간대별 통계
    with tabs[2]:
        st.markdown("## 📈 시간대별 가능 팀 통계")
        
        if st.session_state.teams:
            slot_counts, slot_teams = create_time_slot_summary(st.session_state.teams)
            
            # 날짜별로 그룹화
            dates = ["9/12", "9/13", "9/14"]
            
            for date in dates:
                st.markdown(f"### 📅 {date} {'(금)' if date == '9/12' else '(토)' if date == '9/13' else '(일)'}")
                
                date_slots = {k: v for k, v in slot_counts.items() if k.startswith(date)}
                
                # 시간대별 차트
                times = [k.split()[1] for k in date_slots.keys()]
                counts = list(date_slots.values())
                
                # Plotly 차트
                fig = go.Figure(data=[
                    go.Bar(x=times, y=counts, text=counts, textposition='auto',
                          marker_color=['green' if c >= 2 else 'orange' if c == 1 else 'red' for c in counts])
                ])
                fig.update_layout(
                    title=f"{date} 시간대별 가능 팀 수",
                    xaxis_title="시간대",
                    yaxis_title="가능 팀 수",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 상세 정보
                with st.expander(f"{date} 시간대별 가능 팀 목록"):
                    for slot, teams in slot_teams.items():
                        if slot.startswith(date) and teams:
                            st.write(f"**{slot}**: {', '.join(teams)}")
    
    # Tab 4: 충돌 분석
    with tabs[3]:
        st.markdown("## 🔍 시간대 충돌 및 문제 분석")
        
        if st.session_state.teams:
            # 충돌 가능성이 높은 시간대 찾기
            slot_counts, slot_teams = create_time_slot_summary(st.session_state.teams)
            
            # 경쟁률 높은 시간대 (3팀 이상)
            high_competition = {k: v for k, v in slot_teams.items() if len(v) > 2}
            
            if high_competition:
                st.markdown("### ⚠️ 경쟁률 높은 시간대 (3팀 이상)")
                for slot, teams in sorted(high_competition.items(), key=lambda x: -len(x[1])):
                    st.warning(f"**{slot}**: {len(teams)}팀 경쟁")
                    st.write(f"   경쟁 팀: {', '.join(teams)}")
            
            # 가능 시간이 적은 팀 (3개 이하)
            st.markdown("### 🚨 제약이 많은 팀 (가능 시간 3개 이하)")
            constrained_teams = []
            for team in st.session_state.teams:
                times = team["면접 가능 시간"]
                if isinstance(times, list) and 0 < len(times) <= 3:
                    constrained_teams.append((team["팀명"], times))
            
            if constrained_teams:
                for team_name, times in constrained_teams:
                    st.error(f"**{team_name}**: {len(times)}개 시간만 가능")
                    st.write(f"   가능 시간: {', '.join(times)}")
            else:
                st.success("✅ 모든 팀이 충분한 가능 시간을 가지고 있습니다.")
    
    # Tab 5: 데이터 검증
    with tabs[4]:
        st.markdown("## 💾 추출 데이터 검증")
        
        if st.session_state.teams:
            # 전체 데이터 표시
            df_teams = pd.DataFrame(st.session_state.teams)
            
            # 가능 시간 수 계산
            df_teams['가능 시간 수'] = df_teams['면접 가능 시간'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            
            st.dataframe(df_teams[['파일명', '팀명', '대표자명', '이메일', '전화번호', '가능 시간 수']], 
                        use_container_width=True)
            
            # 디버그 정보
            if st.session_state.debug_info:
                st.markdown("### 🐛 디버그 정보")
                for debug in st.session_state.debug_info:
                    with st.expander(f"📄 {debug['파일명']}"):
                        st.write(f"- 텍스트 길이: {debug['텍스트 길이']}자")
                        st.write(f"- 추출된 시간 수: {debug['추출된 시간 수']}개")
                        st.text_area("원본 텍스트 샘플 (시간대 부분)", debug['원본 텍스트 샘플'], 
                                   height=150, key=f"debug_sample_{debug['파일명']}")
            
            # CSV 다운로드
            csv = df_teams.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 데이터 CSV 다운로드",
                data=csv,
                file_name=f"면접팀_분석_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()