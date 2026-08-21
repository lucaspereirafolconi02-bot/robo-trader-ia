import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import asyncio
from metaapi_cloud_sdk import MetaApi
import yfinance as yf
import datetime
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Terminal Ninja IA - Operational Dashboard",
    page_icon="🥷",
    layout="wide"
)

# ESTADOS DA SESSÃO
if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []
if "total_execucoes" not in st.session_state:
    st.session_state.total_execucoes = 0
if "saldo_banca" not in st.session_state:
    st.session_state.saldo_banca = 1000.0
if "notas_diario" not in st.session_state:
    st.session_state.notas_diario = "📝 [Diário Ninja] Registre aqui observações de notícias, horários de payout e setups do dia..."

# --- ESTILO VISUAL: DASHBOARD NINJA NAVY GLASS ---
st.markdown("""
<style>
    /* Fundo Azul Marinho Profundo */
    .stApp, header[data-testid="stHeader"] { 
        background: radial-gradient(circle at 80% 20%, #0b1120 0%, #050811 60%, #020307 100%) !important; 
        color: #e2e8f0 !important; 
        font-family: 'Inter', 'Segoe UI', sans-serif; 
    }
    
    /* Barra Lateral */
    section[data-testid="stSidebar"] { 
        background: rgba(8, 14, 28, 0.9) !important; 
        border-right: 1px solid rgba(56, 189, 248, 0.2) !important;
        backdrop-filter: blur(15px);
        box-shadow: 10px 0 30px rgba(0, 0, 0, 0.6);
    }
    
    /* Rótulos de Alta Visibilidade */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        letter-spacing: 0.5px;
    }
    
    /* Inputs estilo Neon */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.85) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 12px rgba(129, 140, 248, 0.4) !important;
    }

    /* Cards Translúcidos Institucionais */
    .dash-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 14px;
        padding: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .dash-card:hover {
        border-color: rgba(56, 189, 248, 0.6);
        transform: translateY(-2px);
    }
    .dash-card h4 {
        color: #64748b !important;
        font-size: 11px !important;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
    }
    .dash-card h2 {
        color: #f8fafc !important;
        font-size: 26px !important;
        margin: 0;
        font-weight: 800;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }
    .dash-card sub {
        color: #38bdf8;
        font-size: 12px;
        font-weight: 600;
    }

    /* Botão Principal Neon Glow */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 30px rgba(37, 99, 235, 0.8) !important;
        transform: scale(1.01);
    }

    /* Badges */
    .badge-buy { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
    .badge-sell { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
    .badge-wait { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# HEADER INSTITUCIONAL NINJA
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px;'>
    <div>
        <h1 style='margin:0; font-size: 28px; color: #f8fafc;'>🥷 INSTITUTIONAL NINJA TERMINAL PRO</h1>
        <p style='margin:0; color: #64748b; font-size: 13px;'>Varredura Algorítmica Multi-Ativos | Gestão de Risco Precisa Exness</p>
    </div>
</div>
""", unsafe_allow_html=True)

# FUNÇÃO ASYNC PARA BUSCAR SALDO EXNESS
async def consultar_saldo_exness(token, account_id):
    try:
        api = MetaApi(token)
        account = await api.metatrader_account_api.get_account(account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        info = await connection.get_account_information()
        return True, float(info.get('equity', info.get('balance', 0.0)))
    except Exception as e:
        return False, str(e)

# --- SIDEBAR: CONEXÃO & PRESETS DE IA ---
st.sidebar.markdown("### 🔑 CONEXÃO & SYNCRONIA")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
metaapi_token = st.sidebar.text_input("MetaApi Token:", type="password")
metaapi_account_id = st.sidebar.text_input("MetaApi Account ID:", type="password")

if st.sidebar.button("🔄 Sincronizar Saldo Exness", use_container_width=True):
    if not metaapi_token or not metaapi_account_id:
        st.sidebar.error("⚠️ Preencha as credenciais da MetaApi.")
    else:
        with st.sidebar.spinner("Conectando à Exness..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sucesso, saldo_ou_erro = loop.run_until_complete(consultar_saldo_exness(metaapi_token, metaapi_account_id))
            if sucesso:
                st.session_state.saldo_banca = saldo_ou_erro
                st.sidebar.success(f"Saldo Exness: ${saldo_ou_erro:,.2f}")
            else:
                st.sidebar.error(f"Erro: {saldo_ou_erro}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 COMBOS RECOMENDADOS (IA)")

# DICIONÁRIO DE COMBOS DE ESTRATÉGIA
combos_estrategia = {
    "🥷 Conservador Ninja (Forex Low Risk)": {
        "risco": 0.5, "tp": 150, "sl": 100, "confianca": 70,
        "ativos": ["EURUSD (Euro / Dólar)", "GBPUSD (Libra / Dólar)", "USDJPY (Dólar / Iene)"]
    },
    "🔱 Commodities & Ouro (Safe Gold)": {
        "risco": 1.0, "tp": 250, "sl": 120, "confianca": 65,
        "ativos": ["XAUUSD (Ouro)", "XAGUSD (Prata)", "USOIL (Petróleo WTI)"]
    },
    "🚀 Cripto & Tech (Agressivo)": {
        "risco": 2.0, "tp": 400, "sl": 200, "confianca": 60,
        "ativos": ["BTCUSD (Bitcoin)", "ETHUSD (Ethereum)", "NVDA (NVIDIA)", "TSLA (Tesla)"]
    },
    "🌐 Varredura Global (Todos os Ativos)": {
        "risco": 1.0, "tp": 200, "sl": 100, "confianca": 60,
        "ativos": "TODOS"
    },
    "⚙️ Personalizado (Ajuste Manual)": None
}

combo_selecionado = st.sidebar.selectbox("Perfil de Estratégia:", list(combos_estrategia.keys()))

if combo_selecionado != "⚙️ Personalizado (Ajuste Manual)":
    dados_combo = combos_estrategia[combo_selecionado]
    risco_def = dados_combo["risco"]
    tp_def = dados_combo["tp"]
    sl_def = dados_combo["sl"]
    confianca_def = dados_combo["confianca"]
    ativos_def = dados_combo["ativos"]
else:
    risco_def, tp_def, sl_def, confianca_def, ativos_def = 1.0, 200, 100, 60, []

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ CONTROLE DE RISCO & NINJA MANAGEMENT")
saldo_banca = st.sidebar.number_input("💵 Saldo de Operação ($):", value=st.session_state.saldo_banca, step=100.0)
st.session_state.saldo_banca = saldo_banca

timeframe_sel = st.sidebar.selectbox("⏱️ Timeframe do Gráfico:", options=["5m", "15m", "1h", "4h"], index=1)

risco_por_operacao = st.sidebar.slider("🎯 Risco por Operação (%):", min_value=0.2, max_value=5.0, value=risco_def, step=0.1)
max_drawdown_limite = st.sidebar.slider("🛑 Limite de Loss Diário (%):", min_value=1.0, max_value=10.0, value=3.0, step=0.5)

tp_pips = st.sidebar.number_input("🎯 Take Profit (Pips):", value=tp_def, step=10)
sl_pips = st.sidebar.number_input("🛡️ Stop Loss (Pips):", value=sl_def, step=10)
min_confianca = st.sidebar.slider("🧠 Confiança Mínima IA (%):", min_value=50, max_value=90, value=confianca_def, step=5)

auto_trading = st.sidebar.checkbox("🥷 Auto-Trading Ativo (Exness)", value=False)

# CÁLCULOS MATEMÁTICOS DE RISCO
valor_em_risco = saldo_banca * (risco_por_operacao / 100)
max_drawdown_valor = saldo_banca * (max_drawdown_limite / 100)
retorno_potencial = valor_em_risco * (tp_pips / sl_pips)
lote_calculado = max(0.01, round(valor_em_risco / (sl_pips * 10), 2))

# BASE COMPLETA DE ATIVOS
ativos_master = {
    "EURUSD (Euro / Dólar)": "EURUSD=X", "GBPUSD (Libra / Dólar)": "GBPUSD=X",
    "USDJPY (Dólar / Iene)": "JPY=X", "GBPJPY (Libra / Iene)": "GBPJPY=X",
    "EURJPY (Euro / Iene)": "EURJPY=X", "AUDUSD (Dólar Aus. / Dólar)": "AUDUSD=X",
    "USDCAD (Dólar / Dólar Can.)": "CAD=X", "USDCHF (Dólar / Franco Suíço)": "CHF=X",
    "XAUUSD (Ouro)": "GC=F", "XAGUSD (Prata)": "SI=F", "USOIL (Petróleo WTI)": "CL=F",
    "BTCUSD (Bitcoin)": "BTC-USD", "ETHUSD (Ethereum)": "ETH-USD", "SOLUSD (Solana)": "SOL-USD",
    "US500 (S&P 500)": "^GSPC", "US100 (Nasdaq 100)": "^IXIC", "US30 (Dow Jones)": "^DJI",
    "NVDA (NVIDIA)": "NVDA", "AAPL (Apple)": "AAPL", "TSLA (Tesla)": "TSLA"
}

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 ATIVOS EM OBSERVAÇÃO")
if combo_selecionado != "⚙️ Personalizado (Ajuste Manual)":
    if ativos_def == "TODOS":
        ativos_selecionados = list(ativos_master.keys())
    else:
        ativos_selecionados = ativos_def
    st.sidebar.info(f"Ativos carregados ({len(ativos_selecionados)} no combo).")
else:
    selecionar_todos = st.sidebar.checkbox("🔥 Selecionar Todos os Ativos")
    if selecionar_todos:
        ativos_selecionados = list(ativos_master.keys())
    else:
        ativos_selecionados = st.sidebar.multiselect("Ativos:", options=list(ativos_master.keys()), default=["EURUSD (Euro / Dólar)", "XAUUSD (Ouro)"])

# --- LAYOUT DASHBOARD (CARDS COM NOTAS E CIFRÕES) ---
col_c1, col_c2, col_c3, col_c4 = st.columns(4)

with col_c1:
    st.markdown(f"""
    <div class='dash-card'>
        <h4>💵 Banca Operacional</h4>
        <h2>${saldo_banca:,.2f}</h2>
        <sub>Exness Sync Active</sub>
    </div>
    """, unsafe_allow_html=True)

with col_c2:
    st.markdown(f"""
    <div class='dash-card'>
        <h4>💸 Risco / Entrada</h4>
        <h2>${valor_em_risco:,.2f}</h2>
        <sub>{risco_por_operacao}% por Posição</sub>
    </div>
    """, unsafe_allow_html=True)

with col_c3:
    st.markdown(f"""
    <div class='dash-card'>
        <h4>🎯 Retorno Alvo (TP)</h4>
        <h2>+${retorno_potencial:,.2f}</h2>
        <sub>Ratio 1 : {tp_pips/sl_pips:.1f}</sub>
    </div>
    """, unsafe_allow_html=True)

with col_c4:
    st.markdown(f"""
    <div class='dash-card'>
        <h4>🛡️ Trava de Loss Diário</h4>
        <h2>${max_drawdown_valor:,.2f}</h2>
        <sub>Máx. Loss ({max_drawdown_limite}%)</sub>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# BLOCO DE NOTAS & DIÁRIO DE TRADE NINJA
with st.expander("📝 BLOCO DE NOTAS & DIÁRIO DE PLANO DE TRADE", expanded=False):
    st.session_state.notas_diario = st.text_area(
        "Anotações Estratégicas do Dia:",
        value=st.session_state.notas_diario,
        height=120
    )

# FUNÇÃO ASYNC EXECUÇÃO METAAPI
async def executar_ordem_exness(token, account_id, symbol, action, volume, sl_pips, tp_pips):
    try:
        api = MetaApi(token)
        account = await api.metatrader_account_api.get_account(account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        price_info = await connection.get_symbol_price(symbol=symbol)
        price = price_info['ask'] if action == "BUY" else price_info['bid']
        point = 0.0001 if "JPY" not in symbol else 0.01
        if "GC=F" in symbol or "XAU" in symbol: point = 0.1
        
        sl_price = price - (sl_pips * point) if action == "BUY" else price + (sl_pips * point)
        tp_price = price + (tp_pips * point) if action == "BUY" else price - (tp_pips * point)

        if action == "BUY":
            res = await connection.create_market_buy_order(symbol=symbol, volume=volume, stop_loss=sl_price, take_profit=tp_price)
        else:
            res = await connection.create_market_sell_order(symbol=symbol, volume=volume, stop_loss=sl_price, take_profit=tp_price)
        return True, f"Ordem {action} executada com sucesso! Ticket: {res.get('numericCode', 'OK')}"
    except Exception as e:
        return False, str(e)

# BOTÃO DE AÇÃO PRINCIPAL
if st.button("🥷 PROCESSAR ANÁLISE QUANTITATIVA & VARREDURA IA", use_container_width=True):
    if not gemini_key:
        st.error("⚠️ Insira sua Chave API do Gemini na barra lateral.")
    elif not ativos_selecionados:
        st.warning("⚠️ Selecione pelo menos um ativo para análise.")
    else:
        genai.configure(api_key=gemini_key)
        progresso = st.progress(0)
        total = len(ativos_selecionados)
        resultados = []

        for idx, nome_ativo in enumerate(ativos_selecionados):
            progresso.progress((idx + 1) / total)
            symbol_ticker = ativos_master.get(nome_ativo, "EURUSD=X")
            df = yf.download(tickers=symbol_ticker, period="3d", interval=timeframe_sel, progress=False)
            
            if df.empty:
                continue

            preco_atual = float(df['Close'].iloc[-1])
            sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])
            tendencia = "ALTA 🟢" if preco_atual > sma20 else "BAIXA 🔴"

            prompt = f"""
            Ativo: {nome_ativo} | Timeframe: {timeframe_sel} | Preço: {preco_atual:.5f} | SMA20: {sma20:.5f} | RSI: {rsi:.2f} | Tendência: {tendencia}
            Avalie se deve COMPRAR, VENDER ou AGUARDAR para atingir TP de {tp_pips} pips antes do SL de {sl_pips} pips.
            Se CONFIANÇA < {min_confianca}%, marque OBRIGATORIAMENTE AGUARDAR.

            Responda EXATAMENTE neste formato:
            DECISÃO: [COMPRA / VENDA / AGUARDAR]
            CONFIANÇA: [0 a 100]%
            CHANCE_TP: [0 a 100]%
            JUSTIFICATIVA: [Texto curto em 1 frase]
            """

            modelos = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash-latest']
            resposta_texto = ""
            for mod in modelos:
                try:
                    m = genai.GenerativeModel(mod)
                    r = m.generate_content(prompt)
                    if r and r.text:
                        resposta_texto = r.text
                        break
                except:
                    continue

            if resposta_texto:
                confianca_match = re.search(r'CONFIANÇA:\s*(\d+)', resposta_texto, re.IGNORECASE)
                chance_tp_match = re.search(r'CHANCE_TP:\s*(\d+)', resposta_texto, re.IGNORECASE)
                decisao_match = re.search(r'DECISÃO:\s*(COMPRA|VENDA|AGUARDAR)', resposta_texto, re.IGNORECASE)

                confianca_val = int(confianca_match.group(1)) if confianca_match else 50
                chance_tp_val = int(chance_tp_match.group(1)) if chance_tp_match else 50
                decisao_val = decisao_match.group(1).upper() if decisao_match else "AGUARDAR"

                if confianca_val < min_confianca:
                    decisao_val = "AGUARDAR"

                resultados.append({
                    "Ativo": nome_ativo,
                    "Preço Atual": f"{preco_atual:.5f}",
                    "Sinal IA": decisao_val,
                    "Confiança": f"{confianca_val}%",
                    "Probab. TP": f"{chance_tp_val}%",
                    "Lote Calc.": lote_calculado,
                    "Alvo Estimado": f"+${retorno_potencial:.2f}",
                    "Filtro Ninja": f"✅ Aprovado (≥{min_confianca}%)" if confianca_val >= min_confianca and decisao_val != "AGUARDAR" else "⚠️ Bloqueado"
                })

                # EXECUÇÃO AUTOMÁTICA
                if auto_trading and decisao_val in ["COMPRA", "VENDA"] and confianca_val >= min_confianca:
                    if metaapi_token and metaapi_account_id:
                        acao = "BUY" if decisao_val == "COMPRA" else "SELL"
                        simbolo_mt5 = nome_ativo.split()[0]
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        sucesso, msg = loop.run_until_complete(
                            executar_ordem_exness(metaapi_token, metaapi_account_id, simbolo_mt5, acao, lote_calculado, sl_pips, tp_pips)
                        )
                        if sucesso:
                            st.session_state.historico_ordens.append({
                                "Hora": datetime.datetime.now().strftime("%H:%M:%S"),
                                "Ativo": simbolo_mt5, "Ação": acao, "Lote": lote_calculado,
                                "Risco ($)": f"${valor_em_risco:.2f}", "Alvo ($)": f"+${retorno_potencial:.2f}",
                                "Confiança": f"{confianca_val}%"
                            })

        # PAINEL DE RESULTADOS DA VARREDURA
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class='dash-card'>
            <h3 style='margin-top:0; color:#f8fafc;'>📊 OPORTUNIDADES NINJA ENCONTRADAS</h3>
        </div>
        """, unsafe_allow_html=True)
        
        df_res = pd.DataFrame(resultados)
        if not df_res.empty:
            st.dataframe(df_res, use_container_width=True)

if st.session_state.historico_ordens:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📜 HISTÓRICO DE ORDENS EXECUTADAS (SESSÃO)")
    st.dataframe(pd.DataFrame(st.session_state.historico_ordens), use_container_width=True)
