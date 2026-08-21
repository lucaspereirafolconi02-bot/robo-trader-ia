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
st.set_page_config(page_title="Robô Trader IA - Gestão & Análise Avançada", page_icon="🤖", layout="wide")

if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []
if "total_execucoes" not in st.session_state:
    st.session_state.total_execucoes = 0

# --- DESIGN CYBERPUNK DARK ---
st.markdown("""
<style>
    .stApp, header[data-testid="stHeader"] { background-color: #060812 !important; color: #00f3ff !important; font-family: 'Segoe UI', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #0b0e1e !important; border-right: 2px solid #00f3ff; }
    h1, h2, h3, h4 { color: #00f3ff !important; text-shadow: 0 0 12px rgba(0, 243, 255, 0.7); }
    .metric-card { background: #0f152d; border: 1px solid #00f3ff; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 0 10px rgba(0,243,255,0.2); }
    .analysis-card {
        background: #0d122b;
        border: 2px solid #00f3ff;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.25);
    }
    .buy-badge { background-color: #00ff66; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 16px; }
    .sell-badge { background-color: #ff3366; color: #fff; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 16px; }
    .wait-badge { background-color: #ffcc00; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🤖 ROBÔ TRADER IA ⚡ ANÁLISE & GESTÃO PROFISSIONAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f3ff;'>Filtro Automático ≥ 60% de Confiança | Cálculo de Risco x Retorno Inteligente</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR: CONEXÃO E RISCO ---
st.sidebar.header("🔑 CONEXÃO")
gemini_key = st.sidebar.text_input("API Key Gemini:", type="password")
metaapi_token = st.sidebar.text_input("MetaApi Token:", type="password")
metaapi_account_id = st.sidebar.text_input("MetaApi Account ID:", type="password")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ GESTÃO DE BANCA & RISCO")
saldo_banca = st.sidebar.number_input("💵 Saldo Atual da Banca ($):", value=1000.0, step=100.0)
risco_por_operacao = st.sidebar.slider("🎯 Risco por Entrada (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

tp_pips = st.sidebar.number_input("🎯 Take Profit (Pips):", value=200, step=10)
sl_pips = st.sidebar.number_input("🛡️ Stop Loss (Pips):", value=100, step=10)
auto_trading = st.sidebar.checkbox("⚡ Enviar Ordens Reais na Exness", value=False)

# CÁLCULOS MATEMÁTICOS DE GESTÃO
valor_em_risco = saldo_banca * (risco_por_operacao / 100)
retorno_potencial = valor_em_risco * (tp_pips / sl_pips)
lote_calculado = max(0.01, round(valor_em_risco / (sl_pips * 10), 2))

st.sidebar.info(f"""
💡 **Resumo de Gestão:**
- **Risco ($):** ${valor_em_risco:.2f} ({risco_por_operacao}%)
- **Retorno Potencial ($):** ${retorno_potencial:.2f}
- **Relação Risco/Retorno:** 1 : {tp_pips/sl_pips:.1f}
- **Lote Recom.:** {lote_calculado}
""")

ativos = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "GBPJPY": "GBPJPY=X", "AUDUSD": "AUDUSD=X", "USDCAD": "CAD=X",
    "XAUUSD (Ouro)": "GC=F", "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD",
    "US500 (S&P500)": "^GSPC", "US30 (Dow Jones)": "^DJI"
}
ativo_selecionado = st.sidebar.selectbox("📈 Ativo para Análise:", list(ativos.keys()))

# --- METRICAS DE OPERAÇÃO DA SESSÃO ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-card'><h4>Banca Atual</h4><h3>${saldo_banca:,.2f}</h3></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><h4>Risco da Ordem</h4><h3>${valor_em_risco:,.2f} ({risco_por_operacao}%)</h3></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><h4>Lucro Alvo (TP)</h4><h3>+${retorno_potencial:,.2f}</h3></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card'><h4>Execuções Hoje</h4><h3>{st.session_state.total_execucoes}</h3></div>", unsafe_allow_html=True)

st.markdown("---")

# FUNÇÃO METAAPI
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

# --- EXECUÇÃO COM ANÁLISE AVANÇADA DA IA ---
if st.button("🚀 ANALISAR MERCADO E CALCULAR SINAL VIA IA", use_container_width=True):
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

            Responda OBRIGATORIAMENTE no seguinte formato estruturado:
            DECISÃO: [COMPRA / VENDA / AGUARDAR]
            CONFIANÇA: [Insira número de 0 a 100]%
            CHANCE_TP: [Insira número de 0 a 100]%
            JUSTIFICATIVA: [Breve explicação técnica da entrada em até 2 frases]
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

                # TRAVA DE SEGURANÇA: CONFIANÇA MÍNIMA DE 60%
                if confianca_val < 60 and decisao_val != "AGUARDAR":
                    decisao_val = "AGUARDAR"
                    filtro_msg = "⚠️ Confiança abaixo de 60%. Entrada bloqueada pela gestão de risco."
                else:
                    filtro_msg = "✅ Filtro de Confiança Aprovado (≥ 60%)." if confianca_val >= 60 else "⚠️ Sinal reprovado pelos critérios de segurança."

                # PAINEL PREMIUM DE ANÁLISE DA IA
                st.markdown("<div class='analysis-card'>", unsafe_allow_html=True)
                st.subheader("📊 PAINEL DE ANÁLISE IA & ESTIMATIVA DE RESULTADO")
                
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                with col_a1:
                    if decisao_val == "COMPRA":
                        badge = "<span class='buy-badge'>🟢 COMPRA</span>"
                    elif decisao_val == "VENDA":
                        badge = "<span class='sell-badge'>🔴 VENDA</span>"
                    else:
                        badge = "<span class='wait-badge'>🟡 AGUARDAR</span>"
                    st.markdown(f"**Decisão da IA:**<br><br>{badge}", unsafe_allow_html=True)
                
                with col_a2:
                    st.metric("Confiança da IA", f"{confianca_val}%", delta="Aprovado (≥60%)" if confianca_val >= 60 else "Reprovado (<60%)")
                
                with col_a3:
                    st.metric("Chance de Bater TP", f"{chance_tp_val}%")
                
                with col_a4:
                    st.metric("Lucro Estimado", f"+${retorno_potencial:.2f}", help=f"Risco de ${valor_em_risco:.2f}")

                st.markdown("---")
                st.write(f"**Diagnóstico Detalhado:**")
                st.write(resposta_texto)
                st.caption(f"🛡️ **Gestão:** {filtro_msg}")
                st.markdown("</div>", unsafe_allow_html=True)

                # EXECUÇÃO DA ORDEM
                if auto_trading and decisao_val in ["COMPRA", "VENDA"] and confianca_val >= 60:
                    if not metaapi_token or not metaapi_account_id:
                        st.error("⚠️ Preencha MetaApi Token e Account ID para enviar a ordem.")
                    else:
                        acao = "BUY" if decisao_val == "COMPRA" else "SELL"
                        simbolo_mt5 = ativo_selecionado.split()[0]
                        
                        st.info(f"⚡ Executando ordem real de **{acao}** ({lote_calculado} lotes) na Exness...")
                        
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
