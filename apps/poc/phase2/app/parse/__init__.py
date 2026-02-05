"""Parse module for XML processing."""

from app.parse.jp_gazette_parser import parse_pending_files, parse_single_file

__all__ = ["parse_pending_files", "parse_single_file"]
