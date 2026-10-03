"""Upload validation rules. Untrusted user input is checked against these on
the server at every step — never trust the client's declared values alone."""

ALLOWED_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mpg", ".mpeg",
    ".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg",
}

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-matroska",
    "video/x-msvideo",
    "video/mpeg",
    "video/ogg",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/aac",
    "audio/flac",
    "audio/ogg",
}

# 4 GB per file. Rejected at declare-time and re-checked after upload.
MAX_UPLOAD_BYTES = 4 * 1024**3
# 60 minutes of media per file.
MAX_DURATION_SECONDS = 3600
# Presigned upload URLs expire after 15 minutes.
PRESIGN_UPLOAD_TTL = 900
# Presigned download URLs expire after 10 minutes.
PRESIGN_DOWNLOAD_TTL = 600
