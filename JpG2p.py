import re


class JpG2p:
    def __init__(self):
        self.kana_to_romaji_map = {}
        self.romaji_to_kana_map = {}
        self.load_dict('Dicts', "kana2romaji.txt")

    @staticmethod
    def split_string(input):
        res = []
        rx = r"(?![ー゜])([a-zA-Z]+|[0-9]|[\u4e00-\u9fa5]|[\u3040-\u309F\u30A0-\u30FF][ャュョゃゅょァィゥェォぁぃぅぇぉ]?)"

        pos = 0  # 记录匹配位置的变量

        while True:
            match = re.search(rx, input[pos:])
            if not match:
                break
            start, end = match.span()
            res.append(input[pos + start:pos + end])
            pos += end  # 更新匹配位置

        return res

    def load_dict(self, dict_dir, file_name):
        dict_path = f"{dict_dir}/{file_name}"
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    key, value = line.split(':')
                    self.kana_to_romaji_map[key] = value
                    self.romaji_to_kana_map[value] = key

    @staticmethod
    def filter_string(input_str):
        # 保留字母字符，去除其他字符
        clean_str = re.sub(r'[^a-zA-Z]+', ' ', input_str)
        return clean_str

    @staticmethod
    def split_romaji(input_str):
        clean_str = JpG2p.filter_string(input_str)
        res = re.findall(r'(?=[^aiueo])[a-zA-Z]{0,2}[aiueo]', clean_str)
        return res

    def is_kana(self, character):
        # Kana Unicode 范围：U+3040 - U+30FF
        return '\u3040' <= character <= '\u30FF'

    def convert_kana(self, kana_list, kana_type):
        hiragana_start = ord('\u3041')
        katakana_start = ord('\u30A1')
        converted_list = []

        for kana in kana_list:
            converted_kana = ""
            kana_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF]+', kana)

            if kana_chars:
                for kana_char in kana:
                    if kana_type == 'Hiragana':
                        if katakana_start <= ord(kana_char) < katakana_start + 0x5E:
                            # Katakana 转 Hiragana
                            converted_kana += chr(ord(kana_char) - (katakana_start - hiragana_start))
                        else:
                            converted_kana += kana_char
                    else:
                        if hiragana_start <= ord(kana_char) < hiragana_start + 0x5E:
                            # Hiragana 转 Katakana
                            converted_kana += chr(ord(kana_char) + (katakana_start - hiragana_start))
                        else:
                            converted_kana += kana_char
            else:
                converted_kana = kana

            converted_list.append(converted_kana)

        return converted_list

    def kana_to_romaji(self, kana_list, double_written_sokuon=False):
        input_list = self.convert_kana(kana_list, 'Hiragana')
        romaji_list = []

        for kana in input_list:
            romaji_list.append(self.kana_to_romaji_map.get(kana, kana))

        if double_written_sokuon:
            i = 0
            while i < len(romaji_list) - 1:
                next_char = self.romaji_to_kana_map.get(romaji_list[i + 1], " ")[0]

                if romaji_list[i] == "cl" and self.is_kana(next_char) and next_char not in "あいうえおアイウエオっんを":
                    romaji_list[i + 1] = romaji_list[i + 1][0] + romaji_list[i + 1]
                    romaji_list.pop(i)

                i += 1

        return ' '.join(romaji_list)

    def romaji_to_kana(self, romaji_str):
        romaji_list = self.split_romaji(romaji_str)
        kana_list = [self.romaji_to_kana_map.get(romaji, romaji) for romaji in romaji_list]
        return kana_list
