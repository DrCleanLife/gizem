import streamlit as st
import openai
import requests
import replicate
import json

# Streamlit ayarı
st.set_page_config(page_title="AI Görselli Ürün Paneli", layout="centered")
st.title("🧠 Görselli AI Ürün Paneli (OpenAI + Replicate + Shopify)")

# Trend girdisi
trend_konu = st.text_input("📝 Trend Konusu (\"örn: TikTok'ta viral olanlar\")")

# GPT ile ürünleri oluştur
if st.button("🍭 3 Ürün Oluştur"):
    try:
        openai_client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        gpt_prompt = f"""
        TikTok'ta {trend_konu} bağlı çok satan 3 fiziksel ürün fikri ver. Sadece aşağıdaki JSON formatında ver:
        [
          {{"urun_adi": "...", "aciklama": "...", "seo_aciklama": "..."}},
          ...
        ]
        Sadece JSON olarak yanıt ver."""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": gpt_prompt}],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content
        st.session_state.urunler = json.loads(content)
        st.success("✅ Ürünler başarıyla oluşturuldu!")
    except Exception as e:
        st.error("❌ GPT Hatası:")
        st.code(str(e))

# Toplu görsel üret
if "urunler" in st.session_state and st.button("🖼️ Tüm Görselleri Üret"):
    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
    for i, urun in enumerate(st.session_state.urunler):
        try:
            with st.spinner(f"{urun['urun_adi']} için görsel üretiliyor..."):
                output = replicate_client.run(
                    "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                    input={
                        "prompt": f"{urun['urun_adi']}, {urun['aciklama']}, studio lighting, white background",
                        "num_outputs": 1,
                        "width": 512,
                        "height": 512
                    }
                )
                urun["gorsel_url"] = str(output[0])
                st.image(str(output[0]), caption=urun['urun_adi'], width=300)
        except Exception as e:
            st.error(f"❌ {urun['urun_adi']} için Replicate Hatası:")
            st.code(str(e))

# Ürünleri ve butonları listele
if "urunler" in st.session_state:
    for i, urun in enumerate(st.session_state.urunler):
        with st.container():
            st.subheader(f"🧠 {urun['urun_adi']}")
            st.write("📄", urun["aciklama"])
            st.write("🔍", urun["seo_aciklama"])

            # Tekli görsel üret
            replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
            if st.button(f"🎨 Görsel Üret", key=f"gorsel_{i}"):
                try:
                    with st.spinner("Görsel üretiliyor..."):
                        output = replicate_client.run(
                            "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                            input={
                                "prompt": f"{urun['urun_adi']}, {urun['aciklama']}, studio lighting, white background",
                                "num_outputs": 1,
                                "width": 512,
                                "height": 512
                            }
                        )
                    urun["gorsel_url"] = str(output[0])
                    st.image(str(output[0]), caption="🖼️ Üretilen Görsel", width=300)
                    st.success("✅ Görsel başarıyla üretildi.")
                except Exception as e:
                    st.error("❌ Replicate Hatası:")
                    st.code(str(e))

            # Shopify'a yükle
            if st.button(f"🛒 Shopify'a Yükle", key=f"yukle_{i}"):
                try:
                    sku_kodu = f"fAI-{i+1}"
                    veri = {
                        "product": {
                            "title": urun["urun_adi"],
                            "body_html": f"{urun['aciklama']}<br>{urun['seo_aciklama']}",
                            "vendor": "DrCleanNano",
                            "product_type": "AI Ürünü",
                            "tags": ["trend", "tiktok", "AI", "otomatik"],
                            "images": [{"src": urun.get("gorsel_url", "")}],
                            "variants": [{"price": "149.90", "sku": sku_kodu}]
                        }
                    }
                    yanit = requests.post(
                        f"{st.secrets['SHOPIFY_STORE_URL']}/products.json",
                        headers={"X-Shopify-Access-Token": st.secrets["SHOPIFY_ACCESS_TOKEN"]},
                        json=veri
                    )
                    if yanit.status_code == 201:
                        st.success("✅ Shopify'a yüklendi!")
                    else:
                        st.error(f"Hata kodu: {yanit.status_code}")
                        st.code(yanit.text)
                except Exception as e:
                    st.error("❌ Shopify Yükleme Hatası:")
                    st.code(str(e))
