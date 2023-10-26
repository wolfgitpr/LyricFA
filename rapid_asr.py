import glob
import os
import time

import click
import librosa
from rapid_paraformer import RapidParaformer

from Zh_G2p import ZhG2p


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
        y, sr = librosa.load(wav_path, sr=16000, mono=True)
        result = paraformer(y[None, ...])[0]
        print(f"{wav_path}\n{result}\n")
        wav_name = os.path.splitext(os.path.basename(wav_path))[0]
        with open(f'{lab_folder}/{wav_name}.lab', 'w') as f:
            f.write(g2p.convert_string(result))

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print("---------------")
    print("Done!")
    print(f"Wav time: {time_count:.3f} s")
    print(f"Asr cost time: {elapsed_seconds:.3f} s")


if __name__ == '__main__':
    rapid_asr()
