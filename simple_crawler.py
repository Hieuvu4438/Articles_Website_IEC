#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple News Crawler - Phiên bản test đơn giản
Chuyển đổi từ Jupyter Notebook TEST.ipynb
"""

import csv
import json
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from transformers import pipeline

class SimpleNewsCrawler:
    def __init__(self):
        """Khởi tạo Simple News Crawler"""
        self.load_parsers()
        self.summarizer = None
        
    def load_parsers(self):
        """Load cấu hình parser"""
        try:
            with open("parsers.json", "r", encoding="utf-8") as f:
                self.PARSERS = json.load(f)
        except FileNotFoundError:
            self.create_default_parsers()
    
    def create_default_parsers(self):
        """Tạo parser mặc định nếu chưa có file"""
        self.PARSERS = {
            "techcrunch": {
                "domain": "techcrunch.com",
                "title": "div.article-hero__middle",
                "content": "div.entry-content",
                "images": "div.entry-content img"
            },
            "vnexpress": {
                "domain": "vnexpress.net",
                "title": "h1.title-detail",
                "content": "div.sidebar-1",
                "images": "article.fck_detail img"
            },
            "techradar": {
                "domain": "techradar.com",
                "title": "div.news-article header h1",
                "content": "div.wcp-item-content p",
                "images": "div.wcp-item-content img"
            }
        }
        
        with open("parsers.json", "w", encoding="utf-8") as f:
            json.dump(self.PARSERS, f, ensure_ascii=False, indent=4)
        
        print("✅ Đã tạo file parsers.json mặc định")

    def get_parser_by_domain(self, domain):
        """Lấy parser theo domain"""
        for name, config in self.PARSERS.items():
            if config["domain"] in domain:
                return config
        return None

    def extract_by_config(self, soup, config):
        """Trích xuất nội dung theo config"""
        title_tag = soup.select_one(config["title"])
        paragraphs = soup.select(config["content"])
        images = [img["src"] for img in soup.select(config["images"]) if img.get("src")]

        title = title_tag.text.strip() if title_tag else None
        content = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())

        return {
            "title": title,
            "content": content,
            "images": images
        }

    def init_summarizer(self):
        """Khởi tạo model tóm tắt"""
        if self.summarizer is None:
            print("🤖 Đang tải model tóm tắt...")
            try:
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                print("✅ Đã tải model tóm tắt!")
            except Exception as e:
                print(f"❌ Lỗi khi tải model: {e}")
                print("💡 Cài đặt transformers: pip install transformers torch")
                return False
        return True

    def create_driver(self):
        """Tạo Chrome driver"""
        options = Options()
        options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def process_article(self, url, use_summarizer=True):
        """Xử lý một bài viết"""
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

            article = self.extract_by_config(soup, config)

            if not article["title"] or not article["content"].strip():
                print(f"⚠️ Bỏ qua vì thiếu tiêu đề hoặc nội dung: {url}")
                return None

            # Tóm tắt nếu được yêu cầu
            summary = ""
            if use_summarizer and self.init_summarizer():
                content_trimmed = article["content"][:3000].strip()
                try:
                    summary = self.summarizer(content_trimmed, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
                except Exception as e:
                    print(f"❌ Lỗi khi tóm tắt bài viết: {url}\n{e}")
                    summary = "Không thể tóm tắt"

            print("\n" + "="*60)
            print("📰 URL:", url)
            print("📌 Tiêu đề:", article["title"])
            print("🖼️ Ảnh:", article["images"] if article["images"] else "Không có ảnh")
            print("\n📄 Nội dung:\n", article["content"][:500] + "..." if len(article["content"]) > 500 else article["content"])
            if summary:
                print("\n🧠 Tóm tắt:\n", summary)
            print("="*60)

            return {
                "title": article["title"],
                "url": url,
                "summary": summary,
                "content": article["content"],
                "images": ", ".join(article["images"]) if article["images"] else ""
            }

        except Exception as e:
            print(f"❌ Lỗi khi xử lý URL {url}: {e}")
            return None

    def crawl_urls(self, urls, use_summarizer=True):
        """Crawl danh sách URLs"""
        results = []
        
        print(f"🚀 Bắt đầu crawl {len(urls)} URL(s)...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n📍 Đang xử lý {i}/{len(urls)}: {url}")
            result = self.process_article(url, use_summarizer)
            if result:
                results.append(result)
            
            # Nghỉ giữa các request
            if i < len(urls):
                time.sleep(2)

        return results

    def save_results(self, results, filename="articles"):
        """Lưu kết quả ra file"""
        # Lưu JSON
        json_file = f"{filename}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        # Lưu CSV
        csv_file = f"{filename}.csv"
        if results:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        print(f"✅ Đã lưu {len(results)} bài viết vào {json_file} và {csv_file}")

    def crawl_sample_urls(self):
        """Crawl các URL mẫu"""
        sample_urls = [
            "https://techcrunch.com/2025/05/13/aws-enters-into-strategic-partnership-with-saudi-arabia-backed-humain/",
            "https://vnexpress.net/hon-150-trieu-dong-cho-cac-startup-tranh-tai-tai-pitchfest-2025-4885506.html",
            "https://www.techradar.com/computing/artificial-intelligence/this-new-chatgpt-feature-solves-the-most-annoying-thing-about-deep-research"
        ]
        
        results = self.crawl_urls(sample_urls)
        if results:
            self.save_results(results, "sample_articles")
        
        return results


def main():
    """Hàm chính"""
    crawler = SimpleNewsCrawler()
    
    print("📰 Simple News Crawler - Test Version")
    print("=" * 40)
    print("1. Crawl URLs mẫu")
    print("2. Crawl URL tùy chỉnh")
    print("3. Crawl nhiều URLs từ file")
    
    choice = input("\nChọn chức năng (1-3): ").strip()
    
    if choice == "1":
        print("🔍 Crawling URLs mẫu...")
        results = crawler.crawl_sample_urls()
        print(f"\n✅ Hoàn thành! Thu thập được {len(results)} bài viết.")
        
    elif choice == "2":
        url = input("Nhập URL: ").strip()
        if url:
            use_ai = input("Sử dụng AI tóm tắt? (y/n, mặc định y): ").strip().lower()
            use_summarizer = use_ai != 'n'
            
            result = crawler.process_article(url, use_summarizer)
            if result:
                crawler.save_results([result], "single_article")
                print("\n✅ Đã crawl thành công!")
            else:
                print("\n❌ Không thể crawl URL này!")
        else:
            print("❌ URL không hợp lệ!")
            
    elif choice == "3":
        filename = input("Nhập tên file chứa URLs (mỗi dòng 1 URL): ").strip()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            if urls:
                use_ai = input("Sử dụng AI tóm tắt? (y/n, mặc định y): ").strip().lower()
                use_summarizer = use_ai != 'n'
                
                results = crawler.crawl_urls(urls, use_summarizer)
                if results:
                    crawler.save_results(results, "batch_articles")
                print(f"\n✅ Hoàn thành! Thu thập được {len(results)}/{len(urls)} bài viết.")
            else:
                print("❌ File rỗng hoặc không có URL hợp lệ!")
                
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file: {filename}")
        except Exception as e:
            print(f"❌ Lỗi khi đọc file: {e}")
            
    else:
        print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
