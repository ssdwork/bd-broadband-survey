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
st.set_page_config(page_title="ব্রডব্যান্ড কভারেজ জরিপ", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    
    /* 1. Main Background - White with Watermark */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)),
            url('https://static.vecteezy.com/system/resources/thumbnails/072/508/275/small/a-highly-detailed-shot-of-a-server-rack-s-back-panel-showing-the-organized-chaos-of-cables-and-ports-free-photo.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }

    /* 2. Global Text Color - Black */
    html, body, [class*="css"], .stMarkdown, p, label, .stTextInput > label, .stNumberInput > label { 
        font-family: 'Calibri', 'Nikosh', sans-serif; 
        color: #000000 !important; 
        font-weight: 700 !important; 
        font-size: 14px !important;
    }
    
    /* 3. Headers and Metrics */
    h1, h2, h3, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #000000 !important;
    }

    /* 4. Input Fields - Force White Theme (Fix for Dark Mode Visibility) */
    
    /* Text Color & Cursor */
    div[data-baseweb="input"] input, 
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span,
    div[data-baseweb="base-input"] {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        text-shadow: none !important;
        font-weight: 400 !important;
        font-size: 14px !important;
        padding: 0px 5px !important;
        background-color: transparent !important; /* Inherit from container */
    }

    /* Input Container Background */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] { 
        background-color: #FFFFFF !important; 
        border: 1px solid #006400 !important; 
        border-radius: 8px !important; 
        min-height: 30px !important;
    }
    
    /* Dropdown Menu & Options Fix */
    ul[data-baseweb="menu"], div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
    }
    li[data-baseweb="option"] {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }

    /* ৫. Sidebar - Light Gray */
    [data-testid="stSidebar"] { 
        background-color: #F8F9FA !important; 
        border-right: 1px solid #E6E6E6;
    }

    /* সাইডবারের ভেতরের সব লেখা কালো */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #000000 !important;
        font-size: 14px !important;
        font-weight: 700 !important;
    }

    /* 6. Buttons */
    div.stButton > button { 
        color: #006400 !important; 
        border: 1px solid #006400 !important; 
        background-color: #FFFFFF !important; 
        font-weight: 600 !important; 
        border-radius: 6px !important;
        font-size: 14px !important;
        padding: 0px 10px !important;
        min-height: 30px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        background-color: #006400 !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 100, 0, 0.4) !important;
    }
    div.stButton > button[kind="primary"] { 
        background: linear-gradient(to bottom, #007bff, #0056b3) !important; 
        color: #FFFFFF !important; 
        border: none !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3) !important;
        font-size: 14px !important;
    }
    div.stButton > button[kind="primary"] p {
        color: #FFFFFF !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(to bottom, #0056b3, #004085) !important;
        box-shadow: 0 6px 15px rgba(0, 123, 255, 0.5) !important;
        transform: scale(1.02) !important;
    }

    /* 7. Custom Classes */
    .main-title { 
        color: #006400 !important; 
        text-align: center; 
        font-size: 1.4rem !important; 
        font-weight: 700; 
        border-bottom: 3px solid #F42A41; 
        padding-bottom: 5px; 
        display: inline-block;
    }
    .section-head { 
        color: #006400 !important; 
        font-weight: 700; 
        margin: 5px 0 2px 0; 
        border-bottom: 2px solid #006400; 
        font-size: 16px !important;
        padding-bottom: 5px;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* হেডার পুরোপুরি হাইড না করে সেটিকে ট্রান্সপারেন্ট করা */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        height: 3rem !important; /* বাটনের জন্য জায়গা রাখা */
    }

    /* Chevron বাটনটি সবসময় দৃশ্যমান এবং ক্লিকযোগ্য রাখা */
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: inline-flex !important;
        background-color: rgba(0, 100, 0, 0.1) !important; /* হালকা সবুজ ব্যাকগ্রাউন্ড */
        border: 1px solid #006400 !important;
        border-radius: 50% !important;
        color: #006400 !important;
        z-index: 999999 !important;
    }

    /* অটোমেটিক নেভিগেশন লিস্ট লুকানো */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* Reduce top padding of the main container to save space */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 99% !important;
    }
    
    /* Reduce gap between vertical elements */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.3rem !important;
    }
    
    /* Toast Message Styling - Clean White */
    div[data-testid="stToast"] {
        background-color: #FFFFFF !important;
        border: 2px solid #F42A41 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stToast"] div, div[data-testid="stToast"] p {
        color: #000000 !important;
        text-shadow: none !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
""", unsafe_allow_html=True)

def main():
    # Google Sheets Connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Header with Logos (ICT Division Left, BCC Right)
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
            <div style="flex: 0 0 100px; text-align: left;">
                <img src="https://raw.githubusercontent.com/ssdwork/bd-broadband-survey/main/Ict Division Logo Vector.svg" style="height: 70px; width: auto;" title="ICT Division">
            </div>
            <div style="flex: 1; text-align: center;">
                <div class="main-title"> সমগ্র বাংলাদেশের ব্রডব্যান্ড কভারেজ জরিপ</div>
            </div>
            <div style="flex: 0 0 100px; text-align: right;">
                <img src="https://raw.githubusercontent.com/ssdwork/bd-broadband-survey/main/Bangladesh_Computer_Council_Logo.svg" style="height: 45px; width: auto;" title="Bangladesh Computer Council">
            </div>
        </div>
    """, unsafe_allow_html=True)

    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("তথ্য প্রদানকারী কর্মকর্তার নাম (Name) *", key="user_name") 
        
        # পদবীর তালিকা
        desig_list = [
            "প্রোগ্রামার", "মেইনটেন্যান্স ইঞ্জিনিয়ার", 
            "নেটওয়ার্ক ইঞ্জিনিয়ার", "সহকারী পরিচালক", "সহকারী প্রোগ্রামার", 
            "সহকারী মেইনটেন্যান্স ইঞ্জিনিয়ার", "সহকারী নেটওয়ার্ক ইঞ্জিনিয়ার", 
            "ওয়েবসাইট এ্যাডমিনিস্ট্রেটর", "ডাটা এন্ট্রি/কন্ট্রোল সুপারভাইজার", "কম্পিউটার অপারেটর", 
            "ডাটা এন্ট্রি/কন্ট্রোল অপারেটর", "অফিস সহকারী কাম কম্পিউটার অপারেটর"
        ]
    
    with c2:
        # ড্রপডাউন তৈরি
        selected_desig = st.selectbox(
            "পদবী (Designation) *", 
            ["-- নির্বাচন করুন --"] + desig_list + ["অন্যান্য"], 
            key="desig_select"
        )
        
        # 'অন্যান্য' সিলেক্ট করলে ইনপুট বক্স আসবে, নাহলে ড্রপডাউনের ভ্যালু নেবে
        if selected_desig == "অন্যান্য":
            designation = st.text_input("আপনার পদবী লিখুন *", key="desig_other_input")
        elif selected_desig == "-- নির্বাচন করুন --":
            designation = "" # কিছুই সিলেক্ট না করলে খালি থাকবে
        else:
            designation = selected_desig
            
    with c3:
        workplace = st.text_input("কর্মস্থলের নাম (Workplace Name) *", key="workplace_input")

    st.markdown('<div class="section-head">উপজেলা ও ইউনিয়নের তথ্য</div>', unsafe_allow_html=True)
    
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        div_list = list(BD_DATA.keys())
        final_div = smart_geo_input('বিভাগ (Division)', div_list, 'geo_div')
    with g2:
        dist_opts = list(BD_DATA[final_div].keys()) if final_div in BD_DATA else []
        final_dist = smart_geo_input('জেলা (District)', dist_opts, 'geo_dist')
    with g3:
        upz_opts = list(BD_DATA[final_div][final_dist].keys()) if (final_div in BD_DATA and final_dist in BD_DATA[final_div]) else []
        final_upz = smart_geo_input('উপজেলা (Upazila)', upz_opts, 'geo_upz')
    with g4:
        uni_opts = BD_DATA[final_div][final_dist][final_upz] if (final_div in BD_DATA and final_dist in BD_DATA[final_div] and final_upz in BD_DATA[final_div][final_dist]) else []
        final_uni = smart_geo_input('ইউনিয়ন (Union)', uni_opts, 'geo_uni')

    # ব্রডব্যান্ড ও গ্রামের তথ্য এক লাইনে
    gv1, gv2, gv3 = st.columns(3)
    with gv1:
        is_broadband = st.selectbox("ইউনিয়নটি কি ব্রডব্যান্ড এর আওতাভুক্ত? *", ["-- নির্বাচন করুন --", "হ্যাঁ", "না"], key="bb_coverage")
    with gv2:
        total_villages = st.number_input("ইউনিয়নে মোট গ্রামের সংখ্যা", min_value=0, step=1, key="total_v")
    with gv3:
        covered_villages = st.number_input("ব্রডব্যান্ড ইন্টারনেটের আওতাভুক্ত গ্রামের সংখ্যা", min_value=0, max_value=total_villages, step=1, key="covered_v")

    # NTTN Section
    st.markdown('<div class="section-head">উপজেলাতে বিদ্যমান NTTN</div>', unsafe_allow_html=True)
    nttn_opts = ["সামিট", "ফাইবার@হোম", "বিটিসিএল", "বাহন", "অন্যান্য"]
    nttn_cols = st.columns(5)
    nttn_vars = {}
    for i, opt in enumerate(nttn_opts):
        with nttn_cols[i]:
            nttn_vars[opt] = st.checkbox(opt, key=f"nttn_chk_{i}")
    
    nttn_other_val = ""
    if nttn_vars["অন্যান্য"]:
        nttn_other_val = st.text_input("অন্যান্য (লিখুন)", key="nttn_other_input")

    st.markdown('<div class="section-head">উপজেলাতে সেবা প্রদানকৃত ISP এর তথ্য</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 13px !important; color: #F42A41; margin-top: 2px; margin-bottom: 5px; font-weight: 400 !important;'>⚠️ সতর্কতা: একটি উপজেলার বিপরীতে একবার ISP তথ্য প্রদান করাই যথেষ্ট। নতুন ইউনিয়নের তথ্য দেওয়ার সময় পুনরায় ISP এন্ট্রি এড়িয়ে চলুন।</div>", unsafe_allow_html=True)
    isp_records = []
    for i in range(st.session_state.rows):
        st.markdown(f"**ISP নং {i+1}**")
        ic1, ic2, ic3 = st.columns([3, 2, 2])
        with ic1: 
            iname = st.text_input("ISP নাম", key=f"in_{i}")
        with ic2: 
                icontact = st.text_input("যোগাযোগের নম্বর", key=f"ic_{i}")
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

    # ISP Controls Row: Add Button, Remove Button
    _, ic_add, ic_remove = st.columns([5, 1.5, 1])
    with ic_add:
        if st.button("➕ আরও ISP যোগ করুন", use_container_width=True):
            st.session_state.rows += 1
            st.rerun()
    with ic_remove:
        if st.button("➖ বাদ দিন", use_container_width=True) and st.session_state.rows > 1:
            st.session_state.rows -= 1
            st.rerun()
    
    c_isp_total, _ = st.columns([1, 3])
    with c_isp_total:
        total_isp_count = st.number_input("মোট ISP সংখ্যা", min_value=0, step=1, key="total_isp_count_input")


    # Replace the Submission logic in your main() function with this:

    _, c_sub, _ = st.columns([3, 2, 3])
    with c_sub:
        submit_btn = st.button("জমা দিন (Submit Data)", use_container_width=True, type="primary")

    if submit_btn:
        # ১. সব নম্বরের দৈর্ঘ্য চেক করা
        all_numbers_valid = all(len(r['phone']) == 11 and r['phone'].isdigit() for r in isp_records)
        
        # ২. মিসিং ফিল্ড চেক করা
        missing_fields = []
        if not name: missing_fields.append("তথ্য প্রদানকারী কর্মকর্তার নাম (Name) *")
        if not designation: missing_fields.append("পদবী (Designation) *")
        if not workplace: missing_fields.append("কর্মস্থলের নাম (Workplace Name) *")
        if not final_div: missing_fields.append("বিভাগ (Division)")
        if not final_dist: missing_fields.append("জেলা (District)")
        if not final_upz: missing_fields.append("উপজেলা (Upazila)")
        if not final_uni: missing_fields.append("ইউনিয়ন (Union)")
        if is_broadband == "-- নির্বাচন করুন --": missing_fields.append("ইউনিয়নটি কি ব্রডব্যান্ড এর আওতাভুক্ত? *")
        
        # ৩. যদি কোনো ফিল্ড মিসিং থাকে
        if missing_fields:
            st.toast("দয়া করে বাকি ফিল্ডগুলো পূরণ করুন!", icon="⚠️")
            
            # ডাইনামিক CSS জেনারেট করে লাল বর্ডার দেওয়া
            error_style = "<style>"
            for label in missing_fields:
                # Text Input এবং Selectbox এর জন্য CSS সিলেক্টর (aria-label দিয়ে টার্গেট করা)
                error_style += f"""
                div[data-testid="stTextInput"]:has(input[aria-label="{label}"]) div[data-baseweb="input"],
                div[data-testid="stSelectbox"]:has(input[aria-label="{label}"]) div[data-baseweb="select"] {{
                    border: 1px solid #F42A41 !important;
                }}
                """
            error_style += "</style>"
            st.markdown(error_style, unsafe_allow_html=True)
            
        elif not all_numbers_valid:
            st.toast("❌ ISP যোগাযোগের নম্বর সঠিক নয় (১১ ডিজিট ও শুধুমাত্র সংখ্যা হতে হবে)।", icon="❌")
        else:
            try:
                # ১. ডাটা প্রিপেয়ার করা
                isp_final = " | ".join([f"{r['name']}({r['phone']}):{r['subs']}" for r in isp_records])
                
                # NTTN Data Prepare
                nttn_list = [k for k, v in nttn_vars.items() if v and k != "অন্যান্য"]
                if nttn_vars["অন্যান্য"]:
                    nttn_list.append(f"অন্যান্য({nttn_other_val})")
                nttn_final = ", ".join(nttn_list)
                
                new_record = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "নাম": name,
                    "পদবী": designation,
                    "কর্মস্থল": workplace,
                    "বিভাগ": final_div,
                    "জেলা": final_dist,
                    "উপজেলা": final_upz,
                    "ইউনিয়ন": final_uni,
                    "উপজেলাতে বিদ্যমান NTTN": nttn_final,
                    "ব্রডব্যান্ড আওতাভুক্ত": is_broadband,
                    "মোট গ্রাম": total_villages,
                    "আওতাভুক্ত গ্রাম": covered_villages,
                    "ISP মোট সংখ্যা": total_isp_count,
                    "উপজেলাতে ISP তথ্য": isp_final
                }])
                
                # ২. গুগল শিটে আপডেট পাঠানো
                existing_data = conn.read(ttl=0)
                if existing_data is not None and not existing_data.empty:
                    updated_df = pd.concat([existing_data, new_record], ignore_index=True)
                else:
                    updated_df = new_record
                
                conn.update(data=updated_df)
                
                
                # ৩. ইউজার ফিডব্যাক
                st.balloons() # বেলুন অ্যানিমেশন আগের মতোই 
                
                # কাস্টম সাকসেস মেসেজ তৈরি
                success_message = """
                    <div style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0, 0, 0, 0.6);
                        z-index: 999999;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <div style="
                            background-color: #FFFFFF;
                            padding: 40px;
                            border-radius: 20px;
                            border: 3px solid #006400;
                            text-align: center;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                            max-width: 500px;
                            width: 90%;
                        ">
                            <h1 style="color: #006400; font-family: 'Calibri', 'Nikosh', sans-serif; font-size: 40px; margin: 0; font-weight: 700;">
                                ✅ সফলভাবে সংরক্ষিত হয়েছে!
                            </h1>
                            <p style="color: #000000; font-size: 20px; margin-top: 15px; font-weight: 500;">
                                আপনার তথ্য ডাটাবেজে জমা হয়েছে। 
                            </p>
                        </div>
                    </div>
                """
                
                # মেসেজটি দেখানোর জন্য একটি Placeholder ব্যবহার করা
                placeholder = st.empty()
                placeholder.markdown(success_message, unsafe_allow_html=True)
                
                # ১০ সেকেন্ড ধরে মেসেজটি দেখানো
                import time
                time.sleep(5)
                
                # ১০ সেকেন্ড পর মেসেজটি মুছে ফেলা
                placeholder.empty()
                
                # ৪. পেজটি পুরোপুরি রিলোড করা 
                st.components.v1.html(
                    "<script>window.parent.location.reload();</script>",
                    height=0,
                )
                
               # --- ৪. ২ নম্বর ও ৩ নম্বর সেকশন রিসেট করার চূড়ান্ত লজিক ---
                
                # ২ নম্বর সেকশন: ইউনিয়ন ও গ্রামের তথ্য ক্লিয়ার করা
                if "bb_coverage" in st.session_state:
                    st.session_state["bb_coverage"] = "-- নির্বাচন করুন --"
                
                # গুরুত্বপূর্ণ: আগে total_v এবং covered_v কে সরাসরি ০ করে দিতে হবে
                st.session_state["total_v"] = 0
                st.session_state["covered_v"] = 0
                st.session_state["total_isp_count_input"] = 0

                # NTTN Reset
                for i in range(len(nttn_opts)):
                    st.session_state[f"nttn_chk_{i}"] = False
                if "nttn_other_input" in st.session_state:
                    del st.session_state["nttn_other_input"]

                # ৩ নম্বর সেকশন: ISP তথ্য পুরোপুরি মুছে ফেলা
                #  সেশন স্টেট থেকে সব ISP ডাইনামিক কি (Key) মুছে ফেলা
                current_keys = list(st.session_state.keys())
                for key in current_keys:
                    if any(prefix in key for prefix in ["in_", "ic_", "is_", "un_subs_", "is_dis_"]):
                        del st.session_state[key]

                # রো সংখ্যা ১-এ নামিয়ে আনা
                st.session_state.rows = 1
                
                # ৬. পেজ রিরান (ডাটা ক্লিয়ার করার জন্য এটি আবশ্যিক)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error during submission: {e}")
                
    # --- ADMIN PANEL ---
    st.sidebar.markdown("---")
if st.sidebar.button("🔐 Admin Login"):
    st.switch_page("pages/admin_panel.py")

if __name__ == "__main__":


    main()
       
