import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# ==========================================
# 1. 테마 & 시인성 설정
# ==========================================
st.set_page_config(page_title="Alpha-16 v7.5 Terminal", page_icon="🏛️", layout="wide")
st.title("🏛️ Alpha-16 v7.5 Institutional Platform")

# ==========================================
# 2. API Key 영구 자동 연동 (Secrets)
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 시스템 상태")
    if not api_key:
        api_key = st.text_input("Gemini API Key 입력 (임시)", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
        st.success("🟢 AI 분석 엔진 상시 가동 중")
    else:
        st.warning("⚠️ Secrets 또는 여기에 API 키를 입력하세요.")

    st.divider()
    st.markdown("### 🛡️ Alpha-16 자금 관리 3대 원칙")
    st.markdown("""
    - **Free-Ride**: +50% 시 30% 매도, +100% 시 원금 100% 회수
    - **하방 스탑**: 고점 -10%(30%), -20%(50%), -30%(전량 현금화)
    - **초기 손절**: -7%(50% 축소), -10%(전량 칼손절)
    """)

# ==========================================
# 3. 한글/영문 스마트 검색 및 자동완성 사전
# ==========================================
STOCK_DICT = {
    # 주요 글로벌 빅테크 & 반도체
    "엔비디아 (NVDA)": "NVDA",
    "TSMC (TSM)": "TSM",
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "알파벳/구글 (GOOGL)": "GOOGL",
    "아마존 (AMZN)": "AMZN",
    "메타 (META)": "META",
    "테슬라 (TSLA)": "TSLA",
    "ASML (ASML)": "ASML",
    "브로드컴 (AVGO)": "AVGO",
    "AMD (AMD)": "AMD",
    "인텔 (INTC)": "INTC",
    "퀄컴 (QCOM)": "QCOM",
    "암 홀딩스 (ARM)": "ARM",
    
    # 국내 대표 코스피 / 코스닥
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "현대차 (005380.KS)": "005380.KS",
    "기아 (000270.KS)": "000270.KS",
    "LG에너지솔루션 (373220.KS)": "373220.KS",
    "삼성바이오로직스 (207940.KS)": "207940.KS",
    "셀트리온 (068270.KS)": "068270.KS",
    "알테오젠 (196170.KQ)": "196170.KQ",
    "에코프로비엠 (247540.KQ)": "247540.KQ",
    "한미반도체 (042700.KS)": "042700.KS",
    "NAVER (035420.KS)": "035420.KS",
    "카카오 (035720.KS)": "035720.KS",
    "직접 티커 입력": "CUSTOM"
}

col_search, col_custom = st.columns([3, 2])
with col_search:
    selected_name = st.selectbox("🔍 종목 선택 (한글명 / 영문명 검색 가능)", list(STOCK_DICT.keys()), index=0)

target_ticker = STOCK_DICT[selected_name]

if target_ticker == "CUSTOM":
    with col_custom:
        target_ticker = st.text_input("직접 티커 입력 (예: PLTR, 005930.KS)", value="PLTR").strip().upper()
else:
    with col_custom:
        st.text_input("선택된 티커", value=target_ticker, disabled=True)

# ==========================================
# 4. 데이터 패칭 & 대시보드 렌더링
# ==========================================
if target_ticker and target_ticker != "CUSTOM":
    try:
        stock = yf.Ticker(target_ticker)
        info = stock.info
        
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        high_52 = info.get("fiftyTwoWeekHigh", current_price)
        low_52 = info.get("fiftyTwoWeekLow", current_price)
        drawdown = ((current_price - high_52) / high_52 * 100) if high_52 else 0
        is_kr = "KS" in target_ticker or "KQ" in target_ticker
        curr = "원" if is_kr else "$"

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 [Step 0~8] Alpha-16 마스터 리포트", 
            "⚖️ 종목 교차 비교 (Compare)", 
            "📑 전체 재무제표", 
            "🛡️ 3단계 스탑 & 슬롯 관리"
        ])

        # ----------------------------------------------------
        # TAB 1: Alpha-16 9단계 마스터 파이프라인
        # ----------------------------------------------------
        with tab1:
            st.markdown(f"### 📌 [Step 0] 팩트 데이터 교차 검증: {info.get('shortName', target_ticker)}")
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("현재 기준가", f"{curr}{current_price:,.2f}" if not is_kr else f"{current_price:,.0f}원")
            m2.metric("52주 고점 대비", f"{drawdown:.2f}%", delta=f"{drawdown:.2f}%")
            m3.metric("52주 최고/최저", f"{high_52:,.0f} / {low_52:,.0f}")
            m4.metric("PER (Trailing)", f"{info.get('trailingPE', 'N/A')}")
            m5.metric("PBR", f"{info.get('priceToBook', 'N/A')}")
            m6.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A")

            st.divider()

            if api_key:
                if st.button("🚀 Alpha-16 v7.5 9단계 전체 리포트 생성", use_container_width=True):
                    with st.spinner("Step 0부터 Step 8까지 파이프라인 전개 중..."):
                        # 모델 Fallback 처리 (최신 모델 자동 감지)
                        for model_name in ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]:
                            try:
                                model = genai.GenerativeModel(model_name)
                                break
                            except:
                                continue

                        prompt = f"""
                        너는 기업 펀더멘털 분석 및 기계적 자금 관리 시스템인 'Alpha-16 v7.5' 전문 분석가다.
                        내가 지정한 아래 9단계 파이프라인(Step 0 ~ Step 8)을 단 한 단계도 축약하거나 생략하지 말고 모두 온전히 전개해라.

                        [분석 대상 기업 팩트]
                        - 종목명/티커: {target_ticker} ({info.get('shortName', '')})
                        - 현재가: {current_price}, 52주 고점: {high_52}, 저점: {low_52}, 고점대비: {drawdown:.2f}%
                        - PER: {info.get('trailingPE')}, PBR: {info.get('priceToBook')}, ROE: {info.get('returnOnEquity')}
                        - 매출: {info.get('totalRevenue')}, 영업이익률: {info.get('operatingMargins')}

                        ======================================================================
                        [Alpha-16 v7.5 정규 마스터 파이프라인 규격에 맞춰 상세히 작성할 것]
                        [Step 0] 실시간 다중 채널 교차 검증
                        [Step 0.5] 산업의 존재 이유 & 숨겨진 본질적 해자 심층 분석
                        [Step 0.8] 거시경제·정치·지정학적 리스크 및 포트폴리오 헷지 분석
                        [Step 1] 4대 축 16개 핵심 팩터 정밀 평가 (80점 만점 컴팩트 매트릭스)
                        [Step 2] 비선형 퀀텀점프 3대 게이트 (Gate 1~3) 심사
                        [Step 3] 포트폴리오 5대 슬롯 자산배분 & 가변 스탑 판정
                        [Step 4] 시나리오별 3대 적정 가치 밴드 (Bull/Base/Bear)
                        [Step 5] 실전 매매 프로토콜 (Free-Ride & 3단계 트레일링 스탑)
                        [Step 6] 손절/청산 후 뇌동매매 차단 재진입 게이트 (Gate R-1 ~ R-3)
                        [Step 7] 정밀 백테스팅 검증
                        [Step 8] 최종 투자 결론 및 실전 행동 지침
                        ======================================================================
                        """
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
            else:
                st.info("💡 사이드바 또는 Secrets에 Gemini API Key를 설정해주세요.")

        # ----------------------------------------------------
        # TAB 2: Compare Matrix (종목 비교)
        # ----------------------------------------------------
        with tab2:
            st.markdown("### ⚖️ 동종업계 피어 그룹 밸류에이션 비교")
            default_peers = "NVDA, AMD, TSM, INTC" if "NVDA" in target_ticker or "TSM" in target_ticker else f"{target_ticker}, AAPL, MSFT"
            peers_input = st.text_input("비교할 티커 목록 (쉼표 구분)", value=default_peers)
            
            if peers_input:
                peer_list = [p.strip().upper() for p in peers_input.split(",") if p.strip()]
                comp_data = []
                for p in peer_list:
                    try:
                        p_info = yf.Ticker(p).info
                        comp_data.append({
                            "티커": p,
                            "기업명": p_info.get("shortName", p),
                            "현재가": p_info.get("currentPrice", p_info.get("regularMarketPrice", "N/A")),
                            "PER": p_info.get("trailingPE", "N/A"),
                            "PBR": p_info.get("priceToBook", "N/A"),
                            "ROE(%)": f"{p_info.get('returnOnEquity', 0)*100:.2f}%" if p_info.get('returnOnEquity') else "N/A",
                            "영업이익률": f"{p_info.get('operatingMargins', 0)*100:.2f}%" if p_info.get('operatingMargins') else "N/A",
                        })
                    except:
                        pass
                if comp_data:
                    st.dataframe(pd.DataFrame(comp_data).set_index("티커"), use_container_width=True)

        # ----------------------------------------------------
        # TAB 3: Financials (재무제표)
        # ----------------------------------------------------
        with tab3:
            st.markdown("### 📑 전체 재무제표 원문")
            stmt_choice = st.radio("재무제표 선택", ["손익계산서", "대차대조표", "현금흐름표"], horizontal=True)
            if stmt_choice == "손익계산서":
                st.dataframe(stock.financials, use_container_width=True)
            elif stmt_choice == "대차대조표":
                st.dataframe(stock.balance_sheet, use_container_width=True)
            else:
                st.dataframe(stock.cashflow, use_container_width=True)

        # ----------------------------------------------------
        # TAB 4: Dynamic Stop Calculator
        # ----------------------------------------------------
        with tab4:
            st.markdown("### 🛡️ [Step 5] 기계적 자금 관리 & 트레일링 스탑 계산기")
            c1, c2 = st.columns(2)
            with c1:
                my_buy_price = st.number_input("내 매수 단가", value=float(current_price))
            with c2:
                my_peak_price = st.number_input("매수 이후 형성된 최고가", value=float(max(current_price, my_buy_price)))

            s1, s2, s3 = st.columns(3)
            s1.error(f"**1차 스탑 (-10%)**\n\n- 가격: **{curr}{my_peak_price * 0.90:,.2f}**\n- 액션: **30% 분할 익절**")
            s2.error(f"**2차 스탑 (-20%)**\n\n- 가격: **{curr}{my_peak_price * 0.80:,.2f}**\n- 액션: **50% 추가 익절**")
            s3.error(f"**3차 스탑 (-30%)**\n\n- 가격: **{curr}{my_peak_price * 0.70:,.2f}**\n- 액션: **전량 청산 (현금화)**")

    except Exception as e:
        st.error(f"데이터 조회 중 오류: {e}")