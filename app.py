import streamlit as st
import requests
import json

# API Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Support Ticket Classifier", page_icon="🎫", layout="wide")

# Custom CSS for additional accent touches (10%)
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 2rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR (30% Secondary Area) -----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2082/2082875.png", width=80)
    st.markdown("## 📊 Sistem Kontrolü")
    
    try:
        health_res = requests.get(f"{API_URL}/health", timeout=2)
        if health_res.status_code == 200:
            st.success("🟢 API Aktif ve Çalışıyor")
        else:
            st.warning("🟠 API'de sorun var")
    except:
        st.error("🔴 API Kapalı (Çevrimdışı)")
        
    st.markdown("---")
    st.markdown("### 🏷️ Desteklenen Kategoriler")
    st.info("1. Teknik Sorun\n2. Fatura & Ödeme\n3. İade Talebi\n4. Hesap Yönetimi\n5. Genel Soru")
    
    st.markdown("### 🚨 Öncelik Seviyeleri")
    st.warning("Düşük, Orta, Yüksek, Kritik")

# ----------------- MAIN AREA (60% Dominant Area) -----------------
st.title("🎫 Yapay Zeka Destek Talebi Sınıflandırma")
st.markdown("Müşteriden gelen destek talebini aşağıya yapıştırın. Yapay zeka modelimiz talebin **kategorisini** ve **önceliğini** otomatik belirlesin.")

ticket_text = st.text_area("Müşteri Talebi (Açıklama)", height=250, placeholder="Müşterinin sorununu buraya yazın... (Örn: Dün aldığım ürünü iade etmek istiyorum, kargo kodunu bulamadım.)")

# 10% Accent (Button)
if st.button("🔮 Yapay Zeka ile Analiz Et"):
    if len(ticket_text) < 10:
        st.error("Lütfen daha detaylı bir açıklama girin (En az 10 karakter).")
    else:
        with st.spinner("Model tahmin yapıyor..."):
            try:
                response = requests.post(f"{API_URL}/predict", json={"text": ticket_text})
                if response.status_code == 200:
                    data = response.json()
                    st.toast('Analiz Başarılı!', icon='✅')
                    
                    # Sonuçları göster
                    col_cat, col_pri, col_conf = st.columns(3)
                    with col_cat:
                        st.metric(label="Kategori", value=data.get('category'))
                    with col_pri:
                        st.metric(label="Öncelik (Priority)", value=data.get('priority'))
                    with col_conf:
                        st.metric(label="Güven Skoru", value=f"%{int(data.get('confidence', 0)*100)}")
                    
                    if data.get('explanation'):
                        st.markdown("### 🧠 Model Karar Açıklaması (SHAP/LIME)")
                        st.json(data.get('explanation'))
                else:
                    st.error(f"API Hatası: {response.json().get('detail', 'Bilinmeyen hata')}")
            except Exception as e:
                st.error(f"Bağlantı hatası: {str(e)}. FastAPI sunucusunun çalıştığından emin olun.")
