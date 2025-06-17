import csv
import gzip
import re
import requests
import tempfile
from io import BytesIO, StringIO
from typing import List, Dict, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import logging

logger = logging.getLogger(__name__)

class GutenbergUtils:
    """Utility class for Project Gutenberg integration"""
    
    GUTENBERG_CSV_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"
    GUTENBERG_TEXT_URL = "https://www.gutenberg.org/files/{}/pg{}.txt"
    GUTENBERG_ALTERNATIVE_URL = "https://www.gutenberg.org/ebooks/{}.txt.utf-8"
    
    def __init__(self):
        self.catalog: List[Dict] = []
        
    def load_catalog(self) -> List[Dict]:
        """Load and parse the Gutenberg catalog"""
        try:
            logger.info("Loading Gutenberg catalog...")
            response = requests.get(self.GUTENBERG_CSV_URL, timeout=30)
            response.raise_for_status()
            
            # Decompress and parse CSV
            with gzip.open(BytesIO(response.content), 'rt', encoding='utf-8') as f:
                self.catalog = list(csv.DictReader(f))
            
            logger.info(f"Loaded {len(self.catalog)} books from Gutenberg catalog")
            return self.catalog
            
        except Exception as e:
            logger.error(f"Error loading Gutenberg catalog: {e}")
            return []
    
    def search_books(self, search_term: str = "", language_filter: str = "all", max_results: int = 100) -> List[Dict]:
        """Search books in the catalog"""
        if not self.catalog:
            self.load_catalog()
        
        if not search_term:
            return []
        
        search_term = search_term.lower()
        filtered_books = []
        
        for book in self.catalog:
            # Language filter
            if language_filter != "all" and book.get("Language", "").lower() != language_filter.lower():
                continue
            
            # Text search in title and authors
            title = book.get("Title", "").lower()
            authors = book.get("Authors", "").lower()
            
            if search_term in title or search_term in authors:
                filtered_books.append(book)
                
                if len(filtered_books) >= max_results:
                    break
        
        return filtered_books
    
    def get_book_text(self, book_id: str) -> Optional[str]:
        """Download text content from Gutenberg"""
        try:
            # Try primary URL first
            url = self.GUTENBERG_TEXT_URL.format(book_id, book_id)
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                # Try alternative URL
                url = self.GUTENBERG_ALTERNATIVE_URL.format(book_id)
                response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to download text for book {book_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading text for book {book_id}: {e}")
            return None
    
    def clean_gutenberg_text(self, text: str) -> str:
        """Clean Gutenberg text by removing headers and footers"""
        if not text:
            return ""
        
        lines = text.split('\n')
        start_index = 0
        end_index = len(lines)
        
        # Find start of actual content (after Project Gutenberg header)
        for i, line in enumerate(lines):
            if "*** START OF" in line.upper() or "***START OF" in line.upper():
                start_index = i + 1
                break
            elif "CHAPTER" in line.upper() or "CHAPTER I" in line.upper():
                start_index = i
                break
        
        # Find end of actual content (before Project Gutenberg footer)
        for i in range(len(lines) - 1, -1, -1):
            if "*** END OF" in lines[i].upper() or "***END OF" in lines[i].upper():
                end_index = i
                break
        
        # Extract content
        content_lines = lines[start_index:end_index]
        
        # Remove empty lines at the beginning and end
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()
        
        cleaned_text = '\n'.join(content_lines)
        return cleaned_text
    
    def create_epub_from_text(self, text: str, title: str, author: str = "Unknown", 
                             language: str = "en", book_id: str = "") -> str:
        """Create an EPUB file from text content"""
        try:
            # Clean and prepare text
            cleaned_text = self.clean_gutenberg_text(text)
            
            # Create EPUB
            book = epub.EpubBook()
            book.set_identifier(f'gutenberg-{book_id}')
            book.set_title(title)
            book.set_language(language)
            book.add_author(author)
            
            # Split text into chapters (simple approach)
            chapters = self._split_text_into_chapters(cleaned_text, title)
            
            # Add chapters to book
            spine = ['nav']
            toc = []
            
            for i, (chapter_title, chapter_text) in enumerate(chapters):
                chapter = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{i+1}.xhtml',
                    lang=language
                )
                chapter.content = f'<html><head><title>{chapter_title}</title></head><body><h1>{chapter_title}</h1><p>{chapter_text.replace(chr(10), "</p><p>")}</p></body></html>'
                
                book.add_item(chapter)
                spine.append(chapter)
                toc.append(chapter)
            
            # Add navigation
            book.toc = toc
            book.spine = spine
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Save EPUB to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.epub')
            epub.write_epub(temp_file.name, book)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error creating EPUB: {e}")
            return ""
    
    def _split_text_into_chapters(self, text: str, title: str) -> List[tuple]:
        """Split text into chapters"""
        chapters = []
        
        # Try to find chapter markers
        chapter_pattern = re.compile(r'^\s*(CHAPTER|Chapter|KAPITTEL)\s*([IVX]+|\d+)', re.MULTILINE)
        matches = list(chapter_pattern.finditer(text))
        
        if matches:
            # Split by chapter markers
            for i, match in enumerate(matches):
                chapter_start = match.start()
                chapter_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                chapter_text = text[chapter_start:chapter_end].strip()
                chapter_title = match.group(0).strip()
                
                if chapter_text:
                    chapters.append((chapter_title, chapter_text))
        else:
            # No chapter markers found, split by length
            words = text.split()
            words_per_chapter = max(2000, len(words) // 10)  # Aim for ~10 chapters
            
            for i in range(0, len(words), words_per_chapter):
                chapter_words = words[i:i + words_per_chapter]
                chapter_text = ' '.join(chapter_words)
                chapter_title = f"Chapter {i // words_per_chapter + 1}"
                
                if chapter_text.strip():
                    chapters.append((chapter_title, chapter_text))
        
        # If no chapters found, use the entire text as one chapter
        if not chapters:
            chapters.append((title, text))
        
        return chapters
    
    def extract_gutenberg_id(self, input_text: str) -> Optional[str]:
        """Extract Gutenberg ID from URL or text"""
        if not input_text:
            return None
        
        # URL patterns
        url_patterns = [
            r'gutenberg\.org/ebooks/(\d+)',
            r'gutenberg\.org/files/(\d+)',
            r'gutenberg\.org.*?/(\d+)',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, input_text)
            if match:
                return match.group(1)
        
        # Pure number
        if input_text.isdigit():
            return input_text
        
        return None
    
    def get_book_preview(self, book_id: str, max_chars: int = 2000) -> str:
        """Get a preview of the book text"""
        text = self.get_book_text(book_id)
        if not text:
            return "Preview not available"
        
        cleaned_text = self.clean_gutenberg_text(text)
        
        if len(cleaned_text) > max_chars:
            return cleaned_text[:max_chars] + "..."
        
        return cleaned_text 