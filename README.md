# News Crawler Project

Dự án thu thập và phân tích tin tức tự động được chuyển đổi từ Jupyter Notebook sang Python.

## Tính năng

### 🚀 News Crawler (`news_crawler.py`)
- **Chức năng đầy đủ**: Thu thập tin tức từ nhiều website
- **AI Summarization**: Tóm tắt bài viết bằng Gemini AI
- **SEO Analysis**: Phân tích dữ liệu SEO
- **Auto Scheduling**: Chạy tự động theo lịch
- **Multi-domain**: Hỗ trợ TechCrunch, VnExpress, TechRadar, VietnamNet

### 📰 Simple Crawler (`simple_crawler.py`)
- **Phiên bản đơn giản**: Test và crawl nhanh
- **Local AI**: Sử dụng Transformers để tóm tắt
- **Batch Processing**: Xử lý nhiều URL cùng lúc
- **Export Data**: Xuất ra JSON và CSV

## Cài đặt

### 1. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Cài đặt Chrome Browser
- Tải và cài đặt Google Chrome
- ChromeDriver sẽ được tự động tải về

## Sử dụng

### News Crawler (Phiên bản đầy đủ)
```bash
python news_crawler.py
```

Chọn chức năng:
1. **Crawl tự động theo lịch** - Chạy liên tục
2. **Crawl một URL cụ thể** - Test một link
3. **Crawl tất cả domain một lần** - Thu thập toàn bộ
4. **Lấy thông tin SEO từ URL** - Phân tích SEO

### Simple Crawler (Phiên bản test)
```bash
python simple_crawler.py
```

Chọn chức năng:
1. **Crawl URLs mẫu** - Test với links có sẵn
2. **Crawl URL tùy chỉnh** - Nhập link muốn crawl
3. **Crawl nhiều URLs từ file** - Xử lý batch

## Cấu hình

### Parser Configs (`parsers.json`)
```json
{
    "techcrunch": {
        "domain": "techcrunch.com",
        "title": "div.article-hero__middle",
        "content": "div.entry-content",
        "images": "div.entry-content img",
        "author": "a.wp-block-tc23-author-card-name__link",
        "time": "time",
        "topic": "div.tc23-post-relevant-terms__terms a",
        "references": "div.entry-content a"
    }
}
```

### Parser Links (`parsers_links.json`)
```json
{
    "techcrunch": {
        "domain": "techcrunch.com",
        "links": "a.loop-card__title-link"
    }
}
```

## Output Files

### Dữ liệu bài viết
- `articles.json` - Bài viết chi tiết
- `articles_summarize.json` - Bài viết + tóm tắt AI
- `seo_data.json` - Dữ liệu SEO

### Test files
- `test_article.json` - Kết quả test một bài
- `sample_articles.json` - Kết quả URLs mẫu
- `single_article.json` - Kết quả URL đơn lẻ

## API Keys

### Gemini AI (cho news_crawler.py)
Cập nhật `GEMINI_API_KEY` trong file `news_crawler.py`:
```python
self.GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```

## Troubleshooting

### Lỗi import
```bash
pip install selenium beautifulsoup4 webdriver-manager requests schedule pandas
```

### Lỗi ChromeDriver
- Đảm bảo Chrome đã được cài đặt
- Kiểm tra kết nối internet để tải ChromeDriver

### Lỗi AI Model
```bash
pip install transformers torch
```

### Lỗi Gemini API
- Kiểm tra API key
- Đảm bảo có quota API

## Cấu trúc Files

```
Crawl Data - IEC/
├── news_crawler.py          # Crawler đầy đủ
├── simple_crawler.py        # Crawler đơn giản  
├── requirements.txt         # Dependencies
├── README.md               # Documentation
├── parsers.json            # Cấu hình parser (auto-generated)
├── parsers_links.json      # Cấu hình links (auto-generated)
└── output files...         # JSON/CSV results
```

## Tính năng nâng cao

### Lập lịch tự động
- Crawl theo giờ/phút
- Lưu log thời gian
- Xử lý lỗi tự động

### SEO Analysis
- Meta title, description
- H1, H2 tags
- Internal/external links
- Word count

### AI Summarization
- Gemini API (online)
- Transformers (offline)
- Vietnamese support

## License

MIT License
