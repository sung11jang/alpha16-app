import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import requests

# ==============================================================================
# 1. 페이지 레이아웃 및 스타일 설정
# ==============================================================================
st.set_page_config(
    page_title="Alpha-16 v7.5 Institutional Terminal",
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

st.markdown('<div class="main-title">🏛️ Alpha-16 v7.5 Institutional Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">나스닥 100 · 코스피 상위 400 · 코스닥 상위 200 통합 마스터 터미널</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. 나스닥 100 / 코스피 400 / 코스닥 200 자동 로드 & 캐싱 함수
# ==============================================================================
@st.cache_data(ttl=86400)
def load_all_market_stocks():
    stock_dict = {}

    # 1. 나스닥 100 핵심 대표 구성 종목
    nasdaq_top = {
        "엔비디아 (NVDA)": "NVDA", "애플 (AAPL)": "AAPL", "마이크로소프트 (MSFT)": "MSFT",
        "알파벳 A (GOOGL)": "GOOGL", "알파벳 C (GOOG)": "GOOG", "아마존 (AMZN)": "AMZN",
        "메타 (META)": "META", "브로드컴 (AVGO)": "AVGO", "테슬라 (TSLA)": "TSLA",
        "ASML (ASML)": "ASML", "코스트코 (COST)": "COST", "넷플릭스 (NFLX)": "NFLX",
        "AMD (AMD)": "AMD", "퀄컴 (QCOM)": "QCOM", "어도비 (ADBE)": "ADBE",
        "시스코 (CSCO)": "CSCO", "펩시코 (PEP)": "PEP", "린데 (LIN)": "LIN",
        "인튜이티브 서지컬 (ISRG)": "ISRG", "텍사스 인스트루먼트 (TXN)": "TXN",
        "암 홀딩스 (ARM)": "ARM", "마이크론 (MU)": "MU", "팔란티어 (PLTR)": "PLTR",
        "어플라이드 머티어리얼즈 (AMAT)": "AMAT", "램리서치 (LRCX)": "LRCX", "KLA (KLAC)": "KLAC",
        "인텔 (INTC)": "INTC", "스타벅스 (SBUX)": "SBUX", "에어비앤비 (ABNB)": "ABNB",
        "부킹홀딩스 (BKNG)": "BKNG", "모놀리식 파워 (MPWR)": "MPWR", "크라우드스트라이크 (CRWD)": "CRWD",
        "팔로알토 (PANW)": "PANW", "시놉시스 (SNPS)": "SNPS", "케이던스 (CDNS)": "CDNS",
        "마벨 테크놀로지 (MRVL)": "MRVL", "아날로그 디바이스 (ADI)": "ADI", "온세미컨덕터 (ON)": "ON",
        "페이팔 (PYPL)": "PYPL", "모더나 (MRNA)": "MRNA", "길리어드 (GILD)": "GILD",
        "버텍스 (VRTX)": "VRTX", "암젠 (AMGN)": "AMGN", "리제네론 (REGN)": "REGN",
        "줌 (ZM)": "ZM", "도큐사인 (DOCU)": "DOCU", "루시드 (LCID)": "LCID", "리비안 (RIVN)": "RIVN"
    }
    stock_dict.update(nasdaq_top)

    # 2. KRX 공식 마스터 피드(네이버 증권 시총 랭킹) 기반 코스피 400 / 코스닥 200 실시간 수집
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 코스피 상위 400 (페이지당 50개 x 8페이지)
    for page in range(1, 9):
        try:
            url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok=0&page={page}"
            res = requests.get(url, headers=headers)
            res.encoding = 'euc-kr'
            dfs = pd.read_html(res.text)
            df = dfs[1]
            df = df.dropna(subset=['종목명'])
            for _, row in df.iterrows():
                name = str(row['종목명']).strip()
                # 테이블 링크에서 종목코드 파싱
                code_raw = str(row.name)
                # DataFrame 내 'N' 열 유무 확인
                if name and name != 'nan':
                    # HTML 소스 내 코드 추출
                    pass
        except:
            pass

    # 안정적인 시총 상위 400/200 종목 코드 수집용 백업 파서
    try:
        krx_url = "http://data.krx.co.kr/comm/bldAttPage/getJsonData.cmd"
        # 코스피 400 + 코스닥 200 직접 파싱
        kospi_url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0"
        kosdaq_url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=1"
        
        for sosok, suffix, max_p, market_label in [(0, ".KS", 8, "KOSPI"), (1, ".KQ", 4, "KOSDAQ")]:
            for p in range(1, max_p + 1):
                p_url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={p}"
                r = requests.get(p_url, headers=headers)
                r.encoding = 'euc-kr'
                html_text = r.text
                
                # HTML 텍스트에서 /item/main.naver?code=XXXXXX 파싱
                import re
                matches = re.findall(r'<a href="/item/main\.naver\?code=(\d{6})" class="tltle">(.*?)</a>', html_text)
                for code, name in matches:
                    label = f"{name} ({code} | {market_label})"
                    stock_dict[label] = f"{code}{suffix}"
    except Exception as e:
        pass

    stock_dict["[직접 티커 입력]"] = "CUSTOM"
    return stock_dict

STOCK_DICT = load_all_market_stocks()

# ==============================================================================
# 3. 사이드바: Gemini 3.x 엔진 설정
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
    st.markdown("### 📊 마스터 데이터 현황")
    st.info(f"등록된 감시 종목 수: **{len(STOCK_DICT)-1}개**")
    
    st.markdown("### 🛡️ Alpha-16 자금 관리 3대 원칙")
    st.markdown("""
    - **Free-Ride**: +50% 시 30% 매도, +100% 시 원금 회수
    - **하방 스탑**: 고점 -10%(30%), -20%(50%), -30%(전량 현금화)
    - **초기 손절**: -7%(50% 축소), -10%(전량 칼손절)
    """)

# ==============================================================================
# 4. 스마트 검색 바
# ==============================================================================
col_search, col_custom = st.columns([3, 1])

with col_search:
    selected_name = st.selectbox(
        "🔍 종목 검색 (나스닥 100 / 코스피 400 / 코스닥 200 자동완성)", 
        list(STOCK_DICT.keys()), 
        index=0
    )

target_ticker = STOCK_DICT[selected_name]

with col_custom:
    if target_ticker == "CUSTOM":
        target_ticker = st.text_input("직접 티커 입력 (예: 005930.KS, NVDA)", value="005930.KS").strip().upper()
    else:
        st.text_input("연동 티커", value=target_ticker, disabled=True)

# ==============================================================================
# 5. 실시간 팩트 데이터 추출 & 4대 마스터 탭
# ==============================================================================
if target_ticker and target_ticker != "CUSTOM":
    try:
        stock = yf.Ticker(target_ticker)
        info = stock.info
        
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        high_52 = info.get("fiftyTwoWeekHigh", current_price)
        low_52 = info.get("fiftyTwoWeekLow", current_price)
        drawdown = ((current_price - high_52) / high_52 * 100) if high_52 else 0
        is_kr = "KS" in target_ticker or "KQ" in target_ticker
        curr_unit = "원" if is_kr else "$"
        
        trailing_pe = info.get("trailingPE", "N/A")
        forward_pe = info.get("forwardPE", "N/A")
        pbr = info.get("priceToBook", "N/A")
        roe = f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A"
        opm = f"{info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "N/A"
        revenue = info.get("totalRevenue", "N/A")
        net_income = info.get("netIncomeToCommon", "N/A")
        short_name = info.get("shortName", selected_name.split('(')[0].strip())

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 [Step 0~8] Alpha-16 마스터 리포트", 
            "⚖️ 종목 교차 비교 (Compare)", 
            "📑 전체 재무제표 원문", 
            "🛡️ 3단계 스탑 & 슬롯 관리"
        ])

        with tab1:
            st.markdown(f"### 📌 [Step 0] 팩트 데이터 교차 검증: **{short_name} ({target_ticker})**")
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("현재 기준가", f"{current_price:,.0f}원" if is_kr else f"${current_price:,.2f}")
            m2.metric("52주 고점 대비", f"{drawdown:.2f}%", delta=f"{drawdown:.2f}%")
            m3.metric("52주 최고/최저", f"{high_52:,.0f} / {low_52:,.0f}" if is_kr else f"${high_52:,.2f} / ${low_52:,.2f}")
            m4.metric("PER (Trailing)", f"{trailing_pe}")
            m5.metric("PBR", f"{pbr}")
            m6.metric("ROE / OPM", f"{roe} / {opm}")

            st.divider()

            if api_key:
                if st.button("🚀 Alpha-16 v7.5 9단계 전체 리포트 생성", use_container_width=True, type="primary"):
                    with st.spinner(f"최신 실시간 팩트 주입 완료. {selected_model} 엔진이 9단계 마스터 파이프라인을 연산 중입니다..."):
                        
                        prompt = f"""
                        너는 대한민국 및 글로벌 주식 시장의 기업 펀더멘털 분석과 기계적 자금 관리 시스템인 'Alpha-16 v7.5' 전문 수석 애널리스트다.
                        내가 아래 제공하는 [100% 최신 실시간 팩트 데이터]를 바탕으로, Alpha-16 v7.5 정규 마스터 파이프라인(Step 0부터 Step 8)을 단 한 단계도 축약하거나 생략하지 말고 모두 온전히 전개하라.

                        [100% 최신 실시간 팩트 데이터]
                        - 종목명/티커: {target_ticker} ({short_name})
                        - 실시간 현재가: {current_price}, 52주 최고가: {high_52}, 최저가: {low_52}, 고점대비 하락률: {drawdown:.2f}%
                        - PER(Trailing): {trailing_pe}, Forward PER: {forward_pe}, PBR: {pbr}, ROE: {roe}, 영업이익률(OPM): {opm}
                        - 최근 매출: {revenue}, 순이익: {net_income}

                        ======================================================================
                        [Alpha-16 v7.5 정규 마스터 파이프라인 규격 — 모든 항목 필수 전개]
                        ======================================================================
                        [Step 0] 실시간 다중 채널 교차 검증 (Data Verification)
                         • 종목명/티커, 52주 고점/저점, 실시간 기준가 및 고점 대비 하락률(%), 최신 밸류에이션(PER, PBR, ROE), 실적 팩트(DART/SEC 공시 기반 매출, 영업이익, OPM), 대차대조표 팩트(순현금 체력, 유동비율).

                        [Step 0.5] 산업의 존재 이유 & 숨겨진 본질적 해자 심층 분석 (Fundamental Deep-Dive)
                         1. [Primary] Why Industry Explodes & Where is the Chokepoint? (전방 산업 폭발 동인 및 생태계의 절대적 병목 규명)
                         2. [Primary] 고정비 레버리지 & 한계비용 제로 머신 (BEP 돌파 후 매출의 영업이익 직결 구조)
                         3. [Primary] 3~5년 다년 LTA(장기공급계약) 체결과 '수주형 산업'으로의 탈시클리컬화
                         4. [Primary] 피지컬 AI(자율주행 FSD / 휴머노이드 로봇) 등으로의 2차·3차 거대 TAM 확장성
                         5. [Primary/Secondary] 숨겨진 본질적 해자 및 경쟁사 대비 상대적 우위/열위 매트릭스 표 필수 작성

                        [Step 0.8] 거시경제·정치·지정학적 리스크 및 포트폴리오 헷지 분석 (Macro & Risk-Hedge Matrix)
                         1. 미·중 기술 패권 전쟁 및 대중국 수출 통제/관세 리스크
                         2. 대만 해협 등 지정학적 갈등과 글로벌 공급망 재편 동학
                         3. 글로벌 국채금리 상승에 따른 자금조달 및 밸류에이션(P/E) 압박
                         4. 빅테크 CAPEX 투자 추이 및 AI ROI 의구심 리스크
                         5. Alpha-16 모델의 3중 방어 헷지(자체 순현금 체력, Free-Ride 원금 회수, 고점 -30% 기계적 하드스탑)

                        [Step 1] 4대 축 16개 핵심 팩터 정밀 평가 (80점 만점) — 컴팩트 매트릭스
                         • I. 경제적 해자 (01.독점적표준 02.전환비용 03.데이터효과 04.원가/특허우위)
                         • II. 성장 동력 (05.TAM확장성 06.수출/글로벌비중 07.신사업모멘텀 08.가격결정력)
                         • III. 재무 품질 (09.OPM레버리지 10.ROIC/ROE효율 11.FCF창출력 12.재무건전성)
                         • IV. 거버넌스&외생 (13.경영진얼라인 14.주주환원율 15.CAPEX사이클 16.외생·지정학방어)
                         • 4대 블록별 핵심 팩트 서술 + 각 5점 만점 배점 + Moat 총점(80점 만점) 및 종합 등급 도출

                        [Step 2] 비선형 퀀텀점프 3대 게이트 (Gate 1~3) 심사
                         • Gate 1 : 산업 표준 강제 교체 [Pass/Fail]
                         • Gate 2 : CAPEX 피크아웃 & 독점 Qual/수주 통과 [Pass/Fail]
                         • Gate 3 : 가동률 및 OPM 비선형적 폭발 [Pass/Fail]

                        [Step 3] 포트폴리오 5대 슬롯 자산배분 & 가변 스탑 판정
                         • Slot 1~5 배정 및 권장 비중(%), 가변 스탑 판정

                        [Step 4] 시나리오별 3대 적정 가치 밴드 (Bull / Base / Bear)
                         • 적정 주가 목표 밴드 및 밸류에이션 룸 제시

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
                            except Exception as ex:
                                continue

                        if success:
                            st.success(f"✅ {used_engine} 엔진으로 9단계 풀 리포트 생성 완료")
                            st.markdown(response_text)
                        else:
                            st.error("API 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

        with tab2:
            st.markdown("### ⚖️ 동종업계 피어 그룹 밸류에이션 비교")
            default_peers = f"{target_ticker}, NVDA, TSM, 000660.KS" if "005930" in target_ticker else f"{target_ticker}, AAPL, MSFT, GOOGL"
            peers_input = st.text_input("비교할 티커 목록 (쉼표 구분)", value=default_peers)
            
            if peers_input:
                peer_list = [p.strip().upper() for p in peers_input.split(",") if p.strip()]
                comp_data = []
                for p in peer_list:
                    try:
                        p_info = yf.Ticker(p).info
                        p_price = p_info.get("currentPrice", p_info.get("regularMarketPrice", 0))
                        comp_data.append({
                            "티커": p,
                            "기업명": p_info.get("shortName", p),
                            "현재가": f"${p_price:,.2f}" if "KS" not in p and "KQ" not in p else f"{p_price:,.0f}원",
                            "Trailing PER": p_info.get("trailingPE", "N/A"),
                            "Forward PER": p_info.get("forwardPE", "N/A"),
                            "PBR": p_info.get("priceToBook", "N/A"),
                            "ROE(%)": f"{p_info.get('returnOnEquity', 0)*100:.2f}%" if p_info.get('returnOnEquity') else "N/A",
                            "영업이익률(OPM)": f"{p_info.get('operatingMargins', 0)*100:.2f}%" if p_info.get('operatingMargins') else "N/A",
                        })
                    except:
                        pass
                if comp_data:
                    st.dataframe(pd.DataFrame(comp_data).set_index("티커"), use_container_width=True)

        with tab3:
            st.markdown("### 📑 전체 재무제표 원문 데이터")
            stmt_choice = st.radio("재무제표 선택", ["손익계산서 (Income Statement)", "대차대조표 (Balance Sheet)", "현금흐름표 (Cash Flow)"], horizontal=True)
            if "손익계산서" in stmt_choice:
                st.dataframe(stock.financials, use_container_width=True)
            elif "대차대조표" in stmt_choice:
                st.dataframe(stock.balance_sheet, use_container_width=True)
            else:
                st.dataframe(stock.cashflow, use_container_width=True)

        with tab4:
            st.markdown("### 🛡️ [Step 5] 기계적 자금 관리 & 트레일링 스탑 계산기")
            c1, c2 = st.columns(2)
            with c1:
                my_buy_price = st.number_input("내 매수 단가", value=float(current_price))
            with c2:
                my_peak_price = st.number_input("매수 이후 형성된 최고가", value=float(max(current_price, my_buy_price)))

            st.write("")
            s1, s2, s3 = st.columns(3)
            s1.error(f"**1차 스탑 (-10%)**\n\n- 기준 가격: **{curr_unit}{my_peak_price * 0.90:,.2f}**\n- 액션: **30% 분할 익절**")
            s2.error(f"**2차 스탑 (-20%)**\n\n- 기준 가격: **{curr_unit}{my_peak_price * 0.80:,.2f}**\n- 액션: **50% 추가 익절**")
            s3.error(f"**3차 스탑 (-30%)**\n\n- 기준 가격: **{curr_unit}{my_peak_price * 0.70:,.2f}**\n- 액션: **전량 청산 (현금화)**")

            st.divider()
            f1, f2 = st.columns(2)
            f1.success(f"**Free-Ride 1차 (+50%)**\n\n- 가격: **{curr_unit}{my_buy_price * 1.50:,.2f}**\n- 액션: **30% 매도 (원금 45% 회수)**")
            f2.success(f"**Free-Ride 2차 (+100%)**\n\n- 가격: **{curr_unit}{my_buy_price * 2.00:,.2f}**\n- 액션: **원금 100% 전액 회수**")

    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {e}")