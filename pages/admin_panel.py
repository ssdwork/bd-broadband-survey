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
        st.switch_page("newbroadband_survey.py") 

# পাসওয়ার্ড চেক
pwd = st.sidebar.text_input('Password', type='password')

if pwd == 'Bccadmin2025':
    st.sidebar.success('Authenticated')
    
    try:
        # ডাটা রিড করা
        df_admin = conn.read(ttl="0")
        
        if df_admin is None or df_admin.empty:
            st.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
        else:
            # ১. ফিল্টারিং লজিক 
            st.header("🔍 Data Search & Analytics")
            filtered_df = df_admin.copy()
            filtered_df['মোট গ্রাম'] = pd.to_numeric(filtered_df['মোট গ্রাম'], errors='coerce').fillna(0)
            filtered_df['আওতাভুক্ত গ্রাম'] = pd.to_numeric(filtered_df['আওতাভুক্ত গ্রাম'], errors='coerce').fillna(0)
            filtered_df['ISP মোট সংখ্যা'] = pd.to_numeric(filtered_df['ISP মোট সংখ্যা'], errors='coerce').fillna(0)

            f1, f2 = st.columns(2)
            with f1: 
                div_list = ["All"] + sorted(df_admin['বিভাগ'].unique().astype(str).tolist())
                div_search = st.selectbox("বিভাগ ফিল্টার", div_list)
            
            if div_search != "All": 
                filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]

            # ২. অ্যাডভান্সড ম্যাট্রিক্স ক্যালকুলেশন
            st.markdown("---")
            st.markdown("### 📊 সামগ্রিক পরিসংখ্যান (National Progress)")
            
            TOTAL_UPAZILAS = 495
            TOTAL_UNIONS = 4554
            
            submitted_upazilas = df_admin['উপজেলা'].nunique()
            remaining_upazilas = max(0, TOTAL_UPAZILAS - submitted_upazilas)
            
            submitted_unions = df_admin['ইউনিয়ন'].nunique()
            remaining_unions = max(0, TOTAL_UNIONS - submitted_unions)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("মোট সাবমিশন", len(df_admin))
            m2.metric("উপজেলা কভারেজ", f"{submitted_upazilas}/{TOTAL_UPAZILAS}", f"{remaining_upazilas} বাকি")
            m3.metric("ইউনিয়ন কভারেজ", f"{submitted_unions}/{TOTAL_UNIONS}", f"{remaining_unions} বাকি")
            m4.metric("গ্রাম (ফিল্টার্ড)", int(filtered_df['মোট গ্রাম'].sum()))

            # ৩. প্রগ্রেস চার্ট সেকশন 
            g_progress1, g_progress2 = st.columns(2)
            
            with g_progress1:
                st.write("**উপজেলা কভারেজ প্রগ্রেস (%)**")
                fig_upz = px.pie(names=["জমা হয়েছে", "বাকি আছে"], 
                                values=[submitted_upazilas, remaining_upazilas],
                                hole=0.6, color_discrete_sequence=["#00D487", "#222222"])
                fig_upz.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
                fig_upz.add_annotation(text=f"{int((submitted_upazilas/TOTAL_UPAZILAS)*100)}%", showarrow=False, font_size=20)
                st.plotly_chart(fig_upz, use_container_width=True)

            with g_progress2:
                st.write("**ইউনিয়ন কভারেজ প্রগ্রেস (%)**")
                fig_uni = px.pie(names=["জমা হয়েছে", "বাকি আছে"], 
                                values=[submitted_unions, remaining_unions],
                                hole=0.6, color_discrete_sequence=["#006A4E", "#222222"])
                fig_uni.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
                fig_uni.add_annotation(text=f"{int((submitted_unions/TOTAL_UNIONS)*100)}%", showarrow=False, font_size=20)
                st.plotly_chart(fig_uni, use_container_width=True)

            # ৪. চার্টগুলো 
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            with g1:
                st.write("**ইন্টারনেট কভারেজ অনুপাত (ফিল্টার অনুযায়ী)**")
                total_v = filtered_df['মোট গ্রাম'].sum()
                covered_v = filtered_df['আওতাভুক্ত গ্রাম'].sum()
                uncovered_v = max(0, total_v - covered_v)
                
                if total_v > 0:
                    pie_data = pd.DataFrame({"Category": ["আওতাভুক্ত", "বাকি"], "Count": [covered_v, uncovered_v]})
                    fig_pie = px.pie(pie_data, values='Count', names='Category', hole=0.4,
                                   color_discrete_map={"আওতাভুক্ত": "#006A4E", "বাকি": "#F42A41"})
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with g2:
                st.write("**বিভাগ ভিত্তিক সাবমিশন সংখ্যা**")
                div_counts = filtered_df['বিভাগ'].value_counts().reset_index()
                div_counts.columns = ['Division', 'Count']
                st.plotly_chart(px.bar(div_counts, x='Division', y='Count', text_auto=True, 
                                     color_discrete_sequence=['#00D487']), use_container_width=True)
            
            # ISP Visualization Section
            st.markdown("---")
            total_isps = int(filtered_df['ISP মোট সংখ্যা'].sum())
            st.info(f"**সর্বমোট ISP সংখ্যা:** {total_isps}")
            st.write("**বিভাগ অনুযায়ী মোট ISP সংখ্যা (Total ISP Count by Division)**")
            isp_counts = filtered_df.groupby('বিভাগ')['ISP মোট সংখ্যা'].sum().reset_index()
            fig_isp = px.bar(isp_counts, x='বিভাগ', y='ISP মোট সংখ্যা', text_auto=True,
                             color_discrete_sequence=['#00D487'])
            st.plotly_chart(fig_isp, use_container_width=True)

            # ৫. টেবিল প্রদর্শন 
            st.subheader("📋 Data Records")
            st.dataframe(filtered_df, use_container_width=True)

            # ৬. ডিলিট লজিক 
            st.markdown("---")
            with st.expander("🗑️ Delete Data Entry"):
                delete_index = st.number_input("Enter Row Index to delete:", min_value=0, max_value=max(0, len(df_admin)-1), step=1)
                if st.button("Confirm Delete", type="primary"):
                    df_admin = df_admin.drop(df_admin.index[delete_index])
                    conn.update(data=df_admin)
                    st.cache_data.clear()
                    st.success(f"Row {delete_index} deleted successfully!")
                    st.rerun()

    except Exception as e:
        st.error(f"Error loading admin data: {e}")

elif pwd != "":
    st.sidebar.error('Incorrect Password')
else:
    st.info("অ্যাডমিন প্যানেল দেখার জন্য বাম পাশের সাইডবারে পাসওয়ার্ড দিন।")
