# ASR Evaluation Notes

This note tracks the ASR-model implications from discussion feedback around newer
recognition engines. It is intentionally conservative: claims here should be
treated as candidates to benchmark, not as reasons to replace Vocalinux defaults
without reproducible desktop tests.

## Current Takeaways

| Area | What the evidence suggests | Project implication |
|---|---|---|
| Whisper / whisper.cpp | OpenAI released Whisper in 2022, trained on 680k hours of multilingual data, and documents a 30-second windowed decoding design. The model is no longer the newest ASR architecture, but it remains robust, portable, and easy to run through whisper.cpp. | Keep whisper.cpp as the default until a newer engine proves better across install size, CPU/GPU support, latency, accuracy, and Linux desktop reliability. |
| SenseVoice | SenseVoice-Small is a real modern candidate. Its model card reports non-autoregressive inference, more than 50 languages, and much lower latency than Whisper-Large on its benchmarks. | Evaluate through a service wrapper first. A bundled local engine would add FunASR/model dependencies and needs packaging review. |
| Qwen3-ASR | Qwen3-ASR-0.6B and 1.7B are real modern candidates. The model card documents vLLM serving through `/v1/chat/completions` and streaming support through the vLLM backend. | Support chat-completions audio in the Remote API engine so Qwen3-ASR servers can be tested without adding a heavy local dependency stack. |
| NVIDIA ASR models | NVIDIA Parakeet-TDT-0.6B-v2 is a 600M-parameter ASR model for 16 kHz mono audio. Recent research also points to NVIDIA streaming ASR variants as strong low-latency candidates. | Track as a benchmark candidate, especially on NVIDIA hardware. Avoid making it a default path until the public serving/install story is clear for ordinary Linux users. |
| Streaming | Whisper-style streaming usually needs chunking, partial result stabilization, and duplicate suppression. Native streaming models may reduce that complexity. | Benchmark true streaming engines separately from end-of-utterance dictation; do not judge them only through the batch Remote API path. |

Sources worth re-checking when revisiting this:

- [OpenAI Whisper release](https://openai.com/index/whisper/)
- [OpenAI Whisper model table](https://github.com/openai/whisper#available-models-and-languages)
- [SenseVoiceSmall model card](https://huggingface.co/FunAudioLLM/SenseVoiceSmall)
- [SenseVoice repository](https://github.com/FunAudioLLM/SenseVoice)
- [Qwen3-ASR-0.6B model card](https://huggingface.co/Qwen/Qwen3-ASR-0.6B)
- [NVIDIA Parakeet-TDT-0.6B-v2 model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)

## Benchmark Harness

Use `scripts/benchmark_remote_asr.py` to compare remote servers with the same audio
fixtures. It reports request latency, audio duration, real-time factor (RTF), and
optional word error rate (WER) when a reference transcript is supplied.

### Mock Server Smoke Test

In one terminal:

```bash
python scripts/test_remote_server.py --port 8080
```

In another terminal, point the benchmark at a WAV file:

```bash
python scripts/benchmark_remote_asr.py \
    --server-url http://localhost:8080 \
    --endpoint /v1/chat/completions \
    --model Qwen/Qwen3-ASR-0.6B \
    sample.wav
```

The mock server does not measure recognition quality; it only verifies client
protocol compatibility.

### Manifest With References

Create a JSONL manifest:

```json
{"audio": "samples/hello.wav", "text": "hello this is vocalinux testing the remote api"}
{"audio": "samples/long.wav", "text": "the quick brown fox jumps over the lazy dog"}
```

Run:

```bash
python scripts/benchmark_remote_asr.py \
    --server-url http://localhost:8000 \
    --endpoint /v1/audio/transcriptions \
    --model whisper-1 \
    --manifest samples/manifest.jsonl
```

For repeatability, keep audio short enough to match dictation usage, include noisy
and accented samples, and record hardware/server details with the results.

## Docker Notes

Docker is useful for protocol tests and clean dependency checks, but it is not a
great substitute for a desktop Linux session with microphone, notification,
keyboard injection, IBus, and tray integration.

A minimal Ubuntu container check looks like this:

```bash
docker run --rm -it \
    -v "$PWD:/workspace" \
    -w /workspace \
    ubuntu:24.04 bash
```

Inside the container:

```bash
apt update
apt install -y python3 python3-venv python3-pip portaudio19-dev libasound2-dev
python3 -m venv /tmp/vocalinux-venv
. /tmp/vocalinux-venv/bin/activate
pip install -e ".[dev]"
pytest tests/test_recognition_manager_remote_api.py
python scripts/test_remote_server.py --host 127.0.0.1 --port 8080
```

For full Vocalinux desktop testing, prefer a real Ubuntu/Debian VM with SSH plus
working audio and graphical session access. The important checks are:

1. Remote API protocol works against candidate ASR servers.
2. End-to-end dictation latency is acceptable from hotkey release to text injection.
3. Audio capture, VAD segmentation, and text injection still behave on X11 and Wayland.
4. Install and update paths remain reasonable for users without NVIDIA GPUs.
