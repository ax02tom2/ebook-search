import streamlit as st
import requests
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os
import json

st.set_page_config(page_title="工程防災文獻快搜", page_icon="⛏️", layout="wide")

st.title("⛏️ 工程防災文獻快搜")
st.write("專為地質與邊坡工程打造：支援官方網頁深度爬取，以及政府/學術 PDF 報告精準檢索。")

# --- 自動讀取 API Key 機制 ---
try:
    saved_api_key = st.secrets["SERPER_API_KEY"]
except:
    saved_api_key = ""

st.sidebar.header("⚙️ 搜尋 API 設定")
st.sidebar.write("請輸入 Serper API 金鑰以啟用第二分頁搜尋功能：")
SERPER_API_KEY = st.sidebar.text_input("Serper API Key", type="password", value=saved_api_key)
st.sidebar.markdown("[👉 點此免費取得 Serper API 金鑰](https://serper.dev/)")

tab1, tab2, tab3 = st.tabs(["🕷️ 官方網址文獻爬取 (Web Scraper)", "🔍 台灣官方 PDF 搜尋 (Serper API)", "🛠️ 隱藏 PDF 破解工具箱"])

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
                    refined_query = f"{search_query} filetype:pdf (site:gov.tw OR site:edu.tw)"
                    
                    serper_url = "https://google.serper.dev/search"
                    payload = json.dumps({
                        "q": refined_query,
                        "gl": "tw",
                        "hl": "zh-tw",
                        "num": 20
                    })
                    # 這裡加入了 .strip() 自動清除可能不小心複製到的空白鍵
                    headers = {
                        'X-API-KEY': SERPER_API_KEY.strip(),
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

# ==========================================
# 分頁 3：隱藏 PDF 破解工具箱 (Bookmarklet)
# ==========================================
with tab3:
    st.subheader("🛠️ 網頁閱讀器 PDF 強制下載工具")
    st.write("當政府網站隱藏了下載按鈕，且使用 PDF.js 渲染電子書時，可使用以下工具強制從瀏覽器記憶體匯出檔案。")
    
    st.markdown("### 方法一：建立「一鍵下載」書籤 (推薦)")
    st.write("這是一段打包好的 JavaScript 書籤代碼 (Bookmarklet)。設定完成後，未來遇到無法下載的 PDF 網頁，只要點擊該書籤即可自動下載，**完全不需要按 F12**。")
    st.markdown("""
    **設定步驟：**
    1. 在瀏覽器的書籤列上點擊右鍵 ➡️ 選擇「新增網頁」或「新增書籤」。
    2. 名稱隨便取（例如：`強制下載 PDF`）。
    3. 在「網址」或「URL」欄位中，**貼上以下整段程式碼**，然後存檔。
    """)
    
    bookmarklet_code = """javascript:(function(){
    try {
        PDFViewerApplication.pdfDocument.getData().then(data => {
            const blob = new Blob([data], { type: 'application/pdf' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = '強制破解下載文件.pdf';
            a.click();
        }).catch(e => alert('匯出失敗：' + e));
    } catch(e) {
        alert('找不到 PDF.js 核心，請確認網頁是否使用此技術，或檢查是否被包裝在 iframe 中。');
    }
})();"""
    st.code(bookmarklet_code, language="javascript")
    
    st.markdown("---")
    
    st.markdown("### 方法二：主控台 (Console) 終極匯出法")
    st.write("如果書籤失效，請在該電子書網頁按下 `F12` 開啟開發者工具，切換到 `Console (主控台)`，將以下代碼貼上並按 Enter 執行：")
    
    console_code = """PDFViewerApplication.pdfDocument.getData().then(data => {
  const blob = new Blob([data], { type: 'application/pdf' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '下載文件.pdf';
  a.click();
});"""
    st.code(console_code, language="javascript")
