import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from epub_to_audiobook import epub_to_audiobook, GeneralConfig, AzureTTSProvider, OpenAITTSProvider, TTS_AZURE, TTS_OPENAI
import threading
import os
import urllib.request
import re
import tempfile
from collections import namedtuple
import json
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import logging
import time
import requests
import csv
import gzip
from io import BytesIO, StringIO

# Übersetzungen
translations = {
    'de': {
        'title': 'EPUB zu Audiobook Konverter',
        'main_settings': 'Haupteinstellungen',
        'required_settings': 'Erforderliche Einstellungen',
        'epub_file': 'EPUB Datei',
        'browse': 'Durchsuchen',
        'output_folder': 'Ausgabeordner',
        'tts_provider': 'TTS Provider',
        'tts_settings': 'TTS Provider Einstellungen',
        'language': 'Sprache',
        'voice': 'Stimme',
        'output_format': 'Ausgabeformat',
        'optional_settings': 'Optionale Einstellungen',
        'log_level': 'Log Level',
        'newline_mode': 'Zeilenumbruch Modus',
        'title_mode': 'Titel Modus',
        'output_mode': 'Ausgabe Modus',
        'preview_mode': 'Vorschau Modus',
        'output_text': 'Text mit ausgeben',
        'remove_endnotes': 'Endnoten entfernen',
        'api_config': 'API Konfiguration',
        'azure_config': 'Azure Konfiguration',
        'azure_key': 'Azure Key',
        'azure_region': 'Azure Region',
        'openai_config': 'OpenAI Konfiguration',
        'openai_key': 'OpenAI Key',
        'start_conversion': 'Konvertierung starten',
        'cancel': 'Abbrechen',
        'help': 'Hilfe',
        'language_select': 'Sprache auswählen',
        'error': 'Fehler',
        'warning': 'Warnung',
        'success': 'Erfolg',
        'file_error': 'Bitte wählen Sie eine gültige EPUB-Datei',
        'file_not_found': 'Die ausgewählte Datei existiert nicht',
        'api_key_error': 'API Key ist erforderlich',
        'conversion_success': 'Konvertierung erfolgreich abgeschlossen',
        'conversion_canceled': 'Konvertierung erfolgreich abgebrochen',
        'conversion_running': 'Eine Konvertierung läuft bereits',
        'source_type': 'Quellentyp',
        'local_file': 'Lokale Datei',
        'gutenberg_project': 'Project Gutenberg',
        'gutenberg_id': 'Gutenberg ID oder URL',
        'load_gutenberg': 'Laden',
        'loading': 'Lade...',
        'gutenberg_error': 'Fehler beim Laden von Project Gutenberg',
        'gutenberg_success': 'Text von Project Gutenberg erfolgreich geladen',
        'search_gutenberg': 'Project Gutenberg durchsuchen',
        'search': 'Suchen',
        'author': 'Autor',
        'title': 'Titel',
        'language': 'Sprache',
        'search_placeholder': 'Suchbegriff eingeben...',
        'results': 'Ergebnisse',
        'select': 'Auswählen',
        'loading_catalog': 'Lade Katalog...',
        'catalog_error': 'Fehler beim Laden des Katalogs',
        'no_results': 'Keine Ergebnisse gefunden',
        'book_preview': 'Buchvorschau',
        'load_book': 'Buch laden',
        'close': 'Schließen',
        'no_gutenberg_id': 'Bitte geben Sie eine gültige Gutenberg ID oder URL ein',
        'epub_created': 'EPUB-Datei erfolgreich erstellt',
        'preview_button': 'Vorschau',
        'no_text_loaded': 'Kein Text geladen',
        'info': 'Vorschau'
    },
    'en': {
        'title': 'EPUB to Audiobook Converter',
        'main_settings': 'Main Settings',
        'required_settings': 'Required Settings',
        'epub_file': 'EPUB File',
        'browse': 'Browse',
        'output_folder': 'Output Folder',
        'tts_provider': 'TTS Provider',
        'tts_settings': 'TTS Provider Settings',
        'language': 'Language',
        'voice': 'Voice',
        'output_format': 'Output Format',
        'optional_settings': 'Optional Settings',
        'log_level': 'Log Level',
        'newline_mode': 'Newline Mode',
        'title_mode': 'Title Mode',
        'output_mode': 'Output Mode',
        'preview_mode': 'Preview Mode',
        'output_text': 'Output Text',
        'remove_endnotes': 'Remove Endnotes',
        'api_config': 'API Configuration',
        'azure_config': 'Azure Configuration',
        'azure_key': 'Azure Key',
        'azure_region': 'Azure Region',
        'openai_config': 'OpenAI Configuration',
        'openai_key': 'OpenAI Key',
        'start_conversion': 'Start Conversion',
        'cancel': 'Cancel',
        'help': 'Help',
        'language_select': 'Select Language',
        'error': 'Error',
        'warning': 'Warning',
        'success': 'Success',
        'file_error': 'Please select a valid EPUB file',
        'file_not_found': 'Selected file does not exist',
        'api_key_error': 'API Key is required',
        'conversion_success': 'Conversion completed successfully',
        'conversion_canceled': 'Conversion canceled successfully',
        'conversion_running': 'A conversion is already running',
        'source_type': 'Source Type',
        'local_file': 'Local File',
        'gutenberg_project': 'Project Gutenberg',
        'gutenberg_id': 'Gutenberg ID or URL',
        'load_gutenberg': 'Load',
        'loading': 'Loading...',
        'gutenberg_error': 'Error loading from Project Gutenberg',
        'gutenberg_success': 'Text from Project Gutenberg successfully loaded',
        'search_gutenberg': 'Search Project Gutenberg',
        'search': 'Search',
        'author': 'Author',
        'title': 'Title',
        'language': 'Language',
        'search_placeholder': 'Enter search term...',
        'results': 'Results',
        'select': 'Select',
        'loading_catalog': 'Loading catalog...',
        'catalog_error': 'Error loading catalog',
        'no_results': 'No results found',
        'book_preview': 'Book Preview',
        'load_book': 'Load Book',
        'close': 'Close',
        'no_gutenberg_id': 'Please enter a valid Gutenberg ID or URL',
        'epub_created': 'EPUB file successfully created',
        'preview_button': 'Preview',
        'no_text_loaded': 'No text loaded',
        'info': 'Preview'
    }
}

class GutenbergBookSearchDialog:
    def __init__(self, parent, current_language='de'):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.selected_book_id = None
        self.current_language = current_language
        self.dialog.title(translations[self.current_language]['search_gutenberg'])
        self.dialog.geometry("900x700")  # Größeres Startfenster
        self.dialog.minsize(800, 600)    # Größere Mindestfenstergröße
        
        # Status-Variable für Meldungen
        self.status_var = tk.StringVar()
        
        self.setup_ui()
        self.load_catalog()
        
        # Dialog-Modalität
        self.dialog.transient(parent)
        self.dialog.grab_set()
        parent.wait_window(self.dialog)
    
    def setup_ui(self):
        t = translations[self.current_language]
        
        # Hauptframe
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Suchframe
        search_frame = ttk.LabelFrame(main_frame, text=t['search'], padding="5")
        search_frame.pack(fill=tk.X, pady=5)
        
        # Suchfeld
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.insert(0, t['search_placeholder'])
        search_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, tk.END) if search_entry.get() == t['search_placeholder'] else None)
        search_entry.bind("<Return>", lambda e: self.search_books())
        
        # Sprachfilter
        self.language_filter_var = tk.StringVar(value="all")
        language_frame = ttk.Frame(search_frame)
        language_frame.pack(side=tk.LEFT, padx=5)
        
        language_label = ttk.Label(language_frame, text=t['language'] + ":")
        language_label.pack(side=tk.LEFT)
        
        language_combo = ttk.Combobox(language_frame, textvariable=self.language_filter_var, 
                                    values=["all", "de", "en", "fr", "it", "es"], 
                                    width=5, state="readonly")
        language_combo.pack(side=tk.LEFT, padx=5)
        
        # Suchbutton
        search_button = ttk.Button(search_frame, text=t['search'], command=self.search_books)
        search_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Ergebnisse und Vorschau in einem horizontalen Frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Ergebnisframe - links
        results_frame = ttk.LabelFrame(content_frame, text=t['results'], padding="5")
        results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Ergebnistabelle
        table_frame = ttk.Frame(results_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('id', 'title', 'author', 'language')
        self.results_table = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Spalten konfigurieren
        self.results_table.heading('id', text='ID')
        self.results_table.heading('title', text=t['title'])
        self.results_table.heading('author', text=t['author'])
        self.results_table.heading('language', text=t['language'])
        
        self.results_table.column('id', width=50, anchor=tk.CENTER)
        self.results_table.column('title', width=250)
        self.results_table.column('author', width=200)
        self.results_table.column('language', width=80, anchor=tk.CENTER)
        
        # Scrollbars für Tabelle
        vscrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_table.yview)
        self.results_table.configure(yscrollcommand=vscrollbar.set)
        
        hscrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.results_table.xview)
        self.results_table.configure(xscrollcommand=hscrollbar.set)
        
        # Packing für Tabelle
        self.results_table.grid(row=0, column=0, sticky='nsew')
        vscrollbar.grid(row=0, column=1, sticky='ns')
        hscrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Doppelklick-Binding
        self.results_table.bind("<Double-1>", self.on_book_select)
        
        # Vorschau-Frame - rechts
        preview_frame = ttk.LabelFrame(content_frame, text=t['book_preview'], padding="5")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, width=60, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons - deutlich größer und mittig positioniert
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Button zum Zentrieren der Buttons
        center_frame = ttk.Frame(button_frame)
        center_frame.pack(anchor=tk.CENTER)
        
        self.load_button = ttk.Button(center_frame, text=t['load_book'], command=self.select_book, 
                                    state=tk.DISABLED, width=20)  # Breiterer Button
        self.load_button.pack(side=tk.LEFT, padx=10, pady=5)  # Mehr Abstand
        
        close_button = ttk.Button(center_frame, text=t['close'], command=self.dialog.destroy, 
                                width=20)  # Breiterer Button
        close_button.pack(side=tk.LEFT, padx=10, pady=5)  # Mehr Abstand
        
        # Status-Label - deutlicher sichtbar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('TkDefaultFont', 10, 'bold'))  # Fett für bessere Sichtbarkeit
        self.status_label.pack(fill=tk.X, pady=5)
    
    def load_catalog(self):
        """Lädt den Gutenberg-Katalog aus der CSV-Datei"""
        self.status_var.set(translations[self.current_language]['loading_catalog'])
        
        # Starte den Ladevorgang in einem separaten Thread
        threading.Thread(target=self._load_catalog_thread).start()
    
    def _load_catalog_thread(self):
        """Lädt den Katalog im Hintergrund"""
        try:
            # CSV-Katalog von Project Gutenberg herunterladen
            GUTENBERG_CSV_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"
            
            try:
                import gzip
                from io import BytesIO, StringIO
                
                # Die komprimierte Datei herunterladen
                response = requests.get(GUTENBERG_CSV_URL)
                
                # Die komprimierten Daten dekomprimieren
                with gzip.open(BytesIO(response.content), 'rt', encoding='utf-8') as f:
                    # CSV-Daten einlesen
                    self.catalog = list(csv.DictReader(f))
                
                # Verwende after, um die UI sicher zu aktualisieren
                self.dialog.after(0, lambda: self._update_catalog())
                
            except Exception as e:
                error_message = f"Fehler beim Laden des Katalogs: {str(e)}"
                self.dialog.after(0, lambda: self.status_var.set(error_message))
                
        except Exception as e:
            error_message = f"{translations[self.current_language]['catalog_error']}: {str(e)}"
            self.dialog.after(0, lambda: self.status_var.set(error_message))
    
    def _update_catalog(self):
        """Aktualisiert die Kataloganzeige im UI-Thread"""
        if not self.dialog.winfo_exists():
            return  # Dialog wurde bereits geschlossen
        
        # Zeige die ersten 100 Bücher an
        self.status_var.set(f"Katalog geladen: {len(self.catalog)} Bücher verfügbar. Bitte Suchbegriff eingeben.")
        
        # Zeige keine Bücher an, bis eine Suche durchgeführt wurde
        # Das verbessert die Leistung, da der Katalog sehr groß sein kann
    
    def search_books(self):
        """Durchsucht den Katalog nach den angegebenen Kriterien"""
        search_term = self.search_var.get().lower()
        if search_term == translations[self.current_language]['search_placeholder'].lower():
            search_term = ""
        
        if not search_term:
            self.status_var.set("Bitte einen Suchbegriff eingeben")
            return
            
        self.status_var.set(f"Suche nach '{search_term}'...")
        
        language_filter = self.language_filter_var.get()
        
        # Lösche bisherige Ergebnisse
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        
        # Filtere Bücher
        filtered_books = []
        for book in self.catalog:
            # Sprachfilter
            if language_filter != "all" and book["Language"] != language_filter:
                continue
            
            # Textsuche
            if search_term and search_term not in book["Title"].lower() and search_term not in book["Authors"].lower():
                continue
            
            filtered_books.append(book)
            
            # Begrenze auf 100 Ergebnisse für bessere Leistung
            if len(filtered_books) >= 100:
                break
        
        # Ergebnisse in Tabelle anzeigen
        for book in filtered_books:
            self.results_table.insert('', 'end', values=(
                book["Text#"], 
                book["Title"][:100] + ("..." if len(book["Title"]) > 100 else ""), 
                book["Authors"][:100] + ("..." if len(book["Authors"]) > 100 else ""), 
                book["Language"]
            ))
        
        if filtered_books:
            self.status_var.set(f"{len(filtered_books)} {translations[self.current_language]['results']}" + 
                              (", angezeigt werden die ersten 100" if len(filtered_books) > 100 else ""))
        else:
            self.status_var.set(translations[self.current_language]['no_results'])
    
    def on_book_select(self, event):
        """Wird aufgerufen, wenn ein Buch in der Tabelle ausgewählt wird"""
        selected_items = self.results_table.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        book_id = self.results_table.item(item, "values")[0]
        self.preview_book(book_id)
        self.load_button.config(state=tk.NORMAL)
    
    def preview_book(self, book_id):
        """Zeigt eine Vorschau des ausgewählten Buchs"""
        self.selected_book_id = book_id
        self.status_var.set(translations[self.current_language]['loading'])
        self.preview_text.delete(1.0, tk.END)
        
        # Lade die Buchvorschau im Hintergrund
        threading.Thread(target=self._load_preview_thread, args=(book_id,)).start()
    
    def _load_preview_thread(self, book_id):
        """Lädt die Buchvorschau im Hintergrund"""
        try:
            # URL für das Buch
            url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
            
            # Text herunterladen und Fehlerbehandlung
            try:
                with urllib.request.urlopen(url) as response:
                    text = response.read().decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                # Versuchen mit einer anderen Kodierung
                with urllib.request.urlopen(url) as response:
                    text = response.read().decode('latin-1', errors='replace')
            except Exception as e:
                # Versuche alternative URL
                try:
                    alt_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
                    with urllib.request.urlopen(alt_url) as response:
                        text = response.read().decode('utf-8', errors='replace')
                except Exception:
                    raise Exception(f"Fehler beim Herunterladen: {str(e)}")
            
            # Prüfen, ob Text leer ist
            if not text or len(text.strip()) == 0:
                raise Exception("Heruntergeladener Text ist leer")
            
            # Extrahiere einen Vorschautext
            preview_text = ""
            if "*** START OF" in text:
                start_pos = text.find("*** START OF")
                start_pos = text.find("\n", start_pos) + 1
                if start_pos > 0 and start_pos < len(text):
                    preview_text = text[start_pos:min(start_pos + 2000, len(text))] + "...\n\n[...]"
            
            # Wenn kein Startmarker gefunden wurde, nimm einfach den Anfang des Textes
            if not preview_text:
                preview_text = text[:min(2000, len(text))] + "...\n\n[...]"
            
            # Verwende after, um den Text sicher in der UI anzuzeigen
            self.dialog.after(0, lambda: self._update_preview_text(preview_text, f"Vorschau für Buch #{book_id} geladen"))
            
        except Exception as e:
            error_message = f"Fehler beim Laden der Vorschau: {str(e)}"
            self.dialog.after(0, lambda: self._update_preview_text(error_message, f"Fehler: {str(e)}"))
    
    def _update_preview_text(self, text, status):
        """Aktualisiert den Preview-Text und den Status im UI-Thread"""
        if not self.dialog.winfo_exists():
            return  # Dialog wurde bereits geschlossen
        
        try:
            if text is None:
                text = "Keine Textvorschau verfügbar."
            
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, text)
            self.status_var.set(status)
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Vorschau: {e}")
            try:
                self.status_var.set(f"Fehler bei der Anzeige: {str(e)}")
            except:
                pass
    
    def select_book(self):
        """Das ausgewählte Buch zurückgeben und den Dialog schließen"""
        self.dialog.destroy()

class EpubToAudiobookGUI:
    def __init__(self, root):
        self.root = root
        self.current_language = 'de'  # Standardsprache
        self.root.title(translations[self.current_language]['title'])
        self.root.configure(bg="#2E2E2E")

        self.settings_file = "gui_settings.json"
        self.conversion_thread = None
        self.is_converting = False
        self.gutenberg_text = None
        self.temp_epub_file = None

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", background="#2E2E2E", foreground="#FFFFFF")
        style.configure("TButton", background="#4CAF50", foreground="#FFFFFF")
        style.configure("TEntry", fieldbackground="#3E3E3E", foreground="#FFFFFF")
        style.configure("TCheckbutton", background="#2E2E2E", foreground="#FFFFFF")
        style.configure("TCombobox", fieldbackground="#3E3E3E", foreground="#FFFFFF")
        style.configure("TProgressbar", background="#4CAF50")

        # Status Variable für Meldungen
        self.status_var = tk.StringVar()
        
        # GUI-Sprachauswahl (UI-Sprache)
        language_frame = ttk.Frame(self.root)
        language_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        
        self.language_label = ttk.Label(language_frame, text="Choose Language / Sprache wählen:")
        self.language_label.pack(side=tk.LEFT, padx=5)
        
        self.ui_language_var = tk.StringVar(value=self.current_language)
        self.ui_language_menu = ttk.Combobox(language_frame, textvariable=self.ui_language_var,
                                        values=["de", "en"], width=5, state="readonly")
        self.ui_language_menu.pack(side=tk.LEFT, padx=5)
        self.ui_language_menu.bind("<<ComboboxSelected>>", self.change_language)

        # Erstelle ein Notebook für verschiedene Kategorien
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # Haupteinstellungen
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text=translations[self.current_language]['main_settings'])

        # Required Settings
        self.required_frame = ttk.LabelFrame(main_frame, text=translations[self.current_language]['required_settings'])
        self.required_frame.pack(fill="x", padx=5, pady=5)

        # Source Type Selection
        self.source_type_label = ttk.Label(self.required_frame, text=translations[self.current_language]['source_type'])
        self.source_type_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.source_type_var = tk.StringVar(value="local_file")
        self.source_type_menu = ttk.Combobox(self.required_frame, textvariable=self.source_type_var,
                                           values=["local_file", "gutenberg_project"], width=15, state="readonly")
        self.source_type_menu.grid(row=0, column=1, padx=5, pady=5)
        self.source_type_menu.bind("<<ComboboxSelected>>", self.on_source_type_change)

        # Local File Frame
        self.local_file_frame = ttk.Frame(self.required_frame)
        self.local_file_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.input_file_label = ttk.Label(self.local_file_frame, text=translations[self.current_language]['epub_file'])
        self.input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.input_file_entry = ttk.Entry(self.local_file_frame, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_file_button = ttk.Button(self.local_file_frame, text=translations[self.current_language]['browse'], command=self.browse_input_file)
        self.input_file_button.grid(row=0, column=2, padx=5, pady=5)

        # Gutenberg Frame - Diese Methode wird neu erstellt
        self.create_gutenberg_frame()

        # Output Folder
        self.output_folder_label = ttk.Label(self.required_frame, text=translations[self.current_language]['output_folder'])
        self.output_folder_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.output_folder_entry = ttk.Entry(self.required_frame, width=50)
        self.output_folder_entry.grid(row=2, column=1, padx=5, pady=5)
        self.output_folder_button = ttk.Button(self.required_frame, text=translations[self.current_language]['browse'], command=self.browse_output_folder)
        self.output_folder_button.grid(row=2, column=2, padx=5, pady=5)

        # TTS Provider Settings
        self.tts_frame = ttk.LabelFrame(main_frame, text=translations[self.current_language]['tts_settings'])
        self.tts_frame.pack(fill="x", padx=5, pady=5)

        self.tts_provider_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['tts_provider'])
        self.tts_provider_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.tts_provider_var = tk.StringVar(value="azure")
        self.tts_provider_menu = ttk.Combobox(self.tts_frame, textvariable=self.tts_provider_var, 
                                             values=["azure", "openai", "edge", "piper"])
        self.tts_provider_menu.grid(row=0, column=1, padx=5, pady=5)

        # Spracheinstellungen für Audiobook
        self.tts_language_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['language'])
        self.tts_language_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.tts_language_var = tk.StringVar(value="de-DE")
        self.tts_language_menu = ttk.Combobox(self.tts_frame, textvariable=self.tts_language_var,
                                        values=["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT", "zh-CN", "ja-JP"])
        self.tts_language_menu.grid(row=1, column=1, padx=5, pady=5)

        # OpenAI Modell
        self.model_label = ttk.Label(self.tts_frame, text="Modell")
        self.model_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.model_var = tk.StringVar(value="tts-1")
        self.model_menu = ttk.Combobox(self.tts_frame, textvariable=self.model_var,
                                     values=["tts-1", "tts-1-hd"])
        self.model_menu.grid(row=2, column=1, padx=5, pady=5)
        # Standardmäßig ausblenden
        self.model_label.grid_remove()
        self.model_menu.grid_remove()

        # Stimmeinstellungen
        self.voice_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['voice'])
        self.voice_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.voice_var = tk.StringVar()
        self.voice_menu = ttk.Combobox(self.tts_frame, textvariable=self.voice_var)
        self.voice_menu.grid(row=3, column=1, padx=5, pady=5)

        # Ausgabeformat
        self.format_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['output_format'])
        self.format_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.format_var = tk.StringVar(value="mp3")
        self.format_menu = ttk.Combobox(self.tts_frame, textvariable=self.format_var,
                                      values=["mp3", "wav", "ogg", "m4a"])
        self.format_menu.grid(row=4, column=1, padx=5, pady=5)

        # Optional Settings Tab
        self.optional_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.optional_frame, text=translations[self.current_language]['optional_settings'])

        # Log Level
        self.log_label = ttk.Label(self.optional_frame, text=translations[self.current_language]['log_level'])
        self.log_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.log_var = tk.StringVar(value="INFO")
        self.log_menu = ttk.Combobox(self.optional_frame, textvariable=self.log_var,
                                    values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_menu.grid(row=0, column=1, padx=5, pady=5)

        # Newline Mode
        self.newline_label = ttk.Label(self.optional_frame, text=translations[self.current_language]['newline_mode'])
        self.newline_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.newline_var = tk.StringVar(value="double")
        self.newline_menu = ttk.Combobox(self.optional_frame, textvariable=self.newline_var,
                                        values=["single", "double", "none"])
        self.newline_menu.grid(row=1, column=1, padx=5, pady=5)

        # Title Mode
        self.title_mode_label = ttk.Label(self.optional_frame, text=translations[self.current_language]['title_mode'])
        self.title_mode_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.title_mode_var = tk.StringVar(value="auto")
        self.title_mode_menu = ttk.Combobox(self.optional_frame, textvariable=self.title_mode_var,
                                           values=["auto", "tag_text", "first_few"])
        self.title_mode_menu.grid(row=2, column=1, padx=5, pady=5)

        # Output Mode
        self.output_mode_label = ttk.Label(self.optional_frame, text=translations[self.current_language]['output_mode'])
        self.output_mode_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.output_mode_var = tk.StringVar(value="multiple")
        self.output_mode_menu = ttk.Combobox(self.optional_frame, textvariable=self.output_mode_var,
                                            values=["single", "multiple"])
        self.output_mode_menu.grid(row=3, column=1, padx=5, pady=5)

        # Checkboxen
        self.preview_var = tk.BooleanVar()
        self.preview_check = ttk.Checkbutton(self.optional_frame, text=translations[self.current_language]['preview_mode'], 
                                            variable=self.preview_var)
        self.preview_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.output_text_var = tk.BooleanVar()
        self.output_text_check = ttk.Checkbutton(self.optional_frame, text=translations[self.current_language]['output_text'], 
                                                variable=self.output_text_var)
        self.output_text_check.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        self.remove_endnotes_var = tk.BooleanVar()
        self.remove_endnotes_check = ttk.Checkbutton(self.optional_frame, text=translations[self.current_language]['remove_endnotes'], 
                                                    variable=self.remove_endnotes_var)
        self.remove_endnotes_check.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

        # API Konfiguration
        self.api_frame = ttk.LabelFrame(self.root, text=translations[self.current_language]['api_config'])
        self.api_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # Azure Konfiguration
        self.azure_frame = ttk.LabelFrame(self.api_frame, text=translations[self.current_language]['azure_config'])
        self.azure_frame.pack(fill="x", padx=5, pady=5)
        
        self.azure_key_label = ttk.Label(self.azure_frame, text=translations[self.current_language]['azure_key'])
        self.azure_key_label.grid(row=0, column=0, padx=5, pady=5)
        self.azure_key_entry = ttk.Entry(self.azure_frame, width=40)
        self.azure_key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.azure_region_label = ttk.Label(self.azure_frame, text=translations[self.current_language]['azure_region'])
        self.azure_region_label.grid(row=1, column=0, padx=5, pady=5)
        self.azure_region_entry = ttk.Entry(self.azure_frame, width=40)
        self.azure_region_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # OpenAI Konfiguration
        self.openai_frame = ttk.LabelFrame(self.api_frame, text=translations[self.current_language]['openai_config'])
        self.openai_frame.pack(fill="x", padx=5, pady=5)
        
        self.openai_key_label = ttk.Label(self.openai_frame, text=translations[self.current_language]['openai_key'])
        self.openai_key_label.grid(row=0, column=0, padx=5, pady=5)
        self.openai_key_entry = ttk.Entry(self.openai_frame, width=40)
        self.openai_key_entry.grid(row=0, column=1, padx=5, pady=5)

        # Buttons
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        self.start_button = ttk.Button(self.button_frame, text=translations[self.current_language]['start_conversion'], command=self.start_conversion)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.button_frame, text=translations[self.current_language]['cancel'], command=self.cancel_conversion)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.usage_button = ttk.Button(self.button_frame, text=translations[self.current_language]['help'], command=self.show_usage)
        self.usage_button.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
        
        # Status Label
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # Event Handler für Provider-Änderung
        self.tts_provider_var.trace_add("write", self.on_provider_change)

    def on_provider_change(self, *args):
        """Aktualisiert die verfügbaren Optionen basierend auf dem ausgewählten Provider"""
        provider = self.tts_provider_var.get()
        
        # Aktualisiere verfügbare Sprachen und Stimmen
        if provider == "azure":
            self.tts_language_menu['values'] = ["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT", "zh-CN", "ja-JP"]
            self.voice_menu['values'] = ["de-DE-KatjaNeural", "en-US-JennyNeural", "en-GB-SoniaNeural", 
                                       "fr-FR-DeniseNeural", "es-ES-ElviraNeural", "it-IT-ElsaNeural",
                                       "zh-CN-XiaoxiaoNeural", "ja-JP-NanamiNeural"]
            # Verstecke OpenAI-Modellauswahl
            self.model_label.grid_remove()
            self.model_menu.grid_remove()
        elif provider == "openai":
            self.tts_language_menu['values'] = ["en-US", "en-GB"]
            self.voice_menu['values'] = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            # Zeige OpenAI-Modellauswahl
            self.model_label.grid()
            self.model_menu.grid()
        elif provider == "edge":
            self.tts_language_menu['values'] = ["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT"]
            self.voice_menu['values'] = ["de-DE-Katja", "en-US-Guy", "en-GB-Susan", 
                                       "fr-FR-Julie", "es-ES-Laura", "it-IT-Elsa"]
            # Verstecke OpenAI-Modellauswahl
            self.model_label.grid_remove()
            self.model_menu.grid_remove()
        elif provider == "piper":
            self.tts_language_menu['values'] = ["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT"]
            self.voice_menu['values'] = ["de_DE-thorsten", "en_US-libritts_r", "en_GB-northern_english_male",
                                       "fr_FR-siwis", "es_ES-davefx", "it_IT-riccardo_fasol"]
            # Verstecke OpenAI-Modellauswahl
            self.model_label.grid_remove()
            self.model_menu.grid_remove()

        # Aktualisiere verfügbare Formate
        if provider in ["azure", "openai"]:
            self.format_menu['values'] = ["mp3", "wav", "ogg", "m4a"]
        else:
            self.format_menu['values'] = ["wav", "mp3"]

        # Zeige/Verstecke API-Frames
        if provider == "azure":
            self.azure_frame.pack(fill="x", padx=5, pady=5)
            self.openai_frame.pack_forget()
        elif provider == "openai":
            self.openai_frame.pack(fill="x", padx=5, pady=5)
            self.azure_frame.pack_forget()
        else:
            self.azure_frame.pack_forget()
            self.openai_frame.pack_forget()

    def on_source_type_change(self, event=None):
        """Zeigt die entsprechenden Eingabefelder je nach ausgewähltem Quellentyp an"""
        source_type = self.source_type_var.get()
        if source_type == "local_file":
            self.gutenberg_frame.grid_remove()
            self.local_file_frame.grid()
        else:  # gutenberg_project
            self.local_file_frame.grid_remove()
            self.gutenberg_frame.grid()

    def create_gutenberg_frame(self):
        """Erstellt den Frame für Project Gutenberg"""
        self.gutenberg_frame = ttk.Frame(self.required_frame)
        self.gutenberg_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.gutenberg_frame.grid_remove()  # Hidden by default
        
        self.gutenberg_id_label = ttk.Label(self.gutenberg_frame, text=translations[self.current_language]['gutenberg_id'])
        self.gutenberg_id_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.gutenberg_id_entry = ttk.Entry(self.gutenberg_frame, width=40)
        self.gutenberg_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        gutenberg_buttons_frame = ttk.Frame(self.gutenberg_frame)
        gutenberg_buttons_frame.grid(row=0, column=2, padx=5, pady=5)
        
        self.gutenberg_browse_button = ttk.Button(gutenberg_buttons_frame, text=translations[self.current_language]['search'], command=self.browse_gutenberg)
        self.gutenberg_browse_button.pack(side=tk.LEFT, padx=2)
        
        self.gutenberg_load_button = ttk.Button(gutenberg_buttons_frame, text=translations[self.current_language]['load_gutenberg'], command=self.load_gutenberg_text)
        self.gutenberg_load_button.pack(side=tk.LEFT, padx=2)
        
        # Neuer Vorschau-Button und Anzeige
        if 'preview_button' not in translations['de']:
            translations['de']['preview_button'] = 'Vorschau'
            translations['en']['preview_button'] = 'Preview'
        
        self.preview_button = ttk.Button(self.gutenberg_frame, text=translations[self.current_language]['preview_button'], 
                                   command=self.show_text_preview, state=tk.DISABLED)
        self.preview_button.grid(row=1, column=1, pady=5)

    def show_text_preview(self):
        """Zeigt eine Vorschau des bereinigten Textes an"""
        if not self.gutenberg_text:
            messagebox.showinfo(translations[self.current_language]['info'], 
                              translations[self.current_language]['no_text_loaded'])
            return
        
        # Erstelle ein neues Fenster
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"{translations[self.current_language]['preview_button']}: {self.gutenberg_text['title']}")
        preview_window.geometry("800x600")
        
        # Füge Informationen über das Buch hinzu
        info_frame = ttk.Frame(preview_window, padding=10)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"{translations[self.current_language]['title']}: {self.gutenberg_text['title']}",
                font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"{translations[self.current_language]['author']}: {self.gutenberg_text['author']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Gutenberg ID: {self.gutenberg_text['id']}").pack(anchor=tk.W)
        
        # Textzwischenraum
        ttk.Separator(preview_window, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        # Text mit Scrollbar
        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text-Widget
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Text einfügen
        text_widget.insert(tk.END, self.gutenberg_text['text'])
        
        # Schließen-Button
        button_frame = ttk.Frame(preview_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        close_button = ttk.Button(button_frame, text=translations[self.current_language]['close'], 
                               command=preview_window.destroy)
        close_button.pack(side=tk.RIGHT)

    def load_gutenberg_text(self):
        """Lädt Text von Gutenberg basierend auf Gutenberg-ID oder URL"""
        self.status_var.set(translations[self.current_language]['loading'])
        
        # Gutenberg-ID oder URL bekommen
        gutenberg_input = self.gutenberg_id_entry.get().strip()
        
        if not gutenberg_input:
            messagebox.showerror(translations[self.current_language]['error'], 
                                translations[self.current_language]['no_gutenberg_id'])
            self.status_var.set("")
            return
        
        # Ermittle die Gutenberg-ID
        gutenberg_id = None
        
        try:
            # Überprüfen, ob es sich um eine URL oder eine ID handelt
            if gutenberg_input.startswith("http"):
                # Aus einer URL extrahieren
                match = re.search(r'/([0-9]+)', gutenberg_input)
                if match:
                    gutenberg_id = match.group(1)
                else:
                    raise ValueError("Keine Gutenberg-ID in der URL gefunden")
            else:
                # Direkter ID-Eintrag
                gutenberg_id = gutenberg_input.strip()
                
                # Überprüfe, ob es eine Nummer ist
                if not gutenberg_id.isdigit():
                    raise ValueError("Gutenberg-ID muss eine Zahl sein")
        
            # URL erstellen
            url = f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"
            print(f"URL für Download: {url}")
            
            # Text herunterladen mit besserer Fehlerbehandlung
            text = None
            try:
                with urllib.request.urlopen(url) as response:
                    text = response.read().decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                # Versuchen mit einer anderen Kodierung
                with urllib.request.urlopen(url) as response:
                    text = response.read().decode('latin-1', errors='replace')
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], 
                                    f"Fehler beim Herunterladen: {str(e)}")
                self.status_var.set("")
                return
            
            # Sicherstellen, dass Text vorhanden ist
            if not text or len(text.strip()) == 0:
                messagebox.showerror(translations[self.current_language]['error'], 
                                    "Der heruntergeladene Text ist leer.")
                self.status_var.set("")
                return
                
            # Titel und Autor extrahieren für besseren Titel
            title = f"Gutenberg Book {gutenberg_id}"
            author = "Unknown"
            
            title_match = re.search(r'Title: (.*?)(?:\r?\n)', text)
            if title_match:
                title = title_match.group(1).strip()
            
            author_match = re.search(r'Author: (.*?)(?:\r?\n)', text)
            if author_match:
                author = author_match.group(1).strip()
            
            # Haupttext extrahieren - Project Gutenberg Metadaten entfernen
            main_text = self.clean_gutenberg_text(text)
            
            # Speichere den Text und Metadaten
            self.gutenberg_text = {
                'title': title,
                'author': author,
                'text': main_text,
                'id': gutenberg_id
            }
            
            # Aktiviere den Vorschau-Button
            self.preview_button.config(state=tk.NORMAL)
            
            # Zeige einen Erfolgshinweis an
            self.status_var.set(f"{translations[self.current_language]['gutenberg_success']}: {title}")
            
            # Quelle auf "gutenberg_text" setzen und die lokale Datei deaktivieren
            self.source_type_var.set("gutenberg_project")
            self.input_file_entry.delete(0, tk.END)
            
            messagebox.showinfo(
                translations[self.current_language]['success'],
                f"{title} ({author}) wurde erfolgreich geladen."
            )
                
        except Exception as e:
            messagebox.showerror(translations[self.current_language]['error'], 
                               f"Fehler beim Verarbeiten des Gutenberg-Textes: {str(e)}")
            self.status_var.set("")

    def clean_gutenberg_text(self, text):
        """Entfernt Lizenz- und Metadaten aus einem Project Gutenberg Text"""
        start_marker = "*** START OF"
        end_marker = "*** END OF"
        
        print(f"Originaler Text: {len(text)} Zeichen")
        
        # Suche nach dem Start-Marker
        if start_marker in text:
            start_pos = text.find(start_marker)
            start_pos = text.find("\n", start_pos) + 1
            print(f"Start-Marker gefunden an Position: {start_pos}")
        else:
            # Wenn kein Start-Marker gefunden wird, versuchen wir andere typische Anfänge zu finden
            possible_starts = [
                "Produced by", 
                "This book was produced",
                "This eBook was produced",
                "Transcribed from",
                "Transcriber's Note",
                "TRANSCRIBER'S NOTE"
            ]
            
            # Suche nach dem letzten Vorkommen der möglichen Anfänge
            for marker in possible_starts:
                pos = text.find(marker)
                if pos != -1:
                    # Finde das Ende dieses Abschnitts (nächste Leerzeile)
                    end_of_note = text.find("\n\n", pos)
                    if end_of_note != -1:
                        start_pos = end_of_note + 2  # +2 für die beiden Newlines
                    else:
                        start_pos = 0  # Fallback
                    print(f"Alternativer Start-Marker '{marker}' gefunden, Text beginnt bei Position: {start_pos}")
                    break
            else:
                start_pos = 0  # Wenn kein Marker gefunden wurde
                print("Kein Start-Marker gefunden, beginne am Anfang")
            
        # Suche nach dem End-Marker
        if end_marker in text:
            end_pos = text.find(end_marker)
            print(f"End-Marker gefunden an Position: {end_pos}")
            
            # Suche nach Transkriptionsanmerkungen vor dem End-Marker
            transcription_markers = [
                "Transcriber's Note", 
                "TRANSCRIBER'S NOTE",
                "Transcriber's Notes",
                "TRANSCRIBER'S NOTES",
                "Anmerkungen zur Transkription",
                "ANMERKUNG ZUR TRANSKRIPTION",
                "ANMERKUNGEN ZUR TRANSKRIPTION"
            ]
            
            for marker in transcription_markers:
                trans_pos = text.rfind(marker, start_pos, end_pos)
                if trans_pos != -1:
                    # Finde den Anfang dieses Abschnitts (vorherige Leerzeile)
                    start_of_note = text.rfind("\n\n", start_pos, trans_pos)
                    if start_of_note != -1:
                        end_pos = start_of_note
                        print(f"Transkriptionsanmerkung '{marker}' gefunden vor End-Marker, Ende korrigiert zu: {end_pos}")
                        break
        else:
            # Wenn kein End-Marker gefunden wird, suche nach typischen Endabschnitten
            possible_ends = [
                "End of Project Gutenberg",
                "*** END OF THIS PROJECT GUTENBERG",
                "End of the Project Gutenberg",
                "Ende dieses Projekt Gutenberg",
                "Ende des Projekt Gutenberg"
            ]
            
            for marker in possible_ends:
                pos = text.find(marker)
                if pos != -1:
                    end_pos = pos
                    print(f"Alternativer End-Marker '{marker}' gefunden an Position: {end_pos}")
                    break
            else:
                end_pos = len(text)  # Fallback: Ende des Textes
                print(f"Kein End-Marker gefunden, Ende auf Textlänge gesetzt: {end_pos}")
            
        # Extrahiere den Haupttext
        if start_pos < end_pos:
            main_text = text[start_pos:end_pos].strip()
            print(f"Haupttext extrahiert: {len(main_text)} Zeichen")
            
            # Speichere eine Kopie für den Vergleich
            original_main_text = main_text
            
            import re
            
            # Spezifische Behandlung für genau dieses Format von Transkriptionsanmerkungen
            specific_patterns = [
                (r'Anmerkungen zur Transkription\s*\n+\s*Offensichtliche Fehler wurden stillschweigend korrigert.*?(?:\n\n|\Z)', re.DOTALL),
                (r'Anmerkungen zur Transkription\s*\n+.*?vorher/nachher.*?(?:\n\n\n|\Z)', re.DOTALL),
                (r'Transcriber\'s Notes?\s*\n+\s*Obvious.*?errors.*?corrected.*?(?:\n\n|\Z)', re.DOTALL),
                (r'TRANSCRIBER\'S NOTES?\s*\n+\s*Obvious.*?errors.*?corrected.*?(?:\n\n|\Z)', re.DOTALL)
            ]
            
            for pattern, flags in specific_patterns:
                cleaned_text = re.sub(pattern, '', main_text, flags=flags)
                if cleaned_text != main_text:
                    print(f"Spezifisches Muster für Transkriptionsblock entfernt")
                    main_text = cleaned_text
            
            # Entferne Transkriptionsblöcke mit einem vorsichtigeren Ansatz
            # Wir identifizieren nur sehr spezifische, klar abgegrenzte Blöcke
            transcription_starts = [
                "Transcriber's Note:", 
                "TRANSCRIBER'S NOTE:",
                "Transcriber's Notes:",
                "TRANSCRIBER'S NOTES:",
                "Anmerkungen zur Transkription:",
                "ANMERKUNG ZUR TRANSKRIPTION:",
                "ANMERKUNGEN ZUR TRANSKRIPTION:",
                "Anmerkungen zur Transkription",
                "ANMERKUNGEN ZUR TRANSKRIPTION"
            ]
            
            # Prüfen auf Anmerkungen, die mit eckigen Klammern markiert sind
            # Diese sind oft in der Mitte des Textes
            bracket_patterns = [
                r'\[Transcriber.*?\]',
                r'\[TRANSCRIBER.*?\]',
                r'\[Anmerkung.*?Transkription.*?\]',
                r'\[Anmerkungen.*?Transkription.*?\]',
                r'\(Transcriber.*?\)',
                r'\(TRANSCRIBER.*?\)',
                r'\(Anmerkung.*?Transkription.*?\)',
                r'\(Anmerkungen.*?Transkription.*?\)'
            ]
            
            # Entferne eingebettete Anmerkungen in Klammern
            for pattern in bracket_patterns:
                cleaned_text = re.sub(pattern, '', main_text, flags=re.DOTALL)
                if cleaned_text != main_text:
                    print(f"Eingebettete Anmerkung mit Pattern '{pattern}' entfernt")
                main_text = cleaned_text
            
            # Entferne Abschnitte mit Korrekturlisten
            correction_patterns = [
                r'\[S\. \d+\]:\s*\.\.\. .* \.\.\.\s*\.\.\. .* \.\.\.',
                r'Seite \d+.*?vorher.*?nachher',
                r'Page \d+.*?before.*?after'
            ]
            
            for pattern in correction_patterns:
                cleaned_text = re.sub(pattern, '', main_text, flags=re.DOTALL)
                if cleaned_text != main_text:
                    print(f"Korrekturliste mit Pattern '{pattern}' entfernt")
                main_text = cleaned_text
            
            # Suche nach Transkriptionsblöcken am Ende
            for marker in transcription_starts:
                last_pos = main_text.rfind(marker)
                if last_pos != -1:
                    # Nur entfernen, wenn es nahe am Ende ist (letztes Drittel des Textes)
                    if last_pos > len(main_text) * 0.66:
                        # Finde Anfang des Blocks (vorherige Leerzeile)
                        block_start = main_text.rfind("\n\n", 0, last_pos)
                        if block_start != -1:
                            main_text = main_text[:block_start].strip()
                            print(f"Transkriptionsblock am Ende mit Marker '{marker}' entfernt")
                            break
            
            # Sicherheitsprüfung: Wenn das Ergebnis zu klein ist, verwenden wir den Originaltext
            if len(main_text) < len(original_main_text) * 0.5:
                print("WARNUNG: Zu viel Text entfernt, verwende Originaltext mit minimaler Bereinigung")
                main_text = original_main_text
                
                # Entferne nur eindeutig markierte Blöcke mit exakten Markierungen
                for marker in ["*** START OF", "*** END OF"]:
                    pos = main_text.find(marker)
                    if pos != -1:
                        line_end = main_text.find("\n", pos)
                        if line_end != -1:
                            main_text = main_text.replace(main_text[pos:line_end+1], "")
                            print(f"Nur Marker-Zeile '{marker}' entfernt")
            
            print(f"Bereinigter Text: {len(main_text)} Zeichen")
        else:
            # Fallback: Verwende den gesamten Text
            main_text = text
            print("Warnung: Start-Position >= End-Position, verwende gesamten Text")
            
        return main_text

    def browse_input_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
        if file_path:
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, file_path)

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder_path)

    def filter_options(self, options):
        return {k: v for k, v in options.items() if v}

    def filter_empty_options(self, options):
        return {k: v for k, v in options.items() if v not in [None, "", False]}

    def get_options(self):
        """Sammelt alle gesetzten Optionen und filtert leere Werte"""
        options = {}
        
        # Required options
        options['input_file'] = self.input_file_entry.get()
        options['output_folder'] = self.output_folder_entry.get()
        options['tts'] = self.tts_provider_var.get()
        options['one_file'] = self.output_mode_var.get() == "single"  # Renamed from single_file to one_file

        # Optional settings - nur hinzufügen wenn gesetzt
        if self.log_var.get():
            options['log'] = self.log_var.get()
        
        # Boolean options - immer setzen
        options['preview'] = self.preview_var.get()
        options['output_text'] = self.output_text_var.get()
        options['remove_endnotes'] = self.remove_endnotes_var.get()

        if self.newline_var.get() and self.newline_var.get() != "none":
            options['newline_mode'] = self.newline_var.get()

        if self.title_mode_var.get():
            options['title_mode'] = self.title_mode_var.get()

        if self.tts_language_var.get():
            options['language'] = self.tts_language_var.get()

        # Weitere optionale Einstellungen
        if self.voice_var.get():
            options['voice_name'] = self.voice_var.get()
        
        if self.format_var.get():
            options['output_format'] = self.format_var.get()
            
        # OpenAI-spezifische Einstellungen
        if self.tts_provider_var.get() == "openai" and self.model_var.get():
            options['model_name'] = self.model_var.get()

        # Filtere None und leere Strings
        return {k: v for k, v in options.items() if v not in (None, "")}

    def estimate_costs(self, text_length: int) -> dict:
        """Schätzt die Kosten für die Konvertierung basierend auf der Textlänge"""
        # Azure TTS Preise (Stand: März 2024)
        # Standard (Neural) Voices: $16.00 per 1 million characters
        # Premium (Neural) Voices: $24.00 per 1 million characters
        
        # OpenAI TTS Preise (Stand: März 2024)
        # TTS-1: $0.015 per 1,000 characters
        # TTS-1-HD: $0.030 per 1,000 characters
        
        costs = {
            'azure_standard': (text_length / 1_000_000) * 16.00,
            'azure_premium': (text_length / 1_000_000) * 24.00,
            'openai_tts1': (text_length / 1_000) * 0.015,
            'openai_tts1_hd': (text_length / 1_000) * 0.030
        }
        
        return costs

    def show_cost_estimation(self, text_length: int):
        """Zeigt eine Kostenschätzung an und fragt nach Bestätigung"""
        costs = self.estimate_costs(text_length)
        
        message = f"""
Kostenschätzung für die Konvertierung ({text_length:,} Zeichen):

Azure TTS:
- Standard Voices: ${costs['azure_standard']:.2f}
- Premium Voices: ${costs['azure_premium']:.2f}

OpenAI TTS:
- TTS-1: ${costs['openai_tts1']:.2f}
- TTS-1-HD: ${costs['openai_tts1_hd']:.2f}

Möchten Sie mit der Konvertierung fortfahren?
"""
        
        return messagebox.askyesno("Kostenschätzung", message)

    def validate_api_keys(self, tts_provider):
        """Überprüft die API-Schlüssel vor der Konvertierung"""
        if tts_provider == TTS_AZURE:
            if not self.azure_key_entry.get() or not self.azure_region_entry.get():
                messagebox.showerror("Fehler", "Azure Key und Region sind erforderlich für Azure TTS")
                return False
        elif tts_provider == TTS_OPENAI:
            if not self.openai_key_entry.get():
                messagebox.showerror("Fehler", "OpenAI API Key ist erforderlich für OpenAI TTS")
                return False
        return True

    def validate_file(self, file_path):
        """Überprüft, ob die Datei gültig ist"""
        if not file_path.lower().endswith('.epub'):
            messagebox.showerror("Fehler", "Bitte wählen Sie eine gültige EPUB-Datei")
            return False
        if not os.path.exists(file_path):
            messagebox.showerror("Fehler", "Die ausgewählte Datei existiert nicht")
            return False
        return True

    def run_conversion(self, options, use_gutenberg=False):
        """Führt die Konvertierung durch"""
        try:
            if not self.validate_api_keys(options.get('tts')):
                return

            if 'tts' in options:
                options['tts'] = options.pop('tts')
            
            # Entferne Proxy-Konfiguration, falls vorhanden, um Probleme mit dem OpenAI-Client zu vermeiden
            if 'proxy' in options:
                options.pop('proxy')
            
            # Definiere eine explizite Liste erlaubter Parameter
            # Dies verhindert, dass unbekannte Parameter weitergegeben werden
            allowed_params = [
                'input_file', 'output_folder', 'tts', 'one_file', 'preview', 
                'output_text', 'remove_endnotes', 'log', 'newline_mode', 
                'title_mode', 'language', 'voice_name', 'output_format', 
                'model_name', 'break_duration', 'text_mode', 'custom_filename'
            ]
            
            # Filtere Optionen, so dass nur erlaubte Parameter übrigbleiben
            filtered_options = {k: v for k, v in options.items() if k in allowed_params}
                
            # Wenn Gutenberg-Text verwendet wird, erstelle eine temporäre Textdatei
            temp_text_file = None
            if use_gutenberg and self.gutenberg_text:
                # Erstelle eine temporäre Textdatei
                temp_text_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
                temp_text_file.write(f"# {self.gutenberg_text['title']}\n\n")
                temp_text_file.write(f"## by {self.gutenberg_text['author']}\n\n")
                temp_text_file.write(self.gutenberg_text['text'])
                temp_text_file.close()
                
                # Setze den Pfad als input_file
                filtered_options['input_file'] = temp_text_file.name
                # Setze Text-Modus für die Verarbeitung
                filtered_options['text_mode'] = True
                
                # Setze ein Flag für benutzerdefinierten Dateinamen 
                # (wird später in epub_to_audiobook verwendet)
                filtered_options['custom_filename'] = self.sanitize_filename(f"{self.gutenberg_text['title']} - {self.gutenberg_text['author']}")
                
                print(f"Temporäre Textdatei erstellt: {temp_text_file.name}")

            Args = namedtuple('Args', filtered_options.keys())
            args = Args(**filtered_options)

            # Setze die entsprechenden Umgebungsvariablen
            if args.tts == TTS_AZURE:
                os.environ["MS_TTS_KEY"] = self.azure_key_entry.get()
                os.environ["MS_TTS_REGION"] = self.azure_region_entry.get()
            elif args.tts == TTS_OPENAI:
                os.environ["OPENAI_API_KEY"] = self.openai_key_entry.get()
                
                # Proxy-Umgebungsvariablen temporär entfernen, um Fehler zu vermeiden
                proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "OPENAI_PROXY"]
                saved_vars = {}
                
                # Sichern und Entfernen der Proxy-Variablen
                for var in proxy_vars:
                    if var in os.environ:
                        saved_vars[var] = os.environ[var]
                        del os.environ[var]

            general_config = GeneralConfig(args)

            if args.tts == TTS_AZURE:
                tts_provider_instance = AzureTTSProvider(
                    general_config,
                    args.voice_name,
                    args.break_duration if hasattr(args, 'break_duration') else None,
                    args.output_format,
                )
            elif args.tts == TTS_OPENAI:
                # Erstelle den OpenAI-Provider mit den richtigen Parametern
                model_name = args.model_name if hasattr(args, 'model_name') else "tts-1"
                tts_provider_instance = OpenAITTSProvider(
                    general_config, 
                    model_name, 
                    args.voice_name, 
                    args.output_format
                )
            else:
                raise ValueError(f"Ungültiger TTS-Provider: {args.tts}")

            epub_to_audiobook(tts_provider_instance)
            messagebox.showinfo("Erfolg", "Konvertierung erfolgreich abgeschlossen!")
        except Exception as e:
            logging.error(f"Fehler bei der Konvertierung: {e}")
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {e}")
        finally:
            # Temporäre Datei aufräumen
            if temp_text_file and os.path.exists(temp_text_file.name):
                try:
                    os.unlink(temp_text_file.name)
                    print(f"Temporäre Datei gelöscht: {temp_text_file.name}")
                except Exception as e:
                    print(f"Fehler beim Löschen der temporären Datei: {e}")
            
            # Proxy-Umgebungsvariablen wiederherstellen
            if 'saved_vars' in locals() and args.tts == TTS_OPENAI:
                for var, value in saved_vars.items():
                    os.environ[var] = value
                    
            self.is_converting = False
            self.start_button.config(state=tk.NORMAL)

    def sanitize_filename(self, filename):
        """Entfernt ungültige Zeichen aus dem Dateinamen und kürzt ihn bei Bedarf"""
        # Ersetze Sonderzeichen durch Unterstriche
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
        # Entferne mehrfache Unterstriche
        sanitized = re.sub(r'_+', "_", sanitized)
        # Kürze auf max. 100 Zeichen (für Dateisystembeschränkungen)
        if len(sanitized) > 100:
            sanitized = sanitized[:97] + "..."
        return sanitized

    def start_conversion(self):
        """Startet die Konvertierung mit Validierung und Kostenschätzung"""
        if self.is_converting:
            messagebox.showwarning("Warnung", "Eine Konvertierung läuft bereits")
            return

        self.start_button.config(state=tk.DISABLED)
        self.is_converting = True
        options = self.get_options()
        
        # Überprüfe, ob Gutenberg-Text oder lokale Datei verwendet wird
        use_gutenberg = self.source_type_var.get() == "gutenberg_project" and self.gutenberg_text is not None
        
        # Überprüfe erforderliche Felder
        if not use_gutenberg and (not options.get('input_file') or not options.get('output_folder')):
            messagebox.showerror("Fehler", "Bitte geben Sie sowohl die Eingabedatei als auch den Ausgabepfad an.")
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return
        
        if not options.get('output_folder'):
            messagebox.showerror("Fehler", "Bitte geben Sie einen Ausgabepfad an.")
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return

        # Wenn keine Gutenberg-Quelle, dann überprüfe die Datei
        if not use_gutenberg:
            # Überprüfe Datei
            if not self.validate_file(options['input_file']):
                self.start_button.config(state=tk.NORMAL)
                self.is_converting = False
                return

            # Füge einen kundenspezifischen Dateinamen basierend auf dem Buch hinzu
            try:
                book = epub.read_epub(options['input_file'])
                book_title = book.get_metadata('DC', 'title')[0][0]
                author = book.get_metadata('DC', 'creator')[0][0]
                options['custom_filename'] = self.sanitize_filename(f"{book_title} - {author}")
                
                # Berechne die ungefähre Textlänge für Kostenschätzung
                total_chars = 0
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        content = item.get_content()
                        soup = BeautifulSoup(content, "xml")
                        text = soup.get_text()
                        total_chars += len(text)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Lesen der EPUB-Datei: {e}")
                self.start_button.config(state=tk.NORMAL)
                self.is_converting = False
                return
        else:
            # Berechne die Textlänge aus dem Gutenberg-Text
            total_chars = len(self.gutenberg_text['text'])

        # Zeige Kostenschätzung
        if not self.show_cost_estimation(total_chars):
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return

        # Starte die Konversion
        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(options, use_gutenberg))
        self.conversion_thread.daemon = True
        self.conversion_thread.start()

    def cancel_conversion(self):
        """Bricht die laufende Konvertierung ab"""
        if self.is_converting and self.conversion_thread and self.conversion_thread.is_alive():
            if messagebox.askyesno("Bestätigung", "Möchten Sie die Konvertierung wirklich abbrechen?"):
                self.is_converting = False
            self.conversion_thread.join(0)
            self.start_button.config(state=tk.NORMAL)
            messagebox.showinfo("Abgebrochen", "Konvertierung erfolgreich abgebrochen")

    def show_usage(self):
        """Zeigt Hilfe-Informationen zur Verwendung des Tools an"""
        usage_text = """
        EPUB zu Audiobook Konverter - Anleitung

        Grundlegende Schritte:
        1. Wählen Sie eine EPUB-Datei aus (Input File)
        2. Wählen Sie einen Ausgabeordner (Output Folder)
        3. Wählen Sie einen TTS-Provider (Azure oder OpenAI)
        
        Wichtige Einstellungen:
        - Output Mode: 
          * single: Erstellt eine einzelne MP3-Datei
          * multiple: Erstellt separate MP3-Dateien pro Kapitel
        
        - Newline Mode:
          * single: Neue Absätze bei einzelnen Zeilenumbrüchen
          * double: Neue Absätze bei doppelten Zeilenumbrüchen
          * none: Keine Absatzerkennung
        
        - Preview: Zeigt nur die Kapitel an, ohne sie zu konvertieren
        - Output Text: Speichert den Text zusätzlich als Textdatei
        
        TTS Provider Einstellungen:
        - Azure: Benötigt MS_TTS_KEY und MS_TTS_REGION
        - OpenAI: Benötigt OPENAI_API_KEY
        
        Hinweis: Stellen Sie sicher, dass ffmpeg installiert ist.
        """
        
        # Erstelle ein neues Fenster für die Hilfe
        help_window = tk.Toplevel(self.root)
        help_window.title("Anleitung")
        help_window.geometry("600x500")
        
        # Erstelle ein Text-Widget mit Scrollbar
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # Füge den Hilfetext hinzu
        text_widget.insert(tk.END, usage_text)
        text_widget.config(state=tk.DISABLED)  # Mache den Text schreibgeschützt
        
        # Füge einen "Schließen" Button hinzu
        close_button = ttk.Button(help_window, text="Schließen", command=help_window.destroy)
        close_button.pack(pady=10)

    def save_settings(self):
        """Speichert die Einstellungen"""
        settings = {
            "ui_language": self.current_language,
            "source_type": self.source_type_var.get(),
            "input_file": self.input_file_entry.get(),
            "gutenberg_id": self.gutenberg_id_entry.get() if hasattr(self, 'gutenberg_id_entry') else "",
            "output_folder": self.output_folder_entry.get(),
            "tts_provider": self.tts_provider_var.get(),
            "tts_language": self.tts_language_var.get(),
            "voice_name": self.voice_var.get(),
            "output_format": self.format_var.get(),
            "model_name": self.model_var.get(),  # OpenAI Modell
            "log_level": self.log_var.get(),
            "preview": self.preview_var.get(),
            "newline_mode": self.newline_var.get(),
            "title_mode": self.title_mode_var.get(),
            "single_file": self.output_mode_var.get(),
            "output_text": self.output_text_var.get(),
            "remove_endnotes": self.remove_endnotes_var.get(),
            "azure_key": self.azure_key_entry.get(),
            "azure_region": self.azure_region_entry.get(),
            "openai_key": self.openai_key_entry.get(),
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        """Lädt die gespeicherten Einstellungen"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                # Setze die UI-Sprache, falls in den Einstellungen gespeichert
                saved_language = settings.get("ui_language", self.current_language)
                if saved_language in translations:
                    self.current_language = saved_language
                    self.ui_language_var.set(saved_language)
                
                # Quellentyp
                source_type = settings.get("source_type", "local_file")
                self.source_type_var.set(source_type)
                self.on_source_type_change()
                
                self.input_file_entry.insert(0, settings.get("input_file", ""))
                if hasattr(self, 'gutenberg_id_entry'):
                    self.gutenberg_id_entry.insert(0, settings.get("gutenberg_id", ""))
                self.output_folder_entry.insert(0, settings.get("output_folder", ""))
                self.tts_provider_var.set(settings.get("tts_provider", TTS_AZURE))
                self.tts_language_var.set(settings.get("tts_language", "de-DE"))
                self.voice_var.set(settings.get("voice_name", ""))
                self.format_var.set(settings.get("output_format", "mp3"))
                self.model_var.set(settings.get("model_name", "tts-1"))  # OpenAI Modell
                self.log_var.set(settings.get("log_level", "INFO"))
                self.preview_var.set(settings.get("preview", False))
                self.newline_var.set(settings.get("newline_mode", "double"))
                self.title_mode_var.set(settings.get("title_mode", "auto"))
                self.output_mode_var.set(settings.get("single_file", "multiple"))
                self.output_text_var.set(settings.get("output_text", False))
                self.remove_endnotes_var.set(settings.get("remove_endnotes", False))
                self.azure_key_entry.insert(0, settings.get("azure_key", ""))
                self.azure_region_entry.insert(0, settings.get("azure_region", ""))
                self.openai_key_entry.insert(0, settings.get("openai_key", ""))
                
                # Provider-Einstellungen aktualisieren
                self.on_provider_change()

    def load_gui_settings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handler für das Fenster-Schließen-Event"""
        self.save_settings()
        # Temporäre Dateien aufräumen
        if self.temp_epub_file and os.path.exists(self.temp_epub_file):
            try:
                os.remove(self.temp_epub_file)
            except:
                pass
        self.root.destroy()

    def change_language(self, event=None):
        """Ändert die Sprache der Benutzeroberfläche"""
        new_language = self.ui_language_var.get()
        if new_language and new_language in translations:  # Prüfe, ob die Sprache gültig ist
            self.current_language = new_language
            self.update_ui_texts()
        else:
            # Setze zurück auf die aktuelle Sprache, falls ungültig
            self.ui_language_var.set(self.current_language)

    def update_ui_texts(self):
        """Aktualisiert alle Texte in der Benutzeroberfläche"""
        t = translations[self.current_language]
        
        # Hauptfenster
        self.root.title(t['title'])
        
        # Notebook Tabs
        self.notebook.tab(0, text=t['main_settings'])
        self.notebook.tab(1, text=t['optional_settings'])
        
        # Erforderliche Einstellungen
        self.required_frame.configure(text=t['required_settings'])
        self.source_type_label.configure(text=t['source_type'])
        self.input_file_label.configure(text=t['epub_file'])
        self.input_file_button.configure(text=t['browse'])
        self.gutenberg_id_label.configure(text=t['gutenberg_id'])
        self.gutenberg_browse_button.configure(text=t['search'])
        self.gutenberg_load_button.configure(text=t['load_gutenberg'])
        self.output_folder_label.configure(text=t['output_folder'])
        self.output_folder_button.configure(text=t['browse'])
        
        # TTS Provider
        self.tts_frame.configure(text=t['tts_settings'])
        self.tts_provider_label.configure(text=t['tts_provider'])
        self.tts_language_label.configure(text=t['language'])
        self.voice_label.configure(text=t['voice'])
        self.format_label.configure(text=t['output_format'])
        
        # Optionale Einstellungen
        self.log_label.configure(text=t['log_level'])
        self.newline_label.configure(text=t['newline_mode'])
        self.title_mode_label.configure(text=t['title_mode'])
        self.output_mode_label.configure(text=t['output_mode'])
        self.preview_check.configure(text=t['preview_mode'])
        self.output_text_check.configure(text=t['output_text'])
        self.remove_endnotes_check.configure(text=t['remove_endnotes'])
        
        # API Konfiguration
        self.api_frame.configure(text=t['api_config'])
        self.azure_frame.configure(text=t['azure_config'])
        self.azure_key_label.configure(text=t['azure_key'])
        self.azure_region_label.configure(text=t['azure_region'])
        self.openai_frame.configure(text=t['openai_config'])
        self.openai_key_label.configure(text=t['openai_key'])
        
        # Buttons
        self.start_button.configure(text=t['start_conversion'])
        self.cancel_button.configure(text=t['cancel'])
        self.usage_button.configure(text=t['help'])
        
        # Update Combobox values
        self.source_type_menu['values'] = ["local_file", "gutenberg_project"]
        self.source_type_menu.set(self.source_type_var.get())

    def show_error(self, message_key):
        """Zeigt eine Fehlermeldung in der aktuellen Sprache an"""
        messagebox.showerror(translations[self.current_language]['error'],
                           translations[self.current_language][message_key])

    def show_warning(self, message_key):
        """Zeigt eine Warnung in der aktuellen Sprache an"""
        messagebox.showwarning(translations[self.current_language]['warning'],
                             translations[self.current_language][message_key])

    def show_success(self, message_key):
        """Zeigt eine Erfolgsmeldung in der aktuellen Sprache an"""
        messagebox.showinfo(translations[self.current_language]['success'],
                          translations[self.current_language][message_key])

    def browse_gutenberg(self):
        """Öffnet einen Dialog zum Durchsuchen der Project Gutenberg-Bibliothek"""
        dialog = GutenbergBookSearchDialog(self.root, self.current_language)
        if dialog.selected_book_id:
            self.gutenberg_id_entry.delete(0, tk.END)
            self.gutenberg_id_entry.insert(0, str(dialog.selected_book_id))
            # Optional: Automatisch laden nach Auswahl
            # self.load_gutenberg_text() - Automatisches Laden deaktiviert, um Fehler zu vermeiden

if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToAudiobookGUI(root)
    root.mainloop()
