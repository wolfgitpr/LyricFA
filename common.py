import yaml


class LevenshteinDistance:
    def __init__(self, load_yaml=False, syllable=False, consonant=False, vowel=False):
        self.syllable = syllable
        self.consonant = consonant
        self.vowel = vowel
        self.phoneme_dict = {}
        self.syllable_dict = {}
        self.consonant_dict = {}
        self.vowel_dict = {}
        if load_yaml:
            self.load_yaml()

    def load_yaml(self):
        with open('Near_syllable.yaml', 'r') as file:
            data = yaml.safe_load(file)
        self.load_phoneme_dict(data['dictionary_path'])
        self.syllable_dict = data['syllable']
        self.consonant_dict = data['consonant']
        self.vowel_dict = data['vowel']

    def load_phoneme_dict(self, dict_path):
        with open(dict_path, 'r') as file:
            data = file.readlines()
        for line in data:
            k, v = line.strip("\n").split("\t")
            self.phoneme_dict[k] = v.split(" ")

    def match_pinyin(self, raw, target):
        if raw == target:
            return True
        elif self.syllable and self.syllable_dict.get(raw, raw) == target:
            return True
        elif self.consonant:
            raw = self.phoneme_dict.get(raw, raw)
            target = self.phoneme_dict.get(target, target)
            if len(raw) > 1 and len(target) > 1:
                if self.consonant_dict.get(raw[0], raw[0]) == target[0] and raw[1] == target[1]:
                    return True
            elif len(raw) == 1 and len(target) == 1:
                if raw[0] == target[0]:
                    return True
        elif self.vowel:
            raw = self.phoneme_dict.get(raw, raw)
            target = self.phoneme_dict.get(target, target)
            if len(raw) > 1 and len(target) > 1:
                if raw[0] == target[0] and self.vowel_dict.get(raw[1], raw[1]) == target[1]:
                    return True
            elif len(raw) == 1 and len(target) == 1:
                if raw[0] == target[0]:
                    return True
        return False

    def find_best_matches(self, source_list, sub_list):
        max_match_length = 0
        max_match_index = -1

        diff_res = []
        for i in range(len(source_list)):
            match_length = 0
            j = 0
            while i + j < len(source_list) and j < len(sub_list):
                if self.match_pinyin(source_list[i + j], sub_list[j]):
                    match_length += 1
                else:
                    diff_res.append(f"({source_list[i + j]}->{sub_list[j]})")
                j += 1

            if match_length > max_match_length:
                max_match_length = match_length
                max_match_index = i

        return max_match_index, max_match_index + len(sub_list), diff_res

    def find_similar_substrings(self, target, pinyin_list, text_list=None, del_tip=False, ins_tip=False, sub_tip=False):
        if text_list is None:
            text_list = pinyin_list
        assert len(text_list) == len(pinyin_list), "The length of text_list and pinyin_list must be the same."
        pos = self.find_best_matches(pinyin_list, target)
        slider_res = pinyin_list[pos[0]:pos[1]]
        if slider_res == target:
            return " ".join(text_list[pos[0]:pos[1]]), " ".join(pinyin_list[pos[0]:pos[1]]), " ".join(pos[2])
        elif len(slider_res) > 0 and slider_res[0] == target[0] and slider_res[-1] == target[-1] and len(pos[2]) <= 2:
            return " ".join(text_list[pos[0]:pos[1]]), " ".join(pinyin_list[pos[0]:pos[1]]), " ".join(pos[2])

        similar_substrings = []

        # 扩展匹配范围，最多扩展10个字符
        for sub_length in range(len(target), min(len(target) + 10, len(pinyin_list) + 1)):
            # 滑动窗口，以预匹配的范围为中心，向两边扩展10个字符
            for i in range(max(0, pos[0] - 10), min(pos[1] + 10, len(pinyin_list) - sub_length + 1)):
                _pinyin_list = pinyin_list[i:i + sub_length]
                _text_list = text_list[i:i + sub_length]

                distance, _text_res, _res, _step = self.calculate_edit_distance(_text_list, _pinyin_list, target)
                similar_substrings.append((_text_res, _res, distance, _step))

        similar_substrings.sort(key=lambda _x: _x[2])
        _text_res, _res, _, _step = similar_substrings[0]

        output = []
        for x in _step:
            if type(x) is tuple:
                if x[0] != '' and x[1] == '' and del_tip:
                    output.append(f"({x[0]}->)")
                elif x[0] == '' and x[1] != '' and ins_tip:
                    output.append(f"(->{x[1]})")
                elif x[0] != '' and x[1] != '' and sub_tip:
                    output.append(f"({x[0]}->{x[1]})")
        return " ".join(_text_res), " ".join(_res), " ".join(output)

    def calculate_edit_distance(self, _text, substring, target, del_cost=1, ins_cost=3, sub_cost=6):
        m, n = len(substring), len(target)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i * del_cost  # 删除操作的权重

        for j in range(n + 1):
            dp[0][j] = j * ins_cost  # 插入操作的权重

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if self.match_pinyin(substring[i - 1], target[j - 1]):
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j - 1] + sub_cost,  # 替换操作的权重
                        dp[i][j - 1] + ins_cost,  # 插入操作的权重
                        dp[i - 1][j] + del_cost  # 删除操作的权重
                    )

        if self.match_pinyin(substring[0], target[0]):
            # Compute the edit distance without subtracting 1
            edit_distance = dp[m][n]
        else:
            # Compute the edit distance and add 1
            edit_distance = dp[m][n] + 1

        corresponding_texts = []
        corresponding_characters = []
        i, j = m, n
        while i > 0 and j > 0:
            if self.match_pinyin(substring[i - 1], target[j - 1]):
                corresponding_characters.insert(0, target[j - 1])
                corresponding_texts.insert(0, _text[i - 1])
                i -= 1
                j -= 1
            else:
                min_cost = min(
                    dp[i - 1][j - 1],
                    dp[i][j - 1],
                    dp[i - 1][j]
                )
                if dp[i - 1][j - 1] == min_cost:
                    corresponding_characters.insert(0, (substring[i - 1], target[j - 1]))
                    corresponding_texts.insert(0, (_text[i - 1], target[j - 1]))
                    i -= 1
                    j -= 1
                elif dp[i][j - 1] == min_cost:
                    corresponding_characters.insert(0, ('', target[j - 1]))
                    corresponding_texts.insert(0, ('', target[j - 1]))
                    j -= 1
                else:
                    corresponding_characters.insert(0, (substring[i - 1], ''))
                    corresponding_texts.insert(0, (_text[i - 1], ''))
                    i -= 1

        text_res = []
        pinyin_res = []
        for x, y in zip(corresponding_characters, corresponding_texts):
            if type(x) is str:
                pinyin_res.append(x)
                text_res.append(y)
            elif type(x) is tuple and x[0] == '' and x[1] != '':
                pinyin_res.append(x[1])
                text_res.append(y[1])
            elif type(x) is tuple and x[0] != '' and x[1] != '':
                pinyin_res.append(x[0])
                text_res.append(y[0])

        return edit_distance, text_res, pinyin_res, corresponding_characters


if __name__ == "__main__":
    lyric_pinyin_list = "xi nan dou bu jie bie ren zen me shuo wo dou bu jie yi wo ai bu ai ni ri jiu jian ren xin"
    text_content = "希 男 都 不 解 别 人 怎 么 说 我 都 不 解 一 我 爱 不 爱 你 日 久 见 人 心"
    lab_content = "xi lan ren zen ha ha shuo we dou bu jie"

    LD_Match = LevenshteinDistance(yaml_path=True, consonant=True)
    text, res, step = LD_Match.find_similar_substrings(lab_content.split(" "), lyric_pinyin_list.split(" "),
                                                       text_list=text_content.split(" "), sub_tip=True)

    print("asr_labc:", lab_content)
    print("text_res:", text)
    print("pyin_res:", res)
    print("step:", step)
    print()
