import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/"
    "export?format=csv&gid=1562070767"
)

# ============================================================
# HELPERS
# ============================================================
def find_col(columns, keywords):
    for col in columns:
        for kw in keywords:
            if kw in col:
                return col
    return None


def parse_date_range(raw):
    try:
        if isinstance(raw, (list, tuple)):
            if len(raw) >= 2:
                return (
                    pd.Timestamp(raw),
                    pd.Timestamp(raw) + pd.Timedelta(days=1)
                )
            elif len(raw) == 1:
                s = pd.Timestamp(raw)
                return s, s + pd.Timedelta(days=1)
            return None, None
        else:
            s = pd.Timestamp(raw)
            return s, s + pd.Timedelta(days=1)
    except Exception:
        return None, None


def count_status(series, keywords, exclude=None):
    if series is None or len(series) == 0:
        return 0
    mask = series.str.contains(
        "|".join(keywords), na=False, case=False
    )
    if exclude:
        mask = mask & ~series.str.contains(
            "|".join(exclude), na=False, case=False
        )
    return int(mask.sum())


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


def make_pie(df_in, col, title, colors):
    if not col or col not in df_in.columns:
        return None
    fig = px.pie(
        df_in, names=col, title=title, hole=0.4,
        color_discrete_sequence=colors
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        return pd.DataFrame(), str(e)

    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"], errors="coerce"
        )

    # ✅ Mask ชื่อ — try/except ครอบทุกกรณี
    nc = find_col(list(df.columns), ["ชื่อ-สกุล", "ชื่อ"])
    if nc:
        def mask_name(v):
            try:
                v = str(v).strip()
                if not v or v.lower() == "nan":
                    return "-"
                p = v.split()
                if len(p) >= 2 and len(p) > 0:
                    return p + " " + p + "***"
                elif len(p) >= 1 and len(p) > 0:
                    return p + "***"
                return "-"
            except Exception:
                return "-"
        df[nc] = df[nc].apply(mask_name)

    # ✅ Mask เบอร์
    pc = find_col(list(df.columns), ["เบอร์", "โทร"])
    if pc:
        def mask_phone(v):
            try:
                v = str(v).strip()
                if not v or v.lower() == "nan":
                    return "-"
                if v.endswith(".0"):
                    v = v[:-2]
                if len(v) >= 9:
                    return v[:3] + "-XXX-" + v[-4:]
                return "-"
            except Exception:
                return "-"
        df[pc] = df[pc].apply(mask_phone)

    # ✅ Mask Email
    def mask_email(v):
        try:
            v = str(v).strip()
            if not v or v.lower() == "nan":
                return "-"
            if "@" in v:
                a, b = v.split("@", 1)
                if a:
                    return a + "***@" + b
                return "***@" + b
            return "-"
        except Exception:
            return "-"

    for c in list(df.columns):
        cl = c.lower()
        if "email" in cl or "e-mail" in cl or "อีเมล" in c:
            df[c] = df[c].apply(mask_email)

    if "Timestamp" in df.columns:
        df["_month_dt"] = (
            df["Timestamp"].dt.to_period("M").dt.to_timestamp()
        )
        df["_dow"]  = df["Timestamp"].dt.day_name()
        df["_hour"] = df["Timestamp"].dt.hour

    return df, ""


# ============================================================
# LOAD & VALIDATE
# ============================================================
df, load_err = load_data()

if df.empty:
    st.error("โหลดข้อมูลไม่ได้: " + load_err)
    st.stop()

all_cols = list(df.columns)

STATUS_COL   = find_col(all_cols, ["สถานะ"])
RETURN_COL   = find_col(all_cols, ["การคืน"])
USERTYPE_COL = find_col(all_cols, ["ประเภทผู้ใช้", "ประเภท"])
DEPT_COL     = find_col(all_cols, ["คณะ", "หน่วยงาน"])
TOOL_COL     = find_col(all_cols, ["เครื่องมือ", "อุปกรณ์"])
LOCATION_COL = find_col(all_cols, ["โรงเรือน", "สถานที่", "ห้อง"])
PURPOSE_COL  = find_col(all_cols, ["วัตถุประสงค์", "จุดประสงค์", "เรื่อง"])
NAME_COL     = find_col(all_cols, ["ชื่อ-สกุล", "ชื่อ"])
PHONE_COL    = find_col(all_cols, ["เบอร์", "โทร"])
EMAIL_COL    = find_col(all_cols, ["Email Address", "E-mail",
                                    "email", "อีเมล"])
DATE_START_COL = None
DATE_END_COL   = None

for c in all_cols:
    if any(k in c for k in [
        "วันที่เริ่ม","วันเริ่ม","เริ่มต้น","เริ่มใช้"
    ]):
        if DATE_START_COL is None:
            DATE_START_COL = c
    if any(k in c for k in [
        "วันที่สิ้น","วันสิ้น","สิ้นสุด",
        "วันคืน","กำหนดคืน","ครบกำหนด"
    ]):
        if DATE_END_COL is None:
            DATE_END_COL = c

if DATE_START_COL:
    df[DATE_START_COL] = pd.to_datetime(
        df[DATE_START_COL], errors="coerce"
    )
if DATE_END_COL:
    df[DATE_END_COL] = pd.to_datetime(
        df[DATE_END_COL], errors="coerce"
    )

for c in [USERTYPE_COL, DEPT_COL, TOOL_COL, LOCATION_COL]:
    if c:
        df[c] = df[c].fillna("ไม่ระบุ")
if STATUS_COL:
    df[STATUS_COL] = df[STATUS_COL].fillna("ยังไม่ระบุสถานะ")
if RETURN_COL:
    df[RETURN_COL] = df[RETURN_COL].fillna("ยังไม่ระบุข้อมูล")

# ============================================================
# DEBUG
# ============================================================
with st.expander("Debug: คอลัมน์ที่ตรวจพบ (คลิกเพื่อดู)"):
    st.json({
        "STATUS_COL": STATUS_COL,
        "RETURN_COL": RETURN_COL,
        "USERTYPE_COL": USERTYPE_COL,
        "DEPT_COL": DEPT_COL,
        "TOOL_COL": TOOL_COL,
        "LOCATION_COL": LOCATION_COL,
        "PURPOSE_COL": PURPOSE_COL,
        "NAME_COL": NAME_COL,
        "PHONE_COL": PHONE_COL,
        "EMAIL_COL": EMAIL_COL,
        "DATE_START_COL": DATE_START_COL,
        "DATE_END_COL": DATE_END_COL,
        "ALL_COLUMNS": all_cols,
    })
    d1, d2 = st.columns(2)
    with d1:
        if STATUS_COL:
            sc = df[STATUS_COL].value_counts().reset_index()
            sc.columns = ["ค่า", "จำนวน"]
            st.dataframe(sc, use_container_width=True, hide_index=True)
    with d2:
        if RETURN_COL:
            rc = df[RETURN_COL].value_counts().reset_index()
            rc.columns = ["ค่า", "จำนวน"]
            st.dataframe(rc, use_container_width=True, hide_index=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("ตัวกรองข้อมูล")

    sel_type = "ทั้งหมด"
    if USERTYPE_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[USERTYPE_COL].dropna().unique().tolist()
        )
        sel_type = st.selectbox("ประเภทผู้ใช้", opts)

    sel_dept = "ทั้งหมด"
    if DEPT_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[DEPT_COL].dropna().unique().tolist()
        )
        sel_dept = st.selectbox("คณะ/หน่วยงาน", opts)

    sel_status = "ทั้งหมด"
    if STATUS_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[STATUS_COL].dropna().unique().tolist()
        )
        sel_status = st.selectbox("สถานะอนุมัติ", opts)

    sel_return = "ทั้งหมด"
    if RETURN_COL:
        opts = ["ทั้งหมด"] + sorted(
            df[RETURN_COL].dropna().unique().tolist()
        )
        sel_return = st.selectbox("สถานะคืน", opts)

    st.markdown("---")
    date_start_filter = None
    date_end_filter   = None

    if "Timestamp" in df.columns:
        vts = df["Timestamp"].dropna()
        if not vts.empty:
            mn = vts.min().date()
            mx = vts.max().date()
            raw = st.date_input(
                "เลือกช่วงวันที่",
                value=(mn, mx),
                min_value=mn,
                max_value=mx,
                key="dr"
            )
            date_start_filter, date_end_filter = parse_date_range(raw)

    st.markdown("---")
    if st.button("รีเฟรชข้อมูล"):
        st.cache_data.clear()
        st.rerun()
    st.caption(
        "อัปเดต: " + pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    )

# ============================================================
# FILTER
# ============================================================
dff = df.copy()
if sel_type != "ทั้งหมด" and USERTYPE_COL:
    dff = dff[dff[USERTYPE_COL] == sel_type]
if sel_dept != "ทั้งหมด" and DEPT_COL:
    dff = dff[dff[DEPT_COL] == sel_dept]
if sel_status != "ทั้งหมด" and STATUS_COL:
    dff = dff[dff[STATUS_COL] == sel_status]
if sel_return != "ทั้งหมด" and RETURN_COL:
    dff = dff[dff[RETURN_COL] == sel_return]
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
st.markdown(
    "<div style='background:linear-gradient(135deg,#667eea,#764ba2);"
    "padding:30px;border-radius:20px;margin-bottom:20px;"
    "color:white;text-align:center;'>"
    "<h1 style='margin:0;font-size:2rem;'>"
    "🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์"
    "</h1>"
    "<p style='margin:8px 0 0 0;opacity:.85;'>"
    "Science Equipment Dashboard - AI Enhanced"
    "</p></div>",
    unsafe_allow_html=True
)

# ============================================================
# KPI
# ============================================================
st.subheader("📊 KPI Scorecard")

this_m = 0
if "Timestamp" in dff.columns:
    this_m = int(
        (dff["Timestamp"].dt.to_period("M") == THIS_MONTH).sum()
    )

approved = 0
pending  = 0
if STATUS_COL:
    approved = count_status(
        dff[STATUS_COL], ["อนุมัติ"],
        exclude=["ไม่อนุมัติ","รออนุมัติ","ยังไม่"]
    )
    pending = total - approved

returned = 0
if RETURN_COL:
    returned = count_status(
        dff[RETURN_COL], ["คืน"],
        exclude=["ยังไม่","ไม่ได้คืน"]
    )

overdue = 0
if DATE_END_COL and RETURN_COL:
    not_ret = (
        ~dff[RETURN_COL].str.contains("คืน", na=False, case=False)
        | dff[RETURN_COL].str.contains(
            "ยังไม่|ไม่ได้", na=False, case=False
        )
    )
    overdue = int(((dff[DATE_END_COL] < NOW) & not_ret).sum())

u_types = dff[USERTYPE_COL].nunique() if USERTYPE_COL else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
for col_obj, val, label, g1, g2 in [
    (k1, total,    "📝 คำขอทั้งหมด",  "#667eea", "#764ba2"),
    (k2, this_m,   "📅 เดือนนี้",     "#f093fb", "#f5576c"),
    (k3, pending,  "⏳ รออนุมัติ",    "#f6d365", "#fda085"),
    (k4, returned, "✅ คืนแล้ว",      "#43e97b", "#38f9d7"),
    (k5, overdue,  "🚨 เกินกำหนด",    "#f5576c", "#f093fb"),
    (k6, u_types,  "👥 ประเภทผู้ใช้", "#4facfe", "#00f2fe"),
]:
    with col_obj:
        st.markdown(
            "<div class='metric-card' style='"
            "background:linear-gradient(135deg,"
            + g1 + "," + g2 + ");'>"
            "<h2>" + str(val) + "</h2>"
            "<p>" + label + "</p></div>",
            unsafe_allow_html=True
        )

with st.expander("📊 รายละเอียดสถานะ"):
    e1, e2 = st.columns(2)
    with e1:
        if STATUS_COL:
            sc = dff[STATUS_COL].value_counts().reset_index()
            sc.columns = ["สถานะ", "จำนวน"]
            st.dataframe(sc, use_container_width=True, hide_index=True)
    with e2:
        if RETURN_COL:
            rc = dff[RETURN_COL].value_counts().reset_index()
            rc.columns = ["สถานะ", "จำนวน"]
            st.dataframe(rc, use_container_width=True, hide_index=True)

st.markdown("---")

# ============================================================
# AI INSIGHT
# ============================================================
st.subheader("🤖 AI Insight")

def ai_insight(dff, total, overdue):
    ins = []
    wrn = []
    if total == 0:
        return ["ไม่มีข้อมูลในช่วงที่เลือก"], []

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
            word = "เพิ่มขึ้น" if pct >= 0 else "ลดลง"
            icon = "📈" if pct >= 0 else "📉"
            ins.append(
                icon + " เดือน " + mn + ": " + str(last) +
                " รายการ (" + word + " " +
                str(round(abs(pct), 1)) + "%)"
            )

    if USERTYPE_COL and USERTYPE_COL in dff.columns:
        vc = dff[USERTYPE_COL].value_counts()
        if not vc.empty:
            ins.append(
                "👤 กลุ่มมากสุด: " + str(vc.idxmax()) +
                " (" + str(vc.max()) + " รายการ, " +
                str(round(vc.max() / total * 100, 1)) + "%)"
            )

    if DEPT_COL and DEPT_COL in dff.columns:
        vc = dff[DEPT_COL].value_counts()
        if not vc.empty:
            ins.append(
                "🏫 คณะมากสุด: " + str(vc.idxmax()) +
                " (" + str(vc.max()) + " รายการ)"
            )

    if "_hour" in dff.columns:
        vc = dff["_hour"].value_counts()
        if not vc.empty:
            h = int(vc.idxmax())
            ins.append(
                "⏰ ช่วงยอดนิยม: " + str(h) +
                ":00 - " + str(h + 1) + ":00 น."
            )

    if "_dow" in dff.columns:
        dm = {
            "Monday": "จันทร์", "Tuesday": "อังคาร",
            "Wednesday": "พุธ", "Thursday": "พฤหัสบดี",
            "Friday": "ศุกร์", "Saturday": "เสาร์",
            "Sunday": "อาทิตย์"
        }
        vc = dff["_dow"].value_counts()
        if not vc.empty:
            ins.append(
                "📅 วันมากสุด: วัน" +
                dm.get(vc.idxmax(), str(vc.idxmax()))
            )

    if RETURN_COL and RETURN_COL in dff.columns:
        r = count_status(
            dff[RETURN_COL], ["คืน"],
            exclude=["ยังไม่", "ไม่ได้"]
        )
        rate = r / total * 100
        if rate < 50:
            wrn.append(
                "อัตราคืน " + str(round(rate, 1)) +
                "% -- ค้างอยู่ " + str(total - r) + " รายการ"
            )
        else:
            ins.append(
                "อัตราการคืน " + str(round(rate, 1)) +
                "% -- อยู่ในเกณฑ์ดี"
            )

    if STATUS_COL:
        p = total - count_status(
            dff[STATUS_COL], ["อนุมัติ"],
            exclude=["ไม่อนุมัติ", "รออนุมัติ", "ยังไม่"]
        )
        if p > 0:
            wrn.append(
                "รออนุมัติ " + str(p) +
                " รายการ -- กรุณาดำเนินการ"
            )

    if overdue > 0:
        wrn.append(
            "เกินกำหนดคืน " + str(overdue) +
            " รายการ -- ติดตามด่วน"
        )

    return ins, wrn


ins_list, wrn_list = ai_insight(dff, total, overdue)
ca, cb = st.columns([3, 2])
with ca:
    st.markdown(
        "<div class='ai-box'><b>🤖 AI Analysis</b></div>",
        unsafe_allow_html=True
    )
    for i in ins_list:
        st.success(i)
with cb:
    st.markdown(
        "<div class='alert-box'><b>🚨 AI Alert</b></div>",
        unsafe_allow_html=True
    )
    if wrn_list:
        for w in wrn_list:
            st.error(w)
    else:
        st.info("ไม่มีรายการแจ้งเตือน")

st.markdown("---")

# ============================================================
# MONTHLY TREND
# ============================================================
st.subheader("📈 แนวโน้มการขอใช้บริการรายเดือน")

if "_month_dt" in dff.columns and dff["_month_dt"].notna().any():
    if USERTYPE_COL and USERTYPE_COL in dff.columns:
        mdf = (
            dff.groupby(["_month_dt", USERTYPE_COL])
               .size().reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        mo = (
            mdf[["_month_dt", "เดือน"]].drop_duplicates()
               .sort_values("_month_dt")["เดือน"].tolist()
        )
        fig_t = px.line(
            mdf, x="เดือน", y="จำนวน",
            color=USERTYPE_COL, markers=True,
            title="แนวโน้มรายเดือน แยกประเภทผู้ใช้",
            color_discrete_sequence=px.colors.qualitative.Safe,
            category_orders={"เดือน": mo}
        )
    else:
        mdf = (
            dff.groupby("_month_dt").size()
               .reset_index(name="จำนวน")
               .sort_values("_month_dt")
        )
        mdf["เดือน"] = mdf["_month_dt"].dt.strftime("%b %Y")
        mo = mdf["เดือน"].tolist()
        fig_t = px.line(
            mdf, x="เดือน", y="จำนวน", markers=True,
            title="แนวโน้มรายเดือน",
            color_discrete_sequence=["#667eea"],
            category_orders={"เดือน": mo}
        )
        fig_t.update_traces(
            fill="tozeroy",
            fillcolor="rgba(102,126,234,0.15)"
        )
    fig_t.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_t, use_container_width=True)
else:
    st.info("ไม่พบข้อมูลเวลาสำหรับกราฟรายเดือน")

st.markdown("---")

# ============================================================
# TOP 5
# ============================================================
st.subheader("🏆 Top 5")

t1, t2 = st.columns(2)
with t1:
    col_use = TOOL_COL if TOOL_COL else USERTYPE_COL
    ttl     = "Top 5 เครื่องมือ" if TOOL_COL else "Top 5 ประเภทผู้ใช้"
    fig     = make_bar(dff, col_use, ttl, "Viridis")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลเครื่องมือ")

with t2:
    col_use = LOCATION_COL if LOCATION_COL else DEPT_COL
    ttl     = "Top 5 สถานที่" if LOCATION_COL else "Top 5 คณะ/หน่วยงาน"
    fig     = make_bar(dff, col_use, ttl, "Oranges")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลสถานที่")

st.markdown("---")

# ============================================================
# PIE CHARTS
# ============================================================
st.subheader("🎯 สัดส่วนข้อมูลสำคัญ")

p1, p2 = st.columns(2)
with p1:
    fig = make_pie(dff, USERTYPE_COL, "ประเภทผู้ใช้",
                   px.colors.qualitative.Safe)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
with p2:
    fig = make_pie(dff, DEPT_COL, "คณะ/หน่วยงาน",
                   px.colors.qualitative.Pastel)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

p3, p4 = st.columns(2)
with p3:
    fig = make_pie(dff, STATUS_COL, "สถานะการอนุมัติ",
                   ["#FFCC00", "#2ecc71", "#e74c3c", "#95a5a6"])
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
with p4:
    fig = make_pie(dff, RETURN_COL, "สถานะการคืน",
                   ["#3498db", "#95a5a6", "#e67e22"])
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# HEATMAP
# ============================================================
st.subheader("🗓️ Heatmap วันและเวลายอดนิยม")

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
           .size().reset_index(name="count")
    )
    pivot = (
        hdf.pivot(index="_dow", columns="_hour", values="count")
           .reindex(day_order).fillna(0)
    )
    pivot.index = day_th
    fig = px.imshow(
        pivot,
        labels=dict(x="ชั่วโมง", y="วัน", color="จำนวน"),
        title="จำนวนคำขอตามวันและเวลา",
        color_continuous_scale="YlOrRd",
        aspect="auto"
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ไม่พบข้อมูลเวลาสำหรับ Heatmap")

st.markdown("---")

# ============================================================
# OVERDUE — สร้าง summary นอก tab
# ============================================================
st.subheader("🚨 รายการที่เกินกำหนดคืน")

if DATE_END_COL and RETURN_COL:
    not_ret_mask = (
        ~dff[RETURN_COL].str.contains("คืน", na=False, case=False)
        | dff[RETURN_COL].str.contains(
            "ยังไม่|ไม่ได้", na=False, case=False
        )
    )
    od      = dff[(dff[DATE_END_COL] < NOW) & not_ret_mask].copy()
    ever_od = dff[dff[DATE_END_COL] < NOW].copy()

    if not ever_od.empty:
        ever_od["เกินกำหนด (วัน)"] = (
            NOW - ever_od[DATE_END_COL]
        ).dt.days

    # ✅ สร้าง summary นอก tab
    summary = pd.DataFrame()
    if NAME_COL and not ever_od.empty:
        summary = (
            ever_od.groupby(NAME_COL)
            .agg(
                จำนวนครั้ง=("เกินกำหนด (วัน)", "count"),
                เฉลี่ย_วัน=("เกินกำหนด (วัน)", "mean"),
                สูงสุด_วัน=("เกินกำหนด (วัน)", "max"),
            )
            .reset_index()
            .sort_values("จำนวนครั้ง", ascending=False)
            .reset_index(drop=True)
        )
        summary["เฉลี่ย_วัน"] = summary["เฉลี่ย_วัน"].round(1)

        if DEPT_COL:
            dm = (
                dff.groupby(NAME_COL)[DEPT_COL]
                   .first().reset_index()
            )
            summary = summary.merge(dm, on=NAME_COL, how="left")
        if PHONE_COL:
            pm = (
                dff.groupby(NAME_COL)[PHONE_COL]
                   .first().reset_index()
            )
            summary = summary.merge(pm, on=NAME_COL, how="left")

    tab1, tab2, tab3 = st.tabs([
        "ยังไม่คืน", "ประวัติรายคน", "กราฟความถี่"
    ])

    with tab1:
        if not od.empty:
            od["เกินกำหนด (วัน)"] = (NOW - od[DATE_END_COL]).dt.days
            show_od = [c for c in [
                NAME_COL, USERTYPE_COL, DEPT_COL,
                DATE_END_COL, RETURN_COL,
                "เกินกำหนด (วัน)", PHONE_COL
            ] if c and c in od.columns]
            st.error(
                "พบ " + str(len(od)) +
                " รายการที่ยังไม่คืนและเกินกำหนด"
            )
            st.dataframe(
                od[show_od].sort_values(
                    "เกินกำหนด (วัน)", ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("ไม่มีรายการค้างคืน")

    with tab2:
        if not summary.empty:
            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "จำนวนครั้ง": st.column_config.NumberColumn(
                        "ครั้งที่เกิน"
                    ),
                    "เฉลี่ย_วัน": st.column_config.NumberColumn(
                        "เฉลี่ย (วัน)"
                    ),
                    "สูงสุด_วัน": st.column_config.NumberColumn(
                        "สูงสุด (วัน)"
                    ),
                }
            )
            st.download_button(
                "ดาวน์โหลดประวัติ (CSV)",
                data=summary.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name=(
                    "overdue_" +
                    NOW.strftime("%Y%m%d") + ".csv"
                ),
                mime="text/csv"
            )
        else:
            st.info("ไม่มีข้อมูลประวัติ")

    with tab3:
        if not summary.empty and not ever_od.empty:
            g1, g2 = st.columns(2)
            with g1:
                top10 = summary.head(10).copy()
                fig_f = px.bar(
                    top10,
                    x="จำนวนครั้ง",
                    y=NAME_COL,
                    orientation="h",
                    title="Top 10 ผู้เกินกำหนดบ่อยสุด",
                    color="จำนวนครั้ง",
                    color_continuous_scale="Reds",
                    text="จำนวนครั้ง"
                )
                fig_f.update_traces(textposition="outside")
                fig_f.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(autorange="reversed"),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_f, use_container_width=True)

            with g2:
                fig_h = px.histogram(
                    ever_od,
                    x="เกินกำหนด (วัน)",
                    nbins=20,
                    title="การกระจายวันที่เกินกำหนด",
                    color_discrete_sequence=["#f5576c"]
                )
                fig_h.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_h, use_container_width=True)

            if "_month_dt" in ever_od.columns:
                mod = (
                    ever_od.groupby("_month_dt").size()
                           .reset_index(name="จำนวน")
                           .sort_values("_month_dt")
                )
                mod["เดือน"] = (
                    mod["_month_dt"].dt.strftime("%b %Y")
                )
                mo_od = mod["เดือน"].tolist()
                fig_ot = px.line(
                    mod,
                    x="เดือน",
                    y="จำนวน",
                    markers=True,
                    title="แนวโน้มการเกินกำหนดรายเดือน",
                    color_discrete_sequence=["#f5576c"],
                    category_orders={"เดือน": mo_od}
                )
                fig_ot.update_traces(
                    fill="tozeroy",
                    fillcolor="rgba(245,87,108,0.15)"
                )
                fig_ot.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(tickangle=-45)
                )
                st.plotly_chart(fig_ot, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลกราฟ")

else:
    st.warning(
        "ไม่พบคอลัมน์วันที่สิ้นสุดการยืม -- "
        "เปิด Debug ด้านบนเพื่อดูชื่อคอลัมน์จริง"
    )

st.markdown("---")

# ============================================================
# DATA TABLE + SEARCH + EXPORT
# ============================================================
st.subheader("📋 รายละเอียดผู้ขอใช้บริการทั้งหมด")

search = st.text_input(
    "ค้นหาข้อมูล",
    placeholder="ชื่อ, คณะ, สถานะ..."
)

show_cols = [c for c in [
    "Timestamp", NAME_COL, USERTYPE_COL, DEPT_COL,
    PURPOSE_COL, PHONE_COL, EMAIL_COL,
    STATUS_COL, RETURN_COL,
] if c and c in dff.columns]

disp = dff[show_cols].copy()

if "Timestamp" in disp.columns:
    disp = disp.sort_values("Timestamp", ascending=True)
    disp["Timestamp"] = disp["Timestamp"].dt.strftime(
        "%d/%m/%Y %H:%M"
    )

if search.strip():
    mask = disp.apply(
        lambda r: r.astype(str)
                   .str.contains(search.strip(), case=False)
                   .any(),
        axis=1
    )
    disp = disp[mask]
    st.caption("พบ " + str(len(disp)) + " รายการ")

st.dataframe(disp, use_container_width=True, hide_index=True)

st.download_button(
    "ดาวน์โหลด CSV",
    data=disp.to_csv(index=False).encode("utf-8-sig"),
    file_name="report_" + NOW.strftime("%Y%m%d_%H%M") + ".csv",
    mime="text/csv"
)

st.markdown("---")

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    "<div style='text-align:center;color:#999;"
    "font-size:.8rem;padding:10px;'>"
    "🧪 Science Equipment Dashboard -- AI Enhanced | "
    "อัปเดตทุก 60 วินาที | " +
    NOW.strftime("%d/%m/%Y %H:%M") +
    " น. | ปกปิดข้อมูลส่วนบุคคลตาม PDPA"
    "</div>",
    unsafe_allow_html=True
)
