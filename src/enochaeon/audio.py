"""WAV assembly: 16 kHz mono, silence gaps, and a short INFO comment.

The comment records the gap lengths used to build the file. It does not
contain the plaintext. Decode uses those lengths to tell a syllable break
from a word break.
"""

from __future__ import annotations

import struct
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soxr

SAMPLE_RATE = 16_000
SYLLABLE_MS = 250
WORD_MS = 600
NL_MS = 1000
COMMENT_PREFIX = "enochaeon;v=1"


@dataclass(frozen=True)
class Gaps:
    syllable_ms: int = SYLLABLE_MS
    word_ms: int = WORD_MS
    nl_ms: int = NL_MS

    def comment(self) -> str:
        return (
            f"{COMMENT_PREFIX};syllable_ms={self.syllable_ms};"
            f"word_ms={self.word_ms};nl_ms={self.nl_ms}"
        )


def parse_comment(comment: str | None) -> Gaps | None:
    if not comment or not comment.startswith(COMMENT_PREFIX):
        return None
    fields = {}
    for piece in comment.split(";"):
        if "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        fields[key] = value
    try:
        return Gaps(
            syllable_ms=int(fields["syllable_ms"]),
            word_ms=int(fields["word_ms"]),
            nl_ms=int(fields["nl_ms"]),
        )
    except (KeyError, ValueError):
        return None


def read_comment(path: Path) -> str | None:
    raw = Path(path).read_bytes()
    marker = raw.find(b"ICMT")
    if marker < 0 or marker + 8 > len(raw):
        return None
    size = struct.unpack_from("<I", raw, marker + 4)[0]
    payload = raw[marker + 8 : marker + 8 + size]
    return payload.split(b"\0", 1)[0].decode("utf-8", errors="replace")


def silence(ms: int, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    count = int(sample_rate * ms / 1000)
    return np.zeros(count, dtype=np.float32)


def resample(audio: np.ndarray, source_rate: int, target_rate: int = SAMPLE_RATE) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio[:, 0]
    if source_rate == target_rate:
        return audio
    return np.asarray(soxr.resample(audio, source_rate, target_rate), dtype=np.float32)


def trim_silence(
    audio: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    threshold: float = 0.015,
    pad_ms: int = 50,
) -> np.ndarray:
    """Drop the quiet edges espeak leaves, and keep a little pad so releases survive."""
    magnitude = np.abs(audio)
    voiced = np.flatnonzero(magnitude > threshold)
    if voiced.size == 0:
        return audio[:1]
    pad = int(sample_rate * pad_ms / 1000)
    start = max(0, int(voiced[0]) - pad)
    end = min(audio.shape[0], int(voiced[-1]) + pad + 1)
    return audio[start:end]


def normalize(audio: np.ndarray, peak: float = 0.7) -> np.ndarray:
    loudest = float(np.max(np.abs(audio))) if audio.size else 0.0
    if loudest < 1e-6:
        return audio
    return (audio * (peak / loudest)).astype(np.float32)


def write_wav(path: Path, audio: np.ndarray, sample_rate: int = SAMPLE_RATE, comment: str = "") -> None:
    samples = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    pcm = (samples * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    if comment:
        _append_comment(path, comment)


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
        width = handle.getsampwidth()
    if width != 2:
        raise ValueError(f"{path} is not 16-bit PCM")
    pcm = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32767.0
    if channels > 1:
        pcm = pcm.reshape(-1, channels)[:, 0]
    return pcm, sample_rate


def _append_comment(path: Path, comment: str) -> None:
    raw = path.read_bytes()
    data = comment.encode("utf-8") + b"\0"
    if len(data) % 2:
        data += b"\0"
    icmt = b"ICMT" + struct.pack("<I", len(data)) + data
    payload = b"INFO" + icmt
    chunk = b"LIST" + struct.pack("<I", len(payload)) + payload
    updated = raw + chunk
    size = struct.pack("<I", len(updated) - 8)
    path.write_bytes(updated[:4] + size + updated[8:])


def voiced_regions(
    audio: np.ndarray,
    sample_rate: int,
    threshold: float = 0.02,
    frame_ms: int = 10,
    bridge_ms: int = 100,
) -> list[tuple[int, int]]:
    """Sample ranges that contain speech.

    Gaps shorter than ``bridge_ms`` are closed first, so the silence inside a
    stop consonant does not split a syllable.
    """
    if audio.size == 0:
        return []
    frame = max(1, int(sample_rate * frame_ms / 1000))
    count = audio.shape[0] // frame
    if count == 0:
        return [(0, audio.shape[0])] if float(np.max(np.abs(audio))) > threshold else []
    usable = audio[: count * frame].reshape(count, frame)
    rms = np.sqrt(np.mean(usable * usable, axis=1))
    voiced = rms > threshold
    bridge = max(1, int(bridge_ms / frame_ms))
    index = 0
    while index < count:
        if voiced[index]:
            index += 1
            continue
        end = index
        while end < count and not voiced[end]:
            end += 1
        if index > 0 and end < count and (end - index) <= bridge:
            voiced[index:end] = True
        index = end
    regions: list[tuple[int, int]] = []
    index = 0
    while index < count:
        if not voiced[index]:
            index += 1
            continue
        end = index
        while end < count and voiced[end]:
            end += 1
        regions.append((index * frame, min(audio.shape[0], end * frame)))
        index = end
    return regions


def segment_words(
    audio: np.ndarray,
    sample_rate: int,
    gaps: Gaps,
) -> list[np.ndarray | str]:
    """One audio slice per word, with ``' '`` or ``'\\n'`` between them.

    A silence shorter than the midpoint between a syllable gap and a word gap
    stays inside the word. The slice includes that internal silence, so a word
    spoken as one breath comes back as one piece.
    """
    raw = voiced_regions(audio, sample_rate)
    if not raw:
        return []
    syllable_limit = (gaps.syllable_ms + gaps.word_ms) / 2
    newline_limit = (gaps.word_ms + gaps.nl_ms) / 2
    pad = int(sample_rate * 0.08)
    groups: list[list[tuple[int, int]]] = [[raw[0]]]
    gap_marks: list[str] = []
    for index in range(len(raw) - 1):
        gap_ms = (raw[index + 1][0] - raw[index][1]) * 1000 / sample_rate
        if gap_ms < syllable_limit:
            groups[-1].append(raw[index + 1])
            continue
        gap_marks.append("\n" if gap_ms >= newline_limit else " ")
        groups.append([raw[index + 1]])
    words: list[np.ndarray | str] = []
    for index, group in enumerate(groups):
        left_bound = 0 if index == 0 else raw_gap_midpoint(groups[index - 1], group)
        right_bound = audio.shape[0] if index == len(groups) - 1 else raw_gap_midpoint(group, groups[index + 1])
        start = max(left_bound, group[0][0] - pad)
        end = min(right_bound, group[-1][1] + pad)
        words.append(audio[start:end])
        if index < len(gap_marks):
            words.append(gap_marks[index])
    return words


def raw_gap_midpoint(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> int:
    return (left[-1][1] + right[0][0]) // 2
