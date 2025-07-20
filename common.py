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


def longestCommonSubsequence(seq1: List[str], seq2: List[str]) -> int:
    len1, len2 = len(seq1), len(seq2)
    dp_table = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp_table[i][j] = 1 + dp_table[i - 1][j - 1]
            else:
                dp_table[i][j] = max(dp_table[i - 1][j], dp_table[i][j - 1])

    return dp_table[-1][-1]


class LyricAligner:
    @staticmethod
    def find_best_match_window(
            reference_text_tokens: List[str],
            reference_pronunciation: List[str],
            search_pronunciation: List[str],
            search_text: List[str]
    ) -> AlignmentResult:
        max_match_length = 0
        best_start_idx = -1

        for start_idx in range(len(reference_pronunciation) - len(search_pronunciation)):
            current_match_length = longestCommonSubsequence(
                search_pronunciation,
                reference_pronunciation[start_idx:start_idx + len(search_pronunciation)]
            )

            if current_match_length >= max_match_length:
                max_match_length = current_match_length
                best_start_idx = start_idx

        max_match_length = min(len(reference_pronunciation) - best_start_idx, len(search_pronunciation))
        if max_match_length < len(search_pronunciation):
            best_start_idx = max(0, best_start_idx - (len(search_pronunciation) - max_match_length))
            max_match_length = min(len(reference_pronunciation) - best_start_idx, len(search_pronunciation))

        if best_start_idx == -1:
            best_start_idx = 0
            max_match_length = len(search_pronunciation)

        text_diffs = []
        pronunciation_diffs = []
        for position in range(len(search_pronunciation)):
            if (position < max_match_length and
                    reference_pronunciation[best_start_idx + position] != search_pronunciation[position]):
                text_diffs.append(
                    f"({search_text[position]}->{reference_text_tokens[best_start_idx + position]}, {position})")
                pronunciation_diffs.append(
                    f"({search_pronunciation[position]}->{reference_pronunciation[best_start_idx + position]}, {position})")

        return AlignmentResult(
            start_idx=best_start_idx,
            end_idx=best_start_idx + max_match_length,
            text_changes=text_diffs,
            pronunciation_changes=pronunciation_diffs
        )

    def align_sequences(
            self,
            search_text: List[str],
            search_pronunciation: List[str],
            reference_pronunciation: List[str],
            reference_text: Optional[List[str]] = None,
            show_deletions: bool = False,
            show_insertions: bool = False,
            show_substitutions: bool = False
    ) -> Tuple[str, str, str, str]:
        if reference_text is None:
            reference_text = reference_pronunciation
        assert len(search_pronunciation) <= len(reference_pronunciation)
        assert len(reference_text) == len(reference_pronunciation)

        initial_match = self.find_best_match_window(
            reference_text, reference_pronunciation, search_pronunciation, search_text
        )
        matched_pronunciation = reference_pronunciation[initial_match.start_idx:initial_match.end_idx]

        # Check if initial match is acceptable
        if matched_pronunciation and (
                matched_pronunciation[0] == search_pronunciation[0] or matched_pronunciation[-1] ==
                search_pronunciation[-1]) and len(
            initial_match.text_changes) <= 1:
            return (
                " ".join(reference_text[initial_match.start_idx:initial_match.end_idx]),
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
                window_text = reference_text[start_idx:start_idx + window]

                alignment_candidates.append(self.compute_alignment_details(
                    window_text, window_pronunciation, search_pronunciation, search_text))

        # Select best candidate
        alignment_candidates.sort(key=lambda candidate: candidate.edit_distance)
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
        for position, op in enumerate(operations):
            if isinstance(op, tuple):
                original, replacement = op
                if original and not replacement and show_del:
                    formatted_ops.append(f"({original}->, {position})")
                elif not original and replacement and show_ins:
                    formatted_ops.append(f"(->{replacement}, {position})")
                elif original and replacement and show_sub:
                    formatted_ops.append(f"({replacement}->{original}, {position})")
        return " ".join(formatted_ops)

    @staticmethod
    def create_dp_table(
            rows: int,
            cols: int,
            deletion_cost: int,
            insertion_cost: int
    ) -> List[List[int]]:
        dp_table = [[0] * (cols + 1) for _ in range(rows + 1)]

        for i in range(rows + 1):
            dp_table[i][0] = i * deletion_cost
        for j in range(cols + 1):
            dp_table[0][j] = j * insertion_cost

        return dp_table

    @staticmethod
    def fill_dp_table(
            dp_table: List[List[int]],
            source_seq: List[str],
            target_seq: List[str],
            deletion_cost: int,
            insertion_cost: int,
            substitution_cost: int
    ) -> int:
        rows, cols = len(source_seq), len(target_seq)

        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                if source_seq[i - 1] == target_seq[j - 1]:
                    dp_table[i][j] = dp_table[i - 1][j - 1]
                else:
                    dp_table[i][j] = min(
                        dp_table[i - 1][j - 1] + substitution_cost,
                        dp_table[i][j - 1] + insertion_cost,
                        dp_table[i - 1][j] + deletion_cost
                    )

        return dp_table[rows][cols]

    @staticmethod
    def trace_alignment_path(
            dp_table: List[List[float]],
            reference_text_tokens: List[str],
            source_pronunciation: List[str],
            target_pronunciation: List[str],
            search_text: List[str]
    ) -> Tuple[List[Union[str, Tuple[str, str]]], List[Union[str, Tuple[str, str]]]]:
        text_operations = []
        pronunciation_operations = []
        i, j = len(source_pronunciation), len(target_pronunciation)

        while i > 0 and j > 0:
            if source_pronunciation[i - 1] == target_pronunciation[j - 1]:
                pronunciation_operations.insert(0, target_pronunciation[j - 1])
                text_operations.insert(0, reference_text_tokens[i - 1])
                i -= 1
                j -= 1
            else:
                min_val = min(dp_table[i - 1][j - 1], dp_table[i][j - 1], dp_table[i - 1][j])
                if dp_table[i - 1][j - 1] == min_val:
                    pronunciation_operations.insert(0, (source_pronunciation[i - 1], target_pronunciation[j - 1]))
                    text_operations.insert(0, (reference_text_tokens[i - 1], search_text[j - 1]))
                    i -= 1
                    j -= 1
                elif dp_table[i][j - 1] == min_val:
                    pronunciation_operations.insert(0, ('', target_pronunciation[j - 1]))
                    text_operations.insert(0, ('', search_text[j - 1]))
                    j -= 1
                else:
                    pronunciation_operations.insert(0, (source_pronunciation[i - 1], ''))
                    text_operations.insert(0, (reference_text_tokens[i - 1], ''))
                    i -= 1

        return text_operations, pronunciation_operations

    def compute_alignment_details(
            self,
            reference_text_tokens: List[str],
            source_pronunciation: List[str],
            target_pronunciation: List[str],
            search_text: List[str],
            deletion_cost: int = 1,
            insertion_cost: int = 3,
            substitution_cost: int = 3
    ) -> AlignmentDetails:
        rows, cols = len(source_pronunciation), len(target_pronunciation)
        dp_table = self.create_dp_table(rows, cols, deletion_cost, insertion_cost)
        edit_distance = self.fill_dp_table(
            dp_table, source_pronunciation, target_pronunciation, deletion_cost, insertion_cost, substitution_cost
        )
        text_ops, pronunciation_ops = self.trace_alignment_path(
            dp_table, reference_text_tokens, source_pronunciation, target_pronunciation, search_text
        )

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
        return AlignmentDetails(edit_distance, aligned_text, aligned_pronunciation, text_ops, pronunciation_ops)


if __name__ == "__main__":
    # 示例用法
    g2p_pinyin = "xi nan dou bu jie bie ren zen me shuo wo dou bu jie yi wo ai bu ai ni ri jiu jian ren xin".split()
    lyrics = "希 男 都 不 解 别 人 怎 么 说 我 都 不 解 一 我 爱 不 爱 你 日 久 见 人 心".split()
    input_pinyin = "xi lan ren zen ha ha shuo we dou bu jie".split()

    aligner = LyricAligner()
    text, pinyin, text_diff, pinyin_diff = aligner.align_sequences(
        input_pinyin, input_pinyin, g2p_pinyin, reference_text=lyrics, show_substitutions=True
    )

    print("输入拼音:", " ".join(input_pinyin))
    print("对齐文本:", text)
    print("对齐拼音:", pinyin)
    print("文本操作:", text_diff)
    print("拼音操作:", pinyin_diff)
