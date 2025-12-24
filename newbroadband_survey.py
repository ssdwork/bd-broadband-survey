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
    
    /* 1. Main Background - Dark Overlay */
    .stApp {
        background: linear-gradient(rgba(15, 17, 22, 0.9), rgba(15, 17, 22, 0.9)),
            url('https://static.vecteezy.com/system/resources/thumbnails/072/508/275/small/a-highly-detailed-shot-of-a-server-rack-s-back-panel-showing-the-organized-chaos-of-cables-and-ports-free-photo.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }

    /* 2. Global Text Color - White (ব্যাকগ্রাউন্ড ডার্ক তাই টেক্সট সবসময় সাদা থাকবে) */
    html, body, [class*="css"], .stMarkdown, p, label, .stTextInput > label, .stNumberInput > label { 
        font-family: 'Hind Siliguri', sans-serif; 
        color: #FFFFFF !important; 
        font-weight: 500 !important; 
    }
    
    /* 3. Headers and Metrics */
    h1, h2, h3, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* 4. Input Fields & Dropdowns - লাইট ও ডার্ক মোড ফিক্স */
    div[data-baseweb="input"], div[data-baseweb="select"] { 
        background-color: #E8ECEF !important; /* হালকা সিলভার ব্যাকগ্রাউন্ড যা ডার্ক মোডেও স্পষ্ট থাকবে */
        border: 2px solid #00D487 !important; 
        border-radius: 8px !important; 
    }

    /* ইনপুট বক্সের টেক্সট কালার সবসময় কালো থাকবে */
    div[data-baseweb="input"] input, div[data-baseweb="select"] div {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; /* ব্রাউজার ফোর্সড কালার ওভাররাইড */
        font-weight: 600 !important;
    }

    /* ড্রপডাউন ওপেন হওয়ার পর অপশনগুলোর কালার */
    ul[data-baseweb="menu"] li {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }

    /* ড্রপডাউনের ভিতরের টেক্সট ডার্ক মোডেও যেন স্পষ্ট থাকে */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #000000 !important;
    }

    /* 5. Sidebar - Dark Grey */
    [data-testid="stSidebar"] { 
        background-color: rgba(38, 39, 48, 0.95) !important; 
        border-right: 1px solid #333;
    }

    /* 6. Buttons */
    div.stButton > button { 
        color: #00D487 !important; 
        border: 2px solid #00D487 !important; 
        background-color: rgba(0, 0, 0, 0.5) !important; 
        font-weight: 700 !important; 
        border-radius: 8px !important;
    }
    div.stButton > button:hover {
        background-color: #00D487 !important;
        color: #000000 !important;
    }
    div.stButton > button[kind="primary"] { 
        background-color: #00D487 !important; 
        color: black !important; 
        border: none !important;
    }

    /* 7. Custom Classes */
    .main-title { 
        color: #00D487 !important; 
        text-align: center; 
        font-size: 2.2rem; 
        font-weight: 700; 
        border-bottom: 4px solid #F42A41; 
        padding-bottom: 10px; 
    }
    .section-head { 
        background: #00D487 !important; 
        color: #000000 !important; 
        padding: 10px 15px; 
        border-radius: 8px; 
        font-weight: 700; 
        margin-top: 25px; 
        border-left: 6px solid #F42A41; 
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    </style>
""", unsafe_allow_html=True)

def main():
    # Google Sheets Connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    st.markdown('<div class="main-title">🌐 সমগ্র বাংলাদেশে ব্রডব্যান্ড কভারেজ জরিপ</div>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; margin-bottom: 30px; margin-top: 5px;'><p style='font-size: 1.2rem; color:#FFFFFF; background: rgba(255,255,255,0.1); border: 1px solid #555; display: inline-block; padding: 2px 15px; border-radius: 20px;'>Bangladesh Computer Council (BCC)</p></div>", unsafe_allow_html=True)

    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    st.markdown('<div class="section-head">১. ব্যক্তিগত ও ভৌগোলিক তথ্য</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("নাম (Name) *")
        designation = st.text_input("পদবী (Designation) *")
    with col2:
		# মোবাইল নম্বর ফিল্ড (১১ ডিজিট বাধ্যতামূলক)
        user_phone = st.text_input("মোবাইল নম্বর (১১ ডিজিট) *", max_chars=11, help="উদাহরণ: 01712345678")
        workplace = st.text_input("কর্মস্থলের নাম (Workplace Name) *", placeholder="উপজেলা, জেলা")

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

    st.markdown('<div class="section-head">২. ইউনিয়ন ও গ্রামের তথ্য</div>', unsafe_allow_html=True)
    
    # ব্রডব্যান্ড ড্রপডাউন
    is_broadband = st.selectbox("ইউনিয়নটি ব্রডব্যান্ড এর আওতাভুক্ত? *", ["-- নির্বাচন করুন --", "হ্যাঁ", "না"], key="bb_coverage")
    
    st.write("##")
    
    # গ্রামের সংখ্যা ইনপুট (সম্পূর্ণ স্পেস দিয়ে ইনডেন্ট করা)
    gv1, gv2 = st.columns(2)
    with gv1:
        total_villages = st.number_input("ইউনিয়নে মোট গ্রামের সংখ্যা", min_value=0, step=1, key="total_v")
    with gv2:
        covered_villages = st.number_input("ইন্টারনেটের আওতাভুক্ত গ্রামের সংখ্যা", min_value=0, max_value=total_villages, step=1, key="covered_v")

    st.markdown('<div class="section-head">৩. উপজেলাতে সেবা প্রদানকৃত ISP এর তথ্য</div>', unsafe_allow_html=True)
    isp_records = []
    for i in range(st.session_state.rows):
        st.markdown(f"**ISP নং {i+1}**")
        ic1, ic2, ic3 = st.columns([3, 2, 2])
        with ic1: iname = st.text_input("ISP নাম", key=f"in_{i}")
        with ic2: 
                icontact = st.text_input("যোগাযোগের নম্বর", key=f"ic_{i}", help="১১ ডিজিটের মোবাইল নম্বর দিন")
                # মোবাইল নম্বর ভ্যালিডেশন চেক
                if icontact:
                    if not icontact.isdigit():
                        st.error("⚠️ শুধুমাত্র সংখ্যা ব্যবহার করুন")
                    elif len(icontact) != 11:
                        st.warning("⚠️ নম্বরটি অবশ্যই ১১ ডিজিটের হতে হবে")
        with ic3:
            # ১. চেক-বক্সের মান আগে থেকে জেনে নেওয়া (যাতে নিচের ইনপুট বক্সটি নিয়ন্ত্রণ করা যায়)
            is_unknown = st.session_state.get(f"un_subs_{i}", False)
            
            # ২. গ্রাহক সংখ্যা ইনপুট বক্স (উপরে থাকবে)
            if is_unknown:
                isubs = "জানা নেই"
                st.text_input("গ্রাহক সংখ্যা", value="জানা নেই", key=f"is_dis_{i}", disabled=True)
            else:
                isubs = st.number_input("গ্রাহক সংখ্যা", min_value=0, key=f"is_{i}", step=1)
            
            # ৩. চেক-বক্সটি এখন ইনপুট বক্সের নিচে দেখাবে
            st.checkbox("জানা নেই", key=f"un_subs_{i}")
        
        # ডাটা অ্যাপেন্ড করা
        if iname:
            isp_records.append({"name": iname, "phone": icontact, "subs": isubs})

    b1, b2, _ = st.columns([1.5, 1, 4])
    if b1.button("➕ আরও ISP যোগ করুন"):
        st.session_state.rows += 1
        st.rerun()
    if b2.button("➖ বাদ দিন") and st.session_state.rows > 1:
        st.session_state.rows -= 1
        st.rerun()

    st.write("---")
    # Replace the Submission logic in your main() function with this:

    if st.button("জমা দিন (Submit Data)", use_container_width=True, type="primary"):
        # ১. ডাটাবেজ (Google Sheet) থেকে লাইভ ডাটা পড়া
        existing_data = conn.read(ttl=0)
        
        # ২. ডুপ্লিকেট চেক (ইউজারের মোবাইল নম্বর দিয়ে)
        is_duplicate = False
        if existing_data is not None and not existing_data.empty:
            if "মোবাইল নম্বর" in existing_data.columns:
                # শিটের নম্বরগুলোকে টেক্সট হিসেবে নিয়ে চেক করা
                if user_phone in existing_data["মোবাইল নম্বর"].astype(str).values:
                    is_duplicate = True

        # ৩. সব ISP নম্বরের বৈধতা চেক করা
        all_isp_valid = all(len(r['phone']) == 11 and r['phone'].isdigit() for r in isp_records)

        # ৪. কন্ডিশন ভ্যালিডেশন
        if not (name and user_phone and final_div and final_dist):
            st.error("দয়া করে নাম, আপনার মোবাইল নম্বর এবং ভৌগোলিক তথ্য নিশ্চিত করুন।")
        elif len(user_phone) != 11 or not user_phone.isdigit():
            st.error("❌ আপনার ব্যক্তিগত মোবাইল নম্বরটি সঠিক নয় (১১ ডিজিট হতে হবে)।")
        elif is_duplicate:
            st.warning("⚠️ আপনি ইতোমধ্যে একবার তথ্য দিয়েছেন।")
        elif not all_isp_valid:
            st.error("❌ ISP যোগাযোগের নম্বর সঠিক নয় (১১ ডিজিট ও শুধুমাত্র সংখ্যা হতে হবে)।")
        else:
            try:
                # ৫. ডাটা তৈরি করা
                isp_final = " | ".join([f"{r['name']}({r['phone']}):{r['subs']}" for r in isp_records])
                
                new_record = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "নাম": name, 
                    "পদবী": designation, 
                    "মোবাইল নম্বর": user_phone,  # নতুন কলাম
                    "কর্মস্থল": workplace,
                    "বিভাগ": final_div, 
                    "জেলা": final_dist, 
                    "উপজেলা": final_upz, 
                    "ইউনিয়ন": final_uni,
                    "ব্রডব্যান্ড আওতাভুক্ত": is_broadband,
                    "মোট গ্রাম": total_villages, 
                    "আওতাভুক্ত গ্রাম": covered_villages,
                    "উপজেলাতে ISP তথ্য": isp_final
                }])
                
                # ৬. গুগল শিটে আপডেট করা
                if existing_data is not None and not existing_data.empty:
                    updated_df = pd.concat([existing_data, new_record], ignore_index=True)
                else:
                    updated_df = new_record
                
                conn.update(data=updated_df)
                
                st.success("✅ আপনার তথ্য সফলভাবে সংরক্ষিত হয়েছে।")
                st.balloons()
                
                # ৭. রিসেট লজিক
                st.session_state.rows = 1
                import time
                time.sleep(2) 
                st.rerun() 
                
            except Exception as e:
                st.error(f"Error: {e}")
                
    # --- ADMIN PANEL ---
    st.sidebar.markdown("---") # Visual separator
    
    # This checkbox controls the visibility
    if st.sidebar.checkbox("🔐 Admin Login", value=False):
        
        st.sidebar.header('🔐 Admin Panel')
        pwd = st.sidebar.text_input('Password', type='password')
        
        if pwd == 'Bccadmin2025':
            st.sidebar.success('Authenticated')
            try:
                df_admin = conn.read(ttl="5m")
                if df_admin.empty:
                    st.sidebar.info("জরিপের কোনো তথ্য এখনো জমা পড়েনি।")
                else:
                    show_stats = st.sidebar.checkbox("📊 View Dashboard & Search", value=False)
                    if show_stats:
                        st.markdown("---")
                        st.header("🔍 Data Search & Analytics")
                        
                        # Ensure numeric data for calculations
                        filtered_df = df_admin.copy()
                        filtered_df['মোট গ্রাম'] = pd.to_numeric(filtered_df['মোট গ্রাম'], errors='coerce').fillna(0)
                        filtered_df['আওতাভুক্ত গ্রাম'] = pd.to_numeric(filtered_df['আওতাভুক্ত গ্রাম'], errors='coerce').fillna(0)
    
                        # 1. Filtering Logic
                        f1, f2 = st.columns(2)
                        with f1: 
                            div_search = st.selectbox("বিভাগ ফিল্টার", ["All"] + sorted(df_admin['বিভাগ'].unique().tolist()))
                        if div_search != "All": 
                            filtered_df = filtered_df[filtered_df['বিভাগ'] == div_search]
    
                        # 2. Metrics Calculations
                        m1, m2, m3 = st.columns(3)
                        total_vills = int(filtered_df['মোট গ্রাম'].sum())
                        covered_vills = int(filtered_df['আওতাভুক্ত গ্রাম'].sum())
                        uncovered_vills = max(0, total_vills - covered_vills)
                        
                        m1.metric("Submissions", len(filtered_df))
                        m2.metric("Total Villages", total_vills)
                        m3.metric("Covered Villages", covered_vills)
    
                        # 3. Pie Chart
                        st.write("**ইন্টারনেট কভারেজ অনুপাত (Coverage Ratio)**")
                        if total_vills > 0:
                            pie_data = pd.DataFrame({
                                "Category": ["আওতাভুক্ত (Covered)", "বাকি (Uncovered)"],
                                "Count": [covered_vills, uncovered_vills]
                            })
                            fig_pie = px.pie(pie_data, values='Count', names='Category', hole=0.4,
                                             color_discrete_map={"আওতাভুক্ত (Covered)": "#006A4E", "বাকি (Uncovered)": "#F42A41"})
                            st.plotly_chart(fig_pie, use_container_width=True)

                        # 4. Bar Chart
                        st.write("**Submissions by Division**")
                        div_counts = filtered_df['বিভাগ'].value_counts().reset_index()
                        div_counts.columns = ['Division', 'Count']
                        st.plotly_chart(px.bar(div_counts, x='Division', y='Count', text_auto=True, color_discrete_sequence=['#006A4E']), use_container_width=True)
    
                        # 5. Search Results Table
                        st.subheader("📋 Search Results")
                        st.dataframe(filtered_df, use_container_width=True)
    
                        # 6. Delete Logic
                        with st.expander("🗑️ Delete Data Entry"):
                            delete_index = st.number_input("Enter Row Index:", min_value=0, max_value=max(0, len(df_admin)-1), step=1)
                            if st.button("Confirm Delete"):
                                # ১. লোকাল ডাটাফ্রেম থেকে ড্রপ করা
                                df_admin = df_admin.drop(df_admin.index[delete_index])
                                
                                # ২. গুগল শিটে আপডেট পাঠানো
                                conn.update(data=df_admin)
                                
                                # ৩. গুরুত্বপূর্ণ: ক্যাশ মেমরি পরিষ্কার করা যাতে পরবর্তী রিড লাইভ হয়
                                st.cache_data.clear()
                                
                                st.success("Deleted!")
                                
                                # ৪. গুগল শিট সিঙ্ক হওয়ার জন্য ১ সেকেন্ড বিরতি দেওয়া
                                import time
                                time.sleep(1)
                                
                                # ৫. পেজ রিরান করে নতুন ডাটা দেখানো
                                st.rerun()
    
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
                
        elif pwd:
            st.sidebar.error('ভুল পাসওয়ার্ড')




if __name__ == "__main__":


    main()
       





















