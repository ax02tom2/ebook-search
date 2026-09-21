import streamlit as st
import requests
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os
import json

# 修改網頁分頁標籤名稱與圖示
st.set_page_config(page_title="GeoDocs 探勘者", page_icon="⛏️", layout="wide")

# 修改網頁主標題
st.title("⛏️ GeoDocs 探勘者：工程防災文獻快搜")
st.write("專為地質與邊坡工程打造：支援官方網頁深度爬取，以及政府/學術 PDF 報告精準檢索。")

# --- 側邊欄設定 Serper API ---
st.sidebar.header("⚙️ 搜尋 API 設定")
st.sidebar.write("請輸入 Serper API 金鑰以啟用第二分頁搜尋功能：")
SERPER_API_KEY = st.sidebar.text_input("Serper API Key", type="password")
st.sidebar.markdown("[👉 點此免費取得 Serper API 金鑰](https://serper.dev/)")

tab1, tab2 = st.tabs(["🕷️ 官方網址文獻爬取 (Web Scraper)", "🔍 台灣官方 PDF 搜尋 (Serper API)"])

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
                            href = a.get('href')
                            if not href:
                                continue
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
# 分頁 2：台灣官方 PDF 搜尋 (Serper API)
# ==========================================
with tab2:
    st.subheader("搜尋台灣官方與學術 PDF 文獻")
    st.write("底層強制綁定條件：僅搜尋 `site:gov.tw` 與 `site:edu.tw`，且格式限定為 `PDF`。")
    
    search_query = st.text_input("🔍 輸入專業關鍵字：", placeholder="例如: 大規模崩塌 邊坡監測")
    
    if st.button("開始搜尋官方文獻"):
        if not SERPER_API_KEY:
            st.error("❌ 請先在左側欄位填入 Serper API Key。")
        elif search_query:
            with st.spinner("正在透過專業 API 搜尋 Google 文獻資料庫，請稍候..."):
                try:
                    # 強制加入搜尋條件，鎖定台灣政府與學術網站的 PDF
                    refined_query = f"{search_query} filetype:pdf (site:gov.tw OR site:edu.tw)"
                    
                    # 呼叫 Serper API
                    serper_url = "https://google.serper.dev/search"
                    payload = json.dumps({
                        "q": refined_query,
                        "gl": "tw",      # 設定地區為台灣
                        "hl": "zh-tw",   # 設定語言為繁體中文
                        "num": 10        # 回傳 10 筆結果
                    })
                    headers = {
                        'X-API-KEY': SERPER_API_KEY,
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.post(serper_url, headers=headers, data=payload, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                        
                    results = data.get("organic", [])
                    
                    if results:
                        st.success(f"✅ 成功找到最相關的 {len(results)} 份 PDF 文獻！")
                        
                        for idx, item in enumerate(results):
                            st.markdown(f"### {idx+1}. {item.get('title', '無標題')}")
                            st.markdown(f"> {item.get('snippet', '無摘要描述')}")
                            st.markdown(f"[📥 點此直接下載 PDF 檔案]({item.get('link')})")
                            st.markdown("---")
                    else:
                        st.warning("找不到符合條件的 PDF。請嘗試精簡關鍵字。")
                        
                except Exception as e:
                    st.error(f"❌ 搜尋失敗，請確認 API Key 是否正確或稍後再試: {e}")
        else:
            st.warning("請輸入搜尋關鍵字！")
