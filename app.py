import streamlit as st
import yfinance as yf
import google.generativeai as genai

# 모바일 퍼스트 뷰 설정
st.set_page_config(page_title="Alpha-16 Master Terminal", page_icon="🏛️", layout="centered")

# 세련된 모바일 카드 UI 스타일 적용
st.markdown("""
<style>
    .block-container { max-width: 500px !important; padding: 1.5rem 1rem !important; }
    .header-card { background: #0f172a; color: white; padding: 1.25rem; border-radius: 1.25rem; margin-bottom: 1rem; }
    .badge { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; }
    .metric-container { background: #1e293b; border-radius: 0.875rem; padding: 0.75rem; margin-top: 0.75rem; border: 1px solid #334155; }
    .stButton>button { width: 100%; border-radius: 0.75rem; background-color: #2563eb; color: white; font-weight: bold; padding: 0.5rem; border: none; }
    .stButton>button:hover { background-color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

# 1. API 키 연동 (Secrets 또는 사이드바)
api_key = st.secrets.get("GEMINI_API_KEY", "")
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("🟢 AI 엔진 실시간 연동 완료")

# 2. 상단 헤더 & 티커 매핑
st.markdown("""
<div class="header-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 1.1rem; font-weight: bold;">🏛️ Alpha-16 v7.5 Live</div>
        <span class="badge">● 실시간 최신 연동</span>
    </div>
</div>
""", unsafe_allow_html=True)

STOCK_MAP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "엔비디아 (NVDA)": "NVDA",
    "TSMC (TSM)": "TSM",
    "애플 (AAPL)": "AAPL",
    "직접 티커 입력": "CUSTOM"
}

selected = st.selectbox("🔍 종목 선택", list(STOCK_MAP.keys()), index=0)
ticker = STOCK_MAP[selected]

if ticker == "CUSTOM":
    ticker = st.text_input("티커 입력 (예: 005930.KS, NVDA, TSLA)", value="NVDA").strip().upper()

# 3. 실시간 데이터 팩트 추출 & 9단계 리포트 생성
if ticker and ticker != "CUSTOM" and api_key:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 실시간 데이터 추출
        curr_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        high_52 = info.get("fiftyTwoWeekHigh", curr_price)
        low_52 = info.get("fiftyTwoWeekLow", curr_price)
        drawdown = ((curr_price - high_52) / high_52 * 100) if high_52 else 0
        pe = info.get("trailingPE", "N/A")
        pbr = info.get("priceToBook", "N/A")
        roe = f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A"
        opm = f"{info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "N/A"
        is_kr = "KS" in ticker or "KQ" in ticker
        curr_unit = "원" if is_kr else "$"

        # 실시간 팩트 요약 카드
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 1rem; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-weight: bold; font-size: 0.95rem; margin-bottom: 0.5rem;">📌 [Step 0] 실시간 팩트 데이터: {info.get('shortName', ticker)}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.8rem; color: #475569;">
                <div>현재가: <b style="color: #0f172a;">{curr_unit}{curr_price:,.2f}</b></div>
                <div>고점대비: <b style="color: #e11d48;">{drawdown:.2f}%</b></div>
                <div>52주 최고/저: <b>{high_52:,.0f} / {low_52:,.0f}</b></div>
                <div>PER / PBR: <b>{pe} / {pbr}</b></div>
                <div>ROE: <b>{roe}</b></div>
                <div>영업이익률: <b>{opm}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Alpha-16 v7.5 정규 마스터 리포트 생성", use_container_width=True):
            with st.spinner("최신 실시간 팩트를 기반으로 9단계 파이프라인 연산 중..."):
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # 실시간 최신 수치를 모델에 직접 강제 주입
                prompt = f"""
                너는 기업 펀더멘털 분석 및 기계적 자금 관리 시스템인 'Alpha-16 v7.5' 전문 분석가다.
                내가 아래에 제공하는 [100% 최신 실시간 팩트 데이터]를 기준으로 [Step 0]부터 [Step 8]까지 단 한 단계도 생략하지 말고 온전히 전개하라.

                [100% 최신 실시간 팩트 데이터]
                - 종목명/티커: {ticker} ({info.get('shortName', '')})
                - 실시간 현재가: {curr_price}, 52주 고점: {high_52}, 저점: {low_52}, 고점대비 하락률: {drawdown:.2f}%
                - PER: {pe}, PBR: {pbr}, ROE: {roe}, 영업이익률(OPM): {opm}
                - 최근 매출: {info.get('totalRevenue')}, 순이익: {info.get('netIncomeToCommon')}

                ======================================================================
                [Alpha-16 v7.5 정규 마스터 파이프라인 규격]
                [Step 0] 실시간 다중 채널 교차 검증 (위 팩트 데이터 기반 완벽 기재)
                [Step 0.5] 산업 존재 이유 & 숨겨진 본질적 해자 심층 분석 (절대적 병목 Chokepoint, 고정비 레버리지, LTA 수주형 전환, 피지컬 AI TAM)
                [Step 0.8] 거시경제·정치·지정학적 리스크 및 포트폴리오 헷지 분석 (미중 갈등, 금리/CAPEX 피로도, 3중 방어 헷지)
                [Step 1] 4대 축 16개 핵심 팩터 정밀 평가 (80점 만점 컴팩트 매트릭스, 총점 및 등급)
                [Step 2] 비선형 퀀텀점프 3대 게이트 (Gate 1~3 Pass/Fail)
                [Step 3] 포트폴리오 5대 슬롯 자산배분 & 가변 스탑 판정 (Slot 1~5)
                [Step 4] 시나리오별 3대 적정 가치 밴드 (Bull / Base / Bear)
                [Step 5] 실전 매매 프로토콜 (Free-Ride선 및 -10%/-20%/-30% 기계적 스탑선)
                [Step 6] 손절/청산 후 뇌동매매 차단 재진입 게이트 (Gate R-1 ~ R-3)
                [Step 7] 정밀 백테스팅 검증
                [Step 8] 최종 투자 결론 및 실전 행동 지침 (종합 등급, 즉각 실행 액션, 상방 목표가, One-Line Verdict)
                ======================================================================
                모바일에서 읽기 편하도록 명확하게 작성하라.
                """
                
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"실시간 데이터 수신 오류: {e}")