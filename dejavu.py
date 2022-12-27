#!/usr/bin/python

import os
import sys
import warnings
import argparse

from flask import Flask, jsonify, request
import magic
import logging
import asyncio
from websockets import serve

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer
from dejavu.recognize import MicrophoneRecognizer
from dejavu.recognize import APIRecognizer
from dejavu.recognize import WSRecognizer

from dejavu.version import __version__
from argparse import RawTextHelpFormatter

warnings.filterwarnings("ignore")
logging.basicConfig(filename='dejavu.log',level=logging.INFO)
logging.getLogger("magic")
#l.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.config.from_object(__name__)

ALLOWED_EXTENSIONS = set(['wav','mp3'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # check if the post request has the file part
    dat = request.get_data()
    #print(dat)
    file = request.files
    if file:
        if 'file' not in request.files:
            resp = jsonify({'message' : 'No data in request. Send either form-data with key "file" or raw binary data'})
            resp.status_code = 400
            return resp
        file = request.files['file'] 
        if file.filename == '':
            resp = jsonify({'message' : 'No data selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
        
            #file = io.TextIOWrapper(request.files['file'])
            file = request.files.get('file') 
            filetype = magic.from_buffer(file.read(2024))
            logging.info(filetype)

            ###########print (file.read())
            print("Request for HTTP recognizer received")
            file.seek(0)
            song = djv.recognize(APIRecognizer,file.read())
            resp = jsonify({'message' : song})
            resp.status_code = 201
            return resp

        else:
            resp = jsonify({'message' : 'Allowed file types are wav, mp3'})
            resp.status_code = 400
            return resp
    elif dat:
        #filetype = magic.from_buffer(dat.read(2024))
        #logging.info(filetype)

        print("Request for HTTP recognizer received")
        print(type(dat))
        #dat2=bytes(dat,'UTF-16')
        #dat.seek(0)
        song = djv.recognize(APIRecognizer,dat)
        resp = jsonify({'message' : song})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message' : 'No correct data sent'})
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
        help='Recognize what is sent over HTTP or websocket\n'
        'Usage: \n'
        '--network http data\n'
        '--network ws data\n'


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
        '-v',
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

        if source == 'http':
            # HTTP Server
            app.run(debug=False,host='0.0.0.0', port=4141)
        
        elif source == 'ws':
            # Websocket Server
            WS_PORT = 4242
            async def match(websocket):
                async for message in websocket:
                    print("Request for Websocket recognizer received")
                    #print(type(message))

                    try:
                        #song = djv.recognize(WSRecognizer,str.encode(message))
                        if type(message) == bytes:
                            song = djv.recognize(WSRecognizer,message)
                            try:
                                if song is None:
                                    await websocket.send("No result")
                                else: await websocket.send(song['match'])
                            except Exception as err:
                                print("Could not send response to client", err)
                        else:
                            await websocket.send("Please send byte encoded data")

                    except Exception as e:
                        print(e)
                        await websocket.send("Error getting result, please check your input")
                   
            async def main():
                async with serve(match, "0.0.0.0", str(WS_PORT)):
                    print("Websocket Server listening on Port " + str(WS_PORT))

                    await asyncio.Future()  # run forever

            asyncio.run(main())
    
    sys.exit(0)
