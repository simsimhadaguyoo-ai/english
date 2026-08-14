import io
import requests
from PIL import Image
import streamlit as st

# ==========================================
# [개발자 설정] API Key
# ==========================================
UPSTAGE_API_KEY = "up_Y7OKHBUB2q7pi7C4E1ILIWItBAUOG"
# ==========================================

st.set_page_config(
    page_title="AI 학년별 맞춤 원서 번역기 (B&W)",
    page_icon="📚",
    layout="centered",
)

# 🎨 [디자인 고정] 미니멀 매트 블랙 테마 및 표준 CSS 옵션 반영
st.markdown(
    """
    <style>
        .main { background-color: #FFFFFF; }
        div.stButton > button:first-child {
            background-color: #1E293B !important;
            color: white !important;
            border-radius: 8px !important;
            border: 1px solid #1E293B !important;
            padding: 10px 24px !important;
            font-weight: 500 !important;
            width: 100% !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #000000 !important;
            border-color: #000000 !important;
        }
        h1 { color: #000000; font-weight: 700 !important; text-align: center; letter-spacing: -0.5px; }
        .sub-title { text-align: center; color: #666666; margin-bottom: 40px; font-size: 0.95rem; }
    </style>
""",
    unsafe_allow_html=True,
)


# 🛠️ 이미지 포맷을 RGB로 강제 전처리하는 함수
def preprocess_image(uploaded_file):
  try:
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P", "L"):
      img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()
  except Exception as e:
    st.error(f"이미지 전처리 중 오류가 발생했습니다: {e}")
    return None


# 🛠️ Upstage Document AI OCR API 호출 함수 (URL 수정 완료)
def extract_text_from_image(image_bytes, api_key):
  try:
    url = "https://api.upstage.ai/v1/document-ai/ocr"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": ("image.jpg", io.BytesIO(image_bytes), "image/jpeg")}

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
      return response.json().get("text", "")
    else:
      st.error(
          f"OCR 인식에 실패했습니다. (서버 응답 코드: {response.status_code})"
      )
      return None
  except Exception as e:
    st.error(f"네트워크 오류가 발생했습니다: {e}")
    return None


# 🛠️ Upstage Solar LLM API 호출 함수 (URL 및 모델명 수정 완료)
def generate_translation_and_vocab(
    english_text, api_key, major_info, user_level
):
  try:
    url = "https://api.upstage.ai/v1/solar/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    level_instruction = ""
    if user_level == "고등학교 1~2학년 (기초/내신)":
      level_instruction = (
          "- 번역 수준: 수능 및 내신 기초를 다지는 고등학생 눈높이입니다. 구조가"
          " 복잡한 문장은 끊어 읽기 형태로 직관적으로 번역해 주고, 문장 구조가"
          " 한눈에 보이게 다듬어 주세요.\n- 단어장 수준: 핵심 '수능 필수 영단어"
          " 및 숙어'를 5개 이상 뽑아주시고, 단어의 뜻과 예문을 포함해 주세요."
      )
    elif user_level == "고등학교 3학년 (수능/심화입시)":
      level_instruction = (
          "- 번역 수준: EBS 연계 교재 고난도 지문 분석 수준입니다. 은유적이거나"
          " 꼬여있는 문장을 '주제와 핵심 요지'가 명확하게 전달되도록 해설지처럼"
          " 깔끔하게 의역해 주세요.\n- 단어장 수준: 모의고사 1등급 고난도 어휘"
          " 위주로 발췌하고, 문맥적 해석을 돕는 '구문 독해 팁'을 추가해"
          " 주세요."
      )
    elif user_level == "대학 신입생 / 입문자 (학부 1~2학년)":
      level_instruction = (
          "- 번역 수준: 전공 원서를 처음 읽는 저학년 수준입니다. 생소한 학술"
          " 전문 용어가 등장하면 단어 옆에 괄호()를 치고 '일상적인 비유나 쉬운"
          " 예시 설명'을 본문 속에 직접 주입해 주세요.\n- 단어장 수준: 전공 기초"
          " 어휘 위주로 뽑고, 기초 개념 지식을 친절하게 풀어서 기술해 주세요."
      )
    elif user_level == "학부 고학년 (학부 3~4학년)":
      level_instruction = (
          "- 번역 수준: 전공 서적 교재나 학술 논문 번역본 표준 규격에 맞추어,"
          " 실제 세미나에서 사용하는 매끄럽고 세련된 학술적 어조로 의역해"
          " 주세요.\n- 단어장 수준: 학술 전문 용어 위주로 발췌하고, 졸업 연구에"
          " 인용 서술할 수 있는 정확한 전공 학술적 정의를 기재해 주세요."
      )
    elif user_level == "대학원생 / 연구원 (석박사 단계)":
      level_instruction = (
          "- 번역 수준: 실무 및 연구 전문가용입니다. 기초적인 개념 설명은"
          " 배제하고, 해외 유명 저널의 초록(Abstract)처럼 극도로 정교하고"
          " 조밀하며 압축된 프로페셔널한 번역 톤을 유지해 주세요.\n- 단어장"
          " 수준: 최신 연구 트렌드와 직결된 고난도 핵심 키워드 위주로 간결하게"
          " 주석을 달아주세요."
      )

    system_prompt = (
        f"너는 학생들이 영어 지문, 전공 서적, 논문을 마스터하도록 돕는"
        f" 대한민국 최고의 AI 맞춤형 교육 멘토야. 현재 문서의 학문 분야는"
        f" **[{major_info}]**이며, 독자의 학업 레벨은 **[{user_level}]**"
        f" 단계야.\n\n아래 제시된 학년별 가이드라인을 100% 준수하여 두 가지"
        f" 결과물을 완벽하게 작성해줘:\n\n{level_instruction}\n\n1."
        " [자연스러운 수준별 의역]\n위 지침에 맞춰 문체와 부가설명 깊이를 정밀"
        " 조절한 한국어 해석본을 작성해줘.\n\n2. [필수 개인 맞춤형 단어장]\n본문에서"
        " 독자의 현재 학습 단계에 가장 치명적이고 중요한 어휘를 5개 이상 엄선하여"
        " [단어 - 뜻 - 맞춤형 가이드 해설] 형태로 요약 단어장을 만들어줘."
    )

    payload = {
        "model": "solar-pro",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"다음 영어 텍스트를 처리해줘:\n\n{english_text}",
            },
        ],
        "temperature": 0.2,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
      return response.json()["choices"][0]["message"]["content"]
    else:
      st.error(
          f"Solar LLM 서버 통신에 실패했습니다. (코드:"
          f" {response.status_code})"
      )
      return None
  except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    return None


# 📱 메인 UI
st.write("\n")
st.title("AI 학년별 맞춤 원서 번역기")
st.markdown(
    "<p class='sub-title'>고화질 스크린샷 무손실 우회 가동 모델</p>",
    unsafe_allow_html=True,
)

if UPSTAGE_API_KEY == "UPSTAGE_API_KEY" or not UPSTAGE_API_KEY:
  st.warning("⚠️ 코드 내 `UPSTAGE_API_KEY` 변수에 실제 키 값을 입력해 주세요.")
else:
  st.markdown("#### 🎓 1. 학습 환경 맞춤 설정")
  col_major, col_level = st.columns(2)

  with col_major:
    major_category = st.selectbox(
        "문서의 학문 분야를 지정하세요:",
        [
            "컴퓨터공학 / IT / AI",
            "의학 / 보건 / 바이오",
            "경영학 / 경제학",
            "자연과학 / 일반공학",
            "법학 / 행정학",
            "인문학 / 사회과학",
            "일반 수능 외국어 영역",
            "기타 (직접 입력)",
        ],
    )
  with col_level:
    user_level = st.selectbox(
        "현재 본인의 학업 단계를 선택하세요:",
        [
            "고등학교 1~2학년 (기초/내신)",
            "고등학교 3학년 (수능/심화입시)",
            "대학 신입생 / 입문자 (학부 1~2학년)",
            "학부 고학년 (학부 3~4학년)",
            "대학원생 / 연구원 (석박사 단계)",
        ],
        index=2,
    )

  if major_category == "기타 (직접 입력)":
    selected_major = st.text_input("학문 분야를 구체적으로 적어주세요:")
    selected_major = selected_major if selected_major else "일반 학술"
  else:
    selected_major = major_category

  st.write("\n")
  st.markdown("#### 📸 2. 원서 데이터 스캔")
  input_method = st.radio(
      "원서 입력 방식을 선택하세요:",
      ["카메라 촬영", "이미지 파일 업로드"],
      horizontal=True,
  )

  uploaded_file = None
  if input_method == "카메라 촬영":
    uploaded_file = st.camera_input(
        "책이나 시험지 문단을 카메라 정면에 맞춰서 찍어주세요"
    )
  else:
    uploaded_file = st.file_uploader(
        "분석할 이미지 파일을 선택하세요 (PNG, JPG, JPEG)",
        type=["png", "jpg", "jpeg"],
    )

  if uploaded_file is not None:
    image_bytes = preprocess_image(uploaded_file)

    if image_bytes is not None:
      st.write("\n")
      if input_method == "이미지 파일 업로드":
        st.image(image_bytes, use_container_width=True)
        st.write("\n")

      if st.button("🚀 개인 맞춤형 AI 독해 분석 시작", type="primary"):
        with st.spinner("Processing OCR (고화질 보정 스캔 중)..."):
          extracted_text = extract_text_from_image(image_bytes, UPSTAGE_API_KEY)

        if extracted_text:
          with st.expander("📝 추출된 영어 원문 데이터 확인"):
            st.text(extracted_text)

          with st.spinner(
              "Processing Solar AI (학년별 최적화 가이드 수립 중)..."
          ):
            ai_result = generate_translation_and_vocab(
                extracted_text, UPSTAGE_API_KEY, selected_major, user_level
            )

          if ai_result:
            st.markdown("---")
            st.markdown(f"### 🎯 개인 맞춤형 독해 리포트")
            st.caption(
                f"설정 타깃 도메인: {selected_major} | 선택된 독자 레벨:"
                f" {user_level}"
            )
            st.markdown(ai_result)

            st.download_button(
                label="💾 나만의 학습 리포트 다운로드 (.txt)",
                data=ai_result,
                file_name=f"AI_Study_Report_{user_level}.txt",
                mime="text/plain",
            )
