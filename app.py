
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="문장 유사도 설문", layout="wide")

# CSV 파일 경로
PAIR_FILE = "sentence_pairs.csv"
SAVE_FILE = "responses_temp.csv"
TIME_LIMIT_HOURS = 6

# 문장쌍 불러오기
@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df = load_data()
total_pairs = len(df)

# 중간 저장 응답 불러오기
def load_previous_responses():
    if os.path.exists(SAVE_FILE):
        return pd.read_csv(SAVE_FILE)
    else:
        return pd.DataFrame()

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = "intro"
if "index" not in st.session_state:
    st.session_state.index = 0
if "responses" not in st.session_state:
    st.session_state.responses = load_previous_responses().to_dict("records")
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# 참가자 ID 생성 (이름 + 생년 + 전화번호 일부로 구성)
def generate_participant_id(name, year, phone):
    suffix = phone[-4:] if len(phone) >= 4 else "XXXX"
    return f"{name}_{year}_{suffix}"

# 남은 시간 계산
def get_remaining_time():
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_HOURS * 3600 - elapsed)
    return timedelta(seconds=int(remaining))

# Step 1: 사용자 정보
if st.session_state.step == "intro":
    st.title("📋 문장 유사도 평가 설문 - 시작 전 정보 입력")

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
        st.session_state.step = "instruction"
        st.session_state.start_time = time.time()
        st.rerun()

# Step 2: 설명 및 확인
elif st.session_state.step == "instruction":
    st.header("2️⃣ 설문 설명 및 동의")

    st.markdown("#### ✅ 이 섹션은 '위험 경향과 관련된 행동' 문장들의 유사도를 평가하는 것입니다.")
    st.markdown("- 총 **46개의 문장 쌍**에 대해, **1035번의 유사도 평가**를 하게 됩니다.")
    st.markdown("- 1035 = 46 × 45 ÷ 2")

    understood_1 = st.checkbox("이해했습니다. (위 설명)")
    
    st.markdown("#### ✅ 본 설문지는 응답자의 '위험 성향'을 묻는 것이 아닙니다.")
    st.markdown("- 쌍으로 제시된 두 문장이 **얼마나 유사한지를 평가**하는 것이 목적입니다.")
    
    understood_2 = st.checkbox("이해했습니다. (설문 목적)")

    if understood_1 and understood_2:
        st.success("설문을 시작할 수 있습니다! 아래 버튼을 눌러 주세요.")
        if st.button("👉 설문 시작하기"):
            st.session_state.step = "survey"
            st.rerun()
    else:
        st.warning("두 설명 모두 '이해했습니다' 체크 후 진행할 수 있습니다.")

# Step 3: 설문
elif st.session_state.step == "survey":
    st.title("문장 유사도 평가 설문")

    # 응답 제한 시간 표시
    remaining = get_remaining_time()
    if remaining.total_seconds() <= 0:
        st.error("⏰ 응답 시간이 초과되었습니다. 6시간 이내에 설문을 완료해 주세요.")
        st.stop()
    else:
        st.info(f"⏱️ 남은 시간: {remaining}")

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

    while i < total_pairs and any(r["ID"] == df.iloc[i]["ID"] and r["참가자 ID"] == st.session_state.user_info["참가자 ID"] for r in st.session_state.responses):
        i += 1
        st.session_state.index = i

    if i < total_pairs:
        row = df.iloc[i]

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

            # 중간 저장
            pd.DataFrame(st.session_state.responses).to_csv(SAVE_FILE, index=False)

            st.session_state.index += 1
            st.rerun()
    else:
        st.success("설문이 완료되었습니다. 감사합니다!")

        responses_df = pd.DataFrame(st.session_state.responses)
        filename = "responses.csv"
        responses_df.to_csv(filename, index=False)

        st.download_button("응답 데이터 다운로드", data=responses_df.to_csv(index=False), file_name="responses.csv", mime="text/csv")
