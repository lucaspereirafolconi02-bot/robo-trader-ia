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
    page_title="Terminal IA Trader - Execução & Gestão",
    page_icon="⚡",
    layout="wide"
)

if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []
if "total_execucoes" not in st.session_state:
    st.session_state.total_execucoes = 0

# --- DESIGN FUTURISTA CYBERPUNK GLASSMORPHISM ---
st.markdown("""
<style>
    /* Fundo Global Obsidian */
    .stApp, header[data-testid="stHeader"] { 
        background-color: #03050e !important; 
        color: #00f3ff !important; 
        font-family: 'Segoe UI', Roboto, sans-serif; 
    }
    
    /* Barra Lateral Estilo Terminal */
    section[data-testid="stSidebar"] { 
        background-color: #060a1a !important; 
        border-right: 2px solid #00f3ff !important;
        box-shadow: 5px 0 20px rgba(0, 243, 255, 0.15);
    }
    
    /* Labels e Textos da Sidebar com Alta Visibilidade */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span {
        color: #b0e8fd !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-shadow: 0 0 5px rgba(0, 243, 255, 0.3);
    }
    
    /* Caixas de Entrada (Inputs) com Tema Escuro e Borda Neon */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
        background-color: #0d142b !important;
        color: #00f3ff !important;
        border: 1px solid #00f3ff !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: inset 0 0 8px rgba(0, 243, 255, 0.2);
    }
    
    /* Botões Principais Efeito Neon */
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

    /* Cards de Métricas em Glassmorphism */
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
        letter-spacing: 1px;
    }
    .glass-card h3 {
        color: #00f3ff !important;
        font-size: 24px !important;
        margin: 0;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
    }

    /* Badges de Sinal */
    .buy-badge { background-color: #00ff66; color: #000; padding: 8px 18px; border-radius: 6px; font-weight: 900; font-size: 18px; box-shadow: 0 0 15px rgba(0, 255, 102, 0.6); }
    .sell-badge { background-color: #ff3366; color: #fff; padding: 8px 18px; border-radius: 6px; font-weight: 900; font-size: 18px; box-shadow: 0 0 15px rgba(255, 51, 102, 0.6); }
    .wait-badge { background-color: #ffcc00; color: #000; padding: 8px 18px; border-radius: 6px; font-weight: 900; font-size: 18px; box-shadow: 0 0 15px rgba(255, 204, 0, 0.6); }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>⚡ TERMINAL IA TRADER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8bbcd4; font-weight: 600;'>Sistema de Execução Algorítmica & Filtro Próprio de Risco (Confiança ≥ 60%)</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR: CHAVES & RISCO ---
st.sidebar.header("🔑 CHAVES DE ACESSO")
gemini_key = st.sidebar.text_input("Chave API Gemini:", type="password")
metaapi_token = st.sidebar.text_input("Token MetaApi:", type="password")
metaapi_account_id = st.sidebar.text_input("Account ID MetaApi:", type="password")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ GESTÃO DE RISCO DA BANCA")
saldo_banca = st.sidebar.number_input("💵 Saldo Atual da Banca ($):", value=1000.0, step=100.0)
risco_por_operacao = st.sidebar.slider("🎯 Risco por Operação (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

tp_pips = st.sidebar.number_input("🎯 Take Profit (Pips):", value=200, step=10)
sl_pips = st.sidebar.number_input("🛡️ Stop Loss (Pips):", value=100, step=10)
auto_trading = st.sidebar.checkbox("⚡ Auto-Trading Ativo (Exness)", value=False)

# CÁLCULOS MATEMÁTICOS DE RISCO
valor_em_risco = saldo_banca * (risco_por_operacao / 100)
retorno_potencial = valor_em_risco * (tp_pips / sl_pips)
lote_calculado = max(0.01, round(valor_em_risco / (sl_pips * 10), 2))

# LISTA EXPANDIDA DE ATIVOS MULTI-MERCADO
ativos = {
    # FOREX MAJORS & CROSSES
    "EURUSD (Euro / Dólar)": "EURUSD=X",
    "GBPUSD (Libra / Dólar)": "GBPUSD=X",
    "USDJPY (Dólar / Iene)": "JPY=X",
    "GBPJPY (Libra / Iene)": "GBPJPY=X",
    "EURJPY (Euro / Iene)": "EURJPY=X",
    "AUDUSD (Dólar Aus. / Dólar)": "AUDUSD=X",
    "USDCAD (Dólar / Dólar Can.)": "CAD=X",
    "USDCHF (Dólar / Franco Suíço)": "CHF=X",
    "NZDUSD (Dólar NZ / Dólar)": "NZDUSD=X",
    "EURAUD (Euro / Dólar Aus.)": "EURAUD=X",
    
    # COMMODITIES & METALS
    "XAUUSD (Ouro)": "GC=F",
    "XAGUSD (Prata)": "SI=F",
    "USOIL (Petróleo WTI)": "CL=F",
    "UKOIL (Petróleo Brent)": "BZ=F",
    "NATGAS (Gás Natural)": "NG=F",
    
    # CRIPTOMOEDAS
    "BTCUSD (Bitcoin)": "BTC-USD",
    "ETHUSD (Ethereum)": "ETH-USD",
    "SOLUSD (Solana)": "SOL-USD",
    "XRPUSD (Ripple)": "XRP-USD",
    "ADAUSD (Cardano)": "ADA-USD",
    "BNBUSD (Binance Coin)": "BNB-USD",
    
    # ÍNDICES GLOBAIS
    "US500 (S&P 500)": "^GSPC",
    "US100 (Nasdaq 100)": "^IXIC",
    "US30 (Dow Jones)": "^DJI",
    "GER40 (DAX Alemão)": "^GDAXI",
    "UK100 (FTSE Londres)": "^FTSE",
    "JP225 (Nikkei Japão)": "^N225",
    
    # AÇÕES TECH USA
    "NVDA (NVIDIA)": "NVDA",
    "AAPL (Apple)": "AAPL",
    "TSLA (Tesla)": "TSLA",
    "AMZN (Amazon)": "AMZN",
    "MSFT (Microsoft)": "MSFT"
}

st.sidebar.markdown("---")
ativo_selecionado = st.sidebar.selectbox("📈 Selecionar Ativo:", list(ativos.keys()))

# --- METRICAS DE OPERAÇÃO EM CARDS GLASSMORPHISM ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='glass-card'><h4>Banca Declarada</h4><h3>${saldo_banca:,.2f}</h3></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='glass-card'><h4>Risco da Entrada</h4><h3>${valor_em_risco:,.2f} ({risco_por_operacao}%)</h3></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='glass-card'><h4>Lucro Alvo (TP)</h4><h3>+${retorno_potencial:,.2f}</h3></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='glass-card'><h4>Lote Recom.</h4><h3>{lote_calculado}</h3></div>", unsafe_allow_html=True)

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

# --- BOTÃO PRINCIPAL DE EXECUÇÃO ---
if st.button("🚀 INICIAR ANÁLISE TÉCNICA E PROCESSAR SINAL", use_container_width=True):
    if not gemini_key:
        st.error("⚠️ Insira sua Chave API do Gemini na barra lateral.")
    else:
        st.session_state.total_execucoes += 1
        symbol_ticker = ativos[ativo_selecionado]
        df = yf.download(tickers=symbol_ticker, period="2d", interval="15m")
        
        if not df.empty:
            preco_atual = float(df['Close'].iloc[-1])
            sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])
            
            tendencia = "ALTA 🟢" if preco_atual > sma20 else "BAIXA 🔴"

            genai.configure(api_key=gemini_key)
            prompt = f"""
            Você é um Analista de Mercado e Gestor de Risco Algorítmico Avançado.
            Ativo: {ativo_selecionado}
            Preço Atual: {preco_atual:.5f} | Média Móvel SMA20: {sma20:.5f} | RSI(14): {rsi:.2f}
            Tendência Técnica: {tendencia}
            
            REGRAS DE DECISÃO:
            1. Avalie a probabilidade real do preço atingir o Take Profit ({tp_pips} pips) antes do Stop Loss ({sl_pips} pips).
            2. Se a CONFIANÇA na análise for MENOR que 60%, responda estritamente DECISÃO: AGUARDAR.
            3. Indique a CHANCE_TP (probabilidade percentual estimada de atingir o Take Profit).

            Responda OBRIGATORIAMENTE neste formato:
            DECISÃO: [COMPRA / VENDA / AGUARDAR]
            CONFIANÇA: [Insira número de 0 a 100]%
            CHANCE_TP: [Insira número de 0 a 100]%
            JUSTIFICATIVA: [Breve explicação técnica em 1 ou 2 frases]
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

                if confianca_val < 60 and decisao_val != "AGUARDAR":
                    decisao_val = "AGUARDAR"
                    filtro_msg = "⚠️ Confiança abaixo de 60%. Entrada bloqueada pela Gestão."
                else:
                    filtro_msg = "✅ Filtro Aprovado (≥ 60% de Confiança)." if confianca_val >= 60 else "⚠️ Sinal reprovado pelos critérios de segurança."

                # PAINEL PREMIUM DE ANÁLISE
                st.markdown("<div class='glass-card' style='text-align: left; padding: 25px;'>", unsafe_allow_html=True)
                st.subheader("📊 DIAGNÓSTICO DO ALGORITMO IA")
                
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                with col_a1:
                    if decisao_val == "COMPRA":
                        badge = "<span class='buy-badge'>🟢 COMPRA</span>"
                    elif decisao_val == "VENDA":
                        badge = "<span class='sell-badge'>🔴 VENDA</span>"
                    else:
                        badge = "<span class='wait-badge'>🟡 AGUARDAR</span>"
                    st.markdown(f"**Decisão Oficial:**<br><br>{badge}", unsafe_allow_html=True)
                
                with col_a2:
                    st.metric("Confiança da IA", f"{confianca_val}%", delta="≥60% Aprovado" if confianca_val >= 60 else "<60% Reprovado")
                
                with col_a3:
                    st.metric("Probabilidade TP", f"{chance_tp_val}%")
                
                with col_a4:
                    st.metric("Alvo Estimado", f"+${retorno_potencial:.2f}")

                st.markdown("---")
                st.write(f"**Parecer Técnico da Inteligência Artificial:**")
                st.write(resposta_texto)
                st.caption(f"🛡️ **Gestão:** {filtro_msg}")
                st.markdown("</div>", unsafe_allow_html=True)

                if auto_trading and decisao_val in ["COMPRA", "VENDA"] and confianca_val >= 60:
                    if not metaapi_token or not metaapi_account_id:
                        st.error("⚠️ Preencha MetaApi Token e Account ID para enviar a ordem.")
                    else:
                        acao = "BUY" if decisao_val == "COMPRA" else "SELL"
                        simbolo_mt5 = ativo_selecionado.split()[0]
                        
                        st.info(f"⚡ Enviando ordem de **{acao}** ({lote_calculado} lotes) na Exness via MetaApi...")
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        sucesso, msg = loop.run_until_complete(
                            executar_ordem_exness(metaapi_token, metaapi_account_id, simbolo_mt5, acao, lote_calculado, sl_pips, tp_pips)
                        )
                        
                        if sucesso:
                            st.success(f"🎉 {msg}")
                            st.session_state.historico_ordens.append({
                                "Hora": datetime.datetime.now().strftime("%H:%M:%S"),
                                "Ativo": simbolo_mt5,
                                "Ação": acao,
                                "Lote": lote_calculado,
                                "Risco ($)": f"${valor_em_risco:.2f}",
                                "Alvo ($)": f"+${retorno_potencial:.2f}",
                                "Confiança": f"{confianca_val}%",
                                "Prob. TP": f"{chance_tp_val}%"
                            })
                        else:
                            st.error(f"❌ Falha ao executar ordem: {msg}")

if st.session_state.historico_ordens:
    st.markdown("---")
    st.subheader("📜 Histórico de Ordens da Sessão")
    st.dataframe(pd.DataFrame(st.session_state.historico_ordens), use_container_width=True)
