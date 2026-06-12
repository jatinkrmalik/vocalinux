# Remote HTTP-Based Transcription

Vocalinux can offload speech recognition to a remote HTTP server instead of running a local model. This is useful when you want faster transcription on a more powerful machine, want to share one model across several clients, or want to keep your laptop free of GPU/model overhead.

Vocalinux speaks three wire formats out of the box:

- **OpenAI-compatible** — `POST /v1/audio/transcriptions` (e.g. OpenAI, [Speaches](https://github.com/speaches-ai/speaches), LocalAI, FunASR/SenseVoice)
- **whisper.cpp server** — `POST /inference` (the binary shipped with [whisper.cpp](https://github.com/ggerganov/whisper.cpp))
- **Chat-completions audio** — `POST /v1/chat/completions` for ASR servers that expose audio through the OpenAI chat-completions shape, including Qwen3-ASR via vLLM

Pick whichever your server exposes — the rest of this guide applies to all three.

> **Tip — share the server with your phone.** These HTTP formats are open enough that the same self-hosted server can also back mobile dictation apps. On Android, apps like *Dictate* and *Transcribro* speak OpenAI-compatible Whisper; on iOS, Shortcuts-based dictation clients can hit the same endpoint. Run one Whisper server, point your laptop and phone at it, and you get consistent dictation everywhere without uploading audio to a third party.

## How It Works

When the **Remote API** engine is active, Vocalinux:

1. Captures microphone audio locally (16 kHz, mono, 16-bit PCM).
2. On end-of-utterance, packages the buffer as a WAV file in memory.
3. Uploads it using the configured HTTP format.
4. Reads the transcribed text from the JSON response and types it into the focused window.

No audio is ever written to disk. The local machine still runs the VAD/segmentation logic — only the heavy ASR step is remote.

## Server-Side Setup

You need a server that accepts audio uploads and returns text. Four common setups:

### Option A: whisper.cpp server

Build and run the bundled HTTP server from the [whisper.cpp](https://github.com/ggerganov/whisper.cpp) repo:

```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make server
./models/download-ggml-model.sh medium.en
./build/bin/whisper-server \
    --model models/ggml-medium.en.bin \
    --host 0.0.0.0 \
    --port 8080
```

The server now listens on `http://<server-ip>:8080`. The endpoint is `/inference`.

### Option B: OpenAI-compatible server (Speaches, LocalAI, etc.)

Run any server that implements `POST /v1/audio/transcriptions`. Example with [Speaches](https://github.com/speaches-ai/speaches):

```bash
docker run --rm -p 8000:8000 ghcr.io/speaches-ai/speaches:latest
```

The endpoint is `/v1/audio/transcriptions`.

### Option C: FunASR/SenseVoice local server

[FunASR](https://github.com/modelscope/FunASR) can run a local
OpenAI-compatible transcription service, which keeps audio on your own machine
or LAN while letting Vocalinux use SenseVoice or Paraformer-family models:

```bash
pip install torch torchaudio
pip install funasr vllm fastapi uvicorn python-multipart
funasr-server --device cuda
```

The server listens on `http://localhost:8000` by default and exposes
`POST /v1/audio/transcriptions`. In Vocalinux, set:

- **Server URL**: `http://localhost:8000`
- **API Endpoint**: `OpenAI/FunASR (/v1/audio/transcriptions)`
- **Model**: `sensevoice`

Use `--device cpu` for CPU-only testing if your FunASR install supports it. A
remote GPU host works too: bind the server to the LAN interface, open the port,
and point Vocalinux at that host.

### Option D: Qwen3-ASR / vLLM chat-completions server

Qwen3-ASR exposes an OpenAI-style chat-completions server through `qwen-asr-serve`:

```bash
pip install -U "qwen-asr[vllm]"
qwen-asr-serve Qwen/Qwen3-ASR-0.6B \
    --gpu-memory-utilization 0.8 \
    --host 0.0.0.0 \
    --port 8000
```

Set the endpoint to `/v1/chat/completions` and the model to `Qwen/Qwen3-ASR-0.6B`.
The same client format can be used by other chat-completions audio servers that accept
`audio_url` content containing a base64 WAV data URL.

### Network checklist

- The server must be reachable from the client over HTTP or HTTPS.
- If you bind to `0.0.0.0`, open the port in your firewall (`ufw allow 8080/tcp`, etc.).
- For anything outside a trusted LAN, terminate TLS in front of the server (Caddy, nginx, Traefik) and require an API key — the audio you upload is private speech.
- If you plan to also use the server from a mobile dictation app, terminate TLS even on a LAN — most Android and iOS apps refuse cleartext HTTP regardless of network.

## Client-Side Setup (Vocalinux)

### Via the Settings dialog

The remote engine is a power-user option in the **Speech Engine** settings.

1. Launch Vocalinux and open **Settings → Speech Engine → Remote Server**.
2. Toggle **Use remote server** on. This overrides whatever local engine is selected above it.
3. Fill in the fields:
   - **Server URL**: base URL of the server, e.g. `http://192.168.1.100:8080` (no trailing slash needed; one is stripped automatically).
   - **API Key** (optional): sent as `Authorization: Bearer <key>`. Leave blank if your server doesn't require auth.
   - **API Endpoint**: pick **Whisper.cpp (`/inference`)**, **OpenAI/FunASR (`/v1/audio/transcriptions`)**, or **Chat audio (`/v1/chat/completions`)** to match your server.
   - **Model**: model identifier sent to compatible servers. Use `whisper-1` for classic OpenAI-style Whisper servers, `sensevoice` for FunASR/SenseVoice, or the server's actual model name such as `Qwen/Qwen3-ASR-0.6B`.
4. Click **Test Connection** — a successful test means the URL is reachable and credentials (if any) are accepted. A failure here is just a warning; Vocalinux will still try again on the first transcription.

Settings auto-save and re-initialise the engine immediately, so you can start dictating as soon as the test passes. Toggling the switch off restores the local engine selected on the Speech Engine tab.

### Via the config file

The same options live in `~/.config/vocalinux/config.json`:

```json
{
  "speech_recognition": {
    "engine": "remote_api",
    "remote_api_url": "http://192.168.1.100:8080",
    "remote_api_key": "",
    "remote_api_endpoint": "/inference",
    "remote_api_model": "whisper-1"
  }
}
```

Restart Vocalinux after editing the file by hand.

FunASR/SenseVoice example:

```json
{
  "speech_recognition": {
    "engine": "remote_api",
    "remote_api_url": "http://localhost:8000",
    "remote_api_key": "",
    "remote_api_endpoint": "/v1/audio/transcriptions",
    "remote_api_model": "sensevoice"
  }
}
```

## Wire Protocol Reference

If you're writing a custom server, here's exactly what the client sends.

### Request — whisper.cpp format (`/inference`)

```
POST {server_url}/inference HTTP/1.1
Authorization: Bearer <api_key>          # only if configured
Content-Type: multipart/form-data; boundary=...

--boundary
Content-Disposition: form-data; name="file"; filename="audio.wav"
Content-Type: audio/wav

<WAV bytes: 16 kHz, mono, 16-bit PCM>
--boundary
Content-Disposition: form-data; name="temperature"

0.0
--boundary
Content-Disposition: form-data; name="temperature_inc"

0.2
--boundary
Content-Disposition: form-data; name="response_format"

json
--boundary
Content-Disposition: form-data; name="language"

en
--boundary--
```

### Request — OpenAI-compatible format (`/v1/audio/transcriptions`)

```
POST {server_url}/v1/audio/transcriptions HTTP/1.1
Authorization: Bearer <api_key>
Content-Type: multipart/form-data; boundary=...

--boundary
Content-Disposition: form-data; name="file"; filename="audio.wav"
Content-Type: audio/wav

<WAV bytes>
--boundary
Content-Disposition: form-data; name="model"

whisper-1
--boundary
Content-Disposition: form-data; name="language"

en
--boundary--
```

### Request — chat-completions audio format (`/v1/chat/completions`)

```json
{
  "model": "Qwen/Qwen3-ASR-0.6B",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "audio_url",
          "audio_url": {
            "url": "data:audio/wav;base64,<base64 WAV bytes>"
          }
        }
      ]
    }
  ],
  "temperature": 0
}
```

The response is read from `choices[0].message.content`. If the server returns a leading
line such as `language English`, Vocalinux removes that metadata and injects only the
transcribed text.

### Response (`/inference` and `/v1/audio/transcriptions`)

```json
{ "text": "the transcribed utterance" }
```

For OpenAI-compatible FunASR/SenseVoice wrappers, extra metadata is allowed and
ignored by Vocalinux:

```json
{
  "text": "the transcribed utterance",
  "language": "en",
  "emotion": "neutral",
  "segments": [
    { "text": "the transcribed utterance", "start": 0.0, "end": 1.4 }
  ]
}
```

If `text` is not present, Vocalinux also accepts `transcript`, `transcription`,
or a `segments` list with per-segment `text` fields. If a SenseVoice wrapper
returns rich labels inline, for example `<|en|><|NEUTRAL|><|Speech|>hello`,
Vocalinux strips the leading labels before text injection.

Empty utterances should return `{"text": ""}`. HTTP 4xx/5xx responses are surfaced as transcription errors in the Vocalinux log.

### Language handling

- Vocalinux's UI language `auto` is sent as **no `language` field** (server auto-detects).
- `en-us` is normalised to `en`.
- Anything else is forwarded verbatim.

### Timeouts

- Connection test: **5 s**
- Transcription request: **30 s**

A request that exceeds the transcription timeout is logged and dropped; the next utterance is sent fresh.

## Verifying with `curl`

Quick sanity check without launching the GUI:

```bash
# Whisper.cpp server
curl -F file=@sample.wav \
     -F temperature=0.0 \
     -F response_format=json \
     http://192.168.1.100:8080/inference

# OpenAI-compatible
curl -H "Authorization: Bearer $API_KEY" \
     -F file=@sample.wav \
     -F model=whisper-1 \
     http://192.168.1.100:8000/v1/audio/transcriptions

# FunASR/SenseVoice
curl -F file=@sample.wav \
     -F model=sensevoice \
     http://localhost:8000/v1/audio/transcriptions

# Chat-completions audio
python scripts/benchmark_remote_asr.py \
    --server-url http://localhost:8000 \
    --endpoint /v1/chat/completions \
    --model Qwen/Qwen3-ASR-0.6B \
    sample.wav
```

The multipart endpoints should return JSON with a text field or one of the
compatible response shapes above.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Connection test reports "failed" | Wrong host/port, firewall, or server not running | Check `curl <url>` from the client; check server logs |
| HTTP 401/403 | API key missing or wrong | Set the **API Key** field; ensure the server is configured for that key |
| HTTP 404 on first send | Endpoint format mismatch | Switch the **API Endpoint** dropdown to the format your server actually exposes |
| FunASR/SenseVoice server returns model errors | Model field does not match the served model | Try `sensevoice`, `paraformer`, or the exact model configured on the server |
| Chat-completions server returns model errors | Model field doesn't match the served model | Set **Model** to the server's model identifier |
| SenseVoice labels appear in injected text | Wrapper returned labels somewhere other than the leading transcript prefix | Return plain text in `text` and put language/emotion/speech labels in JSON metadata |
| Transcription always empty | Server rejected the WAV (sample rate, channels) | Confirm server accepts 16 kHz mono 16-bit WAV; check server logs |
| First transcription is slow | Cold model load on the server | Warm the server before dictating, or increase the client timeout server-side |
| Garbled text in foreign language | Wrong `language` setting | Set the language explicitly in Settings instead of `auto` |

Logs live at `~/.local/share/vocalinux/vocalinux.log` (or wherever your `XDG_DATA_HOME` points). Look for lines tagged `Remote API` for client-side detail.

## Security Notes

- The API key is stored in plain JSON in `~/.config/vocalinux/config.json`. Treat that file the same way you treat any other secret on disk.
- Audio is sent as raw WAV — anyone on the wire can hear it. Use HTTPS for any deployment outside a fully trusted network.
- Vocalinux does **not** validate TLS certificate pins; standard system trust is used. Self-signed certs require importing the CA into your system trust store.
