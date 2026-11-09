
import pandas as pd

COMMISSION_RATE = 0.00285  # 0.25% وسيط + 0.035% رسوم بورصة ومقاصة — عدّل حسب شركتك

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # عمولة تقديرية لو الفاتورة مش مكتوبة
    df["commission"] = df.apply(
        lambda r: r["commission"] if r["commission"] and r["commission"] > 0
        else round(r["gross"] * COMMISSION_RATE, 2), axis=1)
    df["net"] = df.apply(
        lambda r: round(r["gross"] - r["commission"], 2) if r["side"] == "بيع"
        else round(-(r["gross"] + r["commission"]), 2), axis=1)
    return df

def stock_report(df: pd.DataFrame) -> pd.DataFrame:
    """تقرير لكل سهم: متوسط شراء/بيع، صافي الربح، نسبة الربح الفعلية"""
    if df.empty: return df
    rows = []
    for stock, g in df.groupby("stock"):
        buys  = g[g["side"] == "شراء"]
        sells = g[g["side"] == "بيع"]
        buy_qty, sell_qty = buys["qty"].sum(), sells["qty"].sum()
        buy_cost  = (buys["gross"] + buys["commission"]).sum()
        sell_gain = (sells["gross"] - sells["commission"]).sum()
        avg_buy   = buy_cost / buy_qty if buy_qty else 0
        avg_sell  = sell_gain / sell_qty if sell_qty else 0
        realized  = sell_gain - (avg_buy * sell_qty) if sell_qty else 0
        # المحجوز حالياً
        open_qty = buy_qty - sell_qty
        open_cost = (buy_cost - avg_buy * sell_qty) if open_qty > 0 else 0
        profit_pct = realized / (avg_buy * sell_qty) * 100 if sell_qty and avg_buy else 0
        rows.append({"السهم": stock, "متوسط الشراء": round(avg_buy, 3),
            "متوسط البيع": round(avg_sell, 3), "الكمية المباعة": sell_qty,
            "الكمية المحتفظ بها": open_qty, "تكلفة المحتفظ": round(open_cost, 2),
            "الربح المحقق": round(realized, 2), "نسبة الربح %": round(profit_pct, 2),
            "إجمالي العمولات": round(g["commission"].sum(), 2)})
    return pd.DataFrame(rows)

def portfolio_summary(df: pd.DataFrame) -> dict:
    if df.empty: return {}
    total_comm = df["commission"].sum()
    turnover   = df["gross"].sum()
    net_flow   = df["net"].sum()
    return {
        "إجمالي قيمة التداول": round(turnover, 2),
        "إجمالي العمولات المدفوعة": round(total_comm, 2),
        "نسبة العمولات من التداول %": round(total_comm / turnover * 100, 3) if turnover else 0,
        "صافي التدفق النقدي (نمو/انكماش المحفظة)": round(net_flow, 2),
        "عدد العمليات": len(df),
    }

def hold_vs_flip(df: pd.DataFrame) -> str:
    """مقارنة: لو كنت احتفظت بالسهم بدل البيع اليومي"""
    if df.empty: return ""
    comm_paid = df["commission"].sum()
    sells = df[df["side"] == "بيع"]
    total_comm_pct = portfolio_summary(df)["نسبة العمولات من التداول %"]
    flip_cost = total_comm_pct * 2  # تكلفة دورة شراء+بيع كاملة
    verdict = ("التداول اليومي مكلف جداً — تكلفة الدورة الواحدة "
               f"{flip_cost:.2f}%، يعني سهمك لازم يتحرك أكتر من كده عشان تكسب. "
               "الاحتفاظ بالسهم أرجح إلا لو معدل نجاحك اليومي مثبت أعلى من التكلفة.")
    return (f"💰 دفعت عمولات بقيمة {comm_paid:,.0f} جنيه على قيمة تداول "
            f"{df['gross'].sum():,.0f} جنيه ({total_comm_pct:.2f}%). {verdict}")
