"""Test cases for EPUB generator."""

import unittest
from epub_generator import EpubGenerator
from pathlib import Path


class TestEpubGenerator(unittest.TestCase):
    """Test cases for EpubGenerator class."""

    def setUp(self):
        """Set up test cases."""
        self.test_title = "測試小說"
        self.test_author = "測試作者"
        self.test_chapters = [
            {
                'title': '第一章',
                'content': '這是第一章的內容。\n有多行文字。\n'
            },
            {
                'title': '第二章',
                'content': '這是第二章的內容。\n也有多行文字。\n'
            }
        ]
        self.generator = EpubGenerator(
            self.test_title,
            self.test_author,
            self.test_chapters
        )

    def test_epub_generation(self):
        """Test if EPUB file can be generated correctly."""
        # 生成 EPUB 檔案
        output_path = self.generator.generate()
        
        # 檢查檔案是否存在
        self.assertTrue(Path(output_path).exists())
        
        # 檢查檔案大小是否合理 (至少應該有1KB)
        self.assertGreater(Path(output_path).stat().st_size, 1024)
        
        # 清理測試檔案
        Path(output_path).unlink()

    def test_custom_output_path(self):
        """Test if custom output path works."""
        test_path = "test_output.epub"
        output_path = self.generator.generate(test_path)
        
        # 檢查檔案是否在指定位置
        self.assertEqual(output_path, test_path)
        self.assertTrue(Path(test_path).exists())
        
        # 清理測試檔案
        Path(test_path).unlink()

    def test_invalid_content(self):
        """Test handling of invalid content."""
        # 測試空內容
        empty_chapters = []
        generator = EpubGenerator(
            self.test_title,
            self.test_author,
            empty_chapters
        )
        
        # 應該仍然能生成檔案，只是沒有章節
        output_path = generator.generate()
        self.assertTrue(Path(output_path).exists())
        
        # 清理測試檔案
        Path(output_path).unlink()

    def tearDown(self):
        """Clean up after tests."""
        # 確保所有測試檔案都被清理
        test_files = Path('.').glob('*.epub')
        for file in test_files:
            try:
                file.unlink()
            except OSError:
                pass


def main():
    """Run the test cases."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main() 