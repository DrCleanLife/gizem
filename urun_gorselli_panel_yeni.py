import streamlit as st
import openai
import requests
import json
import replicate
from openai import OpenAI

# API anahtarlarını gizli olarak secrets üzerinden alıyoruz
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
SHOPIFY_STORE_URL = st.secrets["SHOPIFY_STORE_URL"]
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

st.set_page_config(page_title="AI Görselli Ürün Paneli", page_icon="🧠")
st.title("🧠 Görselli AI Ürün Paneli (OpenAI + Replicate + Shopify)")

trend = st.text_input("📈 Trend Konusu (örn: TikTok’ta viral olanlar)")

if "urunler" not in st.session_state:
    st.session_state.urunler = []

if st.button("🎯 3 Ürün Oluştur"):
    if not trend:
        st.warning("Lütfen trend konusu girin.")
    else:
        prompt = f"""
        '{trend}' konusuna göre 3 yaratıcı e-ticaret ürünü öner. Aşağıdaki formatta yalnızca JSON verisi döndür:

        [
          {{
            "urun_adi": "Minimalist LED Masa Lambası",
            "aciklama": "Estetik görünümlü, dokunmatik sensörlü LED masa lambası...",
            "seo_aciklama": "Modern evler için ideal minimalist LED masa lambası. TikTok’ta viral oldu."
          }}
        ]
        """
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            content = response.choices[0].message.content
            st.session_state.urunler = json.loads(content)
            st.success("✅ Ürünler başarıyla oluşturuldu!")
        except Exception as e:
            st.error("❌ GPT Hatası:")
            st.code(str(e))

# Ürünleri ve butonları listele
for i, urun in enumerate(st.session_state.urunler):
    with st.container():
        st.subheader(f"🛍️ {urun['urun_adi']}")
        st.write("📃", urun["aciklama"])
        st.write("🔍", urun["seo_aciklama"])

        # Görsel üret
     
replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
if st.button(f"🖼 Görsel Üret", key=f"gorsel_{i}"):
    try:
        with st.spinner("Görsel üretiliyor..."):
            output = replicate_client.run(
    "stability-ai/stable-diffusion-xl", 
    input={
        "prompt": f"{urun['urun_adi']}, {urun['aciklama']}, studio lighting, white background",
        "num_outputs": 1,
        "width": 512,
        "height": 512
    }
)

            urun["gorsel_url"] = output[0]
            st.image(output[0], caption="🖼 Üretilen Görsel", width=300)
            st.success("✅ Görsel başarıyla üretildi.")
    except Exception as e:
        st.error("❌ Replicate Hatası:")
        st.code(str(e))

        # Shopify’a yükle
        if st.button(f"📦 Shopify’a Yükle", key=f"yukle_{i}"):
            data = {
                "product": {
                    "title": urun["urun_adi"],
                    "body_html": f"{urun['aciklama']}<br>{urun['seo_aciklama']}",
                    "vendor": "DrCleanNano",
                    "product_type": "AI Ürün",
                    "tags": ["trend", "AI", "görselli"],
                    "images": [{"src": urun.get("gorsel_url", "")}],
                    "variants": [{
                        "price": "199.99",
                        "sku": f"AIGPT{i+1}",
                        "inventory_management": "shopify",
                        "inventory_quantity": 10
                    }]
                }
            }
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": ACCESS_TOKEN
            }
            r = requests.post(
                f"{SHOPIFY_STORE_URL}/products.json",
                headers=headers,
                data=json.dumps(data)
            )
            if r.status_code == 201:
                st.success("✅ Shopify’a başarıyla yüklendi!")
            else:
                st.error("❌ Shopify Hatası:")
                st.code(r.text)
