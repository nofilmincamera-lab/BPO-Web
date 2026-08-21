# Klarna Judgment Layer — Animation Sequence Map

**Cut to:** `Short_Audio_Track_Klarna.mp3` — measured duration **115.12 s**
**Recommended video length:** **118.0 s** (audio + 3.0 s silent final hold, per storyboard minimum)
**Aspect:** 16:9 · **Source storyboard:** `Klarna_Judgment_Layer_Animation_Storyboard.md`
**Grounding:** `klarnafincrimereference_1.md` (13 priced queue families; Tier A–D adjudication ladder; L2 vendor-scope ceiling)

> All timecodes below are measured from the delivered audio (word-level ASR, verified against the storyboard's beat structure). They are not estimates. Timings in the source storyboard are superseded by this document.

---

## 1. What changed between the storyboard and the audio

The storyboard was written for a **55–65 s abstract explainer**. The delivered audio is a **115 s narrative** built around one named case. It is the same operating model, but it is a different film, and four structural things do not carry over unmodified.

| # | Finding | Consequence |
|---|---|---|
| 1 | **The audio runs 2× the storyboarded length.** | Every stage duration in the storyboard's Timing Overview is void. Re-timed in §4. |
| 2 | **There is an 18-second case-setup passage (8.3–25.5 s) with no equivalent stage.** | The storyboard opens on a title card and moves straight to automation. The audio spends a sixth of its runtime establishing *who this customer is*. This needs its own visual treatment — see Shot 2. |
| 3 | **There is a 15-second stakes passage (58.5–73.1 s) with no equivalent stage.** | The asymmetry of decline-vs-approve is the emotional core of the audio and has no home in the six-stage model. Resolved as an **overlay on Stage 3**, not a seventh stage — see §3. |
| 4 | **Stage 5 (QA accepted) has no narration at all.** | The audio goes "Klarna confirms" → "the washing machine ships" → "the case closes." QA must play **silently**, in the 2.00 s gap at 93.28–95.28 s, or it does not appear. See Shot 16 and Decision D3. |

Two smaller divergences worth naming:

- **The outcome is an approval, not a fraud finding.** The storyboard is outcome-neutral. The audio resolves to a legitimate customer being cleared. This makes the **cost of a false positive** the primary proof, which is a stronger RFP argument but a narrower one.
- **The audio is a ring composition, not an open/close.** "Tasks are temporary, judgment is the service" appears at 0.0 s and again at 105.5 s. The storyboard's separate Opening Frame and Final Hold become **the same frame, twice** — same composition, different state. That is a feature; build it deliberately.

---

## 2. Verified narration with timecodes

Silences of ≥0.85 s are marked. **Every one of them is a shot change.** The read is unusually well-spaced — the gaps are the edit points, and no transition needs to be forced under a word.

| In | Out | Narration |
|---:|---:|---|
| 0.00 | 7.12 | Tasks are temporary, judgment is the service. That is our position, and one transaction will earn it. |
| | | *— 1.22 s —* |
| 8.34 | 25.50 | Tuesday, 9:40 at night. A customer three years on the books, 41 purchases, every installment paid on time, checks out a €1,900 basket. She is on a phone your systems have never seen, shipping to an address that changed six days ago. |
| | | *— 0.96 s —* |
| 26.46 | 29.14 | New device. Address change. Unusual basket. |
| | | *— 0.86 s —* |
| 30.00 | 36.02 | Each signal is explainable on its own. Together they cross a threshold the model was built to respect. |
| | | *— 0.92 s —* |
| 36.94 | 39.52 | The automation does its job. The case routes out. |
| | | *— 1.22 s —* |
| 40.74 | 47.82 | A Foundever analyst receives it as a structured case file. Identity confirms — the new phone carries her credentials cleanly. |
| | | *— 1.36 s —* |
| 49.18 | 52.30 | Behavior holds. Transaction context stays open. |
| 52.80 | 57.40 | And this is now the judgment call your automation was designed to route out. |
| | | *— 1.12 s —* |
| 58.52 | 59.24 | The stakes are asymmetric. |
| | | *— 1.34 s —* |
| 60.58 | 67.68 | Decline her, and a decision that should have been a yes ends a three-year relationship at the exact moment she is furnishing a new home. |
| | | *— 1.12 s —* |
| 68.80 | 73.12 | Approve a takeover, and the loss is yours to eat and yours to explain. |
| | | *— 1.06 s —* |
| 74.18 | 81.68 | The analyst reads the cluster whole. Address updated, then a device, then durable goods shipping to that same address. |
| | | *— 1.02 s —* |
| 82.70 | 84.32 | That is what relocation looks like. |
| | | *— 1.50 s —* |
| 85.82 | 88.80 | Klarna keeps what only Klarna should hold. Klarna confirms. |
| | | *— 1.38 s —* |
| 90.18 | 93.28 | The washing machine ships. The customer never felt the review. |
| | | *— 2.00 s (QA plays here) —* |
| 95.28 | 95.78 | The case closes. |
| | | *— 1.14 s —* |
| 96.92 | 102.72 | That history flows back into detection, and the next customer who moves apartments clears straight through. |
| | | *— 2.76 s (longest gap — the pull-back) —* |
| 105.48 | 109.14 | Tasks are temporary. Judgment is the service. |
| | | *— 1.86 s —* |
| 111.00 | 114.56 | That is Foundever. That is what we do. |
| | | *— 3.44 s silent hold to 118.00 —* |

Machine-readable word timings: [`audio_transcript_timings.json`](audio_transcript_timings.json).

---

## 3. Revised screen architecture

The storyboard's six persistent stages are retained unchanged. Two additions and one amendment.

### Retained (stationary for the full 118 s)

```
1 Klarna automation → 2 Foundever L1 → 3 Foundever L2 ‖ 4 Klarna retained → 5 QA accepted → 6 Klarna learns
                                                        ↑
                                          authority boundary (hard rule)
                                                        ↩ return loop 6 → 1
```

Plus the footer: *"Illustrative operating model based on Klarna RFP workflows."*

### Addition A — the customer ribbon

A **single thin mint line running the full width beneath the architecture**, labelled `Customer experience` at its left end. It is drawn at 0:00 and **never breaks, flickers, or changes colour for the entire film.**

This exists to pay off one line — *"the customer never felt the review"* (92.02 s) — and it can only pay off if the viewer has been unconsciously watching it stay unbroken for ninety seconds first. At 92.02 s it is the only element that brightens. Nothing else on screen moves.

Cost: one line of persistent furniture. Return: the film's second-best moment, earned rather than asserted.

### Addition B — the stakes overlay (not a seventh stage)

The 58.5–73.1 s asymmetry passage renders as a **modal overlay above Stage 3**, with the six-stage architecture still visible and dimmed behind it. It resolves and dismisses; the architecture never gained a step.

**Do not add a seventh stage for this.** The asymmetry is a property of the L2 decision, not a process step. A seventh box would break the "boundary sits between 3 and 4" rule that the entire governance proof rests on, and it would desynchronise this animation from every other six-stage diagram in the RFP response.

### Amendment — scale is allowed to change; the architecture is not

The storyboard's cognitive-load rule ("the architecture remains fixed, the case moves") was written for 60 seconds. Holding a fixed wide shot for 115 seconds will read as static.

**Recommendation:** the architecture stays absolutely fixed in *composition and order*, but the camera scales to the active stage during the long middle (40.7–84.3 s), then pulls back to full width at 102.72 s in the 2.76 s gap. Off-screen stages remain visible as edge-anchored labels so the viewer never loses the map.

This is a deliberate departure from the storyboard's stated rule. It is flagged as **Decision D1** in §7 — if the reviewer prefers the original constraint, the fallback is to hold wide throughout and carry the middle on evidence-card motion alone, which is viable but visually flatter.

### Visual grammar (unchanged from storyboard)

| Element | Colour |
|---|---|
| Klarna automation, Klarna retained | Indigo |
| Foundever L1, L2, judgment work | Mint |
| Threat / unresolved risk | Coral |
| QA gate | Dark navy, resolving to mint |
| Learning loop | Indigo→mint return path |
| Background | Warm white |

---

## 4. Shot-by-shot sequence

**19 shots.** Every cut falls in a silence. Durations are exact to the audio.

---

### Shot 1 — Thesis · 0.00 → 8.34 (8.34 s)

> *"Tasks are temporary, judgment is the service. That is our position, and one transaction will earn it."*

**Stage:** none active. **On screen:**

- Headline, centred: **Tasks are temporary. Judgment is the service.**
- Beneath, at 30% opacity: the complete six-stage architecture, already in its final position.
- Lower third: *One transaction will earn it.* — enters on the word "one" (5.82 s).

**Motion:** headline fades in over 350 ms. Architecture reveals left-to-right at 60 ms stagger, completing by ~4.0 s, then settles to 30%. Customer ribbon draws last, 4.0→5.0 s. No case token yet.

**Note:** the architecture is present but subordinate. The viewer should register "there is a system here" without being asked to read it. It gets read properly at 39.52 s.

---

### Shot 2 — The customer · 8.34 → 26.46 (18.12 s)

> *"Tuesday, 9:40 at night. A customer three years on the books, 41 purchases, every installment paid on time, checks out a €1,900 basket. She is on a phone your systems have never seen, shipping to an address that changed six days ago."*

**Stage:** Stage 1 lights; case token enters at left edge. **On screen:** a compact **customer record card** assembles beside the token, one row per narrated fact, each row landing on its own word:

| Lands at | Row | Treatment |
|---:|---|---|
| 8.34 | `Tue · 21:40` | Neutral |
| 11.06 | `3 years · account age` | Mint — positive history |
| 13.32 | `41 purchases` | Mint |
| 14.96 | `100% on time` | Mint |
| 17.80 | `€1,900 basket` | Neutral, holds |
| 20.46 | `New device` | **Coral** |
| 23.82 | `Address changed · 6 days` | **Coral** |

**Motion:** rows enter at 50–70 ms stagger, ease-out. The four mint rows accumulate as a visibly *good* record. At 20.46 s the tone turns: the last two rows arrive coral, and the mint rows above them desaturate slightly — not to red, just to *less certain*.

**Motion intent:** this is the whole reason the film works. The viewer must want this customer to be cleared **before** the system flags her. Eighteen seconds is a long time on screen, and it is spent buying the audience's sympathy. Do not shorten it and do not decorate it.

**Avoid:** a person, an avatar, a photograph, or a name. She is a record. The record is sympathetic on its own evidence.

**Note:** `Tue · 21:40` is doing quiet RFP work — it evidences the Q13 24/7 real-time monitoring requirement without a single word of claim. Keep it on screen for the full shot.

---

### Shot 3 — Three signals · 26.46 → 30.00 (3.54 s)

> *"New device. Address change. Unusual basket."*

**On screen:** three coral chips detach from the record card and align in a row beneath Stage 1:

| Lands at | Chip |
|---:|---|
| 26.46 | `New device` |
| 27.70 | `Address change` |
| 28.84 | `Unusual basket` |

**Motion:** each chip snaps into place on its stressed syllable, 300 ms entry. Sharp, clinical, evenly spaced. No alarm, no pulse, no sound-design cue.

**Critical:** these three chips are the film's spine. They persist — dimmed — from here to 84.32 s, and they **invert** at Shot 12. Build them as one component with two states.

**Avoid:** a fourth signal. The storyboard caps it at three and the audio names exactly three.

---

### Shot 4 — Threshold · 30.00 → 36.94 (6.94 s)

> *"Each signal is explainable on its own. Together they cross a threshold the model was built to respect."*

**On screen:** the three chips separate, each briefly showing a benign one-word rationale beneath it (`travel`, `moved`, `gift`) at ~40% opacity — then the rationales fade and the chips converge into a single cluster.

At 33.94 s ("cross") a horizontal **threshold line** appears through Stage 1. The clustered chips rise across it.

**Motion:** separate 30.0→32.9 s (slow, considered). Converge 32.92→33.94 s (fast). Cross 33.94→36.02 s.

**Motion intent:** individually innocent, collectively actionable. This is the single most important idea in the automation stage and it is carried entirely by the separate-then-converge motion.

**Wording discipline:** the threshold is one *the model was built to respect* — the automation is working correctly. Nothing on screen may imply detection failed.

---

### Shot 5 — Routes out · 36.94 → 40.74 (3.80 s)

> *"The automation does its job. The case routes out."*

**On screen:** four or five clean tokens stream through Stage 1 on the straight-through path and fade — Foundever's stages stay visibly empty while they pass. The flagged token diverges downward onto the judgment path toward Stage 2.

Caption, lower left: **Held for review, not declined.**

**Motion:** clean tokens 36.94→38.88 s. Divergence begins on "routes" (39.26 s), 450–600 ms travel, arriving Stage 2 at ~40.5 s.

**Motion intent:** the storyboard's hardest requirement — *Foundever is visibly absent from the clean path.* This 2-second window is the only place it can be proven. Make the clean tokens unmistakably numerous relative to the one exception.

**PDF frame 2** captures here.

---

### Shot 6 — L1 receives · 40.74 → 49.18 (8.44 s)

> *"A Foundever analyst receives it as a structured case file. Identity confirms — the new phone carries her credentials cleanly."*

**Stage 2 · Foundever L1.** **On screen:** the token lands and expands into an **L1 case card** with three empty evidence rows, plus compact queue / evidence / SLA markers (icons or two-word labels, never sentences).

At 44.52 s row 1 resolves:

> `Identity` → **Confirmed** *(credentials carried cleanly)* — turns mint

**Motion:** card expands 40.74→41.72 s. Three empty rows stagger in at 60 ms. Row 1 resolves at 44.52 s over 300 ms. Rows 2 and 3 stay open and visibly waiting.

**Avoid:** call-centre imagery, headsets, an avatar. And do not present L1 as a permanent team — it is a certified activity level (Tier B in the reference model).

---

### Shot 7 — Evidence resolves · 49.18 → 52.80 (3.62 s)

> *"Behavior holds. Transaction context stays open."*

**On screen:**

> `Behavior` → **Holds** — turns mint at 49.18 s
> `Transaction context` → **Open** — turns **coral, outlined not filled** at 50.90 s

**Motion:** row 2 resolves 300 ms. Row 3 does *not* resolve — it takes a slow 600 ms outline pulse and stops. The card now reads **2 confirmed · 1 open**.

**Note:** this is exactly the storyboard's Stage 3 spec ("two confirmed facts, one remaining uncertainty"), but the audio delivers it at the L1/L2 boundary. Follow the audio. The single open row is the entire justification for everything that follows — it must be the only unresolved thing on screen.

**PDF frame 3** captures here.

---

### Shot 8 — The handoff · 52.80 → 58.52 (5.72 s)

> *"And this is now the judgment call your automation was designed to route out."*

**On screen:** the case card slides from Stage 2 to Stage 3. The `Transaction context · Open` row lifts clear of the card and holds alone in the centre of Stage 3.

At 56.98 s a thin indigo line traces back from the open row to Stage 1 — the automation *pointing at* what it deliberately handed over.

**Motion:** card travel 52.80→53.60 s. Row lift 53.98→54.82 s. Trace-back 56.98→57.40 s, then fades.

**Motion intent:** the automation did not fail and did not guess. It correctly identified the boundary of its own competence. That trace-back line is the proof, and it is worth the 400 ms.

---

### Shot 9 — Asymmetry · 58.52 → 60.58 (2.06 s)

> *"The stakes are asymmetric."*

**On screen:** architecture dims to 25%. A two-column overlay opens above Stage 3. Both columns are empty. Header: **The stakes are asymmetric.**

**Motion:** dim 400 ms. Overlay opens 58.68→59.24 s. Then **1.34 s of held empty frame** — the longest deliberate emptiness in the film. Let it sit.

---

### Shot 10 — The cost of no · 60.58 → 68.80 (8.22 s)

> *"Decline her, and a decision that should have been a yes ends a three-year relationship at the exact moment she is furnishing a new home."*

**On screen:** left column fills:

> **Decline**
> `A decision that should have been yes`
> `3-year relationship · ends`
> `at the moment she is furnishing a new home`

Beside it, the mint rows from Shot 2 (`3 years`, `41 purchases`, `100% on time`) reappear at low opacity and **strike through, one by one**, at 64.56 / 64.92 / 65.46 s.

**Motion:** column header 60.58 s. Lines stagger 70 ms. Strike-throughs are slow, 400 ms each, deliberately uncomfortable.

**Hard constraint:** this is a **counterfactual**, and the storyboard forbids implying the customer was declined. Render the entire left column in **outline / ghosted treatment** — dashed borders, no fill, unmistakably a path *not taken*. It must never resolve into a state. Colour it coral only at the strike-throughs.

---

### Shot 11 — The cost of yes · 68.80 → 74.18 (5.38 s)

> *"Approve a takeover, and the loss is yours to eat and yours to explain."*

**On screen:** right column fills:

> **Approve a takeover**
> `Loss — yours to eat`
> `Explanation — yours to give`

Then both columns hold, equally weighted, for 1.06 s.

**Motion:** fill 68.80→73.12 s. Both columns hold 73.12→74.18 s, then the overlay dismisses upward over 400 ms and the architecture returns to full opacity.

**Motion intent:** the two columns must be **visually identical in weight**. The point is that neither error is cheap — that is what makes this judgment rather than a threshold. If one column looks heavier, the shot argues the opposite of the script.

**Avoid:** presenting this as fraud / not-fraud. It is **cost / cost**. Two prices, not two verdicts. Label the columns by consequence, never by verdict.

**PDF frame 4 (new)** captures here, both columns full.

---

### Shot 12 — The inversion · 74.18 → 82.70 (8.52 s)

> *"The analyst reads the cluster whole. Address updated, then a device, then durable goods shipping to that same address."*

**Stage 3 · Foundever L2.** This is the best shot in the film. Build it first.

The three coral chips from Shot 3 return to full opacity — still in the automation's **detection order**. Then the analyst **reorders them into causal order**, and each inverts to mint as it lands:

| Lands at | Moves to | Chip re-labels as | State |
|---:|---:|---|---|
| 76.92 | position 1 | `Address updated` | coral → **mint** |
| 78.52 | position 2 | `then a device` | coral → **mint** |
| 79.56 | position 3 | `then durable goods` | coral → **mint** |
| 80.48 | — | connector draws chip 3 → chip 1: `shipping to that same address` | mint |

**Motion:** each chip travels 450–600 ms, ease-in-out, arriving on its stressed word. Colour transition runs *during* travel, completing on arrival. The final connector draws 80.48→81.68 s, closing the loop.

**Motion intent:** **the reordering *is* the judgment.** Same three facts, same three chips — nothing new was fetched. What the analyst added was sequence, and sequence turned a threat cluster into a life event. This is the most defensible thing the film says about what human judgment buys, and it costs eight seconds and zero new information.

**Avoid:** any scoring dashboard, confidence percentage, or invented numeric precision. The chips are the evidence and the arrangement is the finding.

**PDF frame 5** captures at 81.68 s.

---

### Shot 13 — Relocation · 82.70 → 85.82 (3.12 s)

> *"That is what relocation looks like."*

**On screen:** the three mint chips consolidate into one mint block labelled **`Relocation`**. The `Transaction context` row from Shot 7 flips from coral-open to **mint-resolved**. The case card now reads **3 confirmed · 0 open**, with a recommendation line: `Recommendation documented`.

**Motion:** consolidation 82.70→83.98 s. Row flip 83.42 s. Card settles by 84.32 s, then 1.5 s of clean hold.

---

### Shot 14 — The boundary · 85.82 → 90.18 (4.36 s)

> *"Klarna keeps what only Klarna should hold. Klarna confirms."*

**Stage 4 · Klarna retained.** The governance proof. **On screen:** the vertical authority boundary between Stage 3 and Stage 4 becomes fully prominent. Four indigo retained-authority labels appear stacked in Stage 4:

`Policy interpretation` · `Material-risk decisions` · `SAR/STR filing authority` · `Risk appetite`

The completed evidence pack crosses the boundary. The **case token stays on the Foundever side** — only the pack crosses.

At 88.42 s Stage 4 returns a single indigo **`Confirmed`** stamp, and the token advances.

**Motion:** boundary strengthens 85.82→86.22 s. Labels stagger 60 ms, 86.22→87.54 s. Pack crosses 87.54→88.42 s. Stamp 88.42→88.80 s.

**Motion intent:** the viewer must be able to point at where supplier authority stops. That is the entire purpose of this 4.4 seconds.

**Hard constraints:**
- The token must **visibly not cross**. If the token crosses, the film says Foundever carried the authority over, and the governance argument collapses.
- No ambiguous shared-ownership zone. The boundary is a line, not a gradient.
- Do not imply Foundever files a SAR/STR. Per the reference model, the vendor scope ceiling is L2; production of the SAR-ready case file to Klarna's quality bar is the claim. Klarna signs.
- Klarna is not a rework step. `Confirmed` returns in under half a second.

**PDF frame 6** captures at 88.80 s.

---

### Shot 15 — The customer never felt it · 90.18 → 93.28 (3.10 s)

> *"The washing machine ships. The customer never felt the review."*

**On screen:** a small mint `Shipped` marker at 90.42 s. Then, at 92.02 s, **everything else on screen holds absolutely still** and the **customer ribbon** — unbroken since 0:05 — brightens once along its full length, left to right, over 900 ms.

**Motion:** ribbon sweep 92.02→92.90 s. Nothing else moves. No other element may animate in this window.

**Motion intent:** ninety seconds of governed machinery ran, and the line representing her experience never broke. The stillness is what sells it — if anything else moves, the shot is wasted.

---

### Shot 16 — QA · 93.28 → 96.92 (3.64 s)

> *(silence 93.28–95.28)* … *"The case closes."*

**Stage 5 · QA accepted.** **This shot has no narration and must carry itself.**

**On screen:** the case passes a restrained three-part gate, each check resolving in ~300 ms in the silence:

| Lands at | Check |
|---:|---|
| 93.60 | `Correct decision` |
| 94.10 | `Complete evidence` |
| 94.60 | `Compliant rationale` |

At 95.28 s the case receives **`Quality accepted`** and closes. The closed case **stays visible** — Shot 17 originates from it.

**Motion:** checks 300 ms each. Status stamp on "closes" (95.54 s). Closure is a settle, not a disappearance.

**Note:** the 2.00 s silence at 93.28 is the only room QA gets. It is enough for three 300 ms checks with breathing space, but only if the checks start immediately at 93.60 s. See **Decision D3** if the reviewer wants QA weighted more heavily — the only way to buy time is a VO pickup.

**Avoid:** confetti or celebration. A generic shield icon standing in for the whole QA story. "Billable" language.

**PDF frame 7** captures at 95.78 s.

---

### Shot 17 — The learning loop · 96.92 → 102.72 (5.80 s)

> *"That history flows back into detection, and the next customer who moves apartments clears straight through."*

**Stage 6 · Klarna learns.** **On screen:**

1. `96.92–97.56` — three small insight blocks lift out of the closed case: **`Risk pattern`** · **`Decision outcome`** · **`Control effectiveness`**
2. `97.56–98.60` — they enter Stage 6, labelled **Klarna-controlled learning**
3. `98.60–100.14` — they travel the return loop toward Stage 1 (1.5 s, within the storyboard's 1.2–1.6 s spec)
4. `100.14` — Stage 1 updates subtly: routing lines sharpen, one new pattern marker appears. **Subtle.**
5. `100.82` — a second case token enters at the left edge
6. `101.68–102.72` — it clears **straight through**, no stop, no coral, no diversion, and fades on the clean path

Governance label, fixed beside the return path for the whole shot:

> **Structured case insight informs future detection, routing, and controls.**

**Motion:** insight blocks stagger 70 ms. Loop travel is smooth and continuous, ease-in-out. The second token moves faster than the first did and never diverges.

**Wording discipline — the one place the audio outruns the storyboard.** The narration says the next customer *"clears straight through,"* which is stronger than the storyboard's permitted register (*informs*, *can improve*, *Klarna-controlled learning*). The on-screen governance label is what keeps the claim inside its bounds, so it is **not optional** and must be legible for the full 5.8 s.

Never show or say: the model automatically retrains · Foundever updates Klarna's model · every case changes the algorithm · any unqualified claim of autonomous production-model learning.

**Avoid:** starting a second full workflow. Shot 17 is 5.8 s and the second case gets 1.9 s of it.

**PDF frame 8** captures at 102.30 s.

---

### Shot 18 — The pull-back · 102.72 → 105.48 (2.76 s)

> *(silence — the longest gap in the film)*

**On screen:** camera pulls back to the full six-stage architecture in its settled state. All stages visible. Both cases resolved. The return loop lit. The customer ribbon unbroken.

**Motion:** a single continuous 2.76 s ease-out pull-back. Nothing else animates.

**Note:** this gap is why Decision D1 (scale changes) is worth taking. If the film has been scaled in through the middle, this is the exhale that makes the whole architecture legible again right before the thesis returns. If the reviewer rejects D1 and the film holds wide throughout, this shot becomes a 2.76 s dead hold — usable, but it gives away the film's best structural moment.

---

### Shot 19 — Ring close · 105.48 → 118.00 (12.52 s)

> *"Tasks are temporary. Judgment is the service."* … *"That is Foundever. That is what we do."*

**On screen:** the Shot 1 headline returns **in the identical position and type size** — but the architecture behind it is now at **full opacity and fully resolved**, where in Shot 1 it was at 30% and empty.

| Lands at | Element |
|---:|---|
| 105.48 | Headline returns: **Tasks are temporary. Judgment is the service.** |
| 108.12 | Word `judgment` receives a single mint emphasis |
| 111.00 | Supporting line: **Thirteen queues. One governed judgment model.** |
| 111.86 | Foundever logo, lower left |
| 112.88 | *Prepared for Klarna*, lower right |
| 114.56 | Audio ends — **hold static to 118.00 s (3.44 s)** |

**Brand treatment:** no additional statistics, no new capability claims, no motion in the hold.

**Motion intent:** the ring is the argument. Same sentence, same frame — but the first time the viewer had no reason to believe it, and now they have watched one transaction earn it, exactly as promised at 5.82 s.

**PDF frame 1** (the operating model) captures at 116.00 s, mid-hold, where the architecture is complete and settled.

---

## 5. Silence map

The read is well-spaced. Use it — no transition needs to be forced under a word.

| Gap | Length | Use |
|---|---:|---|
| 7.12–8.34 | 1.22 s | Thesis → case. Architecture recedes. |
| 25.50–26.46 | 0.96 s | Record card → signal chips. |
| 29.14–30.00 | 0.86 s | Chips settle before separating. |
| 36.02–36.94 | 0.92 s | Threshold crossed; hold before routing. |
| 39.52–40.74 | 1.22 s | Token travel into Stage 2 lands here. |
| 47.82–49.18 | 1.36 s | Row 1 mint; rows 2–3 visibly waiting. |
| 57.40–58.52 | 1.12 s | Architecture dims for the overlay. |
| **59.24–60.58** | **1.34 s** | **Empty two-column frame. Hold it. Do not fill.** |
| 67.68–68.80 | 1.12 s | Left column complete, right still empty. |
| 73.12–74.18 | 1.06 s | Both columns equal; overlay dismisses. |
| 81.68–82.70 | 1.02 s | Inverted cluster holds before consolidating. |
| 84.32–85.82 | 1.50 s | Clean card; boundary strengthens. |
| 88.80–90.18 | 1.38 s | Confirmed stamp settles. |
| **93.28–95.28** | **2.00 s** | **Entire QA sequence. Only room it gets.** |
| 95.78–96.92 | 1.14 s | Closed case holds; insight blocks prepare. |
| **102.72–105.48** | **2.76 s** | **The pull-back. Longest gap; biggest move.** |
| 109.14–111.00 | 1.86 s | Headline holds alone before branding. |
| 114.56–118.00 | 3.44 s | Final static hold. |

---

## 6. PDF companion frames — re-derived

The storyboard specifies six deliberate stills. The audio's structure argues for eight. Frames 4 and 7 are additions; if the deck is capacity-constrained, **cut frame 7 first** — QA reads adequately inside frame 8.

| # | Capture at | Title | What it proves | Status |
|---:|---:|---|---|---|
| 1 | 116.00 s | **The operating model** | Six governed stages, thirteen queues, one model | storyboard |
| 2 | 39.20 s | **Exception routing** | Automation works; Foundever is absent from the clean path | storyboard |
| 3 | 51.90 s | **Structured judgment** | L1 turns an alert into 2 confirmed, 1 open | storyboard |
| 4 | 73.00 s | **The stakes are asymmetric** | Why this is judgment and not a threshold | **new** |
| 5 | 81.68 s | **The same facts, read whole** | Reordering is the judgment — no new data required | storyboard (re-framed) |
| 6 | 88.80 s | **Retained authority** | The pack crosses; the authority does not | storyboard |
| 7 | 95.78 s | **Quality-accepted closure** | Decision, evidence, rationale all pass before close | **new** |
| 8 | 102.30 s | **Klarna-controlled learning** | Structured insight informs future detection, routing, controls | storyboard |

Each still keeps the storyboard's rules: one conclusion-led title, one dominant diagram, no more than three supporting labels (retained-authority terms excepted), one "what this proves" line.

---

## 7. Decisions needed before build

| ID | Decision | Recommendation |
|---|---|---|
| **D1** | Does the camera scale to the active stage through the middle (40.7–84.3 s), or hold wide for all 115 s? | **Scale.** A fixed wide shot for 115 s reads as static, and the 2.76 s pull-back at 102.72 s is wasted without it. The architecture's composition and order never change, which is what the cognitive-load rule actually protects. |
| **D2** | The outcome is an approval, not a fraud finding. Is the false-positive cost the argument we want leading? | **Yes, and say so in the deck.** It is the stronger commercial argument for an evaluator who already owns the fraud-loss case. Note that the film therefore does *not* demonstrate a confirmed-suspicion path — if evaluators need that, it is a second asset, not an extension of this one. |
| **D3** | QA gets 2.00 s of silence and no narration. Accept, or record a VO pickup? | **Accept.** Three 300 ms checks fit with room. A pickup would break the read's rhythm and the ring composition. If QA must be weighted more heavily for a specific evaluator, give it a dedicated PDF frame (frame 7) rather than more screen time. |
| **D4** | The narration's *"clears straight through"* is stronger than the storyboard's permitted learning register. | **Keep the audio; carry the qualification on screen.** The governance label beside the return path is mandatory and must hold for the full 5.8 s of Shot 17. Do not re-record. |
| **D5** | Is the customer ribbon (Addition A) in scope? | **Yes.** One line of persistent furniture, and it is the only way *"the customer never felt the review"* lands as evidence rather than assertion. |

---

## 8. Build order

Not chronological. Build the shots that carry the argument first, so a failure is discovered while it is still cheap.

1. **Shot 12 — the inversion.** The film's central idea. If the chip reorder does not read clearly, nothing downstream matters.
2. **Shot 14 — the boundary.** The governance proof, and the one shot an RFP evaluator will scrub back to.
3. **Shots 2 + 10** — the record card and its strike-throughs. Same component, two states; build them together.
4. **Shot 17** — the learning loop, with the governance label locked in from the first pass.
5. **Shot 3 + persistent architecture** — the three-chip component and all stationary furniture.
6. **Shots 1 + 19** — the ring. Build as one composition with two states, never as two frames.
7. Everything else.

---

## 9. Acceptance checks

Carried from the storyboard's production checklist, plus four this cut adds.

- [ ] The proposition is legible within five seconds.
- [ ] Stage order and composition never change; only scale and the case move.
- [ ] Foundever is visibly absent from the clean automated path (36.94–39.52 s).
- [ ] L1 and L2 have distinct purposes — L1 structures, L2 resolves sequence.
- [ ] The authority boundary is a hard line, and the **token does not cross it**.
- [ ] QA resolves before closure, not after.
- [ ] The learning loop returns insight to Klarna-controlled automation, with the governance label legible throughout.
- [ ] The second case completes without starting a new story.
- [ ] Every beat has a clean, printable settled frame.
- [ ] **The three signals invert rather than being replaced** — same chips, reordered and recoloured.
- [ ] **The decline column never resolves into a state** — ghosted and dashed for its full life.
- [ ] **The customer ribbon is unbroken from 0:05 to 118:00**, and brightens exactly once.
- [ ] **Shots 1 and 19 are the same composition** in two states, not two different frames.

### Final comprehension test

Show frame 8 for five seconds, then hide it. The viewer should be able to say:

> Klarna's automation flags what it should. Foundever resolves the judgment. Klarna keeps the decisions that are Klarna's. QA gates the close. And the next case is better informed.
