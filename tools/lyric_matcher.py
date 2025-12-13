import glob
import json
import os
from typing import Dict, List, Tuple, Optional

from .language_processors import ProcessorFactory, LyricData
from .sequence_aligner import SequenceAligner, calculate_difference_count, SmartHighlighter


class LyricMatcher:
    def __init__(self, language: str):
        self.language = language.lower()
        self.processor = ProcessorFactory.create_processor(language)
        self.aligner = SequenceAligner()
        self.highlighter = SmartHighlighter()

    def process_lyric_file(self, lyric_path: str) -> Optional[LyricData]:
        try:
            with open(lyric_path, 'r', encoding='utf-8') as file:
                raw_text = file.read()
        except Exception as error:
            raise IOError(f"Cannot read lyric file {lyric_path}: {str(error)}")

        cleaned_text = self.processor.clean_text(raw_text)
        text_list = self.processor.split_text(cleaned_text)
        phonetic_list = self.processor.get_phonetic_list(text_list)
        return LyricData(text_list, phonetic_list, cleaned_text)

    def process_asr_content(self, lab_content: str) -> Tuple[List[str], List[str]]:
        cleaned_content = self.processor.clean_text(lab_content)
        text_list = self.processor.split_text(cleaned_content)
        phonetic_list = self.processor.get_phonetic_list(text_list)
        return text_list, phonetic_list

    def align_lyric_with_asr(
            self,
            asr_phonetic: List[str],
            lyric_text: List[str],
            lyric_phonetic: List[str]
    ) -> Tuple[str, str]:
        matched_text, start_index, end_index = self.aligner.find_best_match_and_return_lyrics(
            input_pronunciation=asr_phonetic,
            reference_text=lyric_text,
            reference_pronunciation=lyric_phonetic
        )
        if start_index >= 0 and end_index >= 0:
            matched_phonetic = " ".join(lyric_phonetic[start_index:end_index])
            return matched_text, matched_phonetic
        return "", ""

    @staticmethod
    def save_to_json(json_path: str, text: str, phonetic: str) -> None:
        data = {
            "raw_text": text,
            "lab": phonetic,
            "lab_without_tone": phonetic
        }
        try:
            with open(json_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=3)
        except Exception as error:
            raise IOError(f"Cannot write JSON file {json_path}: {str(error)}")


class ProcessingStats:
    def __init__(self):
        self.total_files = 0
        self.success_count = 0
        self.diff_count = 0
        self.missing_lyrics = []

    def add_missing_lyric(self, lyric_name: str):
        if lyric_name not in self.missing_lyrics:
            self.missing_lyrics.append(lyric_name)

    def print_summary(self, diff_threshold: int):
        if self.missing_lyrics:
            print(f'Files with missing lyrics: {self.missing_lyrics}')
        print(f'{self.diff_count} files exceed difference threshold ({diff_threshold}).')
        print(f'Total files: {self.total_files}, successfully processed: {self.success_count}.')


class LyricMatchingPipeline:
    def __init__(
            self,
            lyric_folder: str,
            lab_folder: str,
            json_folder: str,
            language: str,
            diff_threshold: int = 5
    ):
        self.lyric_folder = lyric_folder
        self.lab_folder = lab_folder
        self.json_folder = json_folder
        self.language = language
        self.diff_threshold = diff_threshold
        self.matcher = LyricMatcher(language)
        self.stats = ProcessingStats()

    def load_all_lyrics(self) -> Dict[str, LyricData]:
        lyric_dict = {}
        lyric_pattern = f'{self.lyric_folder}/*.txt'
        for lyric_path in glob.glob(lyric_pattern):
            lyric_name = self.extract_filename_without_extension(lyric_path)
            try:
                lyric_data = self.matcher.process_lyric_file(lyric_path)
                if lyric_data:
                    lyric_dict[lyric_name] = lyric_data
                    print(f"Processed lyric file: {lyric_name}")
            except Exception as error:
                print(f"Error processing lyric file {lyric_name}: {str(error)}")
        print()
        return lyric_dict

    @staticmethod
    def extract_filename_without_extension(file_path: str) -> str:
        return os.path.splitext(os.path.basename(file_path))[0]

    def process_single_file(
            self,
            lab_path: str,
            lyric_dict: Dict[str, LyricData]
    ) -> Optional[Tuple[str, str, str, List[str], List[str]]]:
        lab_name = self.extract_filename_without_extension(lab_path)
        lyric_name = lab_name.rsplit("_", 1)[0]

        if lyric_name not in lyric_dict:
            self.stats.add_missing_lyric(lyric_name)
            print(f"Lab file: {lab_path}\nMissing lyric file: {lyric_name}")
            return None

        try:
            with open(lab_path, 'r', encoding='utf-8') as file:
                lab_content = file.read().strip()
        except Exception as error:
            print(f"Error reading lab file {lab_name}: {str(error)}")
            return None

        lyric_data = lyric_dict[lyric_name]
        asr_text, asr_phonetic = self.matcher.process_asr_content(lab_content)

        if not asr_phonetic:
            print(f"Warning: ASR result empty {lab_name}")
            return None

        matched_text, matched_phonetic = self.matcher.align_lyric_with_asr(
            asr_phonetic=asr_phonetic,
            lyric_text=lyric_data.text_list,
            lyric_phonetic=lyric_data.phonetic_list
        )

        return lab_name, matched_text, matched_phonetic, asr_phonetic, asr_text

    def compare_and_save_result(
            self,
            lab_name: str,
            matched_text: str,
            matched_phonetic: str,
            asr_phonetic: List[str],
            asr_text: List[str]
    ) -> None:
        if self.language == 'zh':
            source_sequence = asr_phonetic
            target_sequence = matched_phonetic.split()
        else:
            source_sequence = asr_text
            target_sequence = matched_text.split()

        diff_count = calculate_difference_count(source_sequence, target_sequence)

        if diff_count > self.diff_threshold:
            self.display_detailed_differences(
                lab_name, matched_text, matched_phonetic, asr_phonetic
            )
            self.stats.diff_count += 1

        json_path = f'{self.json_folder}/{lab_name}.json'
        self.matcher.save_to_json(json_path, matched_text, matched_phonetic)
        self.stats.success_count += 1

    def display_detailed_differences(
            self,
            lab_name: str,
            matched_text: str,
            matched_phonetic: str,
            asr_phonetic: List[str],
    ) -> None:
        asr_result_str = " ".join(asr_phonetic)
        highlighted_asr, highlighted_phonetic, highlighted_text, operation_count = self.matcher.highlighter.highlight_differences(
            asr_result_str, matched_phonetic, matched_text
        )
        print(f"lab_name:         {lab_name}")
        print(f"match_text:       {highlighted_text}")
        print(f"asr_result:       {highlighted_asr}")
        print(f"match_phonetic:   {highlighted_phonetic}")
        print(f"diff count:       {operation_count}")
        print("-" * 80)

    def execute(self) -> None:
        os.makedirs(self.json_folder, exist_ok=True)
        lyric_dict = self.load_all_lyrics()
        lab_pattern = f'{self.lab_folder}/*.lab'
        asr_lab_files = glob.glob(lab_pattern)
        self.stats.total_files = len(asr_lab_files)

        for lab_path in asr_lab_files:
            result = self.process_single_file(lab_path, lyric_dict)
            if result:
                self.compare_and_save_result(*result)
        self.stats.print_summary(self.diff_threshold)
