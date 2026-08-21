import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import asyncio
from metaapi_cloud_sdk import MetaApi
import yfinance as yf
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Robô Trader IA - Exness Cloud Auto", page_icon="🤖", layout="wide")

# --- ESTADO DE SESSÃO ---
if "bot_rodando" not in st.session_state:
    st.session_state.bot_rodando = False
if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []

# --- DESIGN CYBERPUNK ---
st.markdown("""
<style>
    .stApp { background-color: #060812; color: #00f3ff; font-family: 'Segoe UI', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #0b0e1e !important; border-right: 2px solid #00f3ff; }
    h1, h2, h3 { color: #00f3ff !important; text-shadow: 0 0 12px rgba(0, 243, 255, 0.7); }
    .signal-card {
        background: #0f152d; border: 2px solid #00ff66; border-radius: 12px; padding: 20px;
        box-shadow: 0 0 25px rgba(0, 255, 102, 0.25); margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🤖 ROBÔ TRADER IA ⚡ AUTOMAÇÃO EXNESS CLOUD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f3ff;'>🚀 Execução Automática de Ordens 24/7 sem dependência de PC Local</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR: CONFIGURAÇÕES DE CONEXÃO ---
st.sidebar.header("🔑 CHAVES DE ACESSO")
gemini_key = st.sidebar.text_input("🔑 Chave API Gemini:", type="password")
metaapi_token = st.sidebar.text_input("🌐 MetaApi Token:", type="password")
metaapi_account_id = st.sidebar.text_input("🆔 MetaApi Account ID:", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ OPERAÇÕES & RISCO")

auto_trading = st.sidebar.checkbox("⚡ Habilitar Auto-Trading (Enviar Ordens Reais)", value=False)
lote_fixo = st.sidebar.number_input("📦 Tamanho do Lote (Volume):", value=0.01, step=0.01, min_value=0.01)
tp_pips = st.sidebar.number_input("🎯 Take Profit (Pips):", value=200, step=10)
sl_pips = st.sidebar.number_input("🛡️ Stop Loss (Pips):", value=100, step=10)

ativos = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "XAUUSD (Ouro)": "GC=F",
    "BTCUSD": "BTC-USD"
}

ativo_selecionado = st.sidebar.selectbox("📈 Ativo para Análise:", list(ativos.keys()))

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("🟢 ANALISAR & EXECUTAR", use_container_width=True):
        st.session_state.bot_rodando = True
with col_b2:
    if st.button("🔴 PARAR", use_container_width=True):
        st.session_state.bot_rodando = False

# --- FUNÇÃO ASYNC PARA EXECUTAR ORDEM NA EXNESS VIA METAAPI ---
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
        
        return True, f"Ordem {action} enviada com sucesso! Ticket: {res.get('numericCode', 'OK')}"
    except Exception as e:
        return False, str(e)

# --- EXECUÇÃO DA ANÁLISE DA IA ---
if st.session_state.bot_rodando:
    if not gemini_key:
        st.error("⚠️ Insira sua Chave API do Gemini.")
    else:
        symbol_ticker = ativos[ativo_selecionado]
        df = yf.download(tickers=symbol_ticker, period="2d", interval="15m")
        
        if not df.empty:
            df['sma20'] = df['Close'].rolling(20).mean()
            preco_atual = float(df['Close'].iloc[-1])
            sma20_atual = float(df['sma20'].iloc[-1])
            tendencia = "ALTA 🟢" if preco_atual > sma20_atual else "BAIXA 🔴"

            genai.configure(api_key=gemini_key)
            prompt = f"""
            Você é um Robô Trader Algorítmico operando o mercado Forex e Crypto.
            Ativo: {ativo_selecionado}
            Preço Atual: {preco_atual:.5f}
            Média Móvel (SMA20): {sma20_atual:.5f}
            Tendência Técnica: {tendencia}

            Responda EXATAMENTE neste formato:
            DECISÃO: [COMPRA / VENDA / AGUARDAR]
            CONFIANÇA: [0 a 100]%
            MOTIVO: [Breve justificativa em 1 frase]
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
                st.markdown("<div class='signal-card'>", unsafe_allow_html=True)
                st.markdown("### 🤖 DIAGNÓSTICO EM TEMPO REAL DA IA")
                st.write(resposta_texto)
                st.markdown("</div>", unsafe_allow_html=True)

                if auto_trading and "AGUARDAR" not in resposta_texto.upper():
                    if not metaapi_token or not metaapi_account_id:
                        st.error("⚠️ Preencha o Token e Account ID do MetaApi.")
                    else:
                        acao = "BUY" if "COMPRA" in resposta_texto.upper() else "SELL"
                        simbolo_mt5 = ativo_selecionado.split()[0]
                        
                        st.info(f"⚡ Enviando ordem de {acao} para a Exness via MetaApi...")
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        sucesso, msg = loop.run_until_complete(
                            executar_ordem_exness(metaapi_token, metaapi_account_id, simbolo_mt5, acao, lote_fixo, sl_pips, tp_pips)
                        )
                        
                        if sucesso:
                            st.success(f"🎉 {msg}")
                            st.session_state.historico_ordens.append({"Data": datetime.datetime.now().strftime("%d/%m %H:%M"), "Ativo": simbolo_mt5, "Ação": acao, "Lote": lote_fixo})
                        else:
                            st.error(f"❌ Falha ao executar ordem: {msg}")
            else:
                st.error("Erro ao conectar com a API Gemini.")

if st.session_state.historico_ordens:
    st.markdown("---")
    st.markdown("### 📜 Histórico de Ordens Enviadas")
    st.dataframe(pd.DataFrame(st.session_state.historico_ordens), use_container_width=True)