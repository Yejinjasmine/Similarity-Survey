import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import base64
import json
import requests
from io import StringIO

st.set_page_config(page_title="문장 유사도 설문", layout="wide")

PAIR_FILE = "sentence_pairs.csv"
SAVE_FILE = "responses_temp.csv"
BACKUP_FILE = "responses_backup.csv"
TIME_LIMIT_HOURS = 6
GITHUB_REPO = "Yejinjasmine/Similarity-Survey"
GITHUB_FILE_PATH = "responses_backup.csv"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # secrets.toml에 추가 필요

# GitHub 업로드 함수
def upload_to_github(csv_path, repo, path_in_repo, branch, token):
    with open(csv_path, "rb") as f:
        content = f.read()
    encoded_content = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.get(url, headers=headers)
    sha = res.json()["sha"] if res.status_code == 200 else None

    data = {
        "message": "자동 백업: 응답 데이터 업데이트",
        "branch": branch,
        "content": encoded_content
    }
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code not in [200, 201]:
        print("❌ GitHub 업로드 실패:", response.text)

# GitHub에서 백업 로드 함수
def load_backup_from_github():
    github_raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_FILE_PATH}"
    try:
        response = requests.get(github_raw_url)
        if response.status_code == 200:
            csv_text = response.text
            return pd.read_csv(StringIO(csv_text))
    except:
        pass
    return pd.DataFrame()

@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df_original = load_data()
total_pairs = len(df_original)

# 세션 상태 초기화
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

def generate_participant_id(name, year, phone):
    suffix = phone[-4:] if len(phone) >= 4 else "XXXX"
    return f"{name}_{year}_{suffix}"

def get_remaining_time():
    if st.session_state.paused:
        return st.session_state.remaining_at_pause
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_HOURS * 3600 - elapsed)
    return timedelta(seconds=int(remaining))

# 설문 시작 및 이전 응답 로딩
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
            participant_id = f"{name}_{year}_{suffix}"
            if os.path.exists(BACKUP_FILE):
                prev_data = pd.read_csv(BACKUP_FILE)
            else:
                prev_data = load_backup_from_github()

            if not prev_data.empty and participant_id in prev_data["참가자 ID"].values:
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

# 이후 설문 로직에서 응답 저장할 때 다음 코드 추가
# df_responses.to_csv(BACKUP_FILE, index=False)
# upload_to_github(BACKUP_FILE, GITHUB_REPO, GITHUB_FILE_PATH, GITHUB_BRANCH, GITHUB_TOKEN)
