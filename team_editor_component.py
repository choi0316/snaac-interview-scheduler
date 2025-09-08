"""
팀 정보 편집 컴포넌트
"""

import streamlit as st
from typing import Dict, List, Any

def render_team_editor(team_name: str, team_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    팀 정보를 편집할 수 있는 UI 컴포넌트
    
    Args:
        team_name: 팀 이름
        team_info: 팀 정보 딕셔너리
    
    Returns:
        수정된 팀 정보
    """
    
    st.markdown(f"### ✏️ {team_name} 정보 수정")
    
    # 기본 정보 수정
    col1, col2 = st.columns(2)
    with col1:
        new_team_name = st.text_input("팀명", value=team_info.get('팀명', team_name), key=f"team_name_{team_name}")
        new_email = st.text_input("이메일", value=team_info.get('이메일', ''), key=f"email_{team_name}")
    
    with col2:
        new_representative = st.text_input("대표자명", value=team_info.get('대표자명', ''), key=f"rep_{team_name}")
        new_phone = st.text_input("전화번호", value=team_info.get('전화번호', ''), key=f"phone_{team_name}")
    
    st.markdown("---")
    st.markdown("### 📅 면접 가능 시간대 선택")
    st.info("체크박스를 선택/해제하여 면접 가능 시간을 수정할 수 있습니다.")
    
    # 시간대 정의
    time_slots = {
        "9/12": [
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ],
        "9/13": [
            "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
            "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
            "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ],
        "9/14": [
            "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
            "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
            "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
            "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
        ]
    }
    
    # 현재 선택된 시간대 파싱
    current_available = team_info.get('가능시간', [])
    selected_times = set()
    for time_str in current_available:
        # "9/12 19:00-19:45" 형식을 파싱
        parts = time_str.split(' ')
        if len(parts) >= 2:
            selected_times.add(time_str)
    
    # 날짜별 탭으로 시간대 표시
    date_tabs = st.tabs(["9/12 (금)", "9/13 (토)", "9/14 (일)"])
    
    new_available_times = []
    
    for idx, (date, date_tab) in enumerate(zip(["9/12", "9/13", "9/14"], date_tabs)):
        with date_tab:
            date_names = {"9/12": "9월 12일 (금)", "9/13": "9월 13일 (토)", "9/14": "9월 14일 (일)"}
            st.markdown(f"**{date_names[date]}**")
            
            # 전체 선택/해제 버튼
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button(f"전체 선택", key=f"select_all_{team_name}_{date}"):
                    for time_slot in time_slots[date]:
                        st.session_state[f"cb_{team_name}_{date}_{time_slot}"] = True
            with col2:
                if st.button(f"전체 해제", key=f"deselect_all_{team_name}_{date}"):
                    for time_slot in time_slots[date]:
                        st.session_state[f"cb_{team_name}_{date}_{time_slot}"] = False
            
            # 시간대별 체크박스 (4열로 표시)
            cols = st.columns(4)
            for i, time_slot in enumerate(time_slots[date]):
                with cols[i % 4]:
                    # 초기값 설정
                    time_str = f"{date} {time_slot}"
                    default_checked = time_str in selected_times
                    
                    # 세션 상태에 초기값 설정 (처음 렌더링 시)
                    key = f"cb_{team_name}_{date}_{time_slot}"
                    if key not in st.session_state:
                        st.session_state[key] = default_checked
                    
                    # 체크박스 표시
                    is_checked = st.checkbox(
                        time_slot,
                        value=st.session_state[key],
                        key=key
                    )
                    
                    if is_checked:
                        new_available_times.append(time_str)
    
    # 업데이트된 정보 반환
    updated_info = team_info.copy()
    updated_info['팀명'] = new_team_name
    updated_info['대표자명'] = new_representative
    updated_info['이메일'] = new_email
    updated_info['전화번호'] = new_phone
    updated_info['가능시간'] = new_available_times
    updated_info['면접 가능 시간'] = new_available_times  # 호환성을 위해 두 키 모두 업데이트
    
    # 상세 시간표 업데이트 (improved_pdf_processor와 호환)
    detailed_schedule = {"9/12": [], "9/13": [], "9/14": []}
    for time_str in new_available_times:
        parts = time_str.split(' ')
        if len(parts) >= 2:
            date = parts[0]
            time = parts[1]
            if date in detailed_schedule:
                detailed_schedule[date].append((time, True))
    
    # 선택되지 않은 시간도 False로 추가
    for date, slots in time_slots.items():
        for slot in slots:
            time_str = f"{date} {slot}"
            if time_str not in new_available_times:
                detailed_schedule[date].append((slot, False))
    
    # 시간 순서대로 정렬
    for date in detailed_schedule:
        detailed_schedule[date].sort(key=lambda x: x[0])
    
    updated_info['상세 시간표'] = detailed_schedule
    
    return updated_info

def render_manual_team_adder():
    """
    수동으로 팀을 추가할 수 있는 UI 컴포넌트
    """
    st.markdown("### ➕ 새 팀 추가")
    
    with st.form("add_team_form"):
        col1, col2 = st.columns(2)
        with col1:
            team_name = st.text_input("팀명*", placeholder="예: 팀 이름")
            email = st.text_input("이메일", placeholder="example@email.com")
        
        with col2:
            representative = st.text_input("대표자명", placeholder="홍길동")
            phone = st.text_input("전화번호", placeholder="010-1234-5678")
        
        st.markdown("### 📅 면접 가능 시간대")
        
        # 시간대 정의
        time_slots = {
            "9/12": [
                "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
            ],
            "9/13": [
                "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
                "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
                "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
                "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
            ],
            "9/14": [
                "10:00-10:45", "10:45-11:30", "11:30-12:15", "12:15-13:00",
                "13:00-13:45", "13:45-14:30", "14:30-15:15", "15:15-16:00",
                "16:00-16:45", "16:45-17:30", "17:30-18:15", "18:15-19:00",
                "19:00-19:45", "19:45-20:30", "20:30-21:15", "21:15-22:00"
            ]
        }
        
        selected_times = []
        
        # 날짜별 체크박스
        for date in ["9/12", "9/13", "9/14"]:
            date_names = {"9/12": "9월 12일 (금)", "9/13": "9월 13일 (토)", "9/14": "9월 14일 (일)"}
            st.markdown(f"**{date_names[date]}**")
            
            cols = st.columns(4)
            for i, time_slot in enumerate(time_slots[date]):
                with cols[i % 4]:
                    if st.checkbox(time_slot, key=f"new_{date}_{time_slot}"):
                        selected_times.append(f"{date} {time_slot}")
        
        submitted = st.form_submit_button("팀 추가", type="primary")
        
        if submitted:
            if not team_name:
                st.error("팀명은 필수 입력 항목입니다.")
                return None
            
            # 상세 시간표 생성
            detailed_schedule = {"9/12": [], "9/13": [], "9/14": []}
            for time_str in selected_times:
                parts = time_str.split(' ')
                if len(parts) >= 2:
                    date = parts[0]
                    time = parts[1]
                    if date in detailed_schedule:
                        detailed_schedule[date].append((time, True))
            
            # 선택되지 않은 시간도 False로 추가
            for date, slots in time_slots.items():
                for slot in slots:
                    time_str = f"{date} {slot}"
                    if time_str not in selected_times:
                        detailed_schedule[date].append((slot, False))
            
            # 시간 순서대로 정렬
            for date in detailed_schedule:
                detailed_schedule[date].sort(key=lambda x: x[0])
            
            new_team = {
                '팀명': team_name,
                '대표자명': representative or '미입력',
                '이메일': email or '미입력',
                '전화번호': phone or '미입력',
                '가능시간': selected_times,
                '면접 가능 시간': selected_times,
                '상세 시간표': detailed_schedule,
                '파일명': '수동입력'
            }
            
            return team_name, new_team
    
    return None