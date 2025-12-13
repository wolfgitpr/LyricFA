from typing import List, Tuple


def backtrack_alignment(
        sequence1: List[str],
        sequence2: List[str],
        dp_table: List[List[int]],
        backtrace_table: List[List[int]]
) -> Tuple[int, List[str], List[str]]:
    aligned_sequence1, aligned_sequence2 = [], []
    i, j = len(sequence1), len(sequence2)

    while i > 0 or j > 0:
        if i > 0 and j > 0 and backtrace_table[i][j] == 0:
            aligned_sequence1.insert(0, sequence1[i - 1])
            aligned_sequence2.insert(0, sequence2[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and backtrace_table[i][j] == 1:
            aligned_sequence1.insert(0, sequence1[i - 1])
            aligned_sequence2.insert(0, sequence2[j - 1])
            i -= 1
            j -= 1
        elif backtrace_table[i][j] == 2:
            aligned_sequence1.insert(0, sequence1[i - 1])
            aligned_sequence2.insert(0, "-")
            i -= 1
        else:
            aligned_sequence1.insert(0, "-")
            aligned_sequence2.insert(0, sequence2[j - 1] if j > 0 else "-")
            j -= 1

    return dp_table[len(sequence1)][len(sequence2)], aligned_sequence1, aligned_sequence2


class SequenceAligner:
    def __init__(self, deletion_cost: int = 1, insertion_cost: int = 1, substitution_cost: int = 1):
        self.deletion_cost = deletion_cost
        self.insertion_cost = insertion_cost
        self.substitution_cost = substitution_cost

    @staticmethod
    def compute_edit_distance(
            sequence1: List[str],
            sequence2: List[str]
    ) -> Tuple[int, List[str], List[str]]:
        len1, len2 = len(sequence1), len(sequence2)
        dp_table = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        backtrace_table = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            dp_table[i][0] = i
            backtrace_table[i][0] = 2
        for j in range(len2 + 1):
            dp_table[0][j] = j
            backtrace_table[0][j] = 3

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if sequence1[i - 1] == sequence2[j - 1]:
                    dp_table[i][j] = dp_table[i - 1][j - 1]
                    backtrace_table[i][j] = 0
                else:
                    substitution_cost = 1
                    deletion_cost = 1
                    insertion_cost = 1

                    substitution = dp_table[i - 1][j - 1] + substitution_cost
                    deletion = dp_table[i - 1][j] + deletion_cost
                    insertion = dp_table[i][j - 1] + insertion_cost

                    min_val = min(substitution, deletion, insertion)
                    dp_table[i][j] = min_val

                    if min_val == substitution:
                        backtrace_table[i][j] = 1
                    elif min_val == deletion:
                        backtrace_table[i][j] = 2
                    else:
                        backtrace_table[i][j] = 3

        return backtrack_alignment(sequence1, sequence2, dp_table, backtrace_table)

    def find_best_match_and_return_lyrics(
            self,
            input_pronunciation: List[str],
            reference_text: List[str],
            reference_pronunciation: List[str]
    ) -> Tuple[str, int, int]:
        if not input_pronunciation or not reference_pronunciation:
            return "", -1, -1

        input_length = len(input_pronunciation)
        reference_length = len(reference_pronunciation)

        if input_length > reference_length:
            return " ".join(reference_text), 0, reference_length

        window_size = min(2 * input_length, reference_length)
        best_start = 0
        min_edit_distance = float('inf')

        for start in range(0, reference_length - window_size + 1):
            window_end = start + window_size
            window_pinyin = reference_pronunciation[start:window_end]

            edit_distance, _, _ = self.compute_edit_distance(input_pronunciation, window_pinyin)

            if edit_distance < min_edit_distance:
                min_edit_distance = edit_distance
                best_start = start

        if min_edit_distance == float('inf'):
            return "", -1, -1

        window_end = best_start + window_size
        window_pinyin = reference_pronunciation[best_start:window_end]

        edit_distance, aligned_input, aligned_window = self.compute_edit_distance(input_pronunciation, window_pinyin)

        match_start_in_window = 0
        match_end_in_window = 0
        input_index = 0
        found_start = False

        for i in range(len(aligned_window)):
            if aligned_window[i] != '-' and aligned_input[i] != '-':
                if not found_start:
                    match_start_in_window = i
                    found_start = True
                match_end_in_window = i
                input_index += 1
                if input_index >= input_length:
                    break

        if not found_start:
            return "", -1, -1

        window_start_in_reference = best_start
        match_start_in_reference = window_start_in_reference + match_start_in_window
        match_end_in_reference = min(window_start_in_reference + match_end_in_window + 1, reference_length)

        matched_lyrics = reference_text[match_start_in_reference:match_end_in_reference]
        return " ".join(matched_lyrics), match_start_in_reference, match_end_in_reference


def calculate_difference_count(sequence1: List[str], sequence2: List[str]) -> int:
    min_length = min(len(sequence1), len(sequence2))
    max_length = max(len(sequence1), len(sequence2))

    diff_count = sum(1 for i in range(min_length) if sequence1[i] != sequence2[i])
    diff_count += max_length - min_length

    return diff_count


class SmartHighlighter:
    @staticmethod
    def highlight_differences(asr_result: str, match_phonetic: str, match_text: str) -> Tuple[str, str, str, int]:
        asr_tokens = asr_result.split()
        match_phonetic_tokens = match_phonetic.split()
        match_text_tokens = match_text.split()

        aligner = SequenceAligner()
        edit_operations, aligned_asr, aligned_match = aligner.compute_edit_distance(asr_tokens, match_phonetic_tokens)

        asr_highlighted = []
        phonetic_highlighted = []
        text_highlighted = []

        text_index = 0

        for i in range(len(aligned_asr)):
            asr_token = aligned_asr[i]
            match_token = aligned_match[i]

            text_token = ""
            if match_token != '-':
                if text_index < len(match_text_tokens):
                    text_token = match_text_tokens[text_index]
                    text_index += 1

            if asr_token == '-':
                phonetic_highlighted.append(f"({match_token})")
                asr_highlighted.append("")
                if text_token:
                    text_highlighted.append(f"({text_token})")
            elif match_token == '-':
                asr_highlighted.append(f"({asr_token})")
                phonetic_highlighted.append("")
                text_highlighted.append("")
            elif asr_token != match_token:
                asr_highlighted.append(f"({asr_token})")
                phonetic_highlighted.append(f"({match_token})")
                if text_token:
                    text_highlighted.append(f"({text_token})")
            else:
                asr_highlighted.append(asr_token)
                phonetic_highlighted.append(match_token)
                if text_token:
                    text_highlighted.append(text_token)

        asr_result_str = " ".join(filter(None, asr_highlighted))
        phonetic_result_str = " ".join(filter(None, phonetic_highlighted))
        text_result_str = " ".join(filter(None, text_highlighted))

        return asr_result_str, phonetic_result_str, text_result_str, edit_operations
