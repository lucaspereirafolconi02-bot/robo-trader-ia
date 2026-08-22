import os
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)

ATIVOS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "GC=F": "XAU/USD (Ouro)",
    "BTC-USD": "BTC/USD"
}

BANCA_USD = 1000.00
RISCO_PCT = 0.021
RISCO_USD = BANCA_USD * RISCO_PCT

def calcular_confluencia_probabilistica(df):
    """Calcula score matemático de alta probabilidade baseado em tendência, momento e volatilidade."""
    # Médias Móveis
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # Bandas de Bollinger (20, 2)
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper_Band'] = df['SMA20'] + (df['STD20'] * 2)
    df['Lower_Band'] = df['SMA20'] - (df['STD20'] * 2)
    
    # ATR (14) para Stop Loss e Take Profit Dinâmico
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    df['ATR'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
    
    return df

async def analisar_e_executar():
    print("🚀 Iniciando Motor Probabilístico Quant + IA...\n")
    model = genai.GenerativeModel('gemini-2.5-flash')

    for ticker, nome_ativo in ATIVOS.items():
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if len(df) < 30:
            continue
            
        df = calcular_confluencia_probabilistica(df)
        ultimo = df.iloc[-1]
        
        preco = float(ultimo['Close'])
        ema9, ema20 = float(ultimo['EMA9']), float(ultimo['EMA20'])
        rsi, atr = float(ultimo['RSI']), float(ultimo['ATR'])
        upper_b, lower_b = float(ultimo['Upper_Band']), float(ultimo['Lower_Band'])
        
        # --- FILTRO QUANTITATIVO DE PROBABILIDADE ---
        score = 0
        if ema9 > ema20: score += 1      # Tendência de alta
        if 48 <= rsi <= 62: score += 1   # Momento comprador sem exaustão
        if preco > lower_b and preco < (upper_b * 0.998): score += 1 # Espaço para expansão
        
        if ema9 < ema20: score -= 1      # Tendência de baixa
        if 38 <= rsi <= 52: score -= 1   # Momento vendedor sem exaustão
        
        # Gestão Dinâmica ATR (Risk/Reward 1:1.6)
        sl_pips = int((atr * 1.5) * 10000) if "USD" in ticker else int(atr * 1.5)
        tp_pips = int(sl_pips * 1.6)
        alvo_usd = RISCO_USD * 1.6

        # Só envia para a IA se o modelo matemático atingir confluência relevante
        if abs(score) < 2:
            print(f"   ⏳ {nome_ativo}: Score insuficiente ({score}). Aguardando alinhamento...")
            continue

        prompt = f"""
        Você é um algoritmo de alta frequência e gestão de risco.
        Valide esta oportunidade probabilística para o ativo {nome_ativo}:
        - Preço Atual: {preco:.5f}
        - EMA9: {ema9:.5f} | EMA20: {ema20:.5f}
        - RSI(14): {rsi:.2f} | ATR: {atr:.5f}
        - Score do Modelo: {score}
        
        Regras de Validação:
        1. Se Score > 0 e tendência confirmada -> Apenas "COMPRA".
        2. Se Score < 0 e tendência confirmada -> Apenas "VENDA".
        3. Se houver divergência clara -> Apenas "AGUARDAR".
        
        Responda EXATAMENTE uma palavra: COMPRA, VENDA ou AGUARDAR.
        """

        try:
            resposta = model.generate_content(prompt)
            acao = resposta.text.strip().upper()
            
            if acao in ["COMPRA", "VENDA"]:
                supabase.table('ordens').insert({
                    "ativo": nome_ativo,
                    "acao": acao,
                    "tp_pips": tp_pips,
                    "sl_pips": sl_pips,
                    "risco_usd": RISCO_USD,
                    "alvo_usd": alvo_usd,
                    "confianca": f"PROBABILISTICO_SCORE_{score}"
                }).execute()
                print(f"   ✅ Entrada executada em {nome_ativo}: {acao} (TP: {tp_pips} pips / SL: {sl_pips} pips)")
        except Exception as e:
            print(f"   ❌ Erro na análise de {nome_ativo}: {e}")

if __name__ == "__main__":
    asyncio.run(analisar_e_executar())
