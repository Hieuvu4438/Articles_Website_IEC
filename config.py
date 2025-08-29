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
        self.GEMINI_API_KEY = "AIzaSyD9lfQ4kjedlaR5vqGCHrK6AcZIRx8_Kus"
        self.crawled_urls = set()  # Lưu danh sách URL đã crawl để tránh duplicate
        self.load_configs()
        
    def load_configs(self):
        """Load cấu hình parser từ dictionary trong code"""
        self.PARSERS = {
            "techcrunch": {
                "domain": "techcrunch.com",
                "title": "div.article-hero__middle h1, h1.entry-title",
                "content": "div.entry-content p, .article-content p",
                "images": "div.entry-content img, .article-content img",
                "author": "a.wp-block-tc23-author-card-name__link, .author-name",
                "time": "time, .time-date",
                "highlight": "p.description, .excerpt",
                "topic": "div.tc23-post-relevant-terms__terms a, .tags a",
                "references": "div.entry-content a, .article-content a"
            },
            "vnexpress": {
                "domain": "vnexpress.net",
                "title": "h1.title-detail",
                "content": "article.fck_detail p.Normal, .content_detail p",
                "images": "article.fck_detail img, .content_detail img",
                "author": "article.fck_detail p.Normal strong, .author",
                "time": "div.sidebar-1 span.date, .date",
                "highlight": "p.description, .sapo",
                "topic": "ul.breadcrumb a, .breadcrumb a",
                "references": "div.width_common.box-tinlienquanv2 a, .related-news a"
            },
            "genk": {
                "domain": "genk.vn",
                "title": "h1.knswli-title, .article-title h1",
                "content": ".knswli-content p, .article-content p",
                "images": ".knswli-content img, .article-content img",
                "author": ".knswli-author, .author-name",
                "time": ".knswli-time, .article-time",
                "highlight": ".article-sapo, .excerpt",
                "topic": ".article-tags a, .tags a",
                "references": ".knswli-content a, .article-content a"
            },
            "tinhte": {
                "domain": "tinhte.vn",
                "title": "h1.p-title-value, .thread-title h1",
                "content": ".bbWrapper p, .post-content p",
                "images": ".bbWrapper img, .post-content img",
                "author": ".username, .author-name",
                "time": ".u-dt, .post-time",
                "highlight": ".bbWrapper .excerpt, .post-excerpt",
                "topic": ".tagList a, .tags a",
                "references": ".bbWrapper a, .post-content a"
            },
            "vietnamnet": {
                "domain": "vietnamnet.vn",
                "title": "h1.title, .article-title h1",
                "content": ".ArticleContent p, .article-body p",
                "images": ".ArticleContent img, .article-body img",
                "author": ".author-name, .article-author",
                "time": ".article-time, .time",
                "highlight": ".article-sapo, .sapo",
                "topic": ".article-tags a, .breadcrumb a",
                "references": ".ArticleContent a, .article-body a"
            },
            "techz": {
                "domain": "techz.vn",
                "title": "h1.entry-title, .post-title h1",
                "content": ".entry-content p, .post-content p",
                "images": ".entry-content img, .post-content img",
                "author": ".author-name, .post-author",
                "time": ".entry-date, .post-date",
                "highlight": ".entry-summary, .post-excerpt",
                "topic": ".entry-tags a, .post-tags a",
                "references": ".entry-content a, .post-content a"
            },
            "techradar": {
                "domain": "techradar.com",
                "title": "h1, .strapline h1",
                "content": "#article-body p, .text-copy p",
                "images": "#article-body img, .text-copy img",
                "author": ".byline, .author-name",
                "time": ".relative-date, .published-date",
                "highlight": ".strapline, .intro",
                "topic": ".article-tags a, .breadcrumbs a",
                "references": "#article-body a, .text-copy a"
            },
            "theverge": {
                "domain": "theverge.com",
                "title": "h1.duet--article--dangerously-set-cms-markup, .entry-title h1",
                "content": ".duet--article--article-body-component p, .entry-content p",
                "images": ".duet--article--article-body-component img, .entry-content img",
                "author": ".duet--byline--author-name, .author-name",
                "time": ".duet--timestamp--absolute, .published-date",
                "highlight": ".duet--article--lede, .excerpt",
                "topic": ".duet--article--article-tags a, .tags a",
                "references": ".duet--article--article-body-component a, .entry-content a"
            },
            "engadget": {
                "domain": "engadget.com",
                "title": "h1, .article-title h1",
                "content": ".caas-body p, .article-wrap p",
                "images": ".caas-body img, .article-wrap img",
                "author": ".caas-author-byline-collapse, .author-name",
                "time": ".caas-attr-time-style, .article-time",
                "highlight": ".caas-leadparagraph, .article-summary",
                "topic": ".caas-topic-tags a, .tags a",
                "references": ".caas-body a, .article-wrap a"
            },
            "zdnet": {
                "domain": "zdnet.com",
                "title": "h1, .headline h1",
                "content": ".storyBody p, .content p",
                "images": ".storyBody img, .content img",
                "author": ".author, .byline",
                "time": ".meta-date, .timestamp",
                "highlight": ".summary, .excerpt",
                "topic": ".tags a, .breadcrumbs a",
                "references": ".storyBody a, .content a"
            },
            "gizmodo": {
                "domain": "gizmodo.com",
                "title": "h1.headline, .post-title h1",
                "content": ".post-content p, .entry-content p",
                "images": ".post-content img, .entry-content img",
                "author": ".author, .byline",
                "time": ".meta__time, .timestamp",
                "highlight": ".excerpt, .summary",
                "topic": ".tags a, .categories a",
                "references": ".post-content a, .entry-content a"
            },
            "mashable": {
                "domain": "mashable.com",
                "title": "h1.title, .article-title h1",
                "content": ".article-content p, .content p",
                "images": ".article-content img, .content img",
                "author": ".author-name, .byline",
                "time": ".article-date, .timestamp",
                "highlight": ".article-summary, .excerpt",
                "topic": ".article-topics a, .tags a",
                "references": ".article-content a, .content a"
            },
            "cnet": {
                "domain": "cnet.com",
                "title": "h1, .article-title h1",
                "content": ".col-7 p, .article-main-body p",
                "images": ".col-7 img, .article-main-body img",
                "author": ".author-name, .byline",
                "time": ".article-date, .timestamp",
                "highlight": ".article-dek, .summary",
                "topic": ".article-tags a, .breadcrumbs a",
                "references": ".col-7 a, .article-main-body a"
            },
            "vnreview": {
                "domain": "vnreview.vn",
                "title": "h1.post-title, .article-title h1",
                "content": ".post-content p, .article-content p",
                "images": ".post-content img, .article-content img",
                "author": ".post-author, .author-name",
                "time": ".post-time, .article-time",
                "highlight": ".post-excerpt, .sapo",
                "topic": ".post-tags a, .breadcrumb a",
                "references": ".post-content a, .article-content a"
            },
            "echip": {
                "domain": "echip.vn",
                "title": "h1.entry-title, .post-title h1",
                "content": ".entry-content p, .post-content p",
                "images": ".entry-content img, .post-content img",
                "author": ".author-name, .post-author",
                "time": ".entry-date, .post-date",
                "highlight": ".entry-summary, .post-excerpt",
                "topic": ".entry-tags a, .post-tags a",
                "references": ".entry-content a, .post-content a"
            },
            "vnz": {
                "domain": "vn-z.vn",
                "title": "h1.post-title, .article-title h1",
                "content": ".post-content p, .article-content p",
                "images": ".post-content img, .article-content img",
                "author": ".post-author, .author-name",
                "time": ".post-date, .article-time",
                "highlight": ".post-excerpt, .sapo",
                "topic": ".post-categories a, .tags a",
                "references": ".post-content a, .article-content a"
            },
            "techvify": {
                "domain": "techvify.com",
                "title": "h1.post-title, .entry-title h1",
                "content": ".post-content p, .entry-content p",
                "images": ".post-content img, .entry-content img",
                "author": ".post-author, .author-name",
                "time": ".post-date, .entry-date",
                "highlight": ".post-excerpt, .entry-summary",
                "topic": ".post-tags a, .entry-tags a",
                "references": ".post-content a, .entry-content a"
            },
            "vietnaminsiders": {
                "domain": "vietnaminsiders.com",
                "title": "h1.entry-title, .post-title h1",
                "content": ".entry-content p, .post-content p",
                "images": ".entry-content img, .post-content img",
                "author": ".author-name, .post-author",
                "time": ".entry-date, .post-date",
                "highlight": ".entry-summary, .post-excerpt",
                "topic": ".entry-categories a, .post-categories a",
                "references": ".entry-content a, .post-content a"
            },
            "kenh14": {
                "domain": "kenh14.vn",
                "title": "h1.kbwc-title, .article-title h1",
                "content": ".knc-content p, .article-content p",
                "images": ".knc-content img, .article-content img",
                "author": ".kbwc-author, .author-name",
                "time": ".kbwc-time, .article-time",
                "highlight": ".kbwc-sapo, .sapo",
                "topic": ".kbwc-tags a, .breadcrumb a",
                "references": ".knc-content a, .article-content a"
            },
            "soha": {
                "domain": "soha.vn",
                "title": "h1.detail-title, .article-title h1",
                "content": ".detail-content p, .article-content p",
                "images": ".detail-content img, .article-content img",
                "author": ".detail-author, .author-name",
                "time": ".detail-time, .article-time",
                "highlight": ".detail-sapo, .sapo",
                "topic": ".detail-tags a, .breadcrumb a",
                "references": ".detail-content a, .article-content a"
            },
            "vnanet": {
                "domain": "vnanet.vn",
                "title": "h1.detail-title, .news-title h1",
                "content": ".detail-content p, .news-content p",
                "images": ".detail-content img, .news-content img",
                "author": ".detail-author, .news-author",
                "time": ".detail-time, .news-time",
                "highlight": ".detail-sapo, .news-summary",
                "topic": ".detail-tags a, .news-tags a",
                "references": ".detail-content a, .news-content a"
            },
            "techrum": {
                "domain": "techrum.vn",
                "title": "h1.entry-title, .post-title h1",
                "content": ".entry-content p, .post-content p",
                "images": ".entry-content img, .post-content img",
                "author": ".author-name, .post-author",
                "time": ".entry-date, .post-date",
                "highlight": ".entry-summary, .post-excerpt",
                "topic": ".entry-tags a, .post-tags a",
                "references": ".entry-content a, .post-content a"
            },
            "wired": {
                "domain": "wired.com",
                "title": "h1, .ContentHeaderHed",
                "content": ".ArticleBodyWrapper p, .post-content p",
                "images": ".ArticleBodyWrapper img, .post-content img",
                "author": ".BaseWrap-sc, .author-name",
                "time": ".BaseWrap-sc time, .article-time",
                "highlight": ".ContentHeaderDek, .excerpt",
                "topic": ".ArticleTags a, .tags a",
                "references": ".ArticleBodyWrapper a, .post-content a"
            },
            "arstechnica": {
                "domain": "arstechnica.com",
                "title": "h1.heading, .article-title h1",
                "content": ".post-content p, .article-content p",
                "images": ".post-content img, .article-content img",
                "author": ".author, .byline",
                "time": ".post-time, .article-time",
                "highlight": ".excerpt, .summary",
                "topic": ".post-categories a, .tags a",
                "references": ".post-content a, .article-content a"
            },
            "venturebeat": {
                "domain": "venturebeat.com",
                "title": "h1.article-title, .post-title h1",
                "content": ".article-content p, .post-content p",
                "images": ".article-content img, .post-content img",
                "author": ".author-name, .byline",
                "time": ".the-time, .article-time",
                "highlight": ".article-excerpt, .excerpt",
                "topic": ".article-tags a, .categories a",
                "references": ".article-content a, .post-content a"
            },
            "ft": {
                "domain": "ft.com",
                "title": "h1.headline, .article-title h1",
                "content": ".n-content-body p, .article-body p",
                "images": ".n-content-body img, .article-body img",
                "author": ".n-content-tag, .author",
                "time": ".n-content-tag time, .article-time",
                "highlight": ".n-content-standfirst, .standfirst",
                "topic": ".n-content-tag a, .tags a",
                "references": ".n-content-body a, .article-body a"
            },
            "reuters": {
                "domain": "reuters.com",
                "title": "h1, .ArticleHeader_headline",
                "content": ".StandardArticleBody_body p, .article-body p",
                "images": ".StandardArticleBody_body img, .article-body img",
                "author": ".Attribution_author, .author",
                "time": ".Attribution_timestamp, .article-time",
                "highlight": ".StandardArticleBody_trustBadgeContainer, .summary",
                "topic": ".ArticleHeader_channel a, .breadcrumbs a",
                "references": ".StandardArticleBody_body a, .article-body a"
            },
            "bbc": {
                "domain": "bbc.com",
                "title": "h1, .story-body h1",
                "content": ".story-body p, .article-body p",
                "images": ".story-body img, .article-body img",
                "author": ".byline, .author",
                "time": ".date, .article-time",
                "highlight": ".story-body .intro, .summary",
                "topic": ".tags a, .breadcrumbs a",
                "references": ".story-body a, .article-body a"
            },
            "nytimes": {
                "domain": "nytimes.com",
                "title": "h1, .headline",
                "content": ".StoryBodyCompanionColumn p, .story-body p",
                "images": ".StoryBodyCompanionColumn img, .story-body img",
                "author": ".byline, .author",
                "time": ".timestamp, .article-time",
                "highlight": ".story-summary, .summary",
                "topic": ".keywords a, .tags a",
                "references": ".StoryBodyCompanionColumn a, .story-body a"
            }
        }

        self.PARSERS_LINKS = {
            "techcrunch": {
                "domain": "techcrunch.com",
                "links": "a.loop-card__title-link, .post-title a"
            },
            "vnexpress": {
                "domain": "vnexpress.net", 
                "links": ".wrapper-topstory-folder a[href*='vnexpress.net'], .item-news a"
            },
            "genk": {
                "domain": "genk.vn",
                "links": ".knswli-list-item a, .item-title a"
            },
            "tinhte": {
                "domain": "tinhte.vn",
                "links": ".structItem-title a, .node-title a"
            },
            "vietnamnet": {
                "domain": "vietnamnet.vn",
                "links": ".article-title a, .item-title a"
            },
            "techz": {
                "domain": "techz.vn",
                "links": ".entry-title a, .post-title a"
            },
            "techradar": {
                "domain": "techradar.com",
                "links": ".listingResult h3 a, .article-link"
            },
            "theverge": {
                "domain": "theverge.com",
                "links": ".duet--content-cards--content-card h2 a, .entry-title a"
            },
            "engadget": {
                "domain": "engadget.com",
                "links": ".js-stream-content h2 a, .article-title a"
            },
            "zdnet": {
                "domain": "zdnet.com",
                "links": ".headline a, .story-link"
            },
            "gizmodo": {
                "domain": "gizmodo.com",
                "links": ".headline a, .post-link"
            },
            "mashable": {
                "domain": "mashable.com",
                "links": ".card-title a, .article-link"
            },
            "cnet": {
                "domain": "cnet.com",
                "links": ".assetHed a, .story-link"
            },
            "vnreview": {
                "domain": "vnreview.vn",
                "links": ".post-title a, .item-title a"
            },
            "echip": {
                "domain": "echip.vn",
                "links": ".entry-title a, .post-title a"
            },
            "vnz": {
                "domain": "vn-z.vn",
                "links": ".post-title a, .item-title a"
            },
            "techvify": {
                "domain": "techvify.com",
                "links": ".post-title a, .entry-title a"
            },
            "vietnaminsiders": {
                "domain": "vietnaminsiders.com",
                "links": ".entry-title a, .post-title a"
            },
            "kenh14": {
                "domain": "kenh14.vn",
                "links": ".kbwc-title a, .item-title a"
            },
            "soha": {
                "domain": "soha.vn",
                "links": ".detail-title a, .item-title a"
            },
            "vnanet": {
                "domain": "vnanet.vn",
                "links": ".detail-title a, .news-title a"
            },
            "techrum": {
                "domain": "techrum.vn",
                "links": ".entry-title a, .post-title a"
            },
            "wired": {
                "domain": "wired.com",
                "links": ".summary-item__hed a, .article-link"
            },
            "arstechnica": {
                "domain": "arstechnica.com",
                "links": ".heading a, .post-link"
            },
            "venturebeat": {
                "domain": "venturebeat.com",
                "links": ".article-title a, .post-title a"
            },
            "ft": {
                "domain": "ft.com",
                "links": ".headline a, .story-link"
            },
            "reuters": {
                "domain": "reuters.com",
                "links": ".story-title a, .article-link"
            },
            "bbc": {
                "domain": "bbc.com",
                "links": ".gs-c-promo-heading__title, .story-link"
            },
            "nytimes": {
                "domain": "nytimes.com",
                "links": ".headline a, .story-link"
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

    def test_parser(self, domain_name):
        """Test parser cho một domain cụ thể"""
        if domain_name not in self.PARSERS:
            print(f"❌ Domain '{domain_name}' không có parser")
            return False
            
        config = self.PARSERS[domain_name]
        domain = config["domain"]
        
        print(f"🧪 Testing parser cho {domain_name} ({domain})")
        print("=" * 50)
        
        try:
            # Test get links
            if domain_name in self.PARSERS_LINKS:
                print(f"✅ Links parser: {self.PARSERS_LINKS[domain_name]['links']}")
            else:
                print("❌ Chưa có links parser")
                
            # Test content parsers
            for field, selector in config.items():
                if field != "domain" and selector:
                    print(f"✅ {field}: {selector}")
                elif field != "domain":
                    print(f"❌ {field}: Chưa có selector")
                    
            return True
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False
    
    def list_all_domains(self):
        """Liệt kê tất cả domains đã cấu hình"""
        print("📋 Danh sách tất cả domains đã cấu hình:")
        print("=" * 50)
        
        for i, (key, config) in enumerate(self.PARSERS.items(), 1):
            has_links = "✅" if key in self.PARSERS_LINKS else "❌"
            print(f"{i:2d}. {key:15s} → {config['domain']:25s} {has_links}")
            
        print(f"\n📊 Tổng cộng: {len(self.PARSERS)} domains")
        print("✅ = Có links parser, ❌ = Chưa có links parser")

# Test function
def main():
    """Hàm test"""
    crawler = NewsCrawler()
    
    print("🤖 News Parser Configuration Tester")
    print("=" * 60)
    print("1. 📋 Liệt kê tất cả domains")
    print("2. 🧪 Test parser cho domain cụ thể")
    print("3. 🚀 Test tất cả parsers")
    
    choice = input("\nChọn chức năng (1-3): ").strip()
    
    if choice == "1":
        crawler.list_all_domains()
        
    elif choice == "2":
        domain_name = input("Nhập tên domain (vd: techcrunch, vnexpress): ").strip()
        crawler.test_parser(domain_name)
        
    elif choice == "3":
        print("🧪 Testing tất cả parsers...")
        print("=" * 60)
        for domain_name in crawler.PARSERS.keys():
            crawler.test_parser(domain_name)
            print()
            
    else:
        print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()