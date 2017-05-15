import pyaudio
import wave
import os
import time


def play_sound_file(sound_file):

    ding_wav = wave.open(sound_file, 'rb')
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(), input=False, output=True)
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()


def play_ding():
    play_sound_file(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../resources/sounds/ding.wav"))


def play_dong():
    play_sound_file(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../resources/sounds/dong.wav"))


def play_ding_dong():
    ding_wav = wave.open(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../resources/sounds/dong.wav"), 'rb')
    dong_wav = wave.open(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../resources/sounds/dong.wav"), 'rb')
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    dong_data = dong_wav.readframes(dong_wav.getnframes())
    audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(), input=False, output=True)
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.write(dong_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()
