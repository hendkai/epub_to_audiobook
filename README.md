# 🎧 EPUB to Audiobook Converter

A powerful tool to convert EPUB ebooks into audiobooks with various TTS options.

## ✨ Key Features

- 🔄 Multiple TTS Provider Support:
  - 🔹 Microsoft Azure Text-to-Speech API
  - 🔹 OpenAI Text-to-Speech API
- 📚 Flexible Output Options:
  - 🔸 Single MP3 file for the entire book
  - 🔸 Separate MP3 files for each chapter
- 🎯 Optimized for [Audiobookshelf](https://github.com/advplyr/audiobookshelf)
- 🖥️ User-friendly GUI available

## 🚀 Quick Start

1. **Installation**:
   ```bash
   git clone https://github.com/p0n1/epub_to_audiobook.git
   cd epub_to_audiobook
   pip install -r requirements.txt
   ```

2. **Launch the GUI**:
   ```bash
   python gui.py
   ```

## 📋 Requirements

- Python 3.6+ or **Docker**
- For Azure TTS: Microsoft Azure account with [Speech Services](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices)
- For OpenAI TTS: OpenAI [API Key](https://platform.openai.com/api-keys)
- ffmpeg installed on your system

## 🎮 Usage

### GUI Mode (Recommended)
1. Launch the application: `python gui.py`
2. Select your EPUB file
3. Choose output folder
4. Select TTS provider
5. Enter your API credentials in the settings:
   - For Azure: Enter your Key and Region
   - For OpenAI: Enter your API Key
6. Configure output options:
   - Single file or multiple files
   - Language settings
   - Voice options
7. Click "Start Conversion"

### Command Line Mode (Alternative)
For command line usage, you'll need to set environment variables:
```bash
# For Azure TTS
export MS_TTS_KEY=<your_subscription_key>
export MS_TTS_REGION=<your_region>

# For OpenAI TTS
export OPENAI_API_KEY=<your_openai_api_key>

# Then run
python epub_to_audiobook.py <input_file> <output_folder> [options]
```

## 🔧 Advanced Options

- **Output Format**:
  - Single file: Combines all chapters into one MP3
  - Multiple files: Creates separate MP3s for each chapter

- **Text Processing**:
  - Newline modes: single/double/none
  - Endnote removal
  - Custom break duration

- **TTS Settings**:
  - Voice selection
  - Language options
  - Model selection (OpenAI)
  - Audio quality settings

## 🐳 Docker Support

```bash
# Pull the image
docker pull ghcr.io/p0n1/epub_to_audiobook:latest

# Run with GUI (recommended)
docker run --rm -v ./:/app \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  ghcr.io/p0n1/epub_to_audiobook python gui.py

# Or run command line version
docker run --rm -v ./:/app \
  -e MS_TTS_KEY=$MS_TTS_KEY \
  -e MS_TTS_REGION=$MS_TTS_REGION \
  ghcr.io/p0n1/epub_to_audiobook your_book.epub audiobook_output --tts azure
```

## 🔍 Troubleshooting

- **ffmpeg not found**: Install ffmpeg using your system's package manager
- **API Key Issues**: Check if the credentials are entered correctly in the GUI settings
- **GUI Issues**: Check Python version and tkinter installation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- Developed with the help of ChatGPT
- Thanks to all contributors and users

## 📬 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Check existing issues for solutions

---

*This project is actively maintained and regularly updated.*
