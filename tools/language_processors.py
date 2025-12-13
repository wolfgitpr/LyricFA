import re
from abc import ABC, abstractmethod
from typing import List

from .ZhG2p import ZhG2p, split_string as zh_split_string


def is_letter(character):
    return ('a' <= character <= 'z') or ('A' <= character <= 'Z')


def is_special_letter(character):
    special_letter = "'-’"
    return character in special_letter


def is_hanzi(character):
    return 0x4e00 <= ord(character) <= 0x9fa5


def is_kana(character):
    return (0x3040 <= ord(character) <= 0x309F) or (0x30A0 <= ord(character) <= 0x30FF)


def is_special_kana(character):
    special_kana = "ャュョゃゅょァィゥェォぁぃぅぇぉ"
    return character in special_kana


class LanguageProcessor(ABC):
    def __init__(self, language_code: str):
        self.language_code = language_code.lower()

    @abstractmethod
    def clean_text(self, text: str) -> str:
        pass

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        pass

    @abstractmethod
    def get_phonetic_list(self, text_list: List[str]) -> List[str]:
        pass


class ChineseProcessor(LanguageProcessor):
    def __init__(self):
        super().__init__('zh')
        self.g2p = ZhG2p('mandarin')

    def clean_text(self, text: str) -> str:
        chinese_char_range = r'[\u4e00-\u9fa5]'
        allowed_chars = rf'{chinese_char_range}a-zA-Z0-9\s，。！？、；："\'-'
        cleaned = re.sub(rf'[^{allowed_chars}]', '', text)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def split_text(self, text: str) -> List[str]:
        return zh_split_string(text)

    def get_phonetic_list(self, text_list: List[str]) -> List[str]:
        return self.g2p.convert_list(text_list).split(' ')


class EnglishProcessor(LanguageProcessor):
    def __init__(self):
        super().__init__('en')

    def clean_text(self, text: str) -> str:
        allowed_chars = r'a-zA-Z0-9\s,.!?;:"\'-'
        cleaned = re.sub(rf'[^{allowed_chars}]', '', text)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def split_text(self, text: str) -> List[str]:
        return zh_split_string(text.lower())

    def get_phonetic_list(self, text_list: List[str]) -> List[str]:
        return text_list


class LyricData:
    def __init__(self, text_list: List[str], phonetic_list: List[str], raw_text: str):
        self.text_list = text_list
        self.phonetic_list = phonetic_list
        self.raw_text = raw_text


class ProcessorFactory:
    _PROCESSOR_MAP = {
        'zh': ChineseProcessor,
        'en': EnglishProcessor
    }

    @classmethod
    def create_processor(cls, language_code: str) -> LanguageProcessor:
        if language_code not in cls._PROCESSOR_MAP:
            raise ValueError(f"Unsupported language: {language_code}")
        return cls._PROCESSOR_MAP[language_code]()

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        return list(cls._PROCESSOR_MAP.keys())
