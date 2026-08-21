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
    page_title="Terminal IA Trader - Execução Multi-Ativos & Sync Exness",
    page_icon="⚡",
    layout="wide"
)

if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []
if "total_execucoes" not in st.session_state:
    st.session_state.total_execucoes = 0
if "saldo_banca" not in st.session_state:
    st.session_state.saldo_banca = 1000.0

# --- DESIGN FUTURISTA CYBERPUNK GLASSMORPHISM ---
st.markdown("""
<style>
    .stApp, header[data-testid="stHeader"] { 
        background-color: #03050e !important; 
        color: #00f3ff !important; 
        font-family: 'Segoe UI', Roboto, sans-serif; 
    }
    section[data-testid="stSidebar"] { 
        background-color: #060a1a !important; 
        border-right: 2px solid #00f3ff !important;
        box-shadow: 5px 0 20px rgba(0, 243, 255, 0.15);
    }
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span {
        color: #b0e8fd !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-shadow: 0 0 5px rgba(0, 243, 255, 0.3);
    }
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
        background-color: #0d142b !important;
        color: #00f3ff !important;
        border: 1px solid #00f3ff !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: inset 0 0 8px rgba(0, 243, 255, 0.2);
    }
    .stButton>button {
        background: linear-gradient(135deg, #00f3ff 0%, #00ff66 100%) !important;
        color: #03050e !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0, 243, 255, 0.8) !important;
    }
    .glass-card {
        background: rgba(13, 20, 43, 0.7);
        border: 1px solid rgba(0, 243, 255, 0.4);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.15);
    }
    .glass-card h4 {
        color: #8bbcd4 !important;
        font-size: 13px !important;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .glass-card h3 {
        color: #00f3ff !important;
        font-size: 24px !important;
        margin: 0;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
    }
    .buy-badge { background-color: #00ff66; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: 900; }
    .sell-badge { background-color: #ff3366; color: #fff; padding: 6px 14px; border-radius: 6px; font-weight: 900; }
    .wait-badge { background-color: #ffcc00; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>⚡ TERMINAL IA TRADER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8bbcd4; font-weight: 600;'>Sincronização Exness em Tempo Real | Varredura Multi-Ativos | Confiança ≥ 60%</p>", unsafe_allow_html=True)
st.markdown("---")

# FUNÇÃO ASYNC PARA BUSCAR SALDO DA EXNESS
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

# --- SIDEBAR: CONEXÃO & SALDO ---
st.sidebar.header("🔑 CHAVES DE ACESSO")
gemini_key = st.sidebar.text_input("Chave API Gemini:", type="password")
metaapi_token = st.sidebar.text_input("Token MetaApi:", type="password")
metaapi_account_id = st.sidebar.text_input("Account ID MetaApi:", type="password")

if st.sidebar.button("🔄 Sincronizar Saldo Exness", use_container_width=True):
    if not metaapi_token or not metaapi_account_id:
        st.sidebar.error("⚠️ Insira o Token e Account ID MetaApi.")
    else:
        with st.sidebar.spinner("Conectando à Exness..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sucesso, saldo_ou_erro = loop.run_until_complete(consultar_saldo_exness(metaapi_token, metaapi_account_id))
            if sucesso:
                st.session_state.saldo_banca = saldo_ou_erro
                st.sidebar.success(f"Saldo Exness: ${saldo_ou_erro:,.2f}")
            else:
                st.sidebar.error(f"Erro ao buscar saldo: {saldo_ou_erro}")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ GESTÃO DE RISCO DA BANCA")
saldo_banca = st.sidebar.number_input("💵 Saldo Atual ($):", value=st.session_state.saldo_banca, step=50.0)
st.session_state.saldo_banca = saldo_banca

risco_por_operacao = st.sidebar.slider("🎯 Risco por Operação (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
tp_pips = st.sidebar.number_input("🎯 Take Profit (Pips):", value=200, step=10)
sl_pips = st.sidebar.number_input("🛡️ Stop Loss (Pips):", value=100, step=10)
auto_trading = st.sidebar.checkbox("⚡ Auto-Trading Ativo (Exness)", value=False)

# CÁLCULOS MATEMÁTICOS DE RISCO
valor_em_risco = saldo_banca * (risco_por_operacao / 100)
retorno_potencial = valor_em_risco * (tp_pips / sl_pips)
lote_calculado = max(0.01, round(valor_em_risco / (sl_pips * 10), 2))

# BASE COMPLETA DE ATIVOS
ativos = {
    "EURUSD (Euro / Dólar)": "EURUSD=X", "GBPUSD (Libra / Dólar)": "GBPUSD=X",
    "USDJPY (Dólar / Iene)": "JPY=X", "GBPJPY (Libra / Iene)": "GBPJPY=X",
    "EURJPY (Euro / Iene)": "EURJPY=X", "AUDUSD (Dólar Aus. / Dólar)": "AUDUSD=X",
    "USDCAD (Dólar / Dólar Can.)": "CAD=X", "USDCHF (Dólar / Franco Suíço)": "CHF=X",
    "NZDUSD (Dólar NZ / Dólar)": "NZDUSD=X", "EURAUD (Euro / Dólar Aus.)": "EURAUD=X",
    "XAUUSD (Ouro)": "GC=F", "XAGUSD (Prata)": "SI=F",
    "USOIL (Petróleo WTI)": "CL=F", "UKOIL (Petróleo Brent)": "BZ=F", "NATGAS (Gás Natural)": "NG=F",
    "BTCUSD (Bitcoin)": "BTC-USD", "ETHUSD (Ethereum)": "ETH-USD",
    "SOLUSD (Solana)": "SOL-USD", "XRPUSD (Ripple)": "XRP-USD",
    "US500 (S&P 500)": "^GSPC", "US100 (Nasdaq 100)": "^IXIC", "US30 (Dow Jones)": "^DJI",
    "GER40 (DAX Alemão)": "^GDAXI", "NVDA (NVIDIA)": "NVDA", "AAPL (Apple)": "AAPL",
    "TSLA (Tesla)": "TSLA", "AMZN (Amazon)": "AMZN", "MSFT (Microsoft)": "MSFT"
}

st.sidebar.markdown("---")
st.sidebar.header("🌐 SELEÇÃO DE ATIVOS")
selecionar_todos = st.sidebar.checkbox("🔥 SELECIOMAR TODOS OS ATIVOS (Varredura Geral)")

if selecionar_todos:
    ativos_selecionados = list(ativos.keys())
    st.sidebar.info(f"✅ Todos os {len(ativos_selecionados)} ativos selecionados.")
else:
    ativos_selecionados = st.sidebar.multiselect(
        "📈 Escolha um ou mais ativos:",
        options=list(ativos.keys()),
        default=["EURUSD (Euro / Dólar)", "XAUUSD (Ouro)", "BTCUSD (Bitcoin)"]
    )

# METRICAS DE OPERAÇÃO
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='glass-card'><h4>Banca Sincronizada</h4><h3>${saldo_banca:,.2f}</h3></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='glass-card'><h4>Risco / Entrada</h4><h3>${valor_em_risco:,.2f} ({risco_por_operacao}%)</h3></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='glass-card'><h4>Lucro Alvo (TP)</h4><h3>+${retorno_potencial:,.2f}</h3></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='glass-card'><h4>Lote Calculado</h4><h3>{lote_calculado}</h3></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# FUNÇÃO ASYNC PARA EXECUÇÃO METAAPI
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
        return True, f"Ordem {action} enviada! Ticket: {res.get('numericCode', 'OK')}"
    except Exception as e:
        return False, str(e)

# EXECUÇÃO DA VARREDURA
if st.button("🚀 INICIAR VARREDURA TÉCNICA MULTI-ATIVOS VIA IA", use_container_width=True):
    if not gemini_key:
        st.error("⚠️ Insira sua Chave API do Gemini na barra lateral.")
    elif not ativos_selecionados:
        st.warning("⚠️ Selecione pelo menos um ativo na barra lateral.")
    else:
        st.session_state.total_execucoes += 1
        genai.configure(api_key=gemini_key)
        
        progresso = st.progress(0)
        total_ativos = len(ativos_selecionados)
        resultados = []

        for idx, nome_ativo in enumerate(ativos_selecionados):
            progresso.progress((idx + 1) / total_ativos)
            symbol_ticker = ativos[nome_ativo]
            df = yf.download(tickers=symbol_ticker, period="2d", interval="15m", progress=False)
            
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
            Ativo: {nome_ativo} | Preço: {preco_atual:.5f} | SMA20: {sma20:.5f} | RSI: {rsi:.2f} | Tendência: {tendencia}
            Avalie se deve COMPRAR, VENDER ou AGUARDAR para atingir TP de {tp_pips} pips antes do SL de {sl_pips} pips.
            Se CONFIANÇA < 60%, marque AGUARDAR.

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

                if confianca_val < 60:
                    decisao_val = "AGUARDAR"

                resultados.append({
                    "Ativo": nome_ativo,
                    "Preço": f"{preco_atual:.5f}",
                    "Decisão": decisao_val,
                    "Confiança": confianca_val,
                    "Chance TP": f"{chance_tp_val}%",
                    "Lucro Potencial": f"+${retorno_potencial:.2f}",
                    "Status": "✅ APROVADO" if confianca_val >= 60 and decisao_val != "AGUARDAR" else "⚠️ REPROVADO (<60%)"
                })

                # EXECUÇÃO AUTOMÁTICA DA MELHOR OPORTUNIDADE
                if auto_trading and decisao_val in ["COMPRA", "VENDA"] and confianca_val >= 60:
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

        # EXIBIÇÃO EM TABELA DOS RESULTADOS
        st.markdown("<div class='glass-card' style='text-align: left;'>", unsafe_allow_html=True)
        st.subheader("📊 RESULTADOS DA VARREDURA MULTI-ATIVOS")
        df_res = pd.DataFrame(resultados)
        if not df_res.empty:
            st.dataframe(df_res, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.historico_ordens:
    st.markdown("---")
    st.subheader("📜 Histórico de Ordens Executadas")
    st.dataframe(pd.DataFrame(st.session_state.historico_ordens), use_container_width=True)
