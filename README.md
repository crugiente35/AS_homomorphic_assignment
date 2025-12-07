# Homomorphic Encryption Questionnaire System (BFV)

Complete questionnaire system where responses are encrypted on the client (frontend) using the BFV (Brakerski-Fan-Vercauteren) fully homomorphic encryption scheme. The server can only add encrypted responses without seeing them in plain text.

## 🔒 Features

- **Client-Side Encryption**: Responses are encrypted in JavaScript before sending to the server
- **Total Privacy**: The server never sees individual responses in plain text
- **Homomorphic Addition**: The server can add encrypted responses without decrypting them
- **Secure Database**: Stores accumulated encrypted responses with SQLAlchemy
- **Controlled Decryption**: Only the administrator with the secret key can view results
- **mTLS Authentication**: Client certificate authentication to prevent duplicate submissions

## 📁 Project Structure

```
AS_assignment/
├── Frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx         # Landing page
│   │   │   ├── Create.jsx       # Create new questionnaire
│   │   │   ├── List.jsx         # List all questionnaires
│   │   │   ├── Questionnaire.jsx # Answer questionnaire
│   │   │   └── Results.jsx      # View decrypted results
│   │   ├── crypto.js            # BFV encryption implementation
│   │   ├── crypto.test.js       # Crypto unit tests
│   │   ├── index.css            # Global styles
│   │   └── main.jsx             # React app entry point
│   ├── index.html               # HTML template
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js           # Vite configuration
│   └── proxy-server.js          # mTLS proxy server for development
│
└── Backend/
    ├── models.py                # SQLAlchemy database models
    ├── app.py                   # Flask API server with mTLS
    ├── create_questionnaire.py  # CLI script to create questionnaires
    ├── view_results.py          # CLI script to view decrypted results
    ├── requirements.txt         # Python dependencies
    ├── certs/
    │   ├── generate_ca.bat      # Generate CA certificate
    │   └── generate_certs.bat   # Generate client certificates
    └── debug/
        ├── debug_decrypt.py     # Manual decryption testing
        ├── test_encoder.py      # Encoder testing
        ├── test_full_flow.py    # End-to-end flow testing
        └── generate_schema.py   # Database schema diagram generator
```

## 🚀 Installation and Usage

### 1. Create Certificates

First, generate the CA and client certificates for mTLS:

```powershell
cd Backend/certs
generate_ca.bat
generate_certs.bat Alice
generate_certs.bat Bob
generate_certs.bat Trudy
```

**Important**: Install the Root CA Certificate `ca.crt` and the client certificates `*.p12` in your browser/system.

### 2. Install Backend Dependencies

```powershell
cd Backend
pip install git+https://github.com/sarojaerabelli/py-fhe.git
pip install -r requirements.txt
```

### 3. Start the Backend Server

```powershell
python app.py
```

The server will be available at `https://localhost:5000` (note: HTTPS with mTLS)

### 4. Build the Frontend

```powershell
cd Frontend
npm install
npm run build
```

### 5. Start the Frontend Proxy (for development)

If you want to run in development mode:

```powershell
cd Frontend
node proxy-server.js  # In one terminal
npm run dev           # In another terminal
```

### 6. Open the Application

Open `https://localhost:5000` in Chrome (or your preferred browser).

**Note**: You'll need to select a client certificate (Alice, Bob, or Trudy) when prompted.

### 7. Create a Questionnaire

Use the web interface or run:

```powershell
cd Backend
python create_questionnaire.py
```

### 8. View Results

```powershell
# List all questionnaires
python view_results.py --list

# View results of a specific questionnaire
python view_results.py --link <questionnaire-link>
```

Example output:
```
================================================================================
RESULTS (Decrypted Accumulated Votes)
================================================================================

Question 1: What is your favorite programming language?
--------------------------------------------------------------------------------
  Python                         |  25 votes ( 50.0%) █████████████████████████
  JavaScript                     |  15 votes ( 30.0%) ███████████████
  Java                           |   5 votes ( 10.0%) █████
  C++                            |   5 votes ( 10.0%) █████
```

## 📊 Database

### Table `questionnaires`

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique ID (Primary Key) |
| `link` | String(255) | Unique questionnaire link (unique, indexed) |
| `deadline` | DateTime | Deadline to respond |
| `questions_json` | Text | JSON with questions and options |
| `poly_degree` | Integer | Polynomial degree (BFV parameter) |
| `plain_modulus` | Integer | Plain text modulus (BFV parameter) |
| `ciph_modulus` | String(100) | Cipher modulus (large number, stored as string) |
| `public_key_json` | Text | Serialized public key (JSON) |
| `secret_key_json` | Text | Serialized secret key (JSON) |
| `accumulated_responses_json` | Text | Accumulated encrypted responses (JSON, nullable) |
| `decrypted_results_json` | Text | Decrypted results (JSON, nullable) |
| `is_decrypted` | Integer | Boolean flag: 0=not decrypted, 1=decrypted |
| `hide_results_until_deadline` | Integer | Boolean flag: 1=hide results until deadline, 0=show |
| `created_at` | DateTime | Creation date (UTC) |
| `num_responses` | Integer | Number of responses received |

### Table `submission_records`

Tracks which client certificates (users) have responded to each questionnaire to prevent duplicate submissions.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique ID (Primary Key) |
| `questionnaire_id` | Integer | Questionnaire ID (Foreign Key, indexed) |
| `cert_fingerprint` | String(64) | SHA-256 fingerprint of client certificate |
| `submitted_at` | DateTime | Submission date and time (UTC) |

## 🔐 How It Works

### 1. Key Generation (Backend)

```python
params = BFVParameters(poly_degree=8, plain_modulus=17, ciph_modulus=8000000000000)
key_generator = BFVKeyGenerator(params)
public_key = key_generator.public_key  # Sent to frontend
secret_key = key_generator.secret_key  # Saved on server
```

### 2. Encryption (Frontend)

```javascript
// Encode response as one-hot vector
const vector = [0, 0, 1, 0, 0, 0, 0, 0];  // User selected option 2
const plaintext = encoder.encode(vector);

// Encrypt with public key
const ciphertext = encryptor.encrypt(plaintext);

// Send to server
fetch('/api/submit-answers', {
    method: 'POST',
    body: JSON.stringify({encrypted_answers: [ciphertext.toJSON()]})
});
```

### 3. Homomorphic Accumulation (Backend)

```python
# First response: [0, 0, 1, 0, 0, 0, 0, 0] encrypted
accumulated = ciphertext1

# Second response: [0, 1, 0, 0, 0, 0, 0, 0] encrypted
accumulated = evaluator.add(accumulated, ciphertext2)

# Encrypted result: [0, 1, 1, 0, 0, 0, 0, 0] encrypted
# The server never sees individual values!
```

### 4. Decryption (Backend, only with secret key)

```python
plaintext = decryptor.decrypt(accumulated_ciphertext)
results = encoder.decode(plaintext)
# results = [0, 1, 1, 0, 0, 0, 0, 0]
# Option 1: 0 votes
# Option 2: 1 vote
# Option 3: 1 vote
```

## 🛠️ API Endpoints

### `GET /api/questionnaire/<link>`

Get a questionnaire with its public key.

**Response:**
```json
{
    "id": 1,
    "link": "aB3dEf9HiJkLmN0pQr",
    "deadline": "2025-12-30T12:00:00",
    "questions": [
        {
            "text": "¿Pregunta?",
            "options": ["Opción 1", "Opción 2", ...]
        }
    ],
    "public_key": {
        "p0": {"ring_degree": 8, "coeffs": [...]},
        "p1": {"ring_degree": 8, "coeffs": [...]}
    },
    "params": {
        "poly_degree": 8,
        "plain_modulus": 17,
        "ciph_modulus": 8000000000000
    }
}
```

### `POST /api/submit-answers`

Submit encrypted responses.

**Request:**
```json
{
    "questionnaire_id": "aB3dEf9HiJkLmN0pQr",
    "encrypted_answers": [
        {
            "c0": {"ring_degree": 8, "coeffs": [...]},
            "c1": {"ring_degree": 8, "coeffs": [...]}
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Answers submitted successfully",
    "total_responses": 5
}
```

### `GET /api/questionnaire/<link>/stats`

Get basic statistics (without decrypting).

**Response:**
```json
{
    "link": "aB3dEf9HiJkLmN0pQr",
    "num_responses": 5,
    "deadline": "2025-12-30T12:00:00",
    "is_expired": false
}
```

## 🔧 Customization

### Create a Custom Questionnaire

Edit `create_questionnaire.py`:

```python
questions = [
    {
        'text': 'Your question here?',
        'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4', 
                   'Option 5', 'Option 6', 'Option 7', 'Option 8']
    },
    # ... more questions
]

create_questionnaire(questions, deadline_days=30, link='my-questionnaire')
```

**Important**: The number of options must equal `poly_degree` (default 8).

### Adjust Security Parameters

In `create_questionnaire.py`:

```python
degree = 16           # Higher = more secure but slower
plain_modulus = 257   # Must be prime
ciph_modulus = 2**60  # Much larger for security
```

## 📊 Results Visualization

### Web Interface (Recommended)

Access results with interactive charts via the web application at:

```
https://localhost:5000
```

Navigate to the "Results" page and select your questionnaire.

**Features:**
- 📊 Interactive charts (bar, pie, donut)
- 📋 Table view with detailed percentages
- 📄 Export results to CSV
- 🖨️ Print results
- 📱 Responsive design

**Visualization types:**
1. **Bar Chart**: Clear vote distribution
2. **Pie Chart**: Visual proportions
3. **Donut Chart**: Modern proportion view
4. **Table**: Precise data with progress bars

### Command Line

Terminal alternative:

```powershell
python view_results.py --link <questionnaire-link>
```

Displays results in text format with ASCII bars.

## 📝 Security Notes

1. **Secret Key**: Keep `secret_key` secure. Anyone with it can decrypt all responses.

2. **Parameter Size**: Current parameters (`degree=8`) are for demonstration. For production, use `degree >= 2048`.

3. **HTTPS & mTLS**: The system uses HTTPS with mutual TLS authentication. Client certificates prevent duplicate submissions.

4. **Database**: For production, use PostgreSQL or MySQL instead of SQLite.

5. **Certificate Management**: Properly secure the CA private key and manage certificate revocation.

## 🐛 Troubleshooting

### Error: "Certificate required" or "SSL handshake failed"

Make sure you've installed the CA certificate (`ca.crt`) and a client certificate (`Alice.p12`, `Bob.p12`, or `Trudy.p12`) in your browser.

### Error: "Questionnaire not found"

Verify the link is correct:
```powershell
python view_results.py --list
```

### Frontend doesn't load

Verify that:
1. The Flask server is running (`python app.py`)
2. The frontend is built (`npm run build` in Frontend/)
3. You're accessing via HTTPS: `https://localhost:5000`

## 📚 References

- [BFV Scheme Paper](https://eprint.iacr.org/2012/144.pdf)
- [py-fhe Library](https://github.com/sarojaerabelli/py-fhe)
- [Homomorphic Encryption](https://en.wikipedia.org/wiki/Homomorphic_encryption)
- [Mutual TLS (mTLS)](https://en.wikipedia.org/wiki/Mutual_authentication)

## 📄 License

This project is for educational use.
