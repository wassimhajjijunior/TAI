# P2M-TAI Pitch Q&A - Hard Questions

This document contains comprehensive questions investors, clients, and stakeholders will ask during the demo. Each question probes for specific details, rationale, and proof points.

---

## 1. VALUE PROPOSITION & MARKET

### Q1: What's the actual problem you're solving?
**Why they ask:** Surface-level answers like "we help companies win tenders" are insufficient. They want the pain point quantified.

**What to prepare:**
- Specific percentage of bids lost due to poor response quality
- Time spent on manual tender response (hours per bid)
- Cost of compliance failures (penalties, lost contracts)
- Example: "Companies spend 120+ hours on each tender response, and 67% still fail compliance checks"

---

### Q2: How big is this market really?
**Why they ask:** Need to validate TAM/SAM/SOM and growth potential

**What to prepare:**
- Global government procurement market size ($12T+ annually)
- Addressable market (percentage going to AI solutions)
- Your target segment (enterprise, government, specific industries)
- Year-over-year growth in AI procurement spending

---

### Q3: Why now? Why can't big players just build this?
**Why they ask:** Assess moat and timing advantage

**What to prepare:**
- What makes current timing different (GPU costs, LLMs, market readiness)
- Why existing players haven't solved this (legacy systems, no AI expertise)
- Your first-mover advantage or barriers to entry

---

### Q4: What's your pricing model?
**Why they ask:** Validate business model sustainability

**What to prepare:**
- Per-tender pricing vs. enterprise subscription
- Tiered pricing (basic, pro, enterprise)
- Example: "$500/tender" or "$50K/year unlimited"
- What features are included vs. upsells

---

## 2. AI & TECHNICAL ARCHITECTURE

### Q5: How does the RAG actually work?
**Why they ask:** Technical due diligence - they want to know it's not just a chatbot wrapper

**What to prepare:**
- Document parsing pipeline (PDF extraction, OCR, layout understanding)
- Chunking strategy for legal documents
- Vector database and search implementation
- How you handle large documents (100+ pages)
- Retrieval accuracy metrics (precision@k, recall@k)

---

### Q6: What models do you use? Why those specifically?
**Why they ask:** Validate you're not just using ChatGPT API as a wrapper

**What to prepare:**
- Specific models for each component:
  - Document embedding (e.g., text-embedding-3-large, custom fine-tuned)
  - LLM for response generation (GPT-4, Claude, open-source)
  - Classification models for compliance checking
- Why these beat alternatives (cost, accuracy, speed)
- Whether you fine-tuned own models
- GPU/CPU infrastructure

---

### Q7: How do you ensure response accuracy?
**Why they ask:** Hallucinations in legal/tender documents are career-ending

**What to prepare:**
- Source citation verification process
- Confidence scoring thresholds
- Human review triggers (what triggers "need human review"?)
- Accuracy metrics on current deployment
- Example: "98% of responses pass legal review without changes"

---

### Q8: What's the latency? How long from upload to response?
**Why they ask:** Affects user experience and practical usability

**What to prepare:**
- Breakdown timing:
  - Document upload: X seconds
  - Parsing/indexing: X minutes
  - Compliance check: X seconds
  - Response generation: X minutes
- Total end-to-end time
- Where are the bottlenecks?

---

### Q9: How do you handle different document formats?
**Why they ask:** Real tenders come in various formats, often messy

**What to prepare:**
- Supported formats (PDF, DOCX, scanned images, etc.)
- Handling poor-quality scans
- Multi-language support
- Non-standard layouts (tables, forms, handwritten notes)

---

## 3. COMPLIANCE & SECURITY

### Q10: How do you ensure data privacy? What happens to our data?
**Why they ask:** Government tenders have strict data handling requirements

**What to prepare:**
- Data retention policies (delete after X days?)
- Where is data processed (which jurisdiction?)
- Customer data isolation (multi-tenant security)
- SOC 2, ISO 27001 certifications
- GDPR, CCPA compliance

---

### Q11: What about sensitive/commercial information in our responses?
**Why they ask:** Companies worry about accidentally leaking IP to competitors

**What to prepare:**
- Is customer data used to train your models?
- How do you prevent cross-customer contamination
- On-premise deployment option (if any)
- NDA/data processing agreements

---

### Q12: How compliant are your generated responses?
**Why they ask:** Liability if response doesn't meet tender requirements

**What to prepare:**
- Compliance scoring methodology
- Who's responsible if response fails compliance (you/the customer?)
- Audit trail for responses (can they prove what was generated when?)
- Legal review integration

---

## 4. COMPETITION & DIFFERENTIATION

### Q13: What are you better at than [Competitor X]?
**Why they ask:** Need clear competitive differentiation

**What to prepare:**
- Specific comparisons on key features
- Price/performance advantages
- Unique capabilities they don't have
- Trade-offs you're willing to make differently

**Sample competitors to know:**
- AutoGPT, langchain (developers building own)
- TenderWrite, BidNexus (direct competitors)
- Consultancies (McKinsey, Accenture)

---

### Q14: What's to stop someone from copy-pasting your AI responses into their own tender?
**Why they ask:** Verify you have defensibility beyond the AI

**What to prepare:**
- Watermarking/ fingerprinting technology
- Unique value beyond generation (compliance, tracking, analytics)
- Customer lock-in through workflow integration

---

## 5. IMPLEMENTATION & ROI

### Q15: How do you measure success? What's the ROI?
**Why they ask:** Concrete metrics, not "it saves time"

**What to prepare:**
- Win rate improvement (% increase)
- Time saved per tender (hours)
- Cost reduction (labor costs avoided)
- Compliance success rate improvement
- Example calculations:
  - "Before: 40% win rate, 80 hours/tender"
  - "After: 55% win rate, 25 hours/tender"

---

### Q16: How long does onboarding take?
**Why they ask:** Enterprise sales cycle concerns

**What to prepare:**
- Self-serve setup timeline
- Custom integration requirements
- Training needed
- Enterprise proof-of-concept process

---

### Q17: What's the customer success story? Who can vouch for you?
**Why they ask:** Social proof beats pitch

**What to prepare:**
- Referenceable customers (names, companies)
- Case studies with metrics
- Letters of intent or contracts
- Industry-specific success stories

---

## 6. FUTURE ROADMAP & VISION

### Q18: What's the 3-year vision?
**Why they ask:** Assess long-term thinking and ambition

**What to prepare:**
- Product roadmap highlights
- Market expansion plans
- Technical innovation roadmap
- Team growth plans

---

### Q19: What can't you do today that you want to?
**Why they ask:** Authenticity - everyone has limitations

**What to prepare:**
- Technical debt you're aware of
- Features on backlog
- What customer requests you're declining and why
- Roadmap priorities

---

### Q20: How do you handle tenders in languages you don't support?
**Why they ask:** Real-world constraint discovery

**What to prepare:**
- Current language support
- Translation pipeline integration
- Multi-language roadmap

---

## 7. TEAM & OPERATIONS

### Q21: Who's the technical founder? Why are you qualified?
**Why they ask:** Technical due diligence on the team

**What to prepare:**
- Technical background (AI/ML experience)
- Relevant past companies
- Published research or open-source contributions
- Why you specifically can solve this problem

---

### Q22: How do you handle demand? What's your capacity?
**Why they ask:** Growth constraints

**What to prepare:**
- Current team size and capacity
- How many concurrent customers
- Scaling plan
- Infrastructure limitations

---

## HARD FOLLOW-UP QUESTIONS (During Pitch)

### "Walk me through exactly what happens when I upload a tender"

They want the end-to-end flow detailed - from file drop to final response.

### "Show me a rejection you got from a tender authority and how you fixed it"

Proves continuous improvement and real-world validity.

### "What's your most expensive customer acquisition channel?"

Reveals true unit economics.

### "What happens when your AI generates something legally problematic?"

Tests risk management and accountability.

### "If I were a competitor with $10M, how would I beat you?"

Tests your defensive strategy and barriers to entry.

---

## ANSWER PREPARATION TEMPLATE

For each question, prepare:

1. **One-liner answer** (for quick response)
2. **Supporting evidence** (metrics, examples, stories)
3. **Proof point** (case study, customer quote, demo)
4. **Follow-up angle** (where the conversation could go)

---

## KEY METRICS TO HAVE READY

- Win rate improvement (before/after)
- Hours saved per tender
- Compliance success rate
- Average response time
- Customer count and growth
- Revenue growth (if post-revenue)
- NPS or satisfaction score
- Churn rate (if post-revenue)