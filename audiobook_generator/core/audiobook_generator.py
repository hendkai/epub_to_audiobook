import logging
import multiprocessing
import os
import glob
from pydub import AudioSegment

from audiobook_generator.book_parsers.base_book_parser import get_book_parser
from audiobook_generator.config.general_config import GeneralConfig
from audiobook_generator.core.audio_tags import AudioTags
from audiobook_generator.tts_providers.base_tts_provider import get_tts_provider
from audiobook_generator.utils.log_handler import setup_logging

logger = logging.getLogger(__name__)


def confirm_conversion():
    logger.info("Do you want to continue? (y/n)")
    answer = input()
    if answer.lower() != "y":
        logger.info("Aborted.")
        exit(0)


def get_total_chars(chapters):
    total_characters = 0
    for title, text in chapters:
        total_characters += len(text)
    return total_characters


class AudiobookGenerator:
    def __init__(self, config: GeneralConfig):
        self.config = config

    def __str__(self) -> str:
        return f"{self.config}"

    def process_chapter(self, idx, title, text, book_parser):
        """Process a single chapter: write text (if needed) and convert to audio."""
        try:
            logger.info(f"Processing chapter {idx}: {title}")
            tts_provider = get_tts_provider(self.config)

            # Save chapter text if required
            if self.config.output_text:
                text_file = os.path.join(self.config.output_folder, f"{idx:04d}_{title}.txt")
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(text)

            # Skip audio generation in preview mode
            if self.config.preview:
                return True

            # Generate audio file
            output_file = os.path.join(
                self.config.output_folder,
                f"{idx:04d}_{title}.{tts_provider.get_output_file_extension()}",
            )
            audio_tags = AudioTags(
                title, book_parser.get_book_author(), book_parser.get_book_title(), idx
            )
            tts_provider.text_to_speech(text, output_file, audio_tags)

            logger.info(f"✅ Converted chapter {idx}: {title}, output file: {output_file}")

            return True
        except Exception as e:
            logger.exception(f"Error processing chapter {idx}, error: {e}")
            return False

    def process_chapter_wrapper(self, args):
        """Wrapper for process_chapter to handle unpacking args for imap."""
        idx, title, text, book_parser = args
        return idx, self.process_chapter(idx, title, text, book_parser)

    def _combine_audio_files(self, book_parser, tts_provider):
        """Combine all audio files into a single file."""
        try:
            logger.info("Combining audio files into single output file...")
            
            # Get file extension
            file_extension = tts_provider.get_output_file_extension()
            
            # Find all audio files in output directory
            audio_files = glob.glob(os.path.join(self.config.output_folder, f"*.{file_extension}"))
            audio_files.sort()  # Sort to maintain chapter order
            
            if not audio_files:
                logger.warning("No audio files found to combine")
                return
            
            # Load and combine audio files
            combined_audio = AudioSegment.empty()
            
            for audio_file in audio_files:
                logger.info(f"Adding {os.path.basename(audio_file)} to combined file")
                audio_segment = AudioSegment.from_file(audio_file)
                combined_audio += audio_segment
                
                # Add a small pause between chapters (1 second)
                combined_audio += AudioSegment.silent(duration=1000)
            
            # Create output filename
            book_title = book_parser.get_book_title().replace(" ", "_").replace("/", "_")
            output_filename = f"{book_title}_complete.{file_extension}"
            output_path = os.path.join(self.config.output_folder, output_filename)
            
            # Export combined audio
            logger.info(f"Exporting combined audio to: {output_filename}")
            combined_audio.export(output_path, format=file_extension.lower())
            
            # Set audio tags for the combined file
            audio_tags = AudioTags(
                book_parser.get_book_title(),
                book_parser.get_book_author(),
                book_parser.get_book_title(),
                1
            )
            
            # Apply tags if supported
            try:
                import eyed3
                audiofile = eyed3.load(output_path)
                if audiofile and audiofile.tag:
                    audiofile.tag.title = audio_tags.title
                    audiofile.tag.artist = audio_tags.author
                    audiofile.tag.album = audio_tags.series_title
                    audiofile.tag.track_num = audio_tags.part_number
                    audiofile.tag.save()
            except ImportError:
                logger.warning("eyed3 not available, skipping ID3 tags for combined file")
            except Exception as e:
                logger.warning(f"Could not set audio tags: {e}")
            
            logger.info(f"✅ Combined audio file created: {output_filename}")
            
        except Exception as e:
            logger.exception(f"Error combining audio files: {e}")

    def run(self):
        try:
            logger.info("Starting audiobook generation...")
            book_parser = get_book_parser(self.config)
            tts_provider = get_tts_provider(self.config)

            os.makedirs(self.config.output_folder, exist_ok=True)
            chapters = book_parser.get_chapters(tts_provider.get_break_string())
            # Filter out empty or very short chapters
            chapters = [(title, text) for title, text in chapters if text.strip()]

            logger.info(f"Chapters count: {len(chapters)}.")

            # Check chapter start and end args
            if self.config.chapter_start < 1 or self.config.chapter_start > len(chapters):
                raise ValueError(
                    f"Chapter start index {self.config.chapter_start} is out of range. Check your input."
                )
            if self.config.chapter_end < -1 or self.config.chapter_end > len(chapters):
                raise ValueError(
                    f"Chapter end index {self.config.chapter_end} is out of range. Check your input."
                )
            if self.config.chapter_end == -1:
                self.config.chapter_end = len(chapters)
            if self.config.chapter_start > self.config.chapter_end:
                raise ValueError(
                    f"Chapter start index {self.config.chapter_start} is larger than chapter end index {self.config.chapter_end}. Check your input."
                )

            logger.info(
                f"Converting chapters from {self.config.chapter_start} to {self.config.chapter_end}."
            )

            # Initialize total_characters to 0
            total_characters = get_total_chars(
                chapters[self.config.chapter_start - 1 : self.config.chapter_end]
            )
            logger.info(f"Total characters in selected book chapters: {total_characters}")
            rough_price = tts_provider.estimate_cost(total_characters)
            logger.info(f"Estimate book voiceover would cost you roughly: ${rough_price:.2f}\n")

            # Prompt user to continue if not in preview mode
            if self.config.no_prompt:
                logger.info("Skipping prompt as passed parameter no_prompt")
            elif self.config.preview:
                logger.info("Skipping prompt as in preview mode")
            else:
                confirm_conversion()

            # Prepare chapters for processing
            chapters_to_process = chapters[self.config.chapter_start - 1 : self.config.chapter_end]
            tasks = [
                (idx, title, text, book_parser)
                for idx, (title, text) in enumerate(
                    chapters_to_process, start=self.config.chapter_start
                )
            ]

            # Track failed chapters
            failed_chapters = []

            # Use multiprocessing to process chapters in parallel
            with multiprocessing.Pool(
                processes=self.config.worker_count,
                initializer=setup_logging,
                initargs=(self.config.log, self.config.log_file, True)
            ) as pool:
                # Process chapters and collect results
                results = list(pool.imap_unordered(self.process_chapter_wrapper, tasks))

                # Check for failed chapters
                for idx, success in results:
                    if not success:
                        chapter_title = chapters_to_process[idx - self.config.chapter_start][0]
                        failed_chapters.append((idx, chapter_title))

            if failed_chapters:
                logger.warning("The following chapters failed to convert:")
                for idx, title in failed_chapters:
                    logger.warning(f"  - Chapter {idx}: {title}")
                logger.info(f"Conversion completed with {len(failed_chapters)} failed chapters. Check your output directory: {self.config.output_folder} and log file: {self.config.log_file} for more details.")
            else:
                logger.info(f"All chapters converted successfully. Check your output directory: {self.config.output_folder}")

            # Handle one-file output if requested
            if self.config.one_file_output and not self.config.preview:
                self._combine_audio_files(book_parser, tts_provider)

        except KeyboardInterrupt:
            logger.info("Audiobook generation process interrupted by user (Ctrl+C).")
        except Exception as e:
            logger.exception(f"Error during audiobook generation: {e}")
        finally:
            logger.debug("AudiobookGenerator.run() method finished.")

