import sys
import os
from pprint import pprint
from getpass import getpass
from StringIO import StringIO
from wit import Wit

try:
    import pyaudio
except ImportError:
    print('Error: Make sure you install PyAudio before running this example.')
    sys.exit()


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 3
# Change this based on your OSes settings. This should work for OSX, though.
ENDIAN = 'little'
CONTENT_TYPE = \
    'raw;encoding=signed-integer;bits=16;rate={0};endian={1}'.format(
        RATE, ENDIAN)


def record_and_stream():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE,
        input=True, frames_per_buffer=CHUNK)

    print("* recording and streaming")

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        yield stream.read(CHUNK)

    print("* done recording and streaming")

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == '__main__':
    output_file = StringIO()
    if 'WIT_ACCESS_TOKEN' not in os.environ:
        os.environ['WIT_ACCESS_TOKEN'] = getpass('Enter Wit Access Token: ')
    wit_token = os.environ['WIT_ACCESS_TOKEN']

    w = Wit(wit_token)
    result = w.post_speech(record_and_stream(), content_type=CONTENT_TYPE)
    pprint(result)