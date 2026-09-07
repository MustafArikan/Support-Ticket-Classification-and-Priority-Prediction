import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

# API Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Support Ticket Classifier", page_icon="📝", layout="centered")

# --- Language Dictionary ---
TRANSLATIONS = {
    "tr": {
        "title": "🎫 Yapay Zeka Destek Talebi Sınıflandırma",
        "desc": "Müşteriden gelen destek talebini aşağıya yapıştırın veya bir dosyadan içe aktarın. Yapay zeka modelimiz talebin kategorisini ve önceliğini otomatik belirlesin.",
        "sidebar_title": "⚙️ Ayarlar & Sistem",
        "lang_select": "🌐 Dil Seçimi (Language)",
        "sys_status": "📊 Sistem Kontrolü",
        "api_ok": "🟢 API Aktif ve Çalışıyor",
        "api_warn": "🟠 API'de sorun var",
        "api_err": "🔴 API Kapalı (Çevrimdışı)",
        "categories": "🏷️ Desteklenen Kategoriler",
        "cat_list": "1. Teknik Sorun\n2. Fatura & Ödeme\n3. İade Talebi\n4. Hesap Yönetimi\n5. Genel Soru",
        "priorities": "🚨 Öncelik Seviyeleri",
        "pri_list": "Düşük, Orta, Yüksek, Kritik",
        "input_label": "Müşteri Talebi (Açıklama)",
        "input_ph": "Müşterinin sorununu buraya yazın... (Örn: Dün aldığım ürünü iade etmek istiyorum, kargo kodunu bulamadım.)",
        "analyze_btn": "🔮 Yapay Zeka ile Analiz Et",
        "err_len": "Lütfen daha detaylı bir açıklama girin (En az 10 karakter).",
        "analyzing": "Model tahmin yapıyor...",
        "success": "Analiz Başarılı!",
        "cat_lbl": "Kategori",
        "pri_lbl": "Öncelik (Priority)",
        "conf_lbl": "Güven Skoru",
        "exp_title": "🧠 Model Karar Açıklaması",
        "err_api": "API Hatası",
        "err_conn": "Bağlantı hatası",
        "import_btn": "📂 Talep İçe Aktar (.txt, .csv)",
        "export_btn": "💾 Sonuçları Dışa Aktar",
    },
    "en": {
        "title": "🎫 AI Support Ticket Classification",
        "desc": "Paste a customer support ticket below or import from a file. Our AI model will automatically determine its category and priority.",
        "sidebar_title": "⚙️ Settings & System",
        "lang_select": "🌐 Language (Dil Seçimi)",
        "sys_status": "📊 System Status",
        "api_ok": "🟢 API is Online",
        "api_warn": "🟠 API has issues",
        "api_err": "🔴 API is Offline",
        "categories": "🏷️ Supported Categories",
        "cat_list": "1. Technical Issue\n2. Billing & Payment\n3. Refund Request\n4. Account Management\n5. General Inquiry",
        "priorities": "🚨 Priority Levels",
        "pri_list": "Low, Medium, High, Critical",
        "input_label": "Customer Ticket (Description)",
        "input_ph": "Type the customer issue here... (e.g., I want to return the product I bought yesterday, but I can't find the shipping code.)",
        "analyze_btn": "🔮 Analyze with AI",
        "err_len": "Please enter a more detailed description (at least 10 characters).",
        "analyzing": "Model is predicting...",
        "success": "Analysis Successful!",
        "cat_lbl": "Category",
        "pri_lbl": "Priority",
        "conf_lbl": "Confidence Score",
        "exp_title": "🧠 Model Explanation",
        "err_api": "API Error",
        "err_conn": "Connection error",
        "import_btn": "📂 Import Ticket (.txt, .csv)",
        "export_btn": "💾 Export Results",
    }
}

# --- State Initialization ---
if "lang" not in st.session_state:
    st.session_state.lang = "tr"
if "ticket_input" not in st.session_state:
    st.session_state.ticket_input = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2082/2082875.png", width=80)
    
    # Theme Toggle
    if st.button("🌓 Tema (Dark/Light)"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    # Language Toggle
    st.markdown(f"### {TRANSLATIONS[st.session_state.lang]['sidebar_title']}")
    lang_choice = st.radio(
        TRANSLATIONS[st.session_state.lang]['lang_select'],
        options=["Türkçe", "English"],
        index=0 if st.session_state.lang == "tr" else 1,
        horizontal=True
    )
    st.session_state.lang = "tr" if lang_choice == "Türkçe" else "en"
    t = TRANSLATIONS[st.session_state.lang]

    st.markdown("---")
    st.markdown(f"### {t['sys_status']}")
    try:
        health_res = requests.get(f"{API_URL}/health", timeout=2)
        if health_res.status_code == 200:
            st.success(t['api_ok'])
        else:
            st.warning(t['api_warn'])
    except:
        st.error(t['api_err'])
        
    st.markdown("---")
    st.markdown(f"### {t['categories']}")
    st.info(t['cat_list'])
    st.markdown(f"### {t['priorities']}")
    st.warning(t['pri_list'])

# --- Dynamic CSS ---
theme_css = ""
if st.session_state.theme == "dark":
    theme_css = """
    /* Dark Theme Overrides */
    .stApp {
        background-color: #0E1117 !important;
        color: #FAFAFA !important;
    }
    [data-testid="stSidebar"] {
        background-color: #262730 !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    h1, h2, h3, p, span, div, label {
        color: #FAFAFA !important;
    }
    [data-testid="stMetricValue"] {
        color: #818CF8 !important;
    }
    textarea {
        background-color: #1E1E1E !important;
        color: white !important;
    }
    """

st.markdown(f"""
<style>
    /* Global Styles & Spacing */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}
    /* Modern Gradient Button */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%);
        color: white !important;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 2rem;
        box-shadow: 0 4px 10px 0 rgba(99, 102, 241, 0.3);
        transition: all 0.2s ease;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 15px 0 rgba(99, 102, 241, 0.5);
    }}
    
    /* Metrics customization */
    div[data-testid="stMetric"] {{
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }}
    div[data-testid="stMetricValue"] {{
        color: #6366F1;
        font-weight: 700;
    }}
    {theme_css}
</style>
""", unsafe_allow_html=True)

# --- Main Area ---
st.title(t['title'])
st.markdown(t['desc'])

# UI Tabs for Single vs Batch Input
tab1, tab2 = st.tabs(["✍️ Tekli Giriş (Single)", "📂 Toplu Dosya (Batch Upload)"])

with tab1:
    ticket_text = st.text_area(
        t['input_label'], 
        value=st.session_state.ticket_input, 
        height=200, 
        placeholder=t['input_ph']
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_clicked = st.button(t['analyze_btn'], type="primary", key="single_analyze")
    
    if analyze_clicked:
        st.session_state.ticket_input = ticket_text # Save state
        if len(ticket_text) < 10:
            st.error(t['err_len'])
        else:
            with st.spinner(t['analyzing']):
                try:
                    response = requests.post(f"{API_URL}/predict", json={"text": ticket_text})
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.last_result = {
                            "text": ticket_text,
                            "category": data.get('category'),
                            "priority": data.get('priority'),
                            "confidence": data.get('confidence'),
                            "explanation": data.get('explanation')
                        }
                        st.toast(t['success'], icon='✅')
                    else:
                        st.error(f"{t['err_api']}: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"{t['err_conn']}: {str(e)}")
    
    # Display Results & Export (Single)
    if st.session_state.last_result:
        res = st.session_state.last_result
        st.markdown("---")
        
        col_cat, col_pri, col_conf = st.columns(3)
        with col_cat:
            st.metric(label=t['cat_lbl'], value=res['category'])
        with col_pri:
            st.metric(label=t['pri_lbl'], value=res['priority'])
        with col_conf:
            st.metric(label=t['conf_lbl'], value=f"%{int(res['confidence']*100)}")
        
        if res.get('explanation'):
            st.markdown(f"### {t['exp_title']}")
            st.json(res['explanation'])
    
        # Export Button (Download as JSON)
        json_result = json.dumps(res, indent=4, ensure_ascii=False)
        st.download_button(
            label=t['export_btn'],
            data=json_result,
            file_name="ticket_analysis_result.json",
            mime="application/json",
            key="single_download"
        )

with tab2:
    st.markdown("### 📂 Toplu Dosya Analizi (Batch Analysis)")
    st.info("Yüklediğiniz .csv veya .txt dosyasındaki tüm satırlar sırayla analiz edilecek ve tablo olarak sunulacaktır.")
    
    uploaded_file = st.file_uploader(t['import_btn'], type=["txt", "csv"], key="batch_upload")
    if uploaded_file is not None:
        texts = []
        if uploaded_file.name.endswith('.txt'):
            content = uploaded_file.getvalue().decode("utf-8")
            texts = [line.strip() for line in content.split('\n') if line.strip()]
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            text_col = None
            for col in ["body", "text", "description", "talepler", "mesaj"]:
                if col in df.columns:
                    text_col = col
                    break
            if not text_col and len(df.columns) > 0:
                text_col = df.columns[0]
            if text_col:
                texts = df[text_col].dropna().astype(str).tolist()
                
        if texts:
            st.success(f"✅ Dosya okundu! Toplam **{len(texts)}** adet kayıt bulundu.")
            if st.button("🚀 Tümünü Analiz Et (Analyze All)", type="primary", key="batch_analyze"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                
                for i, txt in enumerate(texts):
                    progress_bar.progress((i + 1) / len(texts))
                    status_text.text(f"Analiz ediliyor: {i+1} / {len(texts)}")
                    
                    try:
                        res = requests.post(f"{API_URL}/predict", json={"text": txt[:5000]}) # Limit text length for safety
                        if res.status_code == 200:
                            data = res.json()
                            results.append({
                                "Talep (Metin)": txt,
                                "Kategori": data.get("category"),
                                "Öncelik": data.get("priority"),
                                "Güven": f"%{int(data.get('confidence', 0)*100)}"
                            })
                        else:
                            results.append({"Talep (Metin)": txt, "Kategori": "Hata", "Öncelik": "-", "Güven": "-"})
                    except:
                        results.append({"Talep (Metin)": txt, "Kategori": "Bağlantı Hatası", "Öncelik": "-", "Güven": "-"})
                
                status_text.text("✅ Analiz tamamlandı!")
                
                res_df = pd.DataFrame(results)
                st.dataframe(res_df, use_container_width=True)
                
                csv_export = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Sonuçları İndir (Download CSV)",
                    data=csv_export,
                    file_name="batch_analysis_results.csv",
                    mime="text/csv",
                    key="batch_download"
                )
