import os
import requests
from PIL import Image
import streamlit as st

# 페이지 설정 (wide 모드)
st.set_page_config(
    page_title="AI 논문 번역기 & 단어장", page_icon="📚", layout="wide"
)

# 🎨 CSS를 이용해 카메라 입력창 크기 키우기 및 UI 최적화
st.markdown(
    """
    <style>
    /* 카메라 입력 컴포넌트의 최대 너비를 넓히고 높이감 부여 */
    [data-testid="stCameraInput"] {
        max-width: 100% !important;
    }
    [data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 기본 API 키
DEFAULT_API_KEY = "up_Y7OKHBUB2q7pi7C4E1ILIWItBAUOG"

st.title("📚 나만의 AI 전공 논문 번역기 & 단어장")
st.markdown("카메라로 사진을 찍거나 이미지를 업로드하면 **학술 번역**과 **단어장**을 생성합니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input(
    "Upstage API Key", value=DEFAULT_API_KEY, type="password"
)

# 탭 나누기: 카메라 직접 촬영 vs 기존 파일 업로드
tab1, tab2 = st.tabs(["📸 카메라 촬영 (확대 뷰)", "📁 파일 업로드"])

input_image = None

with tab1:
  st.markdown("### 📷 논문/원서 촬영")
  camera_image = st.camera_input("카메라로 텍스트를 촬영하세요")
  if camera_image:
    input_image = camera_image

with tab2:
  st.markdown("### 📁 이미지 파일 업로드")
  uploaded_file = st.file_uploader(
      "논문 이미지 선택", type=["png", "jpg", "jpeg"]
  )
  if uploaded_file:
    input_image = uploaded_file

# --- 핵심 로직 ---


# 1. Upstage OCR 함수
def extract_text_with_upstage_ocr(image_file, api_key):
  url = "https://api.upstage.ai/v1/document-ai/ocr"
  headers = {"Authorization": f"Bearer {api_key}"}
  files = {"document": image_file}
  response = requests.post(url, headers=headers, files=files)
  if response.status_code == 200:
    return response.json().get("text", "")
  else:
    st.error(f"OCR 오류 ({response.status_code}): {response.text}")
    return None


# 2. Solar LLM 처리 함수
def process_with_solar(extracted_text, api_key):
  url = "https://api.upstage.ai/v1/solar/chat/completions"
  headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
  }
  system_content = """
    당신은 전문 학술 번역가입니다. 제공된 텍스트를 전문적인 한국어로 번역하고, 핵심 단어를 표로 정리해 주세요.
    ### 📝 전공 맞춤 번역
    (번역 결과)
    ### 📖 핵심 단어장
    | 영어 단어 | 품사 | 한국어 뜻 | 맥락 설명 |
    | :--- | :--- | :--- | :--- |
    """
  payload = {
      "model": "solar-pro",
      "messages": [
          {"role": "system", "content": system_content},
          {"role": "user", "content": f"텍스트:\n\n{extracted_text}"},
      ],
      "temperature": 0.3,
  }
  response = requests.post(url, headers=headers, json=payload)
  if response.status_code == 200:
    return response.json()["choices"][0]["message"]["content"]
  else:
    st.error(f"LLM 오류 ({response.status_code}): {response.text}")
    return None


# 실행 버튼 및 결과 출력
if input_image is not None:
  st.markdown("---")
  st.info("✅ 이미지가 성공적으로 준비되었습니다!")

  if st.button("🚀 번역 및 단어장 생성", type="primary", use_container_width=True):
    if not api_key:
      st.warning("API 키를 확인해주세요.")
    else:
      with st.spinner("Upstage AI가 분석 중입니다..."):
        input_image.seek(0)
        ocr_text = extract_text_with_upstage_ocr(input_image, api_key)
        if ocr_text:
          result = process_with_solar(ocr_text, api_key)
          if result:
            st.markdown("---")
            st.markdown(result)
