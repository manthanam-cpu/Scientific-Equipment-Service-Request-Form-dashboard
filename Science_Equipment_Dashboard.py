import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ระบบจองเครื่องมือ", layout="wide")

st.title("🔬 ระบบจองเครื่องมือวิทยาศาสตร์")

try:
    # 1. โหลดข้อมูล
    df = pd.read_excel("data.xlsx")
    
    # Clean Data
    first_col = df.columns[0]
    df.rename(columns={first_col: 'วันเวลา'}, inplace=True)
    df['วันเวลา'] = pd.to_datetime(df['วันเวลา'], errors='coerce')

    # --- Sidebar ---
    st.sidebar.header("🔍 ตัวเลือกการค้นหา")
    
    # เลือกช่วงเวลา
    min_date = df['วันเวลา'].min().date()
    max_date = df['วันเวลา'].max().date()
    
    date_range = st.sidebar.date_input(
        "เลือกช่วงเวลา:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # เลือกชื่อ
    all_names = df['ชื่อ-สกุล'].unique()
    selected_name = st.sidebar.multiselect("เลือกชื่อผู้จอง:", all_names, default=all_names)
    
    # กรองข้อมูล
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
        col1, col2, col3 = st.columns(3)
        col1.metric("📝 จำนวนรายการจอง", f"{len(df_show)} รายการ")
        col2.metric("👥 จำนวนผู้ใช้งาน", f"{df_show['ชื่อ-สกุล'].nunique()} คน")
        col3.metric("🏢 คณะ/หน่วยงาน", f"{df_show['คณะ/หน่วยงาน'].nunique()} หน่วยงาน")
        
        st.divider()

        # Row 1: Bar & Pie Chart
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏆 Top 5 ผู้ใช้งานสูงสุด")
            if not df_show.empty:
                top_users = df_show['ชื่อ-สกุล'].value_counts().nlargest(5).reset_index()
                top_users.columns = ['ชื่อ-สกุล', 'จำนวนการจอง']
                fig_bar = px.bar(top_users, x='จำนวนการจอง', y='ชื่อ-สกุล', orientation='h', text='จำนวนการจอง', color='จำนวนการจอง', color_continuous_scale='Blues')
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with c2:
            st.subheader("🍰 สัดส่วนตามคณะ")
            if not df_show.empty:
                faculty_counts = df_show['คณะ/หน่วยงาน'].value_counts().reset_index()
                faculty_counts.columns = ['คณะ/หน่วยงาน', 'จำนวน']
                fig_pie = px.pie(faculty_counts, values='จำนวน', names='คณะ/หน่วยงาน', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # Row 2: Line Chart (Trend) **ของใหม่**
        st.subheader("📈 แนวโน้มการใช้งานตามช่วงเวลา")
        if not df_show.empty:
            # นับจำนวนการจองต่อวัน
            daily_data = df_show['วันเวลา'].dt.date.value_counts().reset_index()
            daily_data.columns = ['วันที่', 'จำนวนการจอง']
            daily_data = daily_data.sort_values('วันที่') # เรียงตามวัน
            
            fig_line = px.line(daily_data, x='วันที่', y='จำนวนการจอง', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        st.subheader("รายละเอียดรายการจองทั้งหมด")
        # ปุ่มดาวน์โหลด **ของใหม่**
        csv = df_show.to_csv(index=False).encode('utf-8-sig') # utf-8-sig เพื่อรองรับภาษาไทยใน Excel
        st.download_button(
            label="⬇️ ดาวน์โหลดข้อมูลเป็นไฟล์ CSV",
            data=csv,
            file_name='report_booking.csv',
            mime='text/csv',
        )
        st.dataframe(df_show, use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")