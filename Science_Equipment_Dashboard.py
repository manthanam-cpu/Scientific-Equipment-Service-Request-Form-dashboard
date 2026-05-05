import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide"
)

st.markdown("""
<style>
.metric-card {
    padding: 20px; border-radius: 15px; color: white;
    text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}
.metric-card h2 { font-size: 2.5rem; margin: 0; font-weight: 700; }
.metric-card p  { margin: 5px 0 0 0; font-size: 1rem; opacity: 0.9; }
.ai-box {
    background: linear-gradient(135deg,#11998e,#38ef7d);
    border-radius: 15px; padding: 15px; color: white; margin-bottom:10px;
}
.alert-box {
    background: linear-gradient(135deg,#f093fb,#f5576c);
    border-radius: 15px; padding: 15px; color: white; margin-bottom:10px;
}
#MainMenu {visibility:hidden;} footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/"
    "export?format=csv&gid=1562070767"
)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        return pd.DataFrame(), str(e)

    # Timestamp
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # Mask ชื่อ
    # ค้นหาคอลัมน์ชื่อจริง
    name_col = None
    for c in df.columns:
        if "ชื่อ" in c and "สกุล" in c:
            name_col = c
            break

    if name_col:
        def mask_name(v):
            v = str(v).strip()
            if not v or v.lower() == "nan":
                return "-"
            p = v.split()
            if len(p) >= 2:
                return f"{p} {p}***"
            return v + "***" if v else "-"
        df[name_col] = df[name_col].apply(mask_name)

    # Mask เบอร์
    phone_col = None
    for c in df.columns:
        if "เบอร์" in c or "โทร" in c:
            phone_col = c
            break

    if phone_col:
        def mask_phone(v):
            v = str(v).strip()
            if not v or v.lower() == "nan":
                return "-"
            v = v.replace(".0", "")
            return f"{v[:3]}-XXX-{v[-4:]}" if len(v) >= 9 else "-"
        df[phone_col] = df[phone_col].apply(mask_phone)

    # Mask Email — วนทีละคอลัมน์
    def mask_email(v):
        v = str(v).strip()
        if not v or v.lower() == "nan":
            return "-"
        if "@" in v:
            a, b = v.split("@", 1)
            return f"{a}***@{b}" if a else f"***@{b}"
        return "-"

    for c in list(df.columns):
        if "email" in c.lower() or "e-mail" in c.lower() or "อีเมล" in c:
            df[c] = df[c].apply(mask_email)

    # คอลัมน์ช่วยคำนวณ
    if "Timestamp" in df.columns:
        df["_month_dt"] = (
            df["Timestamp"].dt.to_period("M").dt.to_timestamp()
        )
        df["_dow"]  = df["Timestamp"].dt.day_name()
        df["_hour"] = df["Timestamp"].dt.hour

    return df, ""


# ============================================================
# ฟังก์ชันหาคอลัมน์ — คืน str เดี่ยว หรือ None
# ============================================================
def find_col(columns: list, keywords: list):
    """คืน str ชื่อคอลัมน์แรกที่ตรงกับ keyword — ไม่คืน list"""
    for col in columns:
        for kw in keywords:
            if kw in col:
                return col   # str เดี่ยว
    return None


# ============================================================
# MAIN
# ============================================================
df, load_err = load_data()

if df.empty:
    st.error(f"❌ โหลดข้อมูลไม่ได้: {load_err}")
    st.stop()

all_cols = list(df.columns)

# --- ตรวจหาคอลัมน์ทั้งหมด (str เดี่ยว | None) ---
STATUS_COL     = find_col(all_cols, ["สถานะ"])
RETURN_COL     = find_col(all_cols, ["การคืน"])
USERTYPE_COL   = find_col(all_cols, ["ประเภทผู้ใช้", "ประเภท"])
DEPT_COL       = find_col(all_cols, ["คณะ", "หน่วยงาน"])
TOOL_COL       = find_col(all_cols, ["เครื่องมือ", "อุปกรณ์"])
LOCATION_COL   = find_col(all_cols, ["โรงเรือน", "สถานที่", "ห้อง"])
PURPOSE_COL    = find_col(all_cols, ["วัตถุประสงค์", "จุดประสงค์", "เรื่อง"])
NAME_COL       = find_col(all_cols, ["ชื่อ-สกุล", "ชื่อ", "name"])
PHONE_COL      = find_col(all_cols, ["เบอร์", "โทร", "phone"])
EMAIL_COL      = find_col(all_cols, ["Email Address", "E-mail",
                                      "email", "อีเมล"])
DATE_END_COL   = None
DATE_START_COL = None

for c in all_cols:
    if "วันที่" in c and any(k in c for k in ["สิ้น","คืน","สุด"]):
        DATE_END_COL = c
    if "วันที่" in c and any(k in c for k in ["เริ่ม","ต้น"]):
        DATE_START_COL = c

# แปลงวันที่
if DATE_START_COL:
    df[DATE_START_COL] = pd.to_datetime(
        df[DATE_START_COL], errors="coerce"
    )
if DATE_END_COL:
    df[DATE_END_COL] = pd.to_datetime(
        df[DATE_END_COL], errors="coerce"
    )

# เติมค่าว่าง
for c in [USERTYPE_COL, DEPT_COL, TOOL_COL, LOCATION_COL]:
    if c:
        df[c] = df[c].fillna("ไม่ระบุ")
if STATUS_COL:
    df[STATUS_COL] = df[STATUS_COL].fillna("ยังไม่ระบุสถานะ")
if RETURN_COL:
    df[RETURN_COL] = df[RETURN_COL].fillna("ยังไม่ระบุข้อมูล")

# Debug
with st.expander("🔍 Debug: คอลัมน์ที่ตรวจพบ"):
    st.json({
        "STATUS_COL":    STATUS_COL,
        "RETURN_COL":    RETURN_COL,
        "USERTYPE_COL":  USERTYPE_COL,
        "DEPT_COL":      DEPT_COL,
        "TOOL_COL":      TOOL_COL,
        "LOCATION_COL":  LOCATION_COL,
        "PURPOSE_COL":   PURPOSE_COL,
        "NAME_COL":      NAME_COL,
        "PHONE_COL":     PHONE_COL,
        "EMAIL_COL":     EMAIL_COL,
        "DATE_END_COL":  DATE_END_COL,
        "DATE_START_COL":DATE_START_COL,
        "ALL_COLUMNS":   all_cols,
    })

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🔽 ตัวกรองข้อมูล")

    sel_type = "ทั้งหมด"
    if USERTYPE_COL:
        vals = sorted(df[USERTYPE_COL].dropna().unique().tolist())
        sel_type = st.selectbox(
            "👤 ประเภทผู้ใช้", ["ทั้งหมด"] + vals
        )

    sel_dept = "ทั้งหมด"
    if DEPT_COL:
        vals = sorted(df[DEPT_COL].dropna().unique().tolist())
        sel_dept = st.selectbox(
            "🏫 คณะ/หน่วยงาน", ["ทั้งหมด"] + vals
        )

    sel_status = "ทั้งหมด"
    if STATUS_COL:
        vals = sorted(df[STATUS_COL].dropna().unique().tolist())
        sel_status = st.selectbox(
            "📋 สถานะอนุมัติ", ["ทั้งหมด"] + vals
        )

    sel_return = "ทั้งหมด"
    if RETURN_COL:
        vals = sorted(df[RETURN_COL].dropna().unique().tolist())
        sel_return = st.selectbox(
            "📦 สถานะคืน", ["ทั้งหมด"] + vals
        )

    st.markdown("---")
    st.markdown("📅 **ช่วงเวลา**")

    # ✅ แก้ date_range — ป้องกัน TypeError
    min_date = None
    max_date = None
    date_start_filter = None
    date_end_filter   = None

    if "Timestamp" in df.columns:
        valid_ts = df["Timestamp"].dropna()
        if not valid_ts.empty:
            min_date = valid_ts.min().date()
            max_date = valid_ts.max().date()

            raw_range = st.date_input(
                "เลือกช่วงวันที่",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="date_range_input"
            )

            # ✅ ตรวจสอบว่า raw_range เป็น tuple/list ที่มี 2 ค่า
            if isinstance(raw_range, (list, tuple)) and len(raw_range) == 2:
                date_start_filter = pd.Timestamp(raw_range)
                date_end_filter   = (
                    pd.Timestamp(raw_range) + pd.Timedelta(days=1)
                )
            elif hasattr(raw_range, "year"):
                # กรณีเลือกวันเดียว → ใช้วันนั้นทั้งวัน
                date_start_filter = pd.Timestamp(raw_range)
                date_end_filter   = (
                    pd.Timestamp(raw_range) + pd.Timedelta(days=1)
                )

    st.markdown("---")
    if st.button("🔄 รีเฟรช"):
        st.cache_data.clear()
        st.rerun()
    st.caption(
        f"อัปเดต: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
    )

# ============================================================
# FILTER DATA
# ============================================================
dff = df.copy()

if sel_type   != "ทั้งหมด" and USERTYPE_COL:
    dff = dff[dff[USERTYPE_COL] == sel_type]
if sel_dept   != "ทั้งหมด" and DEPT_COL:
    dff = dff[dff[DEPT_COL]     == sel_dept]
if sel_status != "ทั้งหมด" and STATUS_COL:
    dff = dff[dff[STATUS_COL]   == sel_status]
if sel_return != "ทั้งหมด" and RETURN_COL:
    dff = dff[dff[RETURN_COL]   == sel_return]

# ✅ กรองวันที่ — ปลอดภัย ไม่ TypeError
if (date_start_filter is not None
        and date_end_filter is not None
        and "Timestamp" in dff.columns):
    dff = dff[
        (dff["Timestamp"] >= date_start_filter) &
        (dff["Timestamp"] <  date_end_filter)
    ]

NOW        = pd.Timestamp.now()
THIS_MONTH = NOW.to_period("M")
total      = len(dff)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style='background:linear-gradient(135deg,#667eea,#764ba2);
            padding:30px;border-radius:20px;margin-bottom:20px;
            color:white;text-align:center;'>
  <h1 style='margin:0;font-size:2rem;'>
    🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์
  </h1>
  <p style='margin:8px 0 0 0;opacity:.85;'>
    Science Equipment Dashboard — AI Enhanced
  </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI
# ============================================================
st.subheader("📊 KPI Scorecard")

this_m = 0
if "Timestamp" in dff.columns:
    this_m = int(
        (dff["Timestamp"].dt.to_period("M") == THIS_MONTH).sum()
    )

pending = 0
if STATUS_COL:
    pending = total - int((dff[STATUS_COL] == "อนุมัติแล้ว").sum())

returned = 0
if RETURN_COL:
    returned = int((dff[RETURN_COL] == "คืนเรียบร้อย").sum())

overdue = 0
if DATE_END_COL and RETURN_COL:
    overdue = int(
        ((dff[DATE_END_COL] < NOW) &
         (dff[RETURN_COL] != "คืนเรียบร้อย")).sum()
    )

u_types = dff[USERTYPE_COL].nunique() if USERTYPE_COL else 0

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_cfg = [
    (k1, total,    "📝 คำขอทั้งหมด",  "#667eea,#764ba2"),
    (k2, this_m,   "📅 เดือนนี้",     "#f093fb,#f5576c"),
    (k3, pending,  "⏳ รออนุมัติ",    "#f6d365,#fda085"),
    (k4, returned, "✅ คืนแล้ว",      "#43e97b,#38f9d7"),
    (k5, overdue,  "🚨 เกินกำหนด",    "#f5576c,#f093fb"),
    (k6, u_types,  "👥 ประเภทผู้ใช้", "#4facfe,#00f2fe"),
]
for col_obj, val, label, grad in kpi_cfg:
    g1, g2 = grad.split(",")
    with col_obj:
        st.markdown(
            f"<div class='metric-card' "
            f"style='background:linear-gradient(135deg,{g1},{g2});'>"
            f"<h2>{val}</h2><p>{label}</p></div>",
            unsafe_allow_html=True
        )

st.markdown("---")

# ============================================================
# AI INSIGHT
# ============================================================
st.subheader("🤖 AI Insight")

def ai_insight(dff, total, overdue):
    ins, wrn = [], []
    if total == 0:
        return ["ไม่มีข้อมูลในช่วงที่เลือก"], []

    if "_month_dt" in dff.columns:
        m = (dff.groupby("_month_dt").size()
               .reset_index(name="n")
               .sort_values("_month_dt"))
        if len(m) >= 2:
            last = int(m.iloc[-1]["n"])
            prev = int(m.iloc[-2]["n"])
            mn   = m.iloc[-1]["_month_dt"].strftime("%b %Y")
            pct  = (last - prev) / prev * 100 if prev else 0
            ins.append(
                f"{'📈' if pct>=0 else '📉'} เดือน {mn}: "
                f"**{last} รายการ** "
                f"({'เพิ่ม' if pct>=0 else 'ลด'} {abs(pct):.1f}%)"
            )

    if USERTYPE_COL:
        vc = dff[USERTYPE_COL].value_counts()
        if not vc.empty:
            ins.append(
                f"👤 กลุ่มมากสุด: **{vc.idxmax()}** "
                f"({vc.max()} รายการ, {vc.max()/total*100:.1f}%)"
            )

    if DEPT_COL:
        vc = dff[DEPT_COL].value_counts()
        if not vc.empty:
            ins.append(
                f"🏫 คณะมากสุด: **{vc.idxmax()}** ({vc.max()} รายการ)"
            )

    if "_hour" in dff.columns:
        vc = dff["_hour"].value_counts()
        if not vc.empty:
            h = int(vc.idxmax())
            ins.append(f"⏰ ช่วงยอดนิยม: **{h}:00–{h+1}:00 น.**")

    if "_dow" in dff.columns:
        dm = {
            "Monday":"จันทร์","Tuesday":"อังคาร",
            "Wednesday":"พุธ","Thursday":"พฤหัสบดี",
            "Friday":"ศุกร์","Saturday":"เสาร์","Sunday":"อาทิตย์"
        }
        vc = dff["_dow"].value_counts()
        if not vc.empty:
            ins.append(
                f"📅 วันมากสุด: **วัน{dm.get(vc.idxmax(), vc.idxmax())}**"
            )

    if RETURN_COL:
        r    = int((dff[RETURN_COL] == "คืนเรียบร้อย").sum())
        rate = r / total * 100
        if rate < 50:
            wrn.append(
                f"⚠️ อัตราคืน **{rate:.1f}%** — "
                f"ยังค้างอยู่ {total-r} รายการ"
            )
        else:
            ins.append(f"✅ อัตราคืน **{rate:.1f}%** — อยู่ในเกณฑ์ดี")

    if overdue > 0:
        wrn.append(
            f"🚨 เกินกำหนดคืน **{overdue} รายการ** — ติดตามด่วน!"
        )

    return ins, wrn


ins_list, wrn_list = ai_insight(dff, total, overdue)
col_a, col_b = st.columns([3, 2])

with col_a:
    st.markdown(
        "<div class='ai-box'><b>🤖 AI Analysis</b></div>",
        unsafe_allow_html=True
    )
    for i in ins_list:
        st.success(i)

with col_b:
    st.markdown(
        "<div class='alert-box'><b>🚨 AI Alert</b></div>",
        unsafe_allow_html=True
    )
    if wrn_list:
        for w in wrn_list:
            st.error(w)
    else:
        st.info("✅ ไม่มีรายการแจ้งเตือน")

st.markdown("---")

# ============================================================
# MONTHLY TREND
# ============================================================
st.subheader("📈 แนวโน้มรายเดือน")

if "_month_dt" in dff.columns and dff["_month_dt"].notna().any():
    if USERTYPE_COL:
        mdf = (
            dff.groupby(["_month_dt", USERTYPE_COL])
               .size().reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        fig = px.line(
            mdf, x="เดือน", y="จำนวน",
            color=USERTYPE_COL, markers=True,
            title="แนวโน้มรายเดือน แยกประเภทผู้ใช้",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
    else:
        mdf = (
            dff.groupby("_month_dt").size()
               .reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        fig = px.line(
            mdf, x="เดือน", y="จำนวน", markers=True,
            title="แนวโน้มรายเดือน",
            color_discrete_sequence=["#667eea"]
        )
        fig.update_traces(
            fill="tozeroy",
            fillcolor="rgba(102,126,234,0.15)"
        )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ ไม่พบข้อมูลเวลา")

st.markdown("---")

# ============================================================
# TOP 5
# ============================================================
st.subheader("🏆 Top 5")

def bar_chart(df_in, col, title, scale):
    if not col or col not in df_in.columns:
        return None
    top = df_in[col].value_counts().head(5).reset_index()
    top.columns = [col, "จำนวน"]
    fig = px.bar(
        top, x="จำนวน", y=col, orientation="h",
        title=title, color="จำนวน",
        color_continuous_scale=scale, text="จำนวน"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False
    )
    return fig


t1, t2 = st.columns(2)
with t1:
    c   = TOOL_COL or USERTYPE_COL
    ttl = "🔬 Top 5 เครื่องมือ" if TOOL_COL else "Top 5 ประเภทผู้ใช้"
    f   = bar_chart(dff, c, ttl, "Viridis")
    if f:
        st.plotly_chart(f, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบข้อมูล")

with t2:
    c   = LOCATION_COL or DEPT_COL
    ttl = "🏠 Top 5 สถานที่" if LOCATION_COL else "Top 5 คณะ/หน่วยงาน"
    f   = bar_chart(dff, c, ttl, "Oranges")
    if f:
        st.plotly_chart(f, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบข้อมูล")

st.markdown("---")

# ============================================================
# PIE CHARTS
# ============================================================
st.subheader("🎯 สัดส่วนข้อมูล")

def pie_chart(df_in, col, title, colors):
    if not col or col not in df_in.columns:
        return None
    fig = px.pie(
        df_in, names=col, title=title, hole=0.4,
        color_discrete_sequence=colors
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


r1, r2 = st.columns(2)
with r1:
    f = pie_chart(dff, USERTYPE_COL, "ประเภทผู้ใช้",
                  px.colors.qualitative.Safe)
    if f: st.plotly_chart(f, use_container_width=True)

with r2:
    f = pie_chart(dff, DEPT_COL, "คณะ/หน่วยงาน",
                  px.colors.qualitative.Pastel)
    if f: st.plotly_chart(f, use_container_width=True)

r3, r4 = st.columns(2)
with r3:
    f = pie_chart(dff, STATUS_COL, "สถานะการอนุมัติ",
                  ["#FFCC00","#2ecc71","#e74c3c","#95a5a6"])
    if f: st.plotly_chart(f, use_container_width=True)

with r4:
    f = pie_chart(dff, RETURN_COL, "สถานะการคืน",
                  ["#3498db","#95a5a6","#e67e22"])
    if f: st.plotly_chart(f, use_container_width=True)

st.markdown("---")

# ============================================================
# HEATMAP
# ============================================================
st.subheader("🗓️ Heatmap วันและเวลา")

if "_dow" in dff.columns and "_hour" in dff.columns:
    day_order = ["Monday","Tuesday","Wednesday",
                 "Thursday","Friday","Saturday","Sunday"]
    day_th    = ["จันทร์","อังคาร","พุธ",
                 "พฤหัส","ศุกร์","เสาร์","อาทิตย์"]
    hdf = (
        dff.groupby(["_dow","_hour"]).size()
           .reset_index(name="count")
    )
    pivot = (
        hdf.pivot(index="_dow", columns="_hour", values="count")
           .reindex(day_order)
           .fillna(0)
    )
    pivot.index = day_th
    fig = px.imshow(
        pivot,
        labels=dict(x="ชั่วโมง", y="วัน", color="จำนวน"),
        title="Heatmap คำขอตามวันและเวลา",
        color_continuous_scale="YlOrRd",
        aspect="auto"
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ ไม่พบข้อมูลเวลาสำหรับ Heatmap")

st.markdown("---")

# ============================================================
# OVERDUE TABLE
# ============================================================
st.subheader("🚨 รายการเกินกำหนดคืน")

if DATE_END_COL and RETURN_COL:
    od = dff[
        (dff[DATE_END_COL] < NOW) &
        (dff[RETURN_COL]  != "คืนเรียบร้อย")
    ].copy()
    if not od.empty:
        od["เกินกำหนด(วัน)"] = (NOW - od[DATE_END_COL]).dt.days
        show = [c for c in [
            NAME_COL, USERTYPE_COL, DEPT_COL,
            DATE_END_COL, RETURN_COL,
            "เกินกำหนด(วัน)", PHONE_COL
        ] if c and c in od.columns]
        st.error(f"⚠️ พบ {len(od)} รายการเกินกำหนด")
        st.dataframe(
            od[show].sort_values("เกินกำหนด(วัน)", ascending=False),
            use_container_width=True, hide_index=True
        )
    else:
        st.success("✅ ไม่มีรายการเกินกำหนดคืน")
else:
    st.info("ℹ️ ไม่พบคอลัมน์วันที่สิ้นสุดการยืม")

st.markdown("---")

# ============================================================
# DATA TABLE
# ============================================================
st.subheader("📋 รายละเอียดทั้งหมด")

search = st.text_input(
    "🔍 ค้นหา", placeholder="ชื่อ, คณะ, สถานะ..."
)

show_cols = [c for c in [
    "Timestamp", NAME_COL, USERTYPE_COL, DEPT_COL,
    PURPOSE_COL, PHONE_COL, EMAIL_COL,
    STATUS_COL, RETURN_COL
] if c and c in dff.columns]

disp = dff[show_cols].copy()

if "Timestamp" in disp.columns:
    disp = disp.sort_values("Timestamp", ascending=True)
    disp["Timestamp"] = disp["Timestamp"].dt.strftime("%d/%m/%Y %H:%M")

if search.strip():
    mask = disp.apply(
        lambda r: r.astype(str)
                   .str.contains(search, case=False)
                   .any(),
        axis=1
    )
    disp = disp[mask]
    st.caption(f"พบ {len(disp)} รายการ")

st.dataframe(disp, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ ดาวน์โหลด CSV",
    data=disp.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"report_{NOW.strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#999;font-size:.8rem;'>"
    f"🧪 Science Equipment Dashboard — AI Enhanced | "
    f"{NOW.strftime('%d/%m/%Y %H:%M')} | 🔒 PDPA Protected"
    f"</div>",
    unsafe_allow_html=True
)
