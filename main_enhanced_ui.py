#!/usr/bin/env python3
"""
Enhanced EPUB to Audiobook Converter Web UI
Includes all features from the original GUI:
- Project Gutenberg integration
- German/English UI translation
- Cost estimation
- Text preview
- One-file output option
"""

import argparse
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audiobook_generator.ui.enhanced_web_ui import host_enhanced_ui

def main():
    parser = argparse.ArgumentParser(description='Enhanced EPUB to Audiobook Converter Web UI')
    parser.add_argument('--host', type=str, default='127.0.0.1', 
                       help='Host to run the web UI on (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=7860, 
                       help='Port to run the web UI on (default: 7860)')
    parser.add_argument('--language', type=str, default='en', choices=['en', 'de'],
                       help='Default UI language (default: en)')
    
    args = parser.parse_args()
    
    print(f"🎧 Enhanced EPUB to Audiobook Converter")
    print(f"🌐 Starting web interface on http://{args.host}:{args.port}")
    print(f"🗣️  Default language: {args.language}")
    print(f"")
    print(f"✨ New Features:")
    print(f"   📚 Project Gutenberg integration")
    print(f"   🇩🇪 German/English UI")
    print(f"   💰 Cost estimation")
    print(f"   👁️  Text preview")
    print(f"   💿 One-file output option")
    print(f"")
    print(f"Press Ctrl+C to stop the server")
    print(f"")
    
    try:
        host_enhanced_ui(args)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 