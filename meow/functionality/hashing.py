"""
This file contains functions for taking hashes of data and files.

Author(s): David Marchant
"""

from hashlib import sha256

from core.correctness.vars import HASH_BUFFER_SIZE, SHA256
from core.correctness.validation import check_type, valid_existing_file_path

def _get_file_sha256(file_path):
    sha256_hash = sha256()
    
    with open(file_path, 'rb') as file_to_hash:
        while True:
            buffer = file_to_hash.read(HASH_BUFFER_SIZE)
            if not buffer:
                break
            sha256_hash.update(buffer)
    
    return sha256_hash.hexdigest()

def get_file_hash(file_path:str, hash:str, hint:str=""):
    check_type(hash, str, hint=hint)

    valid_existing_file_path(file_path)

    valid_hashes = {
        SHA256: _get_file_sha256
    }
    if hash not in valid_hashes:
        raise KeyError(f"Cannot use hash '{hash}'. Valid are "
            f"'{list(valid_hashes.keys())}")

    return valid_hashes[hash](file_path)
