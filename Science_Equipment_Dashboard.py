import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ (Page Configuration)
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔴 ตรงนี้สำคัญมาก: นำลิงก์ Google Sheets ของคุณมาใส่แทนที่ (อย่าลืมเปลี่ยน /edit?usp=sharing เป็น /export?format=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/ใส่_ID_ชีตของคุณตรงนี้/export?format=csv"

# --- ส่วนโหลดและเตรียมข้อมูลแบบ Real-time ---
@st.cache_data(ttl=60) # ttl=60 คือการสั่งให้รีเฟรชข้อมูลใหม่ทุกๆ 60 วินาที
def load_data():
    try:
        # อ่านไฟล์ CSV จาก Google Sheets โดยตรง
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ Google Sheets ได้ กรุณาตรวจสอบลิงก์: {e}")
        return pd.DataFrame()

    # ลบแถวที่ไม่มีชื่อ-สกุล (ข้อมูลขยะ)
    if 'ชื่อ-สกุล' in df.columns:
        df = df.dropna(subset=['ชื่อ-สกุล'])
    
    # แปลงวันที่เป็น datetime object เพื่อให้พล็อตลงกราฟได้ถูกต้อง
    if 'เริ่มขอใช้บริการ' in df.columns:
        df['เริ่มขอใช้บริการ'] = pd.to_datetime(df['เริ่มขอใช้บริการ'], errors='coerce')
    if 'สิ้นสุดการขอใช้บริการ' in df.columns:
        df['สิ้นสุดการขอใช้บริการ'] = pd.to_datetime(df['สิ้นสุดการขอใช้บริการ'], errors='coerce')

    return df

df = load_data()

# ตกแต่ง CSS เพื่อความสวยงาม
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-left: 5px solid #4CAF50;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stHeader {
        color: #2E86C1;
    }
</style>
""", unsafe_allow_html=True)

# ตรวจสอบว่ามีข้อมูลหรือไม่ก่อนแสดงผล
if df.empty:
    st.warning("⏳ รอการเชื่อมต่อข้อมูล หรือยังไม่มีข้อมูลในแบบฟอร์ม...")
    st.stop()

# --- Sidebar: เมนูและตัวกรอง ---
st.sidebar.image("https://img.icons8.com/clouds/200/experimental-test-tube-clouds.png", width=100)
st.sidebar.title("🔬 ตัวกรองและรายละเอียด")

# 1. ตัวกรองภาพรวม (Global Filters)
st.sidebar.subheader("🔍 กรองข้อมูล Dashboard")

# เช็คคอลัมน์ก่อนสร้างตัวกรองเพื่อป้องกัน Error
if 'คณะ/หน่วยงาน' in df.columns and 'ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์' in df.columns:
    filter_dept = st.sidebar.multiselect(
        "เลือกคณะ/หน่วยงาน",
        options=df['คณะ/หน่วยงาน'].dropna().unique(),
        default=df['คณะ/หน่วยงาน'].dropna().unique()
    )

    filter_type = st.sidebar.multiselect(
        "เลือกประเภทผู้ขอใช้",
        options=df['ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์'].dropna().unique(),
        default=df['ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์'].dropna().unique()
    )

    # กรองข้อมูลใน DataFrame
    filtered_df = df[
        (df['คณะ/หน่วยงาน'].isin(filter_dept)) &
        (df['ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์'].isin(filter_type))
    ]
else:
    filtered_df = df.copy()

st.sidebar.markdown("---")

# 2. ส่วนแสดงรายละเอียดรายบุคคล (Detail View)
st.sidebar.subheader("📋 รายละเอียดผู้ขอใช้บริการ")
st.sidebar.info("เลือกรายชื่อเพื่อดูข้อมูลในเมนูนี้")

if not filtered_df.empty and 'เรื่อง' in filtered_df.columns:
    selected_person = st.sidebar.selectbox(
        "เลือกรายการ (ชื่อ - เรื่อง):",
        filtered_df.apply(lambda x: f"{x['ชื่อ-สกุล']} - {str(x.get('เรื่อง', ''))[:20]}...", axis=1)
    )
    
    if selected_person:
        selected_name = selected_person.split(" - ")[0]
        person_data = filtered_df[filtered_df['ชื่อ-สกุล'] == selected_name].iloc[0]

        st.sidebar.markdown(f"**Email Address:** {person_data.get('Email Address', '-')}")
        st.sidebar.markdown(f"**ชื่อ-สกุล:** {person_data.get('คำนำหน้าชื่อ', '')} {person_data.get('ชื่อ-สกุล', '')}")
        st.sidebar.markdown(f"**ประเภท:** {person_data.get('ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์', '-')}")
        st.sidebar.markdown(f"**เบอร์โทรศัพท์:** {person_data.get('เบอร์โทรศัพท์เพื่อติดต่อ', '-')}")
        st.sidebar.markdown(f"**คณะ/หน่วยงาน:** {person_data.get('คณะ/หน่วยงาน', '-')}")
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📅 ช่วงเวลาการใช้งาน**")
        st.sidebar.markdown(f"**เริ่ม:** {person_data.get('เริ่มขอใช้บริการ', '-')}")
        st.sidebar.markdown(f"**สิ้นสุด:** {person_data.get('สิ้นสุดการขอใช้บริการ', '-')}")

# --- Main Dashboard Area ---
st.title("🧪 Dashboard สถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown("🟢 ระบบกำลังดึงข้อมูลแบบ Real-time จาก Google Sheets")

# KPI Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📝 จำนวนคำขอทั้งหมด", f"{len(filtered_df)} รายการ")
with col2:
    if 'คณะ/หน่วยงาน' in filtered_df.columns and not filtered_df.empty:
        st.metric("🏢 หน่วยงานที่ใช้งานสูงสุด", filtered_df['คณะ/หน่วยงาน'].mode()[0])
    else:
        st.metric("🏢 หน่วยงานที่ใช้งานสูงสุด", "-")
with col3:
    if 'เริ่มขอใช้บริการ' in filtered_df.columns and not filtered_df.empty:
        st.metric("📅 เดือนที่มีการจองมากสุด", filtered_df['เริ่มขอใช้บริการ'].dt.month_name().mode()[0])
    else:
        st.metric("📅 เดือนที่มีการจองมากสุด", "-")

st.markdown("---")

# Row 1: Graphs
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📊 สัดส่วนประเภทผู้ขอใช้บริการ")
    if not filtered_df.empty and 'ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์' in filtered_df.columns:
        fig_pie = px.pie(filtered_df, names='ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์', 
                         hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.RdBu,
                         title="User Type Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("🏢 จำนวนการขอใช้แยกตามหน่วยงาน")
    if not filtered_df.empty and 'คณะ/หน่วยงาน' in filtered_df.columns:
        dept_counts = filtered_df['คณะ/หน่วยงาน'].value_counts().reset_index()
        dept_counts.columns = ['หน่วยงาน', 'จำนวนครั้ง']
        fig_bar = px.bar(dept_counts, x='หน่วยงาน', y='จำนวนครั้ง',
                         color='จำนวนครั้ง',
                         color_continuous_scale='Viridis',
                         title="Usage by Department")
        st.plotly_chart(fig_bar, use_container_width=True)

# Row 2: Data Table
st.subheader("📋 ตารางข้อมูลรวม (Data Table)")
if not filtered_df.empty:
    display_cols = ['ชื่อ-สกุล', 'ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์', 'คณะ/หน่วยงาน', 'เริ่มขอใช้บริการ']
    valid_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[valid_cols], use_container_width=True, height=400)
