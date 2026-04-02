import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide"
)

# ลิงก์ Google Sheets (ID ของคุณ)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้: {e}")
        return pd.DataFrame()

    # --- 🔒 ส่วนปกปิดข้อมูลส่วนบุคคล (PDPA Masking) ---
    
    # 1. ปกปิด ชื่อ-สกุล
    if 'ชื่อ-สกุล' in df.columns:
        def mask_name(name):
            name = str(name).strip()
            if not name or name.lower() == 'nan': return "-"
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1][0]}***"
            return name[0] + "***"
        df['ชื่อ-สกุล'] = df['ชื่อ-สกุล'].apply(mask_name)

    # 2. ปกปิดเบอร์โทรศัพท์ (08X-XXX-XXXX)
    if 'เบอร์โทรศัพท์เพื่อติดต่อ' in df.columns:
        def mask_phone(phone):
            try:
                p = str(phone).strip()
                if p.lower() == 'nan' or not p: return "-"
                if p.endswith('.0'): p = p[:-2]
                if len(p) >= 9:
                    return f"{p[:3]}-XXX-{p[-4:]}"
                return "-"
            except: return "-"
        df['เบอร์โทรศัพท์เพื่อติดต่อ'] = df['เบอร์โทรศัพท์เพื่อติดต่อ'].apply(mask_phone)

    # 3. ปกปิด Email (a***@domain.com)
    if 'Email Address' in df.columns:
        def mask_email(email):
            email = str(email)
            if '@' in email:
                parts = email.split('@')
                return f"{parts[0][0]}***@{parts[1]}"
            return "-"
        df['Email Address'] = df['Email Address'].apply(mask_email)

    return df

df = load_data()

# ค้นหาคอลัมน์ประเภทผู้ใช้ (เนื่องจากชื่ออาจจะยาว)
actual_type_col = [col for col in df.columns if 'ประเภทผู้ขอใช้บริการ' in col]
type_col = actual_type_col[0] if actual_type_col else None

if df.empty:
    st.warning("⏳ กำลังรอข้อมูลจาก Google Sheets...")
    st.stop()

# --- ส่วนแสดงผล Dashboard ---
st.title("🧪 Dashboard สถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown("🟢 อัปเดตข้อมูลอัตโนมัติพร้อมปกปิดข้อมูลส่วนบุคคล")

# 1. แถวสถิติภาพรวม
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📝 จำนวนคำขอทั้งหมด", f"{len(df)} รายการ")
with col2:
    if 'สถานะ' in df.columns:
        pending = len(df[df['สถานะ'] != 'อนุมัติแล้ว'])
        st.metric("⏳ รายการที่รอจัดการ", f"{pending} รายการ")
with col3:
    if 'การคืน' in df.columns:
        returned = len(df[df['การคืน'] == 'คืนเรียบร้อย'])
        st.metric("✅ คืนอุปกรณ์แล้ว", f"{returned} รายการ")

st.markdown("---")

# 2. ตารางสรุปสัดส่วน (Summary Tables)
st.subheader("📊 ตารางสรุปสัดส่วนข้อมูล")
t_col1, t_col2 = st.columns(2)

with t_col1:
    if type_col:
        st.write(f"**สัดส่วนตาม{type_col}**")
        type_summary = df[type_col].value_counts().reset_index()
        type_summary.columns = [type_col, 'จำนวน (ราย)']
        type_summary['สัดส่วน (%)'] = (type_summary['จำนวน (ราย)'] / len(df) * 100).round(2)
        st.table(type_summary)

with t_col2:
    if 'คณะ/หน่วยงาน' in df.columns:
        st.write("**สัดส่วนตามคณะ/หน่วยงาน**")
        dept_summary = df['คณะ/หน่วยงาน'].value_counts().reset_index()
        dept_summary.columns = ['คณะ/หน่วยงาน', 'จำนวน (ราย)']
        dept_summary['สัดส่วน (%)'] = (dept_summary['จำนวน (ราย)'] / len(df) * 100).round(2)
        st.table(dept_summary)

st.markdown("---")

# 3. กราฟวงกลม
st.subheader("📈 กราฟสรุปภาพรวม")
g_col1, g_col2 = st.columns(2)
with g_col1:
    if 'สถานะ' in df.columns:
        fig_status = px.pie(df, names='สถานะ', title='สถานะการอนุมัติ', hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)
with g_col2:
    if 'การคืน' in df.columns:
        fig_return = px.pie(df, names='การคืน', title='สถานะการคืนอุปกรณ์', hole=0.4,
                          color_discrete_sequence=['#2ecc71', '#e74c3c'])
        st.plotly_chart(fig_return, use_container_width=True)

st.markdown("---")

# 4. ตารางรายละเอียดผู้ขอใช้บริการ (ปกปิดข้อมูล)
st.subheader("📋 รายละเอียดผู้ขอใช้บริการ (Data Masking)")
# กำหนดคอลัมน์ที่จะแสดง รวมถึงข้อมูลส่วนตัวที่ถูกเซ็นเซอร์แล้ว
display_cols = ['Timestamp', 'ชื่อ-สกุล', 'Email Address', 'เบอร์โทรศัพท์เพื่อติดต่อ', 'คณะ/หน่วยงาน', 'เรื่อง', 'สถานะ', 'การคืน']
valid_cols = [c for c in display_cols if c in df.columns]

st.dataframe(df[valid_cols], use_container_width=True, height=500)
