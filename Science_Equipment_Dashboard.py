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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wzOqWDzLNiaU7sKj3PAJxHJD-dH0-PL1wv1r9kfCmv8/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อข้อมูลได้: {e}")
        return pd.DataFrame()

    # --- 🔒 ส่วนปกปิดข้อมูลส่วนบุคคล (PDPA Masking) ---
    
    # ปกปิด ชื่อ-สกุล (เช่น ปัญญา ไ***)
    if 'ชื่อ-สกุล' in df.columns:
        def mask_name(name):
            name = str(name).strip()
            if not name or name.lower() == 'nan': return "-"
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1][0]}***"
            return name[0] + "***"
        df['ชื่อ-สกุล'] = df['ชื่อ-สกุล'].apply(mask_name)

    # ปกปิดเบอร์โทรศัพท์ (081-XXX-5678)
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

    # ปกปิด Email (p***@g.swu.ac.th)
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
st.title("🧪 ระบบรายงานสถิติการขอใช้เครื่องมือวิทยาศาสตร์")
st.markdown(f"📊 ข้อมูลล่าสุด ณ วันที่ {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

# 1. แถวสถิติสรุป (Top Metrics)
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("📝 คำขอทั้งหมด", f"{len(df)} รายการ")
