#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s942.py -- kit S942: proves on the box, BEFORE the model line changes, that Sarvam answers saaras:v4 through BOTH doors
call_transcription.py uses -- the short-call door (speech_to_text.transcribe) and the batch door (speech_to_text_job.create_job) --
with the SAME parameters the script sends (mode, language_code, codec). Read-only on the estate: nothing written anywhere.

  What it sends: a 1.2-second made-up WAV (a soft tone, no speech, 16 kHz mono) to the short door, model saaras:v4, mode
  transcribe, language_code unknown, codec wav -- a 400 on the model, the mode or the codec would show here; a transcript of any
  length (usually empty: there is no speech) is the proof the door took v4. The batch door: one job is INITIATED with the same
  model/mode/language (no file uploaded, never started -- Sarvam lists it as Accepted and nothing is billed).
  --sync-only skips the batch door.  --key-file <path> reads the key from another .env (default /root/wa/.env, as the script).

  Last line:  PROBE OK ...   or   PROBE FAIL <reason>       (exit 0 / 1)
"""
import argparse
import io
import math
import os
import struct
import sys
import wave

ENV_PATH = "/root/wa/.env"


def read_key(path):
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln.startswith("SARVAM_API_KEY="):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def tone_wav(seconds=1.2, rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        n = int(seconds * rate)
        frames = bytearray()
        for i in range(n):
            v = int(2500 * math.sin(2 * math.pi * 440 * i / rate))
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", default=ENV_PATH)
    ap.add_argument("--sync-only", action="store_true")
    ap.add_argument("--model", default="saaras:v4")
    a = ap.parse_args()
    key = read_key(a.key_file)
    if not key:
        print("PROBE FAIL no SARVAM_API_KEY in %s" % a.key_file)
        return 1
    try:
        import sarvamai
        from sarvamai import SarvamAI
    except Exception as e:  # noqa: BLE001
        print("PROBE FAIL sarvamai not importable: %s" % e)
        return 1
    ver = getattr(sarvamai, "__version__", "?")
    client = SarvamAI(api_subscription_key=key)
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "s942_probe.wav")
    with open(tmp, "wb") as fh:
        fh.write(tone_wav())
    try:
        with open(tmp, "rb") as af:
            resp = client.speech_to_text.transcribe(file=af, model=a.model, mode="transcribe",
                                                    language_code="unknown", input_audio_codec="wav")
        text = getattr(resp, "transcript", None)
        if text is None:
            print("PROBE FAIL the short door answered without a transcript field (%r)" % (type(resp).__name__,))
            return 1
        lang = getattr(resp, "language_code", "") or "-"
        rid = getattr(resp, "request_id", "") or "-"
        sync_word = "short door %s answered (transcript %d chars, language %s, request %s)" % (a.model, len(text), lang, str(rid)[:12])
    except Exception as e:  # noqa: BLE001
        print("PROBE FAIL short door %s: %s" % (a.model, str(e).replace(key, "<key>")[:300]))
        return 1
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    batch_word = "batch door not probed"
    if not a.sync_only:
        try:
            job = client.speech_to_text_job.create_job(model=a.model, mode="transcribe", language_code="unknown")
            jid = getattr(job, "_job_id", None) or getattr(job, "job_id", None) or "?"
            batch_word = "batch door %s initiated a job (%s..., not started, nothing billed)" % (a.model, str(jid)[:8])
        except Exception as e:  # noqa: BLE001
            print("PROBE FAIL batch door %s: %s" % (a.model, str(e).replace(key, "<key>")[:300]))
            return 1
    print("PROBE OK sarvamai %s; %s; %s" % (ver, sync_word, batch_word))
    return 0


if __name__ == "__main__":
    sys.exit(main())
