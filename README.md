# dejavu

## Purpose

This fork attempts to:

*   [:heavy_check_mark:] Fix bugs (fixes critical numpy one).
*   [:heavy_check_mark:] Use SQLAlchemy to support PostgreSQL, SQLite3 DBs as well.
*   [:heavy_check_mark:] Use Pipenv to allow db credentials via .env file
*   [:heavy_check_mark:] Support both Python3 and Python2.
*   [WIP] Use the logging module so as to not litter any user's application with prints.
*   [:heavy_check_mark:] Reformat code using YAPF (Facebook)
*   [:heavy_check_mark:] Implement simple HTTP REST interface
*   [:WIP:] Implement simple websocket interface


## Usage

1.  Install directly from this repo:

```commandline
pip install -e git+https://github.com/ivlovric/dejavu@1.3.4#egg=PyDejavu
```

2.  Import and use:

```python
from dejavu import Dejavu
from dejavu.recognize import FileRecognizer

djv = Dejavu(dburl='sqlite://')
djv.fingerprint_directory('~/Music')
song = djv.recognize(FileRecognizer, 'mp3/Dura--Daddy-Yankee.mp3')
print(song)
```

3.  Can also be used as a CLI tool:

```commandline
export DATABASE_URL=mysql+mysqlconnector://bryan:password@localhost/dejavu
python dejavu.py --fingerprint ~/Music mp3 --limit 30
python dejavu.py --recognize mic 10
python dejavu.py --recognize file sometrack.mp3
python dejavu.py --network API

```

For network usage, default TCP port is 4141. 

You can keep the database url saved in an .env file and use pipenv. As
well as specify it via the `--dburl` command line argument.

**NOTE** Some incompatibility around byte encoding is present with this connector pair
for some database versions (e.g. [MariaDb](https://mariadb.org/)).
Consider using `mysql+pymysql` instead of `mysql+mysqlconnector` with a simple
fingerprint to check for this error.

## Migrating from worldveil/dejavu

If you already have a live database that used to follow worldveil/dejavu
database structure, you'll have to migrate your database
by renaming:

*   `song_id` to `id`
*   `song_name` to `name`

in the `songs` table.

## Testing

We have included a `docker-compose.yml` and Dockerfile that allows 'headless' testing.

### Build container

You can choose the Python version you wish to build with by setting:

```
export PYTHON_VERION=3.6.6
```

Or update the Pipfile with the version you want and use:

```
export PYTHON_VERSION=$(cat Pipfile | awk '/python_version/ {print $3}' | tr -d '"')
```

Then run the build:

```
docker-compose build
```

This creates a `dejavu` container.

### Test with docker-compose

Once the container is built, you can run your tests:

```
docker-compose run dejavu pipenv run run_tests
```

This will run the script called `run_tests` in the `Pipfile`

You can get a shell with:

```
docker-compose run dejavu /bin/bash
```

You can then run tests inside the container with either `pipenv run run_tests` or `bash test_dejavu.sh`

You can change the default command the container/service will run by changing the `CMD` in the `Dockerfile` or `command` in the `docker-compose.yml` file.
Currently they are set to `tail -f /dev/null` which basically keeps a process running in the container without doing anything.

You may want to set these to `pipenv run run_tests` for testing. See [Docker](https://docs.docker.com/engine/reference/builder/#cmd) or [docker-compose](https://docs.docker.com/compose/compose-file/#command)
