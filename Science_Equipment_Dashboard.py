import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบจองเครื่องมือ", layout="wide")
st.title("🔬 ระบบจองเครื่องมือวิทยาศาสตร์")

try:
    # 1. โหลดข้อมูล (อ่านไฟล์ CSV)
    # ใช้ encoding='utf-8' หรือ 'cp1252' ขึ้นอยู่กับที่มาของไฟล์ ถ้า error ให้ลองเปลี่ยน
    try:
        df = pd.read_csv("data.csv")
    except:
        # กรณีอ่านภาษาไทยแล้ว error ให้ลองใช้ encoding อื่น
        df = pd.read_csv("data.csv", encoding='cp874')

    # --- Clean Data ---
    # เปลี่ยนชื่อคอลัมน์แรก (Timestamp) เป็น 'วันเวลา'
    # เช็คว่าคอลัมน์แรกชื่อ Timestamp หรือไม่ (Google Forms มักเป็นคำนี้)
    if 'Timestamp' in df.columns:
        df.rename(columns={'Timestamp': 'วันเวลา'}, inplace=True)
    elif df.columns[0] != 'วันเวลา':
         df.rename(columns={df.columns[0]: 'วันเวลา'}, inplace=True)

    df['วันเวลา'] = pd.to_datetime(df['วันเวลา'], errors='coerce')

    # --- Sidebar ---
    st.sidebar.header("🔍 ตัวเลือกการค้นหา")
    
    # กรองช่วงเวลา
    min_date = df['วันเวลา'].min().date()
    max_date = df['วันเวลา'].max().date()
    
    date_range = st.sidebar.date_input(
        "เลือกช่วงเวลา:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # กรองชื่อ
    if 'ชื่อ-สกุล' in df.columns:
        all_names = df['ชื่อ-สกุล'].unique()
        selected_name = st.sidebar.multiselect("เลือกชื่อผู้จอง:", all_names, default=all_names)
    else:
        st.error("ไม่พบคอลัมน์ 'ชื่อ-สกุล' ในไฟล์ข้อมูล")
        st.stop()
    
    # Logic การกรอง
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_show = df[
            (df['ชื่อ-สกุล'].isin(selected_name)) &
            (df['วันเวลา'].dt.date >= start_date) &
            (df['วันเวลา'].dt.date <= end_date)
        ]
    else:
        df_show = df[df['ชื่อ-สกุล'].isin(selected_name)]

    # --- Main Dashboard ---
    tab1, tab2 = st.tabs(["📊 ภาพรวมสถิติ", "📋 ข้อมูลดิบ & ดาวน์โหลด"])

    with tab1: 
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("📝 รายการจอง", f"{len(df_show)} รายการ")
        c2.metric("👥 ผู้ใช้งาน", f"{df_show['ชื่อ-สกุล'].nunique()} คน")
        if 'คณะ/หน่วยงาน' in df.columns:
            c3.metric("🏢 หน่วยงาน", f"{df_show['คณะ/หน่วยงาน'].nunique()} แห่ง")
        
        st.divider()

        # Charts
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("🏆 Top 5 ผู้ใช้งานสูงสุด")
            if not df_show.empty:
                top_users = df_show['ชื่อ-สกุล'].value_counts().nlargest(5).reset_index()
                top_users.columns = ['ชื่อ-สกุล', 'จำนวน']
                fig = px.bar(top_users, x='จำนวน', y='ชื่อ-สกุล', orientation='h', text='จำนวน')
                st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            st.subheader("🍰 สัดส่วนตามคณะ")
            if 'คณะ/หน่วยงาน' in df.columns and not df_show.empty:
                pie_data = df_show['คณะ/หน่วยงาน'].value_counts().reset_index()
                pie_data.columns = ['คณะ', 'จำนวน']
                fig = px.pie(pie_data, values='จำนวน', names='คณะ', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 แนวโน้มตามช่วงเวลา")
        if not df_show.empty:
            line_data = df_show['วันเวลา'].dt.date.value_counts().reset_index()
            line_data.columns = ['วันที่', 'จำนวน']
            line_data = line_data.sort_values('วันที่')
            st.plotly_chart(px.line(line_data, x='วันที่', y='จำนวน', markers=True), use_container_width=True)

    with tab2:
        st.subheader("ตารางข้อมูลละเอียด")
        # แปลงเป็น CSV สำหรับดาวน์โหลด
        csv = df_show.to_csv(index=False).encode('utf-8-sig')
        st.download_button("⬇️ ดาวน์โหลด CSV", csv, "report.csv", "text/csv")
        st.dataframe(df_show, use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")