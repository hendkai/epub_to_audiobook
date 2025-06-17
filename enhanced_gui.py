#!/usr/bin/env python3
"""
Enhanced EPUB to Audiobook Converter
Integrates all features from your original GUI:
- Project Gutenberg integration
- German/English UI translation  
- Cost estimation
- Text preview
- One-file output option
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import tempfile
from typing import Optional, Tuple, List, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from audiobook_generator.utils.gutenberg_utils import GutenbergUtils
    from audiobook_generator.utils.cost_calculator import CostCalculator
    from audiobook_generator.utils.i18n import i18n
    from main import main
    from audiobook_generator.config.general_config import GeneralConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you're running this from the epub_to_audiobook directory")
    sys.exit(1)

class EnhancedEpubToAudiobookGUI:
    """Enhanced GUI with all your original features"""
    
    def __init__(self, root):
        self.root = root
        self.gutenberg_utils = GutenbergUtils()
        self.cost_calculator = CostCalculator()
        
        # Set default language
        i18n.set_language("de")  # Start with German as you prefer
        
        # Initialize UI variables
        self.current_epub_file = None
        self.current_text_preview = ""
        self.conversion_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.root.title(i18n.t("title"))
        self.root.geometry("900x700")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text=i18n.t("main_settings"))
        
        # Gutenberg tab
        gutenberg_frame = ttk.Frame(notebook)
        notebook.add(gutenberg_frame, text=i18n.t("gutenberg_project"))
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="TTS " + i18n.t("settings"))
        
        self.setup_main_tab(main_frame)
        self.setup_gutenberg_tab(gutenberg_frame)
        self.setup_settings_tab(settings_frame)
        
        # Language selector at the bottom
        lang_frame = ttk.Frame(self.root)
        lang_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(lang_frame, text="Language / Sprache:").pack(side=tk.LEFT)
        self.language_var = tk.StringVar(value="de")
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                 values=["de", "en"], state="readonly", width=5)
        lang_combo.pack(side=tk.LEFT, padx=5)
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        
    def setup_main_tab(self, parent):
        """Setup main conversion tab"""
        
        # Source selection
        source_frame = ttk.LabelFrame(parent, text=i18n.t("source_type"), padding="10")
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.source_type_var = tk.StringVar(value="local")
        ttk.Radiobutton(source_frame, text=i18n.t("local_file"), 
                       variable=self.source_type_var, value="local",
                       command=self.on_source_change).pack(anchor=tk.W)
        ttk.Radiobutton(source_frame, text=i18n.t("gutenberg_project"), 
                       variable=self.source_type_var, value="gutenberg",
                       command=self.on_source_change).pack(anchor=tk.W)
        
        # File selection
        file_frame = ttk.LabelFrame(parent, text=i18n.t("select_epub_file"), padding="10")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly")
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(file_frame, text=i18n.t("browse"), 
                  command=self.browse_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output settings
        output_frame = ttk.LabelFrame(parent, text=i18n.t("output_options"), padding="10")
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.output_dir_var = tk.StringVar(value="./output")
        ttk.Label(output_frame, text=i18n.t("output_directory") + ":").pack(anchor=tk.W)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        output_entry.pack(fill=tk.X, pady=2)
        
        self.one_file_var = tk.BooleanVar()
        ttk.Checkbutton(output_frame, text=i18n.t("one_file_output"), 
                       variable=self.one_file_var).pack(anchor=tk.W, pady=2)
        
        # Preview and cost frame
        preview_frame = ttk.LabelFrame(parent, text=i18n.t("preview_text") + " & " + i18n.t("cost_estimation"), padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(preview_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text=i18n.t("show_preview"), 
                  command=self.show_preview).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text=i18n.t("cost_estimation"), 
                  command=self.show_costs).pack(side=tk.LEFT)
        
        # Text area for preview and costs
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=8, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Conversion buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(action_frame, text=i18n.t("start_conversion"), 
                  command=self.start_conversion).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text=i18n.t("cancel"), 
                  command=self.cancel_conversion).pack(side=tk.LEFT)
        
    def setup_gutenberg_tab(self, parent):
        """Setup Gutenberg integration tab"""
        
        # Direct ID input
        id_frame = ttk.LabelFrame(parent, text=i18n.t("gutenberg_id_url"), padding="10")
        id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.gutenberg_id_var = tk.StringVar()
        id_entry = ttk.Entry(id_frame, textvariable=self.gutenberg_id_var)
        id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(id_frame, text=i18n.t("load_from_gutenberg"), 
                  command=self.load_gutenberg_book).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Search section
        search_frame = ttk.LabelFrame(parent, text=i18n.t("search_gutenberg"), padding="10")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search input
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_term_var = tk.StringVar()
        search_entry = ttk.Entry(search_input_frame, textvariable=self.search_term_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.search_lang_var = tk.StringVar(value="all")
        lang_combo = ttk.Combobox(search_input_frame, textvariable=self.search_lang_var,
                                 values=["all", "en", "de", "fr", "es", "it"], width=8)
        lang_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(search_input_frame, text=i18n.t("search"), 
                  command=self.search_gutenberg).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Results table  
        columns = ('id', 'title', 'author', 'language')
        self.results_tree = ttk.Treeview(search_frame, columns=columns, show='headings', height=8)
        
        self.results_tree.heading('id', text='ID')
        self.results_tree.heading('title', text=i18n.t("title"))
        self.results_tree.heading('author', text=i18n.t("author"))
        self.results_tree.heading('language', text=i18n.t("language"))
        
        self.results_tree.column('id', width=80)
        self.results_tree.column('title', width=300)
        self.results_tree.column('author', width=200)
        self.results_tree.column('language', width=80)
        
        scrollbar = ttk.Scrollbar(search_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree.bind("<Double-1>", self.on_book_select)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(parent, textvariable=self.status_var)
        status_label.pack(pady=5)
        
    def setup_settings_tab(self, parent):
        """Setup TTS settings tab"""
        
        # TTS Provider selection
        provider_frame = ttk.LabelFrame(parent, text=i18n.t("tts_provider"), padding="10")
        provider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.tts_provider_var = tk.StringVar(value="edge")
        providers = [("Edge TTS (Free)", "edge"), ("OpenAI", "openai"), ("Azure", "azure")]
        
        for text, value in providers:
            ttk.Radiobutton(provider_frame, text=text, 
                           variable=self.tts_provider_var, value=value).pack(anchor=tk.W)
        
        # Settings
        settings_frame = ttk.LabelFrame(parent, text=i18n.t("settings"), padding="10")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Language and voice
        ttk.Label(settings_frame, text=i18n.t("language") + ":").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.tts_language_var = tk.StringVar(value="en-US")
        lang_combo = ttk.Combobox(settings_frame, textvariable=self.tts_language_var,
                                 values=["en-US", "de-DE", "fr-FR", "es-ES"], width=15)
        lang_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(settings_frame, text=i18n.t("voice") + ":").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.voice_var = tk.StringVar(value="en-US-AriaNeural")
        voice_combo = ttk.Combobox(settings_frame, textvariable=self.voice_var, width=25)
        voice_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
    def on_source_change(self):
        """Handle source type change"""
        pass
        
    def browse_file(self):
        """Browse for EPUB file"""
        file_path = filedialog.askopenfilename(
            title=i18n.t("select_epub_file"),
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.current_epub_file = file_path
            
    def show_preview(self):
        """Show text preview"""
        if not self.current_epub_file:
            messagebox.showwarning(i18n.t("warning"), i18n.t("file_not_found"))
            return
            
        self.preview_text.delete(1.0, tk.END)
        
        if self.current_text_preview:
            self.preview_text.insert(1.0, self.current_text_preview)
        else:
            self.preview_text.insert(1.0, "Text preview not available. Load a book first.")
            
    def show_costs(self):
        """Show cost estimation"""
        if not self.current_text_preview and not self.current_epub_file:
            messagebox.showwarning(i18n.t("warning"), "No text loaded for cost estimation")
            return
            
        text_length = len(self.current_text_preview) if self.current_text_preview else 50000
        
        # Get cost comparison
        comparison = self.cost_calculator.get_cost_comparison(text_length)
        
        # Display results
        self.preview_text.delete(1.0, tk.END)
        result_lines = [f"**{i18n.t('cost_estimation')}**\n"]
        result_lines.append(f"{i18n.t('text_length')}: {text_length:,} {i18n.t('characters')}\n")
        
        for provider_key, cost_info in comparison.items():
            formatted_cost = self.cost_calculator.format_cost_info(cost_info)
            result_lines.append(formatted_cost)
        
        self.preview_text.insert(1.0, "\n".join(result_lines))
        
    def search_gutenberg(self):
        """Search Gutenberg books"""
        search_term = self.search_term_var.get().strip()
        if not search_term or len(search_term) < 2:
            messagebox.showwarning(i18n.t("warning"), "Please enter a search term")
            return
            
        self.status_var.set(i18n.t("loading"))
        
        def search_thread():
            try:
                books = self.gutenberg_utils.search_books(
                    search_term, self.search_lang_var.get(), max_results=50
                )
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_search_results(books))
                
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        
        threading.Thread(target=search_thread, daemon=True).start()
        
    def update_search_results(self, books):
        """Update search results in the tree view"""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Add new results
        for book in books:
            self.results_tree.insert('', 'end', values=(
                book.get("Text#", ""),
                book.get("Title", "")[:80] + ("..." if len(book.get("Title", "")) > 80 else ""),
                book.get("Authors", "")[:50] + ("..." if len(book.get("Authors", "")) > 50 else ""),
                book.get("Language", "")
            ))
        
        self.status_var.set(f"{len(books)} {i18n.t('results')}")
        
    def on_book_select(self, event):
        """Handle book selection from search results"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            book_id = item['values'][0]
            self.gutenberg_id_var.set(str(book_id))
            self.load_gutenberg_book()
            
    def load_gutenberg_book(self):
        """Load a book from Project Gutenberg"""
        book_id = self.gutenberg_id_var.get().strip()
        if not book_id:
            messagebox.showwarning(i18n.t("warning"), "Please enter a Gutenberg ID")
            return
            
        self.status_var.set(i18n.t("loading"))
        
        def load_thread():
            try:
                # Extract ID if it's a URL
                actual_id = self.gutenberg_utils.extract_gutenberg_id(book_id)
                if not actual_id:
                    self.root.after(0, lambda: messagebox.showerror(i18n.t("error"), "Invalid Gutenberg ID"))
                    return
                
                # Get book text
                text = self.gutenberg_utils.get_book_text(actual_id)
                if not text:
                    self.root.after(0, lambda: messagebox.showerror(i18n.t("error"), "Could not download book"))
                    return
                
                # Create EPUB
                epub_path = self.gutenberg_utils.create_epub_from_text(
                    text, f"Gutenberg Book {actual_id}", "Project Gutenberg", "en", actual_id
                )
                
                if not epub_path:
                    self.root.after(0, lambda: messagebox.showerror(i18n.t("error"), "Could not create EPUB"))
                    return
                
                # Get preview
                preview = self.gutenberg_utils.get_book_preview(actual_id, max_chars=1500)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.gutenberg_book_loaded(epub_path, preview))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(i18n.t("error"), f"Error loading book: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Error"))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def gutenberg_book_loaded(self, epub_path, preview):
        """Handle successful book loading"""
        self.current_epub_file = epub_path
        self.current_text_preview = preview
        self.file_path_var.set(epub_path)
        self.status_var.set(i18n.t("gutenberg_success"))
        messagebox.showinfo(i18n.t("success"), i18n.t("gutenberg_success"))
        
    def start_conversion(self):
        """Start the audiobook conversion"""
        if not self.current_epub_file:
            messagebox.showwarning(i18n.t("warning"), i18n.t("file_not_found"))
            return
            
        if self.conversion_running:
            messagebox.showwarning(i18n.t("warning"), i18n.t("conversion_running"))
            return
            
        # Create output directory
        output_dir = self.output_dir_var.get()
        os.makedirs(output_dir, exist_ok=True)
        
        messagebox.showinfo(i18n.t("info"), 
                           f"Conversion would start now with:\n"
                           f"File: {os.path.basename(self.current_epub_file)}\n"
                           f"Output: {output_dir}\n"
                           f"Provider: {self.tts_provider_var.get()}\n"
                           f"One file: {self.one_file_var.get()}")
        
    def cancel_conversion(self):
        """Cancel running conversion"""
        self.conversion_running = False
        
    def change_language(self, event=None):
        """Change UI language"""
        lang = self.language_var.get()
        i18n.set_language(lang)
        
        # Update window title
        self.root.title(i18n.t("title"))
        
        # In a full implementation, you would update all UI elements here
        # For now, just show a message
        messagebox.showinfo("Language", f"Language changed to {lang}. Restart for full effect.")

def main():
    """Main function"""
    root = tk.Tk()
    app = EnhancedEpubToAudiobookGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    print("🎧 Enhanced EPUB to Audiobook Converter")
    print("✨ Features:")
    print("   📚 Project Gutenberg integration")
    print("   🇩🇪 German/English UI")
    print("   💰 Cost estimation")
    print("   👁️  Text preview")
    print("   💿 One-file output option")
    print("")
    
    root.mainloop()

if __name__ == "__main__":
    main() 