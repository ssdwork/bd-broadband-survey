import streamlit as st
import pandas as pd
import os
import json
import urllib.request
from datetime import datetime
import plotly.express as px  # Added for charts

# -----------------------------------------------------------------------------
# 1. GEOGRAPHICAL DATA LOADER (From Code 1)
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
# 3. PAGE SETUP & DESIGN (From Code 2)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="ব্রডব্যান্ড কভারেজ জরিপ", page_icon="🌐", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&display=swap');
    
    /* 1. Global Background & Overlay */
    .stApp {
        background: 
            linear-gradient(rgba(255, 255, 255, 0.94), rgba(255, 255, 255, 0.94)),
            url('https://static.vecteezy.com/system/resources/thumbnails/072/508/275/small/a-highly-detailed-shot-of-a-server-rack-s-back-panel-showing-the-organized-chaos-of-cables-and-ports-free-photo.jpg'); 
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 2. Global Text Colors for Light Mode Visibility */
    html, body, [class*="css"], .stMarkdown, p, label { 
        font-family: 'Hind Siliguri', sans-serif; 
        color: #000000 !important; /* Deep black for maximum legibility */
    }

    /* 3. Button Visibility Fix (The main problem in your screenshot) */
    /* Target the text inside buttons to be dark green so they are visible on white/light gray */
    div.stButton > button {
        color: #006A4E !important;
        border: 2px solid #006A4E !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        font-weight: 700 !important;
    }
    
    /* Primary buttons (Submit) stay Green with White text */
    div.stButton > button[kind="primary"] {
        background-color: #006A4E !important;
        color: white !important;
    }

    /* 4. Sidebar Contrast Fix */
    [data-testid="stSidebar"] {
        background-color: rgba(240, 242, 246, 0.9) !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* 5. Heading & Section Styling */
    .main-title { 
        color: #006A4E !important; 
        text-align: center; 
        font-size: 2.2rem; 
        font-weight: 700; 
        border-bottom: 4px solid #F42A41; 
        padding-bottom: 10px;
    }

    .section-head { 
        background: #006A4E !important; 
        color: white !important; 
        padding: 10px 15px; 
        border-radius: 8px; 
        font-weight: 700; 
        margin-top: 25px; 
        border-left: 6px solid #F42A41;
    }

    /* 6. Form Fields Glassmorphism */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #006A4E !important;
        border-radius: 8px !important;
    }

    /* Fix for Dark Mode switch - Inverse everything if dark mode is active */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: 
                linear-gradient(rgba(14, 17, 23, 0.92), rgba(14, 17, 23, 0.92)),
                url('https://static.vecteezy.com/system/resources/thumbnails/072/508/275/small/a-highly-detailed-shot-of-a-server-rack-s-back-panel-showing-the-organized-chaos-of-cables-and-ports-free-photo.jpg');
        }
        html, body, [class*="css"], .stMarkdown, p, label { 
            color: #FFFFFF !important; 
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #FFFFFF !important;
        }
        div.stButton > button {
            color: #FFFFFF !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # Centered Title with Subtitle
    st.markdown('<div class="main-title">🌐 সমগ্র বাংলাদেশে ব্রডব্যান্ড কভারেজ জরিপ</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px; margin-top: 5px;'>
            <p style='font-size: 1.2rem; color:#080000; background: rgba(255,255,255,0.5); display: inline-block; padding: 2px 15px; border-radius: 20px;'>
                বাংলাদেশ কম্পিউটার কাউন্সিল (BCC)
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        
    """, unsafe_allow_html=True)
    st.markdown('<div class="description">শহর, গ্রাম ও দুর্গম এলাকায় বিদ্যমান ব্রডব্যান্ড অবকাঠামো ও প্রাপ্যতার বাস্তব চিত্র নিরূপণে এই জরিপটি পরিচালিত হচ্ছে।</div>', unsafe_allow_html=True)

    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    # --- ১. ব্যক্তিগত ও কভারেজ এলাকা তথ্য ---
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

    # --- ২. গ্রামের সংখ্যা ---
    st.markdown('<div class="section-head">২. গ্রামের তথ্য</div>', unsafe_allow_html=True)
    gv1, gv2 = st.columns(2)
    with gv1: total_villages = st.number_input("ইউনিয়নে মোট গ্রামের সংখ্যা", min_value=0, step=1)
    with gv2: covered_villages = st.number_input("ইন্টারনেটের আওতাভুক্ত গ্রামের সংখ্যা", min_value=0, step=1)

    # --- ৩. ISP তথ্য (Dynamic Rows) ---
    st.markdown('<div class="section-head">৩. সেবা প্রদানকৃত ISP এর তথ্য</div>', unsafe_allow_html=True)
    
    isp_records = []
    # Note: We don't put the buttons inside the form because st.rerun() resets form state unless handled carefully.
    # However, to keep it simple, we use a container for inputs.
    for i in range(st.session_state.rows):
        st.markdown(f"**ISP নং {i+1}**")
        ic1, ic2, ic3 = st.columns([3, 2, 2])
        with ic1: iname = st.text_input("ISP নাম", key=f"in_{i}")
        with ic2: icontact = st.text_input("যোগাযোগের নম্বর", key=f"ic_{i}")
        with ic3: isubs = st.number_input("গ্রাহক সংখ্যা", min_value=0, key=f"is_{i}", step=1)
        if iname:
            isp_records.append({"name": iname, "phone": icontact, "subs": isubs})

    # Add/Remove buttons
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
            record = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "নাম": name, "পদবী": designation, "কর্মস্থল": workplace,
                "বিভাগ": final_div, "জেলা": final_dist, "উপজেলা": final_upz, "ইউনিয়ন": final_uni,
                "মোট গ্রাম": total_villages, "আওতাভুক্ত গ্রাম": covered_villages,
                "ISP তথ্য": isp_final
            }
            
            df = pd.DataFrame([record])
            file = "broadband_survey_results.csv"
            write_header = not os.path.exists(file)
            df.to_csv(file, mode='a', header=write_header, index=False, encoding='utf-8-sig')
            
            st.success("✅ আপনার তথ্য সফলভাবে রেকর্ড করা হয়েছে। ধন্যবাদ!")
            st.balloons()
            st.session_state.rows = 1 # Reset rows for next entry

   # --- ADMIN SIDEBAR WITH ADVANCED FILTERS & ANALYTICS ---
    st.sidebar.header('🔐 Admin Panel')
    pwd = st.sidebar.text_input('Password', type='password')
    
    if pwd == 'Bccadmin2025':
        st.sidebar.success('Authenticated')
        
        # Check if file exists and has data
        if os.path.exists('broadband_survey_results.csv'):
            df_admin = pd.read_csv('broadband_survey_results.csv')
            
            # --- CRITICAL FIX: Handle Empty Dataframe ---
            if df_admin.empty:
                st.info("জরিপের ফাইলটি বর্তমানে খালি।")
                if st.button("সিস্টেম রিসেট করুন (Delete File)"):
                    os.remove('broadband_survey_results.csv')
                    st.rerun()
            else:
                # 1. DOWNLOAD SECTION
                with open('broadband_survey_results.csv', 'rb') as f:
                    st.sidebar.download_button('📥 Download Full CSV', f, file_name='survey_data.csv')
                
                st.sidebar.markdown("---")
                show_stats = st.sidebar.checkbox("📊 View Dashboard & Search", value=False)
                
                if show_stats:
                    st.markdown("---")
                    st.header("🔍 Data Search & Analytics")

                    # 2. FILTER SECTION
                    st.subheader("Filter Data")
                    f1, f2, f3, f4 = st.columns(4)
                    
                    filtered_df = df_admin.copy()
                    with f1:
                        div_search = st.selectbox("বিভাগ", ["All"] + sorted(df_admin['বিভাগ'].unique().tolist()))
                    if div_search != "All":
                        filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]
                    
                    with f2:
                        dist_search = st.selectbox("জেলা", ["All"] + sorted(filtered_df['জেলা'].unique().tolist()))
                    if dist_search != "All":
                        filtered_df = filtered_df[filtered_df['জেলা'] == dist_search]
                    
                    with f3:
                        upz_search = st.selectbox("উপজেলা", ["All"] + sorted(filtered_df['উপজেলা'].unique().tolist()))
                    if upz_search != "All":
                        filtered_df = filtered_df[filtered_df['উপজেলা'] == upz_search]
                    
                    with f4:
                        uni_search = st.selectbox("ইউনিয়ন", ["All"] + sorted(filtered_df['ইউনিয়ন'].unique().tolist()))
                    if uni_search != "All":
                        filtered_df = filtered_df[filtered_df['ইউনিয়ন'] == uni_search]

                    # 3. METRICS
                    st.markdown("### Statistics for Selection")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Submissions", len(filtered_df))
                    m2.metric("Districts", filtered_df['জেলা'].nunique())
                    m3.metric("Total Villages", int(filtered_df['মোট গ্রাম'].sum()))
                    m4.metric("Covered Villages", int(filtered_df['আওতাভুক্ত গ্রাম'].sum()))

                    # 4. VISUAL CHARTS
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Submissions by Division**")
                        div_counts = filtered_df['বিভাগ'].value_counts().reset_index()
                        div_counts.columns = ['Division', 'Count']
                        fig_div = px.bar(div_counts, x='Division', y='Count', text_auto=True, color_discrete_sequence=['#006A4E'])
                        st.plotly_chart(fig_div, use_container_width=True)

                    with c2:
                        st.write("**Coverage Proportion**")
                        total_v = filtered_df['মোট গ্রাম'].sum()
                        cov_v = filtered_df['আওতাভুক্ত গ্রাম'].sum()
                        if total_v > 0:
                            gap_df = pd.DataFrame({'Cat': ['Covered', 'Uncovered'], 'Val': [cov_v, (total_v - cov_v)]})
                            fig_pie = px.pie(gap_df, values='Val', names='Cat', hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c'])
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.info("No village data for this selection")

                    # 5. DATA TABLE
                    st.subheader("📋 Search Results")
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # 6. DELETE SECTION (Combined Single & All)
                    st.markdown("---")
                    st.subheader("🗑️ Data Management (Danger Zone)")
                    
                    col_del1, col_del2 = st.columns(2)
                    
                    with col_del1:
                        with st.expander("Delete Single Entry"):
                            st.warning("Index based on full list")
                            # int() cast is now safe because we checked if df_admin is empty above
                            delete_index = st.number_input("Enter Row Index:", 
                                                         min_value=int(df_admin.index.min()), 
                                                         max_value=int(df_admin.index.max()), step=1)
                            if st.button("Confirm Single Delete"):
                                df_admin.drop(delete_index).to_csv('broadband_survey_results.csv', index=False, encoding='utf-8-sig')
                                st.success(f"Entry {delete_index} deleted!")
                                st.rerun()

                    with col_del2:
                        with st.expander("Delete ALL Data"):
                            st.error("This will wipe all records!")
                            confirm_text = st.text_input("Type 'DELETE' to wipe all")
                            if st.button("Wipe All Records"):
                                if confirm_text == "DELETE":
                                    # Overwrite with just the column headers
                                    empty_df = pd.DataFrame(columns=df_admin.columns)
                                    empty_df.to_csv('broadband_survey_results.csv', index=False, encoding='utf-8-sig')
                                    st.warning("All data cleared.")
                                    st.rerun()
                                else:
                                    st.info("Type 'DELETE' in all caps.")

        else:
            st.sidebar.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
            
    elif pwd:
        st.sidebar.error('ভুল পাসওয়ার্ড')

if __name__ == "__main__":
    main()