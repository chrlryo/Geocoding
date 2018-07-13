# -*- coding: utf-8 -*-
"""Update the raw data used as the main source of information.

"""

import os
import sys
import zipfile
import requests
import hashlib

from .datapaths import here

raw_data = os.path.join(here, 'raw')
url_content = 'https://adresse.data.gouv.fr/data/contenu.txt'
content_file_name_actual = os.path.join(raw_data, 'contenu.txt')
content_file_name_downloaded = os.path.join(here, 'new_content.txt')
url_ban = 'https://adresse.data.gouv.fr/data/BAN_licence_gratuite_repartage.zip'
ban_zip = os.path.join(raw_data, 'ban.zip')


def completion_bar(msg, fraction):
    percent = int(100 * fraction)
    size = int(50 * fraction)
    sys.stdout.write("\r%-16s: %3d%%[%s%s]" %
                     (msg, percent, '=' * size, ' ' * (50 - size)))
    sys.stdout.flush()

    # New line if bar is complete
    if fraction == 1.:
        print('')


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_ban_file():
    """Download the BAN files.
    """
    if not os.path.exists(raw_data):
        os.mkdir(raw_data)

    with open(content_file_name_downloaded, 'wb') as handle:
        response = requests.get(url_content, stream=True)

        if not response.ok:
            print('Download content file unsuccessful : bad response')
            return False

    try:
        if md5(content_file_name_downloaded) == md5(content_file_name_actual):
            print('BAN database is already up to date. No need to download it again.')
            os.remove(content_file_name_downloaded)
            return False
    except FileNotFoundError:
        pass

    if os.path.exists(ban_zip):
        os.remove(ban_zip)

    with open(ban_zip, 'wb') as handle:
        response = requests.get(url_ban, stream=True)

        if not response.ok:
            print('Download unsuccessful : bad response')
            return False

        done, total_size = 0, int(response.headers.get('content-length'))
        for block in response.iter_content(4096):
            handle.write(block)

            done += len(block)
            completion_bar('Downloading BAN', done / total_size)

    if done != total_size:
        print('Download unsuccessful : incomplete')
        return False

    return True


def decompress():
    # Certifies the existence of the subdirectory.
    if not os.path.isfile(ban_zip):
        print('Decompression unsuccessful : inexistent file')
        return False

    # Decompress each file within ban_zip
    with zipfile.ZipFile(ban_zip) as zf:
        if zf.testzip() is not None:
            print('Decompression unsuccessful : corrupted file')
            return False

        count, n_total = 0, len(zf.infolist())
        for member in zf.infolist():
            zf.extract(member, path=raw_data)

            count += 1
            completion_bar('Decompression', count / n_total)

    return True
