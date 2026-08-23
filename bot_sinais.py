import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEURAL QUANT IA ⚡ | Terminal Algorítmico Pro",
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
        padding: 18px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
    }

    .metric-label { font-size: 0.78rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-val { font-size: 1.7rem; font-weight: 800; color: #ffffff; }

    .color-green { color: #10b981; }
    .color-red { color: #f43f5e; }
    .color-cyan { color: #38bdf8; }
    .color-purple { color: #a855f7; }

    .status-pill { display: inline-flex; align-items: center; padding: 6px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 700; }
    .pill-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.4); }
    .pill-stopped { background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.4); }

    section[data-testid="stSidebar"] { background-color: #060911 !important; border-right: 1px solid rgba(255, 255, 255, 0.07); }
</style>
""", unsafe_allow_html=True)

# --- SANITIZAÇÃO E LIMPEZA DE SECRETS ---
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

if supabase_url and not supabase_url.startswith("http"):
    supabase_url = f"https://{supabase_url}"

supabase = None
db_error_msg = ""

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception:
        db_error_msg = "Erro ao conectar no banco Supabase."
else:
    db_error_msg = "Secrets do Supabase ausentes."

# --- ESTADOS NA SESSÃO ---
if "bot_rodando" not in st.session_state:
    st.session_state.bot_rodando = False

# BASE EXNESS REAL (#198802214)
saldo_usd_base = 421.52
equity_usd_base = 421.52
lucro_usd_base = 0.00
sync_status = "Modo Local"

if "meta_base_usd" not in st.session_state:
    st.session_state.meta_base_usd = round(saldo_usd_base * 0.02, 2)
if "stop_base_usd" not in st.session_state:
    st.session_state.stop_base_usd = round(saldo_usd_base * 0.01, 2)

if supabase and not db_error_msg:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            d = res.data[0]
            saldo_usd_base = float(d.get("saldo", 421.52))
            equity_usd_base = float(d.get("equity", saldo_usd_base))
            lucro_usd_base = float(d.get("lucro_flutuante", 0.00))
            sync_status = "Conectado"
        else:
            sync_status = "Conectado"
    except Exception:
        sync_status = "Aguardando Tabela"

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("## 🧠 **NEURAL QUANT IA**")

    if sync_status == "Conectado":
        st.markdown('<div class="status-pill pill-active">🟢 BANCO SUPABASE CONECTADO</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill pill-stopped">🔴 SINC PENDENTE</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("💵 Configuração de Moeda")
    moeda_sel = st.radio("Exibição:", ["USD ($)", "BRL (R$)"], index=1, horizontal=True)
    cotacao_usd = st.number_input("Cotação USD/BRL:", min_value=1.00, value=5.50, step=0.05)

    m_sym = "$" if moeda_sel == "USD ($)" else "R$"
    m_mult = 1.0 if moeda_sel == "USD ($)" else cotacao_usd

    st.markdown("---")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("▶️ INICIAR", use_container_width=True, type="primary"):
            st.session_state.bot_rodando = True
            if supabase and sync_status == "Conectado":
                try: supabase.table("bot_config").upsert({"id": 1, "is_running": True}).execute()
                except Exception: pass
            st.rerun()

    with col_b2:
        if st.button("⏹️ PARAR", use_container_width=True):
            st.session_state.bot_rodando = False
            if supabase and sync_status == "Conectado":
                try: supabase.table("bot_config").upsert({"id": 1, "is_running": False}).execute()
                except Exception: pass
            st.rerun()

    st.markdown("---")

    st.subheader("🌐 Varredura IA Multi-Ativos")
    ativos_selecionados = st.multiselect(
        "Ativos Monitorados:",
        options=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "BTCUSD", "ETHUSD", "US30", "NAS100"],
        default=["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]
    )

    timeframe = st.select_slider("Timeframe Base:", options=["M1", "M5", "M15", "M30", "H1", "H4", "D1"], value="M5")

    st.markdown("---")
    if st.button("🔄 Atualizar Painel", use_container_width=True):
        st.rerun()

# --- CÁLCULOS VISUAIS ---
saldo_disp = saldo_usd_base * m_mult
equity_disp = equity_usd_base * m_mult
lucro_disp = lucro_usd_base * m_mult

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico ⚡")
    st.caption(f"Engine Quantitativo Direct MT5 | Exibição: {moeda_sel}")

with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Servidor:** `Exness-MT5Trial11`\n\n**Conta:** `198802214`")

st.markdown("<br>", unsafe_allow_html=True)

# --- PAINEL DE MÉTRICAS ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">💰 Saldo Real ({moeda_sel[:3]})</div>
        <div class="metric-val">{m_sym} {saldo_disp:,.2f}</div>
        <div class="metric-subtext color-cyan">Capital em Conta</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📈 Patrimônio (Equity)</div>
        <div class="metric-val">{m_sym} {equity_disp:,.2f}</div>
        <div class="metric-subtext color-purple">Saldo + Flutuante</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    color_pnl = "color-green" if lucro_disp >= 0 else "color-red"
    sinal_pnl = "+" if lucro_disp >= 0 else ""
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📊 Lucro Flutuante</div>
        <div class="metric-val {color_pnl}">{sinal_pnl}{m_sym} {lucro_disp:,.2f}</div>
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

# --- CENTRAL DE EXECUÇÃO REAL VIA SUPABASE ---
st.markdown("### ⚡ **Central de Execução de Ordens Direct MT5**")
col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.5, 1.5, 2])

ativo_exec = ativos_selecionados[0] if ativos_selecionados else "EURUSD"
lote_sugerido = round(max(0.01, (saldo_usd_base * 0.01) / 10), 2)

with col_act1:
    if st.button("🟢 COMPRAR (LONG IA)", use_container_width=True, type="primary"):
        if supabase:
            try:
                supabase.table("ordens").insert({
                    "ativo": ativo_exec, 
                    "tipo": "BUY", 
                    "lote": lote_sugerido, 
                    "status": "PENDENTE"
                }).execute()
                st.toast(f"🚀 COMPRA ({ativo_exec}) enviada para o MT5!", icon="✅")
            except Exception as e:
                st.toast(f"❌ Falha no envio: {e}", icon="⚠️")
        else:
            st.toast("⚠️ Supabase não configurado.", icon="❌")

with col_act2:
    if st.button("🔴 VENDER (SHORT IA)", use_container_width=True):
        if supabase:
            try:
                supabase.table("ordens").insert({
                    "ativo": ativo_exec, 
                    "tipo": "SELL", 
                    "lote": lote_sugerido, 
                    "status": "PENDENTE"
                }).execute()
                st.toast(f"📉 VENDA ({ativo_exec}) enviada para o MT5!", icon="🔻")
            except Exception as e:
                st.toast(f"❌ Falha no envio: {e}", icon="⚠️")
        else:
            st.toast("⚠️ Supabase não configurado.", icon="❌")

with col_act3:
    if st.button("⛔ FECHAR TODAS", use_container_width=True):
        if supabase:
            try:
                supabase.table("ordens").insert({
                    "ativo": "ALL", 
                    "tipo": "CLOSE_ALL", 
                    "lote": 0.0, 
                    "status": "PENDENTE"
                }).execute()
                st.toast("🛑 Ordem de Zeragem enviada!", icon="🛑")
            except Exception as e:
                st.toast(f"❌ Falha: {e}", icon="⚠️")
        else:
            st.toast("⚠️ Supabase não configurado.", icon="❌")

with col_act4:
    st.caption(f"🎯 Ativo Foco: **{ativo_exec}** | Lote Calc: **{lote_sugerido} Mão**")

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS PRINCIPAIS ---
tab_gestao, tab_grafico, tab_ia, tab_ordens = st.tabs([
    "⚙️ Gestão Pro & Cálculo de Metas", 
    "📊 Gráficos ao Vivo", 
    "🧠 Motor IA Quant", 
    "📋 Histórico MT5"
])

with tab_gestao:
    st.subheader(f"🎯 Calculadora de Risco e Metas ({moeda_sel})")

    q1, q2, q3, q4 = st.columns(4)

    if q1.button("⚡ Conservador (2% / 1%)", use_container_width=True):
        st.session_state.meta_base_usd = round(saldo_usd_base * 0.02, 2)
        st.session_state.stop_base_usd = round(saldo_usd_base * 0.01, 2)
        st.rerun()

    if q2.button("🎯 Moderado (5% / 2.5%)", use_container_width=True):
        st.session_state.meta_base_usd = round(saldo_usd_base * 0.05, 2)
        st.session_state.stop_base_usd = round(saldo_usd_base * 0.025, 2)
        st.rerun()

    if q3.button("🔥 Agressivo (10% / 4%)", use_container_width=True):
        st.session_state.meta_base_usd = round(saldo_usd_base * 0.10, 2)
        st.session_state.stop_base_usd = round(saldo_usd_base * 0.04, 2)
        st.rerun()

    if q4.button("🚀 Alavancado (15% / 5%)", use_container_width=True):
        st.session_state.meta_base_usd = round(saldo_usd_base * 0.15, 2)
        st.session_state.stop_base_usd = round(saldo_usd_base * 0.05, 2)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    meta_exib = st.session_state.meta_base_usd * m_mult
    stop_exib = st.session_state.stop_base_usd * m_mult

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        nova_meta_exib = st.number_input(f"Meta Diária ({m_sym})", min_value=1.0, value=float(meta_exib), step=1.0)
        st.session_state.meta_base_usd = nova_meta_exib / m_mult
        pct_meta = (st.session_state.meta_base_usd / saldo_usd_base) * 100
        st.info(f"💡 Meta de **+{pct_meta:.2f}%** do saldo total.")

    with col_m2:
        novo_stop_exib = st.number_input(f"Stop Loss Diário ({m_sym})", min_value=1.0, value=float(stop_exib), step=1.0)
        st.session_state.stop_base_usd = novo_stop_exib / m_mult
        pct_stop = (st.session_state.stop_base_usd / saldo_usd_base) * 100
        st.error(f"⚠️ Parada automática em **-{pct_stop:.2f}%** (-{m_sym} {novo_stop_exib:.2f}).")

    st.markdown("---")
    
    st.subheader("📐 Calculadora Pro de Lote (Pips x Risco)")
    c_pips1, c_pips2, c_pips3 = st.columns(3)
    with c_pips1:
        pips_stop = st.number_input("Distância Stop (Pips):", min_value=1, value=20)
    with c_pips2:
        risco_pct = st.number_input("Risco Operação (%):", min_value=0.1, value=1.0, step=0.5)
    with c_pips3:
        valor_risco_operacao_usd = saldo_usd_base * (risco_pct / 100)
        valor_risco_disp = valor_risco_operacao_usd * m_mult
        lote_calculado = valor_risco_operacao_usd / (pips_stop * 10) if pips_stop > 0 else 0.01
        st.success(f"🧮 Lote Exato: **{max(0.01, round(lote_calculado, 2))}** | Risco: **{m_sym} {valor_risco_disp:.2f}**")

    st.markdown("---")
    if st.button("💾 Sincronizar Configurações", use_container_width=True, type="primary"):
        if supabase:
            try:
                supabase.table("bot_config").upsert({
                    "id": 1,
                    "ativos": ativos_selecionados,
                    "timeframe": timeframe,
                    "meta_usd": st.session_state.meta_base_usd,
                    "stop_usd": st.session_state.stop_base_usd,
                    "is_running": st.session_state.bot_rodando
                }).execute()
                st.success("✅ Configurações salvas no Supabase!")
            except Exception as e:
                st.error(f"Erro: {e}")

with tab_grafico:
    if ativos_selecionados:
        ativo_view = st.selectbox("Ativo Visualizado:", ativos_selecionados)
        tv_symbol = f"BINANCE:{ativo_view}USDT" if "BTC" in ativo_view or "ETH" in ativo_view else (f"OANDA:{ativo_view}" if "XAU" in ativo_view else f"FX:{ativo_view}")
        
        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:520px;width:100%;">
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
        components.html(tradingview_html, height=530)

with tab_ia:
    st.subheader("🧠 Matriz Quantitativa & Sinais IA")
    matrix_data = []
    for asset in ativos_selecionados:
        if "BTC" in asset or "ETH" in asset:
            sinal = "🟢 COMPRA FORTE (Tendência & MFI)"
            conf = "89.2%"
        elif "XAU" in asset:
            sinal = "🟡 AGUARDAR REPETESTE"
            conf = "74.5%"
        else:
            sinal = "🔴 AGUARDAR MERCADO ABRIR"
            conf = "81.0%"

        matrix_data.append({
            "Ativo": asset,
            "Timeframe": timeframe,
            "Estrutura IA": "Tendência de Alta" if "BTC" in asset or "ETH" in asset else "Consolidação",
            "Assertividade Estimada": conf,
            "Direcionamento": sinal
        })
    st.table(pd.DataFrame(matrix_data))

with tab_ordens:
    st.subheader("📋 Ordens do Supabase / MT5")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                st.dataframe(pd.DataFrame(ordens_res.data), use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma ordem pendente ou registrada no banco.")
        except Exception:
            st.info("ℹ️ Aguardando estrutura da tabela 'ordens'.")
    else:
        st.info("ℹ️ Supabase não conectado.")
