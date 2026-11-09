
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st
from core.db import init_db, insert_transactions, fetch_all
from core.parser import parse_invoice
from core.calculator import enrich, stock_report, portfolio_summary, hold_vs_flip

st.set_page_config(page_title="محلل فواتير البورصة المصرية", layout="wide")
st.markdown("<style>body{direction:rtl; text-align:right}</style>", unsafe_allow_html=True)
st.title("📈 محلل فواتير التداول - البورصة المصرية")
st.caption("ارفع صور فواتير حركة التداول وسيقرأها الذكاء الاصطناعي ويحسب أرباحك وعمولاتك")

init_db()

if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ ضع مفتاح الـ API في ملف .env (انسخ .env.example وعدّله) ثم أعد التشغيل")
    st.stop()

tab1, tab2, tab3 = st.tabs(["⬆️ رفع فواتير جديدة", "📊 تقرير المحفظة", "⚖️ الاحتفاظ vs اليومية"])

with tab1:
    files = st.file_uploader("ارفع صور الفواتير (JPG/PNG) — ممكن أكتر من صورة",
                             type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if files and st.button("🔍 اقرأ الفواتير وحسب", type="primary"):
        total = 0
        for f in files:
            with st.spinner(f"جاري قراءة {f.name}..."):
                try:
                    txs = parse_invoice(f.getvalue())
                    insert_transactions(txs)
                    total += len(txs)
                    st.success(f"✅ {f.name}: استخرجت {len(txs)} عملية")
                except Exception as e:
                    st.error(f"❌ {f.name}: {e}")
        st.info(f"إجمالي العمليات المضافة: {total}")

df = enrich(pd.DataFrame(fetch_all()))

with tab2:
    if df.empty:
        st.warning("لا توجد عمليات بعد — ارفع الفواتير أولاً")
    else:
        for k, v in portfolio_summary(df).items():
            st.metric(k, f"{v:,.2f}" if isinstance(v, (int, float)) else v)
        st.subheader("تقرير لكل سهم")
        st.dataframe(stock_report(df), use_container_width=True)
        st.subheader("كل العمليات")
        st.dataframe(df, use_container_width=True)

with tab3:
    if not df.empty:
        st.write(hold_vs_flip(df))
        sells = df[df["side"] == "بيع"]
        if not sells.empty:
            comm_round_trip = portfolio_summary(df)["نسبة العمولات من التداول %"] * 2
            st.subheader("📐 حاسبة سعر التعادل")
            buy_price = st.number_input("متوسط سعر شرائك", min_value=0.0, value=10.0, step=0.05)
            st.metric("لازم تبيع فوق", f"{buy_price * (1 + comm_round_trip/100):.3f} جنيه",
                      f"وإلا العمولة تاكل ربحك ({comm_round_trip:.2f}%)")
