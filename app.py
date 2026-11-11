"""
ISSI Institutional Bandarmology Terminal (Real-Time High-Accuracy)
==================================================================
Aplikasi Streamlit Real-Time siap-pakai untuk memantau pergerakan harga 
dan aktivitas bandar/institusi pada seluruh saham syariah (ISSI) BEI.
Dilengkapi indikator MA (5, 20, 200), Volume, MACD, RSI, dan Stochastic.
"""

import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# ------------------------------------------------------------------ #
# Konfigurasi Halaman
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="ISSI Institutional Bandarmology Terminal - Real-Time",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #07090e; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    .stMetric {
        background: linear-gradient(135deg, #111827 100%, #1f2937 0%);
        border: 1px solid #374151; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white; font-weight: 600; border-radius: 8px; border: none;
        padding: 10px 24px; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2563eb 0%, #1e40af 100%);
        box-shadow: 0 6px 15px rgba(59, 130, 246, 0.5);
    }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 700; }
    .dataframe { background-color: #0f172a !important; color: #f1f5f9 !important; border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Daftar lengkap Ticker ISSI resmi (Sesuai database BEI)
FALLBACK_TICKERS = [
    "AADI", "AALI", "ABMM", "ACES", "ADCP", "ADES", "ADMG", "ADMR", "ADRO", "AGAR",
    "AGII", "AISA", "AKPI", "AKRA", "AKSI", "ALDO", "ALKA", "AMAN", "AMFG", "AMIN",
    "ANTM", "APII", "APLI", "APLN", "ARCI", "AREA", "ARII", "ARNA", "ASGR", "ASHA",
    "ASLC", "ASLI", "ASPI", "ASPR", "ASRI", "ASSA", "ATAP", "ATIC", "ATLA", "AUTO",
    "AVIA", "AWAN", "AXIO", "AYAM", "AYLS", "BABY", "BACH", "BAIK", "BALI", "BANK",
    "BAPI", "BATR", "BAUT", "BAYU", "BBRM", "BBSS", "BCIP", "BDKR", "BELI", "BELL",
    "BESS", "BEST", "BIKE", "BINO", "BIPP", "BIRD", "BISI", "BKDP", "BKSL", "BLES",
    "BLOG", "BLTA", "BLTZ", "BLUE", "BMHS", "BMSR", "BMTR", "BOAT", "BOBA", "BOGA",
    "BOLT", "BRAM", "BRIS", "BRMS", "BRNA", "BRRC", "BSBK", "BSDE", "BSML", "BSSR",
    "BTPS", "BUAH", "BUDI", "BULL", "BUMI", "BWPT", "BYAN", "CAKK", "CAMP", "CANI",
    "CARE", "CASS", "CCSI", "CEKA", "CGAS", "CHEK", "CHEM", "CINT", "CITA", "CITY",
    "CLEO", "CLPI", "CMNP", "CMPP", "CMRY", "CNMA", "COAL", "CPIN", "CPRO", "CRSN",
    "CSAP", "CSIS", "CSMI", "CSRA", "CTBN", "CTRA", "CYBR", "DADA", "DATA", "DAYA",
    "DCII", "DEFI", "DEPO", "DEWA", "DEWI", "DGIK", "DGNS", "DGWG", "DILD", "DIVA",
    "DKFT", "DMAS", "DMMX", "DMND", "DOOH", "DOSS", "DRMA", "DSFI", "DSNG", "DSSA",
    "DUTI", "DVLA", "DWGL", "DYAN", "EAST", "ECII", "EKAD", "ELIT", "ELPI", "ELSA",
    "ELTY", "EMDE", "ENAK", "ENRG", "EPAC", "EPMT", "ERAA", "ERAL", "ERTX", "ESIP",
    "ESSA", "ESTA", "EXCL", "FAST", "FASW", "FILM", "FIRE", "FISH", "FMII", "FOLK",
    "FOOD", "FORE", "FPNI", "FWCT", "GDST", "GDYR", "GEMA", "GEMS", "GGRP", "GHON",
    "GIAA", "GJTL", "GLVA", "GMTD", "GOLD", "GOLF", "GOOD", "GPRA", "GPSO", "GRIA",
    "GRPH", "GTRA", "GULA", "GUNA", "GWSA", "GZCO", "HADE", "HAIS", "HALO", "HATM",
    "HDIT", "HEAL", "HELI", "HERO", "HEXA", "HOKI", "HOMI", "HOPE", "HRTA", "HRUM",
    "HYGN", "IATA", "IBST", "ICBP", "ICON", "IDPR", "IFII", "IFSH", "IGAR", "IIKP",
    "IKAI", "IKAN", "IKBI", "IKPM", "IMPC", "INAF", "INAI", "INCF", "INCO", "INDF",
    "INDR", "INDS", "INKP", "INPP", "INPS", "INRU", "INTA", "INTP", "IOSP", "IPCC",
    "IPCM", "IPOL", "ISAT", "ITMA", "ITMG", "JARR", "JATI", "JECC", "JGLE", "JKON",
    "JPFA", "JRPT", "JSMR", "JSPT", "JTPE", "KAEF", "KARW", "KAYU", "KBAG", "KBLI",
    "KBLM", "KDTN", "KEEN", "KEJU", "KETR", "KIAS", "KINO", "KIJA", "KKGI", "KLBF",
    "KMDS", "KOBX", "KOIN", "KONI", "KOPI", "KPIG", "KRAS", "KUAS", "LABS", "LAJU",
    "LAND", "LAPD", "LCKM", "LEAD", "LIFE", "LMSH", "LPCK", "LPGI", "LPPF", "LPPS",
    "LRNA", "LSIP", "LUCK", "MABA", "MAGP", "MAIN", "MAPA", "MAPB", "MAPI", "MARK",
    "MBAP", "MBSS", "MBTO", "MCOR", "MEDC", "MEGA", "MEJA", "MENN", "MERK", "META",
    "MFMI", "MGLV", "MGMT", "MHKI", "MIDI", "MIKA", "MINA", "MIRA", "MITI", "MKNT",
    "MKPI", "MLIA", "MLPL", "MLPT", "MMIX", "MNCN", "MOLI", "MPMX", "MPPA", "MPXL",
    "MRAT", "MTDL", "MTEL", "MTMH", "MTSM", "MYOH", "MYOR", "NAIN", "NANO", "NASA",
    "NASI", "NELY", "NEST", "NFCX", "NICK", "NINE", "NOBU", "NPGF", "NSSS", "NTBK",
    "NUSA", "NZIA", "OASA", "OBMD", "OKAS", "OMRE", "PADA", "PADI", "PALM", "PAMG",
    "PANI", "PANR", "PANS", "PBID", "PBSA", "PCAR", "PDES", "PEHA", "PEVE", "PGAS",
    "PGEO", "PGLI", "PGUN", "PICO", "PJAA", "PKPK", "PLAS", "POLA", "POLI", "POLL",
    "POLY", "POOL", "PORT", "POWR", "PPRE", "PRAS", "PSAB", "PSDN", "PSGO", "PSSI",
    "PTBA", "PTDU", "PTMP", "PTPW", "PTRO", "PUDP", "PURA", "PWON", "PYFA", "RAAM",
    "RAFI", "RALD", "RANI", "RBMS", "RDTX", "REAL", "RELF", "RENT", "RICY", "RISE",
    "RMKE", "RMKO", "ROCK", "ROTI", "RSGK", "RUIS", "RUNS", "SAFE", "SAGE", "SAID",
    "SAME", "SAMF", "SAPX", "SATU", "SBAT", "SBMA", "SCCO", "SCNP", "SCMA", "SDMU",
    "SDPC", "SDRA", "SEMA", "SFAN", "SGER", "SICO", "SIDO", "SILO", "SIMP", "SKLT",
    "SKRN", "SMCB", "SMDR", "SMGR", "SMIL", "SMKM", "SMLE", "SMMT", "SMRA", "SMSM",
    "SNLK", "SOFA", "SOSS", "SRAJ", "SRIL", "SRSN", "SRTG", "SSIA", "SSTM", "STAA",
    "STAR", "STRK", "SUGI", "SULA", "SULI", "SUPR", "SURE", "SWID", "TALF",
    "TAMA", "TAPG", "TPIA", "TBLA", "TBMS", "TCID", "TCPI", "TEBE", "TECH", "TEDS",
    "TELE", "TFAS", "TFCO", "TGKA", "TGRA", "TIFA", "TINS", "TIRA", "TIRT", "TKIM",
    "TLKM", "TMAS", "TMPO", "TOBA", "TOPS", "TOWR", "TPMA", "TRAM", "TRIA", "TRIN",
    "TRIS", "TRJA", "TRON", "TRST", "TRUE", "TRUK", "TSPC", "TUGU", "TYRE", "UANG",
    "UCID", "UEMS", "UNIQ", "UNIT", "UNTR", "UNVR", "URBN", "USER", "VICI", "VIHA",
    "VINS", "VKTR", "VOKS", "VRNA", "WAPO", "WEGE", "WEHA", "WIFI", "WIKA",
    "WINS", "WIRG", "WMPP", "WMUU", "WOMF", "WOOD", "WOWS", "WSBP", "WSKT",
    "WTON", "XASA", "YELO", "YOII", "YPAS", "YYID", "ZATA", "ZEKE", "ZINC", "ZKAI",
    "ZONE", "ZYRX"
]


# ------------------------------------------------------------------ #
# Indikator Teknikal (MA, MACD, RSI, Stoch)
# ------------------------------------------------------------------ #
def calculate_technical_indicators(df):
    """Menghitung indikator teknikal MA, MACD, RSI, dan Stochastic."""
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()

    # MACD (12, 26, 9)
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # RSI (14)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Stochastic Oscillator (%K, %D)
    low_14 = df["Low"].rolling(window=14).min()
    high_14 = df["High"].rolling(window=14).max()
    df["Stoch_K"] = 100 * ((df["Close"] - low_14) / (high_14 - low_14))
    df["Stoch_D"] = df["Stoch_K"].rolling(window=3).mean()

    return df


@st.cache_data(ttl=60)
def get_market_indices():
    """Mengambil data real-time harga IHSG dan ISSI dari Yahoo Finance."""
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d", interval="1d")
        issi = yf.Ticker("^JKISSI").history(period="2d", interval="1d")

        def last_val(df):
            if df.empty:
                return (0.0, 0.0)
            chg = (
                (df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100
                if len(df) > 1 else 0.0
            )
            return (float(df["Close"].iloc[-1]), float(chg))

        return last_val(ihsg), last_val(issi)
    except Exception:
        return (0.0, 0.0), (0.0, 0.0)


@st.cache_data(ttl=86400)
def get_issi_tickers():
    """Baca daftar ticker ISSI dari Excel lokal jika ada; fallback ke daftar bawaan."""
    try:
        df_excel = pd.read_excel("issi list.xlsx")
        col_name = "ticker" if "ticker" in df_excel.columns else df_excel.columns[0]
        tickers = df_excel[col_name].astype(str).str.strip().tolist()
        cleaned = [t if t.endswith(".JK") else t + ".JK" for t in tickers if t and t.lower() != "nan"]
        if cleaned:
            return cleaned
    except Exception:
        pass
    return [t if t.endswith(".JK") else t + ".JK" for t in FALLBACK_TICKERS if t]


def _flatten(df):
    """Normalisasi kolom multi-index hasil yf.download terbaru."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=300)
def fetch_single_stock(ticker, period="120d", interval="1d"):
    """Mengambil data historis satu emiten secara aman dengan cache."""
    try:
        df = _flatten(yf.download(ticker, period=period, interval=interval, progress=False))
        if not df.empty and len(df) >= 15:
            df = calculate_technical_indicators(df)
            return ticker, df
    except Exception:
        pass
    return ticker, None


# ------------------------------------------------------------------ #
# Header & Layout
# ------------------------------------------------------------------ #
st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0;'>⚡ ISSI INSTITUTIONAL"
    " BANDARMOLOGY TERMINAL (REAL-TIME) ⚡</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #94a3b8;'>High-Accuracy Live Sharia"
    " Stock Screener & Institutional Accumulation/Distribution Tracker</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

ihsg_data, issi_data = get_market_indices()

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("📉 IHSG (Jakarta Composite)", f"{ihsg_data[0]:,.2f}", f"{ihsg_data[1]:+.2f}%")
with col_m2:
    st.metric("☪️ Indeks Saham Syariah (ISSI)", f"{issi_data[0]:,.2f}", f"{issi_data[1]:+.2f}%")
with col_m3:
    st.metric("🕒 Market Engine", "ACTIVE REAL-TIME", "High-Accuracy Feed")

st.markdown("---")

st.sidebar.markdown("<h2>📊 Terminal Menu</h2>", unsafe_allow_html=True)
menu_option = st.sidebar.radio(
    "Pilih Fitur Utama:",
    [
        "🚀 Screener Zigzag (Merah Hari Ini -> Potensi Reversal Hijau)",
        "📋 Matrix Semua Saham & Deteksi Bandar",
    ],
)


def color_coding(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return "color: #22c55e; font-weight: bold;"
        elif val < 0:
            return "color: #ef4444; font-weight: bold;"
        else:
            return "color: #eab308; font-weight: bold;"
    return ""


# ================================================================== #
# RENDER GRAFIK CANDLESTICK UTAMA DENGAN INDIKATOR LENGKAP
# ================================================================== #
def render_comprehensive_chart(emiten_code):
    st.markdown(f"### 📊 Live Candlestick Chart & Technical Indicators: {emiten_code}")
    with st.spinner(f"Memuat data historis dan indikator teknikal untuk {emiten_code}..."):
        _, df = fetch_single_stock(f"{emiten_code}.JK", period="120d", interval="1d")
        if df is not None and not df.empty:
            chart_df = df.tail(80)

            fig = make_subplots(
                rows=5, cols=1, shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.45, 0.15, 0.13, 0.13, 0.14],
                subplot_titles=(
                    f"Chart Harga & Moving Average (MA 5, 20, 200) - {emiten_code}",
                    "Volume",
                    "MACD (12, 26, 9)",
                    "RSI (14)",
                    "Stochastic Oscillator (%K, %D)"
                )
            )

            # 1. Candlestick & Moving Averages
            fig.add_trace(go.Candlestick(
                x=chart_df.index, open=chart_df["Open"], high=chart_df["High"],
                low=chart_df["Low"], close=chart_df["Close"], name="Candles"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["MA5"], line=dict(color="#38bdf8", width=1.2), name="MA 5"), row=1, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["MA20"], line=dict(color="#facc15", width=1.2), name="MA 20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["MA200"], line=dict(color="#f43f5e", width=1.5), name="MA 200"), row=1, col=1)

            # 2. Volume
            colors = ['#22c55e' if row['Close'] >= row['Open'] else '#ef4444' for index, row in chart_df.iterrows()]
            fig.add_trace(go.Bar(x=chart_df.index, y=chart_df["Volume"], marker_color=colors, name="Volume"), row=2, col=1)

            # 3. MACD
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["MACD"], line=dict(color="#38bdf8", width=1), name="MACD"), row=3, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["MACD_Signal"], line=dict(color="#f43f5e", width=1), name="Signal"), row=3, col=1)
            fig.add_trace(go.Bar(x=chart_df.index, y=chart_df["MACD_Hist"], marker_color='gray', name="Histogram"), row=3, col=1)

            # 4. RSI
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["RSI"], line=dict(color="#a855f7", width=1.2), name="RSI (14)"), row=4, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

            # 5. Stochastic
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["Stoch_K"], line=dict(color="#38bdf8", width=1), name="%K"), row=5, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["Stoch_D"], line=dict(color="#f97316", width=1), name="%D"), row=5, col=1)
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=5, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", row=5, col=1)

            fig.update_layout(
                template="plotly_dark",
                height=900,
                xaxis_rangeslider_visible=False,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Gagal mengambil data historis untuk emiten {emiten_code}.")


# ================================================================== #
# MENU 1 : Screener Zigzag (Merah Hari Ini -> Potensi Reversal Hijau)
# ================================================================== #
if menu_option == "🚀 Screener Zigzag (Merah Hari Ini -> Potensi Reversal Hijau)":
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h2>⚙️ Pengaturan Parameter</h2>", unsafe_allow_html=True)
    max_red = st.sidebar.slider("Maksimal Penurunan Hari Ini (%)", -10.0, -0.1, -1.0, 0.5) / 100
    lookback_days = st.sidebar.number_input("Periode Analisis (Hari)", 30, 120, 60, 10)

    scan_button = st.sidebar.button("🚀 Jalankan Live Scan Potensi Reversal Zigzag")

    if "selected_scan_stock" not in st.session_state:
        st.session_state["selected_scan_stock"] = None

    if scan_button:
        tickers = get_issi_tickers()
        progress_bar = st.progress(0)
        status_text = st.empty()

        matched_results = []
        total = len(tickers)
        completed = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ticker = {
                executor.submit(fetch_single_stock, t, period=f"{lookback_days}d", interval="1d"): t
                for t in tickers
            }

            for future in as_completed(future_to_ticker):
                completed += 1
                progress_bar.progress(completed / total)
                ticker = future_to_ticker[future]
                status_text.text(f"Memindai real-time [{completed}/{total}]: {ticker.replace('.JK','')}...")

                try:
                    _, df = future.result()
                    if df is not None and len(df) >= 5:
                        df["ChangePct"] = df["Close"].pct_change()
                        r_today = df["ChangePct"].iloc[-1]
                        rsi_val = df["RSI"].iloc[-1]
                        
                        last_close = df["Close"].iloc[-1]
                        vol_today = df["Volume"].iloc[-1]
                        
                        total_transaksi_rupiah = vol_today * last_close

                        if r_today <= max_red and rsi_val <= 45 and total_transaksi_rupiah >= 5_000_000_000:
                            change = r_today * 100
                            matched_results.append({
                                "Emiten": ticker.replace(".JK", ""),
                                "Harga Terakhir": f"{int(round(last_close)):,}",
                                "Return (%)": change,
                                "RSI": round(rsi_val, 1),
                                "Nilai Transaksi (Rp)": total_transaksi_rupiah,
                                "Volume Saham": f"{int(vol_today):,}",
                            })
                except Exception:
                    continue

        progress_bar.empty()
        status_text.empty()
        st.session_state["scan_results"] = matched_results
        if matched_results:
            st.session_state["selected_scan_stock"] = matched_results[0]["Emiten"]
        else:
            st.session_state["selected_scan_stock"] = None

    st.markdown("<h2>🎯 Hasil Live Scan Screener Zigzag (Volume > 5 Miliar)</h2>", unsafe_allow_html=True)

    # Pengecekan aman agar tidak terjadi KeyError jika hasil scan kosong
    if "scan_results" in st.session_state and st.session_state["scan_results"]:
        res_df = pd.DataFrame(st.session_state["scan_results"])
        
        if not res_df.empty and "Nilai Transaksi (Rp)" in res_df.columns:
            res_df["Nilai Transaksi"] = res_df["Nilai Transaksi (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
            
            st.success(f"Ditemukan **{len(res_df)} emiten** dengan nilai transaksi di atas **Rp 5 Miliar** yang berpotensi reversal!")
            st.dataframe(
                res_df[["Emiten", "Harga Terakhir", "Return (%)", "RSI", "Nilai Transaksi", "Volume Saham"]]
                .style.map(color_coding, subset=["Return (%)"]),
                use_container_width=True,
            )

            st.markdown("---")
            emiten_list = [item["Emiten"] for item in st.session_state["scan_results"]]
            
            def update_selected_stock():
                st.session_state["selected_scan_stock"] = st.session_state["stock_selectbox_key"]

            selected_emiten = st.selectbox(
                "👉 Pilih Nama Saham untuk Membuka Chart Candlestick Lengkap:",
                emiten_list,
                index=emiten_list.index(st.session_state["selected_scan_stock"]) if st.session_state["selected_scan_stock"] in emiten_list else 0,
                key="stock_selectbox_key",
                on_change=update_selected_stock
            )

            if st.session_state["selected_scan_stock"]:
                render_comprehensive_chart(st.session_state["selected_scan_stock"])
        else:
            st.warning("Tidak ada data emiten yang valid untuk ditampilkan.")
    else:
        st.info("👈 Klik tombol di sidebar untuk mulai memindai potensi reversal saham dengan volume > 5 Miliar.")

# ================================================================== #
# MENU 2 : Matrix & Deteksi Bandar Real-Time (Filter Volume > 5 Milyar)
# ================================================================== #
elif menu_option == "📋 Matrix Semua Saham & Deteksi Bandar":
    st.markdown("<h2>📋 Live Matrix & Analisis Bandarmology (Volume > 5 Miliar)</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #94a3b8;'>Menampilkan hanya saham-saham dengan nilai transaksi/volume > Rp 5 Miliar disertai analisis akumulasi institusi.</p>",
        unsafe_allow_html=True,
    )

    load_all_btn = st.button("🔄 Muat Analisis Real-Time (Filter > 5 Miliar)")

    if "matrix_results" not in st.session_state:
        st.session_state["matrix_results"] = None

    if load_all_btn:
        tickers = get_issi_tickers()
        progress_bar = st.progress(0)
        status_text = st.empty()

        matrix_data = []
        total = len(tickers)
        completed = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ticker = {
                executor.submit(fetch_single_stock, t, period="30d", interval="1d"): t
                for t in tickers
            }

            for future in as_completed(future_to_ticker):
                completed += 1
                progress_bar.progress(completed / total)
                ticker = future_to_ticker[future]
                status_text.text(f"Analisis bandar real-time [{completed}/{total}]: {ticker.replace('.JK','')}...")

                try:
                    _, df = future.result()
                    if df is not None and len(df) >= 2:
                        close_today, close_prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
                        high_today, low_today = df["High"].iloc[-1], df["Low"].iloc[-1]
                        vol_today = df["Volume"].iloc[-1]

                        total_transaksi_rupiah = vol_today * close_today

                        if total_transaksi_rupiah >= 5_000_000_000:
                            change_pct = (close_today - close_prev) / close_prev * 100
                            range_price = high_today - low_today if high_today != low_today else 1
                            close_position = (close_today - low_today) / range_price

                            if change_pct > 0:
                                if close_position > 0.7 and vol_today > 0:
                                    bandar_status = "🟢 Markup / Akumulasi Institusi Kuat"
                                    action_signal = "POTENSI LANJUT NAIK"
                                else:
                                    bandar_status = "🟡 Penguatan Wajar / Profit Taking Terbatas"
                                    action_signal = "BERTAHAN / HOLD"
                            elif change_pct < 0:
                                if close_position < 0.3 and vol_today > 0:
                                    bandar_status = "🔴 Tekanan Distribusi Bandar Aktif"
                                    action_signal = "LANJUT TURUN"
                                else:
                                    bandar_status = "🟢 Hidden Accumulation / Serok Bawah (Reversal)"
                                    action_signal = "POTENSI REVERSAL"
                            else:
                                bandar_status = "⚪ Sideways / Konsolidasi Tanpa Arah Jelas"
                                action_signal = "WAIT AND SEE"

                            matrix_data.append({
                                "Emiten": ticker.replace(".JK", ""),
                                "Harga (Rp)": f"{int(round(close_today)):,}",
                                "Return (%)": change_pct,
                                "RSI": round(df["RSI"].iloc[-1], 1),
                                "Nilai Transaksi (Rp)": total_transaksi_rupiah,
                                "Volume Saham": f"{int(vol_today):,}",
                                "Analisis Bandarmology": bandar_status,
                                "Sinyal Potensial": action_signal,
                            })
                except Exception:
                    continue

        progress_bar.empty()
        status_text.empty()
        st.session_state["matrix_results"] = matrix_data

    if st.session_state["matrix_results"]:
        matrix_df = pd.DataFrame(st.session_state["matrix_results"])
        if not matrix_df.empty and "Nilai Transaksi (Rp)" in matrix_df.columns:
            matrix_df["Nilai Transaksi"] = matrix_df["Nilai Transaksi (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
            
            st.success(f"Berhasil menyaring dan menganalisis **{len(matrix_df)} emiten** dengan volume > Rp 5 Miliar!")
            st.dataframe(
                matrix_df[
                    ["Emiten", "Harga (Rp)", "Return (%)", "RSI", "Nilai Transaksi",
                     "Analisis Bandarmology", "Sinyal Potensial"]
                ].style.map(color_coding, subset=["Return (%)"]),
                use_container_width=True,
            )

            st.markdown("---")
            matrix_emiten_list = matrix_df["Emiten"].tolist()
            
            selected_matrix_emiten = st.selectbox(
                "👉 Pilih Nama Saham dari Matrix untuk Melihat Grafik Candlestick:",
                matrix_emiten_list,
                key="matrix_selectbox_key"
            )
            if selected_matrix_emiten:
                render_comprehensive_chart(selected_matrix_emiten)
    else:
        st.info("👆 Klik tombol di atas untuk memuat matriks live berkecepatan tinggi.")
