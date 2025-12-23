import streamlit as st
import pandas as pd
import json
import urllib.request
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. GEOGRAPHICAL DATA LOADER
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
def build_bd_data():
    try:
        div_raw = fetch_json(NUHIL_RAW['divisions'])
        dist_raw = fetch_json(NUHIL_RAW['districts'])
        upz_raw = fetch_json(NUHIL_RAW['upazilas'])
        uni_raw = fetch_json(NUHIL_RAW['unions'])
        
        def extract_data(raw):
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and 'data' in item: return item['data']
            if isinstance(raw, dict) and 'data' in raw: return raw['data']
            return []

        divs, dists, upzs, unis = extract_data(div_raw), extract_data(dist_raw), extract_data(upz_raw), extract_data(uni_raw)
        div_map = {str(d['id']): d.get('bn_name') or d.get('name') for d in divs}
        dist_map = {str(d['id']): {'bn_name': d.get('bn_name') or d.get('name'), 'division_id': str(d.get('division_id'))} for d in dists}
        upz_map = {str(u['id']): {'bn_name': u.get('bn_name') or u.get('name'), 'district_id': str(u.get('district_id'))} for u in upzs}
        
        uni_map = {}
        for u in unis:
            upid = str(u.get('upazilla_id') or u.get('upazila_id') or '')
            uni_map.setdefault(upid, []).append(u.get('bn_name') or u.get('name'))

        data_tree = {}
        for upz_id, upz in upz_map.items():
            dist_id = upz.get('district_id')
            dist_entry = dist_map.get(dist_id)
            if not dist_entry: continue
            div_name = div_map.get(dist_entry.get('division_id'), 'অন্যান্য')
            dist_name = dist_entry.get('bn_name')
            upz_name = upz.get('bn_name')
            data_tree.setdefault(div_name, {}).setdefault(dist_name, {})[upz_name] = uni_map.get(upz_id, [])
        return data_tree
    except:
        return {}

BD_DATA = build_bd_data()

# -----------------------------------------------------------------------------
# 2. UI HELPERS
# -----------------------------------------------------------------------------
def smart_geo_input(label, options_list, key):
    opts = ['-- নির্বাচন করুন --'] + (sorted(options_list) if options_list else []) + ['অন্যান্য']
    choice = st.selectbox(label, opts, key=key)
    if choice == 'অন্যান্য':
        return st.text_input(f"অন্যান্য (লিখুন): {label}", key=f"{key}_other")
    return "" if choice == '-- নির্বাচন করুন --' else choice

# -----------------------------------------------------------------------------
# 3. PAGE SETUP & DESIGN
# -----------------------------------------------------------------------------
st.set_page_config(page_title="ব্রডব্যান্ড কভারেজ জরিপ", page_icon="🌐", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.94), rgba(255, 255, 255, 0.94)),
            url('https://static.vecteezy.com/system/resources/thumbnails/072/508/275/small/a-highly-detailed-shot-of-a-server-rack-s-back-panel-showing-the-organized-chaos-of-cables-and-ports-free-photo.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    html, body, [class*="css"], .stMarkdown, p, label { font-family: 'Hind Siliguri', sans-serif; color: #000000 !important; font-weight: 600 !important; }
    div[data-testid="stWidgetLabel"] p { font-size: 1.2rem !important; }
    div.stButton > button { color: #006A4E !important; border: 2px solid #006A4E !important; background-color: rgba(255, 255, 255, 0.8) !important; font-weight: 700 !important; }
    div.stButton > button[kind="primary"] { background-color: #006A4E !important; color: white !important; }
    [data-testid="stSidebar"] { background-color: rgba(240, 242, 246, 0.9) !important; }
    .main-title { color: #006A4E !important; text-align: center; font-size: 2.2rem; font-weight: 700; border-bottom: 4px solid #F42A41; padding-bottom: 10px; }
    .section-head { background: #006A4E !important; color: white !important; padding: 10px 15px; border-radius: 8px; font-weight: 700; margin-top: 25px; border-left: 6px solid #F42A41; }
    div[data-baseweb="input"], div[data-baseweb="select"] { background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid #006A4E !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

def main():
    # Google Sheets Connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    st.markdown('<div class="main-title">🌐 সমগ্র বাংলাদেশে ব্রডব্যান্ড কভারেজ জরিপ</div>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; margin-bottom: 30px; margin-top: 5px;'><p style='font-size: 1.2rem; color:#080000; background: rgba(255,255,255,0.5); display: inline-block; padding: 2px 15px; border-radius: 20px;'>বাংলাদেশ কম্পিউটার কাউন্সিল (BCC)</p></div>", unsafe_allow_html=True)

    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    st.markdown('<div class="section-head">১. ব্যক্তিগত ও ভৌগোলিক তথ্য</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("নাম (Name) *")
        designation = st.text_input("পদবী (Designation) *")
    with col2:
        workplace = st.text_input("কর্মস্থলের নাম (Workplace Name) *")

    st.write("---")
    g1, g2 = st.columns(2)
    with g1:
        div_list = list(BD_DATA.keys())
        final_div = smart_geo_input('বিভাগ (Division)', div_list, 'geo_div')
        dist_opts = list(BD_DATA[final_div].keys()) if final_div in BD_DATA else []
        final_dist = smart_geo_input('জেলা (District)', dist_opts, 'geo_dist')
    with g2:
        upz_opts = list(BD_DATA[final_div][final_dist].keys()) if (final_div in BD_DATA and final_dist in BD_DATA[final_div]) else []
        final_upz = smart_geo_input('উপজেলা (Upazila)', upz_opts, 'geo_upz')
        uni_opts = BD_DATA[final_div][final_dist][final_upz] if (final_div in BD_DATA and final_dist in BD_DATA[final_div] and final_upz in BD_DATA[final_div][final_dist]) else []
        final_uni = smart_geo_input('ইউনিয়ন (Union)', uni_opts, 'geo_uni')

    st.markdown('<div class="section-head">২. গ্রামের তথ্য</div>', unsafe_allow_html=True)
    gv1, gv2 = st.columns(2)
    with gv1: total_villages = st.number_input("ইউনিয়নে মোট গ্রামের সংখ্যা", min_value=0, step=1)
    with gv2: covered_villages = st.number_input("ইন্টারনেটের আওতাভুক্ত গ্রামের সংখ্যা", min_value=0, step=1)

    st.markdown('<div class="section-head">৩. সেবা প্রদানকৃত ISP এর তথ্য</div>', unsafe_allow_html=True)
    isp_records = []
    for i in range(st.session_state.rows):
        st.markdown(f"**ISP নং {i+1}**")
        ic1, ic2, ic3 = st.columns([3, 2, 2])
        with ic1: iname = st.text_input("ISP নাম", key=f"in_{i}")
        with ic2: icontact = st.text_input("যোগাযোগের নম্বর", key=f"ic_{i}")
        with ic3: isubs = st.number_input("গ্রাহক সংখ্যা", min_value=0, key=f"is_{i}", step=1)
        if iname: isp_records.append({"name": iname, "phone": icontact, "subs": isubs})

    b1, b2, _ = st.columns([1.5, 1, 4])
    if b1.button("➕ আরও ISP যোগ করুন"):
        st.session_state.rows += 1
        st.rerun()
    if b2.button("➖ বাদ দিন") and st.session_state.rows > 1:
        st.session_state.rows -= 1
        st.rerun()

    st.write("---")
    if st.button("জমা দিন (Submit Data)", use_container_width=True, type="primary"):
        if not (name and final_div and final_dist):
            st.error("দয়া করে নাম এবং ভৌগোলিক তথ্য নিশ্চিত করুন।")
        else:
            isp_final = " | ".join([f"{r['name']}({r['phone']}):{r['subs']}" for r in isp_records])
            new_record = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "নাম": name, "পদবী": designation, "কর্মস্থল": workplace,
                "বিভাগ": final_div, "জেলা": final_dist, "উপজেলা": final_upz, "ইউনিয়ন": final_uni,
                "মোট গ্রাম": total_villages, "আওতাভুক্ত গ্রাম": covered_villages,
                "ISP তথ্য": isp_final
            }])
            
            try:
                # Fetch existing data
                existing_data = conn.read()
                updated_df = pd.concat([existing_data, new_record], ignore_index=True)
                conn.update(data=updated_df)
                st.success("✅ আপনার তথ্য সফলভাবে Google Sheet-এ রেকর্ড করা হয়েছে।")
                st.balloons()
                st.session_state.rows = 1
            except Exception as e:
                st.error(f"Error: {e}. Please ensure Google Sheet is connected.")

    # --- ADMIN PANEL ---
    st.sidebar.header('🔐 Admin Panel')
    pwd = st.sidebar.text_input('Password', type='password')
    
    if pwd == 'Bccadmin2025':
        st.sidebar.success('Authenticated')
        try:
            df_admin = conn.read()
            if df_admin.empty:
                st.sidebar.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
            else:
                show_stats = st.sidebar.checkbox("📊 View Dashboard & Search", value=False)
                if show_stats:
                    st.markdown("---")
                    st.header("🔍 Data Search & Analytics")
                    
                    # Filtering Logic
                    f1, f2 = st.columns(2)
                    filtered_df = df_admin.copy()
                    with f1: div_search = st.selectbox("বিভাগ ফিল্টার", ["All"] + sorted(df_admin['বিভাগ'].unique().tolist()))
                    if div_search != "All": filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]
                    
                    # Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Submissions", len(filtered_df))
                    m2.metric("Total Villages", int(filtered_df['মোট গ্রাম'].sum()))
                    m3.metric("Covered Villages", int(filtered_df['আওতাভুক্ত গ্রাম'].sum()))
                    
                    # Chart
                    st.write("**Submissions by Division**")
                    div_counts = filtered_df['বিভাগ'].value_counts().reset_index()
                    div_counts.columns = ['Division', 'Count']
                    st.plotly_chart(px.bar(div_counts, x='Division', y='Count', text_auto=True, color_discrete_sequence=['#006A4E']), use_container_width=True)
                    
                    st.subheader("📋 Search Results")
                    st.dataframe(filtered_df, use_container_width=True)

                    # Delete Logic
                    with st.expander("🗑️ Delete Data Entry"):
                        delete_index = st.number_input("Enter Row Index:", min_value=0, max_value=len(df_admin)-1, step=1)
                        if st.button("Confirm Delete"):
                            df_admin = df_admin.drop(delete_index)
                            conn.update(data=df_admin)
                            st.success("Deleted!")
                            st.rerun()
        except:
            st.sidebar.error("Could not connect to Google Sheets.")
    elif pwd:
        st.sidebar.error('ভুল পাসওয়ার্ড')

if __name__ == "__main__":
    main()