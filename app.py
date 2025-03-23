import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import random

st.set_page_config(page_title="문장 유사도 설문", layout="wide")

# 초기 상태 설정
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

# 파일 경로
PAIR_FILE = "sentence_pairs.csv"
SAVE_FILE = "responses_temp.csv"
BACKUP_FILE = "responses_backup.csv"
TIME_LIMIT_HOURS = 6

@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df_original = load_data()
total_pairs = len(df_original)
if "shuffled_ids" not in st.session_state:
    st.session_state.shuffled_ids = random.sample(range(total_pairs), total_pairs)

# 함수
def load_previous_responses():
    if os.path.exists(SAVE_FILE):
        return pd.read_csv(SAVE_FILE)
    return pd.DataFrame()

def generate_participant_id(name, year, phone):
    suffix = phone[-4:] if len(phone) >= 4 else "XXXX"
    return f"{name}_{year}_{suffix}"

def get_remaining_time():
    if st.session_state.paused:
        return st.session_state.remaining_at_pause
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_HOURS * 3600 - elapsed)
    return timedelta(seconds=int(remaining))


# 1단계: 시작 화면
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
                    st.error("⚠️ 해당 정보로 된 기존 응답이 없습니다.")
            else:
                st.error("⚠️ 백업 데이터가 존재하지 않습니다.")

# 2단계: 사용자 정보 입력
elif st.session_state.step == "intro":
    st.title("📋 문장 유사도 평가 설문 - 시작 전 정보 입력")
    with st.form("user_info_form"):
        st.header("1️⃣ 기본 정보 입력")
        name = st.text_input("이름")
        birth_year = st.selectbox("출생 연도", list(range(1985, 2009)))
        age = st.selectbox("나이 (만 나이 기준)", list(range(17, 41)))
        gender = st.selectbox("성별", ["남자", "여자", "Non-binary 혹은 Third gender", "기타"])
        phone = st.text_input("휴대폰 번호 (대시 '-' 없이 입력)")
        bank_account = st.text_input("사례비를 지급받을 은행 및 계좌번호")
        affiliation = st.text_input("소속")
        ssn = st.text_input("주민등록번호 (예: 970910-xxxxxxx)")
        email = st.text_input("이메일 주소")
        submitted = st.form_submit_button("다음 단계로 진행하기")

    if submitted:
        participant_id = generate_participant_id(name, birth_year, phone)
        st.session_state.user_info = {
            "참가자 ID": participant_id,
            "이름": name,
            "출생 연도": birth_year,
            "나이": age,
            "성별": gender,
            "휴대폰": phone,
            "계좌": bank_account,
            "소속": affiliation,
            "주민등록번호": ssn,
            "이메일": email,
            "응답 시작 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.responses = load_previous_responses().to_dict("records")
        st.session_state.step = "instruction"
        st.session_state.start_time = time.time()
        st.rerun()

# 3단계: 설명 및 동의
elif st.session_state.step == "instruction":
    st.header("2️⃣ 설문 설명 및 동의")
    st.markdown("#### ✅ 이 설문은 '위험 경향과 관련된 행동' 문장들의 유사도를 평가하는 것입니다.")

    explanations = [
        "총 **46개의 문장**으로 구성된 **1035쌍 (=46 x 45 / 2)**의 문장쌍을 평가합니다.",
        "본 연구는 조건부 자율 주행에서의 위험 태도 및 위험 행동 척도를 개발하기 위한 두 번째 단계입니다.",
        "조건부 자율 주행(Level 3)은 ADAS가 자율주행을 하고, 필요 시 운전자에게 제어권을 요청합니다.",
        "위험 경향은 위험 추구(risk loving)와 위험 회피(risk averse)로 나뉩니다.",
        "위험 추구 예: 운전 중 핸드폰 사용.",
        "위험 회피 예: 자율 주행 중 도로 상황 주시.",
        "설문은 서울대학교 한국어 화자가 참여하며, 약 2시간 소요됩니다.",
        "응답자는 문장쌍을 7개 척도로 평가합니다:\n1 - 완전히 다름\n2 - 매우 다름\n3 - 꽤 다름\n4 - 비슷함\n5 - 꽤 비슷함\n6 - 매우 비슷함\n7 - 거의 동일함",
        "문장 유사도는 주관적으로 판단하는 것이므로 정해진 정답이 없습니다. 예시:\n'사자는 매우 용맹한 동물이다.' vs '호랑이는 매우 용감한 동물이다.' → \"5점\" 또는 \"3점\" \"2점\" 등 평가 가능.",
        "본 설문은 응답자의 위험 성향이 아닌 문장 유사도를 묻는 것입니다."
    ]

    all_checked = True
    for i, explanation in enumerate(explanations):
        st.markdown(f"- {explanation}")
        if not st.checkbox("이해했습니다", key=f"agree_{i}"):
            all_checked = False

    if all_checked:
        st.success("설문을 시작할 수 있습니다!")
        if st.button("👉 설문 시작하기"):
            st.session_state.step = "survey"
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        st.warning("모든 항목을 체크해야 다음 단계로 진행할 수 있습니다.")

# 4단계: 설문
elif st.session_state.step == "survey":
    st.title("문장 유사도 평가 설문")

    remaining = get_remaining_time()
    if remaining.total_seconds() <= 0:
        st.warning("⚠️ 응답 가능 시간이 초과되었습니다. 설문은 계속 진행할 수 있지만, 가능한 빠르게 완료해 주세요.")
    else:
        st.info(f"⏱️ 남은 시간: {remaining}")

    if st.session_state.paused:
        if st.button("▶️ 설문 다시 시작하기"):
            st.session_state.paused = False
            st.session_state.start_time = time.time() - (TIME_LIMIT_HOURS * 3600 - st.session_state.remaining_at_pause.total_seconds())
            st.rerun()
    else:
        if st.button("⏸️ 설문 일시 중지하기"):
            st.session_state.paused = True
            st.session_state.remaining_at_pause = remaining
            st.rerun()

    answered_ids = [r["ID"] for r in st.session_state.responses if r["참가자 ID"] == st.session_state.user_info["참가자 ID"]]
    current_idx = len(answered_ids)
    st.markdown(f"**응답 질문: {current_idx + 1} / {total_pairs}**")

    rating_labels = {
        "1 - 완전히 다름 (Totally different)": 1,
        "2 - 매우 다름 (Very different)": 2,
        "3 - 꽤 다름 (Rather different)": 3,
        "4 - 비슷함 (Similar)": 4,
        "5 - 꽤 비슷함 (Rather similar)": 5,
        "6 - 매우 비슷함 (Very similar)": 6,
        "7 - 거의 동일함 (Totally similar)": 7
    }

    i = st.session_state.index
    while i < total_pairs:
        shuffled_i = st.session_state.shuffled_ids[i]
        row = df_original.iloc[shuffled_i]
        if not any(r["ID"] == row["ID"] and r["참가자 ID"] == st.session_state.user_info["참가자 ID"] for r in st.session_state.responses):
            break
        i += 1
        st.session_state.index = i

    if i < total_pairs:
        shuffled_i = st.session_state.shuffled_ids[i]
        row = df_original.iloc[shuffled_i]

        st.markdown(f"<p style='font-size:18px; font-weight:bold;'>Sentence A</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:22px;'>{row['Sentence A']}</p>", unsafe_allow_html=True)

        st.markdown(f"<p style='font-size:18px; font-weight:bold;'>Sentence B</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:22px;'>{row['Sentence B']}</p>", unsafe_allow_html=True)

        choice = st.radio("이 두 문장은 얼마나 유사한가요?", list(rating_labels.keys()), index=3)
        rating = rating_labels[choice]

        if st.button("다음"):
            combined = {
                "ID": int(row["ID"]),
                "Sentence A": row["Sentence A"],
                "Sentence B": row["Sentence B"],
                "Rating": rating,
                "응답 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            combined.update(st.session_state.user_info)
            st.session_state.responses.append(combined)

            df_responses = pd.DataFrame(st.session_state.responses)
            df_responses.to_csv(SAVE_FILE, index=False)
            df_responses.to_csv(BACKUP_FILE, index=False)

            st.session_state.index += 1
            st.rerun()
    else:
        st.success("설문이 완료되었습니다. 감사합니다!")
        final_df = pd.DataFrame(st.session_state.responses)
        filename = "responses.csv"
        final_df.to_csv(filename, index=False)
        st.download_button("응답 데이터 다운로드", data=final_df.to_csv(index=False), file_name=filename, mime="text/csv")
