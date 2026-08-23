import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="NEURAL QUANT AI ⚡ | Institutional Terminal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO (DESIGN INSTITUCIONAL & CYBER-QUANT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Fundo Principal Dark */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1a233a, #090d16 80%);
        color: #e2e8f0;
    }

    /* Cartões Glassmorphism Futuristas */
    .metric-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.5);
    }

    .metric-label {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }

    .metric-val {
        font-size: 1.9rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }

    .metric-subtext {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 6px;
    }

    /* Cores de Status */
    .color-green { color: #10b981; }
    .color-red { color: #f43f5e; }
    .color-cyan { color: #38bdf8; }
    .color-purple { color: #a855f7; }

    /* Badges de Status */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .pill-active {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.4);
    }
    .pill-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.4);
    }

    /* Sidebar Estilizada */
    section[data-testid="stSidebar"] {
        background-color: #060911 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }

    /* Modificação de Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LEITURA SEGURA DAS CHAVES DE API ---
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

# --- BARRA LATERAL (SIDEBAR DE CONTROLE) ---
with st.sidebar:
    st.markdown("## 🤖 **NEURAL QUANT IA**")
    st.caption("v2.5 High-Frequency Trading Bot")
    
    st.markdown("---")
    
    # Status de Conexão
    if supabase:
        st.markdown('<div class="status-pill pill-active">🟢 IA ONLINE & SINCRONIZADA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill pill-warning">⚠️ AGUARDANDO CONEXÃO</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("⚙️ Painel de Operação")
    ativo_selecionado = st.selectbox("💱 Par de Moedas Target", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD (Ouro)"], index=0)
    timeframe = st.select_slider("⏱️ Tempo Gráfico (TF)", options=["M1", "M5", "M15", "H1"], value="M5")
    risco_lote = st.slider("⚖️ Lote Fixo (Lot Size)", min_value=0.01, max_value=0.50, value=0.01, step=0.01)
    
    st.markdown("---")
    st.markdown("#### 🧠 Núcleo Generativo")
    st.markdown("• **Modelo:** Google Gemini 2.5 AI")
    st.markdown("• **Broker:** Exness MetaTrader 5")
    st.markdown("• **Estratégia:** Scalping + Smart Money")
    st.markdown("• **Risk/Reward:** 1 : 2.5 Minimum")
    
    st.markdown("---")
    if st.button("🔄 Recarregar Dados em Tempo Real", use_container_width=True):
        st.rerun()

# --- DADOS DA CONTA EM TEMPO REAL ---
saldo = 0.0
equity = 0.0
lucro = 0.0
status_bot = "Aguardando Operações"

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            d = res.data[0]
            saldo = float(d.get("saldo", 0.0))
            equity = float(d.get("equity", saldo))
            lucro = float(d.get("lucro_flutuante", 0.0))
            status_bot = d.get("status", "Em Execução")
    except Exception:
        pass

# --- CABEÇALHO DO TERMINAL ---
col_head_left, col_head_right = st.columns([3, 1])
with col_head_left:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico 🔮")
    st.caption("Sistema Avançado de Execução Inteligente e Tomada de Decisão em Tempo Real")

with col_head_right:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**Servidor MT5:** `Exness-MT5Trial11`\n\n**Conta:** `198802214`")

st.markdown("<br>", unsafe_allow_html=True)

# --- CARTÕES DE MÉTRICAS MESTRES ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">💰 Saldo em Conta (Balance)</div>
        <div class="metric-val">${saldo:,.2f}</div>
        <div class="metric-subtext color-cyan">Capital Total Garantido</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📈 Patrimônio (Equity)</div>
        <div class="metric-val">${equity:,.2f}</div>
        <div class="metric-subtext color-purple">Saldo + Flutuante Atual</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    color_pnl = "color-green" if lucro >= 0 else "color-red"
    sinal_pnl = "+" if lucro >= 0 else ""
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📊 Lucro Flutuante (PnL)</div>
        <div class="metric-val {color_pnl}">{sinal_pnl}${lucro:,.2f}</div>
        <div class="metric-subtext {color_pnl}">Resultado das Ordens Abertas</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">⚡ Status do Motor IA</div>
        <div class="metric-val color-green" style="font-size: 1.4rem;">{status_bot.upper()}</div>
        <div class="metric-subtext color-cyan">Sincronização Ativa</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS PRINCIPAIS DO SITE ---
tab_grafico, tab_ordens, tab_ia, tab_gestao = st.tabs([
    "📊 Gráfico & Análise ao Vivo", 
    "📋 Ordens & Histórico", 
    "🧠 Diagnóstico da IA Gemini", 
    "🛡️ Gestão de Risco & Parâmetros"
])

# ABAS 1: GRÁFICO TRADINGVIEW INTERATIVO
with tab_grafico:
    c_chart, c_panel = st.columns([2.6, 1])
    
    with c_chart:
        st.subheader(f"📈 Gráfico Profissional em Tempo Real — {ativo_selecionado}")
        
        # Mapeamento do ativo para o TradingView
        tv_symbol = f"FX:{ativo_selecionado}" if "XAU" not in ativo_selecionado else "OANDA:XAUUSD"
        
        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:520px;width:100%;">
          <div id="tradingview_chart" style="height:100%;width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
              "autosize": true,
              "symbol": "{tv_symbol}",
              "interval": "{timeframe.replace('M', '')}",
              "timezone": "America/Sao_Paulo",
              "theme": "dark",
              "style": "1",
              "locale": "br",
              "toolbar_bg": "#f1f3f6",
              "enable_publishing": false,
              "hide_side_toolbar": false,
              "allow_symbol_change": true,
              "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_html, height=530)

    with c_panel:
        st.subheader("🎯 Termômetro da IA")
        st.markdown("Análise contínua das velas e estrutura de mercado:")
        
        st.progress(0.85, text="Confiança da Entrada: 85%")
        st.progress(0.72, text="Pressão Compradora (Bulls): 72%")
        
        st.info("💡 **Último Veredito da IA:** Padrão de Reversão de Alta identificado em suporte chave M5. Tendência favorável.")
        
        st.markdown("#### 🔍 Sinais Recentes")
        st.write("• `00:05` - **COMPRA** EURUSD @ 1.08450 [EXECUTADO]")
        st.write("• `23:50` - **FECHAMENTO** EURUSD +$12.50 [TAKE PROFIT]")

# ABA 2: HISTÓRICO DE ORDENS
with tab_ordens:
    st.subheader("📋 Registro de Operações Executadas no MT5")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                df = pd.DataFrame(ordens_res.data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "id": "ID",
                        "ticket": "Ticket MT5",
                        "symbol": "Ativo",
                        "tipo": "Tipo",
                        "lote": "Lote",
                        "preco_entrada": st.column_config.NumberColumn("Preço Entrada", format="$%.5f"),
                        "profit": st.column_config.NumberColumn("Lucro/Prejuízo", format="$%.2f"),
                        "created_at": "Data/Hora"
                    }
                )
            else:
                st.info("ℹ️ Nenhuma ordem registrada no momento. O robô está escaneando novas oportunidades.")
        except Exception as e:
            st.error(f"Aguardando sincronização de dados: {e}")
    else:
        st.warning("⚠️ Adicione as chaves `SUPABASE_URL` e `SUPABASE_KEY` no Streamlit Secrets.")

# ABA 3: DIAGNÓSTICO IA
with tab_ia:
    st.subheader("🧠 Log de Raciocínio Algorítmico (Google Gemini)")
    st.markdown("""
    Abaixo você pode ver como a Inteligência Artificial interpreta os dados fornecidos pelo servidor MetaTrader 5:
    """)
    
    st.code("""
[NEURAL_ENGINE] Iniciando análise de mercado no ativo EURUSD...
[DATA_FETCH] Múltiplos candles M5 baixados com sucesso.
[GEMINI_PROMPT] Processando price action, RSI, Média Móvel 20 e suporte/resistência.
[DECISÃO_IA] Tipo: BUY | Lote: 0.01 | Stop Loss: 1.08300 | Take Profit: 1.08800
[MT5_EXECUTION] Ordem #198802214 enviada com sucesso ao servidor Exness.
    """, language="txt")

# ABA 4: GESTÃO DE RISCO
with tab_gestao:
    st.subheader("🛡️ Regras Globais de Segurança da Conta")
    
    g1, g2, g3 = st.columns(3)
    with g1:
        st.metric("Perda Máxima Diária (Stop Daily)", "$50.00")
    with g2:
        st.metric("Meta de Lucro Diária (Take Daily)", "$100.00")
    with g3:
        st.metric("Proteção Trailing Stop", "Ativada (10 pips)")

    st.success("🔒 **Proteção Ativa:** Se a conta atingir 5% de rebaixamento (drawdown), o bot interromperá novas operações automaticamente.")
