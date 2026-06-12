#!/usr/bin/env python3
"""Benchmark remote ASR servers supported by Vocalinux."""

import argparse
import base64
import json
import re
import statistics
import string
import time
import urllib.request
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional


CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"
OPENAI_TRANSCRIPTIONS_ENDPOINT = "/v1/audio/transcriptions"
WHISPERCPP_ENDPOINT = "/inference"


@dataclass
class BenchmarkItem:
    audio: Path
    expected: Optional[str] = None


@dataclass
class BenchmarkResult:
    audio: str
    endpoint: str
    model: str
    duration_s: float
    latency_s: float
    rtf: Optional[float]
    text: str
    expected: Optional[str] = None
    wer: Optional[float] = None
    error: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a Vocalinux-compatible ASR server")
    parser.add_argument("--server-url", required=True, help="Base URL, e.g. http://localhost:8000")
    parser.add_argument(
        "--endpoint",
        default=WHISPERCPP_ENDPOINT,
        choices=[WHISPERCPP_ENDPOINT, OPENAI_TRANSCRIPTIONS_ENDPOINT, CHAT_COMPLETIONS_ENDPOINT],
        help="Remote API endpoint format",
    )
    parser.add_argument("--model", default="whisper-1", help="Model name sent to the server")
    parser.add_argument("--api-key", default="", help="Bearer token for servers that require one")
    parser.add_argument("--language", default="", help="Optional language code passed to the server")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to run each sample")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--manifest",
        type=Path,
        help='JSONL file with {"audio": "path.wav", "text": "reference transcript"} rows',
    )
    parser.add_argument("audio", nargs="*", type=Path, help="Audio files to benchmark")
    args = parser.parse_args()

    if not args.audio and not args.manifest:
        parser.error("provide audio files or --manifest")
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    return args


def load_items(args: argparse.Namespace) -> list[BenchmarkItem]:
    items = [BenchmarkItem(audio=path) for path in args.audio]
    if not args.manifest:
        return items

    manifest_dir = args.manifest.resolve().parent
    with args.manifest.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "audio" not in row:
                raise ValueError(f"{args.manifest}:{line_number} missing 'audio'")
            audio_path = Path(row["audio"])
            if not audio_path.is_absolute():
                audio_path = manifest_dir / audio_path
            items.append(BenchmarkItem(audio=audio_path, expected=row.get("text")))
    return items


def audio_duration(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            return frames / float(rate) if rate else 0.0
    except (wave.Error, OSError):
        return 0.0


def normalize_endpoint(endpoint: str) -> str:
    return endpoint if endpoint.startswith("/") else f"/{endpoint}"


def endpoint_url(server_url: str, endpoint: str) -> str:
    return f"{server_url.rstrip('/')}{normalize_endpoint(endpoint)}"


def post_json(url: str, headers: dict[str, str], payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def encode_multipart(fields: dict[str, str], file_name: str, file_bytes: bytes) -> tuple[bytes, str]:
    boundary = f"----vocalinux-asr-benchmark-{time.time_ns()}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    chunks.extend(
        [
            f"--{boundary}\r\n".encode("ascii"),
            (
                'Content-Disposition: form-data; name="file"; '
                f'filename="{file_name}"\r\n'
            ).encode("utf-8"),
            b"Content-Type: audio/wav\r\n\r\n",
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("ascii"),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def post_multipart(
    url: str,
    headers: dict[str, str],
    fields: dict[str, str],
    file_name: str,
    file_bytes: bytes,
    timeout: float,
) -> dict:
    body, content_type = encode_multipart(fields, file_name, file_bytes)
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": content_type},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def clean_transcription_text(text: str) -> str:
    if not text.strip():
        return ""
    return re.sub(r"^\s*(?:<\|[^|>\n]+\|>)+\s*", "", text)


def extract_transcription_text(payload: object) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return clean_transcription_text(payload)
    if isinstance(payload, list):
        parts = [extract_transcription_text(item).strip() for item in payload]
        return "\n".join(part for part in parts if part)
    if not isinstance(payload, dict):
        return clean_transcription_text(str(payload))

    for key in ("text", "transcript", "transcription"):
        value = payload.get(key)
        if isinstance(value, str):
            return clean_transcription_text(value)

    segments = payload.get("segments")
    if isinstance(segments, list):
        text = extract_transcription_text(segments)
        if text:
            return text

    for key in ("result", "data", "output"):
        text = extract_transcription_text(payload.get(key))
        if text:
            return text

    return ""


def parse_chat_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif item:
                parts.append(str(item))
        content = "\n".join(parts)

    text = str(content).strip()
    if not text:
        return ""

    try:
        payload = json.loads(text)
        parsed_text = extract_transcription_text(payload)
        if parsed_text:
            return parsed_text.strip()
    except (TypeError, ValueError):
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].lower().startswith("language ") and len(lines) > 1:
        return clean_transcription_text("\n".join(lines[1:])).strip()
    return clean_transcription_text(text)


def transcribe_file(item: BenchmarkItem, args: argparse.Namespace) -> BenchmarkResult:
    endpoint = normalize_endpoint(args.endpoint)
    url = endpoint_url(args.server_url, endpoint)
    wav_bytes = item.audio.read_bytes()
    headers = {}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key}"

    duration_s = audio_duration(item.audio)
    start = time.perf_counter()
    try:
        if endpoint == CHAT_COMPLETIONS_ENDPOINT:
            audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
            content = [
                {
                    "type": "audio_url",
                    "audio_url": {"url": f"data:audio/wav;base64,{audio_b64}"},
                }
            ]
            if args.language:
                content.append(
                    {
                        "type": "text",
                        "text": f"Transcribe the audio in language code '{args.language}'.",
                    }
                )
            payload = post_json(
                url,
                headers,
                {
                    "model": args.model,
                    "messages": [{"role": "user", "content": content}],
                    "temperature": 0,
                },
                timeout=args.timeout,
            )
            text = parse_chat_text(
                payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
        else:
            data: dict[str, str] = {}
            if endpoint == OPENAI_TRANSCRIPTIONS_ENDPOINT:
                data["model"] = args.model
            else:
                data.update(
                    {
                        "temperature": "0.0",
                        "temperature_inc": "0.2",
                        "response_format": "json",
                    }
                )
            if args.language:
                data["language"] = args.language
            payload = post_multipart(
                url,
                headers,
                data,
                item.audio.name,
                wav_bytes,
                args.timeout,
            )
            text = extract_transcription_text(payload)
        latency_s = time.perf_counter() - start
        return BenchmarkResult(
            audio=str(item.audio),
            endpoint=endpoint,
            model=args.model,
            duration_s=duration_s,
            latency_s=latency_s,
            rtf=latency_s / duration_s if duration_s > 0 else None,
            text=text,
            expected=item.expected,
            wer=word_error_rate(item.expected, text) if item.expected else None,
        )
    except Exception as e:
        latency_s = time.perf_counter() - start
        return BenchmarkResult(
            audio=str(item.audio),
            endpoint=endpoint,
            model=args.model,
            duration_s=duration_s,
            latency_s=latency_s,
            rtf=latency_s / duration_s if duration_s > 0 else None,
            text="",
            expected=item.expected,
            error=str(e),
        )


def normalized_words(text: str) -> list[str]:
    translator = str.maketrans("", "", string.punctuation)
    return text.lower().translate(translator).split()


def levenshtein_distance(a: list[str], b: list[str]) -> int:
    previous = list(range(len(b) + 1))
    for i, word_a in enumerate(a, start=1):
        current = [i]
        for j, word_b in enumerate(b, start=1):
            substitution = previous[j - 1] + (word_a != word_b)
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1]


def word_error_rate(expected: Optional[str], actual: str) -> Optional[float]:
    if expected is None:
        return None
    reference = normalized_words(expected)
    hypothesis = normalized_words(actual)
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return levenshtein_distance(reference, hypothesis) / len(reference)


def median_or_none(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [value for value in values if value is not None]
    return statistics.median(clean) if clean else None


def summarize(results: list[BenchmarkResult]) -> dict:
    successes = [result for result in results if result.error is None]
    return {
        "samples": len(results),
        "successes": len(successes),
        "failures": len(results) - len(successes),
        "median_latency_s": median_or_none(result.latency_s for result in successes),
        "median_rtf": median_or_none(result.rtf for result in successes),
        "median_wer": median_or_none(result.wer for result in successes),
    }


def print_human(results: list[BenchmarkResult]) -> None:
    for result in results:
        if result.error:
            print(f"FAIL {result.audio}: {result.error}")
            continue
        rtf = f"{result.rtf:.3f}" if result.rtf is not None else "n/a"
        wer = f", WER={result.wer:.3f}" if result.wer is not None else ""
        print(
            f"OK   {result.audio}: {result.latency_s:.3f}s, "
            f"audio={result.duration_s:.2f}s, RTF={rtf}{wer}"
        )
        print(f"     {result.text}")

    summary = summarize(results)
    print()
    print(
        "Summary: "
        f"{summary['successes']}/{summary['samples']} ok, "
        f"median latency={summary['median_latency_s']}, "
        f"median RTF={summary['median_rtf']}, "
        f"median WER={summary['median_wer']}"
    )


def main() -> int:
    args = parse_args()
    items = load_items(args)
    results: list[BenchmarkResult] = []

    for item in items:
        if not item.audio.exists():
            results.append(
                BenchmarkResult(
                    audio=str(item.audio),
                    endpoint=normalize_endpoint(args.endpoint),
                    model=args.model,
                    duration_s=0.0,
                    latency_s=0.0,
                    rtf=None,
                    text="",
                    expected=item.expected,
                    error="audio file not found",
                )
            )
            continue
        for _ in range(args.repeat):
            results.append(transcribe_file(item, args))

    if args.json:
        print(
            json.dumps(
                {"results": [asdict(result) for result in results], "summary": summarize(results)}
            )
        )
    else:
        print_human(results)

    return 1 if any(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
