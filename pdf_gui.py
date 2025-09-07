"""
면접 스케줄링 시스템 - PDF 처리 가능한 GUI
"""

import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from typing import List, Optional
import os

# 데이터 클래스
@dataclass
class TeamInfo:
    team_name: str = ""
    representative_name: str = ""
    email: str = ""
    phone: str = ""
    available_times: List[str] = None
    
    def __post_init__(self):
        if self.available_times is None:
            self.available_times = []

# Streamlit 설정
st.set_page_config(
    page_title="면접 스케줄링 시스템 - PDF 처리",
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
    }
</style>
""", unsafe_allow_html=True)

def extract_team_info_from_pdf(pdf_file) -> TeamInfo:
    """PDF에서 팀 정보 추출"""
    team_info = TeamInfo()
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # 디버깅을 위해 텍스트 일부 출력
            st.text_area("추출된 텍스트 (처음 1000자)", full_text[:1000], height=200)
            
            # 팀명 패턴
            team_patterns = [
                r'팀\s*명\s*[:：]\s*([^\n]+)',
                r'팀명\s*[:：]\s*([^\n]+)',
                r'프로젝트\s*명\s*[:：]\s*([^\n]+)',
                r'서비스\s*명\s*[:：]\s*([^\n]+)',
                r'사업\s*명\s*[:：]\s*([^\n]+)',
                r'회사명\s*[:：]\s*([^\n]+)',
                r'업체명\s*[:：]\s*([^\n]+)',
                r'상\s*호\s*\([^)]+\)\s*([^\n]+)',
            ]
            
            for pattern in team_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    team_info.team_name = match.group(1).strip()
                    break
            
            # 대표자명 패턴
            rep_patterns = [
                r'대표자\s*[:：]\s*([^\n]+)',
                r'대표\s*[:：]\s*([^\n]+)',
                r'성\s*명\s*\([^)]*대표[^)]*\)\s*([^\n]+)',
                r'팀장\s*[:：]\s*([^\n]+)',
                r'리더\s*[:：]\s*([^\n]+)',
                r'이름\s*[:：]\s*([^\n]+)',
                r'성명\s*[:：]\s*([^\n]+)',
            ]
            
            for pattern in rep_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    team_info.representative_name = match.group(1).strip()
                    break
            
            # 이메일 패턴
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_match = re.search(email_pattern, full_text)
            if email_match:
                team_info.email = email_match.group(0)
            
            # 전화번호 패턴
            phone_patterns = [
                r'010[-\s]?\d{4}[-\s]?\d{4}',
                r'02[-\s]?\d{3,4}[-\s]?\d{4}',
                r'031[-\s]?\d{3,4}[-\s]?\d{4}',
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, full_text)
                if match:
                    team_info.phone = match.group(0)
                    break
            
            # 시간 패턴
            time_patterns = [
                r'(\d{1,2}시)',
                r'(\d{1,2}:\d{2})',
                r'오전\s*(\d{1,2})',
                r'오후\s*(\d{1,2})',
                r'(\d{1,2})\s*시\s*-\s*(\d{1,2})\s*시',
            ]
            
            times = []
            for pattern in time_patterns:
                matches = re.findall(pattern, full_text)
                for match in matches[:3]:  # 최대 3개
                    if isinstance(match, tuple):
                        times.extend(match)
                    else:
                        times.append(match)
            
            team_info.available_times = list(set(times))[:5]
            
    except Exception as e:
        st.error(f"PDF 처리 오류: {e}")
    
    return team_info

def main():
    st.markdown("<h1 class='main-header'>📄 PDF 기반 면접 스케줄링 시스템</h1>", unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'teams' not in st.session_state:
        st.session_state.teams = []
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📄 PDF 업로드", "📊 추출된 데이터", "💾 엑셀 저장"])
    
    with tab1:
        st.markdown("### PDF 파일 업로드")
        st.info("""
        📌 **지원 형식**: 
        - 팀명/회사명
        - 대표자명
        - 이메일
        - 전화번호
        - 면접 가능 시간
        """)
        
        uploaded_files = st.file_uploader(
            "PDF 파일을 선택하세요 (여러 개 가능)",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.markdown(f"### 📁 업로드된 파일: {len(uploaded_files)}개")
            
            if st.button("🔍 PDF 분석 시작", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    st.markdown(f"#### 📄 {uploaded_file.name} 분석 중...")
                    
                    # PDF 분석
                    team_info = extract_team_info_from_pdf(uploaded_file)
                    
                    # 파일명에서 추가 정보 추출
                    if not team_info.team_name:
                        filename = uploaded_file.name
                        if '_' in filename:
                            parts = filename.split('_')
                            if len(parts) > 1:
                                team_info.team_name = parts[1].replace('.pdf', '')
                    
                    # 결과 표시
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**추출된 정보:**")
                        st.text(f"팀명: {team_info.team_name or '미확인'}")
                        st.text(f"대표자: {team_info.representative_name or '미확인'}")
                        st.text(f"이메일: {team_info.email or '미확인'}")
                    
                    with col2:
                        st.text(f"전화번호: {team_info.phone or '미확인'}")
                        st.text(f"가능시간: {', '.join(team_info.available_times) if team_info.available_times else '미확인'}")
                    
                    # 수동 수정 옵션
                    with st.expander("✏️ 정보 수정"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            team_info.team_name = st.text_input(
                                f"팀명 ({i+1})", 
                                value=team_info.team_name,
                                key=f"team_{i}"
                            )
                            team_info.representative_name = st.text_input(
                                f"대표자명 ({i+1})", 
                                value=team_info.representative_name,
                                key=f"rep_{i}"
                            )
                            team_info.email = st.text_input(
                                f"이메일 ({i+1})", 
                                value=team_info.email,
                                key=f"email_{i}"
                            )
                        
                        with col2:
                            team_info.phone = st.text_input(
                                f"전화번호 ({i+1})", 
                                value=team_info.phone,
                                key=f"phone_{i}"
                            )
                            times_str = st.text_input(
                                f"가능시간 ({i+1}) - 쉼표로 구분", 
                                value=', '.join(team_info.available_times),
                                key=f"times_{i}"
                            )
                            team_info.available_times = [t.strip() for t in times_str.split(',') if t.strip()]
                    
                    # 팀 정보 저장
                    st.session_state.teams.append({
                        "파일명": uploaded_file.name,
                        "팀명": team_info.team_name or "미확인",
                        "대표자명": team_info.representative_name or "미확인",
                        "이메일": team_info.email or "미확인",
                        "전화번호": team_info.phone or "미확인",
                        "면접 가능시간": ', '.join(team_info.available_times) if team_info.available_times else "미확인"
                    })
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ {len(uploaded_files)}개 파일 분석 완료!")
    
    with tab2:
        st.markdown("### 📊 추출된 팀 정보")
        
        if st.session_state.teams:
            df = pd.DataFrame(st.session_state.teams)
            
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
                valid_times = df[df['면접 가능시간'] != '미확인']['면접 가능시간'].count()
                st.metric("시간 정보", f"{valid_times}/{len(df)}")
            
            # 데이터 초기화 버튼
            if st.button("🗑️ 데이터 초기화", type="secondary"):
                st.session_state.teams = []
                st.rerun()
        else:
            st.info("아직 분석된 데이터가 없습니다. PDF를 업로드해주세요.")
    
    with tab3:
        st.markdown("### 💾 엑셀 파일로 저장")
        
        if st.session_state.teams:
            # Excel 파일 생성
            df = pd.DataFrame(st.session_state.teams)
            
            # Excel 다운로드 버튼
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
            
            # CSV 다운로드 옵션
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 파일 다운로드 (한글 지원)",
                data=csv,
                file_name=f"면접팀정보_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    main()