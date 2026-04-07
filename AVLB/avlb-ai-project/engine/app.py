import streamlit as st
import redis
import json
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import altair as alt

# Настройка Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

st.set_page_config(
    page_title="AVLB AI | Neural Network Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- СТИЛИЗАЦИЯ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Основной фон и шрифт */
    .main {
        background-color: #0b0e11;
        font-family: 'Inter', sans-serif;
    }
    
    /* Стилизация метрик */
    .stMetric {
        background: linear-gradient(135deg, #1e222d 0%, #14171f 100%);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(0, 240, 194, 0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 240, 194, 0.4);
    }
    
    /* Заголовки */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    
    /* Скрытие стандартного хедера */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* Кастомная кнопка обновления */
    .stButton>button {
        background: linear-gradient(90deg, #9945FF 0%, #14F195 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
    }
    
    /* Стилизация статус-бара в сайдбаре */
    .status-card {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    /* Убираем эффект потускнения (opacity) при обновлении страницы */
    div[data-testid="stAppViewContainer"] {
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5000, key="datarefresh")

def fetch_from_redis():
    try:
        keys = r.keys("avlb:validator:*")
        data = []
        for k in keys:
            v = r.hgetall(k)
            if not v: continue
            metrics_raw = v.get('metrics', '{}')
            metrics = json.loads(metrics_raw) if metrics_raw else {}
            score = float(v.get('score', 0))
            
            # Добавляем "здоровье" на основе Score
            health_icon = "🟢" if score > 80 else "🟡" if score > 50 else "🔴"
            
            data.append({
                "Health": health_icon,
                "Validator": f"{v.get('pubkey', 'N/A')[:8]}...",
                "FullID": v.get('pubkey', 'N/A'),
                "Score": score,
                "Mode": v.get('mode', 'N/A'),
                "Latency": metrics.get('latency_ms', 0),
                "Sync Diff": metrics.get('sync_diff', 0),
                "Success %": metrics.get('success_rate', 0)
            })
        
        expected_columns = ["Health", "Validator", "FullID", "Score", "Mode", "Latency", "Sync Diff", "Success %"]
        if not data:
            return pd.DataFrame(columns=expected_columns)
        return pd.DataFrame(data)
    except redis.exceptions.ConnectionError:
        return pd.DataFrame()

# Инициализация Session State для стабильности интерфейса
if 'last_df' not in st.session_state:
    st.session_state.last_df = pd.DataFrame()
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = "NORMAL"

def get_stable_data():
    new_df = fetch_from_redis()
    if not new_df.empty:
        st.session_state.last_df = new_df
    
    try:
        mode = r.get("avlb:network_mode")
        if mode: st.session_state.last_mode = mode
    except:
        pass
        
    return st.session_state.last_df, st.session_state.last_mode

# --- САЙДБАР ---
st.sidebar.image("https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png", width=50)
st.sidebar.title("AVLB Control Center")
st.sidebar.markdown("---")

df, net_mode = get_stable_data()

# Гарантируем наличие колонок для отрисовки
if df.empty:
    df = pd.DataFrame(columns=["Health", "Validator", "FullID", "Score", "Mode", "Latency", "Sync Diff", "Success %"])

st.sidebar.subheader("Network State")
if net_mode == "CRITICAL":
    st.sidebar.markdown('<div class="status-card" style="background: rgba(255,75,75,0.2); border: 1px solid #ff4b4b;">🚨 CRITICAL MODE</div>', unsafe_allow_html=True)
elif net_mode == "HIGH_LOAD":
    st.sidebar.markdown('<div class="status-card" style="background: rgba(255,164,33,0.2); border: 1px solid #ffa421;">⚠️ HIGH LOAD</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="status-card" style="background: rgba(0,240,194,0.2); border: 1px solid #00f0c2;">✅ OPERATIONAL</div>', unsafe_allow_html=True)

st.sidebar.info(f"AI Sync Time: {datetime.now().strftime('%H:%M:%S')}")

# --- ОСНОВНОЙ КОНТЕНТ ---
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Validator Intelligence Engine")
    st.markdown("Потоковый анализ нейронной сетью AVLB в реальном времени")
with col_logo:
    st.markdown(f"### `v1.0.2` \n **Mode: {net_mode}**")

if not df.empty:
    df = df.sort_values(by="Score", ascending=False)
    
    # --- МЕТРИКИ ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("AVG NETWORK SCORE", f"{df['Score'].mean():.1f}")
    m_col2.metric("ELITE NODES", len(df[df['Score'] > 85]))
    m_col3.metric("AVG LATENCY", f"{df['Latency'].mean():.1f}ms")
    m_col4.metric("SYNC STATUS", f"{df['Sync Diff'].mean():.1f} slots")

    # --- ТАБЫ ДЛЯ ОРГАНИЗАЦИИ ---
    tab1, tab2 = st.tabs(["🏆 Leaderboard", "📊 Technical Analysis"])
    
    with tab1:
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("### Top Validators by Score")
            if not df.empty:
                chart = alt.Chart(df.head(10)).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                    x=alt.X('Validator', sort='-y', axis=alt.Axis(labelAngle=-45)),
                    y='Score',
                    color=alt.Color('Score', scale=alt.Scale(scheme='viridis'))
                ).properties(height=400)
                st.altair_chart(chart, width="stretch")

        with col_right:
            st.markdown("### Real-time Ledger")
            st.dataframe(
                df[['Health', 'Validator', 'Score', 'Latency']]
                .style.map(lambda x: 'color: #00f0c2' if x == '🟢' else 'color: #ff4b4b' if x == '🔴' else 'color: #ffa421', subset=['Health']),
                width="stretch", height=400
            )

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Latency vs Sync")
            st.scatter_chart(df, x='Latency', y='Sync Diff', color='Score')
        with col_b:
            st.markdown("### Success Rate Distribution")
            st.line_chart(df.set_index('Validator')['Success %'])

    # --- ПОДРОБНАЯ ТАБЛИЦА (НИЖЕ ТАБОВ) ---
    st.markdown("---")
    st.subheader("📋 Detailed System Report")
    
    def color_score(val):
        color = '#ff4b4b' if val < 40 else '#ffa421' if val < 75 else '#00f0c2'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df.style.map(color_score, subset=['Score'])
                .format({"Latency": "{:.1f} ms", "Score": "{:.2f}", "Success %": "{:.1f}%"}),
        width="stretch",
        height=400
    )
else:
    st.info("🔌 Ожидание данных от ИИ... Убедитесь, что запущен collector.py")
    st.progress(0, text="Ожидание метрик из Redis...")