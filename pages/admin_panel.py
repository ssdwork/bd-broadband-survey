import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import datetime
import json
import urllib.request

# -----------------------------------------------------------------------------
# 1. DATA LOADER FUNCTIONS (মাস্টার ডেটা লোড করার উন্নত পদ্ধতি)
# -----------------------------------------------------------------------------
NUHIL_RAW = {
    "upazilas": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/upazilas/upazilas.json",
    "unions": "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/unions/unions.json",
}

@st.cache_data
def get_all_locations():
    try:
        def fetch_and_clean(url):
            with urllib.request.urlopen(url, timeout=30) as r:
                raw_data = json.loads(r.read().decode('utf-8'))
                items = raw_data.get('data', []) if isinstance(raw_data, dict) else raw_data
                # নামগুলো নিয়ে দুই পাশের স্পেস ক্লিন করা হচ্ছে
                return sorted(list(set([str(i.get('bn_name') or i.get('name')).strip() for i in items if i])))

        return fetch_and_clean(NUHIL_RAW['upazilas']), fetch_and_clean(NUHIL_RAW['unions'])
    except Exception as e:
        st.error(f"Error loading master list: {e}")
        return [], []

# মাস্টার লিস্ট লোড করা
ALL_UPAZILAS, ALL_UNIONS = get_all_locations()

# -----------------------------------------------------------------------------
# 2. POP-UP DIALOG FUNCTION (নিখুঁত তালিকা দেখানোর জন্য)
# -----------------------------------------------------------------------------
@st.dialog("বাকি থাকা তথ্যের তালিকা (Pending List)")
def show_pending_list(type, submitted_list):
    # জমা হওয়া লিস্ট ক্লিন করা
    submitted_set = set([str(s).strip() for s in submitted_list if s])
    
    if type == "upazila":
        st.write("### 📍 যেসব উপজেলার তথ্য এখনো আসেনি:")
        master_set = set(ALL_UPAZILAS)
        remaining = sorted(list(master_set - submitted_set))
        
        st.info(f"মোট উপজেলা বাকি: {len(remaining)} টি")
        if remaining:
            st.dataframe(pd.DataFrame(remaining, columns=["উপজেলার নাম"]), use_container_width=True, hide_index=True)
        else:
            st.success("সব উপজেলার তথ্য সংগ্রহ সম্পন্ন হয়েছে!")

    elif type == "union":
        st.write("### 🏛️ যেসব ইউনিয়নের তথ্য এখনো আসেনি:")
        master_set = set(ALL_UNIONS)
        remaining = sorted(list(master_set - submitted_set))
        
        st.info(f"মোট ইউনিয়ন বাকি: {len(remaining)} টি")
        if remaining:
            st.dataframe(pd.DataFrame(remaining, columns=["ইউনিয়নের নাম"]), use_container_width=True, hide_index=True)
        else:
            st.success("সব ইউনিয়নের তথ্য সংগ্রহ সম্পন্ন হয়েছে!")

# -----------------------------------------------------------------------------
# 3. MAIN APP LOGIC
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Admin Dashboard - Broadband Survey", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

c1, c2 = st.columns([5, 1])
with c1: st.title("🔐 Admin Dashboard")
with c2:
    if st.button("🏠 Back to Form"):
        st.switch_page("newbroadband_survey.py")

pwd = st.sidebar.text_input('Password', type='password')

if pwd == 'Bccadmin2025':
    st.sidebar.success('Authenticated')
    try:
        df_admin = conn.read(ttl="0")
        
        if df_admin is None or df_admin.empty:
            st.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
        else:
            # ১. ফিল্টারিং ও ক্লিনিং
            st.header("🔍 Data Search & Analytics")
            filtered_df = df_admin.copy()
            filtered_df['মোট গ্রাম'] = pd.to_numeric(filtered_df['মোট গ্রাম'], errors='coerce').fillna(0)
            
            div_list = ["All"] + sorted(df_admin['বিভাগ'].unique().astype(str).tolist())
            div_search = st.selectbox("বিভাগ ফিল্টার", div_list)
            if div_search != "All": 
                filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]

            # ২. স্ট্যাটিস্টিকস ক্যালকুলেশন (ফিক্সড কাউন্ট নিশ্চিত করা)
            st.markdown("---")
            st.markdown("### 📊 সামগ্রিক পরিসংখ্যান (National Progress)")
            
            # মাস্টার ডেটা অনুযায়ী টোটাল কাউন্ট (মাস্টার ডেটা না পেলে ডিফল্ট ৪৯৫/৪৫৫৪)
            TOTAL_UPZ = len(ALL_UPAZILAS) if len(ALL_UPAZILAS) > 0 else 495
            TOTAL_UNI = len(ALL_UNIONS) if len(ALL_UNIONS) > 0 else 4554
            
            # ইউনিক সাবমিশন লিস্ট
            sub_upz_list = df_admin['উপজেলা'].unique().tolist()
            sub_uni_list = df_admin['ইউনিয়ন'].unique().tolist()
            
            sub_upz_count = len(sub_upz_list)
            sub_uni_count = len(sub_uni_list)
            
            rem_upz_count = max(0, TOTAL_UPZ - sub_upz_count)
            rem_uni_count = max(0, TOTAL_UNI - sub_uni_count)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("মোট সাবমিশন", len(df_admin))
            
            with m2:
                st.metric("উপজেলা কভারেজ", f"{sub_upz_count}/{TOTAL_UPZ}", f"{rem_upz_count} বাকি")
                if st.button("🔍 তালিকা দেখুন", key="btn_upz"):
                    show_pending_list("upazila", sub_upz_list)

            with m3:
                st.metric("ইউনিয়ন কভারেজ", f"{sub_uni_count}/{TOTAL_UNI}", f"{rem_uni_count} বাকি")
                if st.button("🔍 তালিকা দেখুন", key="btn_uni"):
                    show_pending_list("union", sub_uni_list)

            m4.metric("গ্রাম (ফিল্টার্ড)", int(filtered_df['মোট গ্রাম'].sum()))

            # ৩. প্রগ্রেস চার্ট (ডোনাট চার্ট)
            g_progress1, g_progress2 = st.columns(2)
            with g_progress1:
                fig_upz = px.pie(names=["জমা হয়েছে", "বাকি"], values=[sub_upz_count, rem_upz_count], 
                               hole=0.6, title="উপজেলা প্রগ্রেস", color_discrete_sequence=["#00D487", "#222222"])
                st.plotly_chart(fig_upz, use_container_width=True)
            with g_progress2:
                fig_uni = px.pie(names=["জমা হয়েছে", "বাকি"], values=[sub_uni_count, rem_uni_count], 
                               hole=0.6, title="ইউনিয়ন প্রগ্রেস", color_discrete_sequence=["#006A4E", "#222222"])
                st.plotly_chart(fig_uni, use_container_width=True)

            # ৪. টেবিল প্রদর্শন
            st.subheader("📋 Data Records")
            st.dataframe(filtered_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")

elif pwd != "":
    st.sidebar.error('Incorrect Password')
else:
    st.info("অ্যাডমিন প্যানেল দেখার জন্য বাম পাশের সাইডবারে পাসওয়ার্ড দিন।")
