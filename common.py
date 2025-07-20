from typing import List, Tuple, Union, Optional


class AlignmentResult:
    def __init__(self, start_idx: int, end_idx: int, text_changes: List[str], pronunciation_changes: List[str]):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.text_changes = text_changes
        self.pronunciation_changes = pronunciation_changes


class AlignmentDetails:
    def __init__(self, edit_distance, aligned_text, aligned_pronunciation, text_operations, pronunciation_operations):
        self.edit_distance = edit_distance
        self.aligned_text = aligned_text
        self.aligned_pronunciation = aligned_pronunciation
        self.text_operations = text_operations
        self.pronunciation_operations = pronunciation_operations


def longestCommonSubsequence(str1, str2) -> int:
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = 1 + dp[i - 1][j - 1]
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[-1][-1]


class LyricAligner:
    @staticmethod
    def find_longest_match(
            text_tokens: List[str],
            pronunciation_sequence: List[str],
            search_pronunciation: List[str],
            search_text: List[str]
    ) -> AlignmentResult:
        max_match_len = 0
        best_start_idx = -1

        for start_idx in range(len(pronunciation_sequence) - len(search_pronunciation)):
            current_match_len = longestCommonSubsequence(search_pronunciation,
                                                         pronunciation_sequence[
                                                         start_idx:start_idx + len(search_pronunciation)])

            if current_match_len >= max_match_len:
                max_match_len = current_match_len
                best_start_idx = start_idx

        # Ensure we have a valid match window
        max_match_len = min(len(pronunciation_sequence) - best_start_idx, len(search_pronunciation))
        if max_match_len < len(search_pronunciation):
            best_start_idx = max(0, best_start_idx - (len(search_pronunciation) - max_match_len))
            max_match_len = min(len(pronunciation_sequence) - best_start_idx, len(search_pronunciation))

        if best_start_idx == -1:
            best_start_idx = 0
            max_match_len = len(search_pronunciation)

        text_diffs = []
        pronunciation_diffs = []
        for pos in range(len(search_pronunciation)):
            if pos < max_match_len and pronunciation_sequence[best_start_idx + pos] != search_pronunciation[pos]:
                text_diffs.append(f"({search_text[pos]}->{text_tokens[best_start_idx + pos]}, {pos})")
                pronunciation_diffs.append(
                    f"({search_pronunciation[pos]}->{pronunciation_sequence[best_start_idx + pos]}, {pos})")

        return AlignmentResult(
            start_idx=best_start_idx,
            end_idx=best_start_idx + max_match_len,
            text_changes=text_diffs,
            pronunciation_changes=pronunciation_diffs
        )

    def align_sequences(
            self,
            search_text: List[str],
            search_pronunciation: List[str],
            reference_pronunciation: List[str],
            text_tokens: Optional[List[str]] = None,
            show_deletions: bool = False,
            show_insertions: bool = False,
            show_substitutions: bool = False
    ) -> Tuple[str, str, str, str]:
        if text_tokens is None:
            text_tokens = reference_pronunciation
        assert len(search_pronunciation) <= len(reference_pronunciation)
        assert len(text_tokens) == len(reference_pronunciation)

        initial_match = self.find_longest_match(text_tokens, reference_pronunciation, search_pronunciation, search_text)
        matched_pronunciation = reference_pronunciation[initial_match.start_idx:initial_match.end_idx]

        # Check if initial match is acceptable
        if matched_pronunciation and (
                matched_pronunciation[0] == search_pronunciation[0] or matched_pronunciation[-1] ==
                search_pronunciation[-1]) and len(
            initial_match.text_changes) <= 1:
            return (
                " ".join(text_tokens[initial_match.start_idx:initial_match.end_idx]),
                " ".join(reference_pronunciation[initial_match.start_idx:initial_match.end_idx]),
                " ".join(initial_match.text_changes),
                " ".join(initial_match.pronunciation_changes)
            )

        # Find the best alignment using edit distance
        alignment_candidates = []
        window_size = len(search_pronunciation)

        # Expand search window around initial match
        for window in range(window_size, min(window_size + 10, len(reference_pronunciation) + 1)):
            start_range = max(0, initial_match.start_idx - 10)
            end_range = min(initial_match.end_idx + 10, len(reference_pronunciation) - window + 1)

            for start_idx in range(start_range, end_range):
                window_pronunciation = reference_pronunciation[start_idx:start_idx + window]
                window_text = text_tokens[start_idx:start_idx + window]

                alignment_candidates.append(self.compute_alignment_details(
                    window_text, window_pronunciation, search_pronunciation, search_text))

        # Select best candidate
        alignment_candidates.sort(key=lambda x: x.edit_distance)
        best_alignment = alignment_candidates[0]

        return (
            " ".join(best_alignment.aligned_text),
            " ".join(best_alignment.aligned_pronunciation),
            self.format_operations(best_alignment.text_operations, show_deletions, show_insertions, show_substitutions),
            self.format_operations(best_alignment.pronunciation_operations, show_deletions, show_insertions,
                                   show_substitutions)
        )

    @staticmethod
    def format_operations(
            operations: List[Union[str, Tuple[str, str]]],
            show_del: bool,
            show_ins: bool,
            show_sub: bool
    ) -> str:
        formatted_ops = []
        for pos, op in enumerate(operations):
            if isinstance(op, tuple):
                original, replacement = op
                if original and not replacement and show_del:
                    formatted_ops.append(f"({original}->, {pos})")
                elif not original and replacement and show_ins:
                    formatted_ops.append(f"(->{replacement}, {pos})")
                elif original and replacement and show_sub:
                    formatted_ops.append(f"({replacement}->{original}, {pos})")
        return " ".join(formatted_ops)

    @staticmethod
    def create_dp_table(
            rows: int,
            cols: int,
            del_cost: int,
            ins_cost: int
    ) -> List[List[int]]:
        dp = [[0] * (cols + 1) for _ in range(rows + 1)]

        for i in range(rows + 1):
            dp[i][0] = i * del_cost

        for j in range(cols + 1):
            dp[0][j] = j * ins_cost

        return dp

    @staticmethod
    def fill_dp_table(
            dp: List[List[int]],
            source: List[str],
            target: List[str],
            del_cost: int,
            ins_cost: int,
            sub_cost: int
    ) -> int:
        rows, cols = len(source), len(target)

        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                if source[i - 1] == target[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j - 1] + sub_cost,
                        dp[i][j - 1] + ins_cost,
                        dp[i - 1][j] + del_cost
                    )

        return dp[rows][cols]

    @staticmethod
    def trace_alignment_path(
            dp: List[List[float]],
            text_tokens: List[str],
            source_pronunciation: List[str],
            target_pronunciation: List[str],
            search_text: List[str]
    ) -> Tuple[List[Union[str, Tuple[str, str]]], List[Union[str, Tuple[str, str]]]]:
        text_ops = []
        pronunciation_ops = []
        i, j = len(source_pronunciation), len(target_pronunciation)

        while i > 0 and j > 0:
            if source_pronunciation[i - 1] == target_pronunciation[j - 1]:
                pronunciation_ops.insert(0, target_pronunciation[j - 1])
                text_ops.insert(0, text_tokens[i - 1])
                i -= 1
                j -= 1
            else:
                min_val = min(dp[i - 1][j - 1], dp[i][j - 1], dp[i - 1][j])
                if dp[i - 1][j - 1] == min_val:
                    pronunciation_ops.insert(0, (source_pronunciation[i - 1], target_pronunciation[j - 1]))
                    text_ops.insert(0, (text_tokens[i - 1], search_text[j - 1]))
                    i -= 1
                    j -= 1
                elif dp[i][j - 1] == min_val:
                    pronunciation_ops.insert(0, ('', target_pronunciation[j - 1]))
                    text_ops.insert(0, ('', search_text[j - 1]))
                    j -= 1
                else:
                    pronunciation_ops.insert(0, (source_pronunciation[i - 1], ''))
                    text_ops.insert(0, (text_tokens[i - 1], ''))
                    i -= 1

        return text_ops, pronunciation_ops

    def compute_alignment_details(
            self,
            text_tokens: List[str],
            source_pronunciation: List[str],
            target_pronunciation: List[str],
            search_text: List[str],
            del_cost: int = 1,
            ins_cost: int = 3,
            sub_cost: int = 3
    ) -> AlignmentDetails:
        rows, cols = len(source_pronunciation), len(target_pronunciation)
        dp = self.create_dp_table(rows, cols, del_cost, ins_cost)
        edit_dist = self.fill_dp_table(dp, source_pronunciation, target_pronunciation, del_cost, ins_cost, sub_cost)
        text_ops, pronunciation_ops = self.trace_alignment_path(dp, text_tokens, source_pronunciation,
                                                                target_pronunciation, search_text)

        aligned_text = []
        aligned_pronunciation = []
        for p_op, t_op in zip(pronunciation_ops, text_ops):
            if isinstance(p_op, str):
                aligned_pronunciation.append(p_op)
                aligned_text.append(t_op)
            elif p_op[0] == '' and p_op[1] != '':
                aligned_pronunciation.append(p_op[1])
                aligned_text.append(t_op[1])
            elif p_op[0] != '' and p_op[1] != '':
                aligned_pronunciation.append(p_op[0])
                aligned_text.append(t_op[0])

        return AlignmentDetails(edit_dist, aligned_text, aligned_pronunciation, text_ops, pronunciation_ops)


if __name__ == "__main__":
    g2p_pinyin = "xi nan dou bu jie bie ren zen me shuo wo dou bu jie yi wo ai bu ai ni ri jiu jian ren xin".split()
    reference_text = "希 男 都 不 解 别 人 怎 么 说 我 都 不 解 一 我 爱 不 爱 你 日 久 见 人 心".split()
    input_pinyin = "xi lan ren zen ha ha shuo we dou bu jie".split()

    aligner = LyricAligner()
    text, pinyin, text_diff, pinyin_diff = aligner.align_sequences(
        input_pinyin, input_pinyin, g2p_pinyin, text_tokens=reference_text, show_substitutions=True
    )

    print("Input Pinyin:", " ".join(input_pinyin))
    print("Aligned Text:", text)
    print("Aligned Pinyin:", pinyin)
    print("Text Operations:", text_diff)
    print("Pinyin Operations:", pinyin_diff)
