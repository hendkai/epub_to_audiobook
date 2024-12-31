import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from epub_to_audiobook import epub_to_audiobook, GeneralConfig, AzureTTSProvider, OpenAITTSProvider, TTS_AZURE, TTS_OPENAI
import threading
import os
from collections import namedtuple
import json

class EpubToAudiobookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB to Audiobook Converter")
        self.root.configure(bg="#2E2E2E")

        self.settings_file = "gui_settings.json"

        # Initialize preview attribute
        self.preview = None

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", background="#2E2E2E", foreground="#FFFFFF")
        style.configure("TButton", background="#4CAF50", foreground="#FFFFFF")
        style.configure("TEntry", fieldbackground="#3E3E3E", foreground="#FFFFFF")
        style.configure("TCheckbutton", background="#2Espo2E2E", foreground="#FFFFFF")
        style.configure("TCombobox", fieldbackground="#3E3E3E", foreground="#FFFFFF")
        style.configure("TProgressbar", background="#4CAF50")

        # Erstelle ein Notebook für verschiedene Kategorien
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # Haupteinstellungen
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main Settings")

        # Required Settings
        required_frame = ttk.LabelFrame(main_frame, text="Required Settings")
        required_frame.pack(fill="x", padx=5, pady=5)

        # Input/Output
        self.input_file_label = ttk.Label(required_frame, text="EPUB File:")
        self.input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.input_file_entry = ttk.Entry(required_frame, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_file_button = ttk.Button(required_frame, text="Browse", command=self.browse_input_file)
        self.input_file_button.grid(row=0, column=2, padx=5, pady=5)

        self.output_folder_label = ttk.Label(required_frame, text="Output Folder:")
        self.output_folder_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.output_folder_entry = ttk.Entry(required_frame, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_folder_button = ttk.Button(required_frame, text="Browse", command=self.browse_output_folder)
        self.output_folder_button.grid(row=1, column=2, padx=5, pady=5)

        # TTS Provider Settings
        tts_frame = ttk.LabelFrame(main_frame, text="TTS Provider Settings")
        tts_frame.pack(fill="x", padx=5, pady=5)

        self.tts_provider_label = ttk.Label(tts_frame, text="TTS Provider:")
        self.tts_provider_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.tts_provider_var = tk.StringVar(value="azure")
        self.tts_provider_menu = ttk.Combobox(tts_frame, textvariable=self.tts_provider_var, 
                                             values=["azure", "openai", "edge", "piper"])
        self.tts_provider_menu.grid(row=0, column=1, padx=5, pady=5)

        # Optional Settings Tab
        optional_frame = ttk.Frame(self.notebook)
        self.notebook.add(optional_frame, text="Optional Settings")

        # Log Level
        self.log_label = ttk.Label(optional_frame, text="Log Level:")
        self.log_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.log_var = tk.StringVar()
        self.log_menu = ttk.Combobox(optional_frame, textvariable=self.log_var,
                                    values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_menu.grid(row=0, column=1, padx=5, pady=5)

        # Preview Mode
        self.preview_var = tk.BooleanVar()
        self.preview_check = ttk.Checkbutton(optional_frame, text="Preview Mode", 
                                            variable=self.preview_var)
        self.preview_check.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Newline Mode
        self.newline_label = ttk.Label(optional_frame, text="Newline Mode:")
        self.newline_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.newline_var = tk.StringVar()
        self.newline_menu = ttk.Combobox(optional_frame, textvariable=self.newline_var,
                                        values=["single", "double", "none"])
        self.newline_menu.grid(row=2, column=1, padx=5, pady=5)

        # Title Mode
        self.title_mode_label = ttk.Label(optional_frame, text="Title Mode:")
        self.title_mode_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.title_mode_var = tk.StringVar()
        self.title_mode_menu = ttk.Combobox(optional_frame, textvariable=self.title_mode_var,
                                           values=["auto", "tag_text", "first_few"])
        self.title_mode_menu.grid(row=3, column=1, padx=5, pady=5)

        # Single File Output Option
        self.single_file_label = ttk.Label(optional_frame, text="Output Mode:")
        self.single_file_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.single_file_var = tk.StringVar(value="multiple")  # Default: multiple files
        self.single_file_menu = ttk.Combobox(optional_frame, textvariable=self.single_file_var,
                                            values=["single", "multiple"])
        self.single_file_menu.grid(row=4, column=1, padx=5, pady=5)

        # Add model name field
        self.model_name_label = ttk.Label(self.root, text="Model Name:")
        self.model_name_label.grid(row=31, column=0, padx=10, pady=10, sticky="e")
        self.model_name_entry = ttk.Entry(self.root, width=50)
        self.model_name_entry.grid(row=31, column=1, padx=10, pady=10)

        # Add voice name field
        self.voice_name_label = ttk.Label(self.root, text="Voice Name:")
        self.voice_name_label.grid(row=32, column=0, padx=10, pady=10, sticky="e")
        self.voice_name_entry = ttk.Entry(self.root, width=50)
        self.voice_name_entry.grid(row=32, column=1, padx=10, pady=10)

        # Add output format field
        self.output_format_label = ttk.Label(self.root, text="Output Format:")
        self.output_format_label.grid(row=33, column=0, padx=10, pady=10, sticky="e")
        self.output_format_entry = ttk.Entry(self.root, width=50)
        self.output_format_entry.insert(0, "mp3")  # Set default to mp3
        self.output_format_entry.config(state='readonly')  # Make it read-only
        self.output_format_entry.grid(row=33, column=1, padx=10, pady=10)

        # ... (weitere optionale Einstellungen) ...

        self.start_button = ttk.Button(self.root, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=9, column=0, columnspan=3, padx=10, pady=10)

        self.cancel_button = ttk.Button(self.root, text="Cancel", command=self.cancel_conversion)
        self.cancel_button.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

        self.usage_button = ttk.Button(self.root, text="Usage", command=self.show_usage)
        self.usage_button.grid(row=11, column=0, columnspan=3, padx=10, pady=10)

        # Add fields for all command-line options
        self.preview_var = tk.BooleanVar()
        self.preview_checkbutton = ttk.Checkbutton(self.root, text="Preview Mode", variable=self.preview_var)
        self.preview_checkbutton.grid(row=13, column=0, columnspan=3, padx=10, pady=10)

        self.language_label = ttk.Label(self.root, text="Language:")
        self.language_label.grid(row=14, column=0, padx=10, pady=10, sticky="e")
        self.language_entry = ttk.Entry(self.root, width=50)
        self.language_entry.grid(row=14, column=1, padx=10, pady=10)

        self.title_mode_label = ttk.Label(self.root, text="Title Mode:")
        self.title_mode_label.grid(row=16, column=0, padx=10, pady=10, sticky="e")
        self.title_mode_entry = ttk.Entry(self.root, width=50)
        self.title_mode_entry.grid(row=16, column=1, padx=10, pady=10)

        self.chapter_start_label = ttk.Label(self.root, text="Chapter Start:")
        self.chapter_start_label.grid(row=17, column=0, padx=10, pady=10, sticky="e")
        self.chapter_start_entry = ttk.Entry(self.root, width=50)
        self.chapter_start_entry.grid(row=17, column=1, padx=10, pady=10)

        self.chapter_end_label = ttk.Label(self.root, text="Chapter End:")
        self.chapter_end_label.grid(row=18, column=0, padx=10, pady=10, sticky="e")
        self.chapter_end_entry = ttk.Entry(self.root, width=50)
        self.chapter_end_entry.grid(row=18, column=1, padx=10, pady=10)

        self.output_text_var = tk.BooleanVar()
        self.output_text_checkbutton = ttk.Checkbutton(self.root, text="Output Text", variable=self.output_text_var)
        self.output_text_checkbutton.grid(row=19, column=0, columnspan=3, padx=10, pady=10)

        self.remove_endnotes_var = tk.BooleanVar()
        self.remove_endnotes_checkbutton = ttk.Checkbutton(self.root, text="Remove Endnotes", variable=self.remove_endnotes_var)
        self.remove_endnotes_checkbutton.grid(row=20, column=0, columnspan=3, padx=10, pady=10)

        self.search_and_replace_file_label = ttk.Label(self.root, text="Search and Replace File:")
        self.search_and_replace_file_label.grid(row=21, column=0, padx=10, pady=10, sticky="e")
        self.search_and_replace_file_entry = ttk.Entry(self.root, width=50)
        self.search_and_replace_file_entry.grid(row=21, column=1, padx=10, pady=10)

        self.voice_rate_label = ttk.Label(self.root, text="Voice Rate:")
        self.voice_rate_label.grid(row=22, column=0, padx=10, pady=10, sticky="e")
        self.voice_rate_entry = ttk.Entry(self.root, width=50)
        self.voice_rate_entry.grid(row=22, column=1, padx=10, pady=10)

        self.voice_volume_label = ttk.Label(self.root, text="Voice Volume:")
        self.voice_volume_label.grid(row=23, column=0, padx=10, pady=10, sticky="e")
        self.voice_volume_entry = ttk.Entry(self.root, width=50)
        self.voice_volume_entry.grid(row=23, column=1, padx=10, pady=10)

        self.voice_pitch_label = ttk.Label(self.root, text="Voice Pitch:")
        self.voice_pitch_label.grid(row=24, column=0, padx=10, pady=10, sticky="e")
        self.voice_pitch_entry = ttk.Entry(self.root, width=50)
        self.voice_pitch_entry.grid(row=24, column=1, padx=10, pady=10)

        self.proxy_label = ttk.Label(self.root, text="Proxy:")
        self.proxy_label.grid(row=25, column=0, padx=10, pady=10, sticky="e")
        self.proxy_entry = ttk.Entry(self.root, width=50)
        self.proxy_entry.grid(row=25, column=1, padx=10, pady=10)

        self.break_duration_label = ttk.Label(self.root, text="Break Duration:")
        self.break_duration_label.grid(row=26, column=0, padx=10, pady=10, sticky="e")
        self.break_duration_entry = ttk.Entry(self.root, width=50)
        self.break_duration_entry.grid(row=26, column=1, padx=10, pady=10)

        self.piper_path_label = ttk.Label(self.root, text="Piper Path:")
        self.piper_path_label.grid(row=27, column=0, padx=10, pady=10, sticky="e")
        self.piper_path_entry = ttk.Entry(self.root, width=50)
        self.piper_path_entry.grid(row=27, column=1, padx=10, pady=10)

        self.piper_speaker_label = ttk.Label(self.root, text="Piper Speaker:")
        self.piper_speaker_label.grid(row=28, column=0, padx=10, pady=10, sticky="e")
        self.piper_speaker_entry = ttk.Entry(self.root, width=50)
        self.piper_speaker_entry.grid(row=28, column=1, padx=10, pady=10)

        self.piper_sentence_silence_label = ttk.Label(self.root, text="Piper Sentence Silence:")
        self.piper_sentence_silence_label.grid(row=29, column=0, padx=10, pady=10, sticky="e")
        self.piper_sentence_silence_entry = ttk.Entry(self.root, width=50)
        self.piper_sentence_silence_entry.grid(row=29, column=1, padx=10, pady=10)

        self.piper_length_scale_label = ttk.Label(self.root, text="Piper Length Scale:")
        self.piper_length_scale_label.grid(row=30, column=0, padx=10, pady=10, sticky="e")
        self.piper_length_scale_entry = ttk.Entry(self.root, width=50)
        self.piper_length_scale_entry.grid(row=30, column=1, padx=10, pady=10)

        # Füge API-Konfiguration hinzu
        self.api_config_label = ttk.Label(self.root, text="API Configuration:")
        self.api_config_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        self.api_frame = ttk.Frame(self.root)
        self.api_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Azure Konfiguration
        self.azure_frame = ttk.LabelFrame(self.api_frame, text="Azure Configuration")
        self.azure_frame.pack(fill="x", padx=5, pady=5)
        
        self.azure_key_label = ttk.Label(self.azure_frame, text="Azure Key:")
        self.azure_key_label.grid(row=0, column=0, padx=5, pady=5)
        self.azure_key_entry = ttk.Entry(self.azure_frame, width=40)
        self.azure_key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.azure_region_label = ttk.Label(self.azure_frame, text="Azure Region:")
        self.azure_region_label.grid(row=1, column=0, padx=5, pady=5)
        self.azure_region_entry = ttk.Entry(self.azure_frame, width=40)
        self.azure_region_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # OpenAI Konfiguration
        self.openai_frame = ttk.LabelFrame(self.api_frame, text="OpenAI Configuration")
        self.openai_frame.pack(fill="x", padx=5, pady=5)
        
        self.openai_key_label = ttk.Label(self.openai_frame, text="OpenAI Key:")
        self.openai_key_label.grid(row=0, column=0, padx=5, pady=5)
        self.openai_key_entry = ttk.Entry(self.openai_frame, width=40)
        self.openai_key_entry.grid(row=0, column=1, padx=5, pady=5)

        self.load_gui_settings()

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
        options['one_file'] = self.single_file_var.get() == "single"  # Renamed from single_file to one_file

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

        if self.language_entry.get():
            options['language'] = self.language_entry.get()

        # Füge chapter_start und chapter_end nur hinzu, wenn sie nicht leer sind
        chapter_start = self.chapter_start_entry.get()
        if chapter_start:
            try:
                options['chapter_start'] = int(chapter_start)
            except ValueError:
                pass

        chapter_end = self.chapter_end_entry.get()
        if chapter_end:
            try:
                options['chapter_end'] = int(chapter_end)
            except ValueError:
                pass

        # Weitere optionale Einstellungen
        if self.voice_name_entry.get():
            options['voice_name'] = self.voice_name_entry.get()
        
        if self.model_name_entry.get():
            options['model_name'] = self.model_name_entry.get()

        if self.output_format_entry.get():
            options['output_format'] = self.output_format_entry.get()

        # Filtere None und leere Strings
        return {k: v for k, v in options.items() if v not in (None, "")}


    def run_conversion(self, options):
        try:
            # Filtere nur leere Strings und None-Werte, behalte False-Werte
            options = {k: v for k, v in options.items() if v is not None and v != ""}

            Args = namedtuple('Args', options.keys())
            args = Args(**options)

            # Setze die entsprechenden Umgebungsvariablen basierend auf dem gewählten Provider
            if args.tts == TTS_AZURE:
                azure_key = self.azure_key_entry.get()
                azure_region = self.azure_region_entry.get()
                if not azure_key or not azure_region:
                    raise ValueError("Azure Key and Region are required for Azure TTS")
                os.environ["MS_TTS_KEY"] = azure_key
                os.environ["MS_TTS_REGION"] = azure_region
            elif args.tts == TTS_OPENAI:
                openai_key = self.openai_key_entry.get()
                if not openai_key:
                    raise ValueError("OpenAI API Key is required for OpenAI TTS")
                os.environ["OPENAI_API_KEY"] = openai_key

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
                raise ValueError(f"Invalid TTS provider: {args.tts}")

            epub_to_audiobook(tts_provider_instance)
            messagebox.showinfo("Success", "Conversion completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.start_button.config(state=tk.NORMAL)

    def run_conversion(self, options):
        try:
            if 'tts' in options:
                options['tts'] = options.pop('tts')

            Args = namedtuple('Args', options.keys())
            args = Args(**options)

            # Setze die entsprechenden Umgebungsvariablen basierend auf dem gewählten Provider
            if args.tts == TTS_AZURE:
                azure_key = self.azure_key_entry.get()
                azure_region = self.azure_region_entry.get()
                if not azure_key or not azure_region:
                    raise ValueError("Azure Key and Region are required for Azure TTS")
                os.environ["MS_TTS_KEY"] = azure_key
                os.environ["MS_TTS_REGION"] = azure_region
            elif args.tts == TTS_OPENAI:
                openai_key = self.openai_key_entry.get()
                if not openai_key:
                    raise ValueError("OpenAI API Key is required for OpenAI TTS")
                os.environ["OPENAI_API_KEY"] = openai_key

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
                raise ValueError(f"Invalid TTS provider: {args.tts}")

            epub_to_audiobook(tts_provider_instance)
            messagebox.showinfo("Success", "Conversion completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.start_button.config(state=tk.NORMAL)

    def cancel_conversion(self):
        if self.conversion_thread.is_alive():
            self.conversion_thread.join(0)
            messagebox.showinfo("Cancelled", "Conversion cancelled successfully!")
            self.start_button.config(state=tk.NORMAL)

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
        settings = {
            "input_file": self.input_file_entry.get(),
            "output_folder": self.output_folder_entry.get(),
            "tts_provider": self.tts_provider_var.get(),
            "model_name": self.model_name_entry.get(),
            "voice_name": self.voice_name_entry.get(),
            "output_format": self.output_format_entry.get(),
            "log_level": self.log_var.get(),
            "preview": self.preview_var.get(),
            "language": self.language_entry.get(),
            "newline_mode": self.newline_var.get(),
            "title_mode": self.title_mode_entry.get(),
            "chapter_start": self.chapter_start_entry.get(),
            "chapter_end": self.chapter_end_entry.get(),
            "output_text": self.output_text_var.get(),
            "remove_endnotes": self.remove_endnotes_var.get(),
            "search_and_replace_file": self.search_and_replace_file_entry.get(),
            "voice_rate": self.voice_rate_entry.get(),
            "voice_volume": self.voice_volume_entry.get(),
            "voice_pitch": self.voice_pitch_entry.get(),
            "proxy": self.proxy_entry.get(),
            "break_duration": self.break_duration_entry.get(),
            "piper_path": self.piper_path_entry.get(),
            "piper_speaker": self.piper_speaker_entry.get(),
            "piper_sentence_silence": self.piper_sentence_silence_entry.get(),
            "piper_length_scale": self.piper_length_scale_entry.get(),
            "azure_key": self.azure_key_entry.get(),
            "azure_region": self.azure_region_entry.get(),
            "openai_key": self.openai_key_entry.get(),
            "single_file": self.single_file_var.get(),
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.input_file_entry.insert(0, settings.get("input_file", ""))
                self.output_folder_entry.insert(0, settings.get("output_folder", ""))
                self.tts_provider_var.set(settings.get("tts_provider", TTS_AZURE))
                self.model_name_entry.insert(0, settings.get("model_name", ""))
                self.voice_name_entry.insert(0, settings.get("voice_name", ""))
                self.output_format_entry.insert(0, settings.get("output_format", ""))
                self.log_var.set(settings.get("log_level", ""))
                self.preview_var.set(settings.get("preview", False))
                self.language_entry.insert(0, settings.get("language", ""))
                self.newline_var.set(settings.get("newline_mode", "double"))
                self.title_mode_entry.insert(0, settings.get("title_mode", ""))
                self.chapter_start_entry.insert(0, settings.get("chapter_start", ""))
                self.chapter_end_entry.insert(0, settings.get("chapter_end", ""))
                self.output_text_var.set(settings.get("output_text", False))
                self.remove_endnotes_var.set(settings.get("remove_endnotes", False))
                self.search_and_replace_file_entry.insert(0, settings.get("search_and_replace_file", ""))
                self.voice_rate_entry.insert(0, settings.get("voice_rate", ""))
                self.voice_volume_entry.insert(0, settings.get("voice_volume", ""))
                self.voice_pitch_entry.insert(0, settings.get("voice_pitch", ""))
                self.proxy_entry.insert(0, settings.get("proxy", ""))
                self.break_duration_entry.insert(0, settings.get("break_duration", ""))
                self.piper_path_entry.insert(0, settings.get("piper_path", ""))
                self.piper_speaker_entry.insert(0, settings.get("piper_speaker", ""))
                self.piper_sentence_silence_entry.insert(0, settings.get("piper_sentence_silence", ""))
                self.piper_length_scale_entry.insert(0, settings.get("piper_length_scale", ""))
                self.azure_key_entry.insert(0, settings.get("azure_key", ""))
                self.azure_region_entry.insert(0, settings.get("azure_region", ""))
                self.openai_key_entry.insert(0, settings.get("openai_key", ""))
                self.single_file_var.set(settings.get("single_file", "multiple"))

    def load_gui_settings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def start_conversion(self):
        self.start_button.config(state=tk.DISABLED)
        options = self.get_options()

        # Überprüfen Sie, ob die erforderlichen Felder ausgefüllt sind
        if not options.get('input_file') or not options.get('output_folder'):
            messagebox.showerror("Fehler", "Bitte geben Sie sowohl die Eingabedatei als auch den Ausgabepfad an.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Starte die Konversion in einem separaten Thread
        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(options,))
        self.conversion_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToAudiobookGUI(root)
    root.mainloop()
