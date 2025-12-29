import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import json
import urllib.request

# -----------------------------------------------------------------------------
# ১. মাস্টার ডেটা লোডার (মাস্টার লিস্ট নিশ্চিত করার জন্য)
# -----------------------------------------------------------------------------
@st.cache_data
def get_master_data():
    try:
        # বাংলাদেশের সব উপজেলার নাম লোড করা
        upz_url = "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/upazilas/upazilas.json"
        # বাংলাদেশের সব ইউনিয়নের নাম লোড করা
        uni_url = "https://raw.githubusercontent.com/nuhil/bangladesh-geocode/master/unions/unions.json"
        
        def fetch_names(url):
            
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode('utf-8'))
                raw_list = data['data'] if isinstance(data, dict) and 'data' in data else data
                return sorted([str(i.get('bn_name') or i.get('name')).strip() for i in raw_list if isinstance(i, dict) and (i.get('bn_name') or i.get('name'))])

        return fetch_names(upz_url), fetch_names(uni_url)
    except Exception as e:
        st.error(f"মাস্টার ডেটা লোড করতে সমস্যা হয়েছে: {e}")
        return [], []

# মাস্টার লিস্ট সংগ্রহ
ALL_UPAZILAS, ALL_UNIONS = get_master_data()

# -----------------------------------------------------------------------------
# ২. পপ-আপ ডায়ালগ ফাংশন (বাকি তালিকা দেখানোর জন্য)
# -----------------------------------------------------------------------------
@st.dialog("বাকি থাকা তথ্যের তালিকা (Pending List)")
def show_pending_modal(type, submitted_list):
    # জমা হওয়া নামের তালিকা ক্লিন করা এবং 'None' ভ্যালু বাদ দেওয়া
    submitted_set = set([str(name).strip() for name in submitted_list if name and str(name).lower() != 'none'])
    
    if type == "upazila":
        st.subheader("📍 বাকি থাকা উপজেলাসমূহ")
        master_set = set(ALL_UPAZILAS)
        remaining = sorted(list(master_set - submitted_set))
        
        st.info(f"মোট উপজেলা বাকি: {len(remaining)} টি")
        if remaining:
            st.dataframe(pd.DataFrame(remaining, columns=["উপজেলার নাম"]), use_container_width=True, hide_index=True)
        else:
            st.success("অভিনন্দন! সব উপজেলার তথ্য জমা হয়েছে।")

    elif type == "union":
        st.subheader("🏛️ বাকি থাকা ইউনিয়নসমূহ")
        master_set = set(ALL_UNIONS)
        remaining = sorted(list(master_set - submitted_set))
        
        st.info(f"মোট ইউনিয়ন বাকি: {len(remaining)} টি")
        if remaining:
            st.dataframe(pd.DataFrame(remaining, columns=["ইউনিয়নের নাম"]), use_container_width=True, hide_index=True)
        else:
            st.success("অভিনন্দন! সব ইউনিয়নের তথ্য জমা হয়েছে।")

# -----------------------------------------------------------------------------
# ৩. ড্যাশবোর্ড লজিক
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Admin Panel - Broadband Survey", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# হেডার
c1, c2 = st.columns([5, 1])
with c1: st.title("🔐 Admin Dashboard")
with c2: 
    if st.button("🏠 Back to Form"): st.switch_page("newbroadband_survey.py")

pwd = st.sidebar.text_input('Password', type='password')

if pwd == 'Bccadmin2025':
    try:
        df_admin = conn.read(ttl="0")
        
        if df_admin is not None and not df_admin.empty:
            # ইউনিক সাবমিশন তালিকা ক্লিনিং
            submitted_upz_names = [str(name).strip() for name in df_admin['উপজেলা'].unique() if name and str(name).lower() != 'none']
            submitted_uni_names = [str(name).strip() for name in df_admin['ইউনিয়ন'].unique() if name and str(name).lower() != 'none']

            # ফিক্সড টোটাল (৪৯৫ ও ৪৫৫৪)
            TOTAL_UPZ = 495
            TOTAL_UNI = 4554

            # ক্যালকুলেশন
            upz_count = len(submitted_upz_names)
            uni_count = len(submitted_uni_names)
            upz_rem = max(0, TOTAL_UPZ - upz_count)
            uni_rem = max(0, TOTAL_UNI - uni_count)

            st.markdown("### 📊 সামগ্রিক পরিসংখ্যান (National Progress)")
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("মোট সাবমিশন", len(df_admin))
            
            with m2:
                st.metric("উপজেলা কভারেজ", f"{upz_count}/{TOTAL_UPZ}", f"{upz_rem} বাকি", delta_color="inverse")
                if st.button("🔍 তালিকা দেখুন", key="view_upz"):
                    show_pending_modal("upazila", submitted_upz_names)

            with m3:
                st.metric("ইউনিয়ন কভারেজ", f"{uni_count}/{TOTAL_UNI}", f"{uni_rem} বাকি", delta_color="inverse")
                if st.button("🔍 তালিকা দেখুন", key="view_uni"):
                    show_pending_modal("union", submitted_uni_names)

            total_villages = pd.to_numeric(df_admin['মোট গ্রাম'], errors='coerce').fillna(0).sum()
            m4.metric("গ্রাম (তথ্যমতে)", int(total_villages))

            # ৪. প্রগ্রেস চার্ট (ডোনাট চার্ট)
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            upz_pct = int((upz_count / TOTAL_UPZ) * 100) if TOTAL_UPZ > 0 else 0
            uni_pct = int((uni_count / TOTAL_UNI) * 100) if TOTAL_UNI > 0 else 0

            with g1:
                st.write("**উপজেলা সাবমিশন প্রগ্রেস**")
                fig_upz = px.pie(names=["জমা হয়েছে", "বাকি"], values=[upz_count, upz_rem], hole=0.6,
                               color_discrete_sequence=["#00D487", "#222222"])
                fig_upz.add_annotation(text=f"{upz_pct}%", showarrow=False, font_size=25)
                st.plotly_chart(fig_upz, use_container_width=True)
            
            with g2:
                st.write("**ইউনিয়ন সাবমিশন প্রগ্রেস**")
                fig_uni = px.pie(names=["জমা হয়েছে", "বাকি"], values=[uni_count, uni_rem], hole=0.6,
                               color_discrete_sequence=["#006A4E", "#222222"])
                fig_uni.add_annotation(text=f"{uni_pct}%", showarrow=False, font_size=25)
                st.plotly_chart(fig_uni, use_container_width=True)

            # ডাটা টেবিল
            st.subheader("📋 জমা হওয়া ডাটা রেকর্ড")
            st.dataframe(df_admin, use_container_width=True)

    except Exception as e:
        st.error(f"ডাটা লোড করতে সমস্যা হয়েছে: {e}")

elif pwd != "":
    st.sidebar.error('Incorrect Password')
else:
    st.info("অ্যাডমিন প্যানেল দেখার জন্য বাম পাশের সাইডবারে পাসওয়ার্ড দিন।")
