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

        # Replace newline mode entry with checkboxes
        self.newline_mode_label = ttk.Label(self.root, text="Newline Mode:")
        self.newline_mode_label.grid(row=15, column=0, padx=10, pady=10, sticky="e")
        
        self.newline_mode_frame = ttk.Frame(self.root)
        self.newline_mode_frame.grid(row=15, column=1, padx=10, pady=10, sticky="w")
        
        self.newline_mode_var = tk.StringVar(value="double")
        self.single_newline = ttk.Radiobutton(self.newline_mode_frame, text="Single", variable=self.newline_mode_var, value="single")
        self.double_newline = ttk.Radiobutton(self.newline_mode_frame, text="Double", variable=self.newline_mode_var, value="double")
        self.none_newline = ttk.Radiobutton(self.newline_mode_frame, text="None", variable=self.newline_mode_var, value="none")
        
        self.single_newline.pack(side=tk.LEFT, padx=5)
        self.double_newline.pack(side=tk.LEFT, padx=5)
        self.none_newline.pack(side=tk.LEFT, padx=5)

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

        # Optional settings - nur hinzufügen wenn gesetzt
        if self.log_var.get():
            options['log'] = self.log_var.get()
        
        # Setze preview immer, auch wenn es False ist
        options['preview'] = self.preview_var.get()

        if self.newline_var.get() and self.newline_var.get() != "none":
            options['newline_mode'] = self.newline_var.get()

        if self.title_mode_var.get():
            options['title_mode'] = self.title_mode_var.get()

        if self.language_entry.get():
            options['language'] = self.language_entry.get()

        # ... (weitere optionale Einstellungen) ...

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
        usage_text = """
        Usage:
        main.py [-h] [--tts {azure,openai,edge,piper}]
               [--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--preview]
               [--no_prompt] [--language LANGUAGE]
               [--newline_mode {single,double,none}]
               [--title_mode {auto,tag_text,first_few}]
               [--chapter_start CHAPTER_START] [--chapter_end CHA   PTER_END]
               [--output_text] [--remove_endnotes]
               [--search_and_replace_file SEARCH_AND_REPLACE_FILE]
               [--voice_name VOICE_NAME] [--output_format OUTPUT_FORMAT]
               [--model_name MODEL_NAME] [--voice_rate VOICE_RATE]
               [--voice_volume VOICE_VOLUME] [--voice_pitch VOICE_PITCH]
               [--proxy PROXY] [--break_duration BREAK_DURATION]
               [--piper_path PIPER_PATH] [--piper_speaker PIPER_SPEAKER]
               [--piper_sentence_silence PIPER_SENTENCE_SILENCE]
               [--piper_length_scale PIPER_LENGTH_SCALE]
               input_file output_folder

        Convert text book to audiobook

        positional arguments:
          input_file            Path to the EPUB file
          output_folder         Path to the output folder

        options:
          -h, --help            show this help message and exit
          --tts {azure,openai,edge,piper}
                                Choose TTS provider (default: azure). azure: Azure
                                Cognitive Services, openai: OpenAI TTS API. When using
                                azure, environment variables MS_TTS_KEY and
                                MS_TTS_REGION must be set. When using openai,
                                environment variable OPENAI_API_KEY must be set.
          --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                                Log level (default: INFO), can be DEBUG, INFO,
                                WARNING, ERROR, CRITICAL
          --preview             Enable preview mode. In preview mode, the script will
                                not convert the text to speech. Instead, it will print
                                the chapter index, titles, and character counts.
          --no_prompt           Don't ask the user if they wish to continue after
                                estimating the cloud cost for TTS. Useful for
                                scripting.
          --language LANGUAGE   Language for the text-to-speech service (default: en-
                                US). For Azure TTS (--tts=azure), check
                                https://learn.microsoft.com/en-us/azure/ai-
                                services/speech-service/language-
                                support?tabs=tts#text-to-speech for supported
                                languages. For OpenAI TTS (--tts=openai), their API
                                detects the language automatically. But setting this
                                will also help on splitting the text into chunks with
                                different strategies in this tool, especially for
                                Chinese characters. For Chinese books, use zh-CN, zh-
                                TW, or zh-HK.
          --newline_mode {single,double,none}
                                Choose the mode of detecting new paragraphs: 'single',
                                'double', or 'none'. 'single' means a single newline
                                character, while 'double' means two consecutive
                                newline characters. 'none' means all newline
                                characters will be replace with blank so paragraphs
                                will not be detected. (default: double, works for most
                                ebooks but will detect less paragraphs for some
                                ebooks)
          --title_mode {auto,tag_text,first_few}
                                Choose the parse mode for chapter title, 'tag_text'
                                search 'title','h1','h2','h3' tag for title,
                                'first_few' set first 60 characters as title, 'auto'
                                auto apply the best mode for current chapter.
          --chapter_start CHAPTER_START
                                Chapter start index (default: 1, starting from 1)
          --chapter_end CHAPTER_END
                                Chapter end index (default: -1, meaning to the last
                                chapter)
          --output_text         Enable Output Text. This will export a plain text file
                                for each chapter specified and write the files to the
                                output folder specified.
          --remove_endnotes     This will remove endnote numbers from the end or
                                middle of sentences. This is useful for academic
                                books.
          --search_and_replace_file SEARCH_AND_REPLACE_FILE
                                Path to a file that contains 1 regex replace per line,
                                to help with fixing pronunciations, etc. The format
                                is: <search>==<replace> Note that you may have to
                                specify word boundaries, to avoid replacing parts of
                                words.
          --voice_name VOICE_NAME
                                Various TTS providers has different voice names, look
                                up for your provider settings.
          --output_format OUTPUT_FORMAT
                                Output format for the text-to-speech service.
                                Supported format depends on selected TTS provider
          --model_name MODEL_NAME
                                Various TTS providers has different neural model names

        edge specific:
          --voice_rate VOICE_RATE
                                Speaking rate of the text. Valid relative values range
                                from -50%(--xxx='-50%') to +100%. For negative value
                                use format --arg=value,
          --voice_volume VOICE_VOLUME
                                Volume level of the speaking voice. Valid relative
                                values floor to -100%. For negative value use format
                                --arg=value,
          --voice_pitch VOICE_PITCH
                                Baseline pitch for the text.Valid relative values like
                                -80Hz,+50Hz, pitch changes should be within 0.5 to 1.5
                                times the original audio. For negative value use
                                format --arg=value,
          --proxy PROXY         Proxy server for the TTS provider. Format:
                                http://[username:password@]proxy.server:port

        azure/edge specific:
          --break_duration BREAK_DURATION
                                Break duration in milliseconds for the different
                                paragraphs or sections (default: 1250, means 1.25 s).
                                Valid values range from 0 to 5000 milliseconds for
                                Azure TTS.

        piper specific:
          --piper_path PIPER_PATH
                                Path to the Piper TTS executable
          --piper_speaker PIPER_SPEAKER
                                Piper speaker id, used for multi-speaker models
          --piper_sentence_silence PIPER_SENTENCE_SILENCE
                                Seconds of silence after each sentence
          --piper_length_scale PIPER_LENGTH_SCALE
                                Phoneme length, a.k.a. speaking rate
        """
        messagebox.showinfo("Usage", usage_text)

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
            "newline_mode": self.newline_mode_var.get(),
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
                self.newline_mode_var.set(settings.get("newline_mode", "double"))
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

    def load_gui_settings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def start_conversion(self):
        self.start_button.config(state=tk.DISABLED)
        options = self.get_options()
        
        # Starte die Konversion in einem separaten Thread
        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(options,))
        self.conversion_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToAudiobookGUI(root)
    root.mainloop()
