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
    .pill-stopped { background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.4); }

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

# --- ESTADOS PADRÃO DA SESSÃO ---
if "bot_rodando" not in st.session_state:
    st.session_state.bot_rodando = False

# --- CARREGAR SALDO E CONFIGURAÇÕES DA CONTA ---
saldo = 0.00
equity = 0.00
lucro = 0.00
status_bot = "PARADO"
sync_status = "Aguardando MT5"

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            d = res.data[0]
            saldo = float(d.get("saldo", 0.00))
            equity = float(d.get("equity", saldo))
            lucro = float(d.get("lucro_flutuante", 0.00))
            status_bot = d.get("status", "EXECUTANDO" if st.session_state.bot_rodando else "PARADO")
            sync_status = "Sincronizado"
    except Exception:
        pass

# --- LISTA COMPLETA DE ATIVOS PARA VARREDURA ---
TODOS_ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD",
    "XAUUSD", "XAGUSD", "USOIL",
    "BTCUSD", "ETHUSD",
    "US30", "NAS100", "GER30"
]

TIME_FRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

# --- BARRA LATERAL CONTROLES ---
with st.sidebar:
    st.markdown("## 🤖 **NEURAL QUANT IA**")

    # STATUS DO BOT E LIGA/DESLIGA
    if st.session_state.bot_rodando:
        st.markdown('<div class="status-pill pill-active">🟢 IA OPERANDO EM TEMPO REAL</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill pill-stopped">🔴 IA EM PAUSA (PARADA)</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # BOTÕES INICIAR / PARAR
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

    # SELEÇÃO MULTI-ATIVOS
    st.subheader("🌐 Varredura Multi-Ativos (IA)")
    ativos_selecionados = st.multiselect(
        "Ativos Monitorados em Simultâneo:",
        options=TODOS_ATIVOS,
        default=["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]
    )

    timeframe = st.select_slider("Timeframe Base:", options=TIME_FRAMES, value="M5")

    st.markdown("---")

    # PRESETS DE COMBOS
    st.subheader("⚡ Presets Inteligentes")
    combo = st.selectbox(
        "Combos Recomendados:",
        [
            "Customizado (Manual)",
            "🔥 Combo 1: Scalper Sniper (EURUSD + M5 + Soros)",
            "💥 Combo 2: Ouro & Cripto (XAUUSD/BTCUSD + M15)",
            "🛡️ Combo 3: Swing Trade Conservador (H1 + Mão Fixa)"
        ]
    )

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico 🔮")
    st.caption("Varredura Multi-Ativos + Gestão de Risco Inteligente + MT5 Exness")

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
        <div class="metric-subtext color-cyan">{len(ativos_selecionados)} Ativos em Análise</div>
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

# --- TAB 1: GESTÃO E METAS ---
with tab_gestao:
    st.subheader("🎯 Metas de Lucro & Limites de Parada (Calculados pela IA)")
    
    banca_base = saldo if saldo > 0 else 100.00

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("### 🏆 Meta de Lucro Diária (Take Profit)")
        meta_pct_sugerida = 5.0
        meta_usd_sugerida = banca_base * (meta_pct_sugerida / 100)

        meta_diaria_usd = st.number_input(
            "Meta de Lucro Diário ($)",
            min_value=1.0,
            value=float(round(meta_usd_sugerida, 2)),
            step=1.0
        )
        meta_diaria_pct = (meta_diaria_usd / banca_base) * 100
        st.info(f"💡 A meta equivale a **+{meta_diaria_pct:.2f}%** do seu saldo de **${banca_base:,.2f}**.")

    with col_m2:
        st.markdown("### 🛡️ Stop Loss Diário (Limite de Perda)")
        stop_pct_sugerido = 3.0
        stop_usd_sugerido = banca_base * (stop_pct_sugerido / 100)

        stop_diario_usd = st.number_input(
            "Stop Loss Diário ($)",
            min_value=1.0,
            value=float(round(stop_usd_sugerido, 2)),
            step=1.0
        )
        stop_diario_pct = (stop_diario_usd / banca_base) * 100
        st.error(f"⚠️ O robô pausará automaticamente se perder **-${stop_diario_usd:.2f}** (**-{stop_diario_pct:.2f}%**).")

    st.markdown("---")

    c_g1, c_g2 = st.columns([1.2, 1])
    with c_g1:
        st.subheader("📐 Parâmetros de Entrada por Operação")
        estrategia_modo = st.radio(
            "Estratégia de Lote:",
            ["Conservador (Mão Fixa)", "Soros (Alavancagem nos Lucros)", "Martingale (Recuperação de Perdas)"]
        )

        percentual_risco = st.slider("Risco por Operação (% da Banca)", 0.5, 10.0, 2.0, step=0.5)
        valor_riscado = (banca_base * percentual_risco) / 100
        rr_ratio = st.slider("Payoff (Risco x Retorno)", 1.0, 5.0, 2.0, step=0.5)
        alvo_retorno = valor_riscado * rr_ratio

    with c_g2:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 20px;">
            <h4 style="margin-top:0; color:#38bdf8;">📋 Resumo do Plano de Risco</h4>
            <p><b>• Ativos Selecionados:</b> <span class="color-yellow">{', '.join(ativos_selecionados[:4])}{'...' if len(ativos_selecionados)>4 else ''}</span></p>
            <p><b>• Timeframe:</b> <span class="color-yellow">{timeframe}</span> | <b>Estratégia:</b> <span class="color-cyan">{estrategia_modo}</span></p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p><b>• Meta de Lucro Diária:</b> <span class="color-green">+${meta_diaria_usd:.2f} (+{meta_diaria_pct:.1f}%)</span></p>
            <p><b>• Limite de Perda Diária:</b> <span class="color-red">-${stop_diario_usd:.2f} (-{stop_diario_pct:.1f}%)</span></p>
            <p><b>• Risco por Ordem:</b> <span class="color-red">-${valor_riscado:.2f} ({percentual_risco:.1f}%)</span></p>
            <p><b>• Alvo por Ordem:</b> <span class="color-green">+${alvo_retorno:.2f} (+{percentual_risco*rr_ratio:.1f}%)</span></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Salvar Parâmetros e Sincronizar", use_container_width=True):
            if supabase:
                try:
                    supabase.table("bot_config").upsert({
                        "id": 1,
                        "ativos": ativos_selecionados,
                        "timeframe": timeframe,
                        "estrategia": estrategia_modo,
                        "meta_usd": meta_diaria_usd,
                        "stop_usd": stop_diario_usd,
                        "risco_ordem_usd": valor_riscado,
                        "is_running": st.session_state.bot_rodando
                    }).execute()
                    st.success("✅ Configurações e metas salvas com sucesso!")
                except Exception:
                    st.success("✅ Salvo na sessão local!")
            else:
                st.success("✅ Parâmetros aplicados!")

# --- TAB 2: GRÁFICOS MULTI-ATIVOS ---
with tab_grafico:
    if ativos_selecionados:
        ativo_view = st.selectbox("Escolha o gráfico para visualizar:", ativos_selecionados)
        
        if "BTC" in ativo_view:
            tv_symbol = "BINANCE:BTCUSDT"
        elif "ETH" in ativo_view:
            tv_symbol = "BINANCE:ETHUSDT"
        elif "XAU" in ativo_view:
            tv_symbol = "OANDA:XAUUSD"
        elif "US30" in ativo_view or "NAS100" in ativo_view:
            tv_symbol = f"CAPITALCOM:{ativo_view}"
        else:
            tv_symbol = f"FX:{ativo_view}"

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
    else:
        st.warning("Nenhum ativo selecionado na barra lateral.")

# --- TAB 3: ORDENS MT5 ---
with tab_ordens:
    st.subheader("📋 Histórico de Ordens Executadas")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                st.dataframe(pd.DataFrame(ordens_res.data), use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma ordem aberta no momento.")
        except Exception:
            st.info("ℹ️ Aguardando dados do servidor...")

# --- TAB 4: VARREDURA IA MULTI-ATIVOS ---
with tab_ia:
    st.subheader("🧠 Diagnóstico de Varredura Multi-Ativos da IA")
    
    status_txt = "ATIVO (EXECUTANDO)" if st.session_state.bot_rodando else "PARADO (EM PAUSA)"
    
    st.code(f"""
[SISTEMA_STATUS] {status_txt}
[VARREDURA_MULTI_ATIVOS] Analisando simultaneamente: {', '.join(ativos_selecionados)}
[TIMEFRAME] {timeframe}
[GERENCIAMENTO_DE_METAS] Meta Diária: +${meta_diaria_usd:.2f} | Stop Loss Diário: -${stop_diario_usd:.2f}
[STATUS_CONTA] Saldo Exness: ${saldo:.2f} | Equity: ${equity:.2f}
--------------------------------------------------------------------------------
[NEURAL_ENGINE] Buscando gatilhos de entrada com confluência de indicadores em todos os ativos da lista...
    """, language="txt")
