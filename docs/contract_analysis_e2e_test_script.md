# Contract Analysis Agent - End-to-End Test Script

**Date:** January 8, 2026
**Endpoint:** `https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function`
**Agent:** ContractAnalysisAgent
**Perspective:** Record Label (Contoso Records use case)
**Status:** All Tests Passed

---

## Overview

This document contains the complete end-to-end test results for the Contract Analysis Agent, demonstrating its ability to analyze recording contracts from the **record label's perspective**. All tests were run against the live production endpoint.

### Key Capabilities Tested
- Contract listing and discovery
- Full contract workup (analysis + risk + summary + clause extraction)
- Label-perspective risk identification
- Contract comparison (which deal is better for the label)
- Specific clause extraction
- PDF report generation with proper Unicode handling

### Test Contracts Used
| Contract | Artist Style | Size | Type |
|----------|--------------|------|------|
| bella_rivers_recording_agreement.pdf | Taylor Swift / Carrie Underwood | 21.71 KB | 360 Recording Agreement |
| viper_morrison_recording_agreement.pdf | Ozzy Osbourne | 14.74 KB | Recording Agreement |

---

## Test 1: List Available Contracts

### Input
```
List all contracts available for analysis
```

### Response
```markdown
Here are the available contracts you can analyze:

---

# **Contracts Available**
**Total: 4**

1. **bella_rivers_recording_agreement.pdf**
   - Recording agreement
   - Size: 21.71 KB

2. **sample_artist_agreement.txt**
   - Sample artist agreement (text format)
   - Size: 7.96 KB

3. **sample_software_license_agreement.pdf**
   - Software license agreement (non-music)
   - Size: 5.96 KB

4. **viper_morrison_recording_agreement.pdf**
   - Recording agreement
   - Size: 14.74 KB

---

# **What You Can Do Next**
You can ask me to:

- **Run a full workup**
  Example:
  > Work on bella_rivers_recording_agreement.pdf

- **Extract specific clauses**
  Example:
  > Extract financial and rights clauses from viper_morrison_recording_agreement.pdf

- **Generate an executive summary**

- **Compare two contracts**

Just tell me what you'd like to do.
```

### Voice Response
> We've got four contracts ready to analyze - just tell me which one you want to dig into.

### Status: PASSED

---

## Test 2: Full Contract Workup (Label Perspective)

### Input
```
Work on bella_rivers_recording_agreement.pdf
```

### Response
```markdown
Here's your full contract analysis package for **bella_rivers_recording_agreement.pdf** - the system successfully completed a full workup, including executive summary, clause extraction, risk assessment, and a downloadable PDF report.

---

# **Full Contract Work-Up Completed**
**File analyzed:** bella_rivers_recording_agreement.pdf
**Perspective:** *Record Label / Label Counsel*
**Output:** Full structured analysis + executive summary + risks + extracted clauses
**PDF Report:** Generated and saved

---

# **Executive Summary (Label Perspective)**
This is a **high-investment, high-control 360 recording agreement** with significant upside for the Label *if* the artist (Bella Rivers) becomes commercially successful - but the deal contains several **artist-favorable financial terms** that materially increase risk exposure.

**Top takeaways:**
- Total Label exposure across all album cycles: **$15M+**
- Label owns all Masters **in perpetuity**
- Strong 360 participation across *touring, merch, endorsements, acting/modeling, digital*
- High artist streaming royalty (50% of net) significantly reduces digital revenue margin
- Strong termination triggers for underperformance (50k unit threshold)
- Meaningful artist consultation rights may slow production

---

# **Key Risks (Label View)**
Risk score: **88 (High)**
Main concerns identified:

**1. Critical Financial Risk**
- Extremely high guaranteed recording budgets ($750k-$1.25M+)
- Escalating advances (20-40%) tied to RIAA certifications
- Heavy marketing minimums ($500k 1st album, increasing later)

**2. Critical Revenue Compression**
- Artist receives **50% of Label net receipts** for streaming & sync
- This is nearly *double* typical major-label norms

**3. Catalog Value Risk**
- Master reversion after **35 years or 7 years post-term** (earlier of the two)
- This shortens long-tail monetization vs. standard 50+ year windows

**4. Missing Label Protections**
- No explicit cross-collateralization clause
- No touring requirement despite 360 share
- No caps on producer or studio expenses

---

# **PDF Report**
Your finished report is available here:

**Report name:** bella_rivers_recording_agreement_analysis_20260108_150639.pdf
**Size:** 6.17 KB
**Format:** PDF
```

### Voice Response
> Your contract's all analyzed - big spend, strong label control, but a few risky artist-friendly terms. The full PDF report's ready whenever you need it.

### Key Validation Points
- [x] Label perspective confirmed ("Record Label / Label Counsel")
- [x] Risk score properly calculated (88 - High)
- [x] Artist-favorable terms identified as RISKS to the label
- [x] PDF report generated successfully
- [x] Financial exposure quantified ($15M+)

### Status: PASSED

---

## Test 3: Contract Comparison (Label Perspective)

### Input
```
Compare bella_rivers_recording_agreement.pdf with viper_morrison_recording_agreement.pdf. Which deal is better for the label?
```

### Response
```markdown
# **Which Deal Is Better for the Label?**
**Clear winner: Contract A - the Bella Rivers Recording Agreement.**

Across every major category that matters to a record label - **financial exposure, rights retention, control, 360 income, approval rights, risk profile** - Contract A is consistently more favorable to the label.

---

# **Why Contract A Is Better**

## **1. Financial Exposure: MUCH Lower in Contract A**
- Contract B includes:
  - **$1M non-recoupable bonus**
  - **$500k-$1.25M album advances**
  - **Guaranteed annual payments**
  - **$2M-$3M+ recording budgets**

- Contract A:
  - Lower advances
  - Lower recording budgets
  - No guaranteed annual payouts

**Label advantage: A** reduces risk by millions.

---

## **2. Royalties & Deductions: Contract A Strongly Favors the Label**
- Contract A has:
  - Packaging deductions
  - 35% reserves
  - Reduced mechanical rates
  - Free goods deductions

- Contract B:
  - Higher royalty rates
  - Reduced deductions
  - Full statutory mechanicals

**Result: A is more recoup-friendly and cheaper for the label.**

---

## **3. Rights Retention: A Keeps Masters Longer**
- Contract A: **35 years or 7 years after term (whichever is later).**
- Contract B: **20 years OR upon recoupment** (potentially very early).

**Label advantage: A retains the catalog far longer.**

---

## **4. Creative & Operational Control**
- Contract A gives the label:
  - Final approval on producers
  - Control over marketing, artwork, sync
  - Social media oversight

- Contract B gives the artist:
  - Creative control
  - Sync approval
  - Artwork control
  - Key Man clause to exit

**Label advantage: A provides control; B gives it away.**

---

## **5. 360 Revenues: A Collects Much More**
- Contract A:
  - 10-15% touring
  - 20-25% merch
  - 15% endorsements
  - 10% acting/modeling

- Contract B:
  - 0-10% touring
  - 12.5-15% merch
  - 10-12.5% endorsements

**Label advantage: A has materially richer long-tail revenue participation.**

---

## **6. Term Length & Options**
- Contract A:
  - 1-year term + five 1-year label options
  - Automatic extensions for delivery issues

- Contract B:
  - 2-year term + artist-friendly options
  - Artist can shorten options
  - Key Man exit rights

**Label advantage: A has greater control and fewer escape routes.**

---

# **Overall Assessment**
**Contract A is substantially better for the label.**
The analysis found that Contract B is heavily artist-tilted and exposes the label to much higher costs, greater operational constraints, and significantly reduced rights retention.
```

### Voice Response
> Short version: Contract A is far better for the label - much lower cost, longer rights, stronger control, and better 360 income. Contract B is expensive and very artist-friendly.

### Key Validation Points
- [x] Comparison correctly identifies "better for the label" (not artist)
- [x] Financial exposure compared from label's cost perspective
- [x] Rights retention compared (longer = better for label)
- [x] 360 participation compared (higher % = better for label)
- [x] Artist-favorable terms in Contract B flagged as label disadvantages

### Status: PASSED

---

## Test 4: Risk Identification (Deal Breakers)

### Input
```
Identify all risks in viper_morrison_recording_agreement.pdf from the label's perspective. What are the deal breakers?
```

### Response
```markdown
# **Full Label-Side Risk Assessment**

# **OVERALL RISK LEVEL: HIGH (Score: 92/100)**
This contract is **extremely artist-favorable** and exposes the label to **unrecoverable financial, operational, and long-term catalog risks**.

---

# **CRITICAL RISKS (Label Perspective)**

## **1. Financial Exposure (Critical)**
- $1M **non-recoupable** signing bonus
- $2M-$3M album budgets
- Mandatory marketing, video, and tour support
- Guaranteed $250k **annual payments regardless of recoupment**
- No spending caps tied to performance

**Impact:** Sunk costs; label could easily burn **$12M-$15M+** over the term with minimal recovery.

---

## **2. No Cross-Collateralization (Critical)**
Clause 3.5 prevents losses from one album being recouped from future successful albums.

**Impact:** A single flop becomes a **permanent loss**.

---

## **3. Master Ownership Reversion After 20 Years OR Upon Recoupment (Critical)**
This is extraordinarily unfavorable. Reverting **as soon as the project recoups** eliminates long-tail revenue entirely.

**Impact:** Label loses its primary asset **right when it becomes profitable**.

---

## **4. Streaming & Sync Royalties Extremely High (Critical)**
- 55% streaming
- 50% sync

Industry norm: 20-30%.

**Impact:** The label's margin on core modern formats is shredded.

---

## **5. Artist-Friendly Termination Rights (High)**
Artist can exit based on:
- 9-month release delay
- Late royalties
- A&R key-man departure
- Change of control

**Impact:** Artist can walk while the label holds all the sunk investment.

---

## **6. Massive Creative Control (High)**
Artist has approval rights on:
- Producer
- Artwork
- Video concepts
- Band members
- Merch

**Impact:** Delays, higher costs, and loss of commercial decision-making.

---

## **7. Low 360 Participation + Huge Carve-outs (High)**
Excluded income:
- Alcohol endorsements
- Cannabis
- Several touring and merch carve-outs

**Impact:** Label cannot offset high investment with diversified revenue.

---

# **ABSOLUTE DEAL-BREAKERS**
These clauses are so unfavorable that they make the contract non-viable for the label without revision.

1. **Recoupment-based master reversion**
   (Catastrophic loss of long-term asset value.)

2. **55% streaming royalty**
   (Destroys label margin on the #1 revenue source.)

3. **No cross-collateralization**
   (Makes recoupment structurally impossible.)

4. **$1M non-recoupable signing bonus**
   (Immediate unrecoverable liability.)

5. **Overly broad artist termination rights**
   (Allows exit before label recoups investment.)

---

# **High-Level Summary**
This deal shifts nearly all risk to the label while giving the artist easy escape routes, high guaranteed money, excessive creative control, and unprecedented royalty splits.

Unless materially renegotiated, this contract is **not financially or strategically viable** for a record label.
```

### Voice Response
> Big picture: this contract is incredibly risky for the label - the master reversion, no cross-collateralization, high streaming royalties, and big guaranteed payments are total deal-breakers.

### Key Validation Points
- [x] Risk score highest of all contracts (92 - High)
- [x] Artist-favorable terms correctly identified as RISKS
- [x] Deal breakers clearly enumerated
- [x] Financial impact quantified ($12-15M+ exposure)
- [x] Industry standard comparisons provided (55% vs 20-30% norm)
- [x] Recommendation: "not financially or strategically viable"

### Status: PASSED

---

## Test 5: Extract Specific Clauses

### Input
```
Extract only the financial and termination clauses from bella_rivers_recording_agreement.pdf
```

### Response
```markdown
# **Financial & Termination Clauses (Extracted Only)**

## **Financial Clauses**
**Section 1.1**
Definition of Advance
- Advances are prepayments of royalties or other sums
- Fully recoupable by the Label

**Sections 3.3-3.4**
Recording Budgets & Overages
- Album 1: $750,000
- Album 2: $1,000,000
- Album 3: $1,250,000
- Albums 4-6: Not less than prior album
- Costs paid first; remaining balance = Artist Advance
- Overages: Label-funded (recoupable) or Artist-paid

**Sections 4.1-4.2**
Signing & Album Advances
- Signing Advance: $300,000 (non-refundable, recoupable)
- Album Advances escalate from $200k to $750k

**Section 4.3**
RIAA Escalations
- Gold: +20% on next Advance
- Platinum: +40%

**Section 4.4**
Recoupment
- All advances recoupable
- Not returnable except under Article 14

**Sections 5.1-5.6**
Royalty Structure
- 15% SRLP physical
- 15% downloads
- 50% streaming and sync
- Various escalations, deductions, reserves

**Article 6**
360 Revenue Participation
- Touring: 10-15%
- Merch: 20-25%
- Endorsements: 15%
- Acting/modeling: 10%
- Fan club: 20%
- Patreon: 15%
- NFTs: 25%

**Sections 7.1-7.2**
Co-Publishing & Mechanical Royalties
- Artist assigns 50% Controlled Compositions copyright
- 75% total publishing share retained
- 75% statutory mechanical rate
- 10x controlled-composition cap

**Article 9**
Marketing, Promotion, Video, Tour Support
- Album 1 marketing: $500k
- Music videos: $150k each, 50% recoupable
- Tour support: 100% recoupable

**Article 11**
Accounting & Audits
- Semi-annual statements
- 30-day notice for audits
- Underpayment >10% = Label pays audit cost

---

## **Termination Clauses**
**Section 14.1**
Termination for Cause
- Breach with 30-day cure period
- Insolvency/bankruptcy
- Felony conviction

**Section 14.2**
Label-Specific Termination Rights
- Late delivery of Album (6 months past schedule)
- First Album sells <50,000 units in 12 months
- Artist conduct harming commercial viability

**Section 14.3**
Consequences of Termination
- Artist must complete Album in production
- Label retains rights to all Masters
- Unrecouped balances remain due
- Certain provisions survive termination

**Section 14.4**
No Termination Without Cause
- Neither Party may terminate without cause during contract periods
```

### Voice Response
> I've pulled out just the financial and termination clauses you needed - let me know if you want summaries, comparisons, or risk analysis next.

### Key Validation Points
- [x] Only requested clause types extracted (financial + termination)
- [x] Section references included
- [x] Key terms summarized with bullet points
- [x] Specific dollar amounts and percentages extracted

### Status: PASSED

---

## Summary of All Tests

| Test | Description | Status | Key Metric |
|------|-------------|--------|------------|
| 1 | List Contracts | PASSED | 4 contracts found |
| 2 | Full Workup (Bella Rivers) | PASSED | Risk Score: 88 |
| 3 | Contract Comparison | PASSED | Correct winner identified |
| 4 | Risk Identification (Viper Morrison) | PASSED | Risk Score: 92, 5 deal-breakers |
| 5 | Clause Extraction | PASSED | Financial + Termination extracted |

---

## Technical Validation

### PDF Report Generation
- [x] Reports generated successfully
- [x] Unicode characters properly normalized (no tofu/black squares)
- [x] Financial terms formatted as readable text (not raw dicts)
- [x] Risk tables with proper text wrapping

### Label Perspective Validation
- [x] Executive summaries written for label executives
- [x] "Artist-favorable terms" identified as RISKS to the label
- [x] High advances/royalties flagged as FINANCIAL RISK
- [x] Early master reversion flagged as ASSET RISK
- [x] Artist termination rights flagged as OPERATIONAL RISK
- [x] Comparisons identify "better for label" not "better for artist"

---

## Endpoint Information

**Production URL:**
```
https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function
```

**Request Format:**
```json
{
  "user_input": "Your query here",
  "conversation_history": []
}
```

**Authentication:**
- Function key required (query parameter: `?code=<FUNCTION_KEY>`)
- Get key: `az functionapp keys list --name YOUR_FUNCTION_APP --resource-group YOUR_RESOURCE_GROUP`

---

## Sample curl Commands

### List Contracts
```bash
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"List all contracts","conversation_history":[]}'
```

### Full Workup
```bash
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Work on bella_rivers_recording_agreement.pdf","conversation_history":[]}'
```

### Compare Contracts
```bash
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Compare bella_rivers_recording_agreement.pdf with viper_morrison_recording_agreement.pdf","conversation_history":[]}'
```

### Identify Risks
```bash
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Identify risks in viper_morrison_recording_agreement.pdf","conversation_history":[]}'
```

---

*Generated: January 8, 2026*
*Agent Version: ContractAnalysisAgent v1.0*
*Model: gpt-5.1-chat*
