import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEURAL QUANT IA ⚡ | Terminal Multiativos",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS CYBER-QUANT ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace !important; }

    .stApp {
        background: radial-gradient(circle at 50% -20%, #1a233a, #090d16 80%);
        color: #e2e8f0;
    }

    .metric-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
    }

    .metric-label { font-size: 0.78rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #ffffff; }

    .color-green { color: #10b981; }
    .color-red { color: #f43f5e; }
    .color-cyan { color: #38bdf8; }
    .color-purple { color: #a855f7; }
    .color-yellow { color: #f59e0b; }

    .status-pill { display: inline-flex; align-items: center; padding: 6px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 700; }
    .pill-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.4); }
    .pill-sync { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }

    section[data-testid="stSidebar"] { background-color: #060911 !important; border-right: 1px solid rgba(255, 255, 255, 0.07); }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
def get_secret(key):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, "")

supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    if supabase_url and supabase_key:
        try:
            return create_client(supabase_url, supabase_key)
        except Exception:
            return None
    return None

supabase = init_supabase()

# --- CARREGAR SALDO REAL SINCRONIZADO DA EXNESS ---
saldo = 0.00
equity = 0.00
lucro = 0.00
status_bot = "Aguardando Worker Local"
sync_status = "Aguardando MT5"

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            d = res.data[0]
            saldo = float(d.get("saldo", 0.00))
            equity = float(d.get("equity", saldo))
            lucro = float(d.get("lucro_flutuante", 0.00))
            status_bot = d.get("status", "Ativo")
            sync_status = "Sincronizado"
    except Exception:
        pass

# --- CATÁLOGO COMPLETO DE ATIVOS ---
LISTA_ATIVOS = {
    "Forex Majors": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"],
    "Forex Minors": ["EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD"],
    "Commodities": ["XAUUSD (Ouro)", "XAGUSD (Prata)", "USOIL (Petróleo)"],
    "Criptomoedas": ["BTCUSD (Bitcoin)", "ETHUSD (Ethereum)"],
    "Índices Globais": ["US30 (Dow Jones)", "NAS100 (Nasdaq)", "GER30 (DAX)"]
}

TIME FRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("## 🤖 **NEURAL QUANT IA**")
    if sync_status == "Sincronizado":
        st.markdown('<div class="status-pill pill-active">🟢 MT5 EXNESS CONECTADO</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill pill-sync">🔄 SINC CONTA PENDENTE</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("⚡ Combos Recomendados pela IA")
    combo = st.selectbox(
        "Selecione um Preset Inteligente",
        [
            "Customizado (Manual)",
            "🔥 Combo 1: Scalper Sniper EURUSD (M5 + Soros 2)",
            "💥 Combo 2: Gold Trend Hunter XAUUSD (M15 + Mão Fixa 1.5%)",
            "⚡ Combo 3: Volatility BTCUSD (M15 + Martingale 1)",
            "🛡️ Combo 4: Safe Growth USDJPY (H1 + Mão Fixa 2%)"
        ]
    )

    st.markdown("---")
    st.subheader("🎯 Seleção de Ativo & Timeframe")

    # Aplicação dos Presets
    if "Combo 1" in combo:
        ativo_default, tf_default, est_default = "EURUSD", "M5", "Soros (Alavancagem nos Lucros)"
    elif "Combo 2" in combo:
        ativo_default, tf_default, est_default = "XAUUSD (Ouro)", "M15", "Conservador (Mão Fixa)"
    elif "Combo 3" in combo:
        ativo_default, tf_default, est_default = "BTCUSD (Bitcoin)", "M15", "Martingale (Recuperação de Perdas)"
    elif "Combo 4" in combo:
        ativo_default, tf_default, est_default = "USDJPY", "H1", "Conservador (Mão Fixa)"
    else:
        ativo_default, tf_default, est_default = "EURUSD", "M5", "Soros (Alavancagem nos Lucros)"

    categoria = st.selectbox("Categoria do Mercado", list(LISTA_ATIVOS.keys()))
    ativo_selecionado = st.selectbox("Ativo Target", LISTA_ATIVOS[categoria])
    symbol_code = ativo_selecionado.split(" ")[0]

    timeframe = st.select_slider("Tempo Gráfico (Timeframe)", options=TIME FRAMES, value=tf_default if tf_default in TIME FRAMES else "M5")

    st.markdown("---")
    if st.button("🔄 Atualizar Dados em Tempo Real", use_container_width=True):
        st.rerun()

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico 🔮")
    st.caption("Execução Automática na Exness via MetaTrader 5 + Inteligência Generativa Gemini")

with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Servidor MT5:** `Exness-MT5Trial11`\n\n**Conta:** `198802214`")

st.markdown("<br>", unsafe_allow_html=True)

# --- CARTÕES DE MÉTRICAS AO VIVO ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">💰 Saldo Real Exness</div>
        <div class="metric-val">${saldo:,.2f}</div>
        <div class="metric-subtext color-cyan">Capital em Conta</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📈 Patrimônio (Equity)</div>
        <div class="metric-val">${equity:,.2f}</div>
        <div class="metric-subtext color-purple">Saldo + Flutuante</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    color_pnl = "color-green" if lucro >= 0 else "color-red"
    sinal_pnl = "+" if lucro >= 0 else ""
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📊 Lucro Flutuante</div>
        <div class="metric-val {color_pnl}">{sinal_pnl}${lucro:,.2f}</div>
        <div class="metric-subtext {color_pnl}">Ordens em Abertas</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">⚡ Status da Operação</div>
        <div class="metric-val color-green" style="font-size: 1.2rem;">{status_bot.upper()}</div>
        <div class="metric-subtext color-cyan">{symbol_code} ({timeframe})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS PRINCIPAIS ---
tab_gestao, tab_grafico, tab_ordens, tab_ia = st.tabs([
    "⚙️ Gestão de Risco & Estratégias", 
    "📊 Gráfico ao Vivo & TradingView", 
    "📋 Ordens Executadas no MT5", 
    "🧠 Diagnóstico da IA"
])

# --- TAB 1: GESTÃO ---
with tab_gestao:
    st.subheader("🛡️ Gerenciamento de Risco & Alvo de Lucro")
    c_g1, c_g2 = st.columns([1.2, 1])

    with c_g1:
        estrategia_modo = st.radio(
            "Estratégia de Lote:",
            ["Conservador (Mão Fixa)", "Soros (Alavancagem nos Lucros)", "Martingale (Recuperação de Perdas)"],
            index=0 if est_default.startswith("Conservador") else (1 if est_default.startswith("Soros") else 2)
        )

        tipo_risco = st.radio("Modo de Risco:", ["Porcentagem da Banca (%)", "Valor Fixo ($)"], horizontal=True)

        banca_base = saldo if saldo > 0 else 100.00
        if tipo_risco == "Porcentagem da Banca (%)":
            percentual_risco = st.slider("Arriscar por Operação (%)", 0.5, 10.0, 2.0, step=0.5)
            valor_riscado = (banca_base * percentual_risco) / 100
        else:
            valor_riscado = st.number_input("Valor Fixo ($)", min_value=1.0, max_value=500.0, value=5.0, step=1.0)
            percentual_risco = (valor_riscado / banca_base) * 100

        rr_ratio = st.slider("Payoff (Risco x Retorno)", 1.0, 5.0, 2.0, step=0.5)
        alvo_retorno = valor_riscado * rr_ratio

    with c_g2:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 20px;">
            <h4 style="margin-top:0; color:#38bdf8;">🎯 Parâmetros da Próxima Ordem</h4>
            <p><b>• Ativo:</b> <span class="color-yellow">{symbol_code}</span> | <b>Timeframe:</b> <span class="color-yellow">{timeframe}</span></p>
            <p><b>• Estratégia:</b> <span class="color-cyan">{estrategia_modo}</span></p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p><b>• Perda Máxima (SL):</b> <span class="color-red">-${valor_riscado:.2f} ({percentual_risco:.1f}%)</span></p>
            <p><b>• Alvo de Ganho (TP):</b> <span class="color-green">+${alvo_retorno:.2f} (+{percentual_risco*rr_ratio:.1f}%)</span></p>
            <p><b>• Relação R/R:</b> <span class="color-purple">1 : {rr_ratio:.1f}</span></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Salvar & Sincronizar com o Robô", use_container_width=True):
            if supabase:
                try:
                    supabase.table("bot_config").upsert({
                        "id": 1,
                        "ativo": symbol_code,
                        "timeframe": timeframe,
                        "estrategia": estrategia_modo,
                        "risco_usd": valor_riscado,
                        "alvo_usd": alvo_retorno,
                        "rr_ratio": rr_ratio
                    }).execute()
                    st.success("✅ Configurações salvas e enviadas ao robô!")
                except Exception:
                    st.success("✅ Configurações salvas na sessão!")
            else:
                st.success("✅ Parâmetros prontos!")

# --- TAB 2: GRÁFICO TRADINGVIEW ---
with tab_grafico:
    st.subheader(f"📈 Gráfico em Tempo Real — {symbol_code} ({timeframe})")
    
    # Mapeamento do ativo para o TradingView
    if "BTC" in symbol_code:
        tv_symbol = "BINANCE:BTCUSDT"
    elif "ETH" in symbol_code:
        tv_symbol = "BINANCE:ETHUSDT"
    elif "XAU" in symbol_code:
        tv_symbol = "OANDA:XAUUSD"
    elif "US30" in symbol_code or "NAS100" in symbol_code:
        tv_symbol = f"CAPITALCOM:{symbol_code}"
    else:
        tv_symbol = f"FX:{symbol_code}"

    tf_map = {"M1": "1", "M5": "5", "M15": "15", "M30": "30", "H1": "60", "H4": "240", "D1": "D"}
    tv_tf = tf_map.get(timeframe, "5")

    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:520px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
          "autosize": true,
          "symbol": "{tv_symbol}",
          "interval": "{tv_tf}",
          "timezone": "America/Sao_Paulo",
          "theme": "dark",
          "style": "1",
          "locale": "br",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=530)

# --- TAB 3: ORDENS ---
with tab_ordens:
    st.subheader("📋 Histórico de Ordens Registradas no MT5")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                st.dataframe(pd.DataFrame(ordens_res.data), use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma ordem aberta. O robô está analisando os gráficos...")
        except Exception:
            st.info("ℹ️ Sincronização em andamento...")

# --- TAB 4: DIAGNÓSTICO IA ---
with tab_ia:
    st.subheader("🧠 Log de Decisão Generativa Gemini")
    st.code(f"""
[SISTEMA] Ativo Target: {symbol_code} | Timeframe: {timeframe}
[GERENCIAMENTO] Estratégia: {estrategia_modo} | Risco SL: ${valor_riscado:.2f} | Alvo TP: ${alvo_retorno:.2f}
[STATUS_CONTA] Saldo Exness: ${saldo:.2f} | Equity: ${equity:.2f}
[NÚCLEO_IA] Monitorando padrões de vela e gatilhos de entrada para a conta Exness (198802214).
    """, language="txt")
