import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="간식비 자동 정산기", layout="centered")
st.title("🛒 간식비 자동 정산 시스템")
st.write("바쁜 별관병동 업무, 간식비 정산은 AI에게 맡기세요!")

# 1. 비밀 금고에서 API 키 자동으로 꺼내오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("스트림릿 설정(Secrets)에 API 키가 없습니다! 세팅을 먼저 해주세요.")
    st.stop()

# 2. 이미지 업로드 영역
st.header("1. 전표 및 영수증 업로드")
col1, col2 = st.columns(2)
with col1:
    uploaded_memo = st.file_uploader("수기 주문 전표", type=["png", "jpg", "jpeg"])
with col2:
    uploaded_receipt = st.file_uploader("결제 영수증", type=["png", "jpg", "jpeg"])

# 3. AI 분석 프롬프트 세팅
system_prompt = """
당신은 병동 간식비 정산 전문가입니다. 
이미지 1(수기 주문 전표)과 이미지 2(결제 영수증)를 대조하여 환자/직원별 정산 내역을 산출하세요.

[정산 규칙]
1. 수기 전표에서 취소선이 그어진 품목은 주문에서 제외합니다.
2. 영수증에 표기된 품목명과 전표의 약칭(예: 오렌지쥬스P, 바우 등)을 문맥상 동일한 것으로 유연하게 매칭하세요.
3. 매칭된 단가를 적용하여 인당 총 청구 금액을 계산하세요.

[출력 형식]
반드시 아래 마크다운 표 형식으로만 출력하세요.
| 이름 | 주문 품목 및 영수증 단가(원) | 청구 금액 |
"""

# 4. 정산 실행 버튼 및 통신 로직
if st.button("정산 시작하기", use_container_width=True):
    if not uploaded_memo or not uploaded_receipt:
        st.warning("전표와 영수증 이미지를 모두 업로드해 주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            memo_img = Image.open(uploaded_memo)
            receipt_img = Image.open(uploaded_receipt)
            
            with st.spinner("AI가 이미지를 분석하고 정산 중입니다... (약 10~20초 소요)"):
                response = model.generate_content([system_prompt, memo_img, receipt_img])
                st.success("정산 완료!")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다.\n상세 에러: {e}")
