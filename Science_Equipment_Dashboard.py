import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide"
)

# ลิงก์ Google Sheets (ID ที่ถูกต้องของคุณ)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้: {e}")
        return pd.DataFrame()

    # --- 🔒 ส่วนปกปิดข้อมูลส่วนบุคคล (PDPA Masking) ---
    
    # 1. ปกปิด ชื่อ-สกุล (เช่น สมชาย เข็มกลัด -> สมชาย ข***)
    if 'ชื่อ-สกุล' in df.columns:
        def mask_name(name):
            name = str(name).strip()
            if not name or name.lower() == 'nan': return "-"
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1][0]}***" # แสดงชื่อจริง และตัวแรกของนามสกุล
            return name[0] + "***"
        df['ชื่อ-สกุล'] = df['ชื่อ-สกุล'].apply(mask_name)

    # 2. ปกปิดเบอร์โทรศัพท์ (081-XXX-5678)
    if 'เบอร์โทรศัพท์เพื่อติดต่อ' in df.columns:
        df['เบอร์โทรศัพท์เพื่อติดต่อ'] = df['เบอร์โทรศัพท์เพื่อติดต่อ'].astype(str).apply(
            lambda x: x[:3] + "-XXX-" + x[-4:] if len(x) >= 9 else "-"
        )

    # 3. ปกปิด Email (p***@g.swu.ac.th)
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

if df.empty:
    st.warning("⏳ กำลังรอข้อมูลจาก Google Sheets...")
    st.stop()

# --- ส่วนแสดงผล Dashboard ---
st.title("🧪 Dashboard สถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown("🟢 ข้อมูลอัปเดตแบบ Real-time (ปกปิดข้อมูลส่วนบุคคลตาม PDPA)")

# 1. แถวสถิติภาพรวม (Metrics)
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

# 2. ส่วนกราฟวงกลมสรุปสถานะ (Pie Charts)
st.subheader("📊 สรุปสถานะการดำเนินงาน")
c_chart1, c_chart2 = st.columns(2)

with c_chart1:
    if 'สถานะ' in df.columns:
        fig_status = px.pie(df, names='สถานะ', title='สัดส่วนการอนุมัติ', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_status, use_container_width=True)

with c_chart2:
    if 'การคืน' in df.columns:
        fig_return = px.pie(df, names='การคืน', title='สัดส่วนการคืนอุปกรณ์', hole=0.4,
                          color_discrete_sequence=['#2ecc71', '#e74c3c'])
        st.plotly_chart(fig_return, use_container_width=True)

st.markdown("---")

# 3. ตารางข้อมูล (แสดงคอลัมน์ใหม่ 'สถานะ' และ 'การคืน' ด้วย)
st.subheader("📋 รายการข้อมูลล่าสุด")
# เลือกคอลัมน์ที่ต้องการโชว์ในตาราง (เพิ่ม สถานะ และ การคืน เข้าไปแล้ว)
display_cols = ['Timestamp', 'ชื่อ-สกุล', 'คณะ/หน่วยงาน', 'เรื่อง', 'สถานะ', 'การคืน']
# ตรวจสอบว่าคอลัมน์มีจริงในไฟล์ไหมก่อนแสดง
valid_cols = [c for c in display_cols if c in df.columns]

st.dataframe(df[valid_cols], use_container_width=True)
