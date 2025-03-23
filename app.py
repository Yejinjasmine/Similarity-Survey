
import streamlit as st
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="문장 유사도 설문", layout="wide")

PAIR_FILE = "sentence_pairs.csv"
SAVE_FILE = "responses_temp.csv"
BACKUP_FILE = "responses_backup.csv"
TIME_LIMIT_HOURS = 6

@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df_original = load_data()
total_pairs = len(df_original)

# Session initialization
if "step" not in st.session_state:
    st.session_state.step = "start_check"
if "index" not in st.session_state:
    st.session_state.index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "paused" not in st.session_state:
    st.session_state.paused = False
if "shuffled_ids" not in st.session_state:
    st.session_state.shuffled_ids = random.sample(range(total_pairs), total_pairs)

def load_previous_responses():
    if os.path.exists(BACKUP_FILE):
        return pd.read_csv(BACKUP_FILE)
    return pd.DataFrame()

def generate_participant_id(name, year, phone_suffix):
    return f"{name}_{year}_{phone_suffix}"

def get_remaining_time():
    if st.session_state.paused:
        return st.session_state.remaining_at_pause
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_HOURS * 3600 - elapsed)
    return timedelta(seconds=int(remaining))

# Step: Start/resume check
if st.session_state.step == "start_check":
    st.title("📋 문장 유사도 평가 설문 시작")

    st.markdown("🔔 **본 설문조사는 핸드폰이 아닌 컴퓨터로 응시하기를 권장합니다.**")

    choice = st.radio("기존에 응답 중이던 설문이 있나요?", ["아니오, 처음부터 시작합니다", "예, 이어서 응답하겠습니다"])

    if choice == "아니오, 처음부터 시작합니다":
        if st.button("👉 설문 처음부터 시작하기"):
            st.session_state.step = "intro"
            st.rerun()
    else:
        with st.form("resume_form"):
            st.subheader("이전에 사용한 정보 입력")
            name = st.text_input("이름")
            year = st.selectbox("출생 연도", list(range(1985, 2009)))
            suffix = st.text_input("휴대폰 번호 마지막 4자리")
            submitted = st.form_submit_button("기존 정보로 이어서 응답하기")

        if submitted:
            participant_id = generate_participant_id(name, year, suffix)
            prev_data = load_previous_responses()
            if participant_id in prev_data["참가자 ID"].values:
                st.session_state.user_info = {
                    "참가자 ID": participant_id,
                    "이름": name,
                    "출생 연도": year,
                    "휴대폰": f"****{suffix}",
                    "응답 시작 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.responses = prev_data.to_dict("records")
                st.session_state.step = "survey"
                st.session_state.start_time = time.time()
                st.success("✅ 이전 응답을 불러왔습니다. 설문을 이어서 진행합니다.")
                st.rerun()
            else:
                st.error("⚠️ 해당 정보로 된 기존 응답이 없습니다. 이름, 출생연도, 번호 뒷자리를 확인해주세요.")
