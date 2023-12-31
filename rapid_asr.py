import glob
import os
import time

import click
import librosa
from rapid_paraformer import RapidParaformer

from ZhG2p import ZhG2p, split_string


@click.command(help='Asr outputs lab annotations to match the original lyrics.')
@click.option('--model_config',
              metavar='sample:resources/config.yaml Download from: https://github.com/RapidAI/RapidASR/blob/main/python/README.md')
@click.option('--wav_folder', metavar='Sliced wav file folder(*.wav).')
@click.option('--lab_folder', metavar='Folder for outputting lab files.')
def rapid_asr(
        model_config: str = None,
        wav_folder: str = None,
        lab_folder: str = None
):
    assert model_config is not None, 'sample:resources/config.yaml Download from:https://github.com/RapidAI/RapidASR/blob/main/python/README.md'
    assert wav_folder is not None and lab_folder is not None, 'wav input folder or lab output folder not entered.'
    os.makedirs(lab_folder, exist_ok=True)

    paraformer = RapidParaformer(model_config)
    g2p = ZhG2p("mandarin")

    print("Started!")
    print("---------------")
    start_time = time.time()

    wav_list = glob.glob(wav_folder + '/*.wav')

    time_count = 0
    for wav_path in wav_list:
        time_count += librosa.get_duration(filename=wav_path)
        wav_name = os.path.splitext(os.path.basename(wav_path))[0]
        out_lab_path = f'{lab_folder}/{wav_name}.lab'
        if not os.path.exists(out_lab_path):
            y, sr = librosa.load(wav_path, sr=16000, mono=True)
            result = paraformer(y[None, ...])
            if result:
                result = result[0]
                print(f"{wav_path}\n{result}\n")
                with open(out_lab_path, 'w', encoding='utf-8') as f:
                    f.write(g2p.convert(result))
            else:
                print(f"{wav_path}:error\n")
        else:
            print(f"{out_lab_path} exists, skip\n")

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print("---------------")
    print("Done!")
    if time_count != 0:
        print(f"RTF: {elapsed_seconds / time_count:.3f}x")
    print(f"Wav time: {time_count:.3f}s")


if __name__ == '__main__':
    rapid_asr()
