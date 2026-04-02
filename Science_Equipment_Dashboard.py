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

# ลิงก์ Google Sheets ของคุณที่แปลงสำหรับดึงข้อมูลเป็น CSV แล้ว
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/export?format=csv"

# --- ส่วนโหลดและเตรียมข้อมูลแบบ Real-time ---
@st.cache_data(ttl=60) # ดึงข้อมูลใหม่ทุกๆ 60 วินาที
def load_data():
    try:
        # อ่านไฟล์ CSV จาก Google Sheets โดยตรง
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ Google Sheets ได้: {e}")
        st.info("💡 อย่าลืมตั้งค่าแชร์ Google Sheets เป็น 'ทุกคนที่มีลิงก์ (Anyone with the link)' และเป็น 'ผู้มีสิทธิ์อ่าน (Viewer)' นะครับ")
        return pd.DataFrame()

    # ลบแถวที่ไม่มีชื่อ-สกุล (เพื่อกรองแถวว่างทิ้ง)
    if 'ชื่อ-สกุล' in df.columns:
        df = df.dropna(subset=['ชื่อ-สกุล'])
    
    # แปลงวันที่ให้กราฟอ่านได้
    if 'เริ่มขอใช้บริการ' in df.columns:
        df['เริ่มขอใช้บริการ'] = pd.to_datetime(df['เริ่มขอใช้บริการ'], errors='coerce')
    if 'สิ้นสุดการขอใช้บริการ' in df.columns:
        df['สิ้นสุดการขอใช้บริการ'] = pd.to_datetime(df['สิ้นสุดการขอใช้บริการ'], errors='coerce')

    return df

df = load_data()

# ตกแต่ง CSS
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

# หยุดการทำงานถ้าไม่มีข้อมูล
if df.empty:
    st.warning("⏳ รอการเชื่อมต่อข้อมูล หรือยังไม่มีข้อมูลในแบบฟอร์ม...")
    st.stop()

# --- Sidebar: เมนูและตัวกรอง ---
st.sidebar.image("https://img.icons8.com/clouds/200/experimental-test-tube-clouds.png", width=100)
st.sidebar.title("🔬 ตัวกรองและรายละเอียด")

st.sidebar.subheader("🔍 กรองข้อมูล Dashboard")

# กรองข้อมูล
dept_col = 'คณะ/หน่วยงาน'
type_col = 'ประเภทผู้ขอใช้บริการเครื่องมือวิทยาศาสตร์ ' # อาจจะมี space ตามหลังในบางฟอร์ม

# หาชื่อคอลัมน์ประเภทผู้ใช้งานที่ถูกต้องจากข้อมูลจริง
actual_type_col = [col for col in df.columns if 'ประเภทผู้ขอใช้บริการ' in col]
type_col = actual_type_col[0] if actual_type_col else None

if dept_col in df.columns and type_col:
    filter_dept = st.sidebar.multiselect(
        "เลือกคณะ/หน่วยงาน",
        options=df[dept_col].dropna().unique(),
        default=df[dept_col].dropna().unique()
    )

    filter_type = st.sidebar.multiselect(
        "เลือกประเภทผู้ขอใช้",
        options=df[type_col].dropna().unique(),
        default=df[type_col].dropna().unique()
    )

    filtered_df = df[
        (df[dept_col].isin(filter_dept)) &
        (df[type_col].isin(filter_type))
    ]
else:
    filtered_df = df.copy()

st.sidebar.markdown("---")

# รายละเอียดผู้ใช้
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

        st.sidebar.markdown(f"**Email:** {person_data.get('Email Address', '-')}")
        st.sidebar.markdown(f"**ชื่อ-สกุล:** {person_data.get('คำนำหน้าชื่อ', '')} {person_data.get('ชื่อ-สกุล', '')}")
        st.sidebar.markdown(f"**ประเภท:** {person_data.get(type_col, '-') if type_col else '-'}")
        st.sidebar.markdown(f"**เบอร์โทรศัพท์:** {person_data.get('เบอร์โทรศัพท์เพื่อติดต่อ', '-')}")
        st.sidebar.markdown(f"**หน่วยงาน:** {person_data.get('คณะ/หน่วยงาน', '-')}")

# --- Main Dashboard Area ---
st.title("🧪 Dashboard สถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown("🟢 ระบบเชื่อมต่อข้อมูล Real-time จาก Google Sheets แล้ว")

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

# กราฟ
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📊 สัดส่วนประเภทผู้ขอใช้บริการ")
    if not filtered_df.empty and type_col:
        fig_pie = px.pie(filtered_df, names=type_col, hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("🏢 จำนวนการขอใช้แยกตามหน่วยงาน")
    if not filtered_df.empty and 'คณะ/หน่วยงาน' in filtered_df.columns:
        dept_counts = filtered_df['คณะ/หน่วยงาน'].value_counts().reset_index()
        dept_counts.columns = ['หน่วยงาน', 'จำนวนครั้ง']
        fig_bar = px.bar(dept_counts, x='หน่วยงาน', y='จำนวนครั้ง',
                         color='จำนวนครั้ง', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)

# ตารางข้อมูล
st.subheader("📋 ตารางข้อมูลรวม (Data Table)")
if not filtered_df.empty:
    display_cols = ['Timestamp', 'ชื่อ-สกุล', type_col, 'คณะ/หน่วยงาน', 'เรื่อง']
    valid_cols = [c for c in display_cols if c and c in filtered_df.columns]
    
    st.dataframe(filtered_df[valid_cols], use_container_width=True, height=400)
