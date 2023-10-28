import re


class ZhG2p:
    def __init__(self, language):
        self.PhrasesMap = {}
        self.TransDict = {}
        self.WordDict = {}
        self.PhrasesDict = {}

        if language == "mandarin":
            dictDir = "Dicts/mandarin"
        else:
            dictDir = "Dicts/cantonese"

        self.load_dict(dictDir, "phrases_map.txt", self.PhrasesMap)
        self.load_dict(dictDir, "phrases_dict.txt", self.PhrasesDict)
        self.load_dict(dictDir, "user_dict.txt", self.PhrasesDict)
        self.load_dict(dictDir, "word.txt", self.WordDict)
        self.load_dict(dictDir, "trans_word.txt", self.TransDict)

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

    @staticmethod
    def load_dict(_dictDir, _fileName, _resultMap):
        dict_path = _dictDir + "/" + _fileName
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    key, value = line.split(':')
                    _resultMap[key] = value

    NumMap = {
        "0": "零",
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七",
        "8": "八",
        "9": "九"
    }

    @staticmethod
    def reset_zh(input, res, positions):
        result = input.copy()
        for i, pos in enumerate(positions):
            result[pos] = res[i]
        return " ".join(result)

    @staticmethod
    def add_string(text, res):
        temp = text.split(' ')
        res.extend(temp)

    @staticmethod
    def remove_elements(lst, start, n):
        if 0 <= start < len(lst) and n > 0:
            count_to_remove = min(n, len(lst) - start)
            del lst[start:start + count_to_remove]

    def zh_position(self, input, res, positions):
        for i, val in enumerate(input):
            if val in self.WordDict or val in self.TransDict:
                res.append(val)
                positions.append(i)

    def convert_string(self, input, tone=False, convert_num=False):
        return self.convert_list(self.split_string(input), tone, convert_num)

    def convert_list(self, input, tone=False, convert_num=False):
        input_list = []
        input_pos = []
        self.zh_position(input, input_list, input_pos)
        result = []
        cursor = 0

        while cursor < len(input_list):
            raw_current_char = input_list[cursor]
            current_char = self.trad_to_sim(raw_current_char)

            if convert_num and current_char in self.NumMap:
                result.append(self.NumMap[current_char])
                cursor += 1

            if current_char not in self.WordDict:
                result.append(current_char)
                cursor += 1
                continue

            if not self.is_polyphonic(current_char):
                result.append(self.get_default_pinyin(current_char))
                cursor += 1
            else:
                found = False
                for length in range(4, 1, -1):
                    if cursor + length <= len(input_list):
                        sub_phrase = ''.join(input_list[cursor:cursor + length])
                        if sub_phrase in self.PhrasesDict:
                            self.add_string(self.PhrasesDict[sub_phrase], result)
                            cursor += length
                            found = True

                        if cursor >= 1 and not found:
                            sub_phrase_1 = "".join(input_list[cursor - 1:cursor + length - 1])
                            if sub_phrase_1 in self.PhrasesDict:
                                result = result[:-1]
                                self.add_string(self.PhrasesDict[sub_phrase_1], result)
                                cursor += length - 1
                                found = True

                    if 0 <= cursor + 1 - length < cursor + 1 and not found and cursor < len(input_list):
                        x_sub_phrase = ''.join(input_list[cursor + 1 - length:cursor + 1])
                        if x_sub_phrase in self.PhrasesDict:
                            self.remove_elements(result, cursor + 1 - length, length - 1)
                            self.add_string(self.PhrasesDict[x_sub_phrase], result)
                            cursor += 1
                            found = True

                    if 0 <= cursor + 2 - length < cursor + 2 and not found and cursor < len(input_list):
                        x_sub_phrase = ''.join(input_list[cursor + 2 - length:cursor + 2])
                        if x_sub_phrase in self.PhrasesDict:
                            self.remove_elements(result, cursor + 2 - length, length - 2)
                            self.add_string(self.PhrasesDict[x_sub_phrase], result)
                            cursor += 2
                            found = True

                if not found:
                    result.append(self.get_default_pinyin(current_char))
                    cursor += 1

        if not tone:
            result = [re.sub('[^a-z]', '', item) for item in result]

        return self.reset_zh(input, result, input_pos)

    def is_polyphonic(self, text):
        return text in self.PhrasesMap

    def trad_to_sim(self, text):
        return self.TransDict[text] if text in self.TransDict else text

    def get_default_pinyin(self, text):
        return self.WordDict[text] if text in self.WordDict else None
