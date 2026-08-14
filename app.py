import os
import requests
from PIL import Image
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="AI 전공 논문 번역기 & 단어장", page_icon="📚", layout="wide"
)

# 하드코딩된 API 키 설정
DEFAULT_API_KEY = "up_Y7OKHBUB2q7pi7C4E1ILIWItBAUOG"

# 사이드바: 설정 (API 키 입력란만 유지)
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input(
    "Upstage API Key", value=DEFAULT_API_KEY, type="password"
)

st.title("📚 나만의 AI 전공 논문 번역기 & 단어장")
st.markdown("논문 페이지 캡처본을 업로드하면 **학술 맞춤형 번역**과 **핵심 단어장**을 생성합니다.")

# 파일 업로드
uploaded_file = st.file_uploader(
    "이미지 업로드 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)


# Upstage OCR 함수
def extract_text_with_upstage_ocr(image_file, api_key):
  url = "https://api.upstage.ai/v1/document-ai/ocr"
  headers = {"Authorization": f"Bearer {api_key}"}
  files = {"document": image_file}
  response = requests.post(url, headers=headers, files=files)
  if response.status_code == 200:
    return response.json().get("text", "")
  else:
    st.error(f"OCR API 오류: {response.status_code} - {response.text}")
    return None


# Upstage Solar LLM 함수
def process_with_solar(extracted_text, api_key):
  url = "https://api.upstage.ai/v1/solar/chat/completions"
  headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
  }

  system_content = """
    당신은 탁월한 학술 논문 및 원서 전문 번역가입니다.
    제공된 텍스트를 문맥에 맞게 매끄럽게 번역하고, 중요한 핵심 단어를 정리해 주세요.
    
    ### 📝 전공 맞춤 번역
    (자연스럽고 전문적인 한국어 번역)
    
    ### 📖 핵심 단어장
    | 영어 단어 | 품사 | 한국어 뜻 | 맥락 설명/예시 |
    | :--- | :--- | :--- | :--- |
    """

  payload = {
      "model": "solar-pro",
      "messages": [
          {"role": "system", "content": system_content},
          {"role": "user", "content": f"다음 텍스트를 처리해 줘:\n\n{extracted_text}"},
      ],
      "temperature": 0.3,
  }

  response = requests.post(url, headers=headers, json=payload)
  if response.status_code == 200:
    return response.json()["choices"][0]["message"]["content"]
  else:
    st.error(f"Solar LLM API 오류: {response.status_code} - {response.text}")
    return None


# 메인 로직
if uploaded_file is not None:
  if not api_key:
    st.warning("API Key가 입력되지 않았습니다.")
  elif st.button("🚀 번역 및 단어장 생성", type="primary"):
    with st.spinner("Upstage OCR과 Solar LLM으로 분석 중입니다..."):
      uploaded_file.seek(0)
      ocr_text = extract_text_with_upstage_ocr(uploaded_file, api_key)
      if ocr_text:
        result = process_with_solar(ocr_text, api_key)
        if result:
          st.markdown("---")
          st.markdown(result)
