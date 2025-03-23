
import streamlit as st
import pandas as pd
import os

# Load sentence pairs
@st.cache_data
def load_data():
    return pd.read_csv("sentence_pairs.csv")

df = load_data()
total_pairs = len(df)

# Initialize session state
if "index" not in st.session_state:
    st.session_state.index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []

st.title("문장 유사도 평가 설문")
st.write("다음은 두 문장의 의미 유사도를 평가하는 설문입니다. 1~7점 중에서 선택해 주세요.")
st.write("**1점: 완전히 다름**, **7점: 거의 동일함**")

# Show current sentence pair
i = st.session_state.index
if i < total_pairs:
    row = df.iloc[i]
    st.markdown(f"### 문장 A
> {row['Sentence A']}")
    st.markdown(f"### 문장 B
> {row['Sentence B']}")
    
    rating = st.radio("이 두 문장은 얼마나 유사한가요?", [1, 2, 3, 4, 5, 6, 7], horizontal=True)

    if st.button("다음"):
        st.session_state.responses.append({
            "ID": int(row["ID"]),
            "Sentence A": row["Sentence A"],
            "Sentence B": row["Sentence B"],
            "Rating": rating
        })
        st.session_state.index += 1
        st.experimental_rerun()
else:
    st.success("설문이 완료되었습니다. 감사합니다!")
    
    # Save responses
    responses_df = pd.DataFrame(st.session_state.responses)
    filename = "responses.csv"
    responses_df.to_csv(filename, index=False)
    
    st.download_button("응답 데이터 다운로드", data=responses_df.to_csv(index=False), file_name="responses.csv", mime="text/csv")
