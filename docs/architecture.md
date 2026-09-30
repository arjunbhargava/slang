# Architecture

**Status: planned.** Nothing here is implemented yet. The diagrams describe the
[README](../README.md) design for the first version: a terminal push-to-talk
harness. Node names use the README's terms until code exists.

## How to read this doc

The four diagrams zoom in step by step. Each one answers a single question, and
names and colours stay the same across all four, so you can follow a box from
one diagram to the next.

1. [Context](#1-context): what does slang talk to?
2. [Components](#2-components): what are its parts, and what flows between them?
3. [One turn](#3-one-turn): what happens, in order, when the learner speaks?
4. [Turn states](#4-turn-states): what can the harness be doing at any moment?

Start with the legend. Every diagram uses only these shapes and lines.

```mermaid
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryColor: "#faf9f5"
    primaryTextColor: "#141413"
    primaryBorderColor: "#8a887f"
    lineColor: "#8a887f"
    edgeLabelBackground: "#faf9f5"
    clusterBkg: "#faf9f5"
    clusterBorder: "#b0aea5"
  flowchart:
    curve: linear
    nodeSpacing: 40
    rankSpacing: 56
    padding: 14
---
flowchart LR
    accTitle: Diagram legend
    accDescr: One example of each node kind, edge kind, and boundary used in this doc.

    person([Person])
    subgraph boundary [Trust boundary]
        core(<b>Core</b><br/>owns state or policy)
        module(<b>Module</b><br/>adapter or plumbing)
    end
    external[External service]

    person ==>|primary path| core
    core -->|data flow| module
    module -.->|optional or test-only| external

    classDef person fill:#e0e3d7,stroke:#788c5d,stroke-width:1.5px,color:#141413
    classDef core fill:#f3dfd5,stroke:#d97757,stroke-width:2px,color:#141413
    classDef module fill:#faf9f5,stroke:#8a887f,stroke-width:1px,color:#141413
    classDef external fill:#dde6ed,stroke:#6a9bcc,stroke-width:1.5px,color:#141413
    classDef boundary fill:#faf9f5,stroke:#b0aea5,stroke-dasharray:5 4,color:#5e5d59
    class person person
    class core core
    class module module
    class external external
    class boundary boundary
```

| Element | Looks like | In slang |
|---|---|---|
| Person | Green stadium | The learner. In the state diagram, a green state is waiting for the learner. |
| Core | Orange rounded box | Code that owns conversation state or tutoring policy. Start reading here. |
| Module | Plain rounded box | Code we own that moves data: audio, adapters, terminal input and output |
| External service | Blue square box | A paid provider API reached over the network |
| Trust boundary | Dashed region | The learner's machine, which holds every API key |
| Primary path | Thick arrow | The route a spoken turn takes; follow it first |
| Data flow | Arrow, labelled with what moves | Always a noun: `audio`, `reply text` |
| Optional or test-only | Dotted arrow | Test entry points and paths that aren't always taken |

## Glossary

| Term | Meaning |
|---|---|
| STT | Speech-to-text: turns recorded audio into a transcript. |
| TTS | Text-to-speech: turns the tutor's reply into audio. |
| Model provider | The LLM API that generates tutor replies: Bedrock, OpenAI, or Anthropic. Fixed for a session. |
| Turn | One learner utterance and the tutor's reply. The learner starts and ends it with Enter. |
| Partial transcript | STT output shown while the learner is still speaking. It never enters the conversation. |
| Committed transcript | The transcript the learner accepted or edited. Only this enters the conversation history. |
| Tutoring policy | The app-owned instructions: target language, learner level, and when to correct. |

## 1. Context

What does slang talk to, and what crosses the edge of the learner's machine?

```mermaid
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryColor: "#faf9f5"
    primaryTextColor: "#141413"
    primaryBorderColor: "#8a887f"
    lineColor: "#8a887f"
    edgeLabelBackground: "#faf9f5"
    clusterBkg: "#faf9f5"
    clusterBorder: "#b0aea5"
  flowchart:
    curve: linear
    nodeSpacing: 40
    rankSpacing: 56
    padding: 14
---
flowchart LR
    accTitle: Context diagram
    accDescr: The learner uses the terminal harness on their machine, which calls three external providers.

    learner([Learner])
    subgraph machine [Learner's machine · holds all API keys]
        harness(Terminal harness)
    end
    stt[<b>STT provider</b><br/>Soniox or AssemblyAI]
    llm[<b>Model provider</b><br/>Bedrock · OpenAI · Anthropic]
    tts[<b>TTS provider</b><br/>ElevenLabs]

    learner ==>|speech, edits| harness
    harness ==>|audio → transcript| stt
    harness ==>|history → reply| llm
    harness ==>|reply → speech| tts

    classDef person fill:#e0e3d7,stroke:#788c5d,stroke-width:1.5px,color:#141413
    classDef core fill:#f3dfd5,stroke:#d97757,stroke-width:2px,color:#141413
    classDef external fill:#dde6ed,stroke:#6a9bcc,stroke-width:1.5px,color:#141413
    classDef boundary fill:#faf9f5,stroke:#b0aea5,stroke-dasharray:5 4,color:#5e5d59
    class learner person
    class harness core
    class stt,llm,tts external
    class machine boundary
```

Each arrow is one request and its response (`request → response`).
Audio and transcripts leave the machine only to the three providers chosen for
the session. If a provider fails, the error is shown; the harness never
silently switches to another one.

## 2. Components

What are the harness's parts, and what flows between them?

```mermaid
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryColor: "#faf9f5"
    primaryTextColor: "#141413"
    primaryBorderColor: "#8a887f"
    lineColor: "#8a887f"
    edgeLabelBackground: "#faf9f5"
    clusterBkg: "#faf9f5"
    clusterBorder: "#b0aea5"
  flowchart:
    curve: linear
    nodeSpacing: 40
    rankSpacing: 56
    padding: 14
---
flowchart TB
    accTitle: Component diagram
    accDescr: Audio flows from capture through STT and review into the conversation agent, whose reply flows through TTS to playback.

    capture(Audio capture)
    sttA(STT adapter)
    review(<b>Transcript review</b><br/>accept · edit · discard)
    agent(<b>Conversation agent</b><br/>history · tutoring policy)
    mapping(Provider mapping)
    ttsA(TTS adapter)
    playback(Playback)
    textIn(<b>Test input</b><br/>text or recorded audio)

    capture ==>|audio| sttA
    sttA ==>|final transcript| review
    textIn -.->|test input| review
    review ==>|committed transcript| agent
    agent <-->|request, reply| mapping
    agent ==>|reply text| ttsA
    ttsA ==>|audio| playback

    classDef core fill:#f3dfd5,stroke:#d97757,stroke-width:2px,color:#141413
    classDef module fill:#faf9f5,stroke:#8a887f,stroke-width:1px,color:#141413
    class agent core
    class capture,sttA,review,mapping,ttsA,playback,textIn module
```

The conversation agent is the core. It owns the history and the tutoring policy,
and it imports no provider SDK. Everything else is an adapter around it, so a
provider can change without touching tutoring logic. Only committed transcripts
reach the agent.

## 3. One turn

What happens, in order, from the first Enter to the end of playback?

```mermaid
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryTextColor: "#141413"
    lineColor: "#8a887f"
    actorBkg: "#faf9f5"
    actorBorder: "#8a887f"
    actorTextColor: "#141413"
    actorLineColor: "#b0aea5"
    signalColor: "#8a887f"
    signalTextColor: "#141413"
    noteBkgColor: "#e8e6dc"
    noteBorderColor: "#b0aea5"
    noteTextColor: "#141413"
    sequenceNumberColor: "#faf9f5"
  sequence:
    mirrorActors: false
    messageMargin: 36
    boxMargin: 8
---
sequenceDiagram
    accTitle: One turn
    accDescr: The learner records, reviews the transcript, and hears the tutor's spoken reply.
    autonumber

    participant L as Learner
    participant H as Harness
    participant S as STT provider
    participant A as Conversation agent
    participant M as Model provider
    participant T as TTS provider

    rect rgb(250, 249, 245)
        Note over L,T: Record
        L->>H: Enter
        H->>S: stream audio
        L->>H: Enter
        S-->>H: final transcript
    end
    rect rgb(240, 238, 230)
        Note over L,T: Review
        H->>L: show transcript
        L->>H: accept or edit
    end
    rect rgb(250, 249, 245)
        Note over L,T: Respond
        H->>A: committed transcript
        A->>M: history + policy
        M-->>A: reply
        A-->>H: reply text
    end
    rect rgb(240, 238, 230)
        Note over L,T: Speak (microphone off)
        H->>T: reply text
        T-->>H: audio
        H->>L: play audio, stoppable
    end
```

The Enter key, not silence detection, marks the end of the learner's turn.
The microphone is off during playback, so the tutor's voice is never transcribed.

## 4. Turn states

What can the harness be doing at any moment, and what moves it on?

```mermaid
---
config:
  theme: base
  fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
  themeVariables:
    fontSize: 15px
    primaryColor: "#faf9f5"
    primaryTextColor: "#141413"
    primaryBorderColor: "#8a887f"
    lineColor: "#8a887f"
    edgeLabelBackground: "#faf9f5"
---
stateDiagram-v2
    accTitle: Turn states
    accDescr: The harness cycles from Idle through recording, review, response, and playback, returning to Idle on success, discard, or error.

    [*] --> Idle: config valid
    Idle --> Recording: Enter
    Recording --> Transcribing: Enter
    Transcribing --> Reviewing: transcript ready
    Transcribing --> Idle: empty or STT error
    Reviewing --> Responding: accept or edit
    Reviewing --> Idle: discard
    Responding --> Speaking: reply ready
    Responding --> Idle: provider error shown
    Speaking --> Idle: done or stopped
    Idle --> [*]: exit

    classDef person fill:#e0e3d7,stroke:#788c5d,stroke-width:1.5px,color:#141413
    classDef module fill:#faf9f5,stroke:#8a887f,stroke-width:1px,color:#141413
    class Idle,Recording,Reviewing person
    class Transcribing,Responding,Speaking module
```

Green states wait for the learner; plain states are the harness working.
Every failure returns to `Idle` with the error shown, so the learner can always
start another turn. The microphone is open only in `Recording`. Exit closes the
audio devices and provider connections.
