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

        self.input_file_label = ttk.Label(self.root, text="EPUB File:")
        self.input_file_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.input_file_entry = ttk.Entry(self.root, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        self.input_file_button = ttk.Button(self.root, text="Browse", command=self.browse_input_file)
        self.input_file_button.grid(row=0, column=2, padx=10, pady=10)

        self.output_folder_label = ttk.Label(self.root, text="Output Folder:")
        self.output_folder_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.output_folder_entry = ttk.Entry(self.root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
        self.output_folder_button = ttk.Button(self.root, text="Browse", command=self.browse_output_folder)
        self.output_folder_button.grid(row=1, column=2, padx=10, pady=10)

        self.api_token_label = ttk.Label(self.root, text="API Token:")
        self.api_token_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.api_token_entry = ttk.Entry(self.root, width=50)
        self.api_token_entry.grid(row=2, column=1, padx=10, pady=10)

        self.tts_provider_label = ttk.Label(self.root, text="TTS Provider:")
        self.tts_provider_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.tts_provider_var = tk.StringVar(value=TTS_AZURE)
        self.tts_provider_menu = ttk.Combobox(self.root, textvariable=self.tts_provider_var, values=[TTS_AZURE, TTS_OPENAI])
        self.tts_provider_menu.grid(row=3, column=1, padx=10, pady=10)

        self.one_file_var = tk.BooleanVar()
        self.one_file_checkbutton = ttk.Checkbutton(self.root, text="Create one big audio file", variable=self.one_file_var)
        self.one_file_checkbutton.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        self.model_name_label = ttk.Label(self.root, text="Model Name:")
        self.model_name_label.grid(row=5, column=0, padx=10, pady=10, sticky="e")
        self.model_name_entry = ttk.Entry(self.root, width=50)
        self.model_name_entry.grid(row=5, column=1, padx=10, pady=10)

        self.voice_name_label = ttk.Label(self.root, text="Voice Name:")
        self.voice_name_label.grid(row=6, column=0, padx=10, pady=10, sticky="e")
        self.voice_name_entry = ttk.Entry(self.root, width=50)
        self.voice_name_entry.grid(row=6, column=1, padx=10, pady=10)

        self.output_format_label = ttk.Label(self.root, text="Output Format:")
        self.output_format_label.grid(row=7, column=0, padx=10, pady=10, sticky="e")
        self.output_format_entry = ttk.Entry(self.root, width=50)
        self.output_format_entry.grid(row=7, column=1, padx=10, pady=10)

        self.start_button = ttk.Button(self.root, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=9, column=0, columnspan=3, padx=10, pady=10)

        self.cancel_button = ttk.Button(self.root, text="Cancel", command=self.cancel_conversion)
        self.cancel_button.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

        self.usage_button = ttk.Button(self.root, text="Usage", command=self.show_usage)
        self.usage_button.grid(row=11, column=0, columnspan=3, padx=10, pady=10)

        # Add fields for all command-line options
        self.log_label = ttk.Label(self.root, text="Log Level:")
        self.log_label.grid(row=12, column=0, padx=10, pady=10, sticky="e")
        self.log_entry = ttk.Entry(self.root, width=50)
        self.log_entry.grid(row=12, column=1, padx=10, pady=10)

        self.preview_var = tk.BooleanVar()
        self.preview_checkbutton = ttk.Checkbutton(self.root, text="Preview Mode", variable=self.preview_var)
        self.preview_checkbutton.grid(row=13, column=0, columnspan=3, padx=10, pady=10)

        self.language_label = ttk.Label(self.root, text="Language:")
        self.language_label.grid(row=14, column=0, padx=10, pady=10, sticky="e")
        self.language_entry = ttk.Entry(self.root, width=50)
        self.language_entry.grid(row=14, column=1, padx=10, pady=10)

        self.newline_mode_label = ttk.Label(self.root, text="Newline Mode:")
        self.newline_mode_label.grid(row=15, column=0, padx=10, pady=10, sticky="e")
        self.newline_mode_entry = ttk.Entry(self.root, width=50)
        self.newline_mode_entry.grid(row=15, column=1, padx=10, pady=10)

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

    def start_conversion(self):
        input_file = self.input_file_entry.get()
        output_folder = self.output_folder_entry.get()
        api_token = self.api_token_entry.get()
        tts_provider = self.tts_provider_var.get()
        one_file = self.one_file_var.get()
        model_name = self.model_name_entry.get()
        voice_name = self.voice_name_entry.get()
        output_format = self.output_format_entry.get()

        log_level = self.log_entry.get()
        preview = self.preview_var.get()
        language = self.language_entry.get()
        newline_mode = self.newline_mode_entry.get()
        title_mode = self.title_mode_entry.get()
        chapter_start = self.chapter_start_entry.get()
        chapter_end = self.chapter_end_entry.get()
        output_text = self.output_text_var.get()
        remove_endnotes = self.remove_endnotes_var.get()
        search_and_replace_file = self.search_and_replace_file_entry.get()
        voice_rate = self.voice_rate_entry.get()
        voice_volume = self.voice_volume_entry.get()
        voice_pitch = self.voice_pitch_entry.get()
        proxy = self.proxy_entry.get()
        break_duration = self.break_duration_entry.get()
        piper_path = self.piper_path_entry.get()
        piper_speaker = self.piper_speaker_entry.get()
        piper_sentence_silence = self.piper_sentence_silence_entry.get()
        piper_length_scale = self.piper_length_scale_entry.get()

        if not input_file or not output_folder or not api_token:
            messagebox.showerror("Error", "Please select input file, output folder, and enter API token.")
            return

        self.progress["value"] = 0
        self.start_button.config(state=tk.DISABLED)

        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(input_file, output_folder, api_token, tts_provider, one_file, model_name, voice_name, output_format, log_level, preview, language, newline_mode, title_mode, chapter_start, chapter_end, output_text, remove_endnotes, search_and_replace_file, voice_rate, voice_volume, voice_pitch, proxy, break_duration, piper_path, piper_speaker, piper_sentence_silence, piper_length_scale))
        self.conversion_thread.start()

    def run_conversion(self, input_file, output_folder, api_token, tts_provider, one_file, model_name, voice_name, output_format, log_level, preview, language, newline_mode, title_mode, chapter_start, chapter_end, output_text, remove_endnotes, search_and_replace_file, voice_rate, voice_volume, voice_pitch, proxy, break_duration, piper_path, piper_speaker, piper_sentence_silence, piper_length_scale):
        try:
            Args = namedtuple('Args', ['input_file', 'output_folder', 'tts', 'preview', 'language', 'newline_mode', 'chapter_start', 'chapter_end', 'output_text', 'remove_endnotes', 'one_file', 'log', 'title_mode', 'search_and_replace_file', 'voice_rate', 'voice_volume', 'voice_pitch', 'proxy', 'break_duration', 'piper_path', 'piper_speaker', 'piper_sentence_silence', 'piper_length_scale'])
            args = Args(input_file, output_folder, tts_provider, preview, language, newline_mode, chapter_start, chapter_end, output_text, remove_endnotes, one_file, log_level, title_mode, search_and_replace_file, voice_rate, voice_volume, voice_pitch, proxy, break_duration, piper_path, piper_speaker, piper_sentence_silence, piper_length_scale)

            os.environ["API_TOKEN"] = api_token

            general_config = GeneralConfig(args)

            if tts_provider == TTS_AZURE:
                tts_provider_instance = AzureTTSProvider(
                    general_config,
                    voice_name,
                    break_duration,
                    output_format,
                )
            elif tts_provider == TTS_OPENAI:
                tts_provider_instance = OpenAITTSProvider(
                    general_config, model_name, voice_name, output_format
                )
            else:
                raise ValueError(f"Invalid TTS provider: {tts_provider}")

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
            "api_token": self.api_token_entry.get(),
            "tts_provider": self.tts_provider_var.get(),
            "one_file": self.one_file_var.get(),
            "model_name": self.model_name_entry.get(),
            "voice_name": self.voice_name_entry.get(),
            "output_format": self.output_format_entry.get(),
            "log_level": self.log_entry.get(),
            "preview": self.preview_var.get(),
            "language": self.language_entry.get(),
            "newline_mode": self.newline_mode_entry.get(),
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
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.input_file_entry.insert(0, settings.get("input_file", ""))
                self.output_folder_entry.insert(0, settings.get("output_folder", ""))
                self.api_token_entry.insert(0, settings.get("api_token", ""))
                self.tts_provider_var.set(settings.get("tts_provider", TTS_AZURE))
                self.one_file_var.set(settings.get("one_file", False))
                self.model_name_entry.insert(0, settings.get("model_name", ""))
                self.voice_name_entry.insert(0, settings.get("voice_name", ""))
                self.output_format_entry.insert(0, settings.get("output_format", ""))
                self.log_entry.insert(0, settings.get("log_level", ""))
                self.preview_var.set(settings.get("preview", False))
                self.language_entry.insert(0, settings.get("language", ""))
                self.newline_mode_entry.insert(0, settings.get("newline_mode", ""))
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

    def load_gui_settings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToAudiobookGUI(root)
    root.mainloop()
