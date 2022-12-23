#!/usr/bin/python

import os
import sys
import warnings
import argparse

from flask import Flask, jsonify, request, current_app, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
#from werkzeug.datastructures import  FileStorage
import magic
#import pandas as pd
import logging

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer
from dejavu.recognize import MicrophoneRecognizer
from dejavu.recognize import APIRecognizer

from dejavu.version import __version__
from argparse import RawTextHelpFormatter

warnings.filterwarnings("ignore")


app = Flask(__name__)
app.config.from_object(__name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','mp3'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # check if the post request has the file part

    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file = request.files.get('file') 
        filetype = magic.from_buffer(file.read(1024))
        ###########print (file.read())
        #djv.fingerprint_API(file.read())
        print("running API recognizer")
        #song = djv.recognize(FileRecognizer)
        song = djv.recognize(APIRecognizer,file.read())
        resp = jsonify({'message' : song})
        resp.status_code = 201
        return resp

    else:
        resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
        resp.status_code = 400
        return resp

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Dejavu: Audio Fingerprinting library",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        '-d',
        '--dburl',
        nargs='?',
        default=None,
        help='Database URL to use. As supported by SQLAlchemy (RFC-1738). '
             'Will read $DATABASE_URL env var if not specified\n'
        'Usages: \n'
        '--dburl mysql://user:pass@localhost/database\n'
    )
    parser.add_argument(
        '-f',
        '--fingerprint',
        nargs='*',
        help='Fingerprint files in a directory\n'
        'Usages: \n'
        '--fingerprint /path/to/directory extension\n'
        '--fingerprint /path/to/directory'
    )
    parser.add_argument(
        '-r',
        '--recognize',
        nargs=2,
        help='Recognize what is playing through the microphone or file\n'
        'Usage: \n'
        '--recognize mic number_of_seconds \n'
        '--recognize file path/to/file \n'
    )
    parser.add_argument(
        '-n',
        '--network',
        nargs=1,
        help='Recognize what is sent over HTTP\n'
        'Usage: \n'
        '--network API data\n'

    )
    parser.add_argument(
        '-l',
        '--limit',
        nargs='?',
        default=None,
        help='Number of seconds from the start of the music files to limit fingerprinting to.\n'
        'Usage: \n'
        '--limit number_of_seconds \n'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=__version__
    )

    args = parser.parse_args()

    if not args.dburl:
        args.dburl = os.environ['DATABASE_URL']

    if not args.fingerprint and not args.recognize and not args.network:
        parser.print_help()
        sys.exit(0)

    djv = Dejavu(dburl=args.dburl, fingerprint_limit=args.limit)
    if args.fingerprint:
        # Fingerprint all files in a directory
        if len(args.fingerprint) == 2:
            directory = args.fingerprint[0]
            extension = args.fingerprint[1]
            print(
                "Fingerprinting all .%s files in the %s directory" %
                (extension, directory)
            )
            djv.fingerprint_directory(directory, ["." + extension], 4)

        elif len(args.fingerprint) == 1:
            filepath = args.fingerprint[0]
            if os.path.isdir(filepath):
                print(
                    "Please specify an extension if you'd like to fingerprint a directory!"
                )
                sys.exit(1)
            djv.fingerprint_file(filepath)

    elif args.recognize:
        # Recognize audio source
        song = None
        source = args.recognize[0]
        opt_arg = args.recognize[1]

        if source in ('mic', 'microphone'):
            song = djv.recognize(MicrophoneRecognizer, seconds=opt_arg)
        elif source == 'file':
            song = djv.recognize(FileRecognizer, opt_arg)
        print(song)

    elif args.network:
        # Recognize audio source
        song = None
        source = args.network[0]
        #opt_arg = args.network[1]

        if source == 'API':
            logging.basicConfig(filename='fngrprntr.log',level=logging.DEBUG)

        #time_started = datetime.datetime.now()
            app.run(debug=False,host='0.0.0.0', port=4141)
            #song = djv.recognize(APIRecognizer)
        #print(song)

    sys.exit(0)
