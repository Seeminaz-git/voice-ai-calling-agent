"""Text-to-speech providers (ElevenLabs in production, mock for local demo/tests)."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Return synthesized audio bytes."""


class MockTTS(TTSProvider):
    def synthesize(self, text: str) -> bytes:
        # Stand-in "audio": in the demo/test path we just echo the text back
        # as bytes so callers can assert on what would have been spoken.
        return text.encode("utf-8")


class ElevenLabsTTS(TTSProvider):
    def __init__(self, api_key: str | None = None, voice_id: str = "default"):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = voice_id
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not configured")

    def synthesize(self, text: str) -> bytes:
        # Production implementation would call the ElevenLabs REST API:
        #
        #   POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
        #   headers={"xi-api-key": self.api_key}
        #   json={"text": text}
        #
        raise NotImplementedError("Wire up the ElevenLabs REST client with a live API key")


def get_tts_provider() -> TTSProvider:
    if os.environ.get("ELEVENLABS_API_KEY"):
        return ElevenLabsTTS()
    return MockTTS()
