import json
import time
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime

class NewsCrawler:
    def __init__(self):
        """Khởi tạo News Crawler"""
        self.GEMINI_API_KEY = ""
        self.crawled_urls = set()  # Lưu danh sách URL đã crawl để tránh duplicate
        self.load_configs()
        
    def load_configs(self):
        """Load cấu hình parser từ dictionary trong code"""
        self.PARSERS = {
            "techcrunch": {
                "domain": "techcrunch.com",
                "title": "div.article-hero__middle",
                "content": "div.entry-content",
                "images": "div.entry-content img",
                "author": "a.wp-block-tc23-author-card-name__link",
                "time": "time",
                "highlight": "a nofollow",
                "topic": "div.tc23-post-relevant-terms__terms a",
                "references": "div.entry-content a"
            },
            "vnexpress": {
                "domain": "vnexpress.net",
                "title": "h1.title-detail",
                "content": "article.fck_detail p.Normal",
                "images": "article.fck_detail img",
                "author": "article.fck_detail p.Normal strong",
                "time": "div.sidebar-1 span.date",
                "highlight": "p.description",
                "topic": "ul.breadcrumb a",
                "references": "div.width_common.box-tinlienquanv2 a"
            },
            "techradar": {
                "domain": "techradar.com",
                "title": "div.news-article header h1",
                "content": "div.wcp-item-content p",
                "images": "div.wcp-item-content img",
                "author": "",
                "time": "",
                "highlight": "",
                "topic": "",
                "references": ""
            },
            "vietnamnet": {
                "domain": "https://vietnamnet.vn",
                "title": "div.news-article header h1",
                "content": "div.wcp-item-content p",
                "images": "div.wcp-item-content img",
                "author": "",
                "time": "",
                "highlight": "",
                "topic": "",
                "references": ""
            }
        }

        self.PARSERS_LINKS = {
            "techcrunch": {
                "domain": "techcrunch.com",
                "links": "a.loop-card__title-link"
            },
            "vnexpress": {
                "domain": "vnexpress.net",
                "links": ".wrapper-topstory-folder a[href*='vnexpress.net']"
            }
        }
            
        # Topics categories từ file JSON
        self.TOPICS_CATEGORIES = {
            "categories": {
                "Trí tuệ nhân tạo và học máy": [
                    "AI trong tài chính ngân hàng",
                    "AI tạo sinh",
                    "AI đạo đức và quy định",
                    "AI trong phát triển phần mềm"
                ],
                "Phát triển phần mềm và dịch vụ IT": [
                    "Phát triển phần mềm di động / Web",
                    "Dịch vụ Blockchain",
                    "Phân tích dữ liệu lớn",
                    "Điện toán đám mây",
                    "Xu hướng gia công phần mềm"
                ],
                "Phần cứng và điện tử tiêu dùng": [
                    "Thiết bị điện tử",
                    "Thiết bị âm thanh",
                    "Điện tử gia dụng",
                    "Đánh giá phần cứng và thủ thuật",
                    "Phần cứng chơi game"
                ],
                "An ninh mạng": [
                    "Bảo vệ dữ liệu",
                    "An ninh internet",
                    "Chính sách an ninh mạng",
                    "Phòng chống tấn công mạng",
                    "Giải pháp an ninh doanh nghiệp"
                ],
                "Fintech và thương mại điện tử": [
                    "Fintech",
                    "Nền tảng thương mại điện tử",
                    "Ngân hàng kỹ thuật số",
                    "Hệ thống thanh toán",
                    "Đầu tư"
                ],
                "Công nghệ mới": [
                    "IoT",
                    "VR / AR",
                    "Thương mại hóa 5G",
                    "Bán dẫn",
                    "Chuyển đổi số"
                ],
                "Chính sách công nghệ, kinh doanh và xu hướng": [
                    "Đầu tư công nghệ / Startup",
                    "Quyền sở hữu trí tuệ",
                    "Giao thoa khoa học - công nghệ",
                    "Sự kiện công nghệ toàn cầu"
                ]
            }
        }

    def is_url_crawled(self, url):
        """Kiểm tra URL đã được crawl chưa"""
        return url in self.crawled_urls

    def mark_url_as_crawled(self, url):
        """Đánh dấu URL đã được crawl"""
        self.crawled_urls.add(url)

    def get_crawled_count(self):
        """Lấy số lượng URL đã crawl"""
        return len(self.crawled_urls)

    def reset_crawled_urls(self):
        """Reset danh sách URL đã crawl (dùng khi cần crawl lại từ đầu)"""
        self.crawled_urls.clear()

    def get_parser_by_domain(self, domain):
        """Lấy cấu hình parser theo domain"""
        for config in self.PARSERS.values():
            if config["domain"] in domain:
                return config
        return None

    def get_parser_link(self, domain):
        """Lấy cấu hình parser links theo domain"""
        for config in self.PARSERS_LINKS.values():
            if config["domain"] in domain:
                return config
        return None

    def get_latest_news(self, soup, config):
        """Lấy danh sách links tin tức mới nhất"""
        links_tags = soup.select(config["links"])
        links = [a['href'] for a in links_tags]
        return links

    def summarize_with_gemini(self, content):
        """Tóm tắt nội dung sử dụng Gemini AI"""
        prompt = (
            "Bạn là một trợ lý AI chuyên tóm tắt tin tức với độ chính xác cao. "
            "Nhiệm vụ của bạn là đọc đoạn nội dung sau và tóm tắt các ý chính một cách súc tích, dễ hiểu, giữ nguyên tinh thần và thông tin quan trọng của bài viết. "
            "Tóm tắt ngắn gọn, sử dụng ngôn ngữ tự nhiên, trung lập và không thêm thông tin ngoài nội dung gốc. "
            "Trình bày tóm tắt theo đoạn văn bản, không sử dụng markdown, không dùng kí hiệu đặc biệt, không cần lời dẫn, chỉ cần trọng tâm nội dung"
            "Tránh lặp lại từ ngữ không cần thiết và đảm bảo không bỏ sót thông tin cốt lõi.\n\n"
            f"{content.strip()}"
        )
  
        body = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + self.GEMINI_API_KEY
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return None

    def classify_topics_with_gemini(self, title, content, summary, original_topics):
        """Phân loại topics sử dụng Gemini AI với danh sách topics cố định"""
        # Tạo cấu trúc categories cho prompt
        categories_text = ""
        all_subcategories = []
        
        for main_category, subcategories in self.TOPICS_CATEGORIES["categories"].items():
            categories_text += f"\n📂 {main_category}:\n"
            for sub in subcategories:
                all_subcategories.append(sub)
                categories_text += f"   • {sub}\n"

        prompt = (
            "Bạn là chuyên gia phân loại tin tức công nghệ. Nhiệm vụ: phân tích bài viết và chọn topics phù hợp từ danh sách có sẵn.\n\n"
            
            "=== THÔNG TIN BÀI VIẾT ===\n"
            f"Tiêu đề: {title}\n"
            f"Nội dung: {content[:300]}{'...' if len(content) > 300 else ''}\n"
            f"Tóm tắt: {summary}\n"
            f"Topics gốc: {', '.join(original_topics) if original_topics else 'Không có'}\n\n"
            
            "=== DANH SÁCH TOPICS CÓ SẴN ===\n"
            f"{categories_text}\n"
            
            "=== HƯỚNG DẪN ===\n"
            "1. Đọc kỹ nội dung bài viết\n"
            "2. Chọn 1-3 topics con phù hợp nhất từ danh sách trên\n"
            "3. CHỈ sử dụng tên topics CHÍNH XÁC như trong danh sách\n"
            "4. Trả về JSON format:\n\n"
            
            '{"selected_topics": ["topic1", "topic2"]}\n\n'
            
            "VÍ DỤ:\n"
            '{"selected_topics": ["AI tạo sinh", "Phát triển phần mềm di động / Web"]}\n\n'
            
            "QUAN TRỌNG: CHỈ trả về JSON, không giải thích gì thêm!"
        )

        body = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + self.GEMINI_API_KEY
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Debug: in response để kiểm tra
            print(f"🔍 DEBUG - Gemini Response: {response_text[:200]}...")
            
            # Parse JSON response với format đơn giản
            try:
                import re
                # Tìm JSON object trong response  
                json_match = re.search(r'\{[^{}]*"selected_topics"[^{}]*\}', response_text)
                if json_match:
                    print(f"🔍 DEBUG - Found JSON: {json_match.group()}")
                    json_data = json.loads(json_match.group())
                    selected_topics = json_data.get("selected_topics", [])
                    
                    # Validate topics - chỉ giữ lại topics có trong danh sách
                    valid_topics = []
                    all_valid_subcategories = []
                    
                    # Tạo danh sách tất cả subcategories hợp lệ
                    for main_cat, sub_cats in self.TOPICS_CATEGORIES["categories"].items():
                        all_valid_subcategories.extend(sub_cats)
                    
                    for topic in selected_topics:
                        if topic in all_valid_subcategories:
                            valid_topics.append(topic)
                    
                    print(f"🔍 DEBUG - Valid topics: {valid_topics}")
                    return {"selected_topics": valid_topics}
                else:
                    print("❌ DEBUG - No JSON found in response")
                    return {}
            except json.JSONDecodeError as e:
                print(f"❌ DEBUG - JSON decode error: {e}")
                return {}
                
        except Exception as e:
            print(f"❌ DEBUG - Request error: {e}")
            return {}

    def summarize(self, soup, config):
        """Tóm tắt bài viết với đầy đủ thông tin"""
        try:
            title_tag = soup.select_one(config["title"])
            content_tags = soup.select(config["content"])
            image_tags = soup.select(config["images"])
            author_tag = soup.select_one(config["author"])
            time_tag = soup.select_one(config["time"])
            topics_tag = soup.select(config["topic"])
            references_tags = soup.select(config["references"])
            
            title = title_tag.text.strip() if title_tag else None
            content = "\n".join(p.text.strip() for p in content_tags if p.text.strip())
            summ = self.summarize_with_gemini(content)
            images = [img["src"] for img in image_tags if img.get("src")]
            author = author_tag.text.strip() if author_tag else None
            time = time_tag.text.strip() if time_tag else None
            topics = [topic.get_text(strip=True) for topic in topics_tag]
            references = [link['href'] for link in references_tags if link.get('href')]
            
            return {
                "title": title,
                "content": content,
                "images": images,
                "author": author,
                "time": time,
                "topic": topics,
                "references": references,
                "summary": summ,
            }
        except Exception as e:
            return None

    def parser_seo(self, soup, config):
        """Phân tích dữ liệu SEO của bài viết"""
        try:
            seo_data = {
                "meta_title": "",
                "meta_description": "",
                "meta_keywords": [],
                "h1": "",
                "h2": [],
                "canonical_url": "",
                "word_count": 0,
                "internal_links": [],
                "external_links": []
            }
            
            meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
            if meta_title and meta_title.get("content"):
                seo_data["meta_title"] = meta_title["content"]
                
            meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                seo_data["meta_description"] = meta_desc["content"]
                
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords and meta_keywords.get("content"):
                seo_data["meta_keywords"] = [kw.strip() for kw in meta_keywords["content"].split(",")]
                
            h1_tag = soup.find("h1")
            if h1_tag:
                seo_data["h1"] = h1_tag.get_text(strip=True)
                
            h2_tags = soup.find_all("h2")
            if h2_tags:
                seo_data["h2"] = [h2.get_text(strip=True) for h2 in h2_tags]
                
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                seo_data["canonical_url"] = canonical["href"]
                
            content_container = soup.select_one(config.get("content", ""))
            if content_container:
                text_content = " ".join(p.get_text(strip=True) for p in content_container.find_all("p"))
                seo_data["word_count"] = len(text_content.split())

            domain = config["domain"]
            links = soup.select(config.get("references", ""))
            for link in links:
                href = link.get("href")
                if href:
                    if domain in href or href.startswith("/"):
                        seo_data["internal_links"].append(href)
                    else:
                        seo_data["external_links"].append(href)

            return seo_data
        except Exception as e:
            return None

    def create_driver(self):
        """Tạo Chrome driver"""
        options = Options()
        options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def process_article(self, url):
        """Xử lý một bài viết từ URL và return dict tổng hợp"""
        # Kiểm tra URL đã được crawl chưa
        if self.is_url_crawled(url):
            return None
            
        try:
            driver = self.create_driver()
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            
            domain = urlparse(url).netloc 
            config = self.get_parser_by_domain(domain)
            
            if not config:
                return None

            # Thu thập dữ liệu
            summarize_article = self.summarize(soup, config)
            seo_data = self.parser_seo(soup, config)
            
            if not summarize_article or not seo_data:
                return None
            
            # Gộp dữ liệu từ articles_summarize và seo_data
            combined_data = {
                # Dữ liệu từ articles_summarize
                "title": summarize_article.get("title", ""),
                "content": summarize_article.get("content", ""),
                "images": summarize_article.get("images", []),
                "author": summarize_article.get("author", ""),
                "time": summarize_article.get("time", ""),
                "topic": summarize_article.get("topic", []),
                "references": summarize_article.get("references", []),
                "summary": summarize_article.get("summary", ""),
                
                # Dữ liệu từ seo_data
                "meta_title": seo_data.get("meta_title", ""),
                "meta_description": seo_data.get("meta_description", ""),
                "meta_keywords": seo_data.get("meta_keywords", []),
                "h1": seo_data.get("h1", ""),
                "h2": seo_data.get("h2", []),
                "canonical_url": seo_data.get("canonical_url", ""),
                "word_count": seo_data.get("word_count", 0),
                "internal_links": seo_data.get("internal_links", []),
                "external_links": seo_data.get("external_links", []),
                
                # Thông tin bổ sung
                "url": url,
                "domain": domain,
                "crawl_timestamp": datetime.now().isoformat()
            }
            
            # Thêm phân loại topics tự động nếu có đủ dữ liệu
            if combined_data.get("title") and combined_data.get("summary"):
                classified_result = self.classify_topics_with_gemini(
                    combined_data.get("title", ""),
                    combined_data.get("content", ""),
                    combined_data.get("summary", ""),
                    combined_data.get("topic", [])
                )
                combined_data["rcm_topics"] = classified_result
            
            # Đánh dấu URL đã crawl thành công
            self.mark_url_as_crawled(url)
            
            return combined_data
            
        except Exception as e:
            return None

    def crawl_multiple_urls(self):
        """Crawl nhiều URL từ các domain đã cấu hình và return danh sách dict"""
        try:
            crawled_articles = []
            skipped_count = 0
            processed_count = 0
            domains = [config["domain"] for config in self.PARSERS.values()]
            
            print(f"📊 Bắt đầu crawl. Đã có {self.get_crawled_count()} URL trong cache.")
            
            for domain in domains:
                config_links = self.get_parser_link(domain)
                if not config_links:
                    continue
                    
                driver = self.create_driver()
                driver.get(f"https://{domain}")
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                driver.quit()
                
                links = self.get_latest_news(soup, config_links)
                for url in links[:2]:  # Lấy 2 bài mới nhất
                    if url.startswith("/"):
                        url = f"https://{domain}{url}"

                    processed_count += 1
                    if self.is_url_crawled(url):
                        skipped_count += 1
                        continue
                        
                    result = self.process_article(url)
                    if result:
                        crawled_articles.append(result)
            
            print(f"📈 Kết quả: {len(crawled_articles)} bài mới, {skipped_count} bài đã có, {processed_count} bài đã xử lý")
            return crawled_articles
            
        except Exception as e:
            return []

    def auto_crawl_scheduler(self, interval_minutes=5):
        """Chức năng tự động crawl theo thời gian"""
        try:
            while True:
                results = self.crawl_multiple_urls()
                
                # Nghỉ theo thời gian đã định
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            time.sleep(60)  # Nghỉ 1 phút trước khi thử lại
            self.auto_crawl_scheduler(interval_minutes)

    def crawl_single_url(self, url):
        """Crawl một URL đơn lẻ và return dict"""
        result = self.process_article(url)
        return result


def main():
    """Hàm chính"""
    crawler = NewsCrawler()
    
    print("🤖 News Crawler - Hệ thống thu thập tin tức tự động")
    print("=" * 60)
    print("1. 🚀 Crawl tất cả domain") 
    print("2. 🔍 Crawl một URL")
    print("3. ⚙️  Auto crawl (tùy chỉnh thời gian)")
    print("4. 🗑️  Reset cache (xóa danh sách URL đã crawl)")
    print(f"📊 Cache hiện tại: {crawler.get_crawled_count()} URL")

    choice = input("\nChọn chức năng (1-4): ").strip()
    if choice == "1":
        print("🚀 Bắt đầu crawl tất cả domain...")
        results = crawler.crawl_multiple_urls()
        if results:
            print(f"\n🎉 Thành công! Đã crawl {len(results)} bài viết.")
            print("📋 Dữ liệu đã được trả về trong biến results.")
            with open("crawled_data.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            return results
        
    elif choice == "2":
        url = input("Nhập URL: ").strip()
        if url:
            print("🔍 Crawl URL...")
            result = crawler.crawl_single_url(url)
            if result:
                print("🎉 Thành công! Dữ liệu đã được trả về.")
                with open("crawled_data_single.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                return result
        else:
            print("❌ URL không hợp lệ!")
        
    elif choice == "3":
        try:
            minutes = int(input("Nhập số phút giữa mỗi lần crawl (tối thiểu 1 phút): ").strip())
            if minutes < 1:
                print("❌ Thời gian tối thiểu là 1 phút!")
                return
            print(f"⏰ Chế độ auto crawl tùy chỉnh ({minutes} phút/lần)")
            crawler.auto_crawl_scheduler(minutes)
        except ValueError:
            print("❌ Vui lòng nhập số nguyên hợp lệ!")
    
    elif choice == "4":
        old_count = crawler.get_crawled_count()
        crawler.reset_crawled_urls()
        print(f"🗑️  Đã xóa {old_count} URL khỏi cache. Cache hiện tại: {crawler.get_crawled_count()} URL")
            
    else:
        print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
