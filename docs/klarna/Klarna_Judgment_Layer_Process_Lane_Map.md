# Klarna Judgment Layer — Process Lane Map

**Companion to:** `Klarna_Judgment_Layer_Animation_Sequence_Map.md` (same 19 shots, same timecodes)
**Purpose:** fill the visual gaps — at every beat, what is happening in the story, what Klarna's automation is doing behind it, what manual work is actually occurring, and what stays with Klarna.
**Grounding:** `klarnafincrimereference_1.md` — 13 priced queue families, Tier A–D adjudication ladder, EMD field schemas, Identity API, L1/L2 role boundary, QA and governance ladders.

---

## 1. The headline recommendation: build two cuts, not one

The request is for real-process depth. The storyboard's cognitive-load rule says the opposite — one case token, one fixed architecture, no queue mechanics, no SLA clocks, no long evidence lists. Both are right, for different rooms.

**Resolve it by taking one extra layer off the same build:**

| | **Exec cut** | **Ops cut** |
|---|---|---|
| Runtime | 118 s | 118 s — identical timeline |
| Shots | The 19 in the sequence map | The same 19, unchanged |
| Audience | RFP evaluators, procurement, executive sponsors | FinCrime Ops, Risk, operational due diligence, orals Q&A |
| Extra layer | none | Lane rail · field-name sub-labels · queue tags · provenance chips |
| Answers | *Where does authority sit?* | *Yes, but what does the analyst actually do?* |

Same composition, same timings, same renders — the ops layer is a toggleable group. It costs one extra pass, and it is what survives the session where someone stops the video and asks what the analyst was looking at.

Everything in §4 below is authored as the ops layer. The exec cut simply hides it.

---

## 2. Provenance discipline — read this before anything goes on screen

RFP §1.12 treats unstated assumptions as acceptance. An animation that puts Klarna's internal wiring on screen is making claims under that rule, whether or not it intends to.

Every mechanic in §4 carries one of four tags. **The tag decides whether it can appear on screen unqualified.**

| Tag | Meaning | On-screen rule |
|---|---|---|
| **E** | **Evidenced** — published Klarna or RFP source: EMD field schemas, Identity API operations, the 13-queue list, queue SLAs, Tier D retained scope (§4.3), QA model (§7.1), quality ladders (§5.3, §6.1), Control Catalog | Show freely, including exact field names |
| **I** | **Inferred** — engine-to-queue and inter-queue wiring; Klarna-internal, not published (Assumptions Log #1, #2) | Show only under the existing footer, *"Illustrative operating model based on Klarna RFP workflows."* Never as confirmed Klarna wiring |
| **P** | **Foundever-proposed** — our operating design, not a Klarna requirement: L1→L2 triggers, L2 outcome authorities, four-eye and nesting placement, SAR Option B (Assumptions Log #4, #7) | Must read as a proposal. Where a frame carries several, label the frame *"Proposed operating model"* |
| **N** | **Narrative** — from the audio, carrying no process claim | Never dressed as a system state |

**Three hard prohibitions this creates:**

1. **No invented risk score.** Klarna publishes no thresholds. The threshold edge is labelled with the real edge condition — `cannot auto-clear` — not a number.
2. **No invented engine names.** Klarna's UK Privacy Notice v18 establishes that there are **five automated decision categories**; their contents are not published. Cite the count, never the contents.
3. **No itemised basket on the analyst's screen.** Per the Signals Available table, the purchase-category EMD packages carry **no** case-evidence value. The analyst receives the *flag* and the merchant category — not a shopping list. Drawing a basket of goods in the case file would be a visible process error to anyone who knows the data model.

---

## 3. Four persistent additions

Beyond the customer ribbon and the stakes overlay already specified in the sequence map:

### C — The automation river *(new; answers "what's happening back in automation")*

Clean case tokens stream continuously through Stage 1 at ~15% opacity **for the entire 118 seconds** — behind the L1 card, behind the stakes overlay, behind the boundary, behind everything.

This is the single most important visual correction available. The film as storyboarded implies automation hands off and waits. It does not. While one analyst spends minutes on one case, Klarna's engines are still clearing the clean majority, 24/7, uninterrupted. **Foundever's judgment layer is a side-channel on a river that never stops.**

It also silently proves the commercial shape of the deal: the exception rate is what Foundever is priced on, and the river is the denominator.

### D — The retained column stands, it does not queue *(new)*

From Shot 14 onward, Klarna's four retained-authority labels remain lit and **untouched** for the rest of the film. Klarna's authority is a standing property of the model, not a station the case passes through. See Decision **D6** — this is the difference between demonstrating governance and demonstrating a bottleneck.

### E — The lane rail *(ops cut only)*

A four-row rail down the left edge: **Story · Automation · Manual · Retained**. Rows light to show which lanes are live in the current beat. It is the literal answer to "fill in the gaps," and it makes the whole film legible as a process rather than a story with a diagram behind it.

The rail is also self-documenting: at Shot 2 the Manual row is conspicuously dark for eighteen seconds, which proves the "Foundever is absent from the clean path" claim continuously rather than in one two-second window.

### F — The SLA capsule *(ops cut only, optional)*

A thin capsule on the case card showing the **Q13 real-time monitoring 3 h** window `E`, filling imperceptibly. The case resolves in minutes; the capsule barely moves. The storyboard bars prominent SLA clocks, and it is right to — but at 5% of its own width, this one is a quiet proof rather than a mechanic.

---

## 4. The four lanes, shot by shot

**Lane key:** ▸ **Story** · ▸ **Automation** (Klarna, Tier A) · ▸ **Manual** (Foundever, Tier B/C = L1/L2) · ▸ **Retained** (Klarna, Tier D)

---

### Shot 1 · 0.00–8.34 · Thesis

| Lane | What is happening | Tag |
|---|---|---|
| Story | — title card — | N |
| Automation | Already running. The river starts at 4.0 s and never stops. | E |
| Manual | Nothing. | — |
| Retained | Column visible, unlit. | — |

**Fill:** begin the automation river here, at 15%, before the case exists. The viewer should never see a moment where Klarna's automation is idle.

---

### Shot 2 · 8.34–26.46 · The customer

| Lane | What is happening | Tag |
|---|---|---|
| Story | Tuesday 21:40. Checkout initiated on a €1,900 basket, from a device this account has not used, shipping to an address changed six days ago. | N |
| Automation | Klarna's risk assessment runs at checkout against account, payment-history, device and address data. Sanctions/PEP screening clean, straight-through. | E |
| Manual | **Nothing. Foundever has not been called and cannot be.** | E |
| Retained | Nothing. | — |

**What automation is actually reading** — real field names, all `E`:

| Row on screen | Source field | Package |
|---|---|---|
| `3 years` | `account_registration_date` | `customer_account_info` |
| `41 purchases` | `number_paid_purchases` | `payment_history_full` |
| `100% on time` | `total_amount_paid_purchases`, `date_of_first_paid_purchase` | `payment_history_full` |
| — | `paid_before` = true | `payment_history_simple` |
| — | `failed_transactions_attempts` = 0, `fraud_behavior` = false | `account_security` |
| `New device` | `device_id` new; `devices_linked` increments | `account_security` |
| `Address changed · 6 days` | `account_last_modified` | `customer_account_info` |
| — | `street_address`, `postal_code`, `city`, `shipping_method` | `other_delivery_address` |

**The market detail worth building the shot around** `E`:

€1,900 places this in a euro market. Per the Identity Data Keys by GEO table, Germany, Austria, the Netherlands and most EU markets anchor identity on **email + phone + billing details + DOB — no state registry key**. In Sweden, Norway, Finland or Denmark the national identification number would resolve this case in one lookup.

**That is why this case needs a human.** The film can make the point in one mono sub-label under the record card:

> `Market anchor: email + phone + billing — no registry key`

It is evidenced, it is specific, and it converts "judgment is valuable" from an assertion into a consequence of Klarna's own market footprint.

**Fill:** each record row carries its field name as a small mono sub-label. The Manual lane row on the rail stays visibly dark for all eighteen seconds.

---

### Shot 3 · 26.46–30.00 · Three signals

| Lane | What is happening | Tag |
|---|---|---|
| Story | — | — |
| Automation | Three flags surface from the engines and are attached to the order. | E / I |
| Manual | Nothing. | — |

**Chip source tags** (ops cut):

| Chip | Where it actually comes from | Tag |
|---|---|---|
| `New device` | `account_security.device_id` / `devices_linked` | E |
| `Address change` | `customer_account_info.account_last_modified` | E |
| `Unusual basket` | **Risk-engine output — not EMD.** Basket-level item data carries no case-evidence value | E |

**Fill:** the third chip must be tagged differently from the first two. It is a *conclusion the engine reached*, where the other two are *facts the record holds*. Drawing all three as equivalent data points is the most likely process error in this shot.

---

### Shot 4 · 30.00–36.94 · Threshold

| Lane | What is happening | Tag |
|---|---|---|
| Automation | The engines composite the three signals into one disposition. Klarna's UK Privacy Notice v18 establishes five automated decision categories; contents unpublished. | E |
| Manual | Nothing. | — |

**The threshold line's label is the real edge condition:**

> `cannot auto-clear`

That is the actual exit from the Tier A node in the escalation model — Tier A has exactly two exits, `straight-through` and `cannot auto-clear` `E/I`. It is stronger than any invented number and it cannot be challenged.

**Fill:** the count `5 automated decision categories` may appear as a small indigo tag. The categories themselves may not.

---

### Shot 5 · 36.94–40.74 · Routes out

| Lane | What is happening | Tag |
|---|---|---|
| Story | The order is held. Not declined, not cancelled. | E |
| Automation | Straight-through processing continues for the clean majority. One order is routed to a queue. | E / I |
| Manual | L1 receives at 40.74. | P |
| Retained | Nothing. | — |

**Name the queue.** This case is **Q13 · Fraud: 24/7 Real-Time Monitoring** `E` — real-time monitoring 3 h SLA, action monitoring 24 h `E`.

Three things in the narration make Q13 the only correct queue, and each is worth a beat of screen time:

1. **Tuesday, 21:40** — outside any business-hours model. Q13 is the 24/7 queue.
2. **"The customer never felt the review"** — resolution inside the checkout/fulfilment window. That is a real-time SLA, not an alert-review SLA.
3. **The outcome is a release**, not a SAR path. Q1 Transaction Monitoring escalates toward Q4 Investigations and SAR preparation; this case never goes there.

Routing this to Q1 instead — the intuitive choice, because "transaction monitoring" sounds like what happened — would misstate the SLA, the operating window, and the staffing model the queue is priced against.

**Fill:** the divergence path carries `Q13 · Fraud 24/7 · L1`. The order state reads `HELD` — never `DECLINED`. Note also that the merchant-side high-risk order loop (cancel or stop-delivery, 96 h) `E` exists as an option and is **not** used here.

---

### Shot 6 · 40.74–49.18 · L1 receives

| Lane | What is happening | Tag |
|---|---|---|
| Story | — | — |
| Automation | Order still held. 3 h clock running. River still running. | E |
| Manual | **Tier B / L1.** Owns standard case triage and standard evidence gathering; completes prescribed initial checks, records indicators and rationale. | P |
| Retained | Nothing. | — |

**"The new phone carries her credentials cleanly" — what that actually is** `E`:

| Check | Operation / field |
|---|---|
| Session validity on the linked account | `tokenIntrospect` — server-side token state check (RFC 7662 pattern) |
| Phone trust flag | `account_security.phone_verified` |
| Verification recency and method | `last_verification_method`, `last_verification_time` |
| Device count | `devices_linked` |

The finding is precise and worth stating precisely: **the device is new; the credential path is not.** A valid, non-revoked token presented from an unfamiliar device is a materially different fact from a credential presented after a reset — and it is the fact that keeps identity from resolving as an ATO.

**Fill:** the three case-card rows carry what was checked, in mono — `tokenIntrospect · ACTIVE` / `phone_verified · true` / `devices_linked · 3→4`.

---

### Shot 7 · 49.18–52.80 · Evidence resolves

| Lane | What is happening | Tag |
|---|---|---|
| Automation | Unchanged. Holding. | E |
| Manual | L1 resolves behaviour from payment history. Transaction context **cannot** resolve at L1. | P |

**Why the third row stays open — and this is evidenced, not a device** `E`:

The Signals Available table rates `other_delivery_address` as **Low-Medium: can support a first-party-fraud or mule-network pattern (address mismatch) but is rarely sufficient alone.**

So the row does not stay open for drama. It stays open because the only data bearing on it is, by Klarna's own data model, insufficient on its own. Put the reason on screen:

> `address mismatch — not sufficient alone`

**Fill:** that sub-label is the strongest single line in the L1 sequence. It converts the escalation from a narrative beat into a documented evidentiary limit.

---

### Shot 8 · 52.80–58.52 · The handoff

| Lane | What is happening | Tag |
|---|---|---|
| Manual | L1 → L2 escalation on a **named, defined trigger**. | P |

**The trigger has a name** — from the L1-to-L2 Escalation Logic table `P`:

| Field | Value |
|---|---|
| Category | **Fraud escalation** |
| Trigger | Account takeover, synthetic identity, organised fraud, repeated abuse, material loss, or network behaviour |
| L2 action | Investigate linked activity, assess control action, identify typology |

And the governing discipline, which belongs on screen as the label:

> **L1 does not escalate because a case is difficult. Escalation fires only on defined evidence, risk, complexity, or decision-authority conditions.**

**Fill:** the handoff object is a **structured referral template** `P` — a tagged, fielded object, never a free-text note. The difference is the whole argument for a certified activity level over a call centre.

---

### Shots 9–11 · 58.52–74.18 · The stakes overlay

| Lane | What is happening | Tag |
|---|---|---|
| Story | The two costs. | N |
| Automation | Still holding. Order pending, clock running, river running. | E |
| Manual | L2 framing the decision — not a process step. | N |
| Retained | Nothing. | — |

**Mark the whole overlay `N`.** It is the film's emotional core and it carries no process claim. Do not dress either column as a system state — see the ghosting constraint in the sequence map.

**Available grounding, for the deck rather than the film** `E`:

- Conventional IDV answers *is this a real person, are they who they claim*. First-party fraud requires a third question — *will this real, verified person commit fraud* — "answerable only with behavioral/contextual intelligence and human judgment" (LexisNexis 2026).
- 82% of payments-industry fraud targets authentication rather than new-account creation (Entrust 2026).

The first of those is the academic statement of exactly what this overlay dramatises. It belongs in PDF frame 4's "what this proves" line, not in the animation.

---

### Shot 12 · 74.18–82.70 · The inversion

| Lane | What is happening | Tag |
|---|---|---|
| Automation | Unchanged. Holding. | E |
| Manual | **Tier C / L2.** Linkage analysis; typology and red-flag assessment; documentation of both inculpatory **and exculpatory** evidence. | P |

**Caption this shot with the real process name:**

> `Exculpatory evidence documented`

The SAR workflow requires L2 to document "both inculpatory and exculpatory evidence" `P`. The reorder sequence *is* that documentation. There is no better available label — it is precise, it is in the operating model, and it names the thing most fraud operations never write down.

**Chip source tags as they reorder** (ops cut):

| Order | Chip | Field |
|---:|---|---|
| 1 | `Address updated` | `account_last_modified` |
| 2 | `then a device` | `devices_linked` |
| 3 | `then durable goods` | merchant category (engine), **not** basket items |
| — | connector | `same postal_code` |

**Fill:** the connector's label is the finding. `shipping to that same address` is the narration; `same postal_code` is the evidence. Show the second in mono beneath the first.

---

### Shot 13 · 82.70–85.82 · Relocation

| Lane | What is happening | Tag |
|---|---|---|
| Manual | Typology determined. Disposition set. | P |

**The disposition has a defined class** — from L2 Case Outcomes `P`:

> **Resolved: no report** — investigation does not meet the suspicious-activity or material-risk threshold; decision is fully documented. **L2 closes the case within delegated authority.**

**Fill:** the card gains two mono lines — `Typology: relocation · non-reportable` and `Disposition: resolved, no report`.

Note carefully what that second line commits to. It sets up Shot 14.

---

### Shot 14 · 85.82–90.18 · The boundary — **needs a decision**

| Lane | What is happening | Tag |
|---|---|---|
| Manual | Case released. | P |
| Retained | Standing authority, lit. | E |

**Klarna's retained scope, all `E`** — RFP §4.3, the FCC Specialist posting, and the Control Catalog:

`Policy interpretation` · `Material-risk decisions` · `SAR/STR filing authority` · `Risk appetite`

The Control Catalog adds four more that belong on the retained side and strengthen the frame: `Model risk management` · `Jurisdiction risk list` · `Business-wide risk assessment` · `Termination of customer relationships`.

**The problem.** The narration says *"Klarna keeps what only Klarna should hold. Klarna confirms."* But Shot 13 just established the disposition as **Resolved: no report**, which in our own proposed model **L2 closes within delegated authority**. Klarna does not decide a clean release.

Animating Klarna approving this case would therefore do three bad things at once:

1. Contradict the delegated-authority model we are bidding.
2. Trip the storyboard's explicit prohibitions — *"sending every case to Klarna"* and *"making Klarna look like a routine rework step."*
3. Understate the commercial proposition, which is precisely that Klarna's senior capacity is **not** consumed by cases like this one.

**Recommendation — Klarna confirms the boundary, not the case.** The narration supports this reading exactly: *"keeps what only Klarna should hold"* describes a standing column, not a transaction.

| Element | Treatment |
|---|---|
| Retained column | Lights, stands, stays **untouched**. Nothing queues on Klarna's side. |
| The case token | Stays on the Foundever side. Does not cross. Does not wait. |
| What crosses | A `Policy check · within delegated authority` confirmation, returning in under half a second. |
| What Klarna sees | The **decision log** `P` — case identifier, L2 investigator, approver, decision, rationale, filing status, timestamps. That is what "Klarna confirms" honestly means: real-time visibility over an authority that was already correctly exercised. |
| Also on the retained side | **Segregation of duties** `P` — an investigator cannot self-approve; the final approver is never the primary investigator. |

The alternative — animating a genuine Klarna approval step — is available if the reviewer wants it, but it should then be justified on screen by a stated escalation condition, and it makes the film argue for less delegated authority than the bid asks for. See **D6**.

---

### Shot 15 · 90.18–93.28 · The customer never felt it

| Lane | What is happening | Tag |
|---|---|---|
| Story | Order releases. It ships. | N |
| Automation | The hold clears; the order rejoins the normal fulfilment path. | E / I |
| Manual | Case record updated within authorised visibility limits. | P |

**The control that was not pulled** `E`. `tokenRevoke` is the account-takeover response control on a linked account — a Tier C decision. It was available throughout and was not invoked.

**Fill:** a small ghosted label, `tokenRevoke · not invoked`. It is the quietest beat in the film and one of the most credible: it shows the analyst had a live control in hand and correctly did not use it. Resolution lands well inside the Q13 3 h real-time window `E`.

---

### Shot 16 · 93.28–96.92 · QA

| Lane | What is happening | Tag |
|---|---|---|
| Manual | Vendor QA. | E |
| Retained | **Klarna AI-first QC on every case.** | E |

**QA is two gates with two owners, per RFP §7.1** `E` — and the storyboard's single mint gate understates it. Show both:

| Order | Gate | Owner | Colour |
|---:|---|---|---|
| 1 | Vendor QA — correct decision · complete evidence · compliant rationale | Foundever | Mint |
| 2 | **Klarna AI-first QC**, on every case | Klarna | Indigo |

**Be precise about four-eye.** Under the proposed operating model, four-eye review is triggered on **adverse disposition** and on **EDD files** `P`. This case is a clean release, so it is standard QA plus Klarna's AI QC — not four-eye. Animating a four-eye check here would overclaim a control that our own model does not apply to this path, and an operational reviewer will catch it.

**Keep off screen, put in PDF frame 7:** a quality failure means the case is **reopened unpaid and counts against the quality score** (RFP §5.3, §6.1) `E`. The storyboard bars commercial language from the main animation and is right to — but this is the sentence that makes QA a gate rather than a gesture, so it belongs in the still's "what this proves" line.

**Fill timing** inside the 2.00 s silence: vendor gate 93.60→94.50 (three 300 ms checks), Klarna AI QC pass 94.60→95.28 (indigo sweep), `Quality accepted` on 95.28.

---

### Shot 17 · 96.92–102.72 · The learning loop

| Lane | What is happening | Tag |
|---|---|---|
| Manual | Structured case insight produced from the closed case. | P |
| Retained | **Klarna decides whether anything changes.** | E |

**The honest mechanism, with a named control at each step:**

| Step | What happens | Owner | Tag |
|---|---|---|---|
| 1 | Case yields structured insight — risk pattern, decision outcome, control effectiveness | Foundever | P |
| 2 | **Feedback loop** — approved/rejected outcomes feed L2 coaching, QA calibration, and training | Foundever | P |
| 3 | **Model risk management** — validates models used for customer risk scoring and transaction monitoring **before deployment** | **Klarna, Tier D** | **E** |
| 4 | Detection, routing and controls change only after that validation | Klarna | E |

**This fully resolves the wording problem flagged as D4.** The narration's *"the next customer who moves apartments clears straight through"* is stronger than the storyboard's permitted register — but it becomes defensible the moment step 3 is on screen, because Klarna's own published control now gates the outcome. Put it on the return path in indigo:

> `Model risk management · Tier D · validated before deployment`

That single label is the difference between "our insight improves your model" (an unqualified autonomous-learning claim, which the storyboard forbids) and "our insight informs a change your governance validates" (accurate, and a stronger governance story besides).

**Honest context for the deck, not the film** `E`: Klarna states its AML/CTF framework is *in the process of being consolidated* with its consumer and merchant fraud processes. The loop is a live programme, not a finished one — which is an argument for the partner who produces structured insight now, not against it.

---

### Shot 18 · 102.72–105.48 · The pull-back

All four lanes visible simultaneously for the first and only time. The river still running. Nothing else moves.

**Fill:** if the lane rail is built, this is the shot where all four rows are lit at once — the film's only complete process frame.

---

### Shot 19 · 105.48–118.00 · Ring close

*"Thirteen queues. One governed judgment model."* — the 13 queue families are `E`, RFP §4.1. This is scope, not a capability claim, so it survives the storyboard's no-new-claims rule.

**Optional (ops cut):** the thirteen queue names ghost in around the settled architecture during the final hold. It converts the closing frame from a summary into a scope statement. Offered as a decision, not a default.

---

## 5. Provenance summary

| Tag | Count of distinct mechanics | Where the risk sits |
|---|---|---|
| **E** Evidenced | ~28 | None. Show freely. |
| **I** Inferred wiring | 3 | Engine-to-queue routing (Shots 4, 5, 15). Covered by the existing footer. |
| **P** Foundever-proposed | ~12 | Concentrated in Shots 6, 8, 12, 13, 16, 17 — the entire L1/L2 method. |
| **N** Narrative | 4 | Shots 1, 9–11, 15. |

**The exposure to manage:** almost everything the film shows Foundever *doing* is Foundever's proposed operating model, not Klarna's published process. That is expected — it is what a bid is — but under §1.12 it must read as a proposal.

**Mitigation, in order of preference:**

1. The existing footer already qualifies the whole film: *"Illustrative operating model based on Klarna RFP workflows."* Keep it on every frame, including the stills.
2. On the three frames that are almost entirely `P` — L1 triage, the escalation trigger, and the learning loop — add a second-line qualifier: **"Proposed operating model."**
3. Carry every `P` mechanic into the submission's Assumptions Log. Rows #4 and #7 already cover the four-eye placement and the L1→L2 trigger set; the animation adds no new assumption classes, which is the point of having built it this way.

---

## 6. Decisions this document adds

The sequence map opened D1–D5. These are new.

| ID | Decision | Recommendation |
|---|---|---|
| **D6** | Does Klarna **approve this case**, or **confirm the boundary** while L2 closes within delegated authority? | **Confirm the boundary.** Animating an approval contradicts the delegated-authority model we are bidding, trips two of the storyboard's own prohibitions, and argues for less autonomy than the commercial case needs. The narration supports the boundary reading exactly. This is the most consequential open call in the film. |
| **D7** | Build the ops layer (lane rail, field names, queue tags) as a toggleable group, or leave the exec cut as the only asset? | **Build both.** One extra pass on the same renders. The exec cut wins the evaluation; the ops cut wins the room where someone asks what the analyst actually did. |
| **D8** | Name the queue (`Q13 · Fraud 24/7`) on screen, or stay queue-agnostic? | **Name it.** It is evidenced, it makes the 21:40 timestamp and the real-time resolution mutually reinforcing, and it demonstrates we know which of the thirteen we are in. Q1 would be the intuitive guess and it would be wrong. |
| **D9** | Show the market-anchor line (*no registry key in euro markets*)? | **Yes.** One mono sub-label in Shot 2. It is the strongest available evidence that judgment is a structural requirement of Klarna's market footprint rather than a service we are selling. |
| **D10** | Show both QA gates (vendor + Klarna AI-first QC), or the single gate as storyboarded? | **Both.** §7.1 specifies Klarna AI QC on every case; a single mint gate understates Klarna's own control and wastes a governance proof that costs 0.7 s. |

---

## 7. Additions to the acceptance checks

- [ ] The automation river runs unbroken for all 118 s and is never idle.
- [ ] Foundever's lane is visibly dark for the whole of Shot 2, not just at the routing moment.
- [ ] No numeric risk score appears anywhere.
- [ ] No itemised basket appears in any case file.
- [ ] The third signal chip is visibly an engine conclusion, not a record fact.
- [ ] `Q13` is named, and the 3 h real-time window is consistent with the resolution shown.
- [ ] Nothing ever queues on Klarna's side of the boundary.
- [ ] Both QA gates appear, with their two owners visually distinct.
- [ ] `Model risk management · Tier D` is legible for the full learning-loop shot.
- [ ] Every frame carries the illustrative-model footer; the three `P`-heavy frames carry the proposed-operating-model qualifier.
