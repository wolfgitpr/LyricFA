import glob
import json
import os

import click
import pypinyin

from ZhG2p import ZhG2p
from common import LevenshteinDistance


def get_lyrics_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


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
@click.option('--asr_rectify', is_flag=False, metavar='Whether to rectify the ASR results.')
@click.option('--syllable_neglect',
              metavar='Ignore syllable errors with similar pronunciations and refer to the Near_systolic.yaml file.')
@click.option('--consonant_neglect',
              metavar='Ignore consonant errors with similar pronunciations and refer to the Near_systolic.yaml file.')
@click.option('--vowel_neglect',
              metavar='Ignore vowel errors with similar pronunciations and refer to the Near_systolic.yaml file.')
def match_lyric(
        lyric_folder: str = None,
        lab_folder: str = None,
        json_folder: str = None,
        diff_threshold: int = 0,
        asr_rectify: bool = False,
        syllable_neglect: bool = False,
        consonant_neglect: bool = False,
        vowel_neglect: bool = False
):
    assert lyric_folder is not None and lab_folder is not None, 'Missing lyrics or lab files.'
    assert json_folder is not None, 'JSON output folder not entered.'
    os.makedirs(json_folder, exist_ok=True)

    g2p = ZhG2p('mandarin')
    ld_match = LevenshteinDistance(load_yaml=True, syllable=syllable_neglect, consonant=consonant_neglect,
                                   vowel=vowel_neglect)
    lyric_dict = {}

    lyric_paths = glob.glob(f'{lyric_folder}/*.txt')
    for lyric_path in lyric_paths:
        lyric_name = os.path.splitext(os.path.basename(lyric_path))[0]
        text_list = g2p.split_string(get_lyrics_from_txt(lyric_path))
        lyric_dict[lyric_name] = {'text_list': text_list, 'pinyin': g2p.convert_list(text_list)}

    file_num = 0
    success_num = 0
    miss_lyric = []
    diff_num = 0
    asr_lab = glob.glob(f'{lab_folder}/*.lab')
    for lab_path in asr_lab:
        file_num += 1
        lab_name = os.path.splitext(os.path.basename(lab_path))[0]
        lyric_name = os.path.splitext(os.path.basename(lab_path))[0]
        lyric_name = lyric_name.rsplit("_", 1)[0]
        if lyric_name in lyric_dict.keys():
            with open(lab_path, 'r', encoding='utf-8') as f:
                asr_list = f.read().strip("\n").split(" ")
            text_list = lyric_dict[lyric_name]['text_list']
            pinyin_list = lyric_dict[lyric_name]['pinyin'].split(' ')
            if len(g2p.convert_list(asr_list).split(' ')) > 0:
                match_text, match_pinyin, text_step, pinyin_step = ld_match.find_similar_substrings(
                    g2p.convert_list(asr_list).split(' '), pinyin_list,
                    text_list=text_list, del_tip=True, ins_tip=True, sub_tip=True)
                asr_rectify = []
                for _asr, _text, _g2p in zip(asr_list, match_text.split(" "),
                                             match_pinyin.split(" ")):
                    if _asr != _g2p:
                        candidate = pypinyin.pinyin(_text, style=pypinyin.Style.NORMAL, heteronym=True)[0]
                        if _asr in candidate:
                            asr_rectify.append(_asr)
                        else:
                            asr_rectify.append(_g2p)
                    elif _asr == _g2p:
                        asr_rectify.append(_asr)

                if asr_rectify:
                    match_pinyin = " ".join(asr_rectify)

                if asr_list != match_pinyin.split(" ") and len(pinyin_step.split(" ")) > diff_threshold:
                    print("lab_name:", lab_name)
                    print("asr_lab:", " ".join(asr_list))
                    print("text_res:", match_text)
                    print("pyin_res:", match_pinyin)
                    print("text_step:", text_step)
                    print("pyin_step:", pinyin_step)
                    print("---------------")
                    diff_num += 1
                generate_json(f'{json_folder}/{lab_name}.json', match_text, match_pinyin)
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
