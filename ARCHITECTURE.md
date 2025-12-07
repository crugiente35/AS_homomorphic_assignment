# 📊 System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ADMINISTRATOR                               │
│                                                                      │
│  1. Create Questionnaire                                            │
│     Web Interface or $ python create_questionnaire.py               │
│                                                                      │
│     ┌──────────────────────────────────────┐                        │
│     │  Generate BFV Keys                   │                        │
│     │  • Public Key  → Frontend            │                        │
│     │  • Secret Key  → Backend (secure)    │                        │
│     └──────────────────────────────────────┘                        │
│                          ↓                                           │
│     Save in Database (SQLite/PostgreSQL)                            │
│                          ↓                                           │
│     Share link: https://server/#/questionnaire/abc123               │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                             USERS                                    │
│                                                                      │
│  2. Answer Questionnaire                                            │
│     Web Browser → https://server (with client certificate)          │
│                                                                      │
│     ┌──────────────────────────────────────┐                        │
│     │  Frontend (React + JavaScript)       │                        │
│     │                                       │                        │
│     │  a) Receive Public Key               │                        │
│     │  b) User selects answers             │                        │
│     │  c) One-hot encode: [0,0,1,0,...]    │                        │
│     │  d) Encrypt with BFV                 │                        │
│     │  e) Send ciphertexts to server       │                        │
│     └──────────────────────────────────────┘                        │
│                          ↓                                           │
│           POST /api/submit-answers (with client cert)                │
│           { encrypted_answers: [...] }                               │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVER (Backend)                             │
│                                                                      │
│  3. Receive and Accumulate Encrypted Responses                      │
│     Flask API + SQLAlchemy + mTLS                                    │
│                                                                      │
│     ┌──────────────────────────────────────┐                        │
│     │  Homomorphic Addition (BFV Evaluator)│                        │
│     │                                       │                        │
│     │  If first response:                  │                        │
│     │    accumulated = ciphertext_1        │                        │
│     │                                       │                        │
│     │  If responses exist:                 │                        │
│     │    accumulated = accumulated +       │                        │
│     │                  ciphertext_new      │                        │
│     │                                       │                        │
│     │  ⚠️ Server does NOT see responses!   │                        │
│     └──────────────────────────────────────┘                        │
│                          ↓                                           │
│     Save accumulated (encrypted) in DB                               │
│     Record certificate fingerprint to prevent duplicates             │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          ADMINISTRATOR                               │
│                                                                      │
│  4. View Results                                                    │
│     Web Interface or $ python view_results.py --link abc123         │
│                                                                      │
│     ┌──────────────────────────────────────┐                        │
│     │  Decryption with Secret Key          │                        │
│     │                                       │                        │
│     │  1. Read accumulated from DB         │                        │
│     │  2. Decrypt with secret_key          │                        │
│     │  3. Decode vector                    │                        │
│     │  4. Show totals:                     │                        │
│     │     Option 1: 15 votes (30%)         │                        │
│     │     Option 2: 25 votes (50%)         │                        │
│     │     Option 3: 10 votes (20%)         │                        │
│     └──────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Data Flow

### 📤 Response Submission (User → Server)

```
User in Browser
         │
         │ 1. Selects: "Option 2"
         ↓
    [Frontend React/JS]
         │
         │ 2. One-hot encode
         │    [0, 0, 1, 0, 0, 0, 0, 0]
         ↓
    BatchEncoder
         │
         │ 3. Encode (CRT batching)
         │    → Plaintext (polynomial)
         ↓
    BFVEncryptor
         │
         │ 4. Encrypt with public_key
         │    plaintext → ciphertext
         │    (c0, c1)
         ↓
    Serialize JSON
         │
         │ 5. POST /api/submit-answers (via mTLS proxy)
         │    {
         │      questionnaire_id: "abc123",
         │      encrypted_answers: [
         │        { c0: {...}, c1: {...} }
         │      ]
         │    }
         │    + Client Certificate
         ↓
    [Backend Flask]
         │
         │ 6. Verify client certificate
         │    Check for duplicate submission
         ↓
         │ 7. Deserialize ciphertexts
         ↓
    BFVEvaluator
         │
         │ 8. Homomorphic addition
         │    accumulated = accumulated + new
         ↓
    Database
         │
         │ 9. Save accumulated (encrypted)
         │    Record certificate fingerprint
         └─→ SQLite: tables questionnaires, submission_records
```

### 📥 Results Reading (Administrator)

```
Administrator
         │
         │ 1. python view_results.py --link abc123
         │    or Web Interface
         ↓
    [Backend Script/API]
         │
         │ 2. Read accumulated from DB
         ↓
    BFVDecryptor
         │
         │ 3. Decrypt with secret_key
         │    ciphertext → plaintext
         ↓
    BatchEncoder
         │
         │ 4. Decode (CRT)
         │    plaintext → [5, 10, 15, 3, ...]
         ↓
    Display
         │
         │ 5. Show results
         └─→ Option 1: 5 votes
             Option 2: 10 votes
             Option 3: 15 votes
             ...
```

---

## Database Structure

### Table: `questionnaires`

```
┌─────────────────────────────────────────────────────────────┐
│ id (PK)                │ INTEGER (autoincrement)            │
├────────────────────────┼────────────────────────────────────┤
│ link                   │ STRING (unique, indexed)           │
├────────────────────────┼────────────────────────────────────┤
│ deadline               │ DATETIME                           │
├────────────────────────┼────────────────────────────────────┤
│ questions_json         │ TEXT (JSON serialized)             │
│                        │ [                                  │
│                        │   {                                │
│                        │     text: "Question?",             │
│                        │     options: ["A", "B", ...]       │
│                        │   }                                │
│                        │ ]                                  │
├────────────────────────┼────────────────────────────────────┤
│ poly_degree            │ INTEGER (8, 16, 32, ...)           │
├────────────────────────┼────────────────────────────────────┤
│ plain_modulus          │ INTEGER (prime, e.g.: 17)          │
├────────────────────────┼────────────────────────────────────┤
│ ciph_modulus           │ STRING (large number)              │
├────────────────────────┼────────────────────────────────────┤
│ public_key_json        │ TEXT (JSON)                        │
│                        │ {                                  │
│                        │   p0: { coeffs: [...] },           │
│                        │   p1: { coeffs: [...] }            │
│                        │ }                                  │
├────────────────────────┼────────────────────────────────────┤
│ secret_key_json        │ TEXT (JSON) 🔐 SECRET              │
│                        │ {                                  │
│                        │   coeffs: [...]                    │
│                        │ }                                  │
├────────────────────────┼────────────────────────────────────┤
│ accumulated_responses  │ TEXT (JSON)                        │
│ _json                  │ [                                  │
│                        │   { c0: {...}, c1: {...} },  // Q1 │
│                        │   { c0: {...}, c1: {...} },  // Q2 │
│                        │   ...                              │
│                        │ ]                                  │
├────────────────────────┼────────────────────────────────────┤
│ decrypted_results_json │ TEXT (JSON, nullable)              │
├────────────────────────┼────────────────────────────────────┤
│ is_decrypted           │ INTEGER (0/1 boolean)              │
├────────────────────────┼────────────────────────────────────┤
│ hide_results_until     │ INTEGER (0/1 boolean)              │
│ _deadline              │                                    │
├────────────────────────┼────────────────────────────────────┤
│ num_responses          │ INTEGER (counter)                  │
├────────────────────────┼────────────────────────────────────┤
│ created_at             │ DATETIME                           │
└────────────────────────┴────────────────────────────────────┘
```

### Table: `submission_records`

```
┌─────────────────────────────────────────────────┐
│ id (PK)              │ INTEGER (autoincrement)  │
├──────────────────────┼──────────────────────────┤
│ questionnaire_id     │ INTEGER (FK)             │
├──────────────────────┼──────────────────────────┤
│ cert_fingerprint     │ STRING(64) SHA-256 hash  │
├──────────────────────┼──────────────────────────┤
│ submitted_at         │ DATETIME                 │
└──────────────────────┴──────────────────────────┘
```

---

## API Endpoints

### 1. GET `/api/questionnaire/<link>`

**Request:**
```
GET /api/questionnaire/abc123
```

**Response:**
```json
{
  "id": 1,
  "link": "abc123",
  "deadline": "2025-12-31T23:59:59",
  "questions": [
    {
      "text": "¿Pregunta 1?",
      "options": ["A", "B", "C", "D", "E", "F", "G", "H"]
    }
  ],
  "public_key": {
    "p0": { "ring_degree": 8, "coeffs": [...] },
    "p1": { "ring_degree": 8, "coeffs": [...] }
  },
  "params": {
    "poly_degree": 8,
    "plain_modulus": 17,
    "ciph_modulus": 8000000000000
  }
}
```

### 2. POST `/api/submit-answers`

**Request:**
```json
{
  "questionnaire_id": "abc123",
  "encrypted_answers": [
    {
      "c0": { "ring_degree": 8, "coeffs": [...] },
      "c1": { "ring_degree": 8, "coeffs": [...] }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Answers submitted successfully",
  "total_responses": 42
}
```

### 3. GET `/api/questionnaire/<link>/stats`

**Request:**
```
GET /api/questionnaire/abc123/stats
```

**Response:**
```json
{
  "link": "abc123",
  "num_responses": 42,
  "deadline": "2025-12-31T23:59:59",
  "is_expired": false
}
```

---

## Security and Privacy

### 🔐 Cryptographic Guarantees

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND (User)                                         │
│  ✓ Has: public_key                                       │
│  ✓ Can: encrypt messages                                 │
│  ✗ CANNOT: decrypt messages                              │
│  ✗ CANNOT: see other users' responses                    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  BACKEND (Server)                                        │
│  ✓ Has: ciphertexts (encrypted)                          │
│  ✓ Can: add ciphertexts homomorphically                  │
│  ✗ CANNOT: decrypt without secret_key                    │
│  ✗ CANNOT: see individual responses                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  ADMINISTRATOR                                           │
│  ✓ Has: secret_key (securely stored)                     │
│  ✓ Can: decrypt accumulated (totals)                     │
│  ✗ CANNOT: see original individual responses             │
│            (only accumulated totals)                     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  mTLS AUTHENTICATION                                     │
│  ✓ Each user has a unique client certificate             │
│  ✓ Server tracks certificate fingerprints                │
│  ✓ Prevents duplicate submissions                        │
│  ✓ Cannot impersonate other users                        │
└──────────────────────────────────────────────────────────┘
```

### 🛡️ System Properties

1. **Confidentiality**: Individual responses never in plain text
2. **Private Aggregation**: Sums without decrypting
3. **Verifiability**: Administrator can verify totals
4. **Non-Repudiation**: Each response is recorded (timestamp + certificate)
5. **Authentication**: mTLS prevents unauthorized access and duplicate votes

---

## Use Case Examples

### Case 1: Anonymous Satisfaction Survey

```
Question: "How would you rate your experience?"
Options: 1⭐ 2⭐ 3⭐ 4⭐ 5⭐ N/A N/A N/A

User 1 (Alice) selects: 5⭐ → encrypts [0,0,0,0,1,0,0,0]
User 2 (Bob) selects: 4⭐ → encrypts [0,0,0,1,0,0,0,0]
User 3 (Trudy) selects: 5⭐ → encrypts [0,0,0,0,1,0,0,0]

Server accumulates (without seeing):
  accumulated = sum([ciph1, ciph2, ciph3])
  Records: Alice, Bob, Trudy voted (prevents re-voting)

Administrator decrypts:
  [0, 0, 0, 1, 2, 0, 0, 0]
  → 1 person voted 4⭐, 2 people voted 5⭐
  → Average: 4.67⭐
```

### Case 2: Private Voting

```
Question: "In favor of proposal X?"
Options: Yes, No, Abstain, N/A, N/A, N/A, N/A, N/A

100 users vote (each encrypts their response with their certificate)

Server accumulates without seeing individual votes
Tracks which certificates have voted

Administrator decrypts result:
  [65, 30, 5, 0, 0, 0, 0, 0]
  → 65 Yes, 30 No, 5 Abstentions
  → Proposal APPROVED (65%)
```

---

## Current Limitations

1. **Vector Size**: Maximum 8 options per question (with poly_degree=8)
2. **Only Addition**: Current system only supports homomorphic addition
3. **No Multiplication**: Multiplication of responses not implemented
4. **Demo Parameters**: Current parameters are for demonstration, not production

### Future Improvements

- [ ] Support for more options (poly_degree=16, 32, ...)
- [ ] Homomorphic multiplication for complex statistics
- [ ] Rotations for advanced operations
- [ ] Production security parameters
- [ ] Web administration interface
- [ ] Export results to CSV/PDF
- [ ] Certificate revocation list (CRL) support
