# Pre-built / Out-of-the-Box Discord Voice Transcription Tools

## Managed Discord Bots (zero setup)

These require no code — just add them to the server:

| Bot | Notes |
|---|---|
| **Craig** (craig.chat) | Records multi-track audio per user; exports to various formats; post-processing transcription via Otter.ai or similar |
| **SeaVoice** (voice.seasalt.ai) | Live speech-to-text captions in voice channels; uses its own STT engine |
| **DiscMeet** | AI note-taking and transcription in 100+ languages; meeting-summary focused |
| **Otter.ai bot** | Can be invited to Discord meetings; produces transcripts with speaker labels |
| **Fireflies.ai** | Similar to Otter; focused on meeting notes and action items |

These are the easiest path if the goal is just transcription records, but they give no programmatic access to the text for command input.

## Self-Hosted Bot Frameworks (pre-built, configurable)

Open-source bots you deploy yourself, giving access to the transcript output:

| Project | Stack | STT Backend |
|---|---|---|
| **Craig** (self-hosted) | Node.js | Configurable; can pipe to Whisper |
| **disco-whisper** | Python + discord.py | OpenAI Whisper (local) |
| **Real-Time Transcription Bot** (C4se-K) | Python + discord.py | faster-whisper |
| **V.O.L.O** | Python + Pycord | Whisper |
| **discord-speech-to-text** (vadimkantorov) | Python | Google Cloud STT |

These give a running bot with transcription already wired up, but customising for command dispatch means forking the code.

## The Core Library Stack (build-your-own)

**Layer 1 — Audio Capture from Discord**

Discord's official libraries deliberately omit audio receive. All options are unofficial:

| Library | Language | Approach |
|---|---|---|
| `discord-ext-voice-recv` | Python (discord.py extension) | `AudioSink` API; most compatible with discord.py |
| **Pycord** (fork) | Python | `start_recording()` built-in; first-class support |
| `discord-ext-listening` | Python (discord.py extension) | Multiprocessing-based for efficiency |
| `@discordjs/voice` | Node.js | Official voice library for Discord.js; has receive support |

**Layer 2 — Speech-to-Text**

| Option | Type | Latency | Cost | Best For |
|---|---|---|---|---|
| **faster-whisper** | Local | 1–5s (CPU), <1s (GPU) | Free | Offline, privacy-sensitive |
| **openai-whisper** | Local | Slower than faster-whisper | Free | Simple setup |
| **Whisper API** (OpenAI) | Cloud | ~1s | ~$0.006/min | No local compute needed |
| **Deepgram** | Cloud streaming | ~100–200ms | Usage-based | True real-time |
| **AssemblyAI** | Cloud streaming | ~300ms | ~$0.15/hr | Conversational AI, turn detection |
| **Google Cloud STT** | Cloud | ~300ms | Usage-based | Enterprise, 99+ languages |
| **Azure Cognitive Services** | Cloud | ~300ms | Usage-based | Microsoft ecosystem |

## Key Technical Challenge

Discord sends audio as per-user Opus streams but lacks synchronisation/control packets in the receive path. Every implementation needs **Voice Activity Detection (VAD)** to segment audio into utterances before sending to STT. Common approaches:

- **Silence-based**: buffer until N milliseconds of silence (simple, works on CPU)
- **`webrtcvad`**: Google's WebRTC VAD library; accurate, low overhead
- **Silero VAD**: ML-based, more accurate, slightly heavier
