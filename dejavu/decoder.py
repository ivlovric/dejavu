from __future__ import absolute_import
import os
import fnmatch
import numpy as np
from pydub import AudioSegment
from pydub.utils import audioop
from . import wavio
from hashlib import sha1
import logging
import magic
import io

l = logging.getLogger("pydub")
##l = logging.getLogger("magic")
#l.setLevel(logging.DEBUG)
#l.addHandler(logging.StreamHandler())

def unique_hash(filepath, blocksize=2**20):
    """ Small function to generate a hash to uniquely generate
    a file. Inspired by MD5 version here:
    http://stackoverflow.com/a/1131255/712997

    Works with large files.
    """
    s = sha1()
    with open(filepath, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            s.update(buf)
    return s.hexdigest().upper()


def find_files(path, extensions):
    # Allow both with ".mp3" and without "mp3" to be used for extensions
    extensions = [e.replace(".", "") for e in extensions]

    for dirpath, dirnames, files in os.walk(path):
        for extension in extensions:
            for f in fnmatch.filter(files, "*.%s" % extension):
                p = os.path.join(dirpath, f)
                yield (p, extension)


def read(filename, limit=None):
    """
    Reads any file supported by pydub (ffmpeg) and returns the data contained
    within. If file reading fails due to input being a 24-bit wav file,
    wavio is used as a backup.

    Can be optionally limited to a certain amount of seconds from the start
    of the file by specifying the `limit` parameter. This is the amount of
    seconds from the start of the file.

    returns: (channels, samplerate)
    """
    # pydub does not support 24-bit wav files, use wavio when this occurs
    try:
        try:
            audiofile = AudioSegment.from_file(filename)
            #print("API data %s", audiofile._data)
            print(type(filename))

            try:
                filetype = magic.from_file(filename)
                l.info(filetype)

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                l.info(f"Unexpected {err=}, {type(err)=}")

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            l.info(f"Unexpected {err=}, {type(err)=}")
        
        if limit:
            audiofile = audiofile[:int(limit) * 1000]

        data = np.fromstring(audiofile._data, np.int16)

        channels = []
        for chn in range(audiofile.channels):
            channels.append(data[chn::audiofile.channels])

        fs = audiofile.frame_rate
    except audioop.error:
        fs, _, audiofile = wavio.readwav(filename)

        if limit:
            audiofile = audiofile[:limit * 1000]

        audiofile = audiofile.T
        audiofile = audiofile.astype(np.int16)

        channels = []
        for chn in audiofile:
            channels.append(chn)

    return channels, audiofile.frame_rate

def read_api(api_data, limit=None):
    """
    Reads any file supported by pydub (ffmpeg) and returns the data contained
    within. If file reading fails due to input being a 24-bit wav file,
    wavio is used as a backup.

    Can be optionally limited to a certain amount of seconds from the start
    of the file by specifying the `limit` parameter. This is the amount of
    seconds from the start of the file.

    returns: (channels, samplerate)
    """
    # pydub does not support 24-bit wav files, use wavio when this occurs

    try:

        try:
            print(len(api_data))
            print(type(api_data))
            #print(api_data[0:7000])

            try:
                filetype = magic.from_buffer(api_data)
                l.info(filetype)
            except Exception as err:
                l.info(f"Unexpected {err=}, {type(err)=}")

            audiofile = AudioSegment.from_file(io.BytesIO(api_data))
            #audiofile = AudioSegment.from_raw(io.BytesIO(api_data) , sample_width=2, frame_rate=8000, channels=1 )

            print("Frame rate:", audiofile.frame_rate)
            print("Channels:", audiofile.channels)
            print("Sample width:", audiofile.sample_width)

        except Exception as err:
            l.info(f"Unexpected {err=}, {type(err)=}")
            audiofile = AudioSegment.from_raw(io.BytesIO(api_data) , sample_width=2, frame_rate=8000, channels=1 )


        if limit:
            audiofile = audiofile[:int(limit) * 1000]

        data = np.fromstring(audiofile._data, np.int16)
        #data = np.frombuffer(audiofile, np.int16)

        channels = []
        for chn in range(audiofile.channels):
            channels.append(data[chn::audiofile.channels])
        #channels = data

        fs = audiofile.frame_rate
        #fs = 44100
    except audioop.error:
        fs, _, audiofile = wavio.readwav(api_data)

        if limit:
            audiofile = audiofile[:limit * 1000]

        audiofile = audiofile.T
        audiofile = audiofile.astype(np.int16)

        channels = []
        for chn in audiofile:
            channels.append(chn)

    #return channels, audiofile.frame_rate
    return channels, fs

def read_ws(ws_data, limit=None):
    """
    Reads any file supported by pydub (ffmpeg) and returns the data contained
    within. If file reading fails due to input being a 24-bit wav file,
    wavio is used as a backup.

    Can be optionally limited to a certain amount of seconds from the start
    of the file by specifying the `limit` parameter. This is the amount of
    seconds from the start of the file.

    returns: (channels, samplerate)
    """
    # pydub does not support 24-bit wav files, use wavio when this occurs

    try:

        try:
            print(len(ws_data))
            print(type(ws_data))

            try:
                filetype = magic.from_buffer(ws_data)
                l.info(filetype)
            except Exception as err:
                l.info(f"Unexpected {err=}, {type(err)=}")

            try:  
                #audiofile = AudioSegment(bytes(ws_data))
                audiofile = AudioSegment.from_file(io.BytesIO(ws_data))
            except Exception as e:
                print("Audio has no media info, trying to force %s", e)
                audiofile = AudioSegment.from_file(io.BytesIO(ws_data) , sample_width=2, frame_rate=8000, channels=1)

            print("Frame rate:", audiofile.frame_rate)
            print("Channels:", audiofile.channels)
            print("Sample width:", audiofile.sample_width)
                
            data = np.fromstring(audiofile._data, np.int16)
                #data = np.frombuffer(audiofile, np.int16)

            channels = []
            for chn in range(audiofile.channels):
                channels.append(data[chn::audiofile.channels])
                #channels = data

            #fs = audiofile.frame_rate
            fs = 44100

            if limit:
                audiofile = audiofile[:int(limit) * 1000]

        except Exception as e:
            channels = 0
            fs = 0
            print(e)

    except audioop.error:
        try:
            fs, _, audiofile = wavio.readwav(ws_data)
        except Exception as e:
            print(e)

        if limit:
            audiofile = audiofile[:limit * 1000]

        audiofile = audiofile.T
        audiofile = audiofile.astype(np.int16)

        channels = []
        for chn in audiofile:
            channels.append(chn)

    #return channels, audiofile.frame_rate
 
    return channels, fs


def path_to_songname(path):
    """
    Extracts song name from a filepath. Used to identify which songs
    have already been fingerprinted on disk.
    """
    return os.path.splitext(os.path.basename(path))[0]
