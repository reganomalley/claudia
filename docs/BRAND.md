# Claudia Brand Guide

## Identity

**Claudia** is a proactive technology mentor for Claude Code. She's the senior dev who sees your mistake before you do -- and explains why it matters instead of just fixing it.

**Tagline options** (pick one, test in context):
- "The mentor in your terminal"
- "10 domains. 7 hooks. One opinionated mentor."
- "She catches what you miss"

## Personality

| Trait | Expression |
|-------|-----------|
| Direct | Gives the answer first, then explains why |
| Opinionated | Has a clear recommendation, shows the trade-offs |
| Warm but not soft | Tells you the truth without being a jerk about it |
| Curious | Asks what your constraints are before prescribing |
| Honest about limits | "I don't know" over a confident guess |

**Voice examples:**
- Good: "Use Postgres. It handles 90% of use cases and you already know SQL. Switch to Mongo only if your data is truly schemaless and you're writing more than you're reading."
- Bad: "It depends on your use case! Both are great options."
- Good: "Your prompt is too vague. 'Make it better' gives Claude nothing to work with. Try: 'Refactor the auth middleware to use async/await and add error handling for expired tokens.'"
- Bad: "Perhaps you could consider being more specific in your request?"

## Visual Identity

### Color Palette

**Primary: Vermillion Red** `#E63B2E`
- The main brand color. Used for logo background, CTAs, accent highlights
- Warm, energetic, distinct from Claude (tan/orange), GitHub (purple), VS Code (blue)
- Confident without being aggressive

**Secondary: Void Black** `#0A0A0A`
- Text, code blocks, dark backgrounds
- Near-black, not pure #000 (easier on eyes)

**Tertiary: Paper White** `#FAFAF8`
- Backgrounds, cards, breathing room
- Warm white, not clinical

**Accent: Signal Orange** `#FF6B35`
- Warnings, hover states, secondary CTAs
- Bridges between vermillion and white

**Code/Terminal: Soft Gray** `#2A2A2E`
- Code block backgrounds
- Terminal mockup backgrounds

| Swatch | Hex | Usage |
|--------|-----|-------|
| Vermillion | #E63B2E | Primary brand, logo bg, CTAs |
| Void Black | #0A0A0A | Text, dark sections |
| Paper White | #FAFAF8 | Backgrounds |
| Signal Orange | #FF6B35 | Accents, warnings |
| Soft Gray | #2A2A2E | Code blocks |

### Typography

**Wordmark:** `JetBrains Mono` or `Berkeley Mono` -- monospace because Claudia lives in the terminal. The name "claudia" is always lowercase in the wordmark.

**Headings:** `Inter` or `Satoshi` -- clean geometric sans-serif. Strong but not cold.

**Body:** Same sans-serif as headings, lighter weight.

**Code:** `JetBrains Mono` -- matches the wordmark, reinforces the terminal identity.

### Logo

The logo is a **stylized woman's face** in flat illustration style -- minimal, geometric, recognizable at 16x16px.

**Key attributes:**
- Slightly turned head, not straight-on
- One eyebrow raised or knowing smirk (the "I see what you did" expression)
- Dark hair, simple shapes
- Works in: full color (vermillion bg), monochrome (black on white), inverse (white on black)

**Logo lockup:**
```
[icon] claudia
```
Icon + lowercase monospace wordmark. Horizontal lockup is primary. Icon alone for favicons/avatars.

### Illustration Style

- **Flat geometric** -- inspired by Malika Favre, Noma Bar
- **Limited palette** -- max 3 colors per illustration (vermillion, black, white)
- **Subtle grain/stipple texture** -- adds warmth, avoids looking sterile
- **No gradients** -- flat fills only
- **Character poses** for different states:
  - Thinking (hand on chin) -- loading, processing
  - Pointing -- directing attention to a recommendation
  - Arms crossed, smirking -- caught an anti-pattern
  - Magnifying glass -- health audit scanning
  - Waving -- onboarding, welcome

### What the Brand is NOT

- Not dark/moody/atmospheric (save that for Tunnel and Convent)
- Not cutesy/kawaii (she's a senior dev, not a mascot pet)
- Not corporate/enterprise (she has personality)
- Not mysterious (she's transparent and direct)
- Not gendered in a limiting way (the illustration should be stylized enough to be iconic, not realistic enough to be exclusionary)

## Photography/Imagery Rules

- No stock photos ever
- All imagery is illustration or UI screenshots
- Terminal screenshots use the brand's Soft Gray background
- Feature demos are real -- show actual Claudia output, not mockups

## Social Media

**GitHub avatar:** Logo icon on vermillion background
**Twitter/X:** Same icon, banner shows tagline + feature summary
**README badge:** `[![Claudia](badge-url)](claudia.dev)` -- vermillion badge with white text

## Tone in Different Contexts

| Context | Tone |
|---------|------|
| README | Professional but personality-forward. "Here's what I do, here's how to install me." |
| Website hero | Confident, slightly playful. "She catches what you miss." |
| Error messages (hooks) | Direct, helpful. "Blocked: AWS access key detected. Use environment variables instead." |
| Advice (skills) | Opinionated mentor. Recommendation first, reasoning second. |
| Social/launch | Energetic but not hype. Show, don't tell. |
