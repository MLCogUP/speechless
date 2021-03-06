from scipy.io import wavfile
from audio import mel_powerlevel_spectrogram
import numpy as np
import datetime
import subprocess
import os
import io
import sys
from speechless.labeled_example import LabeledExample, LabeledExampleFromFile
from pathlib import Path

import librosa

from speechless.configuration import Configuration

def test_sample():

    filename = 'ALC_0062014047_h_00.wav'

    wav2letter = Configuration.german().load_best_german_model()
    data = librosa.load(filename, sr=16000)[0]

    ex = LabeledExample(get_raw_audio=lambda: data)
    feed_speechless(wav2letter, ex)

def get_wav():
    if args.video:
        filename = args.filename + '.wav'
        command = 'avconv  -i {} -ac 1 -ar 16000 -vn {}.wav'.format(args.filename, args.filename)
        subprocess.call(command, shell=True)
    else:
        filename = args.filename
    return filename

def process_audio():
    filename = get_wav()

    wav2letter = Configuration.german_tib(args.tib_train, args.augment).load_best_tib_model(args.tib_train, args.augment)

    segments = process_wav(filename)
    for idx, segment in enumerate(segments):
        print("[{}]".format(str(datetime.timedelta(seconds=idx * 10))))
        ex = LabeledExample(get_raw_audio=lambda: segment)
        feed_speechless(wav2letter, ex)

    os.remove(filename)

def process_wav(filename, chunk_len=10.0, overlap_len=0.5, rate=16000):
    data = librosa.load(filename, sr=rate)[0]

    if 1.0 * len(data) / rate > chunk_len:
        # segment into 10-second chunks with 1-second overlap
        window_length = int(rate * (chunk_len + overlap_len))
        stride = int(chunk_len * rate)
        segments = rolling_window(data, window_length, stride)
    else:
        segments = [data]

    print(len(segments))
    return segments

def feed_speechless(wav2letter, sg):
    prediction = wav2letter.predict(sg)
    print(prediction)

def feed_model(network, sg):
    predictions = cnn.apply_network(network, sg)
    chars = cnn.look_up_chars(cnn.condense(predictions[0]), language='german')
    out = ''.join(chars)
    sys.stdout.buffer.write(out.encode('utf8'))
    sys.stdout.write("\n")
    print('Decoded:')
    decoded = cnn.kenlm_decode(predictions.swapaxes(0, 1), beam_width=30)
    sys.stdout.buffer.write("".join(cnn.look_up_chars(decoded, language='english')).encode('utf8'))
    sys.stdout.write("\n")

def rolling_window(data, length, stride):
    starts = range(0, len(data), stride)
    return [data[start:(start + length)] for start in starts] 

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='ASR demo')
    parser.add_argument('--video', '-v', action='store_true', help='input is a video file')
    parser.add_argument('--filename', '-f', help='file containing audio')

    parser.add_argument('--augment', '-a', action='store_true', help='use augmented model')
    parser.add_argument('--tib_train', '-t', action='store_true', help='use model trained on TIB'
    args = parser.parse_args()
    process_audio()
