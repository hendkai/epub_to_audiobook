import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from epub_to_audiobook import epub_to_audiobook, GeneralConfig, AzureTTSProvider, OpenAITTSProvider, TTS_AZURE, TTS_OPENAI
import threading
import os
from collections import namedtuple

class EpubToAudiobookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB to Audiobook Converter")
        self.root.configure(bg="#2E2E2E")

        self.create_widgets()

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

        self.usage_button = ttk.Button(self.root, text="Usage", command=self.show_usage)
        self.usage_button.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

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

        if not input_file or not output_folder or not api_token:
            messagebox.showerror("Error", "Please select input file, output folder, and enter API token.")
            return

        self.progress["value"] = 0
        self.start_button.config(state=tk.DISABLED)

        threading.Thread(target=self.run_conversion, args=(input_file, output_folder, api_token, tts_provider, one_file, model_name, voice_name, output_format)).start()

    def run_conversion(self, input_file, output_folder, api_token, tts_provider, one_file, model_name, voice_name, output_format):
        try:
            Args = namedtuple('Args', ['input_file', 'output_folder', 'tts', 'preview', 'language', 'newline_mode', 'chapter_start', 'chapter_end', 'output_text', 'remove_endnotes', 'one_file'])
            args = Args(input_file, output_folder, tts_provider, False, "en-US", "double", 1, -1, False, False, one_file)

            os.environ["API_TOKEN"] = api_token

            general_config = GeneralConfig(args)

            if tts_provider == TTS_AZURE:
                tts_provider_instance = AzureTTSProvider(
                    general_config,
                    voice_name,
                    "1250",
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

if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToAudiobookGUI(root)
    root.mainloop()
