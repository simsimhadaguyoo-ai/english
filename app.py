import os
import requests
from PIL import Image
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="AI 논문 번역기 & 단어장", page_icon="📚", layout="wide"
)

# 기본 API 키 설정 (보안 주의: 배포 시에는 Streamlit Secrets 사용 권장)
DEFAULT_API_KEY = "up_Y7OKHBUB2q7pi7C4E1ILIWItBAUOG"

# 사이드바: 설정
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input(
    "Upstage API Key", value=DEFAULT_API_KEY, type="password"
)

st.title("📚 나만의 AI 전공 논문 번역기 & 단어장")
st.markdown("논문이나 원서 페이지 캡처본을 업로드하면 **학술적 번역**과 **핵심 단어장**을 한 번에 생성합니다.")

# 파일 업로드
uploaded_file = st.file_uploader(
    "논문 이미지 업로드 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)

# 1. Upstage OCR 함수
def extract_text_with_upstage_ocr(image_file, api_key):
    url = "https://api.upstage.ai/v1/document-ai/ocr"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": image_file}
    
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        st.error(f"OCR API 오류 발생 ({response.status_code}): {response.text}")
        return None

# 2. Solar LLM 번역 및 단어장 생성 함수
def process_with_solar(extracted_text, api_key):
    url = "https://api.upstage.ai/v1/solar/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_content = """
    당신은 전문 학술 번역가입니다. 제공된 영어 텍스트를 문맥을 고려하여 매끄럽고 전문적인 한국어로 번역하고,
    학습에 도움이 되는 핵심 단어와 숙어를 표 형식으로 정리해 주세요.
    
    출력 형식:
    ### 📝 전공 맞춤 번역
    (번역 결과 작성)
    
    ### 📖 핵심 단어장
    | 영어 단어 | 품사 | 한국어 뜻 | 맥락 설명 |
    | :--- | :--- | :--- | :--- |
    | 단어 | 품사 | 뜻 | 설명 |
    """

    payload = {
        "model": "solar-pro",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"다음 추출된 텍스트를 처리해 줘:\n\n{extracted_text}"},
        ],
        "temperature": 0.3,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Solar LLM API 오류 발생 ({response.status_code}): {response.text}")
        return None

# 메인 실행 로직
if uploaded_file is not None:
    # 이미지 미리보기
    st.image(uploaded_file, caption="업로드한 이미지", use_container_width=True)
    
    if st.button("🚀 번역 및 단어장 생성하기", type="primary"):
        if not api_key:
            st.warning("API Key가 입력되지 않았습니다.")
        else:
            with st.spinner("이미지 분석 및 번역 중..."):
                uploaded_file.seek(0)
                # 1단계: OCR 실행
                ocr_text = extract_text_with_upstage_ocr(uploaded_file, api_key)
                
                if ocr_text:
                    # 2단계: Solar LLM 실행
                    result = process_with_solar(ocr_text, api_key)
                    if result:
                        st.markdown("---")
                        st.markdown(result)
