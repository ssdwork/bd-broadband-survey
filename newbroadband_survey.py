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
st.set_page_config(page_title="ব্রডব্যান্ড কভারেজ জরিপ", page_icon="🌐", layout="centered", initial_sidebar_state="collapsed")

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

    /* 4. Input Fields & Text Stroke - High Visibility Fix */
    
    div[data-baseweb="input"] input, 
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {
        /* টেক্সট কালার সাদা থাকবে */
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
        
        /*  টেক্সটের চারপাশ কালো বর্ডার (Stroke) দিয়ে ঘেরা */
        text-shadow: 
            -1px -1px 0 #000,  
             1px -1px 0 #000,
            -1px  1px 0 #000,
             1px  1px 0 #000,
             2px  2px 2px rgba(0,0,0,0.8); /*  শ্যাডো যাতে আরও ফুটে ওঠে */
             
        font-weight: 700 !important;
    }

    /* বক্সের ব্যাকগ্রাউন্ড লাইট মোডেও স্পষ্ট রাখার জন্য সামান্য ধূসর */
    div[data-baseweb="input"], div[data-baseweb="select"] { 
        background-color: rgba(255, 255, 255, 0.2) !important; /* হালকা স্বচ্ছ ব্যাকগ্রাউন্ড */
        border: 2px solid #00D487 !important; 
        border-radius: 8px !important; 
        backdrop-filter: blur(5px); /* ব্যাকগ্রাউন্ড ব্লার ইফেক্ট */
    }

    /* ৫. Sidebar - সাইডবার যেন সবসময় পড়া যায় */
    [data-testid="stSidebar"] { 
        background-color: #1E1E1E !important; /* ফিক্সড ডার্ক ব্যাকগ্রাউন্ড */
        border-right: 1px solid #333;
    }

    /* সাইডবারের ভেতরের সব লেখা সাদা */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
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
    
    /* হেডার পুরোপুরি হাইড না করে সেটিকে ট্রান্সপারেন্ট করা */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        height: 3rem !important; /* বাটনের জন্য জায়গা রাখা */
    }

    /* Chevron বাটনটি সবসময় দৃশ্যমান এবং ক্লিকযোগ্য রাখা */
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: inline-flex !important;
        background-color: rgba(0, 212, 135, 0.1) !important; /* হালকা সবুজ ব্যাকগ্রাউন্ড */
        border: 1px solid #00D487 !important;
        border-radius: 50% !important;
        color: #00D487 !important;
        z-index: 999999 !important;
    }

    /* অটোমেটিক নেভিগেশন লিস্ট লুকানো */
    [data-testid="stSidebarNav"] {display: none !important;}
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
        name = st.text_input("নাম (Name) *", key="user_name") 
        
        # পদবীর তালিকা
        desig_list = [
            "মহাপরিচালক", "অতিরিক্ত মহাপরিচালক", "পরিচালক", "উপপরিচালক", 
            "সিস্টেমস ম্যানেজার", "সিনিয়র সিস্টেম এনালিস্ট", "সিনিয়র মেইনটেন্যান্স ইঞ্জিনিয়ার", 
            "সিনিয়র প্রোগ্রামার", "প্রোগ্রামার", "সিস্টেম এনালিস্ট", "মেইনটেন্যান্স ইঞ্জিনিয়ার", 
            "নেটওয়ার্ক ইঞ্জিনিয়ার", "সহকারী পরিচালক", "সহকারী প্রোগ্রামার (উপজেলা পর্যায়)", 
            "সহকারী মেইনটেন্যান্স ইঞ্জিনিয়ার", "সহকারী নেটওয়ার্ক ইঞ্জিনিয়ার", 
            "ওয়েবসাইট এ্যাডমিনিস্ট্রেটর", "ডাটা এন্ট্রি/কন্ট্রোল সুপারভাইজার", "কম্পিউটার অপারেটর", 
            "ডাটা এন্ট্রি/কন্ট্রোল অপারেটর", "অফিস সহকারী কাম কম্পিউটার অপারেটর", "উচ্চমান সহকারী", 
            "ব্যক্তিগত সহকারী", "হিসাবরক্ষক", "ক্যাশিয়ার", "স্টোর কিপার", "ল্যাব এ্যাটেন্ডেন্ট"
        ]
        
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
    with col2:
        
        # কর্মস্থলের নাম ও উদাহরণের লেবেল (সঠিক স্পেসিং সহ)
        st.markdown("""
            <div style="margin-top: 10px; margin-bottom: 15px;"> 
                <label style="font-size: 14px; font-weight: 500; color: white; font-family: 'Hind Siliguri', sans-serif;">
                    কর্মস্থলের নাম (Workplace Name) *
                </label>
                <div style="font-size: 0.85rem; color: #00D487; font-weight: 500;">
                    Example: উপজেলা অফিস, জেলা অফিস
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # ইনপুট বক্স (লেবেল হাইড করা, কারণ উপরে আমরা কাস্টম লেবেল দিয়েছি)
        workplace = st.text_input("", key="workplace_input", label_visibility="collapsed")

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
    is_broadband = st.selectbox("ইউনিয়নটি কি ব্রডব্যান্ড এর আওতাভুক্ত? *", ["-- নির্বাচন করুন --", "হ্যাঁ", "না"], key="bb_coverage")
    
    st.write("##")
    
    # গ্রামের সংখ্যা ইনপুট (সম্পূর্ণ স্পেস দিয়ে ইনডেন্ট করা)
    gv1, gv2 = st.columns(2)
    with gv1:
        total_villages = st.number_input("ইউনিয়নে মোট গ্রামের সংখ্যা", min_value=0, step=1, key="total_v")
    with gv2:
        covered_villages = st.number_input("ব্রডব্যান্ড ইন্টারনেটের আওতাভুক্ত গ্রামের সংখ্যা", min_value=0, max_value=total_villages, step=1, key="covered_v")

    st.markdown('<div class="section-head">৩. উপজেলাতে সেবা প্রদানকৃত ISP এর তথ্য</div>', unsafe_allow_html=True)
    isp_records = []
    for i in range(st.session_state.rows):
        st.markdown(f"**ISP নং {i+1}**")
        ic1, ic2, ic3 = st.columns([3, 2, 2])
        with ic1: iname = st.text_input("ISP নাম", key=f"in_{i}")
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
        # ১. সব নম্বরের দৈর্ঘ্য চেক করা
        all_numbers_valid = all(len(r['phone']) == 11 and r['phone'].isdigit() for r in isp_records)
        
        if not (name and final_div and final_dist):
            st.error("দয়া করে নাম এবং ভৌগোলিক তথ্য নিশ্চিত করুন।")
        elif not all_numbers_valid:
            st.error("❌ ISP যোগাযোগের নম্বর সঠিক নয় (১১ ডিজিট ও শুধুমাত্র সংখ্যা হতে হবে)।")
        else:
            try:
                # ১. ডাটা প্রিপেয়ার করা
                isp_final = " | ".join([f"{r['name']}({r['phone']}):{r['subs']}" for r in isp_records])
                
                new_record = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "নাম": name,
                    "পদবী": designation,
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
                
                # ২. গুগল শিটে আপডেট পাঠানো
                existing_data = conn.read(ttl=0)
                if existing_data is not None and not existing_data.empty:
                    updated_df = pd.concat([existing_data, new_record], ignore_index=True)
                else:
                    updated_df = new_record
                
                conn.update(data=updated_df)
                
                
                # ৩. ইউজার ফিডব্যাক
                st.balloons() # বেলুন অ্যানিমেশন আগের মতোই থাকছে
                
                # বড় এবং কাস্টম সাকসেস মেসেজ তৈরি
                success_message = """
                    <div style="
                        background-color: rgba(0, 212, 135, 0.15);
                        padding: 40px;
                        border-radius: 20px;
                        border: 3px solid #00D487;
                        text-align: center;
                        margin: 25px 0;
                    ">
                        <h1 style="color: #00D487; font-family: 'Hind Siliguri', sans-serif; font-size: 45px; margin: 0; font-weight: 700;">
                            ✅ সফলভাবে সংরক্ষিত হয়েছে!
                        </h1>
                        <p style="color: white; font-size: 22px; margin-top: 15px; font-weight: 500;">
                            আপনার তথ্য ডাটাবেজে জমা হয়েছে। 
                        </p>
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
                
                # ৪. পেজটি পুরোপুরি রিলোড করা (এটিই আপনার চাওয়া কমান্ড)
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

                # ৩ নম্বর সেকশন: ISP তথ্য পুরোপুরি মুছে ফেলা
                # আমরা সেশন স্টেট থেকে সব ISP ডাইনামিক কি (Key) মুছে ফেলব
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
       
























































