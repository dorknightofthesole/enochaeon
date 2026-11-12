![Enochian text of the Fifteenth Key](docs/imgs/Enochian_letters_(1583_manuscript).png)

# Enochaeon

Enochaeon is a spoken cipher. It is also a tool for speaking Dee's forty-eight Keys, and for translating English into spoken Enochian.

The cipher takes a text file letter by letter from English into Hebrew and then into [Enochian](https://en.wikipedia.org/wiki/Enochian), the angelic language John Dee, Elizabeth I's astrologer, recorded in 1583. Each letter is spoken alone, as the sound assigned to that Enochian letter. A short silence follows a letter, a longer one stands between two words, and a longer one again between two lines. A phone recognizer hears each letter, and the same key turns the letters back into English. [`example/pangram.decoded.txt`](example/pangram.decoded.txt) was read back from [`example/cipher/pangram.mp4`](https://github.com/user-attachments/assets/0c8098d5-b723-42d4-ba3f-686fc75707e7).

The **Calls** are Dee's Keys already written in Enochian. A file in `calls/` is spoken from the pronunciation stored for each spelling.

**Translation** speaks an English phrase as Enochian words. The phrase is matched to the English glosses in the [lexicon](calls/lexicon.json), and each match is spoken from that word's pronunciation. The First Call recording below is from that path.

How the three paths work, and the files they read, is in [`docs/enochaeon-in-theory-and-practice.md`](docs/enochaeon-in-theory-and-practice.md).

The name Enochaeon joins Enoch, the prophet who spoke with the angels, and the Greek *aeon*, an epoch or age.

**This is still a WIP, and I am currently building out and verifying the lexicon.** Update 11-11-2026, I believe the Lexicon is in solid enough shape to be used, but I plan to do more analysis with it.

## Setup

```bash
brew install espeak-ng
pip install -e .
python3 -m piper.download_voices --download-dir scratch/piper-voices en_US-john-medium
enochaeon calibrate
```

## Voice

[`enochaeon.json`](enochaeon.json) has a `cipher` section for the cipher, and a `calls` section for Calls and translations. Neither reads the other's section.

```json
{
  "cipher": {
    "voice": "scratch/piper-voices/en_US-john-medium.onnx",
    "sounds": "piper_john",
    "length_scale": 1.0,
    "noise_scale": 0.0,
    "noise_w_scale": 0.0,
    "letter_end": ".",
    "letter_ms": 150,
    "word_ms": 500,
    "line_ms": 1000,
    "edge_ms": 50,
    "bridge_ms": 100,
    "hear_ms": 80
  },
  "calls": {
    "engine": "piper",
    "ipa": "dee_ipa",
    "piper": {
      "length_scale": 1.6,
      "word_ms": 200,
      "voice": "scratch/piper-voices/en_US-john-medium.onnx",
      "ipa": "dee_ipa_piper_john",
      "word_end": "."
    }
  }
}
```

- `calls.engine` is `piper` or `espeak`. `--engine` overrides one Call run.
- `calls.ipa` is `dee_ipa` or `golden_dawn_ipa`. Both are fields of `calls/lexicon.json`, which is the one place that says how a word is said. `golden_dawn_ipa` is empty.
- `calls.piper.voice` is the model downloaded in Setup.
- `calls.piper.ipa` is the lexicon field that lists what this Piper voice is given for each spelling. It is sent as written. Leave it out and Piper is given `calls.ipa`.
- `calls.piper.word_end` is the mark that ends each word given to Piper.
- `calls.piper.length_scale` is how long Piper holds each phoneme. `1.0` is conversational, and higher is slower.
- `calls.piper.word_ms` is the silence between Piper breaths, in milliseconds. Leave it out and Piper keeps the 600 milliseconds espeak uses.

Every `cipher` setting must be there. Run `enochaeon calibrate` again after changing one.

- `cipher.voice` is the model downloaded in Setup.
- `cipher.sounds` is the field of [`src/enochaeon/data/alphabet.json`](src/enochaeon/data/alphabet.json) that lists what this voice is given for each letter sound. It is sent as written.
- `cipher.letter_end` is the mark that ends each letter sound given to Piper.
- `cipher.length_scale` is how long Piper holds each phoneme.
- `cipher.noise_scale` and `cipher.noise_w_scale` are Piper's two kinds of chance: in the sound, and in how long each phoneme is held. At zero the voice says a letter the same way every time, and that is the only setting at which whole texts have come back.
- `cipher.letter_ms`, `cipher.word_ms` and `cipher.line_ms` are the silences after a letter, between two words and between two lines, in milliseconds. Each must be longer than the one before. Longer silences made no difference to what came back in a trial, and they make a longer recording.
- `cipher.edge_ms` is the quiet kept on each side of a spoken letter sound.
- `cipher.bridge_ms` is the longest silence that is still inside one letter. It must be shorter than `cipher.letter_ms`.
- `cipher.hear_ms` is the quiet put on each side of a letter when it is given to the recognizer.

## Use

```bash
enochaeon notes.txt    # writes notes.wav and the three stage files
enochaeon notes.wav    # prints the text and writes notes.decoded.txt
enochaeon calls        # speaks every .txt in ./calls
enochaeon calls calls/01.txt # speaks one call 
enochaeon translate ritual.txt #translate English text into spoken Enochian
```

Pass a `.txt` file of Enochian spellings to `enochaeon calls`. The wav is written beside that file.

`enochaeon translate` writes a wav beside the English file, and `.enochaeon/<stem>-enochian.txt` lists the Call words that wav speaks. The same run writes `<stem>.html` beside the wav, showing the spoken spellings in Enochian letters and playing the recording. An English word with nothing close stays in that file in brackets and is left out of the wav. The wav is not read back.

An [example](example/pangram.html) of the Enochian generated text:

![Enochaeon HTML](docs/imgs/Enochian-HTML.png)

### Stage files

The stage files go in a hidden folder next to the source. For `notes-test.txt` they are:

```text
.enochaeon/notes-test-hebrew.txt
.enochaeon/notes-test-enochian.txt
.enochaeon/notes-test-phonetic.txt
```

Hebrew is the pointed transliteration. Enochian is the letter names. Phonetic is the letter sounds of each English word, written the espeak way.

## Example

[`example/pangram.txt`](example/pangram.txt) is the pangram. Encoding it writes the WAV and the three stage files.

- [`example/.enochaeon/pangram-hebrew.txt`](example/.enochaeon/pangram-hebrew.txt) is the pointed Hebrew spelling.
- [`example/.enochaeon/pangram-enochian.txt`](example/.enochaeon/pangram-enochian.txt) is the Enochian letter names.
- [`example/.enochaeon/pangram-phonetic.txt`](example/.enochaeon/pangram-phonetic.txt) is the letter sounds of each English word, written the espeak way.
- [`example/pangram.wav`](example/pangram.wav) is those sounds spoken, one letter at a time.
- [`example/pangram.decoded.txt`](example/pangram.decoded.txt) is the English recovered from that WAV.

https://github.com/user-attachments/assets/a6e506eb-6648-491f-80e6-3c3d229bb94f

[`example/First Call.wav`](example/First%20Call.wav) is a spoken reading of [`calls/01.txt`](calls/01.txt).

An output that is already there is left alone unless you pass `--force`. A cipher WAV carries a short comment with its three silences and a name for the voice that spoke it, and no plaintext. A WAV with no comment is still decoded, with a warning. A WAV spoken by a voice the calibration was not made with is refused, and so is one from the earlier espeak cipher.

## License

Copyright 2026 Eddie Gonzales. This work is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

`src/enochaeon/data/words.txt` is SCOWL and keeps the terms in [`SCOWL-Copyright.txt`](src/enochaeon/data/SCOWL-Copyright.txt). The Enochian letters in [`enochian.ttf`](src/enochaeon/data/enochian.ttf) are by Лорд Алекс and stay under [CC BY-SA 3.0](src/enochaeon/data/enochian-letters-license.txt).
