"""Acoustic phone recognition with no English language model.

The checkpoint is wav2vec 2.0 fine-tuned to emit espeak phones. It is used as
a closed-set syllable classifier: each chunk is one Enochian letter, and the
phone string is matched to the calibration for that letter.
"""

from __future__ import annotations

import os

import numpy as np

from enochaeon.audio import SAMPLE_RATE, resample

MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"

_BUNDLE: tuple[object, object, dict[int, str], int, str] | None = None
_SKIP = {"<pad>", "<s>", "</s>", "<unk>"}


def _load() -> tuple[object, object, dict[int, str], int, str]:
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import json
    from pathlib import Path

    import torch
    from huggingface_hub import hf_hub_download
    from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

    device = os.environ.get("ENOCHAEON_DEVICE", "cpu")
    # token=False keeps an expired saved login from blocking this public model.
    # The phoneme tokenizer would also pull in phonemizer, which is only needed
    # to spell text. Decoding ids only needs the vocabulary.
    extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID, token=False)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID, token=False)
    vocab_path = hf_hub_download(MODEL_ID, "vocab.json", token=False)
    vocab = json.loads(Path(vocab_path).read_text(encoding="utf-8"))
    ids = {int(index): token for token, index in vocab.items()}
    pad_id = int(vocab["<pad>"])
    model.to(device)
    model.eval()
    _BUNDLE = (extractor, model, ids, pad_id, device)
    return _BUNDLE


def _ctc(ids: list[int], table: dict[int, str], pad_id: int) -> str:
    tokens: list[str] = []
    previous: int | None = None
    for index in ids:
        if index == previous:
            continue
        previous = index
        if index == pad_id:
            continue
        token = table.get(index, "")
        if token in _SKIP:
            continue
        tokens.append(token)
    return " ".join(tokens)


def transcribe(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    """Return the space-separated phone string for one syllable."""
    import torch

    extractor, model, table, pad_id, device = _load()
    if sample_rate != SAMPLE_RATE:
        audio = resample(audio, sample_rate)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size < int(SAMPLE_RATE * 0.05):
        return ""
    inputs = extractor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    values = inputs.input_values.to(device)
    try:
        with torch.inference_mode():
            logits = model(values).logits
    except RuntimeError:
        return ""
    predicted = torch.argmax(logits, dim=-1)[0].tolist()
    return _ctc(predicted, table, pad_id)
