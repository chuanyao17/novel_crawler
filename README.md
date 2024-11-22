# Novel Crawler

一個用於下載小說並轉換為EPUB格式的爬蟲工具。目前支援 czbooks.net。

## 功能特點

- 小說資訊擷取
  - 標題、作者、連載狀態
  - 章節列表與排序
  - 自動清理廣告內容
- 下載功能
  - 多線程下載（效能提升40-50%）
  - 自定義下載範圍（全本/指定範圍/最新章節）
  - 自動重試機制
  - 智慧延遲控制
- EPUB 生成
  - 自動生成目錄
  - 智慧檔名（包含連載狀態與章節範圍）
  - 支援自定義輸出路徑
- 錯誤處理
  - 完整的錯誤處理機制
  - 詳細的錯誤提示
  - 自動重試機制

## 安裝需求

- Python 3.12+
- pip 套件管理器


## 安裝步驟
- clone 專案：
  ```bash
  git clone https://github.com/chuanyao17/novel_crawler.git
  ```
- 進入專案目錄：
  ```bash
  cd novel_crawler
  ```
- 建立虛擬環境:
  ```bash
  python -m venv venv
source venv/bin/activate # Linux/MacOS
.\venv\Scripts\activate # Windows
  ``` 
- 安裝套件：
  ```bash
  pip install -r requirements.txt
  ```
## 使用方法
- 執行程式：
  ```bash
  python novel_info.py
  ```
- 依照提示操作：
   - 輸入小說網址 (czbooks.net)
   - 選擇輸出目錄
   - 選擇下載範圍：
     - 全部章節
     - 指定範圍
     - 最新章節
等待下載完成，EPUB 檔案會生成在指定目錄
## 檔案結構
novel_crawler/
├── novel_info.py # 主程式：爬蟲核心功能
├── epub_generator.py # EPUB生成器：電子書生成功能
├── test_novel_info.py # 測試檔案：功能測試
├── requirements.txt # 依賴套件清單
├── checklist.md # 開發進度追蹤
└── README.md # 專案說明文件
## 開發測試
- 執行所有測試：：
  ```bash
  python -m unittest test_novel_info.py -v
  ```
## 注意事項

- 請遵守網站的使用規則
- 下載的內容僅供個人使用
- 不要過度頻繁地發送請求


