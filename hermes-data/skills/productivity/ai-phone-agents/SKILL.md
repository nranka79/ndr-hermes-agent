---
name: ai-phone-agents
description: "Make automated AI phone calls to businesses: check availability, services, pricing. Covers Bland AI, Vapi, Retell, ElevenLabs voice cloning, Indian accent options, and call script design."
version: 1.0.0
author: Hermes
metadata:
  hermes:
    tags: [calling, phone, voice-agent, robocalling, bland-ai, vapi, retell, elevenlabs, outreach]
    category: productivity
    requires_toolsets: [terminal]
---

# AI Phone Agents Skill

Make automated AI-powered phone calls to businesses on behalf of the user.
The AI agent calls each number, asks pre-defined questions in a natural voice,
and returns structured results.

## When to Use

- User wants to call a list of businesses to check availability, pricing, or services
- User wants an AI to handle phone outreach instead of calling manually
- User wants calls made in their own voice (voice cloning)
- User asks about "robocalling", "AI calling", "voice agent", "automated calls"

## Service Comparison

| Service | Outbound Cost | Free Trial | Indian Accents | Voice Cloning | Ease of Setup |
|---------|--------------|------------|----------------|---------------|---------------|
| **Bland AI** | ~$0.09/min | ~$10 free credits | ✅ Several Indian English voices | ✅ Via ElevenLabs integration | ⭐⭐⭐ (easiest) |
| **Vapi** | ~$0.05-0.08/min | ~$10 free credits | ✅ Indian voice options | ✅ Native + ElevenLabs | ⭐⭐⭐ |
| **Retell AI** | ~$0.07-0.10/min | Trial credits available | ✅ Indian accents supported | ✅ Custom voice support | ⭐⭐ |
| **Vocode** (OSS) | Twilio cost only | Free (open source) | Twilio-based | ✅ DIY | ⭐ (complex) |
| **Play.ai** | ~$0.20/min | Limited free | ✅ Excellent Indian voices | ✅ Built-in cloning | ⭐⭐ |

## Voice Cloning with ElevenLabs (for "my voice")

ElevenLabs does **instant voice cloning** from a 30-second recording:

1. User records a short voice sample on their phone
2. Upload to ElevenLabs via their API or web interface
3. Get a `voice_id` for the cloned voice
4. Use that `voice_id` in Bland AI / Vapi as the agent's voice

**Cost:** ElevenLabs free tier ~10 min/month. Enough for 10-15 short calls.

**Supported by:** Bland AI (via ElevenLabs integration), Vapi (native custom voice).

## Call Script Design

A good AI call script for business inquiry:

### Structure

1. **Greeting** — "Hi, my name is [name] calling from Bangalore..."
2. **Purpose** — "I'm looking for a barber/salon and wanted to check a few things"
3. **Questions** (one at a time):
   - "Do you do men's haircuts?"
   - "What's the price for a men's haircut?"
   - "Do you offer facial services for men?"
   - "Do I need an appointment or can I walk in?"
   - "What are your open hours today?"
4. **Closure** — "Thank you, I'll visit. Goodbye"

### Pitfalls to handle

- **Voicemail**: Agent should leave a brief message with a call-back number
- **Busy signal / no answer**: Retry up to 2 times with 5-min spacing
- **Language switching**: Indian businesses may answer in Hindi/Kannada/Tamil.
  Configure the agent for Hindi + English for better coverage in Bangalore
- **Long hold**: If put on hold, the agent should wait up to 30 seconds
- **Transfers**: If transferred, the agent should re-introduce itself

## Integration Patterns

### Bland AI (simplest path)

```
1. Sign up at bland.ai → get API key
2. Configure an outbound call agent:
   - Agent prompt (system message describing the call purpose)
   - Voice model (pick Indian English voice or ElevenLabs cloned voice)
   - First message (what the agent says when the call connects)
3. POST /v1/calls with { phone_number, task, voice }
4. Receive call results (transcript + summary) via webhook or polling
```

### Vapi + ElevenLabs (best for custom voice)

```
1. Sign up at vapi.ai → get API key
2. Clone voice via ElevenLabs → get voice_id
3. Create Vapi assistant with:
   - ElevenLabs voice_id as the voice provider
   - System prompt for the conversation
4. POST /assistant/call with phone numbers
5. Results returned as conversation transcript
```

## Workflow for Calling Multiple Businesses

1. **Collect numbers** — from OSM places, Google Maps, or user-provided list
2. **Design the call script** — what questions to ask, what info to collect
3. **Set up the agent** — register with the calling service, configure voice
4. **Execute calls** — one API call per business (can parallelize)
5. **Parse results** — extract: { business_name: str, answers: dict, pricing: str, availability: bool, notes: str }
6. **Present to user** — structured table with findings

## Pitfalls

- **Call quality**: Bland AI and Vapi work well on Indian mobile networks.
  Test one call first before running a batch.
- **Business hours**: Call during business hours only. Check OSM `opening_hours`
  field before calling. For Indian salons: 10:00-21:00 typical.
- **Language**: Bangalore businesses commonly speak Kannada, Hindi, English.
  Configure the agent for **English+Hindi** dual language.
- **Free trial limits**: Bland AI $10 trial ≈ 100 min of calls. For 5 salons
  at ~3 min each = 15 min total. More than enough.
- **API key storage**: Keys for Bland AI, Vapi, ElevenLabs go in
  `/run/s6/container_environment/` (requires root) or env_passthrough in
  config.yaml. Keys are general service keys, not per-user.
- **Voice cloning latency**: ElevenLabs instant clone takes ~30 seconds to
  process. Do this first before setting up the calling agent.
