"""Speech-to-text providers.

Real deployments use Deepgram's streaming API. A mock provider is included so the
pipeline runs end-to-end with no external credentials, which is what the test
suite and local demo exercise.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_chunk: bytes) -> tuple[str, float]:
        """Return (text, confidence)."""


class MockSTT(STTProvider):
    """Deterministic stand-in used for local demos and tests.

    In place of real audio bytes, callers pass UTF-8 encoded text through
    `audio_chunk` so the rest of the pipeline can be exercised without a
    microphone or telephony bridge.
    """

    def transcribe(self, audio_chunk: bytes) -> tuple[str, float]:
        text = audio_chunk.decode("utf-8", errors="ignore").strip()
        # Heuristic confidence: short or empty utterances are treated as
        # low-confidence, mirroring how real ASR degrades on noisy audio.
        confidence = 0.95 if len(text.split()) >= 2 else 0.4
        return text, confidence


class DeepgramSTT(STTProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPGRAM_API_KEY not configured")

    def transcribe(self, audio_chunk: bytes) -> tuple[str, float]:
        # Deepgram's SDK (`deepgram-sdk`) would be used here in production:
        #
        #   from deepgram import DeepgramClient
        #   client = DeepgramClient(self.api_key)
        #   response = client.listen.rest.v("1").transcribe_file(...)
        #
        # Kept out of the demo path so the repo has no hard dependency on a
        # paid API key to run.
        raise NotImplementedError("Wire up the Deepgram SDK with a live API key")


def get_stt_provider() -> STTProvider:
    if os.environ.get("DEEPGRAM_API_KEY"):
        return DeepgramSTT()
    return MockSTT()
