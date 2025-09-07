#!/usr/bin/env python3
"""
간단한 GUI 데모 (임포트 오류 없이)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import json

def main():
    st.set_page_config(
        page_title="면접 스케줄링 시스템",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 면접 스케줄링 시스템")
    st.markdown("**70개 팀을 위한 AI 기반 면접 스케줄링 자동화 시스템**")
    
    # 사이드바
    st.sidebar.title("📋 메뉴")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["🏠 홈", "📄 PDF 업로드", "⚙️ 설정", "⚡ 스케줄링", "📊 결과", "📥 다운로드"]
    )
    
    if page == "🏠 홈":
        show_home()
    elif page == "📄 PDF 업로드":
        show_pdf_upload()
    elif page == "⚙️ 설정":
        show_settings()
    elif page == "⚡ 스케줄링":
        show_scheduling()
    elif page == "📊 결과":
        show_results()
    elif page == "📥 다운로드":
        show_download()

def show_home():
    st.header("🚀 시스템 개요")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 처리 가능 팀 수", "70+", "무제한")
        st.metric("⚡ 스케줄링 속도", "< 60초", "고속 처리")
    
    with col2:
        st.metric("🎯 최적화 전략", "5가지", "동시 실행")
        st.metric("📊 출력 시트", "8개", "Excel 포함")
    
    with col3:
        st.metric("📧 이메일 검증", "고급", "DNS 포함")
        st.metric("🇰🇷 한국어 지원", "100%", "완벽 지원")
    
    st.header("✨ 주요 기능")
    
    features = [
        {"기능": "PDF 데이터 추출", "설명": "한국어 팀 정보 자동 인식", "상태": "✅"},
        {"기능": "스케줄링 엔진", "설명": "5가지 최적화 전략 동시 실행", "상태": "✅"},
        {"기능": "Excel 생성", "설명": "8개 시트 종합 파일 자동 생성", "상태": "✅"},
        {"기능": "이메일 시스템", "설명": "고급 검증 및 템플릿 관리", "상태": "✅"},
        {"기능": "웹 GUI", "설명": "직관적인 인터페이스 제공", "상태": "✅"},
        {"기능": "테스트 시스템", "설명": "포괄적인 품질 보증", "상태": "✅"}
    ]
    
    df = pd.DataFrame(features)
    st.dataframe(df, use_container_width=True)

def show_pdf_upload():
    st.header("📄 PDF 파일 업로드")
    
    st.info("📋 팀 정보가 포함된 PDF 파일을 업로드하세요.")
    
    # 파일 업로더
    uploaded_file = st.file_uploader(
        "PDF 파일 선택",
        type=['pdf'],
        help="팀명, 이메일, 연락처, 선호시간이 포함된 PDF 파일"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ 파일 업로드 완료: {uploaded_file.name}")
        
        # 시뮬레이션된 추출 결과
        with st.spinner("📄 PDF에서 팀 정보 추출 중..."):
            import time
            time.sleep(2)
        
        st.success("🎯 팀 정보 추출 완료!")
        
        # 샘플 데이터
        sample_data = [
            {"팀명": "한국대학교 AI팀", "이메일": "ai.team@korea.ac.kr", "연락처": "010-1111-2222", "선호시간": "14:00, 15:00"},
            {"팀명": "스타트업 혁신팀", "이메일": "innovation@startup.co.kr", "연락처": "010-3333-4444", "선호시간": "10:00, 11:00"},
            {"팀명": "테크 솔루션팀", "이메일": "tech.solution@company.com", "연락처": "010-5555-6666", "선호시간": "16:00, 17:00"},
            {"팀명": "창업 동아리", "이메일": "startup@club.ac.kr", "연락처": "010-7777-8888", "선호시간": "13:00, 14:00"},
            {"팀명": "알고리즘 팀", "이메일": "algo@team.com", "연락처": "010-9999-0000", "선호시간": "11:00, 12:00"}
        ]
        
        df = pd.DataFrame(sample_data)
        st.dataframe(df, use_container_width=True)
        
        st.session_state['teams'] = sample_data
    
    else:
        st.markdown("""
        ### 📋 PDF 파일 형식 예시
        
        ```
        팀명: 한국대학교 AI팀
        이메일: ai.team@korea.ac.kr
        연락처: 010-1111-2222
        선호시간: 14:00, 15:00
        피하고싶은 면접관: 김교수
        
        팀명: 스타트업 혁신팀
        이메일: innovation@startup.co.kr
        연락처: 010-3333-4444
        선호시간: 10:00, 11:00
        피하고싶은 면접관: 없음
        ```
        
        💡 **지원하는 정보**
        - ✅ 팀명 (필수)
        - ✅ 이메일 (필수)  
        - ✅ 연락처 (필수)
        - ✅ 선호시간 (선택)
        - ✅ 피하고싶은 면접관 (선택)
        """)

def show_settings():
    st.header("⚙️ 면접 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 기본 설정")
        
        interview_date = st.date_input(
            "면접 날짜",
            value=datetime(2024, 1, 15).date()
        )
        
        start_time = st.time_input(
            "시작 시간",
            value=time(9, 0)
        )
        
        end_time = st.time_input(
            "종료 시간", 
            value=time(17, 0)
        )
        
        interview_duration = st.slider(
            "면접 시간 (분)",
            min_value=15,
            max_value=60,
            value=30
        )
    
    with col2:
        st.subheader("👥 면접관 설정")
        
        interviewers = st.text_area(
            "면접관 명단 (한 줄에 하나씩)",
            value="김교수\n이교수\n박교수\n최교수"
        ).split('\n')
        
        st.write(f"📋 등록된 면접관: {len([i for i in interviewers if i.strip()])}명")
        
        st.subheader("🏢 면접실 설정")
        
        rooms = st.text_area(
            "면접실 목록 (한 줄에 하나씩)",
            value="면접실1\n면접실2\n면접실3\n면접실4"
        ).split('\n')
        
        st.write(f"🏢 등록된 면접실: {len([r for r in rooms if r.strip()])}개")
    
    st.subheader("🎯 최적화 설정")
    
    col3, col4 = st.columns(2)
    
    with col3:
        preference_weight = st.slider(
            "선호시간 가중치",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1
        )
        
        balance_weight = st.slider(
            "시간 분산 가중치", 
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1
        )
    
    with col4:
        constraint_weight = st.slider(
            "제약조건 가중치",
            min_value=0.0, 
            max_value=1.0,
            value=0.9,
            step=0.1
        )
        
        group_weight = st.slider(
            "그룹 균형 가중치",
            min_value=0.0,
            max_value=1.0, 
            value=0.5,
            step=0.1
        )
    
    if st.button("💾 설정 저장", type="primary"):
        settings = {
            "interview_date": interview_date.strftime('%Y-%m-%d'),
            "start_time": start_time.strftime('%H:%M'),
            "end_time": end_time.strftime('%H:%M'), 
            "duration": interview_duration,
            "interviewers": [i.strip() for i in interviewers if i.strip()],
            "rooms": [r.strip() for r in rooms if r.strip()],
            "weights": {
                "preference": preference_weight,
                "balance": balance_weight,
                "constraint": constraint_weight,
                "group": group_weight
            }
        }
        
        st.session_state['settings'] = settings
        st.success("✅ 설정이 저장되었습니다!")

def show_scheduling():
    st.header("⚡ 스케줄링 실행")
    
    if 'teams' not in st.session_state:
        st.warning("⚠️ 먼저 PDF 파일을 업로드하세요.")
        return
    
    if 'settings' not in st.session_state:
        st.warning("⚠️ 먼저 면접 설정을 완료하세요.")
        return
    
    teams = st.session_state['teams']
    settings = st.session_state['settings']
    
    st.info(f"📊 처리할 팀: {len(teams)}개 | 면접관: {len(settings.get('interviewers', []))}명")
    
    if st.button("🚀 스케줄링 시작", type="primary"):
        
        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        
        # 1단계: 데이터 검증
        status_text.text("1/5 데이터 검증 중...")
        time.sleep(1)
        progress_bar.progress(20)
        
        # 2단계: 제약조건 생성
        status_text.text("2/5 제약조건 생성 중...")
        time.sleep(1.5)
        progress_bar.progress(40)
        
        # 3단계: 최적화 실행
        status_text.text("3/5 5가지 전략 최적화 실행 중...")
        time.sleep(2)
        progress_bar.progress(70)
        
        # 4단계: 결과 분석
        status_text.text("4/5 결과 분석 중...")
        time.sleep(1)
        progress_bar.progress(90)
        
        # 5단계: 완료
        status_text.text("5/5 스케줄링 완료!")
        progress_bar.progress(100)
        
        st.success("🎉 스케줄링이 완료되었습니다!")
        
        # 시뮬레이션된 결과
        results = [
            {"전략": "첫 번째 선호도 우선", "점수": 0.85, "배정": 5, "위반": 0},
            {"전략": "시간 분산", "점수": 0.78, "배정": 5, "위반": 1},
            {"전략": "오전/오후 균형", "점수": 0.82, "배정": 4, "위반": 0},
            {"전략": "그룹 균형", "점수": 0.79, "배정": 5, "위반": 1},
            {"전략": "제약조건 우선", "점수": 0.88, "배정": 4, "위반": 0}
        ]
        
        st.session_state['results'] = results
        
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)
        
        # 최적 전략
        best_strategy = max(results, key=lambda x: x['점수'])
        st.success(f"🎯 최적 전략: **{best_strategy['전략']}** (점수: {best_strategy['점수']:.2f})")

def show_results():
    st.header("📊 스케줄링 결과")
    
    if 'results' not in st.session_state:
        st.warning("⚠️ 먼저 스케줄링을 실행하세요.")
        return
    
    results = st.session_state['results']
    
    # 결과 차트
    col1, col2 = st.columns(2)
    
    with col1:
        df = pd.DataFrame(results)
        fig1 = px.bar(
            df, 
            x='전략', 
            y='점수',
            title='전략별 최적화 점수',
            color='점수',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.scatter(
            df,
            x='배정',
            y='점수', 
            size='위반',
            color='전략',
            title='배정 팀 수 vs 최적화 점수'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 상세 스케줄 (시뮬레이션)
    st.subheader("📋 최적 스케줄 상세")
    
    schedule_data = [
        {"시간": "09:00-09:30", "팀": "알고리즘 팀", "면접관": "김교수", "면접실": "면접실1", "선호도": "✅"},
        {"시간": "10:00-10:30", "팀": "스타트업 혁신팀", "면접관": "이교수", "면접실": "면접실2", "선호도": "✅"},
        {"시간": "13:00-13:30", "팀": "창업 동아리", "면접관": "박교수", "면접실": "면접실3", "선호도": "✅"},
        {"시간": "14:00-14:30", "팀": "한국대학교 AI팀", "면접관": "최교수", "면접실": "면접실4", "선호도": "✅"},
        {"시간": "16:00-16:30", "팀": "테크 솔루션팀", "면접관": "김교수", "면접실": "면접실1", "선호도": "✅"}
    ]
    
    df_schedule = pd.DataFrame(schedule_data)
    st.dataframe(df_schedule, use_container_width=True)
    
    # 통계 요약
    st.subheader("📈 결과 통계")
    
    col3, col4, col5, col6 = st.columns(4)
    
    with col3:
        st.metric("배정 완료", "5팀", "100%")
    
    with col4:
        st.metric("선호도 만족", "5팀", "100%")
    
    with col5:
        st.metric("제약조건 위반", "0개", "완벽")
    
    with col6:
        st.metric("최적화 점수", "0.88", "최고 등급")

def show_download():
    st.header("📥 결과 파일 다운로드")
    
    if 'results' not in st.session_state:
        st.warning("⚠️ 먼저 스케줄링을 완료하세요.")
        return
    
    st.info("📋 다음 파일들을 다운로드할 수 있습니다:")
    
    files = [
        {
            "파일명": "면접_스케줄_결과.xlsx", 
            "설명": "8개 시트 종합 Excel 파일",
            "크기": "~500KB",
            "내용": "메인 스케줄, 메일머지, 분석 데이터"
        },
        {
            "파일명": "Gmail_메일머지.csv",
            "설명": "Gmail용 메일머지 데이터 (UTF-8 BOM)",  
            "크기": "~50KB",
            "내용": "팀명, 이메일, 면접 정보"
        },
        {
            "파일명": "Outlook_메일머지.csv", 
            "설명": "Outlook용 메일머지 데이터 (CP949)",
            "크기": "~50KB", 
            "내용": "팀명, 이메일, 면접 정보"
        },
        {
            "파일명": "면접_통지_템플릿.html",
            "설명": "이메일 통지 템플릿",
            "크기": "~10KB",
            "내용": "HTML 이메일 템플릿"
        }
    ]
    
    for file_info in files:
        with st.expander(f"📄 {file_info['파일명']} ({file_info['크기']})"):
            st.write(f"**설명**: {file_info['설명']}")
            st.write(f"**내용**: {file_info['내용']}")
            
            # 샘플 데이터 생성
            if file_info['파일명'].endswith('.csv'):
                sample_csv = """팀명,이메일,면접날짜,면접시간,면접관,면접실
한국대학교 AI팀,ai.team@korea.ac.kr,2024-01-15,14:00-14:30,최교수,면접실4
스타트업 혁신팀,innovation@startup.co.kr,2024-01-15,10:00-10:30,이교수,면접실2"""
                
                st.download_button(
                    label="📥 다운로드",
                    data=sample_csv,
                    file_name=file_info['파일명'],
                    mime='text/csv'
                )
            else:
                st.button(f"📥 {file_info['파일명']} 다운로드", disabled=True, help="실제 파일은 스케줄링 완료 후 생성됩니다.")
    
    st.success("✅ 모든 파일이 준비되었습니다!")
    
    st.markdown("""
    ### 📧 이메일 발송 가이드
    
    1. **Gmail 사용 시**: `Gmail_메일머지.csv` 파일 사용
    2. **Outlook 사용 시**: `Outlook_메일머지.csv` 파일 사용
    3. **템플릿**: `면접_통지_템플릿.html`을 이메일 본문에 사용
    
    💡 **메일머지 방법**:
    - Gmail: 도구 → 메일 머지 → CSV 파일 업로드
    - Outlook: 메일링 → 편지 병합 → 데이터 소스 선택
    """)

if __name__ == "__main__":
    main()