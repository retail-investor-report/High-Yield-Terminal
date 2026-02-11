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
# 🔐 CONFIGURATION & SECRETS
# ==========================================
try:
    BEEHIIV_API_KEY = st.secrets["BEEHIIV_API_KEY"]
    BEEHIIV_PUB_ID = st.secrets["BEEHIIV_PUB_ID"]
except:
    # Fallback for local testing if secrets aren't set up
    BEEHIIV_API_KEY = ""
    BEEHIIV_PUB_ID = ""

LOGIN_BG_COLOR = "#1E293B"
LOGIN_TEXT_COLOR = "#E6EDF3"

# ==========================================
# 🔧 GLOBAL HELPER FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600)
def fetch_overlay_data(ticker, start_date, end_date):
    """
    Fetches historical data for underlying assets (SPY, AAPL, etc.)
    using yfinance.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # auto_adjust=False prevents double-counting dividends
        hist = ticker_obj.history(
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
            actions=True,
            auto_adjust=False
        )
        
        if hist.empty:
            return None, None
        # Format like df_unified
        df_u = hist.reset_index()[['Date', 'Close']].rename(columns={'Close': 'Closing Price'})
        df_u['Date'] = pd.to_datetime(df_u['Date']).dt.tz_localize(None)
        df_u['Ticker'] = ticker
        # Format dividends like df_history
        divs = hist[hist['Dividends'] > 0]['Dividends'].reset_index()
        
        if not divs.empty:
            df_h = divs.rename(columns={'Date': 'Date of Pay', 'Dividends': 'Amount'})
            df_h['Date of Pay'] = pd.to_datetime(df_h['Date of Pay']).dt.tz_localize(None)
            df_h['Ticker'] = ticker
        else:
            df_h = pd.DataFrame(columns=['Date of Pay', 'Amount', 'Ticker'])
        return df_u, df_h
    except Exception as e:
        # Silently fail to avoid UI clutter
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
        .stApp { 
            background-color: #0D1117; 
            color: #E6EDF3; 
        }

        /* Hide scrollbar visually on MAIN CONTENT ONLY, but keep scrolling possible */
        section[data-testid="stMain"] {
            -ms-overflow-style: none;          /* Edge/IE */
            scrollbar-width: none;             /* Firefox */
        }
        section[data-testid="stMain"]::-webkit-scrollbar {
            display: none !important;          /* Chrome/Safari/Opera */
        }

        /* Sidebar scrollbar remains visible and styled (like old version) */
        section[data-testid="stSidebar"]::-webkit-scrollbar {
            display: block !important;
            width: 6px !important;
            background: #0D1117 !important;
        }
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
            background: #30363d !important;
            border-radius: 3px !important;
        }

        /* Normal padding - prevents extreme squished/zoomed-out feeling */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }

        .element-container { 
            margin-bottom: 0.3rem !important; 
        }

        /* Small zoom/font reset to fix perceived "too zoomed in/out" issues */
        .stApp, section[data-testid="stMain"] {
            zoom: 1 !important;
            font-size: 16px !important;
        }

        /* ─────────────────────────────────────────────── */
        /* ALL YOUR ORIGINAL STYLING BELOW - UNCHANGED       */
        /* ─────────────────────────────────────────────── */

        div[data-testid="stMetric"] {
            background-color: #1E293B;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 8px 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            min-height: 80px;
            transition: transform 0.2s;
        }
        
        /* SLOT 4: Annualized Yield (Gold Highlight) */
        div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] {
            background-color: #1a2e35 !important;
            border: 1px solid #F59E0B !important;
        }
        
        /* SLOT 5: True Total Value (THE BIG ONE) */
        div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] {
            background-color: #0D1117 !important;
            border: 2px solid #00C805 !important;
            transform: scale(1.15);
            z-index: 10;
            margin-left: 10px;
        }
        div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetricValue"] div {
            font-size: 1.8rem !important;
        }
        
        /* METRIC TEXT */
        div[data-testid="stMetricLabel"] p { color: #8AC7DE !important; font-size: 0.85rem !important; font-weight: 600 !important; }
        div[data-testid="stMetricValue"] div { color: #FFFFFF !important; font-size: 1.5rem !important; font-weight: 700 !important; }
        
        /* DELTA (COLORED NUMBERS) STYLING */
        div[data-testid="stMetricDelta"] svg { transform: scale(1.2); }
        div[data-testid="stMetricDelta"] > div {
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            filter: brightness(1.2);
        }
        
        /* --- TOOLTIP ICON (The Question Mark) --- */
        [data-testid="stMetricLabel"] svg {
            fill: #E6EDF3 !important;
            opacity: 0.9 !important;
            width: 16px !important;
            height: 16px !important;
        }
        [data-testid="stMetricLabel"]:hover svg {
            fill: #F59E0B !important;
            opacity: 1.0 !important;
        }
        
        /* --- TOOLTIP POPUP BOX FIX --- */
        div[role="tooltip"] {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border: 1px solid #8AC7DE !important;
            border-radius: 6px !important;
            font-size: 0.9rem !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        }
        div[role="tooltip"] > div {
            background-color: #1E293B !important;
        }
        
        /* =========================================
           THE CALENDAR "EVERYTHING" FIX
           ========================================= */
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
        
        /* TEXT OVERRIDES */
        h1, h2, h3, h4, h5, h6, p, label { color: #E6EDF3 !important; }
        
        /* INPUTS & SELECTS GLOBAL */
        div[data-baseweb="select"] > div, div[data-testid="stDateInput"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
            background-color: #1E293B !important;
            border-color: #30363d !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            min-height: 40px !important;
        }
        input { color: #FFFFFF !important; font-weight: bold !important; }
        .stSelectbox svg, .stDateInput svg { fill: #8AC7DE !important; }
        
        /* SIDEBAR COMPACTING */
        .stSidebar .element-container { margin-top: 0rem !important; margin-bottom: 0.5rem !important; }
        .stSidebar .stSelectbox, .stSidebar .stDateInput, .stSidebar .stRadio, .stSidebar .stNumberInput { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        .stSidebar .stCheckbox label { font-weight: bold; color: #8AC7DE !important; }
        
        /* DATAFRAME FIXES */
        div[data-testid="stDataFrame"] {
            border: 1px solid #30363d;
            border-radius: 5px;
            overflow: hidden;
            color-scheme: dark;
        }
        
        /* HIDE COLUMN MENU BUTTONS & SCROLLBARS IN DATAFRAME */
        div[data-testid="stDataFrame"] div[role="columnheader"] button { display: none !important; }
        div[data-testid="stDataFrame"] div[data-testid="stVerticalBlock"] { overflow: hidden !important; }
        div[data-testid="stDataFrame"] ::-webkit-scrollbar { display: none !important; }
        
        /* C. DESKTOP LAYOUT LOCK (Min-width 1200px) */
        @media (min-width: 1200px) {
            section[data-testid="stSidebar"] {
                width: 300px !important; min-width: 300px !important; height: 100vh !important;
                position: fixed !important; top: 0 !important; left: 0 !important;
                background-color: #0D1117 !important; border-right: 1px solid #30363d !important;
                z-index: 9999 !important; transform: none !important; padding-top: 1rem !important;
            }
            section[data-testid="stSidebar"] h2 { padding-top: 0rem !important; margin-top: 0rem !important; margin-bottom: 1rem !important; }
            section[data-testid="stMain"] { margin-left: 300px !important; width: calc(100% - 300px) !important; position: relative !important; display: block !important; }
            .block-container { padding-left: 3rem !important; padding-right: 3rem !important; padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
            header[data-testid="stHeader"], button[data-testid="stSidebarCollapseBtn"], div[data-testid="collapsedControl"] { display: none !important; }
        }
        
        /* D. MOBILE LAYOUT (Max-width 1199px) */
        @media (max-width: 1199px) {
            section[data-testid="stMain"] { margin-left: 0 !important; width: 100% !important; }
            .block-container { padding-top: 4rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100vw !important; min-width: 100vw !important; }
            header[data-testid="stHeader"] { display: block !important; background-color: #0D1117 !important; z-index: 99999 !important; }
            button[data-testid*="SidebarCollapseButton"], [data-testid*="collapsedControl"] { display: block !important; color: #E6EDF3 !important; }
            
            section[data-testid="stSidebar"] {
                background-color: #0D1117 !important;
                border-right: 1px solid #30363d !important;
            }
            section[data-testid="stSidebar"] > div {
                background-color: #0D1117 !important;
            }
        }
        
        footer {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        .viewerBadge_container__1QSob {display: none !important;}
        .viewerBadge_link__1SlnQ {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    
    # --- PRECISION HYBRID DATA LOADING ---
    @st.cache_data(ttl=3600)
    def load_data():
        try:
            # 1. Load the Master (for tickers) and History (for Pay Dates)
            h_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQe4koGj386xkUGn3XXhysM-54_DIbYawunKX49C2Kt6KH9i097JDNnhbKQpRVn7WH05noFpgY3p1_e/pub?gid=970184313&single=true&output=csv"
            m_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQe4koGj386xkUGn3XXhysM-54_DIbYawunKX49C2Kt6KH9i097JDNnhbKQpRVn7WH05noFpgY3p1_e/pub?gid=618318322&single=true&output=csv"
            
            df_m = pd.read_csv(m_url)
            df_h_sheet = pd.read_csv(h_url)
            
            # Clean Master headers
            m_rename_map = {'Fund Strategy': 'Strategy', 'Asset Class': 'Strategy', 'Fund Name': 'Company', 'Name': 'Company'}
            df_m = df_m.rename(columns=m_rename_map)
            
            if 'Ticker' not in df_m.columns:
                st.error("Master sheet must have a 'Ticker' column.")
                return None, None
            tickers_to_fetch = df_m['Ticker'].dropna().astype(str).str.strip().str.upper().unique().tolist()
            
            # Clean History headers (We only care about Date and Ticker now, amount comes from YF)
            h_rename_map = {'Pay Date': 'Date of Pay', 'Payment Date': 'Date of Pay', 'Payout Date': 'Date of Pay', 'Date': 'Date of Pay'}
            df_h_sheet = df_h_sheet.rename(columns=h_rename_map)
            
            # Ensure the sheet has dates and tickers before we try to match them
            if 'Date of Pay' in df_h_sheet.columns and 'Ticker' in df_h_sheet.columns:
                df_h_sheet['Date of Pay'] = pd.to_datetime(df_h_sheet['Date of Pay']).dt.tz_localize(None)
                df_h_sheet['Ticker'] = df_h_sheet['Ticker'].astype(str).str.strip().str.upper()
                # Sort it so we can match chronologically
                df_h_sheet = df_h_sheet.sort_values(['Ticker', 'Date of Pay'])
            else:
                # If the sheet is broken, create an empty one so it doesn't crash
                df_h_sheet = pd.DataFrame(columns=['Date of Pay', 'Ticker'])

            # 2. Fetch Data from yfinance
            all_prices = []
            all_divs_yf = []
            
            progress_text = "Fetching live market & matching dividend dates..."
            my_bar = st.progress(0, text=progress_text)
            
            for i, ticker in enumerate(tickers_to_fetch):
                try:
                    percent_complete = int(((i) / len(tickers_to_fetch)) * 100)
                    my_bar.progress(percent_complete, text=f"Fetching {ticker} ({percent_complete}%)")
                    
                    t = yf.Ticker(ticker)
                    hist = t.history(period="max", auto_adjust=False)
                    
                    if not hist.empty:
                        hist = hist.reset_index()
                        
                        # Extract Prices
                        prices = hist[['Date', 'Close']].copy()
                        prices['Ticker'] = ticker
                        prices = prices.rename(columns={'Close': 'Closing Price'})
                        prices['Date'] = pd.to_datetime(prices['Date']).dt.tz_localize(None)
                        all_prices.append(prices)
                        
                        # Extract YF Dividends (These are on Ex-Dates)
                        if 'Dividends' in hist.columns:
                            divs = hist[hist['Dividends'] > 0][['Date', 'Dividends']].copy()
                            if not divs.empty:
                                divs['Ticker'] = ticker
                                divs = divs.rename(columns={'Date': 'YF_Ex_Date', 'Dividends': 'Amount'})
                                divs['YF_Ex_Date'] = pd.to_datetime(divs['YF_Ex_Date']).dt.tz_localize(None)
                                all_divs_yf.append(divs)
                                
                except Exception as e:
                    pass
                    
            my_bar.empty()
            
            # 3. Build Unified Prices
            if not all_prices:
                st.error("Failed to fetch price data.")
                return None, None
                
            df_u = pd.concat(all_prices, ignore_index=True)
            cols_to_merge = ['Ticker'] + [col for col in ['Strategy', 'Company', 'Underlying'] if col in df_m.columns]
            df_u = df_u.merge(df_m[cols_to_merge], on='Ticker', how='left')
            df_u['Closing Price'] = pd.to_numeric(df_u['Closing Price'], errors='coerce').fillna(0.0)
            
            # 4. THE MATCH-MAKER: Merge YF Amounts with Sheet Pay Dates
            if all_divs_yf:
                df_divs_yf = pd.concat(all_divs_yf, ignore_index=True)
                
                final_history = []
                
                # We have to match them ticker by ticker
                for ticker in tickers_to_fetch:
                    # Get the YF dividends for this ticker (chronological)
                    yf_ticker_divs = df_divs_yf[df_divs_yf['Ticker'] == ticker].sort_values('YF_Ex_Date')
                    
                    # Get your custom Pay Dates for this ticker (chronological)
                    sheet_ticker_dates = df_h_sheet[df_h_sheet['Ticker'] == ticker].sort_values('Date of Pay')
                    
                    # We match them up 1-to-1. 
                    for j, yf_row in enumerate(yf_ticker_divs.itertuples()):
                        amount = yf_row.Amount
                        
                        # Try to find a matching custom Pay Date
                        if j < len(sheet_ticker_dates):
                            pay_date = sheet_ticker_dates.iloc[j]['Date of Pay']
                        else:
                            # Fallback: If you haven't put the Pay Date in your sheet yet, 
                            # we just use the YF Ex-Date so the app doesn't break.
                            pay_date = yf_row.YF_Ex_Date
                            
                        final_history.append({
                            'Date of Pay': pay_date,
                            'Ticker': ticker,
                            'Amount': amount
                        })
                        
                df_h = pd.DataFrame(final_history)
            else:
                df_h = pd.DataFrame(columns=['Date of Pay', 'Amount', 'Ticker'])

            return df_u, df_h

        except Exception as e:
            st.error(f"Data loading error: {str(e)}")
            return None, None
            
    df_unified, df_history = load_data()
    if df_unified is None:
        st.stop()
        
    # --- COMPOUNDING ENGINE ---
    def calculate_journey(ticker, start_date, end_date, initial_shares, drip_enabled, unified_df, history_df):
        t_price = unified_df[unified_df['Ticker'] == ticker].sort_values('Date')
        journey = t_price[(t_price['Date'] >= start_date) & (t_price['Date'] <= end_date)].copy()
        
        if journey.empty:
            return journey
            
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
                        if reinvest_price > 0: # Check to prevent Divide by Zero
                            new_shares = payout / reinvest_price
                            current_shares += new_shares
                        journey.loc[d_date:, 'Shares'] = current_shares
                    else:
                        cum_cash += payout
                        journey.loc[d_date:, 'Cash_Pocketed'] = cum_cash
        
        journey = journey.reset_index()
        journey['Market_Value'] = journey['Closing Price'] * journey['Shares']
        journey['Base_Asset_Value'] = journey['Closing Price'] * initial_shares
        
        if drip_enabled:
            journey['True_Value'] = journey['Market_Value']
        else:
            journey['True_Value'] = journey['Market_Value'] + journey['Cash_Pocketed']
        
        return journey
        
    # --- SIDEBAR ---
    with st.sidebar:
        # Sort tickers safely
        all_tickers = sorted(df_unified['Ticker'].dropna().astype(str).unique())
        
        app_mode = st.radio("Select Mode", ["🛡️ Single Asset", "⚔️ Head-to-Head"], label_visibility="collapsed")
        
        if app_mode == "🛡️ Single Asset":
            selected_ticker = st.selectbox("Select Asset", all_tickers)
            price_df = df_unified[df_unified['Ticker'] == selected_ticker].sort_values('Date')
            
            if price_df.empty:
                st.error("No data.")
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
            if date_mode == "Sell on Specific Date":
                end_date = st.date_input("Sell Date", pd.to_datetime("today"))
                end_date = pd.to_datetime(end_date)
            else:
                end_date = pd.to_datetime("today")
                
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
                    if entry_price > 0:
                        initial_shares = float(dollars) / entry_price
                    else:
                        initial_shares = 0
                    sim_amt = dollars
                st.info(f"Entry Price: ${entry_price:.2f}")
            else:
                st.error("No data for date range.")
                st.stop()
                
            overlay_underlyings = st.checkbox("📊 Overlay Underlying Assets", value=False, help="Adds the performance of underlying tickers (e.g., AAPL for AAPY/AAPW) to the chart and leaderboard.")
            
        else:
            selected_tickers = st.multiselect("Select Assets to Compare", all_tickers, default=all_tickers[:2] if len(all_tickers) > 1 else all_tickers)
            st.markdown("##### Common Date Range")
            default_start = pd.to_datetime("today") - pd.DateOffset(months=12)
            buy_date = st.date_input("Start Date", default_start)
            buy_date = pd.to_datetime(buy_date)
            end_date = st.date_input("End Date", pd.to_datetime("today"))
            end_date = pd.to_datetime(end_date)
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
        
        journey = calculate_journey(selected_ticker, buy_date, end_date, initial_shares, use_drip, df_unified, df_history)
        
        if journey.empty:
            st.error("Journey calculation failed (empty data).")
            st.stop()
        initial_cap = entry_price * initial_shares
        current_market_val = journey.iloc[-1]['Market_Value']
        cash_total = journey.iloc[-1]['Cash_Pocketed']
        current_total_val = journey.iloc[-1]['True_Value']
        final_shares = journey.iloc[-1]['Shares']
        market_pl = current_market_val - initial_cap
        market_pl_pct = (market_pl / initial_cap) * 100 if initial_cap != 0 else 0
        total_pl = current_total_val - initial_cap
        total_return_pct = (total_pl / initial_cap) * 100
        days_held = (end_date - buy_date).days
        annual_yield = (cash_total/initial_cap)*(365.25/days_held)*100 if days_held > 0 and initial_cap > 0 else 0

        # --- HEADER ---
        try:
            meta_row = df_unified[df_unified['Ticker'] == selected_ticker].iloc[0]
            asset_strategy = meta_row.get('Strategy', '-')
            asset_company = meta_row.get('Company', '-')
            und = meta_row.get('Underlying', '-')
            if pd.isna(und) or str(und).strip() == '' or str(und).lower() == 'nan':
                und = '-'
        except:
            asset_strategy = asset_company = und = '-'
        und_pct = None
        if und != '-':
            df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
            if df_u_und is not None and not df_u_und.empty:
                t_price_check = df_u_und.sort_values('Date')
                t_price_check = t_price_check[(t_price_check['Date'] >= buy_date) & (t_price_check['Date'] <= end_date)]
                if not t_price_check.empty:
                    start_p = t_price_check.iloc[0]['Closing Price']
                    initial_s = 1.0
                    t_journey = calculate_journey(und, buy_date, end_date, initial_s, use_drip, df_u_und, df_h_und)
                    if not t_journey.empty:
                        final_true_val = t_journey.iloc[-1]['True_Value']
                        und_pct = ((final_true_val - start_p) / start_p) * 100 if start_p > 0 else 0
                        
        # HEADER - Three clean boxes using native columns
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
                # Strategy box
                with meta_cols[0]:
                    st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;">
                            <div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Strategy</div>
                            <div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_strategy}</div>
                        </div>
                    """, unsafe_allow_html=True)
                # Company box
                with meta_cols[1]:
                    st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;">
                            <div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Company</div>
                            <div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_company}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                meta_cols = st.columns(3)
                # Strategy box
                with meta_cols[0]:
                    st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;">
                            <div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Strategy</div>
                            <div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_strategy}</div>
                        </div>
                    """, unsafe_allow_html=True)
                # Company box
                with meta_cols[1]:
                    st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;">
                            <div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Company</div>
                            <div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">{asset_company}</div>
                        </div>
                    """, unsafe_allow_html=True)
                # Underlying box
                with meta_cols[2]:
                    und_color = "#00C805" if und_pct >= 0 else "#FF4B4B"
                    symbol = "▲" if und_pct > 0 else "▼" if und_pct < 0 else ""
                    st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; text-align: center; height: auto; min-height: 80px; overflow: auto;">
                            <div style="color: #8AC7DE; font-size: 0.7rem; text-transform: uppercase; white-space: normal; word-break: break-word;">Underlying</div>
                            <div style="color: white; font-size: 1.0rem; font-weight: 600; margin-top: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; hyphens: auto; line-height: 1.2; padding-bottom: 8px;">
                                {und} <span style="color: {und_color}; filter: brightness(1.2);">{symbol} {und_pct:+.2f}%</span> <span title="this is the percentage gain or loss of the underlying ticker over the timeline you have selected" style="cursor: help; color: #8AC7DE; font-size: 0.8rem;">?</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Initial Capital", f"${initial_cap:,.2f}")
        
        val_label = "End Asset Value" if not use_drip else "End Value (DRIP)"
        cash_label = "Dividends Collected" if not use_drip else "New Shares Acquired"
        
        m2.metric(val_label, f"${current_market_val:,.2f}", f"{market_pl_pct:+.2f}%")
        
        if use_drip:
            shares_gained = final_shares - initial_shares
            m3.metric(cash_label, f"{shares_gained:.2f} Shares")
            m4.metric("Effective Yield", "N/A (Reinvested)")
        else:
            m3.metric(cash_label, f"${cash_total:,.2f}")
            m4.metric("Annualized Yield", f"{annual_yield:.2f}%")
        m5.metric("True Total Value", f"${current_total_val:,.2f}", f"{total_return_pct:.2f}%")
        
        fig = go.Figure()
        bottom_y = journey['Market_Value'] if not use_drip else journey['Base_Asset_Value']
        top_y = journey['True_Value']
        price_color = '#8AC7DE' if journey.iloc[-1]['Closing Price'] >= journey.iloc[0]['Closing Price'] else '#FF4B4B'
        
        fig.add_trace(go.Scatter(
            x=journey['Date'], y=bottom_y, mode='lines', name='Asset Price',
            line=dict(color=price_color, width=2)
        ))
        fig.add_trace(go.Scatter(
            x=journey['Date'], y=top_y, mode='lines', name='True Value',
            line=dict(color='#00C805', width=3),
            fill='tonexty', fillcolor='rgba(0, 200, 5, 0.1)'
        ))
        fig.add_hline(y=initial_cap, line_dash="dash", line_color="white", opacity=0.3)
        
        profit_text = f"PROFIT: +${total_pl:,.2f}" if total_pl >= 0 else f"LOSS: -${abs(total_pl):,.2f}"
        profit_bg = "#00C805" if total_pl >= 0 else "#FF4B4B"
        fig.add_annotation(
            x=0.02, y=0.95, xref="paper", yref="paper", text=profit_text, showarrow=False,
            font=dict(family="Arial Black, sans-serif", size=16, color="white"),
            bgcolor=profit_bg, bordercolor=profit_bg, borderpad=8, opacity=0.9, align="left"
        )
        if overlay_underlyings:
            unique_underlyings = set()
            meta = df_unified[df_unified['Ticker'] == selected_ticker].iloc[0] if not df_unified[df_unified['Ticker'] == selected_ticker].empty else None
            und = meta.get('Underlying', '-') if meta is not None else '-'
            if und != '-' and und is not None and str(und).strip() != "":
                unique_underlyings.add(und)
            
            overlay_colors = ['#FFD700', '#FF69B4', '#00FF7F', '#87CEEB', '#FFA07A']
            overlay_idx = 0
            for und in unique_underlyings:
                df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
                if df_u_und is None: continue
                
                t_price_check = df_u_und.sort_values('Date')
                t_price_check = t_price_check[(t_price_check['Date'] >= buy_date) & (t_price_check['Date'] <= end_date)]
                if t_price_check.empty: continue
                
                start_p = t_price_check.iloc[0]['Closing Price']
                initial_s = initial_cap / start_p
                t_journey = calculate_journey(und, buy_date, end_date, initial_s, use_drip, df_u_und, df_h_und)
                if t_journey.empty: continue
                
                fig.add_trace(go.Scatter(
                    x=t_journey['Date'], y=t_journey['True_Value'], mode='lines', name=und,
                    line=dict(color=overlay_colors[overlay_idx % len(overlay_colors)], width=2, dash='dash')
                ))
                overlay_idx += 1
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=340, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, hovermode="x unified",
            xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("""
            <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 5px 8px; text-align: center;">
                <span style="color: #00C805; font-weight: 800;">💚 True Value (Total Equity)</span> &nbsp;&nbsp;
                <span style="color: #8AC7DE; font-weight: 800;">🔵 Price Appreciation</span> &nbsp;&nbsp;
                <span style="color: #FF4B4B; font-weight: 800;">🔴 Price Erosion</span>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Data"):
            st.dataframe(journey.sort_values('Date', ascending=False), use_container_width=True)
    # --- HEAD-TO-HEAD MODE ---
    else:
        st.markdown("""
            <div style="margin-top: -10px; margin-bottom: 20px;">
                <h1 style="font-size: 2.5rem; margin-bottom: 0px; color: #E6EDF3; line-height: 1.2;">
                    ⚔️ Head-to-Head <span style="color: #8AC7DE;">Comparison</span>
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        if not selected_tickers:
            st.warning("Please select at least one asset in the sidebar.")
            st.stop()
            
        comp_data = []
        fig_comp = go.Figure()
        colors = ['#00C805', '#F59E0B', '#8AC7DE', '#FF4B4B', '#A855F7', '#EC4899', '#EAB308']
        
        for idx, t in enumerate(selected_tickers):
            t_price_check = df_unified[df_unified['Ticker'] == t].sort_values('Date')
            t_price_check = t_price_check[(t_price_check['Date'] >= buy_date) & (t_price_check['Date'] <= end_date)]
            if t_price_check.empty: continue
            
            start_p = t_price_check.iloc[0]['Closing Price']
            initial_s = sim_amt / start_p
            t_journey = calculate_journey(t, buy_date, end_date, initial_s, use_drip, df_unified, df_history)
            if t_journey.empty: continue
            
            initial_cap = sim_amt
            t_journey['Total_Return_Pct'] = ((t_journey['True_Value'] - initial_cap) / initial_cap) * 100
            
            line_color = colors[idx % len(colors)]
            fig_comp.add_trace(go.Scatter(
                x=t_journey['Date'], y=t_journey['Total_Return_Pct'], mode='lines', name=t,
                line=dict(color=line_color, width=3)
            ))
            
            final_row = t_journey.iloc[-1]
            final_ret = final_row['Total_Return_Pct']
            end_value = final_row['Market_Value']
            cash_generated = final_row['Cash_Pocketed']
            final_total = final_row['True_Value']
            if not use_drip:
                yield_pct = (cash_generated / initial_cap) * 100
            else:
                yield_pct = 0.0
            shares_added = final_row['Shares'] - initial_s
            
            data_row = {
                "Ticker": t, "Total Return": final_ret, "💚 Total Value": final_total
            }
            if use_drip:
                data_row["📈 New Shares Added"] = shares_added
                data_row["Yield %"] = "N/A"
            else:
                data_row["💰 Cash Generated"] = cash_generated
                data_row["Yield %"] = yield_pct
                data_row["📉 Share Value (Remaining)"] = end_value
            comp_data.append(data_row)
            
        # Overlay Logic for Head-to-Head
        if overlay_underlyings:
            unique_underlyings = set()
            for t in selected_tickers:
                meta = df_unified[df_unified['Ticker'] == t].iloc[0] if not df_unified[df_unified['Ticker'] == t].empty else None
                und = meta.get('Underlying', '-') if meta is not None else '-'
                if und != '-' and und is not None and str(und).strip() != "":
                    unique_underlyings.add(und)
            
            overlay_colors = ['#00FFFF', '#FF69B4', '#00FF7F', '#87CEEB', '#FFA07A']
            overlay_idx = 0
            for und in unique_underlyings:
                df_u_und, df_h_und = fetch_overlay_data(und, buy_date, end_date)
                if df_u_und is None: continue
                
                t_price_check = df_u_und.sort_values('Date')
                t_price_check = t_price_check[(t_price_check['Date'] >= buy_date) & (t_price_check['Date'] <= end_date)]
                if t_price_check.empty: continue
                
                start_p = t_price_check.iloc[0]['Closing Price']
                initial_s = sim_amt / start_p
                t_journey = calculate_journey(und, buy_date, end_date, initial_s, use_drip, df_u_und, df_h_und)
                if t_journey.empty: continue
                
                t_journey['Total_Return_Pct'] = ((t_journey['True_Value'] - sim_amt) / sim_amt) * 100
                fig_comp.add_trace(go.Scatter(
                    x=t_journey['Date'], y=t_journey['Total_Return_Pct'], mode='lines', name=und,
                    line=dict(color=overlay_colors[overlay_idx % len(overlay_colors)], width=2, dash='dash')
                ))
                overlay_idx += 1
                
                final_row = t_journey.iloc[-1]
                data_row = {"Ticker": und, "Total Return": final_row['Total_Return_Pct'], "💚 Total Value": final_row['True_Value']}
                if use_drip:
                    data_row["📈 New Shares Added"] = final_row['Shares'] - initial_s
                    data_row["Yield %"] = "N/A"
                else:
                    data_row["💰 Cash Generated"] = final_row['Cash_Pocketed']
                    data_row["Yield %"] = (final_row['Cash_Pocketed'] / sim_amt) * 100
                    data_row["📉 Share Value (Remaining)"] = final_row['Market_Value']
                comp_data.append(data_row)
        
        fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.5, annotation_text="Break Even")
        fig_comp.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400,
            margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
            yaxis_title="Total Return (%)", xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True)
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
        
        if comp_data:
            st.markdown(f"### 🏆 Leaderboard (${sim_amt:,.0f} Investment)")
            df_comp = pd.DataFrame(comp_data).sort_values("Total Return", ascending=False)
            df_display = df_comp.copy()
            df_display['Total Return'] = df_display['Total Return'].apply(lambda x: f"{x:+.2f}%")
            df_display['💚 Total Value'] = df_display['💚 Total Value'].apply(lambda x: f"${x:,.2f}")
            
            if use_drip:
                 df_display['📈 New Shares Added'] = df_display['📈 New Shares Added'].apply(lambda x: f"{x:.2f}")
                 cols = ["Ticker", "Total Return", "📈 New Shares Added", "💚 Total Value"]
            else:
                 df_display['Yield %'] = df_display['Yield %'].apply(lambda x: f"{x:.2f}%")
                 df_display['💰 Cash Generated'] = df_display['💰 Cash Generated'].apply(lambda x: f"${x:,.2f}")
                 df_display['📉 Share Value (Remaining)'] = df_display['📉 Share Value (Remaining)'].apply(lambda x: f"${x:,.2f}")
                 cols = ["Ticker", "Total Return", "Yield %", "💰 Cash Generated", "📉 Share Value (Remaining)", "💚 Total Value"]
            st.dataframe(df_display, column_order=cols, hide_index=True, use_container_width=True)

# ==========================================
# 🛑 MAIN EXECUTION CONTROL
# ==========================================
def main():
    authenticated_dashboard()

if __name__ == "__main__":
    main()
