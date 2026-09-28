# Architecture

Status: planned. Nothing here is implemented yet; the diagrams describe the
design in the [README](../README.md) for the first version, a terminal
push-to-talk harness. Node names use the README's terms until code exists.

## Context

```mermaid
flowchart LR
    learner([Learner])
    subgraph local [Local machine: holds all API keys]
        harness[Terminal harness]
    end
    subgraph providers [External providers]
        stt[STT provider<br/>Soniox or AssemblyAI, TBD]
        llm[Model provider<br/>Bedrock / OpenAI / Anthropic]
        tts[TTS provider<br/>ElevenLabs Flash v2.5, provisional]
    end
    learner -- speech, Enter keys, transcript edits --> harness
    harness -- printed transcript and reply, audio --> learner
    harness -- recorded audio --> stt
    stt -- partial and final transcript --> harness
    harness -- conversation history + tutoring prompt --> llm
    llm -- tutor reply text --> harness
    harness -- reply text --> tts
    tts -- synthesized audio --> harness
```

Audio and transcripts leave the machine only to the three providers selected
for the session; there is no automatic failover to another provider.

## Components

```mermaid
flowchart TB
    cli[Startup config<br/>language, level, provider, model]
    capture[Audio capture]
    sttA[STT adapter]
    review[Transcript review<br/>accept / edit / discard]
    agent[Conversation agent<br/>tutoring policy + history]
    mapping[Provider mapping<br/>bedrock / openai / anthropic]
    ttsA[TTS adapter]
    playback[Playback]
    text[Text / prerecorded-audio input]

    cli --> agent
    capture -- audio --> sttA
    text -. test entry .-> review
    sttA -- final transcript --> review
    review -- committed transcript --> agent
    agent -- request --> mapping
    mapping -- reply --> agent
    agent -- reply text --> ttsA
    ttsA -- audio --> playback
```

The conversation agent owns the history and tutoring policy and depends on no
provider SDK; provider mappings, STT, and TTS are adapters around it.
Only committed transcripts reach the agent.

## Main flow: one turn

```mermaid
sequenceDiagram
    actor L as Learner
    participant H as Harness
    participant S as STT
    participant A as Conversation agent
    participant M as Model provider
    participant T as TTS

    L->>H: Enter (start recording)
    H->>S: stream audio
    L->>H: Enter (stop)
    S-->>H: final transcript
    H->>L: print transcript
    L->>H: accept / edit / discard
    H->>A: committed transcript
    A->>M: history + tutoring prompt
    M-->>A: reply
    A-->>H: reply text
    H->>L: print reply
    H->>T: reply text
    T-->>H: audio
    H->>L: play (microphone off, stoppable)
```

The manual Enter press, not silence detection, defines the turn boundary.

## State: harness turn loop

```mermaid
stateDiagram-v2
    [*] --> Idle: config validated
    Idle --> Recording: Enter
    Recording --> Transcribing: Enter
    Transcribing --> Reviewing: final transcript
    Transcribing --> Idle: empty transcript or STT error
    Reviewing --> Idle: discard
    Reviewing --> Responding: accept or edit
    Responding --> Speaking: reply received
    Responding --> Idle: provider error, shown to learner
    Speaking --> Idle: playback done or stopped
    Idle --> [*]: exit, close devices and connections
```

The microphone is active only in `Recording`, which prevents playback
feedback. Provider and model are fixed for the session.
