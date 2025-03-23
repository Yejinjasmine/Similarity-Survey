import streamlit as st
import os
import pandas as pd
from datetime import datetime
from datetime import timedelta
import time
import random

st.set_page_config(page_title="문장 유사도 설문", layout="wide")

if "step" not in st.session_state:
    st.session_state.step = "start_check"

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
            if os.path.exists("responses_backup.csv"):
                prev_data = pd.read_csv("responses_backup.csv")
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
            else:
                st.error("⚠️ 백업 데이터가 존재하지 않습니다.")

PAIR_FILE = "sentence_pairs.csv"
SAVE_FILE = "responses_temp.csv"
BACKUP_FILE = "responses_backup.csv"
TIME_LIMIT_HOURS = 6

@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df_original = load_data()
total_pairs = len(df_original)

if "step" not in st.session_state:
    st.session_state.step = "intro"
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

if st.session_state.step == "intro":
    st.title("📋 문장 유사도 평가 설문 - 시작 전 정보 입력")
    st.markdown("🔔 **본 설문조사는 핸드폰이 아닌 컴퓨터로 응시하기를 권장합니다.**")

    with st.form("user_info_form"):
        st.header("1️⃣ 기본 정보 입력")

        name = st.text_input("이름")
        birth_year = st.selectbox("출생 연도", list(range(1985, 2009)))
        age = st.selectbox("나이 (만 나이 기준)", list(range(17, 41)))
        gender = st.selectbox("성별", ["남자", "여자", "Non-binary 혹은 Third gender", "기타"])
        phone = st.text_input("휴대폰 번호 (대시 '-' 없이 입력)")
        bank_account = st.text_input("사례비를 지급받을 은행 및 계좌번호 (예: 농협 312-0000-0000-31)")
        affiliation = st.text_input("소속 (예: 서울대학교 공과대학 산업공학과 삶향상기술연구실)")
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
        st.session_state.paused = False
        st.rerun()

elif st.session_state.step == "instruction":
    st.header("2️⃣ 설문 설명 및 동의")
    st.markdown("#### ✅ 이 설문은 '위험 경향과 관련된 행동' 문장들의 유사도를 평가하는 것입니다.")

    explanations = [
        "총 **46개의 문장**으로 구성된 **1035쌍 (=46 x 45 / 2)**의 문장쌍을 평가합니다."  
        "본 연구는 조건부 자율 주행에서의 위험 태도 및 위험 행동 척도를 개발하기 위해 몇 가지 단계를 실행하며, 본 설문은 그 중 두번째 단계에 해당합니다. 해당 설문에서 얻어진 자료는 추후 세번째 단계에 활용될 수 있습니다.",
        "조건부 자율 주행(Level 3)에서는 첨단 운전자 보조 시스템(ADAS)이 일부 교통 조건에서 자율 주행을 실시합니다. 이에 따라 운전자는 핸들에서 손을 놓고 비운전과업(NDRT)에 참여할 수 있습니다. ADAS가 자율 주행을 지속하기 어려운 상황에서는 제어권 전환 요청이 있을 수 있으며, 운전자는 해당 요청에 응해 수동 운전을 해야 합니다.",
        "조건부 자율 주행 중, 운전자의 안전이 아닌 다른 가치를 중요하게 여기는 지에 따라 위험 경향(risk preference)을 위험 추구(risk loving)와 위험 회피(risk averse) 중 어느 쪽에 가까운지로 분류할 수 있습니다. 정가운데 지점은 위험 중립(risk neutral)이라 부릅니다.",
        "위험 추구는 자신의 행동이 처벌이나 손실을 초래할 가능성이 있어도 그러한 행동을 하려는 성향입니다. 예: 운전 중 핸드폰을 사용하는 행위.",
        "위험 회피는 자신의 행동이 손실을 초래할 가능성이 있을 때 그러한 행동을 피하려는 성향입니다. 예: 자율 주행 중 도로 상황을 주시하는 행위.",
        "이번 설문에서는 서울대학교에 재학 중인 한국어 모국어 화자들이 참여 예정입니다. 과업을 완료하는 데에는 2시간이 소요됩니다.",
        "참가자들은 제시되는 문장들을 '완전히 다름'부터 '거의 동일함'까지의 7개 척도로 평가합니다.\n\n*7개 척도*\n1 - 완전히 다름\n2 - 매우 다름\n3 - 꽤 다름\n4 - 비슷함\n5 - 꽤 비슷함\n6 - 매우 비슷함\n7 - 거의 동일함",
        "두 문장이 유사하다고 생각되는 만큼 점수를 평가하면 됩니다. 사람마다 평가가 다를 수 있으므로, 일관적인 기준에 따라 주관적으로 판단하시면 됩니다.\n\n예: '사자는 매우 용맹한 동물이다.' vs '호랑이는 매우 용감한 동물이다.' -> 사자와 호랑이가 다른 동물이지만 맹수라는 점이 비슷하고, 용맹함과 용감함이 정확히 같은 뜻은 아니나 비슷한 의미라고 생각되어 두 문장의 관계를 "5점 - 꽤 비슷함"으로 평가할 수 있음. 혹은, 사자와 호랑이는 엄연히 다른 동물이며, 꼭 용맹스러워야 용감한 것은 아니기 때문에 두 문장의 관계를 "3점 - 꽤 다름"으로 평가할 수 있음.",
        "본 설문은 응답자의 위험 경향을 묻는 것이 아니라, 쌍으로 제시된 두 문장이 얼마나 유사한지를 묻는 것입니다."
    ]

    all_checked = True
    for i, explanation in enumerate(explanations):
        st.markdown(f"- {explanation}")
        if not st.checkbox(f"이해했습니다"):
            all_checked = False

    if all_checked:
        st.success("설문을 시작할 수 있습니다!")
        if st.button("👉 설문 시작하기"):
            st.session_state.step = "survey"
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        st.warning("모든 항목을 체크해야 다음 단계로 진행할 수 있습니다.")
