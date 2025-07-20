import glob
import json
import os

import click

from ZhG2p import split_string
from common import LyricAligner


def get_lyrics_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


def find_best_matches(source_list, sub_list):
    max_match_length = 0
    max_match_index = -1

    for i in range(len(source_list)):
        match_length = 0
        j = 0
        while i + j < len(source_list) and j < len(sub_list):
            if source_list[i + j] == sub_list[j]:
                match_length += 1
            j += 1

        if match_length > max_match_length:
            max_match_length = match_length
            max_match_index = i

    return max_match_index, max_match_index + len(sub_list)


def generate_json(json_path, _text, _pinyin):
    data = {"raw_text": _text, "lab": _pinyin, "lab_without_tone": _pinyin}
    json_str = json.dumps(data, ensure_ascii=False, indent=3)
    with open(json_path, 'w', encoding='utf-8') as _f:
        _f.write(json_str)


@click.command(help='Match the original lyrics based on the ASR results and generate JSON for preloading by Minlabel')
@click.option('--lyric_folder',
              metavar='The file name corresponds to the lab prefix (before \'_\'), only pure lyrics are allowed (*.txt).')
@click.option('--lab_folder', metavar='Chinese characters or pinyin separated by spaces obtained from ASR (*.lab).')
@click.option('--json_folder', metavar='Folder for outputting JSON files.')
@click.option('--diff_threshold', default=0, metavar='Only display different results with n words or more.')
def match_lyric(
        lyric_folder: str = None,
        lab_folder: str = None,
        json_folder: str = None,
        diff_threshold: int = 0
):
    assert lyric_folder is not None and lab_folder is not None, 'Missing lyrics or lab files.'
    assert json_folder is not None, 'JSON output folder not entered.'
    os.makedirs(json_folder, exist_ok=True)

    aligner = LyricAligner()
    lyric_dict = {}

    lyric_paths = glob.glob(f'{lyric_folder}/*.txt')
    for lyric_path in lyric_paths:
        lyric_name = os.path.splitext(os.path.basename(lyric_path))[0]
        words = split_string(get_lyrics_from_txt(lyric_path).replace("’", "'").lower())
        lyric_dict[lyric_name] = {'text_list': words,
                                  'words': words}

    file_num = 0
    success_num = 0
    diff_num = 0
    miss_lyric = []
    asr_lab = glob.glob(f'{lab_folder}/*.lab')
    for lab_path in asr_lab:
        file_num += 1
        lab_name = os.path.splitext(os.path.basename(lab_path))[0]
        lyric_name = os.path.splitext(os.path.basename(lab_path))[0]
        lyric_name = lyric_name.rsplit("_", 1)[0]
        if lyric_name in lyric_dict.keys():
            with open(lab_path, 'r', encoding='utf-8') as f:
                lab_content = f.read()
            text_list = lyric_dict[lyric_name]['text_list']
            word_list = lyric_dict[lyric_name]['words']
            lab_word = split_string(lab_content.replace("’", "'").lower())
            if len(lab_word) > 0:
                match_text, match_kana, text_step, kana_step = aligner.align_sequences(search_text=lab_word,
                                                                                       search_pronunciation=lab_word,
                                                                                       reference_pronunciation=word_list,
                                                                                       show_substitutions=True,
                                                                                       show_insertions=True,
                                                                                       show_deletions=True)
                if lab_content != match_kana and len(kana_step.split(" ")) > diff_threshold:
                    print("lab_name:", lab_name)
                    print("asr_labc:", " ".join(lab_word))
                    print("text_res:", match_text)
                    print("text_step:", text_step)
                    print("---------------")
                    diff_num += 1
                generate_json(f'{json_folder}/{lab_name}.json', match_text, match_kana)
                success_num += 1
        else:
            if lyric_name not in miss_lyric:
                miss_lyric.append(lyric_name)

    if miss_lyric:
        print(f'miss lyrics: {miss_lyric}')
    print(f'{diff_num} files are different from the original lyrics.')
    print(f'{file_num} file in total, {success_num} success file.')


if __name__ == '__main__':
    match_lyric()
