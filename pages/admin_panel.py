import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import datetime

# পেজ সেটআপ
st.set_page_config(page_title="Admin Panel - Broadband Survey", layout="wide")

# গুগল শিট কানেকশন
conn = st.connection("gsheets", type=GSheetsConnection)

# হেডার ও হোমে ফেরার বাটন
c1, c2 = st.columns([5, 1])
with c1:
    st.title("🔐 Admin Dashboard")
with c2:
    if st.button("🏠 Back to Form"):
        st.switch_page("newbroadband_survey.py") # আপনার মূল ফাইলের নাম চেক করে দিন

# পাসওয়ার্ড চেক
pwd = st.sidebar.text_input('Password', type='password')

if pwd == 'Bccadmin2025':
    st.sidebar.success('Authenticated')
    
    try:
        # ডাটা রিড করা
        df_admin = conn.read(ttl="0") # লাইভ ডাটার জন্য ০ দেওয়া ভালো
        
        if df_admin is None or df_admin.empty:
            st.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
        else:
            st.header("🔍 Data Search & Analytics")
            
            # ডাটা ক্লিনআপ
            filtered_df = df_admin.copy()
            filtered_df['মোট গ্রাম'] = pd.to_numeric(filtered_df['মোট গ্রাম'], errors='coerce').fillna(0)
            filtered_df['আওতাভুক্ত গ্রাম'] = pd.to_numeric(filtered_df['আওতাভুক্ত গ্রাম'], errors='coerce').fillna(0)

            # ১. ফিল্টারিং লজিক
            f1, f2 = st.columns(2)
            with f1: 
                div_list = ["All"] + sorted(df_admin['বিভাগ'].unique().astype(str).tolist())
                div_search = st.selectbox("বিভাগ ফিল্টার", div_list)
            
            if div_search != "All": 
                filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]

            # ২. ম্যাট্রিক্স ক্যালকুলেশন
            m1, m2, m3 = st.columns(3)
            total_vills = int(filtered_df['মোট গ্রাম'].sum())
            covered_vills = int(filtered_df['আওতাভুক্ত গ্রাম'].sum())
            uncovered_vills = max(0, total_vills - covered_vills)
            
            m1.metric("Submissions", len(filtered_df))
            m2.metric("Total Villages", total_vills)
            m3.metric("Covered Villages", covered_vills)

            # ৩. চার্ট সেকশন
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            with g1:
                st.write("**ইন্টারনেট কভারেজ অনুপাত (Coverage Ratio)**")
                if total_vills > 0:
                    pie_data = pd.DataFrame({
                        "Category": ["আওতাভুক্ত (Covered)", "বাকি (Uncovered)"],
                        "Count": [covered_vills, uncovered_vills]
                    })
                    fig_pie = px.pie(pie_data, values='Count', names='Category', hole=0.4,
                                   color_discrete_map={"আওতাভুক্ত (Covered)": "#006A4E", "বাকি (Uncovered)": "#F42A41"})
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with g2:
                st.write("**Submissions by Division**")
                div_counts = filtered_df['বিভাগ'].value_counts().reset_index()
                div_counts.columns = ['Division', 'Count']
                st.plotly_chart(px.bar(div_counts, x='Division', y='Count', text_auto=True, 
                                     color_discrete_sequence=['#006A4E']), use_container_width=True)

            # ৪. টেবিল প্রদর্শন
            st.subheader("📋 Data Records")
            st.dataframe(filtered_df, use_container_width=True)

            # ৫. ডিলিট লজিক
            st.markdown("---")
            with st.expander("🗑️ Delete Data Entry"):
                delete_index = st.number_input("Enter Row Index to delete:", min_value=0, max_value=max(0, len(df_admin)-1), step=1)
                if st.button("Confirm Delete", type="primary"):
                    df_admin = df_admin.drop(df_admin.index[delete_index])
                    conn.update(data=df_admin)
                    st.cache_data.clear()
                    st.success(f"Row {delete_index} deleted successfully!")
                    import time
                    time.sleep(1)
                    st.rerun()

    except Exception as e:
        st.error(f"Error loading admin data: {e}")

elif pwd != "":
    st.sidebar.error('Incorrect Password')
else:
    st.info("অ্যাডমিন প্যানেল দেখার জন্য বাম পাশের সাইডবারে পাসওয়ার্ড দিন।")
