import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Science Equipment Dashboard",
    page_icon="🧪",
    layout="wide"
)

# ลิงก์ Google Sheets ของคุณ
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/export?format=csv&gid=1562070767"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้: {e}")
        return pd.DataFrame()

    # --- 🕒 แปลงคอลัมน์ Timestamp ให้เป็นข้อมูลวันที่และเวลาจริงๆ ---
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')

    # --- 🔒 ส่วนปกปิดข้อมูลส่วนบุคคล (PDPA Masking) ---
    
    # ปกปิด ชื่อ-สกุล
    if 'ชื่อ-สกุล' in df.columns:
        def mask_name(name):
            name = str(name).strip()
            if not name or name.lower() == 'nan': return "-"
            parts = name.split()
            if len(parts) >= 2: return f"{parts[0]} {parts[1][0]}***"
            return name[0] + "***"
        df['ชื่อ-สกุล'] = df['ชื่อ-สกุล'].apply(mask_name)

    # ปกปิดเบอร์โทรศัพท์
    if 'เบอร์โทรศัพท์เพื่อติดต่อ' in df.columns:
        def mask_phone(phone):
            try:
                p = str(phone).strip()
                if p.lower() == 'nan' or not p: return "-"
                if p.endswith('.0'): p = p[:-2]
                if len(p) >= 9: return f"{p[:3]}-XXX-{p[-4:]}"
                return "-"
            except: return "-"
        df['เบอร์โทรศัพท์เพื่อติดต่อ'] = df['เบอร์โทรศัพท์เพื่อติดต่อ'].apply(mask_phone)

    # ปกปิด Email
    email_cols = [c for c in df.columns if 'email' in c.lower() or 'อีเมล' in c]
    if email_cols:
        def mask_email(email):
            email = str(email)
            if '@' in email:
                parts = email.split('@')
                return f"{parts[0][0]}***@{parts[1]}"
            return "-"
        df[email_cols[0]] = df[email_cols[0]].apply(mask_email)

    return df

df = load_data()

if df.empty:
    st.warning("⏳ กำลังรอข้อมูลจาก Google Sheets...")
    st.stop()

# --- 🔍 ค้นหาชื่อคอลัมน์อัตโนมัติ ---
status_col = 'สถานะ' if 'สถานะ' in df.columns else None
return_col = 'การคืน' if 'การคืน' in df.columns else None

type_cols = [c for c in df.columns if 'ประเภท' in c]
user_type_col = type_cols[0] if type_cols else None

dept_cols = [c for c in df.columns if 'คณะ' in c or 'หน่วยงาน' in c]
dept_col = dept_cols[0] if dept_cols else None

# --- 🧹 จัดการปัญหาค่าว่าง (Null) ก่อนนำไปแสดงผล ---
if user_type_col: df[user_type_col] = df[user_type_col].fillna('ไม่ระบุ')
if dept_col: df[dept_col] = df[dept_col].fillna('ไม่ระบุ')
if status_col: df[status_col] = df[status_col].fillna('ยังไม่ระบุสถานะ')
if return_col: df[return_col] = df[return_col].fillna('ยังไม่ระบุข้อมูล')


# --- ส่วนแสดงผล Dashboard ---
st.title("🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown(f"📊 ข้อมูลล่าสุด ณ วันที่ {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

# 1. แถวสถิติสรุป
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("📝 คำขอทั้งหมด", f"{len(df)} รายการ")
with m2:
    if status_col:
        pending = len(df[df[status_col] != 'อนุมัติแล้ว'])
        st.metric("⏳ รออนุมัติ", f"{pending} รายการ")
    else:
        st.metric("⏳ รออนุมัติ", "ไม่พบข้อมูล")
with m3:
    if return_col:
        returned = len(df[df[return_col] == 'คืนเรียบร้อย'])
        st.metric("✅ คืนของแล้ว", f"{returned} รายการ")
    else:
        st.metric("✅ คืนของแล้ว", "ไม่พบข้อมูล")
with m4:
    if user_type_col:
        st.metric("👥 กลุ่มผู้ใช้", f"{df[user_type_col].nunique()} ประเภท")
    else:
        st.metric("👥 กลุ่มผู้ใช้", "ไม่พบข้อมูล")

st.markdown("---")

# 2. ส่วนกราฟสัดส่วน
st.subheader("🎯 สรุปสัดส่วนข้อมูลสำคัญ")
c1, c2 = st.columns(2)

with c1:
    if user_type_col:
        fig_user = px.pie(df, names=user_type_col, title='สัดส่วนประเภทผู้ใช้งาน', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_user, use_container_width=True)

with c2:
    if dept_col:
        fig_dept = px.pie(df, names=dept_col, title='สัดส่วนตามคณะ/หน่วยงาน', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_dept, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    if status_col:
        fig_status = px.pie(df, names=status_col, title='สถานะการอนุมัติ', hole=0.4,
                          color_discrete_sequence=['#FFCC00', '#2ecc71', '#e74c3c', '#95a5a6'])
        st.plotly_chart(fig_status, use_container_width=True)
with c4:
    if return_col:
        fig_return = px.pie(df, names=return_col, title='สถานะการคืนอุปกรณ์', hole=0.4,
                          color_discrete_sequence=['#3498db', '#95a5a6', '#e67e22'])
        st.plotly_chart(fig_return, use_container_width=True)

st.markdown("---")

# 3. ตารางรายละเอียดผู้ขอใช้บริการ
st.subheader("📋 รายละเอียดผู้ขอใช้บริการ (เรียงลำดับก่อน-หลัง)")

# ประกาศหาตัวแปร email_cols อีกครั้ง เพื่อให้พร้อมใช้งานสำหรับตารางด้านล่าง
email_cols_for_display = [c for c in df.columns if 'email' in c.lower() or 'อีเมล' in c]
email_display = email_cols_for_display[0] if email_cols_for_display else 'Email Address'

display_cols = [
    'Timestamp', 
    'ชื่อ-สกุล', 
    user_type_col, 
    dept_col, 
    'เรื่อง', 
    'เบอร์โทรศัพท์เพื่อติดต่อ', 
    email_display,
    status_col, 
    return_col
]

valid_display = [c for c in display_cols if c and c in df.columns]

# เตรียมข้อมูลเพื่อนำมาแสดงผล
df_display = df[valid_display].copy()

# สั่งเรียงลำดับตาม Timestamp โดยให้คนที่มาก่อน (ข้อมูลเก่ากว่า) อยู่บนสุด (ascending=True)
if 'Timestamp' in df_display.columns:
    df_display = df_display.sort_values(by='Timestamp', ascending=True)
    # จัดรูปแบบวันที่ให้ดูสวยงามอ่านง่ายขึ้นก่อนแสดงผล
    df_display['Timestamp'] = df_display['Timestamp'].dt.strftime('%d/%m/%Y %H:%M')

st.dataframe(
    df_display, 
    use_container_width=True,
    hide_index=True
)
