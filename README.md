# LyricFA

## Intro

Using ASR to obtain syllables, matching text from lyrics, and generating JSON for Minlabel preloading.

## How to use

1. Install
    + Asr model from: https://github.com/RapidAI/RapidASR

    1. Install `rapid_paraformer`
        ```bash
        pip install rapid_paraformer
        ```
    2. Download **resources.zip
       ** ([Google Drive](https://drive.google.com/drive/folders/1RVQtMe0eB_k6G5TJlmXwPELx4VtF2oCw?usp=sharing) | [百度网盘](https://pan.baidu.com/s/1zf8Ta6QxFHY3Z75fHNYKrQ?pwd=6ekq))
        ```bash
        resources
        ├── [ 700]  config.yaml
        └── [4.0K]  models
            ├── [ 11K]  am.mvn
            ├── [824M]  asr_paraformerv2.onnx
            └── [ 50K]  token_list.pkl
        ```
2. Collect lyric
    1. Collect the original lyrics text and place it in the Lyric folder. The content is pure lyrics, and the file name
       is consistent with the audio before the AudioSlicer slicing (i.e. the part before the file name '_' after
       slicing)
       ```bash
       lyric
       ├── chuanqi.txt
       ├── caocao.txt
       └── ...
        ```

    2. Place the cut file fragments in the wav folder. Unify the file name with the previous lyrics: [lyricName]_xxx.wav.
   
       If there are multiple '_' in the file name, Take the far right as the dividing line. The file name in the left
       half must be the same as the lyrics file name in the previous step.
       ```bash
       wav
       ├── caocao_001.wav
       ├── caocao_002.wav
       └── ...
        ```

    3. Run rapid_asr.py obtains the lab results of asr.
        ```bash
       python rapid_asr.py --model_config resources/config.yaml --wav_folder wav_folder --lab_folder lab_folder
       
       Option:
           --model_config   sample:resources/config.yaml Download from: https://github.com/RapidAI/RapidASR/blob/main/python/README.md
           --wav_folder     Sliced wav file folder (*.wav).
           --lab_folder     Folder for outputting lab files.       
       ```

    4. Run match_lyric.py obtains JSON and put it in the annotation folder of Minlabel.
       ```bash
       python match_lyric.py --lyric_folder lyric --lab_folder lab_folder --json_folder json_folder
       
       Option:
           --model_config   The file name corresponds to the lab prefix (before \'_\'), only pure lyrics are allowed (*.txt).
           --lab_folder     Chinese characters or pinyin separated by spaces obtained from ASR (*.lab).
           --json_folder     Folder for outputting JSON files.       
       ```

## Open-source softwares used

+ [zh_CN](https://github.com/ZiQiangWang/zh_CN)
  The core algorithm source has been further tailored to the dictionary in this project.

+ [RapidASR](https://github.com/RapidAI/RapidASR)
  The test data source.

+ [cc-edict](https://cc-cedict.org/wiki/)
  The dictionary source.

