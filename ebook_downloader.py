import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os

st.set_page_config(page_title="全能電子書下載中心", page_icon="📖", layout="wide")

st.title("📖 全能電子書下載與搜尋中心")
st.write("結合網頁爬蟲與開源書庫 API，找書、下載一站完成！")

# 建立兩個分頁：一個用來貼網址爬蟲，一個用來關鍵字搜尋
tab1, tab2 = st.tabs(["🕷️ 網址解析下載 (Web Scraper)", "🔍 直接搜尋書庫 (Search)"])

# ==========================================
# 分頁 1：網址解析與下載 (Web Scraper)
# ==========================================
with tab1:
    st.subheader("貼上電子書介紹頁面或下載網址")
    st.info("💡 如果貼上的是網頁，系統會自動爬取頁面內所有隱藏的 .epub, .pdf, .mobi 下載連結。")
    
    url = st.text_input("🔗 貼上網址：", placeholder="https://example.com/book-page")
    
    if st.button("🚀 解析網頁 / 取得檔案"):
        if url:
            try:
                with st.spinner("正在連線並解析網頁，請稍候..."):
                    # 🌟 進階模擬真實瀏覽器標頭 (Headers)
                    advanced_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1'
                    }
                    
                    # 使用 Session 處理可能的 Cookie 檢查
                    session = requests.Session()
                    response = session.get(url, headers=advanced_headers, timeout=20)
                    response.raise_for_status()
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # 情況 A：網址本身就是一個直接下載的檔案
                    if 'application/' in content_type or any(ext in url.lower() for ext in ['.pdf', '.epub', '.mobi']):
                        parsed_url = urlparse(url)
                        file_name = os.path.basename(parsed_url.path) or "downloaded_ebook"
                        
                        st.success(f"✅ 判定為直接下載檔案！檔名：`{file_name}`")
                        st.download_button(
                            label=f"⬇️ 點擊下載 {file_name}",
                            data=response.content,
                            file_name=file_name,
                            mime=content_type
                        )
                    
                    # 情況 B：網址是一個普通網頁，啟動 BeautifulSoup 爬蟲抓連結
                    elif 'text/html' in content_type:
                        st.write("🕵️‍♂️ 判定為網頁，正在分析頁面內的下載按鈕...")
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        links = soup.find_all('a', href=True)
                        found_files = []
                        
                        for a in links:
                            href = a['href']
                            full_url = urljoin(url, href)
                            if any(ext in full_url.lower() for ext in ['.epub', '.pdf', '.mobi', '.azw3']):
                                link_text = a.text.strip() or "未命名連結"
                                found_files.append({"text": link_text, "url": full_url})
                        
                        if found_files:
                            st.success(f"✅ 在網頁中發現 {len(found_files)} 個下載連結！")
                            for idx, item in enumerate(found_files):
                                st.markdown(f"**{idx+1}. {item['text']}**")
                                st.markdown(f"[🔗 點此前往下載檔案]({item['url']})")
                        else:
                            st.warning("⚠️ 網頁中沒有找到常見的電子書下載連結 (.epub, .pdf, .mobi)。")
                            
            except requests.exceptions.Timeout:
                st.error("❌ 連線逾時 (Timeout)：該網站可能回應太慢，或是其防火牆阻擋了此次自動化請求。")
            except Exception as e:
                st.error(f"❌ 解析失敗: {e}")
        else:
            st.warning("請先輸入網址！")

# ==========================================
# 分頁 2：內建書庫搜尋 (Gutendex API)
# ==========================================
with tab2:
    st.subheader("搜尋開源免費電子書庫")
    st.write("資料來源：Project Gutenberg (古騰堡計畫)，提供超過 7 萬本免費公有領域電子書。")
    
    search_query = st.text_input("🔍 輸入品名或作者 (支援英文，部分支援中文)：", placeholder="例如: Alice in Wonderland 或 曹雪芹")
    
    if st.button("開始搜尋"):
        if search_query:
            with st.spinner("正在搜尋書庫..."):
                try:
                    api_url = f"https://gutendex.com/books/?search={search_query}"
                    res = requests.get(api_url, timeout=15)
                    data = res.json()
                    
                    results = data.get('results', [])
                    
                    if results:
                        st.success(f"✅ 找到 {len(results)} 本相關書籍！")
                        
                        for book in results[:10]:
                            with st.container():
                                col1, col2 = st.columns([1, 4])
                                
                                formats = book.get('formats', {})
                                cover_url = formats.get('image/jpeg', 'https://via.placeholder.com/150')
                                with col1:
                                    st.image(cover_url, width=120)
                                    
                                with col2:
                                    st.markdown(f"### {book.get('title', '未知書名')}")
                                    authors = [author['name'] for author in book.get('authors', [])]
                                    st.markdown(f"**作者：** {', '.join(authors) if authors else '未知'}")
                                    
                                    epub_url = formats.get('application/epub+zip')
                                    if epub_url:
                                        st.markdown(f"[📥 點此直接下載 EPUB 格式]({epub_url})")
                                    else:
                                        st.write("⚠️ 此書目前無 EPUB 格式可下載")
                                        
                                st.markdown("---")
                    else:
                        st.warning("找不到符合的書籍，請嘗試其他關鍵字！")
                        
                except Exception as e:
                    st.error(f"❌ 搜尋失敗: {e}")
        else:
            st.warning("請輸入搜尋關鍵字！")
