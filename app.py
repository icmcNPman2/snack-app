import streamlit as st
import requests
import base64
import io
from PIL import Image

st.set_page_config(page_title="간식비 자동 정산기", layout="centered")
st.title("🛒 간식비 자동 정산 시스템 (정신과 병동용)")
st.write("복잡한 환자 간식비 정산, AI가 빠르게 처리해 드립니다.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("스트림릿 설정(Secrets)에 API 키가 없습니다.")
    st.stop()

st.header("1. 전표 및 영수증 업로드")
col1, col2 = st.columns(2)
with col1:
    uploaded_memo = st.file_uploader("환자 수기 전표", type=["png", "jpg", "jpeg"])
with col2:
    uploaded_receipt = st.file_uploader("결제 영수증", type=["png", "jpg", "jpeg"])

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

# --- 새로고침 시 API 중복 호출을 막는 방어막(금고) 세팅 ---
if 'final_result' not in st.session_state:
    st.session_state.final_result = None

# 5. 정산 실행 로직 (직통 API 통신)
if st.button("정산 시작하기", use_container_width=True):
    if not uploaded_memo or not uploaded_receipt:
        st.warning("전표와 영수증 이미지를 모두 업로드해 주세요.")
    else:
        with st.spinner("구글 라이브러리를 거치지 않고 직통망으로 정산 중입니다... (최대 60초)"):
            try:
                # 1. 이미지를 가볍게 압축하고 텍스트(Base64)로 완벽히 변환
                def encode_image(upload):
                    img = Image.open(upload).convert('RGB')
                    img.thumbnail((800, 800))
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG")
                    return base64.b64encode(buffer.getvalue()).decode('utf-8')

                memo_b64 = encode_image(uploaded_memo)
                receipt_b64 = encode_image(uploaded_receipt)

                # 2. [수정 완료] URL을 강력한 3.6-flash 버전으로 변경
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"

                # 3. 전송할 데이터 조립
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": system_prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": memo_b64}},
                            {"inline_data": {"mime_type": "image/jpeg", "data": receipt_b64}}
                        ]
                    }]
                }

                # 4. 직통으로 쏘기 (60초 넘어가면 칼같이 강제 종료)
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    # 통신 성공 시, 결과를 바로 화면에 뿌리지 않고 방어막 금고에 먼저 저장
                    st.session_state.final_result = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("정산 완료!")
                else:
                    st.error(f"서버가 에러를 뱉었습니다 (코드 {response.status_code}):\n{response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("통신 시간이 60초를 초과하여 강제 종료되었습니다. 사진이 너무 복잡하거나 구글 서버가 지연되고 있습니다.")
            except Exception as e:
                st.error(f"오류가 발생했습니다.\n상세 에러: {e}")

# 5. 금고에 정산 표가 들어있다면, 화면이 새로고침 되어도 API 호출 없이 꺼내서 보여줌
if st.session_state.final_result:
    st.markdown(st.session_state.final_result)
