from multiprocessing import Process
from typing import Optional, Tuple, List, Dict
import os
import tempfile
from datetime import datetime
import threading
import time

import gradio as gr
from gradio_log import Log

from audiobook_generator.config.general_config import GeneralConfig
from audiobook_generator.tts_providers.azure_tts_provider import get_azure_supported_languages, \
    get_azure_supported_voices, get_azure_supported_output_formats
from audiobook_generator.tts_providers.edge_tts_provider import get_edge_tts_supported_voices, \
    get_edge_tts_supported_language, get_edge_tts_supported_output_formats
from audiobook_generator.tts_providers.openai_tts_provider import get_openai_supported_models, \
    get_openai_supported_voices, get_openai_instructions_example, get_openai_supported_output_formats
from audiobook_generator.tts_providers.piper_tts_provider import get_piper_supported_languages, \
    get_piper_supported_voices, get_piper_supported_qualities, get_piper_supported_speakers
from audiobook_generator.utils.log_handler import generate_unique_log_path
from audiobook_generator.utils.gutenberg_utils import GutenbergUtils
from audiobook_generator.utils.cost_calculator import CostCalculator
from audiobook_generator.utils.i18n import i18n
from main import main

# Global variables
selected_tts = "Edge"
running_process: Optional[Process] = None
webui_log_file = None
gutenberg_utils = GutenbergUtils()
cost_calculator = CostCalculator()
current_language = "en"
current_epub_file = None
current_text_preview = ""

def set_language(language: str):
    """Set the UI language"""
    global current_language
    current_language = language
    i18n.set_language(language)
    return language

def on_tab_change(evt: gr.SelectData):
    global selected_tts
    selected_tts = evt.value

def get_azure_voices_by_language(language):
    voices_list = [voice for voice in get_azure_supported_voices() if voice.startswith(language)]
    return gr.Dropdown(voices_list, value=voices_list[0] if voices_list else "", 
                      label=i18n.t("voice"), interactive=True, 
                      info=i18n.t("select_voice"))

def get_edge_voices_by_language(language):
    voices_list = [voice for voice in get_edge_tts_supported_voices() if voice.startswith(language)]
    return gr.Dropdown(voices_list, value=voices_list[0] if voices_list else "", 
                      label=i18n.t("voice"), interactive=True, 
                      info=i18n.t("select_voice"))

def get_piper_supported_voices_gui(language):
    voices_list = get_piper_supported_voices(language)
    return gr.Dropdown(voices_list, value=voices_list[0] if voices_list else "", 
                      label=i18n.t("voice"), interactive=True, 
                      info=i18n.t("select_voice"))

def get_piper_supported_qualities_gui(language, voice):
    qualities_list = get_piper_supported_qualities(language, voice)
    return gr.Dropdown(qualities_list, value=qualities_list[0] if qualities_list else "", 
                      label="Quality", interactive=True, info="Select the quality")

def get_piper_supported_speakers_gui(language, voice, quality):
    speakers_list = get_piper_supported_speakers(language, voice, quality)
    return gr.Dropdown(speakers_list, value=speakers_list[0] if speakers_list else "", 
                      label="Speaker", interactive=True, info="Select the speaker")

def search_gutenberg_books(search_term: str, language_filter: str = "all") -> Tuple[List[List], str]:
    """Search Project Gutenberg books"""
    try:
        if not search_term or len(search_term.strip()) < 2:
            return [], i18n.t("search_placeholder")
        
        books = gutenberg_utils.search_books(search_term, language_filter, max_results=50)
        
        if not books:
            return [], i18n.t("no_results")
        
        # Format for display in table
        table_data = []
        for book in books:
            table_data.append([
                book.get("Text#", ""),
                book.get("Title", "")[:80] + ("..." if len(book.get("Title", "")) > 80 else ""),
                book.get("Authors", "")[:50] + ("..." if len(book.get("Authors", "")) > 50 else ""),
                book.get("Language", "")
            ])
        
        status_msg = f"{len(books)} {i18n.t('results')}"
        return table_data, status_msg
        
    except Exception as e:
        return [], f"{i18n.t('catalog_error')}: {str(e)}"

def load_gutenberg_book(book_id: str) -> Tuple[str, str, str]:
    """Load a book from Project Gutenberg"""
    try:
        if not book_id:
            return "", "", i18n.t("gutenberg_error")
        
        # Extract ID if it's a URL
        actual_id = gutenberg_utils.extract_gutenberg_id(book_id)
        if not actual_id:
            return "", "", i18n.t("gutenberg_error")
        
        # Get book text
        text = gutenberg_utils.get_book_text(actual_id)
        if not text:
            return "", "", i18n.t("gutenberg_error")
        
        # Create EPUB
        epub_path = gutenberg_utils.create_epub_from_text(
            text, f"Gutenberg Book {actual_id}", "Project Gutenberg", "en", actual_id
        )
        
        if not epub_path:
            return "", "", i18n.t("gutenberg_error")
        
        # Get preview
        preview = gutenberg_utils.get_book_preview(actual_id, max_chars=1500)
        
        global current_epub_file, current_text_preview
        current_epub_file = epub_path
        current_text_preview = preview
        
        return epub_path, preview, i18n.t("gutenberg_success")
        
    except Exception as e:
        return "", "", f"{i18n.t('gutenberg_error')}: {str(e)}"

def estimate_conversion_costs(file_path: str = None, text: str = None) -> str:
    """Estimate TTS conversion costs"""
    try:
        if not file_path and not text:
            return i18n.t("no_text_loaded")
        
        # Calculate text length
        if text:
            text_length = len(text)
        else:
            # For EPUB files, we'd need to extract text first
            # This is a simplified approach
            text_length = 50000  # Estimate
        
        # Get cost comparison
        comparison = cost_calculator.get_cost_comparison(text_length)
        
        # Format results
        result_lines = [f"**{i18n.t('cost_estimation')}**\n"]
        result_lines.append(f"{i18n.t('text_length')}: {text_length:,} {i18n.t('characters')}\n")
        
        for provider_key, cost_info in comparison.items():
            formatted_cost = cost_calculator.format_cost_info(cost_info)
            result_lines.append(formatted_cost)
        
        # Add cheapest option
        cheapest_key, cheapest_info = cost_calculator.get_cheapest_option(text_length)
        result_lines.append(f"\n**{i18n.t('cheapest_option')}:** {cheapest_key}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"{i18n.t('error')}: {str(e)}"

def show_text_preview(file_path: str = None) -> str:
    """Show text preview"""
    global current_text_preview
    
    if current_text_preview:
        return current_text_preview
    
    if file_path and os.path.exists(file_path):
        try:
            # This would need proper EPUB parsing
            return "Preview will be available after implementing EPUB text extraction"
        except Exception as e:
            return f"{i18n.t('error')}: {str(e)}"
    
    return i18n.t("no_text_loaded")

def process_ui_form(
    # Source selection
    source_type, input_file, gutenberg_id, 
    # Output settings
    output_dir, one_file_output,
    # Processing settings
    worker_count, log_level, output_text, preview,
    # Advanced options
    search_and_replace_file, title_mode, new_line_mode, 
    chapter_start, chapter_end, remove_endnotes, remove_reference_numbers,
    # TTS provider settings
    model, voices, speed, openai_output_format, instructions,
    azure_language, azure_voice, azure_output_format, azure_break_duration,
    edge_language, edge_voice, edge_output_format, proxy, 
    edge_voice_rate, edge_volume, edge_pitch, edge_break_duration,
    piper_executable_path, piper_docker_image, piper_language, 
    piper_voice, piper_quality, piper_speaker,
    piper_noise_scale, piper_noise_w_scale, piper_length_scale, piper_sentence_silence
):
    """Process the UI form and start conversion"""
    
    config = GeneralConfig(None)
    
    # Handle source type
    if source_type == i18n.t("gutenberg_project"):
        if current_epub_file and os.path.exists(current_epub_file):
            config.input_file = current_epub_file
        else:
            return f"{i18n.t('error')}: {i18n.t('gutenberg_error')}"
    else:
        config.input_file = input_file.name if hasattr(input_file, 'name') else input_file
    
    config.output_folder = output_dir
    config.preview = preview
    config.output_text = output_text
    config.log = log_level
    config.worker_count = worker_count
    config.no_prompt = True
    
    # Advanced options
    config.title_mode = title_mode
    config.newline_mode = new_line_mode
    config.chapter_start = chapter_start
    config.chapter_end = chapter_end
    config.remove_endnotes = remove_endnotes
    config.remove_reference_numbers = remove_reference_numbers
    config.search_and_replace_file = search_and_replace_file.name if hasattr(search_and_replace_file, 'name') else search_and_replace_file
    
    # One file output (your feature!)
    if hasattr(config, 'one_file_output'):
        config.one_file_output = one_file_output
    
    # TTS provider configuration
    global selected_tts
    if selected_tts == "OpenAI":
        config.tts = "openai"
        config.output_format = openai_output_format
        config.voice_name = voices
        config.model_name = model
        config.instructions = instructions
        config.speed = speed
    elif selected_tts == "Azure":
        config.tts = "azure"
        config.language = azure_language
        config.voice_name = azure_voice
        config.output_format = azure_output_format
        config.break_duration = azure_break_duration
    elif selected_tts == "Edge":
        config.tts = "edge"
        config.language = edge_language
        config.voice_name = edge_voice
        config.output_format = edge_output_format
        config.proxy = proxy
        config.voice_rate = edge_voice_rate
        config.voice_volume = edge_volume
        config.voice_pitch = edge_pitch
        config.break_duration = edge_break_duration
    elif selected_tts == "Piper":
        config.tts = "piper"
        config.piper_path = piper_executable_path
        config.piper_docker_image = piper_docker_image
        config.model_name = f"{piper_language}-{piper_voice}-{piper_quality}"
        config.piper_speaker = piper_speaker
        config.piper_noise_scale = piper_noise_scale
        config.piper_noise_w_scale = piper_noise_w_scale
        config.piper_length_scale = piper_length_scale
        config.piper_sentence_silence = piper_sentence_silence
    else:
        raise ValueError("Unsupported TTS provider selected")

    launch_audiobook_generator(config)

def launch_audiobook_generator(config):
    """Launch the audiobook generator"""
    global running_process
    if running_process and running_process.is_alive():
        print("Audiobook generator already running")
        return

    running_process = Process(target=main, args=(config, str(webui_log_file.absolute())))
    running_process.start()

def terminate_audiobook_generator():
    """Terminate the running process"""
    global running_process
    if running_process and running_process.is_alive():
        running_process.terminate()
        running_process = None
        print("Audiobook generator terminated manually")

def create_enhanced_ui(config):
    """Create the enhanced UI with all features"""
    default_output_dir = os.path.join("audiobook_output", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    
    with gr.Blocks(analytics_enabled=False, 
                   title=i18n.t("title"),
                   css="""
                   .gutenberg-section { border: 2px solid #e1e5e9; border-radius: 8px; padding: 15px; margin: 10px 0; }
                   .cost-display { background-color: #f8f9fa; padding: 15px; border-radius: 8px; }
                   .preview-text { max-height: 300px; overflow-y: auto; }
                   """) as ui:
        
        # Title and language selector
        with gr.Row():
            gr.Markdown(f"# {i18n.t('title')}")
            with gr.Column(scale=1):
                language_dropdown = gr.Dropdown(
                    choices=[("Deutsch", "de"), ("English", "en")],
                    value=current_language,
                    label="Language / Sprache",
                    interactive=True
                )
        
        # Source selection
        with gr.Row():
            source_type = gr.Radio(
                choices=[i18n.t("local_file"), i18n.t("gutenberg_project")],
                value=i18n.t("local_file"),
                label=i18n.t("source_type"),
                interactive=True
            )
        
        # File input (for local files)
        with gr.Row(visible=True) as local_file_row:
            input_file = gr.File(
                label=i18n.t("select_book_file"), 
                file_types=[".epub"], 
                file_count="single", 
                interactive=True
            )
        
        # Gutenberg section
        with gr.Group(visible=False, elem_classes=["gutenberg-section"]) as gutenberg_section:
            gr.Markdown(f"## {i18n.t('gutenberg_project')}")
            
            with gr.Row():
                gutenberg_id = gr.Textbox(
                    label=i18n.t("gutenberg_id_url"),
                    placeholder="1234 oder https://www.gutenberg.org/ebooks/1234",
                    interactive=True
                )
                load_gutenberg_btn = gr.Button(i18n.t("load_from_gutenberg"), variant="secondary")
            
            # Gutenberg search
            with gr.Row():
                search_term = gr.Textbox(
                    label=i18n.t("search"),
                    placeholder=i18n.t("search_placeholder"),
                    interactive=True
                )
                search_language = gr.Dropdown(
                    choices=["all", "en", "de", "fr", "es", "it"],
                    value="all",
                    label=i18n.t("language"),
                    interactive=True
                )
                search_btn = gr.Button(i18n.t("search"), variant="secondary")
            
            # Search results
            with gr.Row():
                search_results = gr.Dataframe(
                    headers=["ID", i18n.t("title"), i18n.t("author"), i18n.t("language")],
                    label=i18n.t("results"),
                    interactive=True,
                    max_height=200
                )
            
            search_status = gr.Textbox(label="Status", interactive=False)
        
        # Output settings
        with gr.Row():
            with gr.Column():
                output_dir = gr.Textbox(
                    label=i18n.t("output_directory"), 
                    value=default_output_dir, 
                    interactive=True, 
                    info=i18n.t("default_output_note")
                )
            with gr.Column():
                one_file_output = gr.Checkbox(
                    label=i18n.t("one_file_output"),
                    value=False,
                    info=i18n.t("one_file_info")
                )
        
        # Preview and cost estimation section
        with gr.Row():
            with gr.Column():
                preview_btn = gr.Button(i18n.t("show_preview"), variant="secondary")
                text_preview = gr.Textbox(
                    label=i18n.t("preview_text"),
                    lines=8,
                    max_lines=12,
                    interactive=False,
                    elem_classes=["preview-text"]
                )
            
            with gr.Column():
                cost_btn = gr.Button(i18n.t("cost_estimation"), variant="secondary")
                cost_display = gr.Markdown(
                    value="",
                    elem_classes=["cost-display"]
                )
        
        # Processing options
        with gr.Row():
            with gr.Column():
                log_level = gr.Dropdown(
                    ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"], 
                    label=i18n.t("log_level"), 
                    value="INFO", 
                    interactive=True
                )
                worker_count = gr.Slider(
                    minimum=1, maximum=8, step=1, 
                    label=i18n.t("worker_count"), 
                    value=1,
                    info=i18n.t("worker_info")
                )
            
            with gr.Column():
                output_text = gr.Checkbox(
                    label=i18n.t("enable_output_text"), 
                    value=False,
                    info=i18n.t("output_text_info")
                )
                preview = gr.Checkbox(
                    label=i18n.t("enable_preview_mode"), 
                    value=False,
                    info=i18n.t("preview_mode_info")
                )
        
        # Advanced options
        gr.Markdown("---")
        with gr.Accordion(i18n.t("advanced_options"), open=False):
            with gr.Row():
                search_and_replace_file = gr.File(
                    label=i18n.t("search_replace_file"), 
                    file_types=[".txt"], 
                    file_count="single", 
                    interactive=True
                )
                title_mode = gr.Dropdown(
                    ["auto", "tag_text", "first_few"], 
                    label=i18n.t("title_mode"), 
                    value="auto",
                    interactive=True, 
                    info=i18n.t("title_mode_info")
                )
                new_line_mode = gr.Dropdown(
                    ["single", "double", "none"], 
                    label=i18n.t("newline_mode"), 
                    value="double",
                    interactive=True, 
                    info=i18n.t("newline_mode_info")
                )
            
            with gr.Row():
                chapter_start = gr.Slider(
                    minimum=1, maximum=100, step=1, 
                    label=i18n.t("chapter_start"), 
                    value=1,
                    interactive=True, 
                    info=i18n.t("chapter_start_info")
                )
                chapter_end = gr.Slider(
                    minimum=-1, maximum=100, step=1, 
                    label=i18n.t("chapter_end"), 
                    value=-1,
                    interactive=True, 
                    info=i18n.t("chapter_end_info")
                )
                
            with gr.Row():
                remove_endnotes = gr.Checkbox(
                    label=i18n.t("remove_endnotes"), 
                    value=False, 
                    info=i18n.t("remove_endnotes_info")
                )
                remove_reference_numbers = gr.Checkbox(
                    label=i18n.t("remove_reference_numbers"), 
                    value=False,
                    info=i18n.t("remove_reference_numbers_info")
                )
        
        # TTS provider tabs (keeping the existing structure but with translations)
        gr.Markdown("---")
        with gr.Tabs(selected="edge_tab_id"):
            with gr.Tab("OpenAI", id="openai_tab_id") as open_ai_tab:
                gr.Markdown(i18n.t("openai_key_info"))
                with gr.Row(equal_height=True):
                    model = gr.Dropdown(get_openai_supported_models(), label=i18n.t("model"), interactive=True, allow_custom_value=True)
                    voices = gr.Dropdown(get_openai_supported_voices(), label=i18n.t("voice"), interactive=True, allow_custom_value=True)
                    speed = gr.Slider(minimum=0.25, maximum=4.0, step=0.1, label=i18n.t("speed"), value=1.0)
                    openai_output_format = gr.Dropdown(get_openai_supported_output_formats(), label=i18n.t("output_format"), interactive=True)
                with gr.Row(equal_height=True):
                    instructions = gr.TextArea(label=i18n.t("voice_instructions"), interactive=True, lines=3,
                                             value=get_openai_instructions_example())
                open_ai_tab.select(on_tab_change, inputs=None, outputs=None)
            
            with gr.Tab("Azure", id="azure_tab_id") as azure_tab:
                gr.Markdown(i18n.t("azure_key_info"))
                with gr.Row(equal_height=True):
                    azure_language = gr.Dropdown(get_azure_supported_languages(), value="en-US", label=i18n.t("language"),
                                               interactive=True)
                    azure_voice = get_azure_voices_by_language(azure_language.value)
                    azure_output_format = gr.Dropdown(get_azure_supported_output_formats(), label=i18n.t("output_format"), interactive=True,
                                                value="audio-24khz-48kbitrate-mono-mp3")
                    azure_break_duration = gr.Slider(minimum=0, maximum=5000, step=1, label=i18n.t("break_duration"), value=1250,
                                               info=i18n.t("break_duration_info"))
                    azure_language.change(get_azure_voices_by_language, inputs=azure_language, outputs=azure_voice)
                azure_tab.select(on_tab_change, inputs=None, outputs=None)
            
            with gr.Tab("Edge", id="edge_tab_id") as edge_tab:
                gr.Markdown(i18n.t("edge_free_info"))
                with gr.Row(equal_height=True):
                    edge_language = gr.Dropdown(get_edge_tts_supported_language(), value="en-US", label=i18n.t("language"), interactive=True)
                    edge_voice = get_edge_voices_by_language(edge_language.value)
                    edge_output_format = gr.Dropdown(get_edge_tts_supported_output_formats(), label=i18n.t("output_format"), interactive=True, value="mp3")
                    proxy = gr.Textbox(label=i18n.t("proxy"), interactive=True, info=i18n.t("proxy_info"))
                with gr.Row(equal_height=True):
                    edge_voice_rate = gr.Textbox(label=i18n.t("voice_rate"), value="+0%", interactive=True)
                    edge_volume = gr.Textbox(label=i18n.t("voice_volume"), value="+0%", interactive=True)
                    edge_pitch = gr.Textbox(label=i18n.t("voice_pitch"), value="+0Hz", interactive=True)
                    edge_break_duration = gr.Slider(minimum=0, maximum=5000, step=1, label=i18n.t("break_duration"), value=1250,
                                                  info=i18n.t("break_duration_info"))
                    edge_language.change(get_edge_voices_by_language, inputs=edge_language, outputs=edge_voice)
                edge_tab.select(on_tab_change, inputs=None, outputs=None)
            
            with gr.Tab("Piper", id="piper_tab_id") as piper_tab:
                gr.Markdown(i18n.t("piper_local_info"))
                with gr.Row(equal_height=True):
                    piper_executable_path = gr.Textbox(label="Piper Path", value="piper", interactive=True)
                    piper_docker_image = gr.Textbox(label="Docker Image", value="", interactive=True)
                    piper_language = gr.Dropdown(get_piper_supported_languages(), label=i18n.t("language"), interactive=True, value="en_US")
                    piper_voice = get_piper_supported_voices_gui(piper_language.value)
                with gr.Row(equal_height=True):
                    piper_quality = get_piper_supported_qualities_gui(piper_language.value, "amy")
                    piper_speaker = get_piper_supported_speakers_gui(piper_language.value, "amy", "low")
                    piper_noise_scale = gr.Slider(minimum=0.1, maximum=1.0, step=0.1, label="Noise Scale", value=0.667, interactive=True)
                    piper_noise_w_scale = gr.Slider(minimum=0.1, maximum=1.0, step=0.1, label="Noise W Scale", value=0.8, interactive=True)
                with gr.Row(equal_height=True):
                    piper_length_scale = gr.Slider(minimum=0.1, maximum=2.0, step=0.1, label="Length Scale", value=1.0, interactive=True)
                    piper_sentence_silence = gr.Slider(minimum=0.0, maximum=5.0, step=0.1, label="Sentence Silence", value=0.2, interactive=True)
                    
                piper_language.change(get_piper_supported_voices_gui, inputs=piper_language, outputs=piper_voice)
                piper_voice.change(get_piper_supported_qualities_gui, inputs=[piper_language, piper_voice], outputs=piper_quality)
                piper_quality.change(get_piper_supported_speakers_gui, inputs=[piper_language, piper_voice, piper_quality], outputs=piper_speaker)
                piper_tab.select(on_tab_change, inputs=None, outputs=None)
        
        # Action buttons
        with gr.Row():
            start_btn = gr.Button(i18n.t("start_conversion"), variant="primary", size="lg")
            cancel_btn = gr.Button(i18n.t("cancel_conversion"), variant="secondary", size="lg")
        
        # Log display
        with gr.Row():
            log_display = Log(label="Conversion Logs", lines=15)
        
        # Event handlers
        def update_source_visibility(source):
            if source == i18n.t("gutenberg_project"):
                return gr.update(visible=False), gr.update(visible=True)
            else:
                return gr.update(visible=True), gr.update(visible=False)
        
        source_type.change(
            update_source_visibility,
            inputs=[source_type],
            outputs=[local_file_row, gutenberg_section]
        )
        
        # Gutenberg events
        search_btn.click(
            search_gutenberg_books,
            inputs=[search_term, search_language],
            outputs=[search_results, search_status]
        )
        
        load_gutenberg_btn.click(
            load_gutenberg_book,
            inputs=[gutenberg_id],
            outputs=[input_file, text_preview, search_status]
        )
        
        # Preview and cost estimation
        preview_btn.click(
            show_text_preview,
            inputs=[input_file],
            outputs=[text_preview]
        )
        
        cost_btn.click(
            estimate_conversion_costs,
            inputs=[input_file, text_preview],
            outputs=[cost_display]
        )
        
        # Language change
        def update_ui_language(lang):
            set_language(lang)
            # Note: In a real implementation, you'd need to refresh the entire UI
            # This is a simplified version
            return gr.update()
        
        language_dropdown.change(
            update_ui_language,
            inputs=[language_dropdown],
            outputs=[]
        )
        
        # Start conversion
        start_btn.click(
            process_ui_form,
            inputs=[
                source_type, input_file, gutenberg_id,
                output_dir, one_file_output,
                worker_count, log_level, output_text, preview,
                search_and_replace_file, title_mode, new_line_mode,
                chapter_start, chapter_end, remove_endnotes, remove_reference_numbers,
                model, voices, speed, openai_output_format, instructions,
                azure_language, azure_voice, azure_output_format, azure_break_duration,
                edge_language, edge_voice, edge_output_format, proxy,
                edge_voice_rate, edge_volume, edge_pitch, edge_break_duration,
                piper_executable_path, piper_docker_image, piper_language,
                piper_voice, piper_quality, piper_speaker,
                piper_noise_scale, piper_noise_w_scale, piper_length_scale, piper_sentence_silence
            ]
        )
        
        cancel_btn.click(terminate_audiobook_generator)
    
    return ui

def host_enhanced_ui(config):
    """Host the enhanced UI with all features"""
    global webui_log_file
    webui_log_file = generate_unique_log_path()
    
    ui = create_enhanced_ui(config)
    
    # Launch with custom settings
    ui.launch(
        server_name=getattr(config, 'host', '127.0.0.1'),
        server_port=getattr(config, 'port', 7860),
        share=False,
        debug=False,
        show_error=True
    ) 