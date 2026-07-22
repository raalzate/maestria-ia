"""Tests for error handling: FileTooLargeError raised before upload.

[TS-016]
"""

import pytest

pytestmark = pytest.mark.offline

from domain.exceptions import FileTooLargeError


class TestFileTooLargeError:
    """[TS-016] FileTooLargeError raised before upload when audio exceeds size limit."""

    def _build_adapter(self, max_bytes: int):
        from unittest.mock import MagicMock, patch

        from infra.adapters.faster_whisper_transcription import (
            FasterWhisperTranscriptionAdapter,
        )

        with patch(
            "infra.adapters.faster_whisper_transcription.WhisperModel",
            return_value=MagicMock(),
        ):
            return FasterWhisperTranscriptionAdapter(model_name="base", max_bytes=max_bytes)

    def test_transcription_adapter_raises_on_oversized_file(self):
        adapter = self._build_adapter(max_bytes=100)
        oversized_audio = b"x" * 200

        with pytest.raises(FileTooLargeError):
            adapter.transcribe(oversized_audio)

    def test_file_too_large_error_is_exception(self):
        assert issubclass(FileTooLargeError, Exception)

    def test_error_message_is_descriptive(self):
        adapter = self._build_adapter(max_bytes=100)

        with pytest.raises(FileTooLargeError, match="exceeds.*limit"):
            adapter.transcribe(b"x" * 200)
