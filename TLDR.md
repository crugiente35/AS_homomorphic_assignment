Create the certitficates

```
cd Backend/certs
generate_ca.bat
generate_certs.bat Alice
generate_certs.bat Bob
generate_certs.bat Trudy
```

Install the Root CA Certificate "ca.crt" and the client certificate "*.p12".

```

Start the Backend Server

```

cd Backend
pip install git+https://github.com/sarojaerabelli/py-fhe.git
pip install -r requirements.txt
python app.py

```

Build the Frontend

```

cd Frontend
npm install
npm run build

```

Open the Application `https://localhost:5000` with Chrome