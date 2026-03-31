"""
Static constants for crawling utilities.
Extracted from url_handler.py to reduce file size and decouple logic.
"""

BINARY_EXTENSIONS = {
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz", ".tgz",
    # Executables and installers
    ".exe", ".dmg", ".pkg", ".deb", ".rpm", ".msi", ".app", ".appimage",
    # Documents (non-HTML)
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods",
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff",
    # Audio/Video
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv", ".wav", ".flac",
    # Data files
    ".csv", ".sql", ".db", ".sqlite",
    # Binary data
    ".iso", ".img", ".bin", ".dat",
    # Development files
    ".wasm", ".pyc", ".jar", ".war", ".class", ".dll", ".so", ".dylib",
}
