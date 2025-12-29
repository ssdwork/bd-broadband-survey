import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import datetime
import json
import urllib.request

# -----------------------------------------------------------------------------
# 1. DATA LOADER FUNCTIONS (মাস্টার ডেটা লোড করার জন্য এই অংশটি )
# -----------------------------------------------------------------------------
NUHIL_RAW = {
    "divisions": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/divisions/divisions.json",
    "districts": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/districts/districts.json",
    "upazilas": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/upazilas/upazilas.json",
    "unions": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/unions/unions.json",
}

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

@st.cache_data
def get_all_locations():
    # মাস্টার ডেটা থেকে সব উপজেলা এবং ইউনিয়নের নাম নিয়ে আসা
    try:
        upz_raw = fetch_json(NUHIL_RAW['upazilas'])
        uni_raw = fetch_json(NUHIL_RAW['unions'])
        
        def extract_names(raw):
            names = []
            data = raw.get('data', []) if isinstance(raw, dict) else raw
            for item in data:
                name = item.get('bn_name') or item.get('name')
                if name: names.append(name)
            return names

        return extract_names(upz_raw), extract_names(uni_raw)
    except:
        return [], []

# মাস্টার লিস্ট লোড করা
ALL_UPAZILAS, ALL_UNIONS = get_all_locations()

# -----------------------------------------------------------------------------
# 2. POP-UP DIALOG FUNCTION
# -----------------------------------------------------------------------------
@st.dialog("বাকি থাকা তথ্যের তালিকা (Pending List)")
def show_pending_list(type, submitted_list):
    if type == "upazila":
        st.write("### 📍 যেসব উপজেলার তথ্য এখনো আসেনি:")
        # মাস্টার লিস্ট থেকে সাবমিটেড লিস্ট বাদ দেওয়া
        remaining = sorted(list(set(ALL_UPAZILAS) - set(submitted_list)))
        st.info(f"মোট বাকি: {len(remaining)} টি")
        st.dataframe(pd.DataFrame(remaining, columns=["উপজেলার নাম"]), use_container_width=True, hide_index=True)

    elif type == "union":
        st.write("### 🏛️ যেসব ইউনিয়নের তথ্য এখনো আসেনি:")
        remaining = sorted(list(set(ALL_UNIONS) - set(submitted_list)))
        st.info(f"মোট বাকি: {len(remaining)} টি")
        st.dataframe(pd.DataFrame(remaining, columns=["ইউনিয়নের নাম"]), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 3. MAIN APP LOGIC
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Admin Panel - Broadband Survey", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

c1, c2 = st.columns([5, 1])
with c1: st.title("🔐 Admin Dashboard")
with c2:
    if st.button("🏠 Back to Form"):
        st.switch_page("newbroadband_survey.py") #  মেইন ফাইলের নাম

pwd = st.sidebar.text_input('Password', type='password')

if pwd == 'Bccadmin2025':
    st.sidebar.success('Authenticated')
    
    try:
        df_admin = conn.read(ttl="0")
        
        if df_admin is None or df_admin.empty:
            st.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
        else:
            # ১. ফিল্টারিং লজিক 
            st.header("🔍 Data Search & Analytics")
            filtered_df = df_admin.copy()
            filtered_df['মোট গ্রাম'] = pd.to_numeric(filtered_df['মোট গ্রাম'], errors='coerce').fillna(0)
            filtered_df['আওতাভুক্ত গ্রাম'] = pd.to_numeric(filtered_df['আওতাভুক্ত গ্রাম'], errors='coerce').fillna(0)

            f1, f2 = st.columns(2)
            with f1: 
                div_list = ["All"] + sorted(df_admin['বিভাগ'].unique().astype(str).tolist())
                div_search = st.selectbox("বিভাগ ফিল্টার", div_list)
            
            if div_search != "All": 
                filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]

            # ২. অ্যাডভান্সড ম্যাট্রিক্স ক্যালকুলেশন (আপডেটেড)
            st.markdown("---")
            st.markdown("### 📊 সামগ্রিক পরিসংখ্যান (National Progress)")
            
            # মাস্টার ডেটা থেকে সংখ্যা নেওয়া (যদি ইন্টারনেট না থাকে তবে ডিফল্ট ভ্যালু)
            TOTAL_UPAZILAS_COUNT = len(ALL_UPAZILAS) if ALL_UPAZILAS else 495
            TOTAL_UNIONS_COUNT = len(ALL_UNIONS) if ALL_UNIONS else 4554
            
            submitted_upazilas_list = df_admin['উপজেলা'].unique()
            submitted_unions_list = df_admin['ইউনিয়ন'].unique()

            submitted_upazilas_count = len(submitted_upazilas_list)
            remaining_upazilas_count = max(0, TOTAL_UPAZILAS_COUNT - submitted_upazilas_count)
            
            submitted_unions_count = len(submitted_unions_list)
            remaining_unions_count = max(0, TOTAL_UNIONS_COUNT - submitted_unions_count)
            
            m1, m2, m3, m4 = st.columns(4)
            
            # Col 1
            m1.metric("মোট সাবমিশন", len(df_admin))
            
            # Col 2: Upazila with Button
            with m2:
                st.metric("উপজেলা কভারেজ", f"{submitted_upazilas_count}/{TOTAL_UPAZILAS_COUNT}", f"{remaining_upazilas_count} বাকি")
                if st.button("🔍 তালিকা দেখুন", key="btn_upz"):
                    show_pending_list("upazila", submitted_upazilas_list)

            # Col 3: Union with Button
            with m3:
                st.metric("ইউনিয়ন কভারেজ", f"{submitted_unions_count}/{TOTAL_UNIONS_COUNT}", f"{remaining_unions_count} বাকি")
                if st.button("🔍 তালিকা দেখুন", key="btn_uni"):
                    show_pending_list("union", submitted_unions_list)

            # Col 4
            m4.metric("গ্রাম (ফিল্টার্ড)", int(filtered_df['মোট গ্রাম'].sum()))

            # ৩. প্রগ্রেস চার্ট সেকশন 
            g_progress1, g_progress2 = st.columns(2)
            
            with g_progress1:
                st.write("**উপজেলা কভারেজ প্রগ্রেস (%)**")
                fig_upz = px.pie(names=["জমা হয়েছে", "বাকি আছে"], 
                                values=[submitted_upazilas_count, remaining_upazilas_count],
                                hole=0.6, color_discrete_sequence=["#00D487", "#222222"])
                fig_upz.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
                # Zero division error handle
                upz_pct = int((submitted_upazilas_count/TOTAL_UPAZILAS_COUNT)*100) if TOTAL_UPAZILAS_COUNT > 0 else 0
                fig_upz.add_annotation(text=f"{upz_pct}%", showarrow=False, font_size=20)
                st.plotly_chart(fig_upz, use_container_width=True)

            with g_progress2:
                st.write("**ইউনিয়ন কভারেজ প্রগ্রেস (%)**")
                fig_uni = px.pie(names=["জমা হয়েছে", "বাকি আছে"], 
                                values=[submitted_unions_count, remaining_unions_count],
                                hole=0.6, color_discrete_sequence=["#006A4E", "#222222"])
                fig_uni.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
                uni_pct = int((submitted_unions_count/TOTAL_UNIONS_COUNT)*100) if TOTAL_UNIONS_COUNT > 0 else 0
                fig_uni.add_annotation(text=f"{uni_pct}%", showarrow=False, font_size=20)
                st.plotly_chart(fig_uni, use_container_width=True)

            # ৪. চার্টগুলো 
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            with g1:
                st.write("**ইন্টারনেট কভারেজ অনুপাত (ফিল্টার অনুযায়ী)**")
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
