import streamlit as st
import openai
import requests
import replicate
import time

st.set_page_config(page_title="🧠 AI Görselli Ürün Paneli", layout="wide")

st.title("🧠 Görselli AI Ürün Paneli (OpenAI + Replicate + Shopify)")
st.markdown("#### 🧾 Trend Konusu (örn: TikTok'ta viral olanlar)")
trend_konu = st.text_input("📌 Trend Konusu")

if st.button("🍭 3 Ürün Oluştur"):
    try:
        with st.spinner("Ürünler oluşturuluyor..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": f"'{trend_konu}' trendine uygun 3 yaratıcı ürün öner ve her biri için şu formatta sadece JSON ver: [{{'urun_adi': '', 'aciklama': '', 'seo_aciklama': ''}}]"
                }],
                temperature=0.7
            )
            urunler = eval(response.choices[0].message.content)
            st.session_state.urunler = urunler
            st.success("✅ Ürünler başarıyla oluşturuldu!")
    except Exception as e:
        st.error("❌ GPT Hatası:")
        st.code(str(e))

# Ürünleri ve butonları listele
for i, urun in enumerate(st.session_state.urunler if "urunler" in st.session_state else []):
    with st.container():
        st.subheader(f"📦 {urun['urun_adi']}")
        st.write("📃", urun["aciklama"])
        st.write("🔍", urun["seo_aciklama"])

        # Görsel üret
        replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])

        if st.button(f"🖼️ Görsel Üret", key=f"gorsel_{i}"):
            try:
                with st.spinner("Görsel üretiliyor..."):
                    output = replicate_client.run(
                        "stability-ai/stable-diffusion-xl:latest",
                        input={
                            "prompt": f"{urun['urun_adi']}, {urun['aciklama']}, studio lighting, white background",
                            "num_outputs": 1,
                            "width": 512,
                            "height": 512
                        }
                    )
                urun["gorsel_url"] = output[0]
                st.image(output[0], caption="🖼️ Üretilen Görsel", width=300)
                st.success("✅ Görsel başarıyla üretildi.")

                time.sleep(10)  # ⚠️ Rate limit önlemi

            except Exception as e:
                st.error(f"❌ Replicate Hatası:")
                st.code(str(e))

        # Shopify'a yükle
        if st.button(f"🛒 Shopify'a Yükle", key=f"yukle_{i}"):
            try:
                veri = {
                    "product": {
                        "title": urun["urun_adi"],
                        "body_html": f"{urun['aciklama']}<br>{urun['seo_aciklama']}",
                        "vendor": "DrCleanNano",
                        "product_type": "AI Ürünü",
                        "tags": ["trend", "tiktok", "yeni"],
                        "images": [{"src": urun.get("gorsel_url", "")}],
                        "variants": [{
                            "price": "149.90",
                            "sku": f"AI-{i+1}"
                        }]
                    }
                }
                yanit = requests.post(
                    url=f"{st.secrets['SHOPIFY_STORE_URL']}/admin/api/2023-10/products.json",
                    json=veri,
                    headers={
                        "X-Shopify-Access-Token": st.secrets["ACCESS_TOKEN"],
                        "Content-Type": "application/json"
                    }
                )
                if yanit.status_code == 201:
                    st.success("✅ Shopify'a başarıyla yüklendi.")
                else:
                    st.error("❌ Shopify Hatası:")
                    st.code(yanit.text)
            except Exception as e:
                st.error("❌ Shopify API Hatası:")
                st.code(str(e))