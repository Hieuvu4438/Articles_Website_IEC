import json
import time
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import schedule
import os
from datetime import datetime

class NewsCrawler:
    def __init__(self):
        """Khởi tạo News Crawler"""
        self.GEMINI_API_KEY = "AIzaSyCprlPj5kLhDb6hU-Z39qh4VZTcc_7gMAM"
        self.load_configs()
        
    def load_configs(self):
        """Load cấu hình parser từ file JSON"""
        with open("parsers.json", "r", encoding="utf-8") as f:
            self.PARSERS = json.load(f)

        with open("parsers_links.json", "r", encoding="utf-8") as f:
            self.PARSERS_LINKS = json.load(f)
            
        # Load topics categories
        try:
            with open("topics_categories.json", "r", encoding="utf-8") as f:
                self.TOPICS_CATEGORIES = json.load(f)
        except FileNotFoundError:
            print("⚠️ Không tìm thấy topics_categories.json")
            self.TOPICS_CATEGORIES = {"categories": {}}

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

    def extract_by_config(self, soup, config):
        """Trích xuất dữ liệu bài viết theo cấu hình"""
        result = {
            "title": "",
            "author": "",
            "time": "",
            "topics": [],
            "content": []
        }
        
        title_tag = soup.select_one(config.get("title", ""))
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)
            
        author_tag = soup.select_one(config.get("author", ""))
        if author_tag:
            result["author"] = author_tag.get_text(strip=True)
            
        time_tag = soup.select_one(config.get("time", ""))
        if time_tag:
            result["time"] = time_tag.get_text(strip=True)
            
        topic_tags = soup.select(config.get("topic", ""))
        if topic_tags:
            result["topics"] = [tag.get_text(strip=True) for tag in topic_tags]
            
        content_container = soup.select_one(config.get("content", ""))
        if content_container:
            all_elements = content_container.find_all(recursive=True)
            for element in all_elements:
                if element.name == "p" and element.get_text(strip=True):
                    result["content"].append({"type": "text", "value": element.get_text(strip=True)})
                elif element.name == "img" and element.get("src", ""):
                    result["content"].append({"type": "image", "value": element.get("src")})
                elif element.name == "a" and element.get("href", ""):
                    result["content"].append({"type": "link", "value": element.get("href")})
                    
        return result

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
            print(f"❌ Lỗi khi tóm tắt với Gemini: {e}")
            return None

    def classify_topics_with_gemini(self, title, content, summary, original_topics):
        """Phân loại topics sử dụng Gemini AI"""
        # Tạo danh sách tất cả categories và subcategories
        categories_text = ""
        for main_category, subcategories in self.TOPICS_CATEGORIES["categories"].items():
            categories_text += f"\n{main_category}:\n"
            for sub in subcategories:
                categories_text += f"  - {sub}\n"

        prompt = (
            "Bạn là một chuyên gia phân loại tin tức công nghệ. "
            "Nhiệm vụ của bạn là đọc thông tin bài viết và chọn 1-3 topics phù hợp nhất từ danh sách có sẵn.\n\n"
            
            "THÔNG TIN BÀI VIẾT:\n"
            f"Tiêu đề: {title}\n"
            f"Tóm tắt: {summary}\n"
            f"Topics gốc từ website: {', '.join(original_topics) if original_topics else 'Không có'}\n\n"
            
            "DANH SÁCH TOPICS CÓ SẴN:" + categories_text + "\n\n"
            
            "YÊUCẦU:\n"
            "1. Chọn 1-3 topics con (subcategories) phù hợp nhất\n"
            "2. Trả về CHÍNH XÁC theo format JSON:\n"
            '{"selected_topics": ["topic1", "topic2", "topic3"]}\n\n'
            
            "3. CHỈ chọn từ danh sách có sẵn, KHÔNG tự tạo topics mới\n"
            "4. Ưu tiên topics cụ thể hơn topics chung\n"
            "5. KHÔNG thêm giải thích, chỉ trả về JSON"
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
            
            # Parse JSON response
            try:
                # Tìm và extract JSON từ response
                import re
                json_match = re.search(r'\{[^{}]*"selected_topics"[^{}]*\}', response_text)
                if json_match:
                    json_data = json.loads(json_match.group())
                    return json_data.get("selected_topics", [])
                else:
                    print(f"⚠️ Không tìm thấy JSON trong response: {response_text}")
                    return []
            except json.JSONDecodeError as e:
                print(f"⚠️ Lỗi parse JSON: {e}")
                print(f"Response: {response_text}")
                return []
                
        except Exception as e:
            print(f"❌ Lỗi khi phân loại topics với Gemini: {e}")
            return []

    def add_classified_topics_to_articles(self, articles_file="articles_summarize.json", output_file="articles_with_topics.json"):
        """Thêm topics được phân loại vào các bài viết"""
        try:
            # Load articles
            with open(articles_file, "r", encoding="utf-8") as f:
                articles = json.load(f)
            
            updated_articles = []
            
            for i, article in enumerate(articles):
                print(f"🔍 Đang phân loại bài {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
                
                # Extract thông tin cần thiết
                title = article.get("title", "")
                content = article.get("content", "")
                summary = article.get("summary", "")
                original_topics = article.get("topic", [])
                
                # Phân loại topics
                classified_topics = self.classify_topics_with_gemini(title, content, summary, original_topics)
                
                # Thêm vào article
                article_copy = article.copy()
                article_copy["classified_topics"] = classified_topics
                article_copy["classification_timestamp"] = datetime.now().isoformat()
                
                updated_articles.append(article_copy)
                
                print(f"✅ Topics được chọn: {', '.join(classified_topics) if classified_topics else 'Không có'}")
                
                # Delay để tránh rate limit
                time.sleep(2)
            
            # Lưu kết quả
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(updated_articles, f, ensure_ascii=False, indent=4)
            
            print(f"✅ Đã hoàn thành phân loại và lưu vào {output_file}")
            return len(updated_articles)
            
        except Exception as e:
            print(f"❌ Lỗi khi phân loại topics: {e}")
            return 0

    def classify_single_article_topics(self, article_file="test_summary.json"):
        """Phân loại topics cho một bài viết đơn lẻ"""
        try:
            # Load article
            with open(article_file, "r", encoding="utf-8") as f:
                articles = json.load(f)
            
            if not articles:
                print("❌ Không có bài viết nào trong file!")
                return None
                
            article = articles[0] if isinstance(articles, list) else articles
            
            print(f"🔍 Đang phân loại bài viết: {article.get('title', 'Unknown')[:50]}...")
            
            # Extract thông tin
            title = article.get("title", "")
            content = article.get("content", "")
            summary = article.get("summary", "")
            original_topics = article.get("topic", [])
            
            # Phân loại
            classified_topics = self.classify_topics_with_gemini(title, content, summary, original_topics)
            
            # Thêm topics vào article
            article["classified_topics"] = classified_topics
            article["classification_timestamp"] = datetime.now().isoformat()
            
            # Lưu lại
            with open("test_summary_with_topics.json", "w", encoding="utf-8") as f:
                json.dump([article], f, ensure_ascii=False, indent=4)
            
            print(f"✅ Topics được chọn: {', '.join(classified_topics) if classified_topics else 'Không có'}")
            print(f"✅ Đã lưu kết quả vào test_summary_with_topics.json")
            
            return classified_topics
            
        except Exception as e:
            print(f"❌ Lỗi khi phân loại topics: {e}")
            return None

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
            print(f"❌ Lỗi khi trích xuất dữ liệu: {e}")
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
            print(f"❌ Lỗi khi phân tích SEO: {e}")
            return None

    def create_driver(self):
        """Tạo Chrome driver"""
        options = Options()
        options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def load_existing_data(self, filename):
        """Load dữ liệu hiện có từ file JSON"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"⚠️ Lỗi khi đọc {filename}: {e}")
            return []

    def is_duplicate_article(self, new_article, existing_articles):
        """Kiểm tra bài viết có trùng lặp không"""
        if not new_article or not new_article.get("title"):
            return True
            
        new_title = new_article["title"].strip().lower()
        
        for existing in existing_articles:
            if not existing or not existing.get("title"):
                continue
                
            existing_title = existing["title"].strip().lower()
            
            # Kiểm tra tiêu đề giống nhau
            if new_title == existing_title:
                return True
                
            # Kiểm tra độ tương đồng cao (85% trở lên)
            similarity = self.calculate_similarity(new_title, existing_title)
            if similarity >= 0.85:
                return True
                
        return False

    def calculate_similarity(self, text1, text2):
        """Tính độ tương đồng giữa 2 chuỗi"""
        if not text1 or not text2:
            return 0
            
        # Sử dụng Jaccard similarity với từ
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0
            
        return len(intersection) / len(union)

    def save_data_incrementally(self, new_articles, new_summaries, new_seo_data):
        """Lưu dữ liệu mới vào file hiện có"""
        # Load dữ liệu hiện có
        existing_articles = self.load_existing_data("articles.json")
        existing_summaries = self.load_existing_data("articles_summarize.json")
        existing_seo = self.load_existing_data("seo_data.json")
        
        # Filter bài viết mới không trùng lặp
        filtered_articles = []
        filtered_summaries = []
        filtered_seo = []
        
        for i, article in enumerate(new_articles):
            if not self.is_duplicate_article(article, existing_articles):
                filtered_articles.append(article)
                if i < len(new_summaries):
                    filtered_summaries.append(new_summaries[i])
                if i < len(new_seo_data):
                    filtered_seo.append(new_seo_data[i])
            else:
                print(f"⚠️ Bỏ qua bài trùng lặp: {article.get('title', 'Unknown')[:50]}...")
        
        # Thêm vào dữ liệu hiện có
        existing_articles.extend(filtered_articles)
        existing_summaries.extend(filtered_summaries)
        existing_seo.extend(filtered_seo)
        
        # Lưu lại file
        with open("articles.json", "w", encoding="utf-8") as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=4)
        with open("articles_summarize.json", "w", encoding="utf-8") as f:
            json.dump(existing_summaries, f, ensure_ascii=False, indent=4)
        with open("seo_data.json", "w", encoding="utf-8") as f:
            json.dump(existing_seo, f, ensure_ascii=False, indent=4)
            
        return len(filtered_articles)

    def get_seo_inf(self, url):
        """Lấy thông tin SEO từ URL"""
        try:
            driver = self.create_driver()
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            
            domain = urlparse(url).netloc
            config = self.get_parser_by_domain(domain)

            if not config:
                print(f"❌ Không có parser cho domain: {domain}")
                return None

            seo_data = self.parser_seo(soup, config)
            if not seo_data:
                print(f"⚠️ Không thể thu thập dữ liệu SEO cho: {url}")
                return None
                
            output_file = "seo_data.json"
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = []

            existing_data.append({
                "url": url,
                "domain": domain,
                "seo_data": seo_data
            })

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)

            return seo_data
        except Exception as e:
            print(f"❌ Lỗi khi xử lý URL {url}: {e}")
            return None

    def process_article(self, url):
        """Xử lý một bài viết từ URL"""
        try:
            driver = self.create_driver()
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            
            domain = urlparse(url).netloc 
            config = self.get_parser_by_domain(domain)
            config_links = self.get_parser_link(domain)
            
            if not config:
                print(f"❌ Không có parser cho domain: {domain}")
                return None

            if not config_links:
                print(f"❌ Không có parser_links cho domain: {domain}")
                return None

            links = self.get_latest_news(soup, config_links)
            article = self.extract_by_config(soup, config)
            summarize_article = self.summarize(soup, config)
            seo_data = self.parser_seo(soup, config)
            
            # Thêm phân loại topics tự động
            if summarize_article and summarize_article.get("title") and summarize_article.get("summary"):
                print("🎯 Đang phân loại topics...")
                classified_topics = self.classify_topics_with_gemini(
                    summarize_article.get("title", ""),
                    summarize_article.get("content", ""),
                    summarize_article.get("summary", ""),
                    summarize_article.get("topic", [])
                )
                
                # Thêm topics vào cả hai article objects
                if article:
                    article["rcm_topics"] = classified_topics
                if summarize_article:
                    summarize_article["rcm_topics"] = classified_topics
                
                print(f"✅ Topics gợi ý: {', '.join(classified_topics) if classified_topics else 'Không có'}")
            
            return article, summarize_article, seo_data
        except Exception as e:
            print(f"❌ Lỗi khi xử lý URL {url}: {e}")   
            return None

    def crawl_multiple_urls(self):
        """Crawl nhiều URL từ các domain đã cấu hình"""
        try:
            articles = []
            summaries = []
            seo_data_list = []
            domains = [config["domain"] for config in self.PARSERS.values()]
            
            for domain in domains:
                config_links = self.get_parser_link(domain)
                if not config_links:
                    print(f"❌ Không có parser_links cho domain: {domain}")
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

                    result = self.process_article(url)
                    if result:
                        article, summarize_article, seo_data = result
                        articles.append(article)
                        summaries.append(summarize_article)
                        seo_data_list.append({
                            "url": url,
                            "domain": domain,
                            "seo_data": seo_data
                        })
                        
            # Lưu kết quả incremental (ghi tiếp vào file hiện có)
            new_articles_count = self.save_data_incrementally(articles, summaries, seo_data_list)
                
            print(f"✅ Hoàn thành crawl lúc {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Số bài viết mới thu thập: {new_articles_count}/{len(articles)}")
            
        except Exception as e:
            print(f"❌ Lỗi khi crawl multiple URLs: {e}")

    def start_crawling(self, interval_minutes=1):
        """Bắt đầu crawl tự động theo lịch"""
        schedule.every(interval_minutes).minutes.do(self.crawl_multiple_urls)
        
        print(f"🚀 Bắt đầu lịch crawl tự động mỗi {interval_minutes} phút...")
        print("📋 Nhấn Ctrl+C để dừng...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Đã dừng crawling!")

    def crawl_single_url(self, url):
        """Crawl một URL đơn lẻ (để test)"""
        print(f"🔍 Đang crawl: {url}")
        result = self.process_article(url)
        
        if result:
            article, summarize_article, seo_data = result
            
            # Lưu kết quả test với topics
            with open("test_article.json", "w", encoding="utf-8") as f:
                json.dump([article], f, ensure_ascii=False, indent=4)
            with open("test_summary.json", "w", encoding="utf-8") as f:
                json.dump([summarize_article], f, ensure_ascii=False, indent=4)
            with open("test_seo.json", "w", encoding="utf-8") as f:
                json.dump([seo_data], f, ensure_ascii=False, indent=4)
                
            print("✅ Đã lưu kết quả test (bao gồm topics gợi ý)!")
            return result
        else:
            print("❌ Không thể crawl URL này!")
            return None


def main():
    """Hàm chính"""
    crawler = NewsCrawler()
    
    print("🤖 News Crawler - Hệ thống thu thập tin tức tự động")
    print("=" * 60)
    print("1. 🔄 Crawl tự động theo lịch + AI Topics")
    print("2. 🚀 Crawl tất cả domain + AI Topics") 
    print("3. 🔍 Crawl một URL + AI Topics")

    
    choice = input("\nChọn chức năng (1-3): ").strip()
    
    if choice == "1":
        interval = input("Nhập khoảng thời gian (phút, mặc định 1): ").strip()
        interval = int(interval) if interval.isdigit() else 1
        print("🔄 Bắt đầu crawl tự động với AI topics classification...")
        crawler.start_crawling(interval)
        
    elif choice == "2":
        print("🚀 Bắt đầu crawl tất cả domain với AI topics classification...")
        crawler.crawl_multiple_urls()
        
    elif choice == "3":
        url = input("Nhập URL: ").strip()
        if url:
            print("🔍 Crawl URL với AI topics classification...")
            crawler.crawl_single_url(url)
        else:
            print("❌ URL không hợp lệ!")
            
    else:
        print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
