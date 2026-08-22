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
RISCO_USD = BANCA_USD * 0.021  # Risco fixo de 2.1% ($21.00)

def calcular_indicadores(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    df['ATR'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
    return df

async def analisar_e_executar():
    model = genai.GenerativeModel('gemini-2.5-flash')

    for ticker, nome_ativo in ATIVOS.items():
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if len(df) < 30:
            continue
            
        df = calcular_indicadores(df)
        ultimo = df.iloc[-1]
        preco, ema9, ema20, rsi, atr = float(ultimo['Close']), float(ultimo['EMA9']), float(ultimo['EMA20']), float(ultimo['RSI']), float(ultimo['ATR'])
        
        sl_pips = int((atr * 1.5) * 10000) if "USD" in ticker else int(atr * 1.5)
        tp_pips = int(sl_pips * 1.6)
        alvo_usd = RISCO_USD * 1.6

        prompt = f"""
        Analise a estrutura técnica do ativo {nome_ativo}:
        - Preço: {preco:.5f} | EMA9: {ema9:.5f} | EMA20: {ema20:.5f} | RSI: {rsi:.2f} | ATR: {atr:.5f}
        
        Regras:
        - EMA9 > EMA20 e RSI entre 45 e 65 -> COMPRA
        - EMA9 < EMA20 e RSI entre 35 e 55 -> VENDA
        - Fora disso ou RSI > 70 / < 30 -> AGUARDAR
        
        Responda APENAS em uma palavra: COMPRA, VENDA ou AGUARDAR.
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
                    "confianca": "ALTA_IA"
                }).execute()
        except Exception as e:
            print(f"Erro em {nome_ativo}: {e}")

if __name__ == "__main__":
    asyncio.run(analisar_e_executar())
