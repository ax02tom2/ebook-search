import streamlit as st
import requests
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os

st.set_page_config(page_title="地質與邊坡文獻下載中心", page_icon="⛰️", layout="wide")

st.title("⛰️ 地質與邊坡監測文獻下載中心")
st.write("專為工程防災領域打造：支援官方網頁深度爬取，以及政府/學術 PDF 精準搜尋。")

# --- 側邊欄設定 Google API ---
st.sidebar.header("⚙️ Google 搜尋 API 設定")
st.sidebar.write("請輸入憑證以啟用第二分頁的搜尋功能：")
GOOGLE_API_KEY = st.sidebar.text_input("Google API Key", type="password")
GOOGLE_CX = st.sidebar.text_input("搜尋引擎 ID (CX)", type="password")

tab1, tab2 = st.tabs(["🕷️ 官方網址文獻爬取 (Web Scraper)", "🔍 台灣官方 PDF 搜尋 (Google Search)"])

# ==========================================
# 分頁 1：官方網址文獻爬取
# ==========================================
with tab1:
    st.subheader("貼上政府機關或計畫介紹頁面網址")
    st.info("💡 系統會自動抓取頁面內所有 PDF, Word, Excel, PPT, ODT 與 ZIP 附件檔。")
    
    url = st.text_input("🔗 貼上網址：", placeholder="https://www.cgs.gov.tw/...")
    
    if st.button("🚀 解析網頁 / 取得檔案附件"):
        if url:
            try:
                with st.spinner("啟動進階防護繞過機制，正在解析網頁..."):
                    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
                    response = scraper.get(url, timeout=20)
                    response.raise_for_status()
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    target_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.zip', '.rar']
                    
                    if 'application/' in content_type or any(ext in url.lower() for ext in target_exts):
                        parsed_url = urlparse(url)
                        file_name = os.path.basename(parsed_url.path) or "downloaded_document"
                        st.success(f"✅ 判定為直接下載檔案！檔名：`{file_name}`")
                        st.download_button(label=f"⬇️ 點擊下載 {file_name}", data=response.content, file_name=file_name, mime=content_type)
                    
                    elif 'text/html' in content_type:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        links = soup.find_all('a', href=True)
                        found_files = []
                        
                        for a in links:
                            href = a['href']
                            full_url = urljoin(url, href)
                            if any(ext in full_url.lower() for ext in target_exts):
                                link_text = a.text.strip() or os.path.basename(urlparse(full_url).path)
                                found_files.append({"text": link_text, "url": full_url})
                        
                        if found_files:
                            st.success(f"✅ 在網頁中發現 {len(found_files)} 個文獻下載連結！")
                            for idx, item in enumerate(found_files):
                                st.markdown(f"**{idx+1}. {item['text']}**")
                                st.markdown(f"[🔗 點此前往下載檔案]({item['url']})")
                        else:
                            st.warning("⚠️ 網頁中沒有找到常見的公文書或文獻格式檔案。")
                            
            except requests.exceptions.Timeout:
                st.error("❌ 連線逾時：該網站防火牆等級極高，已將此連線阻斷。")
            except Exception as e:
                st.error(f"❌ 解析失敗: {e}")
        else:
            st.warning("請先輸入網址！")

# ==========================================
# 分頁 2：台灣官方 PDF 搜尋 (Google Custom Search)
# ==========================================
with tab2:
    st.subheader("搜尋台灣官方與學術 PDF 文獻")
    st.write("已在底層強制綁定條件：僅搜尋 `site:.gov.tw` 與 `site:.edu.tw`，且格式限定為 `PDF`。")
    
    search_query = st.text_input("🔍 輸入專業關鍵字：", placeholder="例如: 大規模崩塌 邊坡監測 發生機制")
    
    if st.button("開始搜尋官方文獻"):
        if not GOOGLE_API_KEY or not GOOGLE_CX:
            st.error("❌ 請先在左側欄位填入 Google API Key 與 搜尋引擎 ID (CX)。")
        elif search_query:
            with st.spinner("正在向 Google 請求官方文獻資料..."):
                try:
                    # 強制加入搜尋條件
                    refined_query = f"{search_query} filetype:pdf (site:.gov.tw OR site:.edu.tw)"
                    api_url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "key": GOOGLE_API_KEY,
                        "cx": GOOGLE_CX,
                        "q": refined_query,
                        "num": 10  # 回傳前 10 筆
                    }
                    
                    res = requests.get(api_url, params=params, timeout=15)
                    data = res.json()
                    
                    if "error" in data:
                        st.error(f"API 錯誤：{data['error']['message']}")
                    elif "items" in data:
                        results = data["items"]
                        st.success(f"✅ 找到最相關的 {len(results)} 份 PDF 文獻！")
                        
                        for idx, item in enumerate(results):
                            st.markdown(f"### {idx+1}. {item.get('title')}")
                            st.markdown(f"> {item.get('snippet')}")
                            st.markdown(f"[📥 點此直接下載 PDF 檔案]({item.get('link')})")
                            st.markdown("---")
                    else:
                        st.warning("找不到符合條件的 PDF，請嘗試精簡關鍵字！")
                        
                except Exception as e:
                    st.error(f"❌ 搜尋失敗: {e}")
        else:
            st.warning("請輸入搜尋關鍵字！")
