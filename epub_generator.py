"""EPUB generator for novel crawler."""

from typing import List, Dict
from ebooklib import epub  # type: ignore
from pathlib import Path


class EpubGenerator:
    """Class to handle EPUB generation."""

    def __init__(
        self,
        title: str,
        author: str,
        chapters: List[Dict[str, str]],
        language: str = 'zh-TW'
    ) -> None:
        """Initialize EPUB generator."""
        self.title = title
        self.author = author
        self.chapters = chapters
        self.language = language
        self.book = epub.EpubBook()

    def generate(self, output_path: str | None = None) -> str:
        """Generate EPUB file."""
        # 設置書籍基本資訊
        self.book.set_title(self.title)
        self.book.set_language(self.language)
        self.book.add_author(self.author)

        # 創建章節
        chapter_items = []
        for idx, chapter in enumerate(self.chapters, 1):
            # 創建章節
            c = epub.EpubHtml(
                title=chapter['title'],
                file_name=f'chapter_{idx}.xhtml',
                content=self._format_chapter_content(
                    chapter['title'],
                    chapter['content']
                )
            )
            self.book.add_item(c)
            chapter_items.append(c)

        # 創建目錄
        self.book.toc = chapter_items
        self.book.spine = ['nav'] + chapter_items

        # 添加導航文件
        self.book.add_item(epub.EpubNcx())
        nav = epub.EpubNav()
        self.book.add_item(nav)

        # 設置輸出路徑
        if output_path is None:
            output_path = str(Path.cwd() / f"{self.title}.epub")

        # 生成 EPUB 檔案
        epub.write_epub(output_path, self.book)
        return output_path

    def _format_chapter_content(self, title: str, content: str) -> str:
        """Format chapter content with HTML."""
        html_content = f"""
        <html>
            <head>
                <title>{title}</title>
                <link rel="stylesheet" href="style.css" type="text/css"/>
            </head>
            <body>
                <h1>{title}</h1>
                {self._convert_text_to_html(content)}
            </body>
        </html>
        """
        return html_content

    def _convert_text_to_html(self, text: str) -> str:
        """Convert plain text to HTML paragraphs."""
        paragraphs = text.split('\n')
        html_paragraphs = [
            f"<p>{p}</p>" for p in paragraphs if p.strip()
        ]
        return '\n'.join(html_paragraphs)