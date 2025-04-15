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
        'no_gutenberg_id': 'Bitte geben Sie eine gültige Gutenberg ID oder URL ein'
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
        'no_gutenberg_id': 'Please enter a valid Gutenberg ID or URL'
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
        
        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('TkDefaultFont', 10, 'bold'))  # Fett für bessere Sichtbarkeit
        status_label.pack(fill=tk.X, pady=5)
    
    def load_catalog(self):
        """Lädt den Gutenberg-Katalog (simuliert für dieses Beispiel)"""
        self.status_var.set(translations[self.current_language]['loading_catalog'])
        
        # In einer echten Anwendung würde hier der Katalog von einer API geladen
        # Für dieses Beispiel laden wir einen kleinen Testdatensatz
        threading.Thread(target=self._load_catalog_thread).start()
    
    def _load_catalog_thread(self):
        """Lädt den Katalog im Hintergrund"""
        try:
            # Hier würde normalerweise der API-Aufruf erfolgen
            # Für dieses Beispiel simulieren wir eine Verzögerung und laden einen Testdatensatz
            time.sleep(1)
            
            # In einer echten Anwendung würde der Katalog von einer API kommen
            # Testdaten für deutsche und englische Bücher
            self.catalog = [
                {"id": 62575, "title": "Nebel der Andromeda", "author": "Fritz Brehmer", "language": "de"},
                {"id": 1228, "title": "Die Verwandlung", "author": "Franz Kafka", "language": "de"},
                {"id": 5648, "title": "Also sprach Zarathustra", "author": "Friedrich Nietzsche", "language": "de"},
                {"id": 2229, "title": "Siddhartha", "author": "Hermann Hesse", "language": "de"},
                {"id": 11, "title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll", "language": "en"},
                {"id": 1342, "title": "Pride and Prejudice", "author": "Jane Austen", "language": "en"},
                {"id": 76, "title": "Adventures of Huckleberry Finn", "author": "Mark Twain", "language": "en"},
                {"id": 84, "title": "Frankenstein", "author": "Mary Shelley", "language": "en"},
                {"id": 2701, "title": "Moby Dick", "author": "Herman Melville", "language": "en"},
                {"id": 1952, "title": "The Yellow Wallpaper", "author": "Charlotte Perkins Gilman", "language": "en"},
                {"id": 345, "title": "Dracula", "author": "Bram Stoker", "language": "en"},
                {"id": 98, "title": "A Tale of Two Cities", "author": "Charles Dickens", "language": "en"},
                {"id": 19942, "title": "Die Leiden des jungen Werther", "author": "Johann Wolfgang von Goethe", "language": "de"},
                {"id": 2600, "title": "War and Peace", "author": "Leo Tolstoy", "language": "en"},
                {"id": 6130, "title": "Der Stechlin", "author": "Theodor Fontane", "language": "de"},
                {"id": 7205, "title": "Faust", "author": "Johann Wolfgang von Goethe", "language": "de"},
                {"id": 8242, "title": "Effi Briest", "author": "Theodor Fontane", "language": "de"},
                {"id": 16328, "title": "Beowulf", "author": "Unknown", "language": "en"},
                {"id": 2554, "title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "language": "en"},
                {"id": 219, "title": "Heart of Darkness", "author": "Joseph Conrad", "language": "en"}
            ]
            
            # Verwende after, um die UI sicher zu aktualisieren
            self.dialog.after(0, lambda: self._update_catalog())
            
        except Exception as e:
            error_message = f"{translations[self.current_language]['catalog_error']}: {str(e)}"
            self.dialog.after(0, lambda: self.status_var.set(error_message))
    
    def _update_catalog(self):
        """Aktualisiert die Kataloganzeige im UI-Thread"""
        if not self.dialog.winfo_exists():
            return  # Dialog wurde bereits geschlossen
        
        try:
            # Daten in Tabelle laden
            for book in self.catalog:
                self.results_table.insert('', 'end', values=(book["id"], book["title"], book["author"], book["language"]))
            
            self.status_var.set(f"{len(self.catalog)} Bücher geladen")
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Katalogs: {e}")
    
    def search_books(self):
        """Durchsucht den Katalog nach den angegebenen Kriterien"""
        search_term = self.search_var.get().lower()
        if search_term == translations[self.current_language]['search_placeholder'].lower():
            search_term = ""
        
        language_filter = self.language_filter_var.get()
        
        # Lösche bisherige Ergebnisse
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        
        # Filtere Bücher
        filtered_books = []
        for book in self.catalog:
            # Sprachfilter
            if language_filter != "all" and book["language"] != language_filter:
                continue
            
            # Textsuche
            if search_term and search_term not in book["title"].lower() and search_term not in book["author"].lower():
                continue
            
            filtered_books.append(book)
            self.results_table.insert('', 'end', values=(book["id"], book["title"], book["author"], book["language"]))
        
        if filtered_books:
            self.status_var.set(f"{len(filtered_books)} {translations[self.current_language]['results']}")
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
        
        # In einer echten Anwendung würde hier der Inhalt des Buchs geladen
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
        self.status_var = tk.StringVar()  # Status-Variable für Statusmeldungen

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

        # Gutenberg Frame
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

        # Stimmeinstellungen
        self.voice_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['voice'])
        self.voice_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.voice_var = tk.StringVar()
        self.voice_menu = ttk.Combobox(self.tts_frame, textvariable=self.voice_var)
        self.voice_menu.grid(row=2, column=1, padx=5, pady=5)

        # Ausgabeformat
        self.format_label = ttk.Label(self.tts_frame, text=translations[self.current_language]['output_format'])
        self.format_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.format_var = tk.StringVar(value="mp3")
        self.format_menu = ttk.Combobox(self.tts_frame, textvariable=self.format_var,
                                      values=["mp3", "wav", "ogg", "m4a"])
        self.format_menu.grid(row=3, column=1, padx=5, pady=5)

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
        elif provider == "openai":
            self.tts_language_menu['values'] = ["en-US", "en-GB"]
            self.voice_menu['values'] = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif provider == "edge":
            self.tts_language_menu['values'] = ["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT"]
            self.voice_menu['values'] = ["de-DE-Katja", "en-US-Guy", "en-GB-Susan", 
                                       "fr-FR-Julie", "es-ES-Laura", "it-IT-Elsa"]
        elif provider == "piper":
            self.tts_language_menu['values'] = ["de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT"]
            self.voice_menu['values'] = ["de_DE-thorsten", "en_US-libritts_r", "en_GB-northern_english_male",
                                       "fr_FR-siwis", "es_ES-davefx", "it_IT-riccardo_fasol"]

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
                
            # Titel und Autor extrahieren für besseren EPUB-Titel
            title = f"Gutenberg Book {gutenberg_id}"
            author = "Unknown"
            
            title_match = re.search(r'Title: (.*?)(?:\r?\n)', text)
            if title_match:
                title = title_match.group(1).strip()
            
            author_match = re.search(r'Author: (.*?)(?:\r?\n)', text)
            if author_match:
                author = author_match.group(1).strip()
            
            # Haupttext extrahieren
            main_text = ""
            if "*** START OF" in text and "*** END OF" in text:
                start_pos = text.find("*** START OF")
                start_pos = text.find("\n", start_pos) + 1
                end_pos = text.find("*** END OF")
                
                if start_pos > 0 and end_pos > start_pos:
                    main_text = text[start_pos:end_pos].strip()
            
            # Wenn die Extraktion fehlschlägt, verwenden wir den gesamten Text
            if not main_text:
                main_text = text
            
            # EPUB erstellen
            book = ebooklib.epub.EpubBook()
            book.set_title(title)
            book.set_language('en')
            book.add_author(author)
            
            # Kapitel erstellen
            chapter = ebooklib.epub.EpubHtml(title=title, file_name='chapter.xhtml')
            chapter.content = f'<html><body><h1>{title}</h1><p>{main_text.replace(chr(10), "</p><p>")}</p></body></html>'
            
            book.add_item(chapter)
            book.toc = [chapter]
            book.spine = ['nav', chapter]
            book.add_item(ebooklib.epub.EpubNcx())
            book.add_item(ebooklib.epub.EpubNav())
            
            # Temporäre Datei erstellen
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.epub')
            temp_file.close()
            
            try:
                # EPUB in temporäre Datei schreiben
                ebooklib.epub.write_epub(temp_file.name, book)
                print(f"EPUB erfolgreich erstellt: {temp_file.name}")
                
                # Pfad in das Eingabefeld eintragen
                self.input_file_entry.delete(0, tk.END)
                self.input_file_entry.insert(0, temp_file.name)
                
                # Status aktualisieren
                self.status_var.set(translations[self.current_language]['epub_created'])
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], 
                                     f"Fehler beim Erstellen der EPUB-Datei: {str(e)}")
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                self.status_var.set("")
                
        except Exception as e:
            messagebox.showerror(translations[self.current_language]['error'], 
                               f"Fehler beim Verarbeiten des Gutenberg-Textes: {str(e)}")
            self.status_var.set("")

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

    def run_conversion(self, options):
        """Führt die Konvertierung durch"""
        try:
            if not self.validate_api_keys(options.get('tts')):
                return

            if 'tts' in options:
                options['tts'] = options.pop('tts')

            Args = namedtuple('Args', options.keys())
            args = Args(**options)

            # Setze die entsprechenden Umgebungsvariablen
            if args.tts == TTS_AZURE:
                os.environ["MS_TTS_KEY"] = self.azure_key_entry.get()
                os.environ["MS_TTS_REGION"] = self.azure_region_entry.get()
            elif args.tts == TTS_OPENAI:
                os.environ["OPENAI_API_KEY"] = self.openai_key_entry.get()

            general_config = GeneralConfig(args)

            if args.tts == TTS_AZURE:
                tts_provider_instance = AzureTTSProvider(
                    general_config,
                    args.voice_name,
                    args.break_duration,
                    args.output_format,
                )
            elif args.tts == TTS_OPENAI:
                tts_provider_instance = OpenAITTSProvider(
                    general_config, args.model_name, args.voice_name, args.output_format
                )
            else:
                raise ValueError(f"Ungültiger TTS-Provider: {args.tts}")

            epub_to_audiobook(tts_provider_instance)
            messagebox.showinfo("Erfolg", "Konvertierung erfolgreich abgeschlossen!")
        except Exception as e:
            logging.error(f"Fehler bei der Konvertierung: {e}")
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {e}")
        finally:
            self.is_converting = False
            self.start_button.config(state=tk.NORMAL)

    def start_conversion(self):
        """Startet die Konvertierung mit Validierung und Kostenschätzung"""
        if self.is_converting:
            messagebox.showwarning("Warnung", "Eine Konvertierung läuft bereits")
            return

        self.start_button.config(state=tk.DISABLED)
        self.is_converting = True
        options = self.get_options()

        # Überprüfe erforderliche Felder
        if not options.get('input_file') or not options.get('output_folder'):
            messagebox.showerror("Fehler", "Bitte geben Sie sowohl die Eingabedatei als auch den Ausgabepfad an.")
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return

        # Überprüfe Datei
        if not self.validate_file(options['input_file']):
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return

        # Lese die EPUB-Datei und schätze die Kosten
        try:
            book = epub.read_epub(options['input_file'])
            total_chars = 0
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    soup = BeautifulSoup(content, "xml")
                    text = soup.get_text()
                    total_chars += len(text)

            # Zeige Kostenschätzung
            if not self.show_cost_estimation(total_chars):
                self.start_button.config(state=tk.NORMAL)
                self.is_converting = False
                return

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Lesen der EPUB-Datei: {e}")
            self.start_button.config(state=tk.NORMAL)
            self.is_converting = False
            return

        # Starte die Konversion
        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(options,))
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
            "gutenberg_id": self.gutenberg_id_entry.get(),
            "output_folder": self.output_folder_entry.get(),
            "tts_provider": self.tts_provider_var.get(),
            "tts_language": self.tts_language_var.get(),
            "voice_name": self.voice_var.get(),
            "output_format": self.format_var.get(),
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
                self.gutenberg_id_entry.insert(0, settings.get("gutenberg_id", ""))
                self.output_folder_entry.insert(0, settings.get("output_folder", ""))
                self.tts_provider_var.set(settings.get("tts_provider", TTS_AZURE))
                self.tts_language_var.set(settings.get("tts_language", "de-DE"))
                self.voice_var.set(settings.get("voice_name", ""))
                self.format_var.set(settings.get("output_format", "mp3"))
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
