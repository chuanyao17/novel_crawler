"""Novel information crawler for czbooks.net."""

from typing import List, Optional, TypedDict, Dict
import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import time
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tqdm import tqdm
from epub_generator import EpubGenerator


class ChapterInfo(TypedDict):
    """Type definition for chapter information."""
    title: str
    url: str


class ChapterContent(TypedDict):
    """Type definition for chapter content."""
    title: str
    content: str
    error: Optional[str]


class NovelData(TypedDict, total=False):
    """Type definition for novel information."""
    title: str
    author: str
    status: str
    first_chapter: Optional[str]
    last_chapter: Optional[str]
    total_chapters: int
    chapters: List[ChapterInfo]
    error: str


class NovelInfo:
    """Class to handle novel information extraction."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
        self.delay_range = (0.5, 1)  # 修改延遲範圍：0.5-1秒

    def _request_with_retry(
        self,
        url: str,
        max_retries: int = 3
    ) -> requests.Response:
        """Make HTTP request with retry mechanism."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                # 加入延遲
                delay = random.uniform(*self.delay_range)
                time.sleep(delay)
                
                # 分行處理長字串
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=5
                )
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                last_exception = e
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise last_exception
                time.sleep(1)  # 固定重試延遲為1秒
        
        raise requests.RequestException("All retry attempts failed")

    def get_info(self) -> NovelData:
        """Get novel info including title, author and chapters."""
        try:
            response = self._request_with_retry(self.url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_elem = soup.select_one('.novel-detail .info .title')
            if not title_elem:
                print("\nDEBUG: 找不到標題")
                raise ValueError("無法找書名")
            
            author_elem = soup.select_one('.novel-detail .info .author a')
            if not author_elem:
                print("\nDEBUG: 找不到作者")
                raise ValueError("無法找到作者資訊")
            
            chapters = soup.select('.chapter-list li a')
            chapter_list: List[ChapterInfo] = []
            
            base_url = 'https://czbooks.net'
            for chapter in chapters:
                href = chapter.get('href', '')
                if href.startswith('//czbooks.net'):
                    href = href.replace('//czbooks.net', '')
                chapter_url = f"{base_url}{href}"
                
                chapter_list.append({
                    'title': chapter.text.strip(),
                    'url': chapter_url
                })
            
            if not chapter_list:
                print("\nDEBUG: 找不到章節列表")
                raise ValueError("無法獲章節列表")
            
            title = title_elem.text.strip().replace('《', '').replace('》', '')
            author = author_elem.text.strip()
            
            # 獲取連載狀態
            status_selector = '.novel-detail .state td:contains("連載狀態") + td'
            status_elem = soup.select_one(status_selector)
            if not status_elem:
                status = "未知"
            else:
                status = status_elem.text.strip()
            
            return {
                'title': title,
                'author': author,
                'status': status,
                'first_chapter': chapter_list[0]['title'],
                'last_chapter': chapter_list[-1]['title'],
                'total_chapters': len(chapter_list),
                'chapters': chapter_list
            }
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            return {
                'error': f'獲取資訊失敗: {str(e)}',
                'title': '',
                'author': '',
                'status': '',
                'first_chapter': None,
                'last_chapter': None,
                'total_chapters': 0,
                'chapters': []
            }

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        """Get content of a specific chapter."""
        try:
            response = self._request_with_retry(chapter_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 獲取章節標題
            title_elem = soup.select_one('.name')
            if not title_elem:
                raise ValueError("無法找到章節標題")
            
            # 獲取章節內容
            content_elem = soup.select_one('.content')
            if not content_elem:
                raise ValueError("無法找到章節內容")
            
            # 清理內容
            content = self._clean_content(content_elem.text)
            
            # 處理標題，移除書名
            title = title_elem.text.strip()
            if '《' in title and '》' in title:
                title = title.split('》')[-1].strip()
            
            return {
                'title': title,
                'content': content,
                'error': None
            }
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            return {
                'title': '',
                'content': '',
                'error': f'取章節內容失敗: {str(e)}'
            }

    def _clean_content(self, content: str) -> str:
        """Clean up chapter content."""
        # 移除多餘空白行
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line]
        
        # 移除廣告相關文字
        ad_keywords = [
            '本章完',
            '手機用戶請訪問',
            'czbooks.net',
            '////',
            '----',
            '＊＊＊',
        ]
        
        cleaned_lines = []
        for line in lines:
            if not any(keyword in line for keyword in ad_keywords):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def download_chapters_parallel(
        self,
        chapters: List[ChapterInfo],
        max_workers: int = 3
    ) -> List[Dict[str, str]]:
        """Download chapters using multiple threads."""
        results = []
        print(f"\n開始多線程下載 (使用 {max_workers} 個線程)...")
        
        def download_single(chapter: ChapterInfo) -> Optional[Dict[str, str]]:
            """Helper function to download a single chapter."""
            content = self.get_chapter_content(chapter['url'])
            if not content['error']:
                return {
                    'title': content['title'],
                    'content': content['content']
                }
            return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(download_single, chapter)
                for chapter in chapters
            ]
            
            for future in tqdm(futures, desc="下載進度"):
                result = future.result()
                if result:
                    results.append(result)
        
        return results


def main() -> None:
    """Main function to demonstrate usage."""
    url = input("請輸入小說網址: ")
    output_dir = input("請輸入輸出目錄 (直接按 Enter 使用當前目錄): ").strip()
    
    if not output_dir:
        output_dir = "."
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    crawler = NovelInfo(url)
    info = crawler.get_info()
    
    if 'error' not in info:
        print("\n=== 小說資訊 ===")
        print(f"書名: {info['title']}")
        print(f"作者: {info['author']}")
        print(f"連載狀態: {info['status']}")
        print(f"總章數: {info['total_chapters']}")
        
        # 選擇下載範圍
        while True:
            try:
                print("\n請選擇下載範圍:")
                print("1. 下載全部章節")
                print("2. 下載指定範圍")
                print("3. 下載最新章")
                choice = input("請選擇 (1-3): ").strip()
                
                if choice == '1':
                    start_idx = 0
                    end_idx = len(info['chapters'])
                    break
                elif choice == '2':
                    prompt = f"請輸入起始章節 (1-{info['total_chapters']}): "
                    start = int(input(prompt))
                    
                    prompt = f"請輸入結束章節 (1-{info['total_chapters']}): "
                    end = int(input(prompt))
                    
                    if 1 <= start <= end <= info['total_chapters']:
                        start_idx = start - 1
                        end_idx = end
                        break
                    else:
                        print("輸入範圍無效，請重試")
                elif choice == '3':
                    num = int(input("請輸入要下載的最新章節數量: "))
                    if 1 <= num <= info['total_chapters']:
                        start_idx = info['total_chapters'] - num
                        end_idx = info['total_chapters']
                        break
                    else:
                        print("輸入數量無效，請重試")
                else:
                    print("無效選擇，請重試")
            except ValueError:
                print("請輸入有效的數字")
        
        # 使用多線程下載選定範圍的章節
        selected_chapters = info['chapters'][start_idx:end_idx]
        print(f"\n開始下載章節 {start_idx + 1} 到 {end_idx}...")
        
        chapters = crawler.download_chapters_parallel(
            selected_chapters,
            max_workers=3  # 使用3個線程
        )
        
        # 生成 EPUB
        if chapters:
            print("\n生成 EPUB 檔案...")
            generator = EpubGenerator(
                info['title'],
                info['author'],
                chapters
            )
            
            # 根據下載範圍和連載狀態生成檔名
            if start_idx == 0 and end_idx == info['total_chapters']:
                if info['status'] != '已完結':
                    filename = (
                        f"{info['title']}_"
                        f"第1章到第{info['total_chapters']}章_"
                        f"最新{info['last_chapter']}.epub"
                    )
                else:
                    filename = f"{info['title']}_全本.epub"
            else:
                # 分行處理長字串
                chapter_range = (
                    f"{info['title']}_"
                    f"第{start_idx + 1}章到第{end_idx}章.epub"
                )
                filename = chapter_range
            
            output_path = generator.generate(
                str(Path(output_dir) / filename)
            )
            print(f"EPUB 檔案已生成: {output_path}")
    else:
        print(info['error'])


if __name__ == "__main__":
    main() 