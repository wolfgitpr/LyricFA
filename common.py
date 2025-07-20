from typing import List, Tuple, Union, Optional


class LdRes:
    def __init__(self, edit_distance, text_res, pinyin_res, corresponding_texts, corresponding_characters):
        self.edit_distance = edit_distance
        self.text_res = text_res
        self.pinyin_res = pinyin_res
        self.corresponding_texts = corresponding_texts
        self.corresponding_characters = corresponding_characters


class LevenshteinDistance:
    @staticmethod
    def find_best_matches(
            text_list: List[str],
            source_list: List[str],
            sub_list: List[str]
    ) -> Tuple[int, int, List[str], List[str]]:
        max_match_length: int = 0
        max_match_index: int = -1

        for i in range(len(source_list)):
            match_length: int = 0
            j: int = 0
            while i + j < len(source_list) and j < len(sub_list):
                if source_list[i + j] == sub_list[j]:
                    match_length += 1
                j += 1

            if match_length > max_match_length:
                max_match_length = match_length
                max_match_index = i

        max_match_length = min(len(source_list) - max_match_index, len(sub_list))
        if max_match_length < len(sub_list):
            max_match_index = max(0, max_match_index - (len(sub_list) - max_match_length))
            max_match_length = min(len(source_list) - max_match_index, len(sub_list))

        if max_match_index == -1:
            max_match_index = 0
            max_match_length = len(sub_list)

        text_diff: List[str] = []
        pinyin_diff: List[str] = []
        for k in range(0, len(sub_list)):
            if not source_list[max_match_index + k] == sub_list[k]:
                text_diff.append(f"({text_list[max_match_index + k]}->{sub_list[k]}, {k})")
                pinyin_diff.append(f"({source_list[max_match_index + k]}->{sub_list[k]}, {k})")

        return max_match_index, max_match_index + max_match_length, text_diff, pinyin_diff

    def find_similar_substrings(
            self,
            target: List[str],
            pinyin_list: List[str],
            text_list: Optional[List[str]] = None,
            del_tip: bool = False,
            ins_tip: bool = False,
            sub_tip: bool = False
    ) -> Tuple[str, str, str, str]:
        if text_list is None:
            text_list = pinyin_list
        assert len(target) <= len(
            pinyin_list), "The length of target must be less than or equal to the length of pinyin_list."
        assert len(text_list) == len(pinyin_list), "The length of text_list and pinyin_list must be the same."
        pos = self.find_best_matches(text_list, pinyin_list, target)
        slider_res: List[str] = pinyin_list[pos[0]:pos[1]]
        if len(slider_res) > 0 and (slider_res[0] == target[0] or slider_res[-1] == target[-1]) and len(pos[2]) <= 1:
            return " ".join(text_list[pos[0]:pos[1]]), " ".join(pinyin_list[pos[0]:pos[1]]), " ".join(pos[2]), " ".join(
                pos[3])

        ld_results: List[LdRes] = []

        # 扩展匹配范围，最多扩展10个字符
        for sub_length in range(len(target), min(len(target) + 10, len(pinyin_list) + 1)):
            # 滑动窗口，以预匹配的范围为中心，向两边扩展10个字符
            for i in range(max(0, pos[0] - 10), min(pos[1] + 10, len(pinyin_list) - sub_length + 1)):
                _pinyin_list = pinyin_list[i:i + sub_length]
                _text_list = text_list[i:i + sub_length]

                ld_results.append(self.calculate_edit_distance(_text_list, _pinyin_list, target))

        ld_results.sort(key=lambda _x: _x.edit_distance)
        min_edit_distance_res = ld_results[0]

        return (" ".join(min_edit_distance_res.text_res), " ".join(min_edit_distance_res.pinyin_res),
                self.fill_step_out(min_edit_distance_res.corresponding_texts, del_tip, ins_tip, sub_tip),
                self.fill_step_out(min_edit_distance_res.corresponding_characters, del_tip, ins_tip, sub_tip))

    @staticmethod
    def fill_step_out(
            _step: List[Union[str, Tuple[str, str]]],
            del_tip: bool,
            ins_tip: bool,
            sub_tip: bool
    ) -> str:
        output: List[str] = []
        for idx, x in enumerate(_step):
            if type(x) is tuple:
                if x[0] != '' and x[1] == '' and del_tip:
                    output.append(f"({x[0]}->, {idx})")
                elif x[0] == '' and x[1] != '' and ins_tip:
                    output.append(f"(->{x[1]}, {idx})")
                elif x[0] != '' and x[1] != '' and sub_tip:
                    output.append(f"({x[0]}->{x[1]}, {idx})")
        return " ".join(output)

    @staticmethod
    def initialize_dp_matrix(
            m: int,
            n: int,
            del_cost: float,
            ins_cost: float
    ) -> List[List[float]]:
        dp: List[List[float]] = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i * del_cost  # 删除操作的权重

        for j in range(n + 1):
            dp[0][j] = j * ins_cost  # 插入操作的权重

        return dp

    @staticmethod
    def calculate_edit_distance_dp(
            dp: List[List[float]],
            substring: List[str],
            target: List[str],
            del_cost: float,
            ins_cost: float,
            sub_cost: float
    ) -> float:
        m, n = len(substring), len(target)

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if substring[i - 1] == target[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j - 1] + sub_cost,  # 替换操作的权重
                        dp[i][j - 1] + ins_cost,  # 插入操作的权重
                        dp[i - 1][j] + del_cost  # 删除操作的权重
                    )

        return dp[m][n]

    @staticmethod
    def backtrack_corresponding(
            dp: List[List[float]],
            _text: List[str],
            substring: List[str],
            target: List[str]
    ) -> Tuple[List[Union[str, Tuple[str, str]]], List[Union[str, Tuple[str, str]]]]:
        corresponding_texts: List[Union[str, Tuple[str, str]]] = []
        corresponding_characters: List[Union[str, Tuple[str, str]]] = []
        i, j = len(substring), len(target)

        while i > 0 and j > 0:
            if substring[i - 1] == target[j - 1]:
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

        return corresponding_texts, corresponding_characters

    def calculate_edit_distance(
            self,
            _text: List[str],
            substring: List[str],
            target: List[str],
            del_cost: float = 1,
            ins_cost: float = 3,
            sub_cost: float = 6
    ) -> LdRes:
        m, n = len(substring), len(target)
        dp: List[List[float]] = self.initialize_dp_matrix(m, n, del_cost, ins_cost)
        edit_distance: float = self.calculate_edit_distance_dp(dp, substring, target, del_cost, ins_cost, sub_cost)
        corresponding_texts: List[Union[str, Tuple[str, str]]]
        corresponding_characters: List[Union[str, Tuple[str, str]]]
        corresponding_texts, corresponding_characters = self.backtrack_corresponding(dp, _text, substring, target)

        text_res: List[str] = []
        pinyin_res: List[str] = []
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

        return LdRes(edit_distance, text_res, pinyin_res, corresponding_texts, corresponding_characters)


if __name__ == "__main__":
    lyric_pinyin_list = "xi nan dou bu jie bie ren zen me shuo wo dou bu jie yi wo ai bu ai ni ri jiu jian ren xin"
    text_content = "希 男 都 不 解 别 人 怎 么 说 我 都 不 解 一 我 爱 不 爱 你 日 久 见 人 心"
    lab_content = "xi lan ren zen ha ha shuo we dou bu jie"

    LD_Match = LevenshteinDistance()
    text, res, t_step, p_step = LD_Match.find_similar_substrings(lab_content.split(" "), lyric_pinyin_list.split(" "),
                                                                 text_list=text_content.split(" "), sub_tip=True)

    print("asr_labc:", lab_content)
    print("text_res:", text)
    print("pyin_res:", res)
    print("text_step:", t_step)
    print("pyin_step:", p_step)
    print()
