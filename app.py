import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# ==========================================
# 1. 페이지 레이아웃 및 테마 설정
# ==========================================
st.set_page_config(
    page_title="Alpha-16 v7.5 Institutional Terminal",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Alpha-16 v7.5 Institutional Platform")

# ==========================================
# 2. 사이드바 (API 설정 및 자금 관리 안내)
# ==========================================
with st.sidebar:
    st.header("⚙️ 환경 설정")
    gemini_key = st.text_input("Gemini API Key (무료)", type="password", help="Google AI Studio에서 무료 발급")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        st.success("AI 엔진 연동 완료")
    
    st.divider()
    st.markdown("### 🛡️ Alpha-16 자금 관리 3대 원칙")
    st.markdown("""
    - **Free-Ride**: +50% 시 30% 매도, +100% 시 원금 100% 회수
    - **하방 스탑**: 고점 -10%(30%), -20%(50%), -30%(전량 현금화)
    - **초기 손절**: -7%(50% 축소), -10%(전량 칼손절)
    """)

# ==========================================
# 3. 메인 종목 검색 영역
# ==========================================
col_search, col_btn = st.columns([4, 1])
with col_search:
    ticker_input = st.text_input("종목 티커 입력 (예: NVDA, AAPL, MSFT, 005930.KS, 000660.KS)", value="NVDA").strip().upper()
with col_btn:
    st.write("")
    st.write("")
    run_search = st.button("🔍 데이터 로드", use_container_width=True)

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        
        # 실시간성 데이터 추출
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        high_52 = info.get("fiftyTwoWeekHigh", current_price)
        low_52 = info.get("fiftyTwoWeekLow", current_price)
        drawdown = ((current_price - high_52) / high_52 * 100) if high_52 else 0
        is_kr = "KS" in ticker_input or "KQ" in ticker_input
        currency_symbol = "원" if is_kr else "$"

        # 4대 탭 네비게이션
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 [Step 0~8] Alpha-16 분석", 
            "⚖️ 종목 교차 비교 (Compare)", 
            "📑 전체 재무제표", 
            "🛡️ 3단계 스탑 & 슬롯 관리"
        ])

        # ----------------------------------------------------
        # TAB 1: Alpha-16 9단계 마스터 파이프라인
        # ----------------------------------------------------
        with tab1:
            st.markdown(f"### 📌 [Step 0] 팩트 데이터 교차 검증: {info.get('shortName', ticker_input)}")
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("현재 기준가", f"{currency_symbol}{current_price:,.2f}" if not is_kr else f"{current_price:,.0f}원")
            m2.metric("52주 고점 대비", f"{drawdown:.2f}%", delta=f"{drawdown:.2f}%")
            m3.metric("52주 최고/최저", f"{high_52:,.0f} / {low_52:,.0f}")
            m4.metric("PER (Trailing)", f"{info.get('trailingPE', 'N/A')}")
            m5.metric("PBR", f"{info.get('priceToBook', 'N/A')}")
            m6.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A")

            st.divider()

            if gemini_key:
                if st.button("🚀 Alpha-16 v7.5 9단계 전체 리포트 생성", use_container_width=True):
                    with st.spinner("Step 0부터 Step 8까지 정밀 분석 중..."):
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        prompt = f"""
                        너는 기업 펀더멘털 분석 및 기계적 자금 관리 시스템인 'Alpha-16 v7.5' 전문 분석가다.
                        내가 지정한 아래 9단계 파이프라인(Step 0 ~ Step 8)을 단 한 단계도 축약하거나 생략하지 말고 모두 온전히 전개해라.

                        [분석 대상 기업 팩트]
                        - 종목명/티커: {ticker_input} ({info.get('shortName', '')})
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
                st.info("💡 사이드바에 무료 Gemini API Key를 입력하면 9단계 리포트가 자동으로 생성됩니다.")

        # ----------------------------------------------------
        # TAB 2: Compare Matrix (멀티 종목 비교)
        # ----------------------------------------------------
        with tab2:
            st.markdown("### ⚖️ 피어 그룹(Peer Group) 밸류에이션 및 재무 건전성 비교")
            default_peers = "NVDA, AMD, INTC, TSM" if "NVDA" in ticker_input else f"{ticker_input}, AAPL, MSFT"
            peers_input = st.text_input("비교할 티커들을 쉼표(,)로 구분해 입력하세요", value=default_peers)
            
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
                            "Forward PER": p_info.get("forwardPE", "N/A"),
                            "PBR": p_info.get("priceToBook", "N/A"),
                            "ROE(%)": f"{p_info.get('returnOnEquity', 0)*100:.2f}%" if p_info.get('returnOnEquity') else "N/A",
                            "영업이익률(OPM)": f"{p_info.get('operatingMargins', 0)*100:.2f}%" if p_info.get('operatingMargins') else "N/A",
                            "시가총액": f"${p_info.get('marketCap', 0):,}" if p_info.get('marketCap') else "N/A"
                        })
                    except:
                        pass
                
                if comp_data:
                    st.dataframe(pd.DataFrame(comp_data).set_index("티커"), use_container_width=True)

        # ----------------------------------------------------
        # TAB 3: Financial Statements (전체 재무제표)
        # ----------------------------------------------------
        with tab3:
            st.markdown("### 📑 전체 재무제표 원문 (Income Statement / Balance Sheet / Cash Flow)")
            stmt_choice = st.radio("표시할 재무제표", ["손익계산서", "대차대조표", "현금흐름표"], horizontal=True)
            
            if stmt_choice == "손익계산서":
                st.dataframe(stock.financials, use_container_width=True)
            elif stmt_choice == "대차대조표":
                st.dataframe(stock.balance_sheet, use_container_width=True)
            else:
                st.dataframe(stock.cashflow, use_container_width=True)

        # ----------------------------------------------------
        # TAB 4: Portfolio & Dynamic Stop Tracker
        # ----------------------------------------------------
        with tab4:
            st.markdown("### 🛡️ [Step 5] 기계적 자금 관리 & 트레일링 스탑 계산기")
            
            c1, c2 = st.columns(2)
            with c1:
                my_buy_price = st.number_input("내 매수 단가", value=float(current_price))
            with c2:
                my_peak_price = st.number_input("매수 이후 형성된 최고가", value=float(max(current_price, my_buy_price)))

            st.markdown("#### 🚨 하방 3단계 트레일링 스탑 가격표")
            s1, s2, s3 = st.columns(3)
            s1.error(f"**1차 스탑 (-10%)**\n\n- 가격: **{currency_symbol}{my_peak_price * 0.90:,.2f}**\n- 액션: **30% 분할 익절**")
            s2.error(f"**2차 스탑 (-20%)**\n\n- 가격: **{currency_symbol}{my_peak_price * 0.80:,.2f}**\n- 액션: **50% 추가 익절**")
            s3.error(f"**3차 스탑 (-30%)**\n\n- 가격: **{currency_symbol}{my_peak_price * 0.70:,.2f}**\n- 액션: **전량 청산 (현금 100%)**")

            st.markdown("#### 💎 Free-Ride 상방 원금 회수 기준선")
            f1, f2 = st.columns(2)
            f1.success(f"**+50% 도달**: {currency_symbol}{my_buy_price * 1.50:,.2f} (보유 비중 30% 매도하여 원금 45% 확보)")
            f2.success(f"**+100% 도달**: {currency_symbol}{my_buy_price * 2.00:,.2f} (추가 분할 매도로 원금 100% 전액 회수)")

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")