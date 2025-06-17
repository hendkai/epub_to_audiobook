from typing import Dict, Any
import os
import json

class I18n:
    """Internationalization utility class"""
    
    def __init__(self, default_language: str = "en"):
        self.current_language = default_language
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation dictionaries"""
        return {
            'de': {
                # Main UI
                'title': 'EPUB zu Audiobook Konverter',
                'subtitle': 'Konvertiere EPUB-Bücher zu Audiobüchern mit verschiedenen TTS-Anbietern',
                
                # File selection
                'select_book_file': 'Buchddatei auswählen',
                'select_epub_file': 'EPUB-Datei auswählen',
                'output_directory': 'Ausgabeordner',
                'default_output_note': 'Standard sollte in Ordnung sein.',
                
                # Source selection
                'source_type': 'Quellentyp',
                'local_file': 'Lokale Datei',
                'gutenberg_project': 'Project Gutenberg',
                'gutenberg_id_url': 'Gutenberg ID oder URL',
                'load_from_gutenberg': 'Von Gutenberg laden',
        'select_from_results': 'Ausgewähltes Buch laden',
        'no_book_selected': 'Kein Buch ausgewählt. Suchen Sie zuerst nach Büchern und klicken Sie dann auf "Ausgewähltes Buch laden".',
                'search_gutenberg': 'Project Gutenberg durchsuchen',
                
                # TTS Settings
                'tts_provider': 'TTS-Anbieter',
                'language': 'Sprache',
                'voice': 'Stimme',
                'model': 'Modell',
                'speed': 'Geschwindigkeit',
                'output_format': 'Ausgabeformat',
                
                # Processing options
                'log_level': 'Log-Level',
                'worker_count': 'Anzahl Arbeiter',
                'worker_info': 'Anzahl der Arbeiter für die Verarbeitung. Mehr Arbeiter können den Prozess beschleunigen, verwenden aber mehr Ressourcen.',
                'enable_output_text': 'Text-Ausgabe aktivieren',
                'output_text_info': 'Exportiert eine Textdatei für jedes Kapitel.',
                'enable_preview_mode': 'Vorschau-Modus aktivieren',
                'preview_mode_info': 'Es wird nicht zu Audio konvertiert, nur Kapitel vorbereitet und Kosten berechnet.',
                
                # Advanced options
                'advanced_options': 'Erweiterte Optionen',
                'search_replace_file': 'Suchen & Ersetzen Datei (optional)',
                'title_mode': 'Titel-Modus',
                'title_mode_info': 'Wählen Sie den Parse-Modus für Kapiteltitel.',
                'newline_mode': 'Zeilenumbruch-Modus',
                'newline_mode_info': 'Wählen Sie den Modus zur Erkennung neuer Absätze',
                'chapter_start': 'Kapitel Start',
                'chapter_start_info': 'Kapitel-Startindex auswählen (Standard: 1)',
                'chapter_end': 'Kapitel Ende',
                'chapter_end_info': 'Kapitel-Endindex (Standard: -1, bedeutet letztes Kapitel)',
                'remove_endnotes': 'Endnoten entfernen',
                'remove_endnotes_info': 'Entfernt Endnoten aus dem Text',
                'remove_reference_numbers': 'Referenznummern entfernen',
                'remove_reference_numbers_info': 'Entfernt Referenznummern aus dem Text',
                
                # Output options
                'output_options': 'Ausgabe-Optionen',
                'one_file_output': 'Eine Datei-Ausgabe',
                'one_file_info': 'Alle Kapitel in einer einzigen MP3-Datei kombinieren',
                
                # Gutenberg search
                'search': 'Suchen',
                'search_placeholder': 'Suchbegriff eingeben...',
                'author': 'Autor',
                'results': 'Ergebnisse',
                'book_preview': 'Buchvorschau',
                'load_book': 'Buch laden',
                'loading': 'Lade...',
                'loading_catalog': 'Lade Katalog...',
                'no_results': 'Keine Ergebnisse gefunden',
                'catalog_error': 'Fehler beim Laden des Katalogs',
                'gutenberg_success': 'Text von Project Gutenberg erfolgreich geladen',
                'gutenberg_error': 'Fehler beim Laden von Project Gutenberg',
                'preview_text': 'Text Preview',
                'show_preview': 'Show Preview',
                'hide_preview': 'Hide Preview',
                'show_full_text': 'Show Full Text',
                'full_text_preview': 'Full Text Preview',
                'chapters': 'Chapters',
                'no_text_loaded': 'No text loaded',
                'show_full_text': 'Volltext anzeigen',
                'full_text_preview': 'Volltext-Vorschau',
                'chapters': 'Kapitel',
                'no_text_loaded': 'Kein Text geladen',
                
                # Cost estimation
                'cost_estimation': 'Kostenschätzung',
                'estimated_costs': 'Geschätzte Kosten',
                'text_length': 'Textlänge',
                'characters': 'Zeichen',
                'free_service': 'KOSTENLOS',
                'cost_usd': 'Kosten (USD)',
                'cost_eur': 'Kosten (EUR)',
                'cheapest_option': 'Günstigste Option',
                
                # Actions
                'start_conversion': 'Konvertierung starten',
                'cancel_conversion': 'Konvertierung abbrechen',
                'conversion_running': 'Konvertierung läuft',
                'conversion_completed': 'Konvertierung abgeschlossen',
                'conversion_failed': 'Konvertierung fehlgeschlagen',
                
                # Messages
                'success': 'Erfolg',
                'error': 'Fehler',
                'warning': 'Warnung',
                'info': 'Information',
                'file_not_found': 'Datei nicht gefunden',
                'invalid_file': 'Ungültige Datei',
                'api_key_required': 'API-Schlüssel erforderlich',
                'processing': 'Verarbeitung...',
                'please_wait': 'Bitte warten...',
                
                # Language names
                'german': 'Deutsch',
                'english': 'Englisch',
                'french': 'Französisch',
                'spanish': 'Spanisch',
                'italian': 'Italienisch',
                
                # Provider-specific
                'azure_config': 'Azure-Konfiguration',
                'azure_key_info': 'Es wird erwartet, dass der Benutzer MS_TTS_KEY und MS_TTS_REGION in den Umgebungsvariablen konfiguriert hat.',
                'openai_config': 'OpenAI-Konfiguration', 
                'openai_key_info': 'Es wird erwartet, dass der Benutzer OPENAI_API_KEY in den Umgebungsvariablen konfiguriert hat.',
                'edge_config': 'Edge TTS-Konfiguration',
                'edge_free_info': 'Edge TTS ist kostenlos und erfordert keine API-Schlüssel.',
                'piper_config': 'Piper TTS-Konfiguration',
                'piper_local_info': 'Piper TTS läuft lokal und ist kostenlos.',
                
                # Settings
                'voice_instructions': 'Stimmanweisungen',
                'voice_rate': 'Sprechgeschwindigkeit',
                'voice_volume': 'Lautstärke',
                'voice_pitch': 'Tonhöhe',
                'break_duration': 'Pausendauer',
                'break_duration_info': 'Pausendauer in Millisekunden',
                'proxy': 'Proxy',
                'proxy_info': 'Optional: Proxy-Server für Netzwerkanfragen',
                
                # Close/Exit
                'close': 'Schließen',
                'exit': 'Beenden',
                'cancel': 'Abbrechen',
                'ok': 'OK',
                'yes': 'Ja', 
                'no': 'Nein',
            },
            'en': {
                # Main UI
                'title': 'EPUB to Audiobook Converter',
                'subtitle': 'Convert EPUB books to audiobooks using various TTS providers',
                
                # File selection
                'select_book_file': 'Select the book file to process',
                'select_epub_file': 'Select EPUB file',
                'output_directory': 'Set Output Directory',
                'default_output_note': 'Default one should be fine.',
                
                # Source selection
                'source_type': 'Source Type',
                'local_file': 'Local File',
                'gutenberg_project': 'Project Gutenberg',
                'gutenberg_id_url': 'Gutenberg ID or URL',
                'load_from_gutenberg': 'Load from Gutenberg',
        'select_from_results': 'Load Selected Book',
        'no_book_selected': 'No book selected. Search for books first, then click "Load Selected Book".',
                'search_gutenberg': 'Search Project Gutenberg',
                
                # TTS Settings
                'tts_provider': 'TTS Provider',
                'language': 'Language',
                'voice': 'Voice',
                'model': 'Model',
                'speed': 'Speed',
                'output_format': 'Output Format',
                
                # Processing options
                'log_level': 'Log Level',
                'worker_count': 'Worker Count',
                'worker_info': 'Number of workers to use for processing. More workers may speed up the process but will use more resources.',
                'enable_output_text': 'Enable Output Text',
                'output_text_info': 'Export a plain text file for each chapter.',
                'enable_preview_mode': 'Enable Preview Mode',
                'preview_mode_info': 'It will not convert to audio, only prepare chapters and calculate costs.',
                
                # Advanced options
                'advanced_options': 'Advanced Options',
                'search_replace_file': 'Select search and replace file (optional)',
                'title_mode': 'Title Mode',
                'title_mode_info': 'Choose the parse mode for chapter title.',
                'newline_mode': 'New Line Mode',
                'newline_mode_info': 'Choose the mode of detecting new paragraphs',
                'chapter_start': 'Chapter Start',
                'chapter_start_info': 'Select chapter start index (default: 1)',
                'chapter_end': 'Chapter End',
                'chapter_end_info': 'Chapter end index (default: -1, means last chapter)',
                'remove_endnotes': 'Remove Endnotes',
                'remove_endnotes_info': 'Remove endnotes from text',
                'remove_reference_numbers': 'Remove Reference Numbers',
                'remove_reference_numbers_info': 'Remove reference numbers from text',
                
                # Output options
                'output_options': 'Output Options',
                'one_file_output': 'One File Output',
                'one_file_info': 'Combine all chapters into a single MP3 file',
                
                # Gutenberg search
                'search': 'Search',
                'search_placeholder': 'Enter search term...',
                'author': 'Author',
                'results': 'Results',
                'book_preview': 'Book Preview',
                'load_book': 'Load Book',
                'loading': 'Loading...',
                'loading_catalog': 'Loading catalog...',
                'no_results': 'No results found',
                'catalog_error': 'Error loading catalog',
                'gutenberg_success': 'Text successfully loaded from Project Gutenberg',
                'gutenberg_error': 'Error loading from Project Gutenberg',
                'preview_text': 'Text Preview',
                'show_preview': 'Show Preview',
                'hide_preview': 'Hide Preview',
                'show_full_text': 'Show Full Text',
                'full_text_preview': 'Full Text Preview',
                'chapters': 'Chapters',
                'no_text_loaded': 'No text loaded',
                
                # Cost estimation
                'cost_estimation': 'Cost Estimation',
                'estimated_costs': 'Estimated Costs',
                'text_length': 'Text Length',
                'characters': 'Characters',
                'free_service': 'FREE',
                'cost_usd': 'Cost (USD)',
                'cost_eur': 'Cost (EUR)',
                'cheapest_option': 'Cheapest Option',
                
                # Actions
                'start_conversion': 'Start Conversion',
                'cancel_conversion': 'Cancel Conversion',
                'conversion_running': 'Conversion Running',
                'conversion_completed': 'Conversion Completed',
                'conversion_failed': 'Conversion Failed',
                
                # Messages
                'success': 'Success',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Information',
                'file_not_found': 'File not found',
                'invalid_file': 'Invalid file',
                'api_key_required': 'API key required',
                'processing': 'Processing...',
                'please_wait': 'Please wait...',
                
                # Language names
                'german': 'German',
                'english': 'English',
                'french': 'French',
                'spanish': 'Spanish',
                'italian': 'Italian',
                
                # Provider-specific
                'azure_config': 'Azure Configuration',
                'azure_key_info': 'It is expected that user configured: MS_TTS_KEY and MS_TTS_REGION in the environment variables.',
                'openai_config': 'OpenAI Configuration',
                'openai_key_info': 'It is expected that user configured: OPENAI_API_KEY in the environment variables.',
                'edge_config': 'Edge TTS Configuration',
                'edge_free_info': 'Edge TTS is free and requires no API keys.',
                'piper_config': 'Piper TTS Configuration',
                'piper_local_info': 'Piper TTS runs locally and is free.',
                
                # Settings
                'voice_instructions': 'Voice Instructions',
                'voice_rate': 'Voice Rate',
                'voice_volume': 'Voice Volume',
                'voice_pitch': 'Voice Pitch',
                'break_duration': 'Break Duration',
                'break_duration_info': 'Break duration in milliseconds',
                'proxy': 'Proxy',
                'proxy_info': 'Optional: Proxy server for network requests',
                
                # Close/Exit
                'close': 'Close',
                'exit': 'Exit',
                'cancel': 'Cancel',
                'ok': 'OK',
                'yes': 'Yes',
                'no': 'No',
            }
        }
    
    def set_language(self, language: str):
        """Set the current language"""
        if language in self.translations:
            self.current_language = language
    
    def t(self, key: str, **kwargs) -> str:
        """Translate a key to the current language"""
        translation = self.translations.get(self.current_language, {}).get(key, key)
        
        # Simple string formatting
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError:
                pass  # Ignore formatting errors
        
        return translation
    
    def get_language(self) -> str:
        """Get current language"""
        return self.current_language
    
    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.translations.keys())
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Get display name for language"""
        display_names = {
            'de': 'Deutsch',
            'en': 'English'
        }
        return display_names.get(lang_code, lang_code.upper())

# Global instance
i18n = I18n() 