import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ============================================================
# 1. ตั้งค่าหน้าเว็บ
# ============================================================
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #f0f2f6; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .metric-card h2 { font-size: 2.5rem; margin: 0; font-weight: 700; }
    .metric-card p  { margin: 5px 0 0 0; font-size: 1rem; opacity: 0.9; }
    .ai-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .ai-box h4 { margin-top: 0; font-size: 1.1rem; }
    .alert-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .info-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 15px;
        padding: 15px 20px;
        color: white;
        margin-bottom: 10px;
    }
    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
    .dataframe-container { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. โหลดข้อมูลจาก Google Sheets
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
        st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้: {e}")
        return pd.DataFrame()

    # แปลง Timestamp
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')

    # ✅ BUG FIX #1 — mask_name: ใช้ parts และ parts ให้ถูกต้อง
    if 'ชื่อ-สกุล' in df.columns:
        def mask_name(name):
            name = str(name).strip()
            if not name or name.lower() == 'nan':
                return "-"
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts} {parts}***"   # ✅ แก้จาก parts → parts, parts
            return name + "***"
        df['ชื่อ-สกุล'] = df['ชื่อ-สกุล'].apply(mask_name)

    # mask_phone (ถูกต้องแล้ว)
    if 'เบอร์โทรศัพท์เพื่อติดต่อ' in df.columns:
        def mask_phone(phone):
            try:
                p = str(phone).strip()
                if p.lower() == 'nan' or not p:
                    return "-"
                if p.endswith('.0'):
                    p = p[:-2]
                if len(p) >= 9:
                    return f"{p[:3]}-XXX-{p[-4:]}"
                return "-"
            except:
                return "-"
        df['เบอร์โทรศัพท์เพื่อติดต่อ'] = df['เบอร์โทรศัพท์เพื่อติดต่อ'].apply(mask_phone)

    # ✅ BUG FIX #2 — mask_email: วนลูปทีละคอลัมน์ ไม่ใช้ list เป็น key
    def mask_email(email):
        email = str(email).strip()
        if email.lower() == 'nan' or not email:
            return "-"
        if '@' in email:
            parts = email.split('@')
            visible = parts if parts else '*'
            return f"{visible}***@{parts}"           # ✅ แก้จาก parts → parts, parts
        return "-"

    for col in df.columns:                               # ✅ วนลูปแทนการใช้ list
        if 'email' in col.lower() or 'อีเมล' in col:
            df[col] = df[col].apply(mask_email)

    return df


df = load_data()

if df.empty:
    st.warning("⏳ กำลังรอข้อมูลจาก Google Sheets...")
    st.stop()

# ============================================================
# 3. ตรวจหาชื่อคอลัมน์อัตโนมัติ
# ✅ BUG FIX #3 — ทุกตัวแปรต้องเป็น string เดี่ยว ไม่ใช่ list
# ============================================================
status_col    = 'สถานะ'   if 'สถานะ'   in df.columns else None
return_col    = 'การคืน'  if 'การคืน'  in df.columns else None

type_cols     = [c for c in df.columns if 'ประเภท' in c]
user_type_col = type_cols if type_cols else None          # ✅  ไม่ใช่ list ทั้งก้อน

dept_cols     = [c for c in df.columns if 'คณะ' in c or 'หน่วยงาน' in c]
dept_col      = dept_cols if dept_cols else None          # ✅

tool_cols     = [c for c in df.columns if 'เครื่องมือ' in c or 'อุปกรณ์' in c]
tool_col      = tool_cols if tool_cols else None          # ✅

location_cols = [c for c in df.columns if 'โรงเรือน' in c or 'สถานที่' in c or 'ห้อง' in c]
location_col  = location_cols if location_cols else None  # ✅

purpose_cols  = [c for c in df.columns if 'วัตถุประสงค์' in c or 'เรื่อง' in c or 'จุดประสงค์' in c]
purpose_col   = purpose_cols if purpose_cols else None    # ✅

date_start_cols = [c for c in df.columns if 'วันที่' in c and ('เริ่ม' in c or 'ต้น' in c)]
date_end_cols   = [c for c in df.columns if 'วันที่' in c and ('สิ้น' in c or 'คืน' in c or 'สุด' in c)]
date_start_col  = date_start_cols if date_start_cols else None  # ✅
date_end_col    = date_end_cols   if date_end_cols   else None  # ✅

# ✅ BUG FIX #4 — แปลงวันที่ด้วยชื่อคอลัมน์ string เดี่ยว
if date_start_col:
    df[date_start_col] = pd.to_datetime(df[date_start_col], errors='coerce')
if date_end_col:
    df[date_end_col]   = pd.to_datetime(df[date_end_col],   errors='coerce')

# จัดการค่าว่าง
if user_type_col: df[user_type_col] = df[user_type_col].fillna('ไม่ระบุ')
if dept_col:      df[dept_col]      = df[dept_col].fillna('ไม่ระบุ')
if status_col:    df[status_col]    = df[status_col].fillna('ยังไม่ระบุสถานะ')
if return_col:    df[return_col]    = df[return_col].fillna('ยังไม่ระบุข้อมูล')
if tool_col:      df[tool_col]      = df[tool_col].fillna('ไม่ระบุ')
if location_col:  df[location_col]  = df[location_col].fillna('ไม่ระบุ')

# ============================================================
# 4. เพิ่มคอลัมน์ช่วยคำนวณ
# ============================================================
if 'Timestamp' in df.columns:
    df['YearMonth'] = df['Timestamp'].dt.to_period('M').astype(str)
    df['Month_dt']  = df['Timestamp'].dt.to_period('M').dt.to_timestamp()
    df['MonthTH']   = df['Timestamp'].dt.strftime('%b %Y')
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['Hour']      = df['Timestamp'].dt.hour

# ============================================================
# 5. Sidebar — Filters (Slicer)
# ============================================================
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/"
        "Wikimedia-logo.png/240px-Wikimedia-logo.png",
        width=80
    )
    st.title("🔽 ตัวกรองข้อมูล")
    st.markdown("เลือกเงื่อนไขเพื่อกรองข้อมูลในทุกส่วนของ Dashboard")

    if user_type_col:
        all_types = ['ทั้งหมด'] + sorted(df[user_type_col].unique().tolist())
        sel_type  = st.selectbox("👤 ประเภทผู้ใช้งาน", all_types)
    else:
        sel_type = 'ทั้งหมด'

    if dept_col:
        all_depts = ['ทั้งหมด'] + sorted(df[dept_col].unique().tolist())
        sel_dept  = st.selectbox("🏫 คณะ/หน่วยงาน", all_depts)
    else:
        sel_dept = 'ทั้งหมด'

    if status_col:
        all_status = ['ทั้งหมด'] + sorted(df[status_col].unique().tolist())
        sel_status = st.selectbox("📋 สถานะการอนุมัติ", all_status)
    else:
        sel_status = 'ทั้งหมด'

    if return_col:
        all_return = ['ทั้งหมด'] + sorted(df[return_col].unique().tolist())
        sel_return = st.selectbox("📦 สถานะการคืน", all_return)
    else:
        sel_return = 'ทั้งหมด'

    st.markdown("---")
    st.markdown("📅 **ช่วงเวลา**")
    date_range = None
    if 'Timestamp' in df.columns:
        min_date = df['Timestamp'].dropna().min().date()
        max_date = df['Timestamp'].dropna().max().date()
        date_range = st.date_input(
            "เลือกช่วงวันที่",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    st.markdown("---")
    st.markdown("🔄 **รีเฟรชข้อมูล**")
    if st.button("🔄 โหลดข้อมูลใหม่"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"อัปเดตล่าสุด: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# 6. กรองข้อมูลตาม Sidebar
# ============================================================
dff = df.copy()

if sel_type   != 'ทั้งหมด' and user_type_col:
    dff = dff[dff[user_type_col] == sel_type]
if sel_dept   != 'ทั้งหมด' and dept_col:
    dff = dff[dff[dept_col]      == sel_dept]
if sel_status != 'ทั้งหมด' and status_col:
    dff = dff[dff[status_col]    == sel_status]
if sel_return != 'ทั้งหมด' and return_col:
    dff = dff[dff[return_col]    == sel_return]

# ✅ BUG FIX #5 — date_range ต้องใช้  และ 
if date_range and 'Timestamp' in dff.columns and len(date_range) == 2:
    start_dt = pd.Timestamp(date_range)               # ✅ date_range
    end_dt   = pd.Timestamp(date_range) + pd.Timedelta(days=1)  # ✅ date_range
    dff = dff[(dff['Timestamp'] >= start_dt) & (dff['Timestamp'] < end_dt)]

# ============================================================
# 7. Header
# ============================================================
st.markdown("""
<div style='background:linear-gradient(135deg,#667eea,#764ba2);
            padding:30px; border-radius:20px; margin-bottom:20px;
            color:white; text-align:center;'>
    <h1 style='margin:0; font-size:2.2rem;'>
        🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์
    </h1>
    <p style='margin:8px 0 0 0; opacity:.85; font-size:1rem;'>
        Science Equipment Request Monitoring Dashboard — AI Enhanced
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 8. KPI Scorecard
# ============================================================
st.subheader("📊 ภาพรวมสถิติสำคัญ (KPI Scorecard)")

now        = pd.Timestamp.now()
this_month = now.to_period('M')

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    total = len(dff)
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#667eea,#764ba2);'>
        <h2>{total}</h2><p>📝 คำขอทั้งหมด</p>
    </div>""", unsafe_allow_html=True)

with kpi2:
    if 'Timestamp' in dff.columns:
        this_m_count = len(
            dff[dff['Timestamp'].dt.to_period('M') == this_month]
        )
    else:
        this_m_count = 0
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#f093fb,#f5576c);'>
        <h2>{this_m_count}</h2><p>📅 คำขอเดือนนี้</p>
    </div>""", unsafe_allow_html=True)

with kpi3:
    if status_col:
        approved = len(dff[dff[status_col] == 'อนุมัติแล้ว'])
        pending  = total - approved
    else:
        pending = 0
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#f6d365,#fda085);'>
        <h2>{pending}</h2><p>⏳ รออนุมัติ</p>
    </div>""", unsafe_allow_html=True)

with kpi4:
    if return_col:
        returned = len(dff[dff[return_col] == 'คืนเรียบร้อย'])
    else:
        returned = 0
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#43e97b,#38f9d7);'>
        <h2>{returned}</h2><p>✅ คืนของแล้ว</p>
    </div>""", unsafe_allow_html=True)

with kpi5:
    overdue = 0
    if date_end_col and return_col:
        overdue_mask = (
            (dff[date_end_col] < now) &
            (dff[return_col] != 'คืนเรียบร้อย')
        )
        overdue = int(overdue_mask.sum())
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#f5576c,#f093fb);'>
        <h2>{overdue}</h2><p>🚨 เกินกำหนดคืน</p>
    </div>""", unsafe_allow_html=True)

with kpi6:
    unique_users = dff[user_type_col].nunique() if user_type_col else 0
    st.markdown(f"""
    <div class='metric-card'
         style='background:linear-gradient(135deg,#4facfe,#00f2fe);'>
        <h2>{unique_users}</h2><p>👥 ประเภทผู้ใช้</p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# 9. AI Insight Box
# ============================================================
st.subheader("🤖 AI Insight — สรุปและข้อเสนอแนะอัตโนมัติ")

def generate_ai_insight(dff, status_col, return_col, user_type_col, dept_col):
    insights = []
    warnings = []
    total = len(dff)
    if total == 0:
        return ["ไม่มีข้อมูลในช่วงที่เลือก"], []

    # 1. แนวโน้มรายเดือน
    if 'Month_dt' in dff.columns:
        monthly = dff.groupby('Month_dt').size().reset_index(name='count')
        if len(monthly) >= 2:
            last       = monthly.iloc[-1]['count']
            prev       = monthly.iloc[-2]['count']
            month_name = monthly.iloc[-1]['Month_dt'].strftime('%B %Y')
            pct = ((last - prev) / prev * 100) if prev > 0 else 0
            if pct >= 0:
                insights.append(
                    f"📈 เดือนล่าสุด ({month_name}) มีคำขอ **{last} รายการ** "
                    f"เพิ่มขึ้น {pct:.1f}% จากเดือนก่อน — แนะนำเตรียมทีมรองรับ"
                )
            else:
                insights.append(
                    f"📉 เดือนล่าสุด ({month_name}) มีคำขอ **{last} รายการ** "
                    f"ลดลง {abs(pct):.1f}% จากเดือนก่อน"
                )

    # 2. ประเภทผู้ใช้มากสุด
    if user_type_col:
        top_user     = dff[user_type_col].value_counts().idxmax()
        top_user_cnt = dff[user_type_col].value_counts().max()
        pct_user     = top_user_cnt / total * 100
        insights.append(
            f"👤 กลุ่มผู้ใช้งานมากที่สุดคือ **{top_user}** "
            f"({top_user_cnt} รายการ, {pct_user:.1f}%)"
        )

    # 3. คณะ/หน่วยงานมากสุด
    if dept_col:
        top_dept     = dff[dept_col].value_counts().idxmax()
        top_dept_cnt = dff[dept_col].value_counts().max()
        insights.append(
            f"🏫 คณะ/หน่วยงานที่ขอใช้บริการมากที่สุดคือ **{top_dept}** "
            f"({top_dept_cnt} รายการ)"
        )

    # 4. ชั่วโมงยอดนิยม
    if 'Hour' in dff.columns:
        top_hour = int(dff['Hour'].value_counts().idxmax())
        insights.append(
            f"⏰ ช่วงเวลาที่มีการส่งคำขอมากที่สุดคือ "
            f"**{top_hour}:00 - {top_hour+1}:00 น.**"
        )

    # 5. วันยอดนิยม
    if 'DayOfWeek' in dff.columns:
        day_map = {
            'Monday':'วันจันทร์','Tuesday':'วันอังคาร',
            'Wednesday':'วันพุธ','Thursday':'วันพฤหัสบดี',
            'Friday':'วันศุกร์','Saturday':'วันเสาร์','Sunday':'วันอาทิตย์'
        }
        top_day = dff['DayOfWeek'].value_counts().idxmax()
        insights.append(
            f"📅 **{day_map.get(top_day, top_day)}** "
            f"คือวันที่มีคำขอบ่อยที่สุดในสัปดาห์"
        )

    # 6. อัตราการคืน
    if return_col:
        returned_cnt = len(dff[dff[return_col] == 'คืนเรียบร้อย'])
        rate = returned_cnt / total * 100
        if rate < 50:
            warnings.append(
                f"⚠️ อัตราการคืนอุปกรณ์อยู่ที่ **{rate:.1f}%** เท่านั้น "
                f"— ควรติดตามรายการที่ยังไม่คืนจำนวน {total - returned_cnt} รายการ"
            )
        else:
            insights.append(
                f"✅ อัตราการคืนอุปกรณ์อยู่ที่ **{rate:.1f}%** — อยู่ในเกณฑ์ดี"
            )

    # 7. รายการเกินกำหนด
    if overdue > 0:
        warnings.append(
            f"🚨 พบรายการ **เกินกำหนดคืน {overdue} รายการ** "
            f"— กรุณาติดตามผู้ยืมโดยด่วน"
        )

    return insights, warnings


insights, warnings = generate_ai_insight(
    dff, status_col, return_col, user_type_col, dept_col
)

col_ins, col_warn = st.columns([3, 2])

with col_ins:
    st.markdown("""
    <div class='ai-box'>
        <h4>🤖 AI Analysis — ผลการวิเคราะห์ข้อมูลอัตโนมัติ</h4>
    </div>""", unsafe_allow_html=True)
    for ins in insights:
        st.success(ins)

with col_warn:
    st.markdown("""
    <div class='alert-box'>
        <h4>🚨 AI Alert — รายการที่ต้องดำเนินการ</h4>
    </div>""", unsafe_allow_html=True)
    if warnings:
        for w in warnings:
            st.error(w)
    else:
        st.info("✅ ไม่พบรายการที่ต้องแจ้งเตือน ณ ขณะนี้")

st.markdown("---")

# ============================================================
# 10. Monthly Trend
# ============================================================
st.subheader("📈 แนวโน้มการขอใช้บริการรายเดือน (Monthly Trend)")

if 'Month_dt' in dff.columns and not dff['Month_dt'].isna().all():
    monthly_df = (
        dff.groupby('Month_dt')
           .size()
           .reset_index(name='จำนวนคำขอ')
           .sort_values('Month_dt')
    )
    monthly_df['Month_Label'] = monthly_df['Month_dt'].dt.strftime('%b %Y')

    if user_type_col:
        monthly_type = (
            dff.groupby(['Month_dt', user_type_col])
               .size()
               .reset_index(name='จำนวนคำขอ')
               .sort_values('Month_dt')
        )
        monthly_type['Month_Label'] = (
            monthly_type['Month_dt'].dt.strftime('%b %Y')
        )
        fig_trend = px.line(
            monthly_type,
            x='Month_Label', y='จำนวนคำขอ',
            color=user_type_col, markers=True,
            title='แนวโน้มการขอใช้บริการรายเดือน แยกตามประเภทผู้ใช้',
            labels={'Month_Label':'เดือน','จำนวนคำขอ':'จำนวน (รายการ)'},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
    else:
        fig_trend = px.line(
            monthly_df,
            x='Month_Label', y='จำนวนคำขอ',
            markers=True,
            title='แนวโน้มการขอใช้บริการรายเดือน',
            labels={'Month_Label':'เดือน','จำนวนคำขอ':'จำนวน (รายการ)'},
            color_discrete_sequence=['#667eea']
        )
        fig_trend.update_traces(
            fill='tozeroy', fillcolor='rgba(102,126,234,0.15)'
        )

    fig_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("ℹ️ ไม่พบข้อมูล Timestamp สำหรับสร้างกราฟรายเดือน")

st.markdown("---")

# ============================================================
# 11. Top 5 Tools / Locations
# ============================================================
st.subheader("🏆 Top 5 — เครื่องมือและสถานที่ที่ถูกขอใช้บ่อยที่สุด")
col_t1, col_t2 = st.columns(2)

with col_t1:
    target_col = tool_col if tool_col else user_type_col
    chart_title = (
        '🔬 Top 5 เครื่องมือที่ถูกขอใช้มากที่สุด'
        if tool_col else 'Top 5 ประเภทผู้ใช้งาน'
    )
    col_label = 'เครื่องมือ' if tool_col else 'ประเภท'

    if target_col:
        top_df = (
            dff[target_col].value_counts()
            .head(5).reset_index()
        )
        top_df.columns = [col_label, 'จำนวน']
        fig_t1 = px.bar(
            top_df, x='จำนวน', y=col_label, orientation='h',
            title=chart_title,
            color='จำนวน', color_continuous_scale='Viridis', text='จำนวน'
        )
        fig_t1.update_traces(textposition='outside')
        fig_t1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange='reversed'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_t1, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบคอลัมน์ข้อมูลเครื่องมือ")

with col_t2:
    target_col2  = location_col if location_col else dept_col
    chart_title2 = (
        '🏠 Top 5 สถานที่/โรงเรือนที่ถูกขอใช้มากที่สุด'
        if location_col else 'Top 5 คณะ/หน่วยงานที่ขอใช้บริการมากที่สุด'
    )
    col_label2 = 'สถานที่' if location_col else 'คณะ/หน่วยงาน'

    if target_col2:
        top_df2 = (
            dff[target_col2].value_counts()
            .head(5).reset_index()
        )
        top_df2.columns = [col_label2, 'จำนวน']
        fig_t2 = px.bar(
            top_df2, x='จำนวน', y=col_label2, orientation='h',
            title=chart_title2,
            color='จำนวน', color_continuous_scale='Oranges', text='จำนวน'
        )
        fig_t2.update_traces(textposition='outside')
        fig_t2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange='reversed'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_t2, use_container_width=True)
    else:
        st.info("ℹ️ ไม่พบคอลัมน์ข้อมูลสถานที่/โรงเรือน")

st.markdown("---")

# ============================================================
# 12. Pie Charts
# ============================================================
st.subheader("🎯 สรุปสัดส่วนข้อมูลสำคัญ")
c1, c2 = st.columns(2)

with c1:
    if user_type_col:
        fig_user = px.pie(
            dff, names=user_type_col,
            title='สัดส่วนประเภทผู้ใช้งาน', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_user.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_user, use_container_width=True)

with c2:
    if dept_col:
        fig_dept = px.pie(
            dff, names=dept_col,
            title='สัดส่วนตามคณะ/หน่วยงาน', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_dept.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_dept, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    if status_col:
        fig_status = px.pie(
            dff, names=status_col,
            title='สถานะการอนุมัติ', hole=0.4,
            color_discrete_sequence=['#FFCC00','#2ecc71','#e74c3c','#95a5a6']
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)

with c4:
    if return_col:
        fig_return = px.pie(
            dff, names=return_col,
            title='สถานะการคืนอุปกรณ์', hole=0.4,
            color_discrete_sequence=['#3498db','#95a5a6','#e67e22']
        )
        fig_return.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_return, use_container_width=True)

st.markdown("---")

# ============================================================
# 13. Heatmap
# ============================================================
st.subheader("🗓️ Heatmap — ช่วงเวลาและวันที่ยอดนิยม")

if 'DayOfWeek' in dff.columns and 'Hour' in dff.columns:
    day_order = [
        'Monday','Tuesday','Wednesday',
        'Thursday','Friday','Saturday','Sunday'
    ]
    day_th = ['จันทร์','อังคาร','พุธ','พฤหัส','ศุกร์','เสาร์','อาทิตย์']

    heat_df = (
        dff.groupby(['DayOfWeek','Hour'])
           .size()
           .reset_index(name='count')
    )
    heat_pivot = (
        heat_df.pivot(index='DayOfWeek', columns='Hour', values='count')
               .reindex(day_order)
               .fillna(0)
    )
    heat_pivot.index = day_th

    fig_heat = px.imshow(
        heat_pivot,
        labels=dict(x='ชั่วโมง', y='วัน', color='จำนวนคำขอ'),
        title='จำนวนคำขอตามวันและช่วงเวลา (Heatmap)',
        color_continuous_scale='YlOrRd',
        aspect='auto'
    )
    fig_heat.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("ℹ️ ไม่พบข้อมูล Timestamp สำหรับสร้าง Heatmap")

st.markdown("---")

# ============================================================
# 14. ตารางเกินกำหนด
# ============================================================
st.subheader("🚨 รายการที่เกินกำหนดคืน (ต้องดำเนินการด่วน)")

if date_end_col and return_col:
    overdue_df = dff[
        (dff[date_end_col] < now) &
        (dff[return_col]   != 'คืนเรียบร้อย')
    ].copy()

    if not overdue_df.empty:
        overdue_df['เกินกำหนด (วัน)'] = (
            now - overdue_df[date_end_col]
        ).dt.days

        overdue_cols = [
            'ชื่อ-สกุล', date_end_col, return_col,
            'เกินกำหนด (วัน)', 'เบอร์โทรศัพท์เพื่อติดต่อ'
        ]
        if user_type_col: overdue_cols.insert(2, user_type_col)
        if dept_col:      overdue_cols.insert(3, dept_col)
        valid_oc = [c for c in overdue_cols if c in overdue_df.columns]

        st.error(f"⚠️ พบรายการเกินกำหนดคืน {len(overdue_df)} รายการ")
        st.dataframe(
            overdue_df[valid_oc].sort_values(
                'เกินกำหนด (วัน)', ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ ไม่มีรายการที่เกินกำหนดคืน")
else:
    st.info("ℹ️ ไม่พบคอลัมน์วันที่สิ้นสุดการยืม — ข้ามส่วนนี้")

st.markdown("---")

# ============================================================
# 15. ตารางรายละเอียดทั้งหมด + Search + Export
# ============================================================
st.subheader("📋 รายละเอียดผู้ขอใช้บริการทั้งหมด")

search_query = st.text_input(
    "🔍 ค้นหา (ชื่อ, คณะ, สถานะ, หรือคำใดๆ ในตาราง)",
    placeholder="พิมพ์คำค้นหาที่นี่..."
)

# ✅ BUG FIX #6 — email_display ต้องเป็น string เดี่ยว ไม่ใช่ list
email_cols_list = [
    c for c in df.columns
    if 'email' in c.lower() or 'อีเมล' in c
]
email_display = email_cols_list if email_cols_list else None  # ✅ 

display_cols = [
    'Timestamp', 'ชื่อ-สกุล',
    user_type_col, dept_col, purpose_col,
    'เบอร์โทรศัพท์เพื่อติดต่อ',
    email_display,                                               # ✅ string เดี่ยว
    status_col, return_col
]
valid_display = [c for c in display_cols if c and c in dff.columns]

df_display = dff[valid_display].copy()

if 'Timestamp' in df_display.columns:
    df_display = df_display.sort_values('Timestamp', ascending=True)
    df_display['Timestamp'] = df_display['Timestamp'].dt.strftime('%d/%m/%Y %H:%M')

if search_query:
    mask = df_display.apply(
        lambda row: row.astype(str)
                      .str.contains(search_query, case=False)
                      .any(),
        axis=1
    )
    df_display = df_display[mask]
    st.caption(f"🔍 พบ {len(df_display)} รายการที่ตรงกับ '{search_query}'")

st.dataframe(df_display, use_container_width=True, hide_index=True)

csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="⬇️ ดาวน์โหลดข้อมูล (CSV)",
    data=csv_data,
    file_name=f"equipment_report_{now.strftime('%Y%m%d_%H%M')}.csv",
    mime='text/csv'
)

st.markdown("---")

# ============================================================
# 16. Footer
# ============================================================
st.markdown(f"""
<div style='text-align:center; color:#888; padding:20px; font-size:0.85rem;'>
    🧪 Science Equipment Dashboard — AI Enhanced Version<br>
    อัปเดตอัตโนมัติทุก 60 วินาที |
    ข้อมูล ณ วันที่ {now.strftime('%d/%m/%Y %H:%M')} น.<br>
    🔒 ข้อมูลส่วนบุคคลได้รับการปกปิดตาม PDPA
</div>
""", unsafe_allow_html=True)
