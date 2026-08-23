import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEURAL QUANT IA ⚡ | Terminal Algorítmico",
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
    .pill-stopped { background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.4); }

    section[data-testid="stSidebar"] { background-color: #060911 !important; border-right: 1px solid rgba(255, 255, 255, 0.07); }
</style>
""", unsafe_allow_html=True)

# --- HIGIENIZAÇÃO DE CHAVES DO SUPABASE ---
def get_clean_secret(key):
    val = ""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            val = str(st.secrets[key])
    except Exception:
        pass
    if not val:
        val = os.getenv(key, "")
    return val.strip().strip('"').strip("'")

supabase_url = get_clean_secret("SUPABASE_URL")
supabase_key = get_clean_secret("SUPABASE_KEY")

# Garantir formato correto da URL
if supabase_url and not supabase_url.startswith("http"):
    supabase_url = f"https://{supabase_url}"

supabase = None
db_error_msg = ""

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        db_error_msg = f"Erro na inicialização: {e}"
else:
    db_error_msg = "Chaves ausentes nos Secrets."

# --- ESTADOS PADRÃO ---
if "bot_rodando" not in st.session_state:
    st.session_state.bot_rodando = False

saldo = 0.00
equity = 0.00
lucro = 0.00
sync_status = "Pendente"

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            d = res.data[0]
            saldo = float(d.get("saldo", 0.00))
            equity = float(d.get("equity", saldo))
            lucro = float(d.get("lucro_flutuante", 0.00))
            sync_status = "Conectado"
        else:
            sync_status = "Conectado"
    except Exception as e:
        db_error_msg = f"Aguardando tabela no banco ({e})"

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("## 🤖 **NEURAL QUANT IA**")

    if sync_status == "Conectado" and not db_error_msg:
        st.markdown('<div class="status-pill pill-active">🟢 MT5 EXNESS CONECTADO</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill pill-stopped">🔴 SINC CONTA PENDENTE</div>', unsafe_allow_html=True)

    if db_error_msg:
        st.caption(f"⚠️ `{db_error_msg}`")

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ INICIAR", use_container_width=True, type="primary"):
            st.session_state.bot_rodando = True
            if supabase:
                try:
                    supabase.table("bot_config").upsert({"id": 1, "is_running": True}).execute()
                except Exception:
                    pass
            st.rerun()

    with col_btn2:
        if st.button("⏹️ PARAR", use_container_width=True):
            st.session_state.bot_rodando = False
            if supabase:
                try:
                    supabase.table("bot_config").upsert({"id": 1, "is_running": False}).execute()
                except Exception:
                    pass
            st.rerun()

    st.markdown("---")

    st.subheader("🌐 Varredura Multi-Ativos (IA)")
    ativos_selecionados = st.multiselect(
        "Ativos Monitorados em Simultâneo:",
        options=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "XAUUSD", "BTCUSD", "ETHUSD", "US30", "NAS100"],
        default=["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]
    )

    timeframe = st.select_slider("Timeframe Base:", options=["M1", "M5", "M15", "M30", "H1", "H4", "D1"], value="M5")

    st.markdown("---")
    if st.button("🔄 Atualizar Painel", use_container_width=True):
        st.rerun()

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico 🔮")
    st.caption("Varredura Multi-Ativos + Gestão de Risco Inteligente + MT5 Exness")

with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Servidor MT5:** `Exness-MT5Trial11`\n\n**Conta:** `198802214`")

st.markdown("<br>", unsafe_allow_html=True)

# --- CARTÕES DE MÉTRICAS ---
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
        <div class="metric-subtext {color_pnl}">Ordens Abertas</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    txt_status = "OPERANDO" if st.session_state.bot_rodando else "PARADO"
    cor_status = "color-green" if st.session_state.bot_rodando else "color-red"
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">⚡ Status do Robô</div>
        <div class="metric-val {cor_status}" style="font-size: 1.3rem;">{txt_status}</div>
        <div class="metric-subtext color-cyan">{len(ativos_selecionados)} Ativos Monitorados</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS PRINCIPAIS ---
tab_gestao, tab_grafico, tab_ordens, tab_ia = st.tabs([
    "⚙️ Gestão de Risco & Metas", 
    "📊 Gráficos ao Vivo", 
    "📋 Ordens MT5", 
    "🧠 Varredura IA Multi-Ativos"
])

with tab_gestao:
    st.subheader("🎯 Metas de Lucro & Limites de Parada")
    banca_base = saldo if saldo > 0 else 100.00

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        meta_diaria_usd = st.number_input("Meta de Lucro Diário ($)", min_value=1.0, value=float(round(banca_base * 0.05, 2)), step=1.0)
        st.info(f"💡 Meta de **+{(meta_diaria_usd/banca_base)*100:.2f}%** do saldo.")

    with col_m2:
        stop_diario_usd = st.number_input("Stop Loss Diário ($)", min_value=1.0, value=float(round(banca_base * 0.03, 2)), step=1.0)
        st.error(f"⚠️ Parada automática em **-${stop_diario_usd:.2f}**.")

    st.markdown("---")
    if st.button("💾 Salvar Parâmetros e Sincronizar", use_container_width=True):
        if supabase:
            try:
                supabase.table("bot_config").upsert({
                    "id": 1,
                    "ativos": ativos_selecionados,
                    "timeframe": timeframe,
                    "meta_usd": meta_diaria_usd,
                    "stop_usd": stop_diario_usd,
                    "is_running": st.session_state.bot_rodando
                }).execute()
                st.success("✅ Configurações salvas e enviadas!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

with tab_grafico:
    if ativos_selecionados:
        ativo_view = st.selectbox("Escolha o ativo para análise gráfica:", ativos_selecionados)
        tv_symbol = f"BINANCE:{ativo_view}USDT" if "BTC" in ativo_view or "ETH" in ativo_view else (f"OANDA:{ativo_view}" if "XAU" in ativo_view else f"FX:{ativo_view}")
        
        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:500px;width:100%;">
          <div id="tradingview_chart" style="height:100%;width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
              "autosize": true,
              "symbol": "{tv_symbol}",
              "interval": "5",
              "timezone": "America/Sao_Paulo",
              "theme": "dark",
              "style": "1",
              "locale": "br",
              "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_html, height=510)

with tab_ordens:
    st.subheader("📋 Histórico de Ordens Executadas")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                st.dataframe(pd.DataFrame(ordens_res.data), use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma ordem registrada.")
        except Exception:
            st.info("ℹ️ Aguardando registros da tabela 'ordens'.")

with tab_ia:
    st.subheader("🧠 Matriz de Análise IA em Tempo Real")
    dados_varredura = [{"Ativo": asset, "Timeframe": timeframe, "Sinal IA": "NEUTRO / MONITORANDO"} for asset in ativos_selecionados]
    st.table(pd.DataFrame(dados_varredura))
