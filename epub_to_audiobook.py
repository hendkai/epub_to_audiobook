import sys
import os
import re
import io
import argparse
import html
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import requests
from typing import List, Tuple
from datetime import datetime, timedelta
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError
from mutagen.id3._frames import TIT2, TPE1, TALB, TRCK
import logging
from time import sleep
import dataclasses
from openai import OpenAI
from tqdm import tqdm
import time
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pydub import AudioSegment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),  # Hier wird die Log-Datei festgelegt
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


MAX_RETRIES = 12  # Max_retries constant for network errors
MAGIC_BREAK_STRING = " @BRK#"  # leading blank is for text split

TTS_AZURE = "azure"
TTS_OPENAI = "openai"

def read_config_file(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config

def save_config_file(config_file_path, config):
    with open(config_file_path, "w") as configfile:
        config.write(configfile)

def load_config(args):
    # Prioritize command line arguments over config file
    config = configparser.ConfigParser()

    # Try to read from the specified config file
    if args.config_file:
        config = read_config_file(args.config_file)

    # Override or add config values from command line arguments
    for key, value in vars(args).items():
        if value is not None:
            config.set("DEFAULT", key, str(value))

    return config

@dataclasses.dataclass
class AudioTags:
    title: str  # for TIT2
    author: str  # for TPE1
    book_title: str  # for TALB
    idx: int  # for TRCK


class GeneralConfig:
    def __init__(self, args):
        self.input_file = args.input_file
        self.output_folder = args.output_folder
        self.tts = args.tts
        self.preview = getattr(args, 'preview', False)
        self.newline_mode = getattr(args, 'newline_mode', 'double')
        self.chapter_start = getattr(args, 'chapter_start', 1)
        self.chapter_end = getattr(args, 'chapter_end', -1)
        self.remove_endnotes = getattr(args, 'remove_endnotes', False)
        self.output_text = getattr(args, 'output_text', False)
        self.one_file = getattr(args, 'one_file', False)
        self.language = getattr(args, 'language', None)
        self.output_format = getattr(args, 'output_format', 'mp3')
        self.voice_name = getattr(args, 'voice_name', None)
        self.model_name = getattr(args, 'model_name', None)
        self.break_duration = getattr(args, 'break_duration', None)
        
        # Logging setup
        log_level = getattr(args, 'log', 'INFO')
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Filter out options without user input
        self.filter_options()

    def filter_options(self):
        for attr, value in self.__dict__.items():
            if value is None or value == "":
                setattr(self, attr, None)

    def __str__(self):
        return f"input_file={self.input_file}, output_folder={self.output_folder}, tts={self.tts}, preview={self.preview}, newline_mode={self.newline_mode}, chapter_start={self.chapter_start}, chapter_end={self.chapter_end}, output_text={self.output_text}, remove_endnotes={self.remove_endnotes}, one_file={self.one_file}"


class TTSProvider:
    # Base provider interface
    def __init__(self, general_config: GeneralConfig):
        self.general_config = general_config

    def __str__(self) -> str:
        return f"{self.general_config}"

    def text_to_speech(self, *args, **kwargs):
        raise NotImplementedError


class AzureTTSProvider(TTSProvider):
    def __init__(
        self,
        general_config: GeneralConfig,
        voice_name,
        break_duration,
        output_format,
    ):
        super().__init__(general_config)

        # TTS provider specific config
        self.voice_name = voice_name
        self.break_duration = break_duration
        self.output_format = output_format

        # access token and expiry time
        self.access_token = None
        self.token_expiry_time = datetime.utcnow()

        subscription_key = os.environ.get("MS_TTS_KEY")
        region = os.environ.get("MS_TTS_REGION")

        if not subscription_key or not region:
            raise ValueError(
                "Please set MS_TTS_KEY and MS_TTS_REGION environment variables. Check https://github.com/p0n1/epub_to_audiobook#how-to-get-your-azure-cognitive-service-key."
            )

        self.TOKEN_URL = (
            f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        )
        self.TOKEN_HEADERS = {"Ocp-Apim-Subscription-Key": subscription_key}
        self.TTS_URL = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    def __str__(self) -> str:
        return (
            super().__str__()
            + f", voice_name={self.voice_name}, language={self.general_config.language}, break_duration={self.break_duration}, output_format={self.output_format}"
        )

    def is_access_token_expired(self) -> bool:
        return self.access_token is None or datetime.utcnow() >= self.token_expiry_time

    def auto_renew_access_token(self) -> str:
        if self.access_token is None or self.is_access_token_expired():
            logger.info(
                f"azure tts access_token doesn't exist or is expired, getting new one"
            )
            self.access_token = self.get_access_token()
            self.token_expiry_time = datetime.utcnow() + timedelta(minutes=9, seconds=1)
        return self.access_token

    def get_access_token(self) -> str:
        for retry in range(MAX_RETRIES):
            try:
                logger.info("Getting new access token")
                response = requests.post(self.TOKEN_URL, headers=self.TOKEN_HEADERS)
                response.raise_for_status()  # Will raise HTTPError for 4XX or 5XX status
                access_token = str(response.text)
                logger.info("Got new access token")
                return access_token
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Network error while getting access token (attempt {retry + 1}/{MAX_RETRIES}): {e}"
                )
                if retry < MAX_RETRIES - 1:
                    sleep(2**retry)
                else:
                    raise e
        raise Exception("Failed to get access token")

    def text_to_speech(
        self,
        text: str,
        output_file: str,
        audio_tags: AudioTags,
    ):
        # Adjust this value based on your testing
        max_chars = 1800 if self.general_config.language.startswith("zh") else 3000

        text_chunks = split_text(text, max_chars, self.general_config.language)

        audio_segments = []

        for i, chunk in enumerate(text_chunks, 1):
            logger.debug(
                f"Processing chunk {i} of {len(text_chunks)}, length={len(chunk)}, text=[{chunk}]"
            )
            escaped_text = html.escape(chunk)
            logger.debug(f"Escaped text: [{escaped_text}]")
            # replace MAGIC_BREAK_STRING with a break tag for section/paragraph break
            escaped_text = escaped_text.replace(
                MAGIC_BREAK_STRING.strip(),
                f" <break time='{self.break_duration}ms' /> ",
            )  # strip in case leading bank is missing
            logger.info(
                f"Processing chapter-{audio_tags.idx} <{audio_tags.title}>, chunk {i} of {len(text_chunks)}"
            )
            ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{self.general_config.language}'><voice name='{self.voice_name}'>{escaped_text}</voice></speak>"
            logger.debug(f"SSML: [{ssml}]")

            for retry in range(MAX_RETRIES):
                self.auto_renew_access_token()
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": self.output_format,
                    "User-Agent": "Python",
                }
                try:
                    logger.info(
                        "Sending request to Azure TTS, data length: " + str(len(ssml))
                    )
                    response = requests.post(
                        self.TTS_URL, headers=headers, data=ssml.encode("utf-8")
                    )
                    response.raise_for_status()  # Will raise HTTPError for 4XX or 5XX status
                    logger.info(
                        "Got response from Azure TTS, response length: "
                        + str(len(response.content))
                    )
                    audio_segments.append(io.BytesIO(response.content))
                    break
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        f"Error while converting text to speech (attempt {retry + 1}): {e}"
                    )
                    if retry < MAX_RETRIES - 1:
                        sleep(2**retry)
                    else:
                        raise e

        with open(output_file, "wb") as outfile:
            for segment in audio_segments:
                segment.seek(0)
                outfile.write(segment.read())

        set_audio_tags(output_file, audio_tags)


class OpenAITTSProvider(TTSProvider):
    def __init__(self, general_config: GeneralConfig, model, voice, format):
        super().__init__(general_config)
        self.model = model
        self.voice = voice
        self.format = format
        self.client = OpenAI()  # User should set OPENAI_API_KEY environment variable

    def __str__(self) -> str:
        return (
            super().__str__()
            + f", model={self.model}, voice={self.voice}, format={self.format}"
        )

    def text_to_speech(self, text: str, output_file: str, audio_tags: AudioTags):
        max_chars = 4000  # should be less than 4096 for OpenAI

        text_chunks = split_text(text, max_chars, self.general_config.language)

        audio_segments = []

        for i, chunk in enumerate(text_chunks, 1):
            logger.debug(
                f"Processing chunk {i} of {len(text_chunks)}, length={len(chunk)}, text=[{chunk}]"
            )
            # replace MAGIC_BREAK_STRING with blank space because OpenAI TTS doesn't support SSML
            chunk = chunk.replace(
                MAGIC_BREAK_STRING.strip(),
                "   ",
            )  # strip in case leading bank is missing
            logger.info(
                f"Processing chapter-{audio_tags.idx} <{audio_tags.title}>, chunk {i} of {len(text_chunks)}"
            )

            logger.debug(f"Text: [{chunk}], length={len(chunk)}")

            # NO retry for OpenAI TTS because SDK has built-in retry logic
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=chunk,
                response_format=self.format,
            )
            audio_segments.append(io.BytesIO(response.content))

        with open(output_file, "wb") as outfile:
            for segment in audio_segments:
                segment.seek(0)
                outfile.write(segment.read())

        set_audio_tags(output_file, audio_tags)


def sanitize_title(title: str) -> str:
    # replace MAGIC_BREAK_STRING with a blank space
    # strip incase leading bank is missing
    title = title.replace(MAGIC_BREAK_STRING.strip(), " ")
    sanitized_title = re.sub(r"[^\w\s]", "", title, flags=re.UNICODE)
    sanitized_title = re.sub(r"\s+", "_", sanitized_title.strip())
    return sanitized_title


def extract_chapters(
    epub_book: epub.EpubBook, newline_mode: str, remove_endnotes: bool
) -> List[Tuple[str, str]]:
    chapters = []
    for item in epub_book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content()
            soup = BeautifulSoup(content, "xml")
            title = soup.title.string if soup.title else ""
            raw = soup.get_text(strip=False)
            logger.debug(f"Raw text: <{raw[:100]}>")

            # Erste Bereinigung: Entferne übermäßige Leerzeichen und Zeilenumbrüche
            cleaned_text = raw.strip()
            
            # Ersetze Zeilenumbrüche basierend auf dem Modus
            if newline_mode == "single":
                cleaned_text = re.sub(r"[\n]+", " " + MAGIC_BREAK_STRING + " ", cleaned_text)
            elif newline_mode == "double":
                cleaned_text = re.sub(r"[\n]{2,}", " " + MAGIC_BREAK_STRING + " ", cleaned_text)
            elif newline_mode is None:
                cleaned_text = re.sub(r"\n", " ", cleaned_text)
            else:
                raise ValueError(f"Invalid newline mode: {newline_mode}")

            # Normalisiere Leerzeichen
            cleaned_text = re.sub(r"\s+", " ", cleaned_text)
            
            # Stelle sicher, dass vor und nach MAGIC_BREAK_STRING Leerzeichen sind
            cleaned_text = cleaned_text.replace(MAGIC_BREAK_STRING, " " + MAGIC_BREAK_STRING + " ")
            cleaned_text = re.sub(r"\s+", " ", cleaned_text)  # Entferne doppelte Leerzeichen
            
            # Entferne Leerzeichen vor Satzzeichen
            cleaned_text = re.sub(r'\s+([.,!?])', r'\1', cleaned_text)

            # Removes endnote numbers wenn aktiviert
            if remove_endnotes:
                cleaned_text = re.sub(r'(?<=[a-zA-Z.,!?;"])\d+', "", cleaned_text)

            logger.debug(f"Cleaned text: <{cleaned_text[:100]}>")

            # Titel verarbeiten
            if not title:
                title = cleaned_text[:60]
            title = sanitize_title(title)
            logger.debug(f"Sanitized title: <{title}>")

            chapters.append((title, cleaned_text))
            soup.decompose()
    return chapters


def is_special_char(char: str) -> bool:
    # Check if the character is a English letter, number or punctuation or a punctuation in Chinese, never split these characters.
    ord_char = ord(char)
    result = (
        (ord_char >= 33 and ord_char <= 126)
        or (char in "。，、？！：；“”‘’（）《》【】…—～·「」『』〈〉〖〗〔〕")
        or (char in "∶")
    )  # special unicode punctuation
    logger.debug(f"is_special_char> char={char}, ord={ord_char}, result={result}")
    return result


def split_text(text: str, max_chars: int, language: str) -> List[str]:
    chunks = []
    current_chunk = ""

    if language.startswith("zh"):  # Chinese
        for char in text:
            if len(current_chunk) + 1 <= max_chars or is_special_char(char):
                current_chunk += char
            else:
                chunks.append(current_chunk)
                current_chunk = char

        if current_chunk:
            chunks.append(current_chunk)

    else:
        words = text.split()

        for word in words:
            if len(current_chunk) + len(word) + 1 <= max_chars:
                current_chunk += (" " if current_chunk else "") + word
            else:
                chunks.append(current_chunk)
                current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

    logger.info(f"Split text into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks, 1):
        first_100 = chunk[:100]
        last_100 = chunk[-100:] if len(chunk) > 100 else ""
        logger.info(
            f"Chunk {i}: Length={len(chunk)}, Start={first_100}..., End={last_100}"
        )

    return chunks


def set_audio_tags(output_file, audio_tags):
    try:
        try:
            tags = ID3(output_file)
            logger.debug(tags)
        except ID3NoHeaderError:
            logger.debug(f"handling ID3NoHeaderError: {output_file}")
            tags = ID3()
        tags.add(TIT2(encoding=3, text=audio_tags.title))
        tags.add(TPE1(encoding=3, text=audio_tags.author))
        tags.add(TALB(encoding=3, text=audio_tags.book_title))
        tags.add(TRCK(encoding=3, text=str(audio_tags.idx)))
        tags.save(output_file)
    except Exception as e:
        logger.error(f"Error while setting audio tags: {e}, {output_file}")
        raise e  # TODO: use this raise to catch unknown errors for now


def process_chapter(chapter: Tuple[str, str], tts_provider: TTSProvider, output_folder: str, book_title: str, author: str, idx: int) -> AudioSegment:
    """
    Verarbeitet ein einzelnes Kapitel und konvertiert es in Audio.
    
    Args:
        chapter: Tuple aus (Titel, Text) des Kapitels
        tts_provider: Der TTS-Provider für die Audiokonvertierung
        output_folder: Ausgabeordner für die Audiodateien
        book_title: Titel des Buches
        author: Autor des Buches
        idx: Index des Kapitels
    
    Returns:
        AudioSegment: Das verarbeitete Audiokapitel
    """
    title, text = chapter
    
    # Erstelle die Ausgabedatei
    output_file = os.path.join(output_folder, f"chapter_{idx:03d}_{title}.mp3")
    
    # Erstelle die Audio-Tags
    audio_tags = AudioTags(
        title=title,
        author=author,
        book_title=book_title,
        idx=idx
    )
    
    # Konvertiere Text zu Sprache
    tts_provider.text_to_speech(text, output_file, audio_tags)
    
    # Lade die erstellte Audiodatei
    return AudioSegment.from_mp3(output_file)

def epub_to_audiobook(tts_provider: TTSProvider):
    # assign config values
    conf = tts_provider.general_config
    input_file = conf.input_file
    output_folder = conf.output_folder
    preview = conf.preview
    newline_mode = conf.newline_mode
    chapter_start = conf.chapter_start
    chapter_end = conf.chapter_end
    remove_endnotes = conf.remove_endnotes
    output_text = conf.output_text
    one_file = conf.one_file

    book = epub.read_epub(input_file)
    chapters = extract_chapters(book, newline_mode, remove_endnotes)

    os.makedirs(output_folder, exist_ok=True)

    # Get the book title and author from metadata or use fallback values
    book_title = "Untitled"
    author = "Unknown"
    if book.get_metadata("DC", "title"):
        book_title = book.get_metadata("DC", "title")[0][0]
    if book.get_metadata("DC", "creator"):
        author = book.get_metadata("DC", "creator")[0][0]

    # Filter out empty or very short chapters
    chapters = [(title, text) for title, text in chapters if text.strip()]

    logger.info(f"Chapters count: {len(chapters)}.")

    # Check chapter start and end args
    if chapter_start < 1 or chapter_start > len(chapters):
        raise ValueError(
            f"Chapter start index {chapter_start} is out of range. Check your input."
        )
    if chapter_end < -1 or chapter_end > len(chapters):
        raise ValueError(
            f"Chapter end index {chapter_end} is out of range. Check your input."
        )
    if chapter_end == -1:
        chapter_end = len(chapters)
    if chapter_start > chapter_end:
        raise ValueError(
            f"Chapter start index {chapter_start} is larger than chapter end index {chapter_end}. Check your input."
        )

    total_characters = 0  # Variable initialisieren

    start_time = time.time()  # Startzeit messen

    # Überprüfen Sie die one_file Option
    if one_file:
        # Logik für einzelne Ausgabedatei
        combined_audio = AudioSegment.empty()
        for idx, chapter in enumerate(chapters[chapter_start-1:chapter_end], start=chapter_start):
            # Verarbeite jeden Chapter
            audio = process_chapter(chapter, tts_provider, output_folder, book_title, author, idx)
            combined_audio += audio
            total_characters += len(chapter[1])
            
        # Speichere die kombinierte Audiodatei
        output_file = os.path.join(output_folder, f"{book_title}_complete.mp3")
        combined_audio.export(output_file, format="mp3")
    else:
        # Bestehende Logik für mehrere Dateien
        for idx, chapter in enumerate(chapters[chapter_start-1:chapter_end], start=chapter_start):
            audio = process_chapter(chapter, tts_provider, output_folder, book_title, author, idx)
            total_characters += len(chapter[1])

    elapsed_time = time.time() - start_time  # Gesamtzeit berechnen

    logger.info(f"✨ Total characters in selected chapters: {total_characters} ✨")
    logger.info(f"⌛ Elapsed Time: {elapsed_time:.2f} seconds ⌛")

    # Überprüfen Sie das Ausgabeformat
    if tts_provider.general_config.output_format.lower() != "mp3":
        raise ValueError("Das Ausgabeformat muss mp3 sein.")

def clean_text(text: str) -> str:
    """Clean the text by removing unwanted characters and normalizing whitespace."""
    try:
        # Entferne HTML-Tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Ersetze verschiedene Arten von Anführungszeichen durch einfache
        text = text.replace('"', '"').replace('"', '"').replace('„', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Ersetze mehrfache Leerzeichen durch ein einzelnes
        text = re.sub(r'\s+', ' ', text)
        
        # Entferne Leerzeichen am Anfang und Ende
        text = text.strip()
        
        # Behandle unausgewogene Klammern
        stack = []
        cleaned_text = ""
        
        for i, char in enumerate(text):
            if char == '(':
                stack.append(i)
                cleaned_text += char
            elif char == ')':
                if stack:  # Wenn es eine öffnende Klammer gibt
                    stack.pop()
                    cleaned_text += char
                # Ignoriere schließende Klammer ohne öffnende Klammer
            else:
                cleaned_text += char
                
        # Füge fehlende schließende Klammern am Ende hinzu
        cleaned_text += ')' * len(stack)
        
        # Behandle MAGIC_BREAK_STRING
        cleaned_text = cleaned_text.replace(MAGIC_BREAK_STRING.strip(), MAGIC_BREAK_STRING)
        
        # Entferne doppelte Breaks
        cleaned_text = re.sub(f"{MAGIC_BREAK_STRING}+", MAGIC_BREAK_STRING, cleaned_text)
        
        logger.debug(f"Cleaned text step 2: <{cleaned_text[:100]}>")  # Ändern zu debug level
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error in clean_text: {e}")
        return text  # Gib den ursprünglichen Text zurück, wenn ein Fehler auftritt

def check_dependencies():
    """Überprüft die notwendigen Abhängigkeiten"""
    try:
        # Überprüfe ffmpeg Installation
        from shutil import which
        if which('ffmpeg') is None:
            logger.warning("ffmpeg ist nicht installiert. Bitte installieren Sie ffmpeg für die Audiobearbeitung.")
            if sys.platform.startswith('linux'):
                logger.info("Unter Linux können Sie ffmpeg mit 'sudo apt-get install ffmpeg' installieren")
            elif sys.platform.startswith('darwin'):
                logger.info("Unter macOS können Sie ffmpeg mit 'brew install ffmpeg' installieren")
            elif sys.platform.startswith('win'):
                logger.info("Unter Windows laden Sie ffmpeg von https://www.ffmpeg.org/download.html herunter")
            return False
        return True
    except Exception as e:
        logger.error(f"Fehler beim Überprüfen der Abhängigkeiten: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert EPUB to audiobook")
    parser.add_argument("input_file", help="Path to the EPUB file")
    parser.add_argument("output_folder", help="Path to the output folder")
    parser.add_argument(
        "--tts",
        choices=[TTS_AZURE, TTS_OPENAI],
        default=TTS_AZURE,
        help="Choose TTS provider (default: azure). azure: Azure Cognitive Services, openai: OpenAI TTS API. When using azure, environment variables MS_TTS_KEY and MS_TTS_REGION must be set. When using openai, environment variable OPENAI_API_KEY must be set.",
    )
    parser.add_argument(
        "--log",
        default="INFO",
        help="Log level (default: INFO), can be DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Enable preview mode. In preview mode, the script will not convert the text to speech. Instead, it will print the chapter index, titles, and character counts.",
    )
    parser.add_argument(
        "--language",
        default="en-US",
        help="Language for the text-to-speech service (default: en-US). For Azure TTS (--tts=azure), check https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#text-to-speech for supported languages. For OpenAI TTS (--tts=openai), their API detects the language automatically. But setting this will also help on splitting the text into chunks with different strategies in this tool, especially for Chinese characters. For Chinese books, use zh-CN, zh-TW, or zh-HK.",
    )
    parser.add_argument(
        "--newline_mode",
        choices=["single", "double", "none"],
        help="Choose the mode of detecting new paragraphs: 'single', 'double', or 'none'. 'single' means a single newline character, while 'double' means two consecutive newline characters. 'none' means all newline characters will be replace with blank so paragraphs will not be detected.",
    )
    parser.add_argument(
        "--title_mode",
        choices=["auto", "tag_text", "first_few"],
        default="auto",
        help="Choose the parse mode for chapter title, 'tag_text' search 'title','h1','h2','h3' tag for title, 'first_few' set first 60 characters as title, 'auto' auto apply the best mode for current chapter.",
    )
    parser.add_argument(
        "--chapter_start",
        default=1,
        type=int,
        help="Chapter start index (default: 1, starting from 1)",
    )
    parser.add_argument(
        "--chapter_end",
        default=-1,
        type=int,
        help="Chapter end index (default: -1, meaning to the last chapter)",
    )
    parser.add_argument(
        "--output_text",
        action="store_true",
        help="Enable Output Text. This will export a plain text file for each chapter specified and write the files to the output folder specified.",
    )
    parser.add_argument(
        "--remove_endnotes",
        action="store_true",
        help="This will remove endnote numbers from the end or middle of sentences. This is useful for academic books.",
    )
    parser.add_argument(
        "--search_and_replace_file",
        help="Path to a file that contains 1 regex replace per line, to help with fixing pronunciations, etc. The format is: <search>==<replace> Note that you may have to specify word boundaries, to avoid replacing parts of words.",
    )
    parser.add_argument(
        "--voice_name",
        help="Various TTS providers has different voice names, look up for your provider settings.",
    )
    parser.add_argument(
        "--output_format",
        help="Output format for the text-to-speech service. Supported format depends on selected TTS provider",
    )
    parser.add_argument(
        "--model_name",
        help="Various TTS providers has different neural model names",
    )
    parser.add_argument(
        "--voice_rate",
        help="Speaking rate of the text. Valid relative values range from -50%(--xxx='-50%') to +100%. For negative value use format --arg=value,",
    )
    parser.add_argument(
        "--voice_volume",
        help="Volume level of the speaking voice. Valid relative values floor to -100%. For negative value use format --arg=value,",
    )
    parser.add_argument(
        "--voice_pitch",
        help="Baseline pitch for the text.Valid relative values like -80Hz,+50Hz, pitch changes should be within 0.5 to 1.5 times the original audio. For negative value use format --arg=value,",
    )
    parser.add_argument(
        "--proxy",
        help="Proxy server for the TTS provider. Format: http://[username:password@]proxy.server:port",
    )
    parser.add_argument(
        "--break_duration",
        help="Break duration in milliseconds for the different paragraphs or sections (default: 1250, means 1.25 s). Valid values range from 0 to 5000 milliseconds for Azure TTS.",
    )
    parser.add_argument(
        "--piper_path",
        help="Path to the Piper TTS executable",
    )
    parser.add_argument(
        "--piper_speaker",
        help="Piper speaker id, used for multi-speaker models",
    )
    parser.add_argument(
        "--piper_sentence_silence",
        help="Seconds of silence after each sentence",
    )
    parser.add_argument(
        "--piper_length_scale",
        help="Phoneme length, a.k.a. speaking rate",
    )

    args = parser.parse_args()

    # Überprüfen Sie, ob die Eingabedatei und der Ausgabepfad angegeben sind
    if not args.input_file or not args.output_folder:
        parser.error("Die Eingabedatei und der Ausgabepfad sind erforderlich.")

    if args.tts == TTS_AZURE:
        tts_provider = AzureTTSProvider(
            general_config,
            args.voice_name,
            args.break_duration,
            args.output_format,
        )
    elif args.tts == TTS_OPENAI:
        tts_provider = OpenAITTSProvider(
            general_config, args.openai_model, args.openai_voice, args.openai_format
        )
    else:
        raise ValueError(f"Invalid TTS provider: {args.tts}")

    epub_to_audiobook(tts_provider)
    logger.info("Done! 👍")
    logger.info(f"args = {args}")


if __name__ == "__main__":
    try:
        # Überprüfe Abhängigkeiten
        check_dependencies()
        
        # Ignoriere bestimmte Warnungen
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib.epub")
        warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib.epub")
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub.utils")
        
        # Überprüfen Sie, ob Kommandozeilenargumente übergeben wurden
        if len(sys.argv) > 1:
            main()
        else:
            # Wenn keine Argumente übergeben wurden, starten Sie die GUI
            import tkinter as tk
            from gui import EpubToAudiobookGUI
            root = tk.Tk()
            app = EpubToAudiobookGUI(root)
            root.mainloop()
            sys.exit(0)
    except Exception as e:
        logger.error(f"Ein Fehler ist aufgetreten: {e}")
        if len(sys.argv) <= 1:  # Wenn GUI-Modus
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", str(e))
        sys.exit(1)
