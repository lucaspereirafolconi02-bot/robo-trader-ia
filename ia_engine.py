import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_KEY"))

def tomar_decisao_quant(ativo, preco_atual, rsi_14, ema_20, ema_200):
    model = genai.GenerativeModel('gemini-1.5-flash')
    tendencia = "ALTA" if ema_20 > ema_200 else "BAIXA"
    
    prompt = f"""
    Atue como um algoritmo quantitativo. Analise o ativo {ativo}:
    - Preço Atual: {preco_atual}
    - RSI (14): {rsi_14}
    - EMA 20: {ema_20} | EMA 200: {ema_200} ({tendencia})

    Regras:
    - COMPRA se RSI < 35 e tendência de ALTA.
    - VENDA se RSI > 65 e tendência de BAIXA.
    - Senão, AGUARDAR.

    Retorne estritamente em JSON:
    {{
        "acao": "COMPRA" | "VENDA" | "AGUARDAR",
        "confianca_pct": 85,
        "motivo": "resumo de 1 frase",
        "tp_pips": 40,
        "sl_pips": 20
    }}
    """
    try:
        response = model.generate_content(prompt)
        texto = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto)
    except Exception as e:
        return {"acao": "AGUARDAR", "confianca_pct": 0, "motivo": f"Erro IA: {e}", "tp_pips": 0, "sl_pips": 0}
