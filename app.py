import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# --- 1. PAGE CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="High-Yield Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🔧 GLOBAL HELPER FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600)
def fetch_overlay_data(ticker, start_date, end_date):
    """Fetches historical data for underlying assets using yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
            actions=True,
            auto_adjust=False
        )
        if hist.empty:
            return None, None
        df_u = hist.reset_index()[['Date', 'Close']].rename(columns={'Close': 'Closing Price'})
        df_u['Date'] = pd.to_datetime(df_u['Date']).dt.tz_localize(None)
        df_u['Ticker'] = ticker
        divs = hist[hist['Dividends'] > 0]['Dividends'].reset_index()
        if not divs.empty:
            df_h = divs.rename(columns={'Date': 'Date of Pay', 'Dividends': 'Amount'})
            df_h['Date of Pay'] = pd.to_datetime(df_h['Date of Pay']).dt.tz_localize(None)
            df_h['Ticker'] = ticker
        else:
            df_h = pd.DataFrame(columns=['Date of Pay', 'Amount', 'Ticker'])
        return df_u, df_h
    except Exception:
        return None, None

# ==========================================
# 🚀 MAIN APP LOGIC
# ==========================================
def authenticated_dashboard():
    
    # --- INJECT CSS ---
    st.components.v1.html('''
    <script>
    window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));
    </script>
    ''', height=0)

    st.markdown("""
        <style>
        .stApp { background-color: #0D1117; color: #E6EDF3; }
        section[data-testid="stMain"] { -ms-overflow-style: none; scrollbar-width: none; }
        section[data-testid="stMain"]::-webkit-scrollbar { display: none !important; }
        section[data-testid="stSidebar"]::-webkit-scrollbar { display: block !important; width: 6px !important; background: #0D1117 !important; }
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: #30363d !important; border-radius: 3px !important; }
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
        .element-container { margin-bottom: 0.3rem !important; }
        .stApp, section[data-testid="stMain"] { zoom: 1 !important; font-size: 16px !important; }
        div[data-testid="stMetric"] { background-color: #1E293B; border: 1px solid #30363d; border-radius: 10px; padding: 8px 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); min-height: 80px; transition: transform 0.2s; }
        div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] { background-color: #1a2e35 !important; border: 1px solid #F59E0B !important; }
        div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] { background-color: #0D1117 !important; border: 2px solid #00C805 !important; transform: scale(1.15); z-index: 10; margin-left: 10px; }
        div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetricValue"] div { font-size: 1.8rem !important; }
        div[data-testid="stMetricLabel"] p { color: #8AC7DE !important; font-size: 0.85rem !important; font-weight: 600 !important; }
        div[data-testid="stMetricValue"] div { color: #FFFFFF !important; font-size: 1.5rem !important; font-weight: 700 !important; }
        div[data-testid="stMetricDelta"] svg { transform: scale(1.2); }
        div[data-testid="stMetricDelta"] > div { font-size: 1.1rem !important; font-weight: 800 !important; filter: brightness(1.2); }
        [data-testid="stMetricLabel"] svg { fill: #E6EDF3 !important; opacity: 0.9 !important; width: 16px !important; height: 16px !important; }
        [data-testid="stMetricLabel"]:hover svg { fill: #F59E0B !important; opacity: 1.0 !important; }
        div[role="tooltip"] { background-color: #1E293B !important; color: #FFFFFF !important; border: 1px solid #8AC7DE !important; border-radius: 6px !important; font-size: 0.9rem !important; box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important; }
        div[role="tooltip"] > div { background-color: #1E293B !important; }
        div[data-baseweb="calendar"] { background-color: #1E293B !important; color: #FFFFFF !important; border: 1px solid #30363d !important; }
        div[data-baseweb="calendar"] > div { background-color: #1E293B !important; }
        div[data-baseweb="select"] div { color: #FFFFFF !important; }
        ul[role="listbox"], div[data-baseweb="menu"] { background-color: #1E293B !important; border: 1px solid #30363d !important; }
        li[role="option"] { color: #FFFFFF !important; background-color: #1E293B !important; }
        li[role="option"]:hover, li[role="option"][aria-selected="true"] { background-color: #8AC7DE !important; color: #0D1117 !important; font-weight: bold !important; }
        div[data-baseweb="calendar"] button svg { fill: #8AC7DE !important; }
        div[data-baseweb="calendar"] button { background-color: transparent !important; }
        div[data-baseweb="calendar"] div[role="grid"] div { color: #E6EDF3 !important; }
        div[data-baseweb="calendar"] button[aria-label] { color: #FFFFFF !important; }
        div[data-baseweb="calendar"] [aria-selected="true"] { background-color: #8AC7DE !important; color: #0D1117 !important; font-weight: bold !important; }
        div[data-baseweb="calendar"] [aria-selected="false"]:hover { background-color: #30363d !important; color: #FFFFFF !important; }
        h1, h2, h3, h4, h5, h6, p, label { color: #E6EDF3 !important; }
        div[data-baseweb="select"] > div, div[data-testid="stDateInput"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #1E293B !important; border-color: #30363d !important; color: #FFFFFF !important; font-weight: bold !important; border-radius: 6px !important; min-height: 40px !important; }
        input { color: #FFFFFF !important; font-weight: bold !important; }
        .stSelectbox svg, .stDateInput svg { fill: #8AC7DE !important; }
        .stSidebar .element-container { margin-top: 0rem !important; margin-bottom: 0.5rem !important; }
        .stSidebar .stSelectbox, .stSidebar .stDateInput, .stSidebar .stRadio, .stSidebar .stNumberInput { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        .stSidebar .stCheckbox label { font-weight: bold; color: #8AC7DE !important; }
        div[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 5px; overflow: hidden; color-scheme: dark; }
        div[data-testid="stDataFrame"] div[role="columnheader"] button { display: none !important; }
        div[data-testid="stDataFrame"] div[data-testid="stVerticalBlock"] { overflow: hidden !important; }
        div[data-testid="stDataFrame"] ::-webkit-scrollbar { display: none !important; }
        @media (min-width: 1200px) {
            section[data-testid="stSidebar"] { width: 300px !important; min-width: 300px !important; height: 100vh !important; position: fixed !important; top: 0 !important; left: 0 !important; background-color: #0D1117 !important; border-right: 1px solid #30363d !important; z-index: 9999 !important; transform: none !important; padding-top: 1rem !important; }
            section[data-testid="stSidebar"] h2 { padding-top: 0rem !important; margin-top: 0rem !important; margin-bottom: 1rem !important; }
            section[data-testid="stMain"] { margin-left: 300px !important; width: calc(100% - 300px) !important; position: relative !important; display: block !important; }
            .block-container { padding-left: 3rem !important; padding-right: 3rem !important; padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
            header[data-testid="stHeader"], button[data-testid="stSidebarCollapseBtn"], div[data-testid="collapsedControl"] { display: none !important; }
        }
        @media (max-width: 1199px) {
            section[data-testid="stMain"] { margin-left: 0 !important; width: 100% !important; }
            .block-container { padding-top: 4rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100vw !important; min-width: 100vw !important; }
            header[data-testid="stHeader"] { display: block !important; background-color: #0D1117 !important; z-index: 99999 !important; }
            button[data-testid*="SidebarCollapseButton"], [data-testid*="collapsedControl"] { display: block !important; color: #E6EDF3 !important; }
            section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background-color: #0D1117 !important; border-right: 1px solid #30363d !important; }
        }
        footer, #MainMenu, .viewerBadge_container__1QSob, .viewerBadge_link__1SlnQ { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # --- PHASE 1: LOAD ONLY THE MENUS (INSTANT) ---
    @st.cache_data(ttl=3600)
    def load_base_sheets():
        try:
            h_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQe4koGj386xkUGn3XXhysM-54_DIbYawunKX49C2Kt6KH9i097JDNnhbKQpRVn7WH05noFpgY3p1_e/pub?gid=970184313&single=true&output=csv"
            m_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQe4koGj386xkUGn3XXhysM-54_DIbYawunKX49C2Kt6KH9i097JDNnhbKQpRVn7WH05noFpgY3p1_e/pub?gid=618318322&single=true&output=csv"
            
            df_m = pd.read_csv(m_url)
            df_h_sheet = pd.read_csv(h_url)
            
            # 1. Clean invisible spaces off column headers
            df_m.columns = df_m.columns.str.strip()
            df_h_sheet.columns = df_h_sheet.columns.str.strip()
            
            # 2. Rename mapped columns
            m_rename_map = {'Fund Strategy': 'Strategy', 'Asset Class': 'Strategy', 'Fund Name': 'Company', 'Name': 'Company'}
            df_m = df_m.rename(columns=m_rename_map)
            df_h_sheet = df_h_sheet.rename(columns={'Pay Date': 'Date of Pay', 'Payment Date': 'Date of Pay', 'Payout Date': 'Date of Pay', 'Date': 'Date of Pay'})
            
            if 'Ticker' not in df_m.columns:
                return None, None
            
            # 3. Clean Ticker Data & Explicit Denylist
            df_m['Ticker'] = df_m['Ticker'].astype(str).str.strip().str.upper()
            
            bad_headers = [
                'DEFIANCE', 
                'YIELDMAX', 
                'ROUNDHILL', 
                'KURV', 
                'PROSHARES', 
                'GLOBALX', 
                'REX',
                'TIDAL',
                'ELEVATE',
                'SIMPLIFY',
                'ISHARES',
                'VANGUARD',
                'VANECK',
                'INVESCO',
                'COMPANY',
                'STRATEGY',
                'CALAMOS',
                'GRAYSCALE',
                'INVESCO',
                'KRANESHARES',
                'VISTASHARES',
            ]
            
            # Remove explicit bad headers
            df_m = df_m[~df_m['Ticker'].isin(bad_headers)]
            # Remove any entry containing a space
            df_m = df_m[~df_m['Ticker'].str.contains(' ', na=False)]
                
            # 4. Clean History Dates
            if 'Date of Pay' in df_h_sheet.columns and 'Ticker' in df_h_sheet.columns:
                df_h_sheet['Date of Pay'] = pd.to_datetime(df_h_sheet['Date of Pay']).dt.tz_localize(None)
                df_h_sheet['Ticker'] = df_h_sheet['Ticker'].astype(str).str.strip().str.upper()
                df_h_sheet = df_h_sheet.sort_values(['Ticker', 'Date of Pay'])
            else:
                df_h_sheet = pd.DataFrame(columns=['Date of Pay', 'Ticker'])
                
            return df_m, df_h_sheet
        except Exception as e:
            st.error(f"Failed to load Google Sheets: {e}")
            return None, None

    df_m, df_h_sheet = load_base_sheets()
    if df_m is None:
        st.stop()

    all_tickers = sorted(df_m['Ticker'].unique())

    # --- PHASE 2: LAZY LOAD A SPECIFIC TICKER ---
    @st.cache_data(ttl=3600)
    def fetch_single_asset(ticker):
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="max", auto_adjust=False)
            if hist.empty:
                return pd.DataFrame(), pd.DataFrame()
            
            hist = hist.reset_index()
            
            # Build Prices
            prices = hist[['Date', 'Close']].copy().rename(columns={'Close': 'Closing Price'})
            prices['Ticker'] = ticker
            prices['Date'] = pd.to_datetime(prices['Date']).dt.tz_localize(None)
            
            # Attach Metadata Safely
            meta = df_m[df_m['Ticker'] == ticker]
            if not meta.empty:
                for col in ['Strategy', 'Company', 'Underlying']:
                    if col in meta.columns:
                        val = meta.iloc[0][col]
                        if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan':
                            prices[col] = '-'
                        else:
                            prices[col] = val
                    else:
                        prices[col] = '-'
            prices['Closing Price'] = pd.to_numeric(prices['Closing Price'], errors='coerce').fillna(0.0)
            
            # Build Dividends (Matching YF Amount to Sheet Pay Date)
            final_history = []
            if 'Dividends' in hist.columns:
                divs = hist[hist['Dividends'] > 0][['Date', 'Dividends']].copy()
                if not divs.empty:
                    divs['YF_Ex_Date'] = pd.to_datetime(divs['Date']).dt.tz_localize(None)
                    divs = divs.sort_values('YF_Ex_Date')
                    
                    sheet_dates = df_h_sheet[df_h_sheet['Ticker'] == ticker].sort_values('Date of Pay')
                    
                    for j, yf_row in enumerate(divs.itertuples()):
                        amt = yf_row.Dividends
                        # Use Sheet Pay Date if available, fallback to YF Ex-Date
                        pay_date = sheet_dates.iloc[j]['Date of Pay'] if j < len(sheet_dates) else yf_row.YF_Ex_Date
                        final_history.append({'Date of Pay': pay_date, 'Ticker': ticker, 'Amount': amt})
            
            df_h_single = pd.DataFrame(final_history) if final_history else pd.DataFrame(columns=['Date of Pay', 'Amount', 'Ticker'])
            return prices, df_h_single
            
        except Exception:
            return pd.DataFrame(), pd.DataFrame()

    # --- COMPOUNDING ENGINE ---
    def calculate_journey(ticker, start_date, end_date, initial_shares, drip_enabled, unified_df, history_df):
        t_price = unified_df[unified_df['Ticker'] == ticker].sort_values('Date')
        journey = t_price[(t_price['Date'] >= start_date) & (t_price['Date'] <= end_date)].copy()
        if journey.empty: return journey
            
        t_divs = history_df[history_df['Ticker'] == ticker].sort_values('Date of Pay')
        relevant_divs = t_divs[(t_divs['Date of Pay'] >= start_date) & (t_divs['Date of Pay'] <= end_date)].copy()
        
        journey = journey.set_index('Date')
        journey['Shares'] = initial_shares
        journey['Cash_Pocketed'] = 0.0
        
        current_shares = initial_shares
        cum_cash = 0.0
        
        if not relevant_divs.empty:
            for _, row in relevant_divs.iterrows():
                d_date = row['Date of Pay']
                d_amt = row['Amount']
                if d_date in journey.index:
                    payout = current_shares * d_amt
                    if drip_enabled:
                        reinvest_price = journey.loc[d_date, 'Closing Price']
                        if reinvest_price > 0:
                            current_shares += (payout / reinvest_price)
                        journey.loc[d_date:, 'Shares'] = current_shares
                    else:
                        cum_cash += payout
                        journey.loc[d_date:, 'Cash_Pocketed'] = cum_cash
        
        journey = journey.reset_index()
        journey['Market_Value'] = journey['Closing Price'] * journey['Shares']
        journey['Base_Asset_Value'] = journey['Closing Price'] * initial_shares
        journey['True_Value'] = journey['Market_Value'] if drip_enabled else journey['Market_Value'] + journey['Cash_Pocketed']
        return journey
        
    # --- SIDEBAR ---
    with st.sidebar:
        app_mode = st.radio("Select Mode", ["🛡️ Single Asset", "⚔️ Head-to-Head"], label_visibility="collapsed")
        
        if app_mode == "🛡️ Single Asset":
            selected_ticker = st.selectbox("Select Asset", all_tickers)
            
            # FETCH ONLY THE SELECTED TICKER
            with st.spinner(f"Loading {selected_ticker}..."):
                price_df, hist_df = fetch_single_asset(selected_ticker)
            
            if price_df.empty:
                st.error("No data found on Yahoo Finance for this ticker.")
                st.stop()
            
            inception_date = price_df['Date'].min()
            use_inception = st.checkbox("🚀 Start from Inception", value=False)
            
            if use_inception:
                buy_date = inception_date
                st.markdown(f"<div style='font-size: 0.8rem; color: #8AC7DE; margin-top: -10px; margin-bottom: 10px; font-weight: bold;'>Starting: {buy_date.date()}</div>", unsafe_allow_html=True)
            else:
                default_date = pd.to_datetime("today") - pd.DateOffset(months=12)
                if default_date < inception_date: default_date = inception_date
                buy_date = st.date_input("Purchase Date", default_date)
            
            buy_date = pd.to_datetime(buy_date)
            
            date_mode = st.radio("Simulation End:", ["Hold to Present", "Sell on Specific Date"])
            end_date = pd.to_datetime(st.date_input("Sell Date", pd.to_datetime("today"))) if date_mode == "Sell on Specific Date" else pd.to_datetime("today")
                
            mode = st.radio("Input Method:", ["Share Count", "Dollar Amount"])
            use_drip = st.checkbox("🔄 Enable DRIP", value=False, help="Reinvests all dividends back into shares.")
            
            temp_journey = price_df[(price_df['Date'] >= buy_date) & (price_df['Date'] <= end_date)]
            if not temp_journey.empty:
                entry_price = temp_journey.iloc[0]['Closing Price']
                if mode == "Share Count":
                    initial_shares = st.number_input("Shares Owned", min_value=1, value=10)
                    sim_amt = initial_shares * entry_price
                else:
                    dollars = st.number_input("Amount Invested ($)", min_value=100, value=1000, step=100)
                    initial_shares = float(dollars) / entry_price if entry_price > 0 else 0
                    sim_amt = dollars
                st.info(f"Entry Price: ${entry_price:.2f}")
            else:
                st.error("No data for date range.")
                st.stop()
                
            overlay_underlyings = st.checkbox("📊 Overlay Underlying Assets", value=False, help="Adds the performance of underlying tickers (e.g., AAPL for AAPY/AAPW) to the chart and leaderboard.")
            
        else:
            selected_tickers = st.multiselect("Select Assets to Compare", all_tickers, default=all_tickers[:2] if len(all_tickers) > 1 else all_tickers)
            st.markdown("##### Common Date Range")
            buy_date = pd.to_datetime(st.date_input("Start Date", pd.to_datetime("today") - pd.DateOffset(months=12)))
            end_date = pd.to_datetime(st.date_input("End Date", pd.to_datetime("today")))
            st.markdown("##### Comparison Inputs")
            sim_amt = st.number_input("Hypothetical Investment ($)", value=10000, step=1000)
            use_drip = st.checkbox("🔄 Enable DRIP", value=False, help="Reinvests all dividends back into shares.")
            st.info(f"Leaderboard assumes ${sim_amt:,.0f} invested in each.")
            overlay_underlyings = st.checkbox("📊 Overlay Underlying Assets", value=False, help="Adds the performance of underlying tickers (e.g., AAPL for AAPY/AAPW) to the chart and leaderboard.")
            
    # ==========================================
    # MAIN LAYOUT LOGIC
    # ==========================================
    
    # --- SINGLE ASSET MODE ---
    if app_mode == "🛡️ Single Asset":
        journey = calculate_journey(selected_ticker, buy_date, end_date, initial_shares, use_drip, price_df, hist_df)
        if journey.empty:
            st.error("Journey calculation failed (empty data).")
            st.stop()
            
        initial_cap = entry_price * initial_shares
        current_market_val = journey.iloc[-1]['Market_Value']
        cash_total = journey.iloc[-1]['Cash_Pocketed']
        current_total_val = journey.iloc[-1]['True_Value']
        final_shares = journey.iloc[-1]['Shares']
        market_pl_pct = ((current_market_val - initial_cap) / initial_cap) * 100 if initial_cap != 0 else 0
        total_pl = current_total_val - initial_cap
        total_return_pct = (total_pl / initial_cap) * 100
        days_held = (end_date - buy_date).days
        annual_yield = (cash_total/initial_cap)*(365.25/days_held)*100 if days_held > 0 and initial_cap > 0 else 0

        # --- HEADER ---
        meta_row = price_df.iloc[0]
        asset_strategy = meta_row.get('Strategy', '-')
        asset_company = meta_row.get('Company', '-')
        und = meta_row.get('Underlying', '-')
        if pd.isna(und) or str(und).strip() == '' or str(und).lower() == 'nan': und = '-'
        
        und_pct = None
        if und != '-':
            df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
            if df_u_und is not None and not df_u_und.empty:
                t_price_check = df_u_und[(df_u_und['Date'] >= buy_date) & (df_u_und['Date'] <= end_date)].sort_values('Date')
                if not t_price_check.empty:
                    start_p = t_price_check.iloc[0]['Closing Price']
                    t_journey = calculate_journey(und, buy_date, end_date, 1.0, use_drip, df_u_und, df_h_und)
                    if not t_journey.empty:
                        und_pct = ((t_journey.iloc[-1]['True_Value'] - start_p) / start_p) * 100 if start_p > 0 else 0
                        
        col_head, col_meta = st.columns([1.8, 1.2])
        with col_head:
            st.markdown(f"""
                <div style="margin-top: -10px;">
                    <h1 style="font-size: 2.5rem; margin-bottom: 0px; color: #E6EDF3; line-height: 1.2;">
                        Performance Simulator : <span style="color: #8AC7DE;">{selected_ticker}</span>
                    </h1>
                    <p style="font-size: 1.1rem; color: #8AC7DE; opacity: 0.8; margin-top: -5px; margin-bottom: 10px;">
                        <b>{final_shares:.2f} shares</b> &nbsp;|&nbsp; {buy_date.date()} ➝ {end_date.date()} ({days_held} days)
                    </p>
                </div>
            """, unsafe_allow_html=True)
        with col_meta:
            if und == '-' or und_pct is None:
                meta_cols = st.columns(2)
                with meta_cols[0]:
                    st.markdown(f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;"><div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Strategy</div><div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_strategy}</div></div>', unsafe_allow_html=True)
                with meta_cols[1]:
                    st.markdown(f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;"><div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Company</div><div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_company}</div></div>', unsafe_allow_html=True)
            else:
                meta_cols = st.columns(3)
                with meta_cols[0]:
                    st.markdown(f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;"><div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Strategy</div><div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_strategy}</div></div>', unsafe_allow_html=True)
                with meta_cols[1]:
                    st.markdown(f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;"><div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Company</div><div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_company}</div></div>', unsafe_allow_html=True)
                with meta_cols[2]:
                    und_color = "#00C805" if und_pct >= 0 else "#FF4B4B"
                    symbol = "▲" if und_pct > 0 else "▼" if und_pct < 0 else ""
                    st.markdown(f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;"><div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Underlying</div><div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{und} <span style="color: {und_color}; filter: brightness(1.2);">{symbol} {und_pct:+.2f}%</span></div></div>', unsafe_allow_html=True)
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Initial Capital", f"${initial_cap:,.2f}")
        m2.metric("End Asset Value" if not use_drip else "End Value (DRIP)", f"${current_market_val:,.2f}", f"{market_pl_pct:+.2f}%")
        if use_drip:
            m3.metric("New Shares Acquired", f"{final_shares - initial_shares:.2f} Shares")
            m4.metric("Effective Yield", "N/A (Reinvested)")
        else:
            m3.metric("Dividends Collected", f"${cash_total:,.2f}")
            m4.metric("Annualized Yield", f"{annual_yield:.2f}%")
        m5.metric("True Total Value", f"${current_total_val:,.2f}", f"{total_return_pct:.2f}%")
        
        fig = go.Figure()
        bottom_y = journey['Market_Value'] if not use_drip else journey['Base_Asset_Value']
        price_color = '#8AC7DE' if journey.iloc[-1]['Closing Price'] >= journey.iloc[0]['Closing Price'] else '#FF4B4B'
        
        fig.add_trace(go.Scatter(x=journey['Date'], y=bottom_y, mode='lines', name='Asset Price', line=dict(color=price_color, width=2)))
        fig.add_trace(go.Scatter(x=journey['Date'], y=journey['True_Value'], mode='lines', name='True Value', line=dict(color='#00C805', width=3), fill='tonexty', fillcolor='rgba(0, 200, 5, 0.1)'))
        fig.add_hline(y=initial_cap, line_dash="dash", line_color="white", opacity=0.3)
        
        profit_bg = "#00C805" if total_pl >= 0 else "#FF4B4B"
        fig.add_annotation(
            x=0.02, y=0.95, xref="paper", yref="paper", text=f"PROFIT: +${total_pl:,.2f}" if total_pl >= 0 else f"LOSS: -${abs(total_pl):,.2f}", showarrow=False,
            font=dict(family="Arial Black, sans-serif", size=16, color="white"), bgcolor=profit_bg, bordercolor=profit_bg, borderpad=8, opacity=0.9, align="left"
        )
        
        if overlay_underlyings and und != '-':
            df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
            if df_u_und is not None:
                t_price_check = df_u_und[(df_u_und['Date'] >= buy_date) & (df_u_und['Date'] <= end_date)].sort_values('Date')
                if not t_price_check.empty:
                    t_journey = calculate_journey(und, buy_date, end_date, initial_cap / t_price_check.iloc[0]['Closing Price'], use_drip, df_u_und, df_h_und)
                    if not t_journey.empty:
                        fig.add_trace(go.Scatter(x=t_journey['Date'], y=t_journey['True_Value'], mode='lines', name=und, line=dict(color='#FFD700', width=2, dash='dash')))
                        
        fig.update_layout(
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=340, 
            margin=dict(l=0, r=0, t=20, b=0), 
            showlegend=False, 
            hovermode="x unified", 
            xaxis=dict(fixedrange=True), 
            yaxis=dict(fixedrange=True)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown('<div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 5px 8px; text-align: center;"><span style="color: #00C805; font-weight: 800;">💚 True Value (Total Equity)</span> &nbsp;&nbsp; <span style="color: #8AC7DE; font-weight: 800;">🔵 Price Appreciation</span> &nbsp;&nbsp; <span style="color: #FF4B4B; font-weight: 800;">🔴 Price Erosion</span></div>', unsafe_allow_html=True)
        with st.expander("View Data"): st.dataframe(journey.sort_values('Date', ascending=False), use_container_width=True)

    # --- HEAD-TO-HEAD MODE ---
    else:
        st.markdown('<div style="margin-top: -10px; margin-bottom: 20px;"><h1 style="font-size: 2.5rem; margin-bottom: 0px; color: #E6EDF3; line-height: 1.2;">⚔️ Head-to-Head <span style="color: #8AC7DE;">Comparison</span></h1></div>', unsafe_allow_html=True)
        if not selected_tickers:
            st.warning("Please select at least one asset in the sidebar.")
            st.stop()
            
        comp_data = []
        fig_comp = go.Figure()
        colors = ['#00C805', '#F59E0B', '#8AC7DE', '#FF4B4B', '#A855F7', '#EC4899', '#EAB308']
        
        with st.spinner("Fetching data for selected assets..."):
            for idx, t in enumerate(selected_tickers):
                price_df, hist_df = fetch_single_asset(t)
                if price_df.empty: continue
                
                t_price_check = price_df[(price_df['Date'] >= buy_date) & (price_df['Date'] <= end_date)].sort_values('Date')
                if t_price_check.empty: continue
                
                initial_s = sim_amt / t_price_check.iloc[0]['Closing Price']
                t_journey = calculate_journey(t, buy_date, end_date, initial_s, use_drip, price_df, hist_df)
                if t_journey.empty: continue
                
                t_journey['Total_Return_Pct'] = ((t_journey['True_Value'] - sim_amt) / sim_amt) * 100
                fig_comp.add_trace(go.Scatter(x=t_journey['Date'], y=t_journey['Total_Return_Pct'], mode='lines', name=t, line=dict(color=colors[idx % len(colors)], width=3)))
                
                f_row = t_journey.iloc[-1]
                data_row = {"Ticker": t, "Total Return": f_row['Total_Return_Pct'], "💚 Total Value": f_row['True_Value']}
                if use_drip:
                    data_row["📈 New Shares Added"] = f_row['Shares'] - initial_s
                    data_row["Yield %"] = "N/A"
                else:
                    data_row["💰 Cash Generated"] = f_row['Cash_Pocketed']
                    data_row["Yield %"] = (f_row['Cash_Pocketed'] / sim_amt) * 100
                    data_row["📉 Share Value (Remaining)"] = f_row['Market_Value']
                comp_data.append(data_row)
            
            if overlay_underlyings:
                unique_und = {df_m[df_m['Ticker'] == t].iloc[0].get('Underlying', '-') for t in selected_tickers if not df_m[df_m['Ticker'] == t].empty}
                unique_und.discard('-')
                
                overlay_colors = ['#00FFFF', '#FF69B4', '#00FF7F', '#87CEEB', '#FFA07A']
                for idx, und in enumerate(unique_und):
                    df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
                    if df_u_und is None: continue
                    t_price_check = df_u_und[(df_u_und['Date'] >= buy_date) & (df_u_und['Date'] <= end_date)].sort_values('Date')
                    if t_price_check.empty: continue
                    
                    t_journey = calculate_journey(und, buy_date, end_date, sim_amt / t_price_check.iloc[0]['Closing Price'], use_drip, df_u_und, df_h_und)
                    if t_journey.empty: continue
                    
                    t_journey['Total_Return_Pct'] = ((t_journey['True_Value'] - sim_amt) / sim_amt) * 100
                    fig_comp.add_trace(go.Scatter(x=t_journey['Date'], y=t_journey['Total_Return_Pct'], mode='lines', name=und, line=dict(color=overlay_colors[idx % len(overlay_colors)], width=2, dash='dash')))
                    
                    f_row = t_journey.iloc[-1]
                    data_row = {"Ticker": und, "Total Return": f_row['Total_Return_Pct'], "💚 Total Value": f_row['True_Value']}
                    if use_drip:
                        data_row["📈 New Shares Added"] = f_row['Shares'] - (sim_amt / t_price_check.iloc[0]['Closing Price'])
                        data_row["Yield %"] = "N/A"
                    else:
                        data_row["💰 Cash Generated"] = f_row['Cash_Pocketed']
                        data_row["Yield %"] = (f_row['Cash_Pocketed'] / sim_amt) * 100
                        data_row["📉 Share Value (Remaining)"] = f_row['Market_Value']
                    comp_data.append(data_row)
        
        fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.5, annotation_text="Break Even")
        fig_comp.update_layout(
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=400, 
            margin=dict(l=0, r=0, t=30, b=0), 
            hovermode="x unified", 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")), 
            yaxis_title="Total Return (%)", 
            xaxis=dict(fixedrange=True), 
            yaxis=dict(fixedrange=True)
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
        
        if comp_data:
            st.markdown(f"### 🏆 Leaderboard (${sim_amt:,.0f} Investment)")
            df_comp = pd.DataFrame(comp_data).sort_values("Total Return", ascending=False)
            df_comp['Total Return'] = df_comp['Total Return'].apply(lambda x: f"{x:+.2f}%")
            df_comp['💚 Total Value'] = df_comp['💚 Total Value'].apply(lambda x: f"${x:,.2f}")
            if use_drip:
                 df_comp['📈 New Shares Added'] = df_comp['📈 New Shares Added'].apply(lambda x: f"{x:.2f}")
                 st.dataframe(df_comp, column_order=["Ticker", "Total Return", "📈 New Shares Added", "💚 Total Value"], hide_index=True, use_container_width=True)
            else:
                 df_comp['Yield %'] = df_comp['Yield %'].apply(lambda x: f"{x:.2f}%")
                 df_comp['💰 Cash Generated'] = df_comp['💰 Cash Generated'].apply(lambda x: f"${x:,.2f}")
                 df_comp['📉 Share Value (Remaining)'] = df_comp['📉 Share Value (Remaining)'].apply(lambda x: f"${x:,.2f}")
                 st.dataframe(df_comp, column_order=["Ticker", "Total Return", "Yield %", "💰 Cash Generated", "📉 Share Value (Remaining)", "💚 Total Value"], hide_index=True, use_container_width=True)

# ==========================================
# 🛑 MAIN EXECUTION CONTROL
# ==========================================
def main():
    authenticated_dashboard()

if __name__ == "__main__":
    main()
