import streamlit as st
import openai
import requests
import replicate
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- Kullanıcı Girişi ---
st.set_page_config(page_title="🧠 AI Ürün Paneli", layout="wide")
st.sidebar.title("🔐 Giriş Paneli")
username = st.sidebar.text_input("Kullanıcı Adı")
password = st.sidebar.text_input("Parola", type="password")

if st.sidebar.button("Giriş Yap"):
    if username == st.secrets["APP_USER"] and password == st.secrets["APP_PASS"]:
        st.session_state["giris_yapildi"] = True
        st.sidebar.success("✔️ Giriş başarılı!")
    else:
        st.sidebar.error("❌ Hatalı kullanıcı adı ya da parola")

if not st.session_state.get("giris_yapildi"):
    st.warning("Lütfen sol menüden giriş yapın.")
    st.stop()

st.title("🧠 AI Ürün Paneli (Geçmiş Kayıtlı)")
st.markdown("#### 🧾 Trend Konusu (örn: TikTok'ta viral olanlar)")
trend_konu = st.text_input("📌 Trend Konusu")

GEÇMİŞ_DOSYA = Path("urun_gecmisi.json")

def urun_gecmisini_yukle():
    if GEÇMİŞ_DOSYA.exists():
        with open(GEÇMİŞ_DOSYA, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def urun_gecmisini_kaydet(yeni_urun):
    gecmis = urun_gecmisini_yukle()
    gecmis.append(yeni_urun)
    with open(GEÇMİŞ_DOSYA, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

def urun_gecmisini_temizle():
    GEÇMİŞ_DOSYA.unlink(missing_ok=True)

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
            for urun in urunler:
                urun["zaman"] = datetime.now().isoformat()
                urun["shopify_yuklendi"] = False
                urun_gecmisini_kaydet(urun)
            st.session_state.urunler = urunler
            st.success("✅ Ürünler başarıyla oluşturuldu ve geçmişe kaydedildi!")
    except Exception as e:
        st.error("❌ GPT Hatası:")
        st.code(str(e))

st.markdown("---")
st.subheader("📜 Ürün Geçmişi")

gecmis_istatistik = urun_gecmisini_yukle()
toplam = len(gecmis_istatistik)
yuklenen = sum([1 for u in gecmis_istatistik if u.get("shopify_yuklendi")])
yuklenmeyen = toplam - yuklenen

st.markdown(f"**🔢 Toplam Ürün:** {toplam}")
st.markdown(f"✅ **Shopify'a Yüklenen:** {yuklenen}")
st.markdown(f"⏳ **Yüklenmeyen:** {yuklenmeyen}")
if toplam > 0:
    oran = round((yuklenen / toplam) * 100, 2)
    st.markdown(f"📈 **Yüklenme Oranı:** %{oran}")

filtre_yuklenen = st.selectbox("🧰 Shopify yükleme durumuna göre filtrele:", ["Tümü", "Yüklenenler", "Yüklenmeyenler"])

if st.button("🧹 Geçmişi Temizle"):
    urun_gecmisini_temizle()
    st.success("🗑️ Geçmiş başarıyla temizlendi.")

gecmis_urunler = urun_gecmisini_yukle()

if gecmis_urunler:
    df = pd.DataFrame(gecmis_urunler)
    st.download_button("📥 Excel Olarak İndir", data=df.to_excel(index=False), file_name="urun_gecmisi.xlsx")

    if filtre_yuklenen == "Yüklenenler":
        gecmis_urunler = [u for u in gecmis_urunler if u.get("shopify_yuklendi")]
    elif filtre_yuklenen == "Yüklenmeyenler":
        gecmis_urunler = [u for u in gecmis_urunler if not u.get("shopify_yuklendi")]

for urun in reversed(gecmis_urunler):
    with st.container():
        st.markdown(f"### {urun['urun_adi']}")
        st.write("🕒", urun.get("zaman", "-")[:19])
        st.write("📄", urun["aciklama"])
        st.write("🔍", urun["seo_aciklama"])

        if "gorsel_url" in urun and urun["gorsel_url"]:
            st.image(urun["gorsel_url"], width=300)
        else:
            if st.button(f"🎨 Bu ürün için görsel üret", key=f"gorsel_{urun['urun_adi']}"):
                try:
                    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
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
                    for g in gecmis_urunler:
                        if g["urun_adi"] == urun["urun_adi"]:
                            g["gorsel_url"] = output[0]
                    with open(GEÇMİŞ_DOSYA, "w", encoding="utf-8") as f:
                        json.dump(gecmis_urunler, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    st.error("❌ Replicate Hatası:")
                    st.code(str(e))

        if not urun.get("shopify_yuklendi"):
            if st.button(f"🛒 Shopify'a Yükle", key=f"shopify_{urun['urun_adi']}"):
                try:
                    veri = {
                        "product": {
                            "title": urun["urun_adi"],
                            "body_html": f"{urun['aciklama']}<br>{urun['seo_aciklama']}",
                            "vendor": "DrCleanNano",
                            "product_type": "AI Ürünü",
                            "tags": ["trend", "gecmis"],
                            "images": [{"src": urun.get("gorsel_url", "")}],
                            "variants": [{
                                "price": "149.90",
                                "sku": "AI-GECMIS"
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
                        for g in gecmis_urunler:
                            if g["urun_adi"] == urun["urun_adi"]:
                                g["shopify_yuklendi"] = True
                        with open(GEÇMİŞ_DOSYA, "w", encoding="utf-8") as f:
                            json.dump(gecmis_urunler, f, ensure_ascii=False, indent=2)
                    else:
                        st.error("❌ Shopify Hatası:")
                        st.code(yanit.text)
                except Exception as e:
                    st.error("❌ Shopify API Hatası:")
                    st.code(str(e))
        else:
            st.info("Shopify'a yüklendi.")