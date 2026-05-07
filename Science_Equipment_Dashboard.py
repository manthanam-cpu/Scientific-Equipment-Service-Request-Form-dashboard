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
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SHEET URL
# ============================================================
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/"
    "export?format=csv&gid=1562070767"
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def find_col(columns: list, keywords: list):
    """คืน str ชื่อคอลัมน์แรกที่มี keyword — คืน None ถ้าไม่พบ"""
    for col in columns:
        for kw in keywords:
            if kw in col:
                return col
    return None


def parse_date_range(raw):
    """
    แปลง output จาก st.date_input → (pd.Timestamp, pd.Timestamp)
    ✅ แก้: ใช้ raw, raw แทน raw ทั้งก้อน
    """
    try:
        if isinstance(raw, (list, tuple)):
            if len(raw) >= 2:
                s = pd.Timestamp(raw)   # ✅ raw
                e = pd.Timestamp(raw) + pd.Timedelta(days=1)  # ✅ raw
                return s, e
            elif len(raw) == 1:
                s = pd.Timestamp(raw)   # ✅ raw
                e = s + pd.Timedelta(days=1)
                return s, e
            else:
                return None, None
        else:
            # single date object
            s = pd.Timestamp(raw)
            e = s + pd.Timedelta(days=1)
            return s, e
    except Exception:
        return None, None


def count_status(series: pd.Series, keywords: list,
                 exclude: list = None) -> int:
    """นับแถวที่มี keyword และไม่มี exclude keyword"""
    if series is None or len(series) == 0:
        return 0
    mask = series.str.contains(
        "|".join(keywords), na=False, case=False
    )
    if exclude:
        ex_mask = series.str.contains(
            "|".join(exclude), na=False, case=False
        )
        mask = mask & ~ex_mask
    return int(mask.sum())


# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        return pd.DataFrame(), str(e)

    # แปลง Timestamp
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"], errors="coerce"
        )

    # PDPA: Mask ชื่อ-สกุล
    name_col_local = find_col(list(df.columns), ["ชื่อ-สกุล", "ชื่อ"])
    if name_col_local:
        def mask_name(v):
            v = str(v).strip()
            if not v or v.lower() == "nan":
                return "-"
            p = v.split()
            if len(p) >= 2:
                # ✅ แก้: p และ p ไม่ใช่ p ทั้ง list
                return f"{p} {p}***"
            return f"{v}***" if v else "-"
        df[name_col_local] = df[name_col_local].apply(mask_name)

    # PDPA: Mask เบอร์โทร
    phone_col_local = find_col(list(df.columns), ["เบอร์", "โทร"])
    if phone_col_local:
        def mask_phone(v):
            v = str(v).strip()
            if not v or v.lower() == "nan":
                return "-"
            if v.endswith(".0"):
                v = v[:-2]
            return f"{v[:3]}-XXX-{v[-4:]}" if len(v) >= 9 else "-"
        df[phone_col_local] = df[phone_col_local].apply(mask_phone)

    # PDPA: Mask Email — วนทีละคอลัมน์
    def mask_email(v):
        v = str(v).strip()
        if not v or v.lower() == "nan":
            return "-"
        if "@" in v:
            a, b = v.split("@", 1)
            # ✅ แก้: a ตัวแรกเท่านั้น ไม่ใช่ a ทั้งหมด
            first = a if a else "*"
            return f"{first}***@{b}"
        return "-"

    for c in list(df.columns):
        c_low = c.lower()
        if "email" in c_low or "e-mail" in c_low or "อีเมล" in c:
            df[c] = df[c].apply(mask_email)

    # คอลัมน์ช่วยคำนวณ
    if "Timestamp" in df.columns:
        df["_month_dt"] = (
            df["Timestamp"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        df["_dow"]  = df["Timestamp"].dt.day_name()
        df["_hour"] = df["Timestamp"].dt.hour

    return df, ""


# ============================================================
# LOAD & VALIDATE
# ============================================================
df, load_err = load_data()

if df.empty:
    st.error(f"❌ โหลดข้อมูลไม่ได้: {load_err}")
    st.stop()

all_cols = list(df.columns)

# ============================================================
# ตรวจหาคอลัมน์ — str | None เสมอ
# ============================================================
STATUS_COL    = find_col(all_cols, ["สถานะ"])
RETURN_COL    = find_col(all_cols, ["การคืน"])
USERTYPE_COL  = find_col(all_cols, ["ประเภทผู้ใช้", "ประเภท"])
DEPT_COL      = find_col(all_cols, ["คณะ", "หน่วยงาน"])
TOOL_COL      = find_col(all_cols, ["เครื่องมือ", "อุปกรณ์"])
LOCATION_COL  = find_col(all_cols, ["โรงเรือน", "สถานที่", "ห้อง"])
PURPOSE_COL   = find_col(all_cols, ["วัตถุประสงค์", "จุดประสงค์", "เรื่อง"])
NAME_COL      = find_col(all_cols, ["ชื่อ-สกุล", "ชื่อ"])
PHONE_COL     = find_col(all_cols, ["เบอร์", "โทร"])
EMAIL_COL     = find_col(all_cols, ["Email Address", "E-mail",
                                     "email", "อีเมล"])

# ✅ หาคอลัมน์วันที่ด้วย keyword ที่ครอบคลุมกว่าเดิม
DATE_START_COL = None
DATE_END_COL   = None

for c in all_cols:
    c_str = str(c)
    # วันเริ่ม
    if any(k in c_str for k in [
        "วันที่เริ่ม", "วันเริ่ม", "เริ่มต้น",
        "เริ่มใช้", "วันต้น", "start", "เริ่ม"
    ]):
        if DATE_START_COL is None:
            DATE_START_COL = c
    # วันสิ้นสุด/คืน
    if any(k in c_str for k in [
        "วันที่สิ้น", "วันสิ้น", "สิ้นสุด",
        "วันคืน", "กำหนดคืน", "สิ้นสุดใช้",
        "วันที่คืน", "end", "สุดท้าย",
        "วันที่สุด", "ครบกำหนด"
    ]):
        if DATE_END_COL is None:
            DATE_END_COL = c

# แปลงคอลัมน์วันที่
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

# ============================================================
# DEBUG EXPANDER
# ============================================================
with st.expander("🔍 Debug: คอลัมน์และค่าที่ตรวจพบ (คลิกเพื่อดู)"):
    st.json({
        "STATUS_COL":     STATUS_COL,
        "RETURN_COL":     RETURN_COL,
        "USERTYPE_COL":   USERTYPE_COL,
        "DEPT_COL":       DEPT_COL,
        "TOOL_COL":       TOOL_COL,
        "LOCATION_COL":   LOCATION_COL,
        "PURPOSE_COL":    PURPOSE_COL,
        "NAME_COL":       NAME_COL,
        "PHONE_COL":      PHONE_COL,
        "EMAIL_COL":      EMAIL_COL,
        "DATE_START_COL": DATE_START_COL,
        "DATE_END_COL":   DATE_END_COL,
        "ALL_COLUMNS":    all_cols,
    })

    d1, d2 = st.columns(2)
    with d1:
        if STATUS_COL:
            st.markdown(f"**ค่าจริงใน `{STATUS_COL}`:**")
            sc = df[STATUS_COL].value_counts().reset_index()
            sc.columns = ["ค่า", "จำนวน"]
            st.dataframe(sc, use_container_width=True, hide_index=True)
    with d2:
        if RETURN_COL:
            st.markdown(f"**ค่าจริงใน `{RETURN_COL}`:**")
            rc = df[RETURN_COL].value_counts().reset_index()
            rc.columns = ["ค่า", "จำนวน"]
            st.dataframe(rc, use_container_width=True, hide_index=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🔽 ตัวกรองข้อมูล")
    st.markdown("เลือกเงื่อนไขเพื่อกรองข้อมูล")

    sel_type = "ทั้งหมด"
    if USERTYPE_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[USERTYPE_COL].dropna().unique().tolist()
        )
        sel_type = st.selectbox("👤 ประเภทผู้ใช้", opts)

    sel_dept = "ทั้งหมด"
    if DEPT_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[DEPT_COL].dropna().unique().tolist()
        )
        sel_dept = st.selectbox("🏫 คณะ/หน่วยงาน", opts)

    sel_status = "ทั้งหมด"
    if STATUS_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[STATUS_COL].dropna().unique().tolist()
        )
        sel_status = st.selectbox("📋 สถานะอนุมัติ", opts)

    sel_return = "ทั้งหมด"
    if RETURN_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[RETURN_COL].dropna().unique().tolist()
        )
        sel_return = st.selectbox("📦 สถานะคืน", opts)

    st.markdown("---")
    st.markdown("📅 **ช่วงเวลา**")

    date_start_filter = None
    date_end_filter   = None

    if "Timestamp" in df.columns:
        valid_ts = df["Timestamp"].dropna()
        if not valid_ts.empty:
            mn = valid_ts.min().date()
            mx = valid_ts.max().date()
            raw = st.date_input(
                "เลือกช่วงวันที่",
                value=(mn, mx),
                min_value=mn,
                max_value=mx,
                key="date_range_input"
            )
            # ✅ parse_date_range จัดการ raw, raw อย่างถูกต้อง
            date_start_filter, date_end_filter = parse_date_range(raw)

    st.markdown("---")
    if st.button("🔄 รีเฟรชข้อมูล"):
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
<div style='
    background:linear-gradient(135deg,#667eea,#764ba2);
    padding:30px; border-radius:20px; margin-bottom:20px;
    color:white; text-align:center;'>
  <h1 style='margin:0; font-size:2rem;'>
    🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์
  </h1>
  <p style='margin:8px 0 0 0; opacity:.85;'>
    Science Equipment Dashboard — AI Enhanced
  </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI SCORECARD
# ============================================================
st.subheader("📊 KPI Scorecard")

this_m = 0
if "Timestamp" in dff.columns:
    this_m = int(
        (dff["Timestamp"].dt.to_period("M") == THIS_MONTH).sum()
    )

# ✅ รออนุมัติ
pending  = 0
approved = 0
if STATUS_COL:
    approved = count_status(
        dff[STATUS_COL],
        keywords=["อนุมัติ"],
        exclude=["ไม่อนุมัติ", "รออนุมัติ", "ยังไม่"]
    )
    pending = total - approved

# ✅ คืนแล้ว
returned = 0
if RETURN_COL:
    returned = count_status(
        dff[RETURN_COL],
        keywords=["คืน"],
        exclude=["ยังไม่", "ไม่ได้คืน"]
    )

# ✅ เกินกำหนด
overdue = 0
if DATE_END_COL and RETURN_COL:
    not_returned_mask = (
        ~dff[RETURN_COL].str.contains("คืน", na=False, case=False)
        | dff[RETURN_COL].str.contains(
            "ยังไม่|ไม่ได้", na=False, case=False
        )
    )
    overdue = int(
        ((dff[DATE_END_COL] < NOW) & not_returned_mask).sum()
    )

u_types = dff[USERTYPE_COL].nunique() if USERTYPE_COL else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi_data = [
    (k1, total,    "📝 คำขอทั้งหมด",  "#667eea", "#764ba2"),
    (k2, this_m,   "📅 เดือนนี้",     "#f093fb", "#f5576c"),
    (k3, pending,  "⏳ รออนุมัติ",    "#f6d365", "#fda085"),
    (k4, returned, "✅ คืนแล้ว",      "#43e97b", "#38f9d7"),
    (k5, overdue,  "🚨 เกินกำหนด",    "#f5576c", "#f093fb"),
    (k6, u_types,  "👥 ประเภทผู้ใช้", "#4facfe", "#00f2fe"),
]
for col_obj, val, label, g1, g2 in kpi_data:
    with col_obj:
        st.markdown(
            f"<div class='metric-card' style='"
            f"background:linear-gradient(135deg,{g1},{g2});'>"
            f"<h2>{val}</h2><p>{label}</p></div>",
            unsafe_allow_html=True
        )

# ตารางสรุปสถานะ
with st.expander("📊 ดูรายละเอียดสถานะทั้งหมด"):
    e1, e2 = st.columns(2)
    with e1:
        if STATUS_COL:
            st.markdown(f"**สถานะอนุมัติ** (`{STATUS_COL}`):")
            sc = dff[STATUS_COL].value_counts().reset_index()
            sc.columns = ["สถานะ", "จำนวน"]
            st.dataframe(sc, use_container_width=True, hide_index=True)
    with e2:
        if RETURN_COL:
            st.markdown(f"**สถานะการคืน** (`{RETURN_COL}`):")
            rc = dff[RETURN_COL].value_counts().reset_index()
            rc.columns = ["สถานะ", "จำนวน"]
            st.dataframe(rc, use_container_width=True, hide_index=True)

st.markdown("---")

# ============================================================
# AI INSIGHT
# ============================================================
st.subheader("🤖 AI Insight — วิเคราะห์อัตโนมัติ")

def ai_insight(dff, total, overdue):
    ins, wrn = [], []
    if total == 0:
        return ["ไม่มีข้อมูลในช่วงที่เลือก"], []

    # แนวโน้มรายเดือน
    if "_month_dt" in dff.columns:
        m = (
            dff.groupby("_month_dt").size()
               .reset_index(name="n")
               .sort_values("_month_dt")
        )
        if len(m) >= 2:
            last = int(m.iloc[-1]["n"])
            prev = int(m.iloc[-2]["n"])
            mn   = m.iloc[-1]["_month_dt"].strftime("%b %Y")
            pct  = (last - prev) / prev * 100 if prev else 0
            icon = "📈" if pct >= 0 else "📉"
            word = "เพิ่มขึ้น" if pct >= 0 else "ลดลง"
            ins.append(
                f"{icon} เดือน {mn}: **{last} รายการ** "
                f"({word} {abs(pct):.1f}%)"
            )

    # กลุ่มผู้ใช้มากสุด
    if USERTYPE_COL and USERTYPE_COL in dff.columns:
        vc = dff[USERTYPE_COL].value_counts()
        if not vc.empty:
            ins.append(
                f"👤 กลุ่มมากสุด: **{vc.idxmax()}** "
                f"({vc.max()} รายการ, {vc.max()/total*100:.1f}%)"
            )

    # คณะมากสุด
    if DEPT_COL and DEPT_COL in dff.columns:
        vc = dff[DEPT_COL].value_counts()
        if not vc.empty:
            ins.append(
                f"🏫 คณะมากสุด: **{vc.idxmax()}** "
                f"({vc.max()} รายการ)"
            )

    # ชั่วโมงยอดนิยม
    if "_hour" in dff.columns:
        vc = dff["_hour"].value_counts()
        if not vc.empty:
            h = int(vc.idxmax())
            ins.append(f"⏰ ช่วงยอดนิยม: **{h}:00–{h+1}:00 น.**")

    # วันยอดนิยม
    if "_dow" in dff.columns:
        dm = {
            "Monday":    "จันทร์",
            "Tuesday":   "อังคาร",
            "Wednesday": "พุธ",
            "Thursday":  "พฤหัสบดี",
            "Friday":    "ศุกร์",
            "Saturday":  "เสาร์",
            "Sunday":    "อาทิตย์",
        }
        vc = dff["_dow"].value_counts()
        if not vc.empty:
            ins.append(
                f"📅 วันมากสุด: "
                f"**วัน{dm.get(vc.idxmax(), vc.idxmax())}**"
            )

    # อัตราการคืน
    if RETURN_COL and RETURN_COL in dff.columns:
        r = count_status(
            dff[RETURN_COL],
            keywords=["คืน"],
            exclude=["ยังไม่", "ไม่ได้"]
        )
        rate = r / total * 100
        if rate < 50:
            wrn.append(
                f"⚠️ อัตราคืน **{rate:.1f}%** — "
                f"ค้างอยู่ {total - r} รายการ"
            )
        else:
            ins.append(
                f"✅ อัตราการคืน **{rate:.1f}%** — อยู่ในเกณฑ์ดี"
            )

    # รออนุมัติ
    if STATUS_COL:
        p = total - count_status(
            dff[STATUS_COL],
            keywords=["อนุมัติ"],
            exclude=["ไม่อนุมัติ", "รออนุมัติ", "ยังไม่"]
        )
        if p > 0:
            wrn.append(
                f"📋 มีคำขอรออนุมัติ **{p} รายการ** — กรุณาดำเนินการ"
            )

    # เกินกำหนด
    if overdue > 0:
        wrn.append(
            f"🚨 เกินกำหนดคืน **{overdue} รายการ** — ติดตามด่วน!"
        )

    return ins, wrn


ins_list, wrn_list = ai_insight(dff, total, overdue)
col_a, col_b = st.columns([3, 2])

with col_a:
    st.markdown(
        "<div class='ai-box'>"
        "<b>🤖 AI Analysis — ผลวิเคราะห์</b></div>",
        unsafe_allow_html=True
    )
    for i in ins_list:
        st.success(i)

with col_b:
    st.markdown(
        "<div class='alert-box'>"
        "<b>🚨 AI Alert — รายการแจ้งเตือน</b></div>",
        unsafe_allow_html=True
    )
    if wrn_list:
        for w in wrn_list:
            st.error(w)
    else:
        st.info("✅ ไม่มีรายการแจ้งเตือน")

st.markdown("---")

# ============================================================
# MONTHLY TREND ✅ เรียงลำดับถูกต้อง
# ============================================================
st.subheader("📈 แนวโน้มการขอใช้บริการรายเดือน")

if "_month_dt" in dff.columns and dff["_month_dt"].notna().any():

    if USERTYPE_COL and USERTYPE_COL in dff.columns:
        mdf = (
            dff.groupby(["_month_dt", USERTYPE_COL])
               .size()
               .reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        month_order  = (
            mdf[["_month_dt", "เดือน"]]
            .drop_duplicates()
            .sort_values("_month_dt")["เดือน"]
            .tolist()
        )
        fig_trend = px.line(
            mdf, x="เดือน", y="จำนวน",
            color=USERTYPE_COL, markers=True,
            title="แนวโน้มรายเดือน แยกตามประเภทผู้ใช้",
            color_discrete_sequence=px.colors.qualitative.Safe,
            category_orders={"เดือน": month_order}
        )
    else:
        mdf = (
            dff.groupby("_month_dt").size()
               .reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        month_order  = mdf["เดือน"].tolist()
        fig_trend = px.line(
            mdf, x="เดือน", y="จำนวน", markers=True,
            title="แนวโน้มรายเดือน",
            color_discrete_sequence=["#667eea"],
            category_orders={"เดือน": month_order}
        )
        fig_trend.update_traces(
            fill="tozeroy",
            fillcolor="rgba(102,126,234,0.15)"
        )

    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("ℹ️ ไม่พบข้อมูลเวลาสำหรับกราฟรายเดือน")

st.markdown("---")

# ============================================================
# TOP 5
# ============================================================
st.subheader("🏆 Top 5 ที่ถูกขอใช้บ่อยที่สุด")

def make_bar(df_in, col, title, scale):
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
    col_use = TOOL_COL or USERTYPE_COL
    ttl     = "🔬 Top 5 เครื่องมือ" if TOOL_COL else "Top 5 ประเภทผู้ใช้"
    fig     = make_bar(dff, col_use, ttl, "Viridis")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบข้อมูลเครื่องมือ")

with t2:
    col_use = LOCATION_COL or DEPT_COL
    ttl     = "🏠 Top 5 สถานที่" if LOCATION_COL else "Top 5 คณะ/หน่วยงาน"
    fig     = make_bar(dff, col_use, ttl, "Oranges")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบข้อมูลสถานที่")

st.markdown("---")

# ============================================================
# PIE CHARTS
# ============================================================
st.subheader("🎯 สัดส่วนข้อมูลสำคัญ")

def make_pie(df_in, col, title, colors):
    if not col or col not in df_in.columns:
        return None
    fig = px.pie(
        df_in, names=col, title=title, hole=0.4,
        color_discrete_sequence=colors
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


p1, p2 = st.columns(2)
with p1:
    fig = make_pie(dff, USERTYPE_COL, "ประเภทผู้ใช้",
                   px.colors.qualitative.Safe)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with p2:
    fig = make_pie(dff, DEPT_COL, "คณะ/หน่วยงาน",
                   px.colors.qualitative.Pastel)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

p3, p4 = st.columns(2)
with p3:
    fig = make_pie(dff, STATUS_COL, "สถานะการอนุมัติ",
                   ["#FFCC00", "#2ecc71", "#e74c3c", "#95a5a6"])
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with p4:
    fig = make_pie(dff, RETURN_COL, "สถานะการคืนอุปกรณ์",
                   ["#3498db", "#95a5a6", "#e67e22"])
    if fig:
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# HEATMAP
# ============================================================
st.subheader("🗓️ Heatmap — วันและเวลายอดนิยม")

if "_dow" in dff.columns and "_hour" in dff.columns:
    day_order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]
    day_th = [
        "จันทร์", "อังคาร", "พุธ",
        "พฤหัส", "ศุกร์", "เสาร์", "อาทิตย์"
    ]
    hdf = (
        dff.groupby(["_dow", "_hour"])
           .size()
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
        title="จำนวนคำขอตามวันและช่วงเวลา",
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
st.subheader("🚨 รายการที่เกินกำหนดคืน")

if DATE_END_COL and RETURN_COL:
    not_ret = (
        ~dff[RETURN_COL].str.contains("คืน", na=False, case=False)
        | dff[RETURN_COL].str.contains(
            "ยังไม่|ไม่ได้", na=False, case=False
        )
    )
    od = dff[(dff[DATE_END_COL] < NOW) & not_ret].copy()

    if not od.empty:
        od["เกินกำหนด (วัน)"] = (NOW - od[DATE_END_COL]).dt.days
        show_od = [c for c in [
            NAME_COL, USERTYPE_COL, DEPT_COL,
            DATE_END_COL, RETURN_COL,
            "เกินกำหนด (วัน)", PHONE_COL
        ] if c and c in od.columns]
        st.error(f"⚠️ พบ {len(od)} รายการที่เกินกำหนดคืน")
        st.dataframe(
            od[show_od].sort_values(
                "เกินกำหนด (วัน)", ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ ไม่มีรายการที่เกินกำหนดคืน")
else:
    # ✅ แสดงข้อความแนะนำการแก้ไขแทน info ธรรมดา
    st.warning(
        "⚠️ ไม่พบคอลัมน์วันที่สิ้นสุดการยืม\n\n"
        "**วิธีแก้ไข:** เปิด Debug expander ด้านบน "
        "แล้วดูชื่อคอลัมน์จริงใน ALL_COLUMNS "
        "จากนั้นแจ้งชื่อคอลัมน์วันที่เพื่อเพิ่ม keyword ให้ตรง"
    )

st.markdown("---")

# ============================================================
# DATA TABLE + SEARCH + EXPORT
# ============================================================
st.subheader("📋 รายละเอียดผู้ขอใช้บริการทั้งหมด")

search = st.text_input(
    "🔍 ค้นหาข้อมูล",
    placeholder="พิมพ์ชื่อ, คณะ, สถานะ หรือคำใดๆ..."
)

show_cols = [c for c in [
    "Timestamp", NAME_COL, USERTYPE_COL, DEPT_COL,
    PURPOSE_COL, PHONE_COL, EMAIL_COL,
    STATUS_COL, RETURN_COL,
] if c and c in dff.columns]

disp = dff[show_cols].copy()

if "Timestamp" in disp.columns:
    disp = disp.sort_values("Timestamp", ascending=True)
    disp["Timestamp"] = disp["Timestamp"].dt.strftime("%d/%m/%Y %H:%M")

if search.strip():
    mask = disp.apply(
        lambda row: row.astype(str)
                       .str.contains(search.strip(), case=False)
                       .any(),
        axis=1
    )
    disp = disp[mask]
    st.caption(f"🔍 พบ {len(disp)} รายการที่ตรงกับ '{search}'")

st.dataframe(disp, use_container_width=True, hide_index=True)

st.download_button(
    label="⬇️ ดาวน์โหลดข้อมูล (CSV)",
    data=disp.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"report_{NOW.strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)

st.markdown("---")

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    f"<div style='text-align:center;color:#999;"
    f"font-size:.8rem;padding:10px;'>"
    f"🧪 Science Equipment Dashboard — AI Enhanced<br>"
    f"อัปเดตอัตโนมัติทุก 60 วินาที | "
    f"ข้อมูล ณ {NOW.strftime('%d/%m/%Y %H:%M')} น. | "
    f"🔒 PDPA Protected"
    f"</div>",
    unsafe_allow_html=True
)
