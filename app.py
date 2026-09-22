import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="간식비 자동 정산기", layout="centered")
st.title("🛒 간식비 자동 정산 시스템 (정신과 병동용)")
st.write("복잡한 환자 간식비 정산, AI가 빠르게 처리해 드립니다.")

# 1. API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("스트림릿 설정(Secrets)에 API 키가 없습니다.")
    st.stop()

# 2. 이미지 업로드 영역
st.header("1. 전표 및 영수증 업로드")
col1, col2 = st.columns(2)
with col1:
    uploaded_memo = st.file_uploader("환자 수기 전표", type=["png", "jpg", "jpeg"])
with col2:
    uploaded_receipt = st.file_uploader("결제 영수증", type=["png", "jpg", "jpeg"])

# 3. 정신과 병동 전용 프롬프트
system_prompt = """
당신은 정신과 병동의 환자 간식비 정산 전문가입니다. 
이미지 1(환자들의 수기 주문 전표)과 이미지 2(결제 영수증)를 대조하여 각 환자별 청구 금액을 산출하세요.

[절대 규칙]
1. 전표에 적힌 내역은 100% '환자'들의 간식 주문입니다. 직원용은 일절 없으므로 분류하려 하지 말고 모두 환자 기준으로 정산하세요.
2. 수기 전표에 악필로 적힌 환자명(또는 병상 번호)과 품목 약칭(예: 바우, 초코 등)을 영수증의 정식 품목명과 문맥상 유연하게 매칭하세요.
3. 수기 전표에서 취소선이 그어진 품목은 주문이 취소된 것이므로 정산에서 제외합니다.

[출력 형식]
반드시 아래 마크다운 표 형식으로만 깔끔하게 출력하세요.
| 환자명(병상) | 주문 품목 및 영수증 단가(원) | 총 청구 금액 |
"""

# 4. 정산 실행 로직
if st.button("정산 시작하기", use_container_width=True):
    if not uploaded_memo or not uploaded_receipt:
        st.warning("전표와 영수증 이미지를 모두 업로드해 주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.6-flash')
            
            with st.spinner("AI가 전표와 영수증을 대조 중입니다 (약 20~30초 소요)..."):
                # 내장 썸네일 기능으로 서버 과부하 없이 비율 유지하며 안전하게 축소
                memo_img = Image.open(uploaded_memo)
                memo_img.thumbnail((800, 800))
                
                receipt_img = Image.open(uploaded_receipt)
                receipt_img.thumbnail((800, 800))
                
                # 텍스트 대신 다시 원래대로 프롬프트와 안전해진 이미지 2장을 전송
                response = model.generate_content([system_prompt, memo_img, receipt_img])
                
                st.success("정산 완료!")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다.\n상세 에러: {e}")
