import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="간식비 자동 정산기", layout="centered")
st.title("🛒 간식비 자동 정산 시스템")
st.write("바쁜 교대 근무 속 간식비 정산, 이제 AI가 5초 만에 끝내드립니다.")

# 1. API 키 입력 영역
api_key = st.sidebar.text_input("Gemini API 키 입력", type="password")

# 2. 이미지 업로드 영역
col1, col2 = st.columns(2)
with col1:
    uploaded_memo = st.file_uploader("수기 주문 전표 업로드", type=["png", "jpg", "jpeg"])
with col2:
    uploaded_receipt = st.file_uploader("결제 영수증 업로드", type=["png", "jpg", "jpeg"])

# 3. AI 분석 프롬프트 (명령어) 세팅
system_prompt = """
당신은 병동 간식비 정산 전문가입니다. 
제공된 이미지 1(수기 주문 전표)과 이미지 2(결제 영수증)를 대조하여 환자/직원별 정산 내역을 산출하세요.

[정산 규칙]
1. 수기 전표에서 취소선이 그어진 품목은 주문에서 제외합니다.
2. 영수증에 표기된 품목명과 전표의 약칭(예: 오렌지쥬스P, 바우 등)을 문맥상 동일한 것으로 유연하게 매칭하세요.
3. 매칭된 단가를 적용하여 인당 총 청구 금액을 계산하세요.

[출력 형식]
반드시 아래 마크다운 표 형식으로만 출력하세요.
| 이름 | 주문 품목 및 영수증 단가(원) | 청구 금액 |
"""

# 4. 정산 실행 버튼 및 AI 통신 로직
if st.button("정산 시작하기", use_container_width=True):
    if not api_key:
        st.warning("좌측 사이드바에 API 키를 입력해 주세요.")
    elif not uploaded_memo or not uploaded_receipt:
        st.warning("전표와 영수증 이미지를 모두 업로드해 주세요.")
    else:
        try:
            # AI 모델 초기화
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 이미지 열기
            memo_img = Image.open(uploaded_memo)
            receipt_img = Image.open(uploaded_receipt)
            
            with st.spinner("AI가 이미지를 분석하고 정산 중입니다... (약 10~20초 소요)"):
                # AI에게 프롬프트와 두 장의 이미지 전송
                response = model.generate_content([system_prompt, memo_img, receipt_img])
                
                st.success("정산이 완료되었습니다!")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다. API 키가 정확한지 확인해 주세요.\n상세 에러: {e}")