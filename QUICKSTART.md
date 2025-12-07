# 🚀 Quick Start - Homomorphic Encryption Questionnaire System

## Get started in 5 minutes

### 1️⃣ Create Certificates

```powershell
cd Backend/certs
generate_ca.bat
generate_certs.bat Alice
generate_certs.bat Bob
generate_certs.bat Trudy
```

**Important**: Install the Root CA Certificate `ca.crt` and the client certificate `*.p12` in your browser.

### 2️⃣ Install Backend dependencies

```powershell
cd Backend
pip install git+https://github.com/sarojaerabelli/py-fhe.git
pip install -r requirements.txt
```

### 3️⃣ Start the Backend server

```powershell
python app.py
```

**Expected output:**
```
Starting Flask server with mTLS...
Server ready!
Access the application at: https://localhost:5000
```

### 4️⃣ Build the Frontend

```powershell
cd Frontend
npm install
npm run build
```

### 5️⃣ Open the application

Open `https://localhost:5000` in Chrome (or your preferred browser).

**Note**: Select a client certificate (Alice, Bob, or Trudy) when prompted.

### 6️⃣ Create a questionnaire

Use the web interface to create a new questionnaire, or run:

```powershell
cd Backend
python create_questionnaire.py
```

### 7️⃣ Answer the questionnaire

1. Open the questionnaire in the browser
2. Answer all questions
3. Click "Submit Encrypted Answers 🔐"
4. Your answers are encrypted in the browser and sent to the server!

### 8️⃣ View decrypted results

```powershell
# List all questionnaires
python view_results.py --list

# View results of your questionnaire
python view_results.py --link <questionnaire-link>
```

**Expected output:**
```
================================================================================
RESULTS (Decrypted Accumulated Votes)
================================================================================

Question 1: What is your favorite programming language?
--------------------------------------------------------------------------------
  Python                         |   1 votes (100.0%) ██████████████████████████
```

---

## 🎯 Useful Commands

### View all questionnaires
```powershell
python view_results.py --list
```

### View statistics without decrypting
Open in browser:
```
https://localhost:5000/api/questionnaire/<link>/stats
```

### Create custom questionnaire

Edit `create_questionnaire.py` and modify the `example_questionnaire()` function:

```python
questions = [
    {
        'text': 'Your question here?',
        'options': ['Op1', 'Op2', 'Op3', 'Op4', 'Op5', 'Op6', 'Op7', 'Op8']
    }
]

create_questionnaire(questions, deadline_days=30, link='my-survey')
```

Then run:
```powershell
python create_questionnaire.py
```

---

## 📁 File Structure

```
AS_assignment/
├── Frontend/
│   ├── src/
│   │   ├── pages/           # React components
│   │   ├── crypto.js        # BFV encryption
│   │   └── main.jsx         # App entry point
│   ├── proxy-server.js      # mTLS proxy
│   └── vite.config.js       # Vite configuration
│
└── Backend/
    ├── app.py               # Flask server with mTLS
    ├── models.py            # SQLAlchemy database
    ├── create_questionnaire.py # Create questionnaires
    ├── view_results.py      # View results
    ├── certs/               # SSL certificates
    └── py-fhe/              # Encryption library
```

---

## 🔒 What does each component do?

### Frontend (React + JavaScript)
- **crypto.js**: BFV encryption implementation (polynomial arithmetic, NTT, encoding, encryption)
- **pages/**: React components for Home, Create, List, Questionnaire, and Results views
- **proxy-server.js**: Node.js proxy that handles client certificates for API calls

### Backend (Python)
- **models.py**: Defines SQL tables `questionnaires` and `submission_records` with SQLAlchemy
- **app.py**: Flask API to serve questionnaires and receive responses with mTLS authentication
- **create_questionnaire.py**: Generates BFV keys and creates questionnaires
- **view_results.py**: Decrypts accumulated responses with secret key

---

## 🔐 Encryption Flow

```
User → [Frontend]
   1. Answer: Option 2
   2. Encode: [0, 0, 1, 0, 0, 0, 0, 0]
   3. Encrypt with public key
   4. Send ciphertext

Server → [Backend]
   5. Receive ciphertext
   6. Homomorphically add: accumulated += ciphertext
   7. Save in DB (encrypted)

Administrator → [Backend]
   8. Run view_results.py
   9. Decrypt with secret key
   10. View totals: [5, 3, 8, 2, 1, 0, 0, 0]
```

**The server NEVER sees individual responses in plain text!** 🔒

---

## ⚠️ Troubleshooting

### Error: ModuleNotFoundError: No module named 'flask'
```powershell
pip install -r requirements.txt
```

### Error: Certificate required / SSL handshake failed
Make sure you've installed:
1. CA certificate `ca.crt` as a trusted root
2. A client certificate (Alice.p12, Bob.p12, or Trudy.p12)

### Error: Questionnaire not found
Verify the link:
```powershell
python view_results.py --list
```

### Frontend doesn't load
Make sure:
1. The Flask server is running: `python app.py`
2. The frontend is built: `npm run build` in Frontend/
3. You're accessing via HTTPS: `https://localhost:5000`

### Port 5000 already in use
Change the port in `app.py`:
```python
run_simple('0.0.0.0', 8080, wrapped_app, ssl_context=context, ...)
```

---

## 📚 More Information

Read the complete [README.md](README.md) for:
- Detailed BFV explanation
- Advanced customization
- Security parameters
- Complete API endpoints

---

## 🎓 Key Concepts

- **BFV**: Fully homomorphic encryption scheme
- **One-hot encoding**: Vector with one 1 and the rest 0s
- **Homomorphic addition**: Add ciphertexts without decrypting
- **Public key**: Shared with everyone (frontend)
- **Secret key**: Only for the server (decryption)
- **mTLS**: Mutual TLS authentication with client certificates

---

Ready to start! 🚀
