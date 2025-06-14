import streamlit as st
import openai
import requests
import json

# 🔐 API Anahtarları (KENDİ BİLGİLERİNİ GİR)
openai.api_key = "sk-..."  # OpenAI Key'in
SHOPIFY_STORE_URL = "https://drclean-life.myshopify.com"
ACCESS_TOKEN = "shpat_..."  # Shopify Access Token

# Sayfa başlığı
st.set_page_config(page_title="Toplu Ürün Paneli", page_icon="📦")
st.title("📦 AI ile Toplu Ürün Üretimi ve Shopify'a Yükleme")

# Trend konusu al
trend = st.text_input("🧠 Trend Konusu Girin (örn: TikTok mutfak ürünleri)")

# Ürün listesi session'da saklanıyor
if "urunler" not in st.session_state:
    st.session_state.urunler = []

# ÜRÜN OLUŞTUR
if st.button("🎯 3 Ürün Oluştur"):
    if not trend:
        st.warning("Lütfen bir trend konusu girin.")
    else:
        prompt = f"""
        '{trend}' konusuna göre 3 farklı trend ürünü aşağıdaki JSON formatında üret:

        [
          {{
            "urun_adi": "Mini Meyve Sıkacağı",
            "aciklama": "Bu ürün taşınabilir meyve suyu hazırlamak için idealdir...",
            "seo_aciklama": "TikTok'ta popüler olan bu mini meyve sıkacağı ile taze içeceklerin keyfini çıkarın..."
          }},
          ...
        ]

        Sadece JSON verisi üret. Açıklama ekleme.
        """
        try:
            gpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            content = gpt_response['choices'][0]['message']['content']
            urunler = json.loads(content)
            st.session_state.urunler = urunler
            st.success("✅ Ürünler başarıyla oluşturuldu!")
        except Exception as e:
            st.error("❌ GPT Hatası:")
            st.code(str(e))

# Ürünleri listele ve yükleme seçenekleri
for i, urun in enumerate(st.session_state.urunler):
    with st.container():
        st.subheader(f"🛍️ Ürün {i+1}: {urun['urun_adi']}")
        st.write("📃", urun["aciklama"])
        st.write("🔍", urun["seo_aciklama"])
        if st.button(f"📦 Bu Ürünü Shopify’a Yükle", key=f"yukle_{i}"):
            data = {
                "product": {
                    "title": urun["urun_adi"],
                    "body_html": f"{urun['aciklama']}<br><br>{urun['seo_aciklama']}",
                    "vendor": "DrCleanNano",
                    "product_type": "Toplu AI Ürünü",
                    "tags": ["trend", "toplu", "AI"],
                    "variants": [{
                        "price": "199.99",
                        "sku": f"TOPLUAI{i+1}",
                        "inventory_management": "shopify",
                        "inventory_quantity": 10
                    }]
                }
            }
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": ACCESS_TOKEN
            }
            response = requests.post(
                f"{SHOPIFY_STORE_URL}/admin/api/2023-10/products.json",
                headers=headers,
                data=json.dumps(data)
            )
            if response.status_code == 201:
                st.success("✅ Shopify'a yüklendi!")
            else:
                st.error("❌ Shopify hata:")
                st.code(response.text)

# TÜMÜNÜ YÜKLE
if st.session_state.urunler:
    if st.button("🚀 Tüm Ürünleri Shopify’a Yükle"):
        for i, urun in enumerate(st.session_state.urunler):
            data = {
                "product": {
                    "title": urun["urun_adi"],
                    "body_html": f"{urun['aciklama']}<br><br>{urun['seo_aciklama']}",
                    "vendor": "DrCleanNano",
                    "product_type": "Toplu AI Ürünü",
                    "tags": ["trend", "toplu", "AI"],
                    "variants": [{
                        "price": "199.99",
                        "sku": f"TOPLUAI{i+1}",
                        "inventory_management": "shopify",
                        "inventory_quantity": 10
                    }]
                }
            }
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": ACCESS_TOKEN
            }
            requests.post(
                f"{SHOPIFY_STORE_URL}/admin/api/2023-10/products.json",
                headers=headers,
                data=json.dumps(data)
            )
        st.success("✅ Tüm ürünler Shopify'a başarıyla yüklendi!")
