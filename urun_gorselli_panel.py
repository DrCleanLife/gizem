import streamlit as st
import openai
import requests
import json
import replicate

# 🔐 API Anahtarları
openai.api_key = ""
replicate_api = ""
SHOPIFY_STORE_URL = "https://drclean-life.myshopify.com"
ACCESS_TOKEN = ""

# Replicate ayarları
replicate.Client(api_token=replicate_api)

# Sayfa başlığı
st.set_page_config(page_title="Görselli Ürün Paneli", page_icon="🧠")
st.title("🧠 Görselli AI Ürün Paneli")

trend = st.text_input("🧠 Trend Konusu (örn: TikTok'ta viral mutfak ürünleri)")

if "urunler" not in st.session_state:
    st.session_state.urunler = []

# Ürün oluştur
if st.button("🎯 3 Ürün Oluştur"):
    if not trend:
        st.warning("Lütfen trend konusu girin.")
    else:
        prompt = f"""
        '{trend}' konusuna göre 3 ürün fikri üret. Aşağıdaki JSON formatında:

        [
          {{
            "urun_adi": "Mini Meyve Sıkacağı",
            "aciklama": "Kompakt ve taşınabilir meyve sıkacağı...",
            "seo_aciklama": "TikTok’ta popüler mini meyve sıkacağı..."
          }},
          ...
        ]
        Sadece JSON verisi üret.
        """
        try:
            gpt = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            content = gpt['choices'][0]['message']['content']
            st.session_state.urunler = json.loads(content)
            st.success("✅ Ürünler oluşturuldu!")
        except Exception as e:
            st.error("❌ GPT Hatası:")
            st.code(str(e))

# Ürünleri göster
for i, urun in enumerate(st.session_state.urunler):
    with st.container():
        st.subheader(f"🛍️ Ürün {i+1}: {urun['urun_adi']}")
        st.write("📃", urun["aciklama"])
        st.write("🔍", urun["seo_aciklama"])

        # Görsel üret
        if st.button(f"🖼 Görsel Üret", key=f"gorsel_{i}"):
            try:
                with st.spinner("Görsel üretiliyor..."):
                    output = replicate.run(
                        "lucataco/realistic-product-photo:dbdd4e741ea7128b564d180cf6ee1a7e122b0f0f3eb4698f58cc53c84b7c8434",
                        input={
                            "prompt": f"{urun['urun_adi']}, {urun['aciklama']}, studio light, white background",
                            "width": 512,
                            "height": 512,
                            "num_outputs": 1
                        }
                    )
                    urun["gorsel_url"] = output[0]
                    st.image(output[0], caption="Üretilen Görsel", width=300)
                    st.success("✅ Görsel üretildi!")
            except Exception as e:
                st.error("❌ Replicate API hatası:")
                st.code(str(e))

        # Shopify’a yükle
        if st.button(f"📦 Shopify’a Yükle", key=f"yukle_{i}"):
            data = {
                "product": {
                    "title": urun["urun_adi"],
                    "body_html": f"{urun['aciklama']}<br>{urun['seo_aciklama']}",
                    "vendor": "DrCleanNano",
                    "product_type": "AI Görselli Ürün",
                    "tags": ["trend", "AI", "görselli"],
                    "images": [{"src": urun.get("gorsel_url", "")}],
                    "variants": [{
                        "price": "199.99",
                        "sku": f"AIGRS{i+1}",
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
                st.success("✅ Shopify’a yüklendi!")
            else:
                st.error("❌ Shopify hata:")
                st.code(response.text)
