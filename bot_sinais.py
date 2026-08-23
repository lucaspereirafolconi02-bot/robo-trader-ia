import os
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="QUANTIA CORE | AI Dashboard", page_icon="⚡", layout="wide")

supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if supabase_url and supabase_key:
        return create_client(supabase_url, supabase_key)
    return None

supabase = init_supabase()

st.title("⚡ QUANTIA CORE — Central de Controle IA")

if supabase:
    try:
        res = supabase.table("conta_status").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            d = res.data[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Saldo Real", f"${d['saldo']:.2f}")
            c2.metric("📈 Patrimônio (Equity)", f"${d.get('equity', d['saldo']):.2f}")
            c3.metric("📊 Lucro Aberto", f"${d.get('lucro_flutuante', 0.0):.2f}")
        else:
            st.info("ℹ️ Aguardando sincronização da conta...")
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
else:
    st.error("⚠️ Configuração do Supabase pendente.")

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 Ordens do Robô")
    if supabase:
        try:
            ordens_res = supabase.table("ordens").select("*").order("created_at", desc=True).limit(5).execute()
            if ordens_res.data:
                st.dataframe(ordens_res.data, use_container_width=True)
            else:
                st.write("Nenhuma ordem registrada.")
        except Exception as e:
            st.write("Aguardando histórico...")

with col_right:
    st.subheader("📈 Gráfico em Tempo Real")
    tv_code = """
    <div class="tradingview-widget-container" style="height:400px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
          "autosize": true, "symbol": "FX:EURUSD", "interval": "5",
          "timezone": "America/Sao_Paulo", "theme": "dark", "style": "1",
          "locale": "br", "backgroundColor": "rgba(14, 17, 23, 1)",
          "container_id": "tradingview_chart"
      });
      </script>
    </div>
    """
    components.html(tv_code, height=410)
