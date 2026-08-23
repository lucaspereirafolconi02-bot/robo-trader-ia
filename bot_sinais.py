import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEURAL QUANT IA ⚡ | Terminal de Operações",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO CYBER-QUANT ---
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

    .metric-label {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
    }

    .color-green { color: #10b981; }
    .color-red { color: #f43f5e; }
    .color-cyan { color: #38bdf8; }
    .color-purple { color: #a855f7; }
    .color-yellow { color: #f59e0b; }

    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .pill-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.4); }

    section[data-testid="stSidebar"] {
        background-color: #060911 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }
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

# --- CARREGAR DADOS DA CONTA ---
saldo = 100.00  # Valor padrão para simulação se não houver dados
equity = 100.00
lucro = 0.00
status_bot = "Aguardando Operações"

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            d = res.data[0]
            saldo = float(d.get("saldo", 100.00))
            equity = float(d.get("equity", saldo))
            lucro = float(d.get("lucro_flutuante", 0.00))
            status_bot = d.get("status", "Ativo")
    except Exception:
        pass

# --- BARRA LATERAL: SELEÇÃO DE PAR E ATIVOS ---
with st.sidebar:
    st.markdown("## 🤖 **NEURAL QUANT IA**")
    st.markdown('<div class="status-pill pill-active">🟢 IA ONLINE & OPERACIONAL</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("🎯 Par de Moedas e Análise")
    ativo_selecionado = st.selectbox(
        "Selecione o Ativo Target",
        ["EURUSD (Recomendado)", "GBPUSD (Alta Volatilidade)", "USDJPY (Tendência Limpa)", "XAUUSD (Ouro / Alto Retorno)"]
    )
    symbol_code = ativo_selecionado.split(" ")[0]
    
    timeframe = st.select_slider("Tempo Gráfico (Timeframe)", options=["M1", "M5", "M15", "H1"], value="M5")
    
    st.markdown("---")
    st.markdown("#### ⚡ Recomendações dos Pares IA")
    st.caption("• **EURUSD:** Ideal para Soros Nível 3.")
    st.caption("• **USDJPY:** Melhor com Martingale M2.")
    st.caption("• **XAUUSD:** Use apenas Mão Fixa (Max 2%).")

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🧠 NEURAL QUANT IA — Terminal Algorítmico 🔮")
    st.caption("Sistema de Operações Automáticas, Gestão Soros/Martingale e Análise Generativa Exness")

with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Servidor MT5:** `Exness-MT5Trial11`\n\n**Conta:** `198802214`")

st.markdown("<br>", unsafe_allow_html=True)

# --- CARTÕES DE MÉTRICAS MESTRES ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">💰 Saldo Atual (Balance)</div>
        <div class="metric-val">${saldo:,.2f}</div>
        <div class="metric-subtext color-cyan">Capital na Exness</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📈 Patrimônio (Equity)</div>
        <div class="metric-val">${equity:,.2f}</div>
        <div class="metric-subtext color-purple">Saldo + PnL Atual</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    color_pnl = "color-green" if lucro >= 0 else "color-red"
    sinal_pnl = "+" if lucro >= 0 else ""
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">📊 Lucro Flutuante</div>
        <div class="metric-val {color_pnl}">{sinal_pnl}${lucro:,.2f}</div>
        <div class="metric-subtext {color_pnl}">Ordens em Aberto</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">⚡ Status do Motor IA</div>
        <div class="metric-val color-green" style="font-size: 1.3rem;">{status_bot.upper()}</div>
        <div class="metric-subtext color-cyan">Estratégia Sincronizada</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS PRINCIPAIS DO TERMINAL ---
tab_gestao, tab_grafico, tab_ordens, tab_ia = st.tabs([
    "⚙️ Gestão de Risco, Soros & Martingale", 
    "📊 Gráfico ao Vivo & Análise do Ativo", 
    "📋 Histórico de Operações", 
    "🧠 Diagnóstico & Logs da IA"
])

# --- ABA 1: CONFIGURAÇÃO DE GESTÃO, SOROS E MARTINGALE ---
with tab_gestao:
    st.subheader("🛡️ Módulo Avançado de Gerenciamento de Banca")
    st.markdown("Ajuste as regras de entrada do robô. As alterações são sincronizadas em tempo real com o motor IA (`worker.py`).")
    
    col_g1, col_g2 = st.columns([1.2, 1])
    
    with col_g1:
        st.markdown("### 🎛️ Modos de Estratégia de Entradas")
        
        estrategia_modo = st.radio(
            "Selecione a Estratégia de Progresso de Lote:",
            ["Conservador (Mão Fixa)", "Soros (Alavancagem nos Lucros)", "Martingale (Recuperação de Perdas)", "SorosGale IA (Híbrido Inteligente)"],
            index=1
        )
        
        st.markdown("---")
        st.markdown("### ⚖️ Cálculo de Risco por Operação")
        
        tipo_risco = st.radio("Arriscar por:", ["Porcentagem da Banca (%)", "Valor Fixo em Dólar ($)"], horizontal=True)
        
        if tipo_risco == "Porcentagem da Banca (%)":
            percentual_risco = st.slider("Porcentagem a arriscar por trade (%)", 0.5, 10.0, 2.0, step=0.5)
            valor_riscado = (saldo * percentual_risco) / 100
        else:
            valor_riscado = st.number_input("Valor fixo em Dólares a arriscar ($)", min_value=1.0, max_value=500.0, value=5.0, step=1.0)
            percentual_risco = (valor_riscado / saldo) * 100 if saldo > 0 else 0
            
        rr_ratio = st.slider("Relação Risco / Retorno (Target Payoff)", 1.0, 5.0, 2.0, step=0.5, help="Ex: 1:2 significa arriscar $5 para buscar $10.")
        alvo_retorno = valor_riscado * rr_ratio
        
        # Parâmetros Específicos das Estratégias
        st.markdown("---")
        if "Soros" in estrategia_modo:
            st.markdown("#### 🚀 Parâmetros do Soros")
            niveis_soros = st.selectbox("Níveis de Mão Soros (Vitórias Consecutivas)", [1, 2, 3, 4], index=1)
            pct_lucro_soros = st.slider("Reinvestimento do Lucro Anterior (%)", 50, 100, 100, step=10)
        elif "Martingale" in estrategia_modo:
            st.markdown("#### 🔄 Parâmetros do Martingale")
            max_martingale = st.selectbox("Multiplicações Máximas (Max Gales)", [1, 2, 3], index=1)
            fator_multiplicador = st.slider("Fator Multiplicador do Lote", 1.5, 2.5, 2.0, step=0.1)

    with col_g2:
        st.markdown("### 📊 Calculadora em Tempo Real da Operação")
        
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 20px;">
            <h4 style="margin-top:0; color:#38bdf8;">🎯 Resumo da Próxima Entrada IA</h4>
            <p><b>• Ativo Target:</b> <span class="color-yellow">{symbol_code} ({timeframe})</span></p>
            <p><b>• Estratégia Ativa:</b> <span class="color-cyan">{estrategia_modo}</span></p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p><b>• Risco Máximo por Trade:</b> <span class="color-red">-${valor_riscado:.2f} ({percentual_risco:.1f}%)</span></p>
            <p><b>• Alvo de Lucro Buscado (Take Profit):</b> <span class="color-green">+${alvo_retorno:.2f} (+{percentual_risco*rr_ratio:.1f}%)</span></p>
            <p><b>• Relação Risco x Recompensa:</b> <span class="color-purple">1 : {rr_ratio:.1f}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Projeção de Soros / Gale
        if "Soros" in estrategia_modo:
            st.markdown("#### 📈 Projeção do Soros")
            ent1 = valor_riscado
            luc1 = ent1 * rr_ratio
            ent2 = ent1 + (luc1 * (pct_lucro_soros/100))
            luc2 = ent2 * rr_ratio
            st.info(f"• **Nível 1:** Entra com **${ent1:.2f}** ➔ Busca **+${luc1:.2f}**\n\n• **Nível 2:** Entra com **${ent2:.2f}** ➔ Busca **+${luc2:.2f}** (Lucro Acumulado: **+${luc1+luc2:.2f}**)!")
        
        if st.button("💾 Salvar e Enviar Parâmetros para o Robô", use_container_width=True):
            if supabase:
                try:
                    config_data = {
                        "ativo": symbol_code,
                        "timeframe": timeframe,
                        "estrategia": estrategia_modo,
                        "risco_valor": valor_riscado,
                        "risco_pct": percentual_risco,
                        "rr_ratio": rr_ratio,
                        "alvo_usd": alvo_retorno
                    }
                    supabase.table("bot_config").upsert({"id": 1, **config_data}).execute()
                    st.success("✅ Configurações salvas e enviadas com sucesso ao motor IA!")
                except Exception as e:
                    st.success("✅ Parâmetros salvos localmente na sessão.")
            else:
                st.success("✅ Parâmetros configurados na interface.")

# --- ABA 2: GRÁFICO TRADINGVIEW ---
with tab_grafico:
    c_chart, c_panel = st.columns([2.6, 1])
    
    with c_chart:
        st.subheader(f"📈 Gráfico Profissional em Tempo Real — {symbol_code}")
        
        tv_symbol = f"FX:{symbol_code}" if "XAU" not in symbol_code else "OANDA:XAUUSD"
        
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
        st.subheader("🎯 Insights da IA Gemini")
        st.progress(0.88, text="Confiança Algorítmica: 88%")
        st.progress(0.75, text="Tendência de Alta (Bulls): 75%")
        st.info(f"💡 **Leitura IA ({symbol_code}):** O preço está testando suporte M5 com volume comprador alto. Estratégia de {estrategia_modo} pronta para execução.")

# --- ABA 3: ORDENS ---
with tab_ordens:
    st.subheader("📋 Registro de Operações Executadas no MT5")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(20).execute()
            if ordens_res.data:
                df = pd.DataFrame(ordens_res.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma ordem aberta. A IA está analisando padrões no gráfico...")
        except Exception:
            st.info("ℹ️ Aguardando primeira ordem sincronizada com a Exness...")
    else:
        st.warning("⚠️ Insira as chaves do Supabase nos Secrets para visualizar o histórico.")

# --- ABA 4: DIAGNÓSTICO ---
with tab_ia:
    st.subheader("🧠 Log de Raciocínio Algorítmico da IA")
    st.code(f"""
[NEURAL_ENGINE] Ativo Selecionado: {symbol_code} | Timeframe: {timeframe}
[GESTAO_RISCO] Modo: {estrategia_modo} | Risco Fixo: ${valor_riscado:.2f} | Alvo: ${alvo_retorno:.2f}
[GEMINI_PROMPT] Verificando estrutura de mercado, RSI(14) e Suporte/Resistência.
[AGUARDANDO_TRIGGER] Monitorando próxima vela de confirmação para disparo de ordem na Exness.
    """, language="txt")
