import os
import requests
from PIL import Image
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="AI 전공 논문 번역기 & 단어장", page_icon="📚", layout="wide"
)

# 사이드바: API 키 및 설정
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input(
    "Upstage API Key", type="password", help="Upstage 콘솔에서 발급받은 키를 입력하세요."
)
major_field = st.sidebar.text_input(
    "전공 분야 (선택)",
    placeholder="예: 컴퓨터공학, 생명과학, 경제학 등",
    help="전공 맥락을 반영한 정확한 번역을 위해 입력하세요.",
)

st.title("📚 나만의 AI 전공 논문 번역기 & 단어장")
st.markdown(
    "영문 논문이나 원서 페이지 캡처본을 업로드하면, **전공 맥락에 맞는 번역**과 **핵심 단어장**을 만들어 드립니다."
)

# 파일 업로드
uploaded_file = st.file_uploader(
    "논문/원서 페이지 이미지 업로드 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)


# Upstage OCR 함수
def extract_text_with_upstage_ocr(image_file, api_key):
  url = "https://api.upstage.ai/v1/document-ai/ocr"
  headers = {"Authorization": f"Bearer {api_key}"}
  files = {"document": image_file}

  try:
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
      result = response.json()
      # OCR 결과 텍스트 추출
      return result.get("text", "")
    else:
      st.error(f"OCR API 오류 발생: {response.status_code} - {response.text}")
      return None
  except Exception as e:
    st.error(f"OCR 요청 중 오류가 발생했습니다: {e}")
    return None


# Upstage Solar LLM 번역 및 단어장 추출 함수
def process_with_solar(extracted_text, major_field, api_key):
  url = "https://api.upstage.ai/v1/solar/chat/completions"
  headers = {
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
  }

  major_prompt = (
      f"사용자의 전공 분야는 '{major_field}'야."
      if major_field
      else "일반적인 학술 전공 분야야."
  )

  system_content = f"""
    너는 탁월한 학술 논문 번역가이자 전공 분야 전문가야. {major_prompt}
    제공되는 영어 텍스트를 바탕으로 다음 두 가지 작업을 수행해 줘:
    
    1. **전공 맞춤형 번역**: 일반 번역기가 아닌, 해당 학술/전공 맥락에 맞는 자연스럽고 전문적인 한국어 번역을 제공해 줘.
    2. **핵심 단어장**: 텍스트에 등장하는 전공 핵심 단어 또는 어려울 수 있는 학술 어휘 5~10개를 골라 아래 양식에 맞게 정리해 줘.
    
    반드시 아래 마크다운 형식으로 출력해 줘:
    
    ### 📝 전공 맞춤 번역
    (번역 결과 작성)
    
    ### 📖 핵심 단어 및 숙어 정리
    | 영어 단어 | 품사 | 한국어 뜻 | 전공 맥락 설명/예시 |
    | :--- | :--- | :--- | :--- |
    | 단어1 | 품사 | 뜻 | 설명 |
    """

  payload = {
      "model": "solar-1.5-mini-chat",  # 또는 solar-pro
      "messages": [
          {"role": "system", "content": system_content},
          {
              "role": "user",
              "content": (
                  f"다음 추출된 영문 텍스트를 처리해 줘:\n\n{extracted_text}"
              ),
          },
      ],
      "temperature": 0.3,
  }

  try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
      return response.json()["choices"][0]["message"]["content"]
    else:
      st.error(
          f"Solar LLM API 오류 발생: {response.status_code} - {response.text}"
      )
      return None
  except Exception as e:
    st.error(f"LLM 요청 중 오류가 발생했습니다: {e}")
    return None


# 메인 로직 처리
if uploaded_file is not None:
  col1, col2 = st.columns([1, 1])

  with col1:
    st.subheader("🖼️ 업로드된 이미지")
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

  with col2:
    st.subheader("⚙️ 처리 결과")
    if not api_key:
      st.warning(
          "⚠️ 사이드바에 Upstage API Key를 먼저 입력해주세요.", icon="🔑"
      )
    else:
      if st.button("🚀 번역 및 단어장 생성하기", type="primary"):
        with st.spinner(
            "Upstage OCR로 텍스트를 추출하고 Solar LLM이 분석 중입니다..."
        ):
          # 파일 포인터를 처음으로 돌려 업로드 준비
          uploaded_file.seek(0)

          # 단계 1: OCR 실행
          ocr_text = extract_text_with_upstage_ocr(uploaded_file, api_key)

          if ocr_text:
            with st.expander("🔍 추출된 원본 영문 텍스트 (OCR 결과)"):
              st.text(ocr_text)

            # 단계 2: Solar LLM 실행
            ai_response = process_with_solar(ocr_text, major_field, api_key)

            if ai_response:
              st.markdown("---")
              st.markdown(ai_response)
