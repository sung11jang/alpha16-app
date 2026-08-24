import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import requests
import re

# ==============================================================================
# 1. 페이지 레이아웃 및 한글 UI 스타일 설정
# ==============================================================================
st.set_page_config(
    page_title="Alpha-16 v7.5 기관용 터미널",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title { font-size: 2.1rem; font-weight: 800; color: #0f172a; margin-bottom: 0.2rem; }
    .sub-title { font-size: 0.95rem; color: #64748b; margin-bottom: 1.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; white-space: pre-wrap; background-color: #f1f5f9;
        border-radius: 8px 8px 0px 0px; padding: 10px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #2563eb !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ Alpha-16 v7.5 기관용 퀀트 터미널</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">미국 S&P 500 (1~500위) · 코스피 500위 · 코스닥 300위 통합 마스터 플랫폼</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. 재무제표 표준 한글 계정과목 매핑 및 쉼표 포맷팅
# ==============================================================================
KOR_FINANCIAL_MAP = {
    # 손익계산서
    "Total Revenue": "매출액",
    "Operating Revenue": "영업수익",
    "Cost Of Revenue": "매출원가",
    "Gross Profit": "매출총이익",
    "Operating Expense": "영업비용",
    "Selling General And Administration": "판관비 (판매비와 관리비)",
    "Research And Development": "연구개발비 (R&D)",
    "Operating Income": "영업이익",
    "Net Non Operating Interest Income Expense": "이자수익/비용 (순)",
    "Other Income Expense": "기타영업외손익",
    "Pretax Income": "법인세차감전순이익",
    "Tax Provision": "법인세비용",
    "Net Income Common Stockholders": "당기순이익 (지배주주)",
    "Net Income": "당기순이익",
    "Basic EPS": "기본 주당순이익 (EPS)",
    "Diluted EPS": "희석 주당순이익 (EPS)",
    "EBITDA": "EBITDA (이자·세금·감가상각비 차감전이익)",
    "EBIT": "EBIT (영업이익)",

    # 대차대조표
    "Total Assets": "자산총계",
    "Current Assets": "유동자산",
    "Cash And Cash Equivalents": "현금 및 현금성자산",
    "Other Short Term Investments": "단기금융상품 (단기투자자산)",
    "Cash Cash Equivalents And Short Term Investments": "총 현금성 자산 (현금+단기투자)",
    "Receivables": "매출채권 및 미수금",
    "Inventory": "재고자산",
    "Other Current Assets": "기타유동자산",
    "Total Non Current Assets": "비유동자산 (고정자산)",
    "Net PPE": "유형자산 (설비·기계·부동산)",
    "Goodwill": "영업권 (Goodwill)",
    "Other Intangible Assets": "무형자산",
    "Investments And Advances": "장기투자자산",
    "Total Liabilities Net Minority Interest": "부채총계",
    "Current Liabilities": "유동부채 (1년 이내 상환)",
    "Current Debt": "단기차입금",
    "Accounts Payable": "매입채무",
    "Total Non Current Liabilities Net Minority Interest": "비유동부채 (장기부채)",
    "Long Term Debt": "장기차입금 (회사채)",
    "Stockholders Equity": "자기자본 총계 (순자산)",
    "Common Stock Equity": "보통주 자본금",
    "Retained Earnings": "이익잉여금",
    "Treasury Stock": "자사주 (취득액)",

    # 현금흐름표
    "Operating Cash Flow": "영업활동 현금흐름 (OCF)",
    "Investing Cash Flow": "투자활동 현금흐름",
    "Financing Cash Flow": "재무활동 현금흐름",
    "Capital Expenditure": "설비투자 (CAPEX)",
    "Free Cash Flow": "잉여현금흐름 (FCF)",
    "End Cash Position": "기말 현금 잔액",
    "Beginning Cash Position": "기초 현금 잔액",
    "Cash Dividends Paid": "배당금 지급액",
    "Repurchase Of Capital Stock": "자사주 매입/소각액"
}

def format_currency_df(df, is_kr):
    if df is None or df.empty:
        return df
    new_df = df.copy()
    new_df.index = [KOR_FINANCIAL_MAP.get(str(idx), str(idx)) for idx in new_df.index]
    
    for col in new_df.columns:
        new_df[col] = new_df[col].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else x)
    return new_df

# ==============================================================================
# 3. 미국 500위 / 코스피 500위 / 코스닥 300위 자동 캐싱 로더 (1,300여 개)
# ==============================================================================
@st.cache_data(ttl=86400)
def load_all_market_stocks():
    stock_dict = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 1. 미국 S&P 500 전 종목 (1위 ~ 500위)
    try:
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(requests.get(sp500_url, headers=headers, timeout=5).text)
        sp_df = tables[0]
        for _, row in sp_df.iterrows():
            sym = str(row['Symbol']).replace('.', '-')
            sec_name = str(row['Security'])
            label = f"[미국 S&P 500] {sec_name} ({sym})"
            stock_dict[label] = sym
    except Exception:
        fallback_us = {
            "[미국 S&P 500] 엔비디아 (NVDA)": "NVDA", "[미국 S&P 500] 애플 (AAPL)": "AAPL",
            "[미국 S&P 500] 마이크로소프트 (MSFT)": "MSFT", "[미국 S&P 500] 알파벳/구글 (GOOGL)": "GOOGL",
            "[미국 S&P 500] 아마존 (AMZN)": "AMZN", "[미국 S&P 500] 메타 (META)": "META",
            "[미국 S&P 500] 테슬라 (TSLA)": "TSLA", "[미국 S&P 500] 브로드컴 (AVGO)": "AVGO"
        }
        stock_dict.update(fallback_us)

    # 2. 국내 코스피 상위 500위 (10페이지) + 코스닥 상위 300위 (6페이지)
    try:
        targets = [
            (0, ".KS", 10, "코스피 500"),  # 50개 x 10페이지 = 500종목
            (1, ".KQ", 6, "코스닥 300")   # 50개 x 6페이지 = 300종목
        ]
        for sosok, suffix, max_p, market_label in targets:
            for p in range(1, max_p + 1):
                p_url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={p}"
                r = requests.get(p_url, headers=headers, timeout=5)
                r.encoding = 'euc-kr'
                matches = re.findall(r'<a href="/item/main\.naver\?code=(\d{6})" class="tltle">(.*?)</a>', r.text)
                for code, name in matches:
                    label = f"[{market_label}] {name} ({code})"
                    stock_dict[label] = f"{code}{suffix}"
    except Exception:
        pass

    stock_dict["[직접 티커 입력]"] = "CUSTOM"
    return stock_dict

STOCK_DICT = load_all_market_stocks()

# ==============================================================================
# 4. ROE/PBR 결측치 자동 연산 보정 캐싱 함수
# ==============================================================================
@st.cache_data(ttl=3600)
def get_cached_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    data = {}
    try:
        info = stock.info
        data = info if info else {}
    except Exception:
        data = {}

    try:
        fast = stock.fast_info
        if "currentPrice" not in data or not data["currentPrice"]:
            data["currentPrice"] = getattr(fast, "last_price", 0)
        if "fiftyTwoWeekHigh" not in data or not data["fiftyTwoWeekHigh"]:
            data["fiftyTwoWeekHigh"] = getattr(fast, "year_high", data.get("currentPrice", 0))
        if "fiftyTwoWeekLow" not in data or not data["fiftyTwoWeekLow"]:
            data["fiftyTwoWeekLow"] = getattr(fast, "year_low", data.get("currentPrice", 0))
        if "marketCap" not in data or not data["marketCap"]:
            data["marketCap"] = getattr(fast, "market_cap", 0)
    except Exception:
        pass

    roe_val = data.get("returnOnEquity")
    pbr_val = data.get("priceToBook")
    
    if roe_val is None or roe_val == "N/A" or pbr_val is None or pbr_val == "N/A":
        try:
            bs = stock.balance_sheet
            fin = stock.financials
            if not bs.empty and not fin.empty:
                equity = None
                for eq_key in ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]:
                    if eq_key in bs.index:
                        equity = bs.loc[eq_key].iloc[0]
                        break
                
                net_inc = None
                for ni_key in ["Net Income Common Stockholders", "Net Income"]:
                    if ni_key in fin.index:
                        net_inc = fin.loc[ni_key].iloc[0]
                        break
                
                mcap = data.get("marketCap", 0)
                
                if (roe_val is None or roe_val == "N/A") and equity and net_inc:
                    if equity > 0:
                        data["returnOnEquity"] = net_inc / equity
                    else:
                        data["returnOnEquity"] = "초고수익 (자사주 소각 효과)"
                
                if (pbr_val is None or pbr_val == "N/A") and equity and mcap:
                    if equity > 0:
                        data["priceToBook"] = round(mcap / equity, 2)
                    else:
                        data["priceToBook"] = "자본잠식 (대규모 자사주 소각)"
        except Exception:
            pass

    return data

# ==============================================================================
# 5. 사이드바: Gemini 3.x 엔진 설정
# ==============================================================================
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 시스템 환경 설정")
    selected_model = st.selectbox(
        "🧠 AI 모델 엔진 (Gemini 3.x)",
        [
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3-flash-preview",
            "gemini-3.5-flash-lite",
            "gemini-3.1-pro-preview"
        ],
        index=0
    )
    
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
        st.success(f"🟢 {selected_model} 연동 완료")
    else:
        st.warning("⚠️ API 키를 입력해주세요.")

    st.divider()
    st.markdown("### 📊 감시 유니버스 현황")
    st.info(f"등록된 감시 종목 수: **{len(STOCK_DICT)-1:,}개**\n\n(미국 500 + 코스피 500 + 코스닥 300)")
    
    st.markdown("### 🛡️ Alpha-16 자금 관리 3대 원칙")
    st.markdown("""
    - **원금 회수 (Free-Ride)**: +50% 도달 시 30% 매도, +100% 도달 시 원금 100% 전액 회수
    - **하방 스탑**: 고점 대비 -10%(30% 익절), -20%(50% 익절), -30%(전량 청산/현금화)
    - **초기 리스크 손절**: 매수가 대비 -7%(비중 50% 축소), -10%(전량 칼손절)
    """)

# ==============================================================================
# 6. 스마트 검색 바
# ==============================================================================
col_search, col_custom = st.columns([3, 1])

with col_search:
    selected_name = st.selectbox(
        "🔍 종목 검색 (미국 500 / 코스피 500 / 코스닥 300 자동완성)", 
        list(STOCK_DICT.keys()), 
        index=0
    )

target_ticker = STOCK_DICT[selected_name]

with col_custom:
    if target_ticker == "CUSTOM":
        target_ticker = st.text_input("직접 티커 입력 (예: NVDA, AAPL, 005930.KS)", value="AAPL").strip().upper()
    else:
        st.text_input("확정 티커", value=target_ticker, disabled=True)

# ==============================================================================
# 7. 실시간 팩트 데이터 추출 & 4대 마스터 탭
# ==============================================================================
if target_ticker and target_ticker != "CUSTOM":
    info = get_cached_stock_info(target_ticker)
    
    current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
    high_52 = info.get("fiftyTwoWeekHigh", current_price)
    low_52 = info.get("fiftyTwoWeekLow", current_price)
    drawdown = ((current_price - high_52) / high_52 * 100) if (high_52 and current_price) else 0
    is_kr = "KS" in target_ticker or "KQ" in target_ticker
    curr_symbol = "₩" if is_kr else "$"
    curr_name = "원화 (KRW)" if is_kr else "달러 (USD)"
    curr_suffix = "원" if is_kr else ""
    
    # PER 소수점 2자리 포맷팅
    raw_trailing_pe = info.get("trailingPE")
    if isinstance(raw_trailing_pe, (int, float)):
        trailing_pe_display = f"{raw_trailing_pe:.2f}배"
    elif raw_trailing_pe and raw_trailing_pe != "N/A":
        trailing_pe_display = f"{float(raw_trailing_pe):.2f}배" if str(raw_trailing_pe).replace('.','',1).isdigit() else str(raw_trailing_pe)
    else:
        trailing_pe_display = "N/A"

    raw_forward_pe = info.get("forwardPE")
    if isinstance(raw_forward_pe, (int, float)):
        forward_pe_display = f"{raw_forward_pe:.2f}배"
    elif raw_forward_pe and raw_forward_pe != "N/A":
        forward_pe_display = f"{float(raw_forward_pe):.2f}배" if str(raw_forward_pe).replace('.','',1).isdigit() else str(raw_forward_pe)
    else:
        forward_pe_display = "N/A"
    
    # ROE 포맷팅
    raw_roe = info.get("returnOnEquity")
    if isinstance(raw_roe, (int, float)):
        roe_display = f"{raw_roe * 100:.2f}%"
    elif raw_roe:
        roe_display = str(raw_roe)
    else:
        roe_display = "N/A"

    # PBR 소수점 2자리 포맷팅
    raw_pbr = info.get("priceToBook")
    if isinstance(raw_pbr, (int, float)):
        pbr_display = f"{raw_pbr:.2f}배"
    elif raw_pbr:
        pbr_display = str(raw_pbr)
    else:
        pbr_display = "N/A"

    # 영업이익률 포맷팅
    raw_opm = info.get("operatingMargins")
    opm_display = f"{raw_opm * 100:.2f}%" if isinstance(raw_opm, (int, float)) else "N/A"
    
    revenue = info.get("totalRevenue", "N/A")
    net_income = info.get("netIncomeToCommon", "N/A")
    revenue_str = f"{curr_symbol} {revenue:,.0f}{curr_suffix}" if isinstance(revenue, (int, float)) else "N/A"
    net_income_str = f"{curr_symbol} {net_income:,.0f}{curr_suffix}" if isinstance(net_income, (int, float)) else "N/A"
    
    short_name = info.get("shortName", selected_name.split('] ')[-1].split(' (')[0].strip())

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 [Step 0~8] Alpha-16 마스터 리포트", 
        "⚖️ 동종업계 교차 비교 (피어 분석)", 
        "📑 표준 재무제표 원문 (한글화)", 
        "🛡️ 기계적 자금관리 & 트레일링 스탑"
    ])

    with tab1:
        st.markdown(f"### 📌 [Step 0] 팩트 데이터 교차 검증: **{short_name} ({target_ticker})** `기준 통화: {curr_name}`")
        
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("현재 기준가", f"{curr_symbol} {current_price:,.0f}{curr_suffix}" if is_kr else f"{curr_symbol} {current_price:,.2f}")
        m2.metric("52주 최고가 대비", f"{drawdown:.2f}%", delta=f"{drawdown:.2f}%")
        m3.metric("52주 최고 / 최저", f"{high_52:,.0f} / {low_52:,.0f}{curr_suffix}" if is_kr else f"{curr_symbol} {high_52:,.2f} / {low_52:,.2f}")
        m4.metric("PER (과거 실적)", f"{trailing_pe_display}")
        m5.metric("PBR (순자산비율)", f"{pbr_display}")
        m6.metric("ROE / 영업이익률", f"{roe_display} / {opm_display}")

        st.divider()

        if api_key:
            if st.button("🚀 Alpha-16 v7.5 9단계 전체 마스터 리포트 생성", use_container_width=True, type="primary"):
                with st.spinner(f"최신 실시간 팩트 주입 완료. {selected_model} 엔진이 9단계 마스터 파이프라인을 연산 중입니다..."):
                    
                    price_fmt = f"{curr_symbol} {current_price:,.0f}{curr_suffix}" if is_kr else f"{curr_symbol} {current_price:,.2f}"
                    high_fmt = f"{curr_symbol} {high_52:,.0f}{curr_suffix}" if is_kr else f"{curr_symbol} {high_52:,.2f}"
                    low_fmt = f"{curr_symbol} {low_52:,.0f}{curr_suffix}" if is_kr else f"{curr_symbol} {low_52:,.2f}"

                    prompt = f"""
                    너는 대한민국 및 글로벌 주식 시장의 기업 펀더멘털 분석과 기계적 자금 관리 시스템인 'Alpha-16 v7.5' 전문 수석 애널리스트다.
                    내가 아래 제공하는 [100% 최신 실시간 팩트 데이터]를 바탕으로, Alpha-16 v7.5 정규 마스터 파이프라인(Step 0부터 Step 8)을 단 한 단계도 축약하거나 생략하지 말고 모두 온전히 전개하라.
                    모든 금액 수치는 통화 단위({curr_name})와 천 단위 쉼표(,)를 정확히 표기하고, PER 수치는 소수점 2자리로 명확히 작성하라.

                    [100% 최신 실시간 팩트 데이터]
                    - 종목명/티커: {target_ticker} ({short_name}) [기준 통화: {curr_name}]
                    - 실시간 현재가: {price_fmt}, 52주 최고가: {high_fmt}, 최저가: {low_fmt}, 고점대비 하락률: {drawdown:.2f}%
                    - PER(Trailing): {trailing_pe_display}, Forward PER: {forward_pe_display}, PBR: {pbr_display}, ROE: {roe_display}, 영업이익률(OPM): {opm_display}
                    - 최근 매출액: {revenue_str}, 당기순이익: {net_income_str}

                    ======================================================================
                    [Alpha-16 v7.5 정규 마스터 파이프라인 규격 — 모든 항목 필수 전개]
                    ======================================================================
                    [Step 0] 실시간 다중 채널 교차 검증 (Data Verification)
                     • 종목명/티커, 52주 고점/저점, 실시간 기준가 및 고점 대비 하락률(%), 최신 밸류에이션(PER, PBR, ROE), 실적 팩트(DART/SEC 공시 기반 매출, 영업이익, OPM), 대차대조표 팩트(순현금 체력, 유동비율).

                    [Step 0.5] 산업의 존재 이유 & 숨겨진 본질적 해자 심층 분석 (Fundamental Deep-Dive)
                     1. [Primary] 전방 산업 폭발 동인 및 생태계의 절대적 병목(Chokepoint) 규명
                     2. [Primary] 고정비 레버리지 & 한계비용 제로 머신 (손익분기점 돌파 후 이익 급증 구조)
                     3. [Primary] 3~5년 다년 장기공급계약(LTA) 체결과 수주형 산업으로의 탈시클리컬화
                     4. [Primary] 피지컬 AI(자율주행 FSD / 휴머노이드 로봇) 등으로의 2차·3차 거대 시장(TAM) 확장성
                     5. [Primary/Secondary] 숨겨진 본질적 해자 및 경쟁사 대비 상대적 우위/열위 매트릭스 표 필수 작성

                    [Step 0.8] 거시경제·정치·지정학적 리스크 및 포트폴리오 헷지 분석 (Macro & Risk-Hedge Matrix)
                     1. 미·중 기술 패권 전쟁 및 대중국 수출 통제/관세 리스크
                     2. 대만 해협 등 지정학적 갈등과 글로벌 공급망 재편 동학
                     3. 글로벌 국채금리 상승에 따른 자금조달 및 밸류에이션(P/E) 압박
                     4. 빅테크 CAPEX 설비투자 추이 및 AI ROI(투자수익률) 의구심 리스크
                     5. Alpha-16 모델의 3중 방어 헷지(자체 순현금 체력, Free-Ride 원금 회수, 고점 -30% 기계적 하드스탑)

                    [Step 1] 4대 축 16개 핵심 팩터 정밀 평가 (80점 만점 컴팩트 매트릭스)
                     • I. 경제적 해자 (01.독점적표준 02.전환비용 03.데이터효과 04.원가/특허우위)
                     • II. 성장 동력 (05.시장확장성 06.수출/글로벌비중 07.신사업모멘텀 08.가격결정력)
                     • III. 재무 품질 (09.영업이익레버리지 10.투자효율ROIC 11.잉여현금흐름FCF 12.재무건전성)
                     • IV. 거버넌스&외생 (13.경영진주주정렬 14.주주환원율 15.설비투자사이클 16.외생·지정학방어)
                     • 4대 블록별 핵심 팩트 서술 + 각 5점 만점 배점 + Moat 총점(80점 만점) 및 종합 등급 도출

                    [Step 2] 비선형 퀀텀점프 3대 게이트 (Gate 1~3) 심사
                     • Gate 1 : 산업 표준 강제 교체 [Pass/Fail]
                     • Gate 2 : CAPEX 피크아웃 & 독점 Qual/수주 통과 [Pass/Fail]
                     • Gate 3 : 가동률 및 OPM 비선형적 폭발 [Pass/Fail]

                    [Step 3] 포트폴리오 5대 슬롯 자산배분 & 가변 스탑 판정
                     • Slot 1~5 배정 및 권장 비중(%), 가변 스탑 판정

                    [Step 4] 시나리오별 3대 적정 가치 밴드 (Bull / Base / Bear)
                     • 적정 주가 목표 밴드 및 상승 여력 제시

                    [Step 5] 실전 매매 프로토콜 (Free-Ride & 3단계 트레일링 스탑)
                     • Free-Ride 목표가(+50% 시 30% 매도, +100% 시 원금 회수)
                     • 3단계 트레일링 하방 스탑선(-10% 30% 익절, -20% 50% 익절, -30% 전량 청산)

                    [Step 6] 손절/청산 후 뇌동매매 차단 재진입 게이트 (Gate R-1 ~ R-3)

                    [Step 7] 정밀 백테스팅 검증

                    [Step 8] 최종 투자 결론 및 실전 행동 지침 (Actionable Verdict)
                     1. 종목 펀더멘털 판정 및 종합 등급
                     2. 포지션별 즉각 실행 액션
                     3. 상방 목표가 및 밸류에이션 룸
                     4. 원칙 요약 (One-Line Verdict)
                    ======================================================================
                    """

                    model_candidates = [
                        selected_model,
                        "gemini-3.7-flash",
                        "gemini-3.5-flash",
                        "gemini-3-flash-preview",
                        "gemini-3.5-flash-lite",
                        "gemini-3.1-pro-preview"
                    ]
                    
                    model_queue = []
                    for m in model_candidates:
                        if m not in model_queue:
                            model_queue.append(m)

                    success = False
                    response_text = ""
                    used_engine = ""

                    for m_name in model_queue:
                        try:
                            model = genai.GenerativeModel(m_name)
                            res = model.generate_content(prompt)
                            response_text = res.text
                            used_engine = m_name
                            success = True
                            break
                        except Exception:
                            continue

                    if success:
                        st.success(f"✅ {used_engine} 엔진으로 9단계 풀 리포트 생성 완료")
                        st.markdown(response_text)
                    else:
                        st.error("API 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

    with tab2:
        st.markdown(f"### ⚖️ 동종업계 피어 그룹 밸류에이션 교차 비교 `기준: {curr_name}`")
        default_peers = f"{target_ticker}, NVDA, TSM, 000660.KS" if "005930" in target_ticker else f"{target_ticker}, MSFT, GOOGL, NVDA"
        peers_input = st.text_input("비교할 티커 목록 (쉼표로 구분)", value=default_peers)
        
        if peers_input:
            peer_list = [p.strip().upper() for p in peers_input.split(",") if p.strip()]
            comp_data = []
            for p in peer_list:
                p_info = get_cached_stock_info(p)
                p_price = p_info.get("currentPrice", p_info.get("regularMarketPrice", 0))
                p_is_kr = "KS" in p or "KQ" in p
                p_curr_sym = "₩" if p_is_kr else "$"
                p_suffix = "원" if p_is_kr else ""
                
                # PER 소수점 2자리 포맷팅
                p_trailing_pe = p_info.get("trailingPE")
                p_pe_str = f"{p_trailing_pe:.2f}배" if isinstance(p_trailing_pe, (int, float)) else "N/A"

                p_fwd_pe = p_info.get("forwardPE")
                p_fwd_str = f"{p_fwd_pe:.2f}배" if isinstance(p_fwd_pe, (int, float)) else "N/A"

                p_roe = p_info.get("returnOnEquity")
                p_roe_str = f"{p_roe*100:.2f}%" if isinstance(p_roe, (int, float)) else (str(p_roe) if p_roe else "N/A")
                
                p_pbr = p_info.get("priceToBook")
                p_pbr_str = f"{p_pbr:.2f}배" if isinstance(p_pbr, (int, float)) else (str(p_pbr) if p_pbr else "N/A")
                
                p_opm = p_info.get("operatingMargins")
                p_opm_str = f"{p_opm*100:.2f}%" if isinstance(p_opm, (int, float)) else "N/A"

                comp_data.append({
                    "티커": p,
                    "기업명": p_info.get("shortName", p),
                    "현재가": f"{p_curr_sym} {p_price:,.0f}{p_suffix}" if p_is_kr else f"{p_curr_sym} {p_price:,.2f}",
                    "PER (과거실적)": p_pe_str,
                    "Forward PER (선행)": p_fwd_str,
                    "PBR (순자산비율)": p_pbr_str,
                    "ROE (자기자본이익률)": p_roe_str,
                    "영업이익률 (OPM)": p_opm_str,
                })
            if comp_data:
                st.dataframe(pd.DataFrame(comp_data).set_index("티커"), use_container_width=True)

    with tab3:
        st.markdown(f"### 📑 표준 재무제표 원문 데이터 (한글 번역 / 천 단위 쉼표 표기) `단위: {curr_name}`")
        stmt_choice = st.radio("재무제표 종류 선택", ["손익계산서 (매출·이익)", "대차대조표 (자산·부채·자본)", "현금흐름표 (영업·투자·잉여현금)"], horizontal=True)
        try:
            stock_obj = yf.Ticker(target_ticker)
            if "손익계산서" in stmt_choice:
                st.dataframe(format_currency_df(stock_obj.financials, is_kr), use_container_width=True)
            elif "대차대조표" in stmt_choice:
                st.dataframe(format_currency_df(stock_obj.balance_sheet, is_kr), use_container_width=True)
            else:
                st.dataframe(format_currency_df(stock_obj.cashflow, is_kr), use_container_width=True)
        except Exception:
            st.info("재무제표 데이터를 불러오는 중입니다.")

    with tab4:
        st.markdown(f"### 🛡️ [Step 5] 기계적 자금 관리 & 트레일링 스탑 계산기 `기준 통화: {curr_name}`")
        c1, c2 = st.columns(2)
        with c1:
            my_buy_price = st.number_input(f"내 매수 단가 ({curr_name})", value=float(current_price if current_price else 100.0))
        with c2:
            my_peak_price = st.number_input(f"매수 이후 형성된 최고가 ({curr_name})", value=float(max(current_price if current_price else 100.0, my_buy_price)))

        st.write("")
        s1, s2, s3 = st.columns(3)
        s1.error(f"**1차 하방 스탑 (-10%)**\n\n- 기준 가격: **{curr_symbol} {my_peak_price * 0.90:,.2f}{curr_suffix}**\n- 대응 액션: **보유 비중 30% 분할 익절**")
        s2.error(f"**2차 하방 스탑 (-20%)**\n\n- 기준 가격: **{curr_symbol} {my_peak_price * 0.80:,.2f}{curr_suffix}**\n- 대응 액션: **보유 비중 50% 추가 익절**")
        s3.error(f"**3차 하방 스탑 (-30%)**\n\n- 기준 가격: **{curr_symbol} {my_peak_price * 0.70:,.2f}{curr_suffix}**\n- 대응 액션: **잔여 포지션 전량 청산 (현금화)**")

        st.divider()
        f1, f2 = st.columns(2)
        f1.success(f"**Free-Ride 1차 (+50% 달성)**\n\n- 목표 가격: **{curr_symbol} {my_buy_price * 1.50:,.2f}{curr_suffix}**\n- 대응 액션: **30% 매도 (투자 원금의 45% 회수)**")
        f2.success(f"**Free-Ride 2차 (+100% 달성)**\n\n- 목표 가격: **{curr_symbol} {my_buy_price * 2.00:,.2f}{curr_suffix}**\n- 대응 액션: **원금 100% 전액 회수 (무위험 주식화)**")