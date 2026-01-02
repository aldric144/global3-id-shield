import hashlib
from typing import Tuple, BinaryIO


def compute_file_hashes(file: BinaryIO) -> Tuple[str, str]:
    """
    Compute SHA-256 and MD5 hashes for a file.
    Returns (sha256_hash, md5_hash)
    
    This is a critical forensic function - hashes are computed immediately
    upon evidence ingestion to establish chain of custody.
    """
    sha256_hasher = hashlib.sha256()
    md5_hasher = hashlib.md5()
    
    file.seek(0)
    
    for chunk in iter(lambda: file.read(8192), b""):
        sha256_hasher.update(chunk)
        md5_hasher.update(chunk)
    
    file.seek(0)
    
    return sha256_hasher.hexdigest(), md5_hasher.hexdigest()


def compute_string_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode()).hexdigest()


def compute_bytes_hash(content: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(content).hexdigest()


def verify_file_integrity(file: BinaryIO, expected_sha256: str) -> bool:
    """
    Verify file integrity by comparing computed hash with expected hash.
    Used for chain-of-custody verification.
    """
    sha256_hash, _ = compute_file_hashes(file)
    return sha256_hash == expected_sha256
