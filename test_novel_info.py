"""Test cases for novel information crawler."""

import unittest
from novel_info import NovelInfo
import time
import requests  # type: ignore
from pathlib import Path
from epub_generator import EpubGenerator


class TestNovelInfo(unittest.TestCase):
    """Test cases for NovelInfo class."""

    def setUp(self):
        """Set up test cases."""
        self.test_url = "https://czbooks.net/n/s6pbed"
        self.crawler = NovelInfo(self.test_url)

    def test_get_info_success(self):
        """Test if novel information can be retrieved correctly."""
        info = self.crawler.get_info()
        
        # 確認沒有錯誤
        self.assertNotIn('error', info)
        
        # 檢查必要欄位是否存在
        required_fields = [
            'title', 'author', 'first_chapter',
            'last_chapter', 'total_chapters'
        ]
        for field in required_fields:
            self.assertIn(field, info)
        
        # 檢查資料正確性
        self.assertEqual(info['title'], '誰讓他修仙的！')
        self.assertEqual(info['author'], '最白的烏鴉')
        self.assertEqual(
            info['first_chapter'],
            '第1章 今日宜出行，不宜作弊'
        )
        self.assertEqual(info['total_chapters'], 1205)

    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        invalid_crawler = NovelInfo("https://czbooks.net/invalid_url")
        info = invalid_crawler.get_info()
        self.assertIn('error', info)

    def test_data_types(self):
        """Test if returned data types are correct."""
        info = self.crawler.get_info()
        self.assertIsInstance(info['title'], str)
        self.assertIsInstance(info['author'], str)
        self.assertIsInstance(info['first_chapter'], str)
        self.assertIsInstance(info['last_chapter'], str)
        self.assertIsInstance(info['total_chapters'], int)

    def test_chapter_urls(self):
        """Test if chapter URLs are correctly formatted."""
        info = self.crawler.get_info()
        self.assertIn('chapters', info)
        self.assertIsInstance(info['chapters'], list)
        self.assertTrue(len(info['chapters']) > 0)
        
        first_chapter = info['chapters'][0]
        self.assertIn('title', first_chapter)
        self.assertIn('url', first_chapter)
        self.assertTrue(
            first_chapter['url'].startswith('https://czbooks.net')
        )

    def test_request_delay(self):
        """Test if requests are properly delayed."""
        start_time = time.time()
        
        # 連續發送3個請求
        info = self.crawler.get_info()
        chapter_url = info['chapters'][0]['url']
        self.crawler.get_chapter_content(chapter_url)
        self.crawler.get_chapter_content(chapter_url)
        
        elapsed_time = time.time() - start_time
        
        # 修改時間檢查
        min_expected_time = 1.5  # 最小延遲總和 (3 * 0.5)
        self.assertGreaterEqual(
            elapsed_time,
            min_expected_time,
            f"Requests were too fast: {elapsed_time:.2f}s"
        )
        
        max_expected_time = 5  # 合理的最大延遲 (3 * 1 + buffer)
        self.assertLessEqual(
            elapsed_time,
            max_expected_time,
            f"Requests were too slow: {elapsed_time:.2f}s"
        )

    def test_retry_mechanism(self):
        """Test if retry mechanism works."""
        # 使用一個必定失敗的 URL
        bad_url = "https://nonexistent.example.com"
        crawler = NovelInfo(bad_url)
        
        # 應該會重試指定次數後失敗
        with self.assertRaises(requests.RequestException):
            crawler._request_with_retry(bad_url)

    def test_custom_output_path(self):
        """Test if custom output path works."""
        # 建立測試目錄
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        try:
            # 獲取小說資訊
            info = self.crawler.get_info()
            if 'error' in info:
                self.fail(f"Failed to get novel info: {info['error']}")
            
            # 只下載第一章來測試
            chapter = info['chapters'][0]
            content = self.crawler.get_chapter_content(chapter['url'])
            
            # 生成 EPUB
            generator = EpubGenerator(
                info['title'],
                info['author'],
                [{
                    'title': content['title'],
                    'content': content['content']
                }]
            )
            
            # 測試自定義路徑
            output_path = str(test_dir / f"{info['title']}.epub")
            actual_path = generator.generate(output_path)
            
            # 驗證
            self.assertEqual(actual_path, output_path)
            self.assertTrue(Path(output_path).exists())
            self.assertGreater(Path(output_path).stat().st_size, 0)
            
        finally:
            # 清理測試檔案和目錄
            if test_dir.exists():
                for file in test_dir.glob('*.epub'):
                    file.unlink()
                test_dir.rmdir()

    def test_parallel_download(self):
        """Compare performance between serial and parallel download."""
        info = self.crawler.get_info()
        test_chapters = info['chapters'][:10]  # 測試前10章
        
        print("\n=== 開始普通下載（單線程）===")
        start_time = time.time()
        normal_results = []
        for chapter in test_chapters:
            content = self.crawler.get_chapter_content(chapter['url'])
            if not content['error']:
                normal_results.append(content)
        normal_time = time.time() - start_time
        
        time.sleep(5)  # 休息5秒避免被封鎖
        
        print("\n=== 開始多線程下載 ===")
        start_time = time.time()
        parallel_results = self.crawler.download_chapters_parallel(
            test_chapters,
            max_workers=3
        )
        parallel_time = time.time() - start_time
        
        # 分行處理長字串
        improvement = (
            (normal_time - parallel_time) / normal_time * 100
        )
        print(f"\n普通下載時間: {normal_time:.2f}秒")
        print(f"多線程下載時間: {parallel_time:.2f}秒")
        print(f"效能提升: {improvement:.2f}%")
        
        # 確保內容相同
        self.assertEqual(len(normal_results), len(parallel_results))


def main():
    """Run the test cases."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main() 