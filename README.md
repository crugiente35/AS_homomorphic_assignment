# Sistema de Cuestionarios con Cifrado Homomórfico (BFV)

Sistema completo de cuestionarios donde las respuestas se cifran en el cliente (frontend) usando el esquema BFV (Brakerski-Fan-Vercauteren) de cifrado totalmente homomórfico. El servidor solo puede sumar las respuestas cifradas sin verlas en texto plano.

## 🔒 Características

- **Cifrado en el Cliente**: Las respuestas se cifran en JavaScript antes de enviarlas al servidor
- **Privacidad Total**: El servidor nunca ve las respuestas individuales en texto plano
- **Suma Homomórfica**: El servidor puede sumar respuestas cifradas sin descifrarlas
- **Base de Datos Segura**: Almacena respuestas cifradas acumuladas con SQLAlchemy
- **Descifrado Controlado**: Solo el administrador con la clave secreta puede ver resultados

## 📁 Estructura del Proyecto

```
AS_assignment/
├── Frontend/
│   ├── questionnaire.html       # Interfaz web del cuestionario
│   ├── results.html             # Página de visualización de resultados
│   ├── polynomial.js            # Aritmética de polinomios
│   ├── ntt.js                   # Transformada NTT/FTT
│   ├── number_theory.js         # Funciones de teoría de números
│   ├── random_sample.js         # Muestreo aleatorio
│   ├── crypto_structures.js     # Plaintext, Ciphertext, PublicKey
│   ├── batch_encoder.js         # Codificador CRT
│   └── bfv_encryptor.js         # Cifrador BFV
│
└── Backend/
    ├── py-fhe/                  # Librería Python de FHE
    ├── models.py                # Modelos SQLAlchemy
    ├── app.py                   # API Flask
    ├── create_questionnaire.py  # Script para crear cuestionarios
    ├── view_results.py          # Script para ver resultados
    └── requirements.txt         # Dependencias Python
```

## 🚀 Instalación y Uso

### 1. Instalar Dependencias Backend

```powershell
cd Backend
pip install git+https://github.com/sarojaerabelli/py-fhe.git
pip install -r requirements.txt
```

### 2. Crear un Cuestionario

```powershell
python create_questionnaire.py
```

Este script:
- Genera un par de claves BFV (pública/secreta)
- Crea un cuestionario de ejemplo
- Guarda todo en la base de datos SQLite
- Devuelve un link único

Salida de ejemplo:
```
✅ Questionnaire created successfully!
   Link: aB3dEf9HiJkLmN0pQr
   Deadline: 2025-12-30 12:00:00 UTC
   URL: http://localhost:5000/questionnaire.html?id=aB3dEf9HiJkLmN0pQr
```

### 3. Iniciar el Servidor

```powershell
python app.py
```

El servidor estará disponible en `http://localhost:5000`

### 4. Rellenar el Cuestionario

Abre el navegador en la URL proporcionada:
```
http://localhost:5000/questionnaire.html?id=aB3dEf9HiJkLmN0pQr
```

El frontend:
1. Descarga la clave pública del servidor
2. Codifica cada respuesta como un vector one-hot
3. Cifra cada vector con BFV
4. Envía los ciphertexts al servidor

### 5. Ver Resultados (Descifrados)

```powershell
# Listar todos los cuestionarios
python view_results.py --list

# Ver resultados de un cuestionario específico
python view_results.py --link aB3dEf9HiJkLmN0pQr
```

Salida de ejemplo:
```
================================================================================
RESULTS (Decrypted Accumulated Votes)
================================================================================

Question 1: ¿Cuál es tu lenguaje de programación favorito?
--------------------------------------------------------------------------------
  Python                         |  25 votes ( 50.0%) █████████████████████████
  JavaScript                     |  15 votes ( 30.0%) ███████████████
  Java                           |   5 votes ( 10.0%) █████
  C++                            |   5 votes ( 10.0%) █████
```

## 📊 Base de Datos

### Tabla `questionnaires`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID único |
| `link` | String | Link único del cuestionario |
| `deadline` | DateTime | Fecha límite |
| `questions_json` | Text | JSON con preguntas y opciones |
| `poly_degree` | Integer | Grado del polinomio (parámetro BFV) |
| `plain_modulus` | Integer | Módulo de texto plano |
| `ciph_modulus` | String | Módulo de cifrado (número grande) |
| `public_key_json` | Text | Clave pública serializada |
| `secret_key_json` | Text | Clave secreta serializada |
| `accumulated_responses_json` | Text | Respuestas cifradas acumuladas |
| `num_responses` | Integer | Número de respuestas recibidas |

### Tabla `responses`

Rastrea metadata de respuestas individuales (sin datos cifrados).

## 🔐 Cómo Funciona

### 1. Generación de Claves (Backend)

```python
params = BFVParameters(poly_degree=8, plain_modulus=17, ciph_modulus=8000000000000)
key_generator = BFVKeyGenerator(params)
public_key = key_generator.public_key  # Se envía al frontend
secret_key = key_generator.secret_key  # Se guarda en el servidor
```

### 2. Cifrado (Frontend)

```javascript
// Codificar respuesta como vector one-hot
const vector = [0, 0, 1, 0, 0, 0, 0, 0];  // Usuario seleccionó opción 2
const plaintext = encoder.encode(vector);

// Cifrar con la clave pública
const ciphertext = encryptor.encrypt(plaintext);

// Enviar al servidor
fetch('/api/submit-answers', {
    method: 'POST',
    body: JSON.stringify({encrypted_answers: [ciphertext.toJSON()]})
});
```

### 3. Acumulación Homomórfica (Backend)

```python
# Primera respuesta: [0, 0, 1, 0, 0, 0, 0, 0] cifrada
accumulated = ciphertext1

# Segunda respuesta: [0, 1, 0, 0, 0, 0, 0, 0] cifrada
accumulated = evaluator.add(accumulated, ciphertext2)

# Resultado cifrado: [0, 1, 1, 0, 0, 0, 0, 0] cifrado
# ¡El servidor nunca ve los valores individuales!
```

### 4. Descifrado (Backend, solo con clave secreta)

```python
plaintext = decryptor.decrypt(accumulated_ciphertext)
results = encoder.decode(plaintext)
# results = [0, 1, 1, 0, 0, 0, 0, 0]
# Opción 1: 0 votos
# Opción 2: 1 voto
# Opción 3: 1 voto
```

## 🛠️ API Endpoints

### `GET /api/questionnaire/<link>`

Obtiene un cuestionario con su clave pública.

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

Envía respuestas cifradas.

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

Obtiene estadísticas básicas (sin descifrar).

**Response:**
```json
{
    "link": "aB3dEf9HiJkLmN0pQr",
    "num_responses": 5,
    "deadline": "2025-12-30T12:00:00",
    "is_expired": false
}
```

## 🔧 Personalización

### Crear un Cuestionario Personalizado

Edita `create_questionnaire.py`:

```python
questions = [
    {
        'text': '¿Tu pregunta aquí?',
        'options': ['Opción 1', 'Opción 2', 'Opción 3', 'Opción 4', 
                   'Opción 5', 'Opción 6', 'Opción 7', 'Opción 8']
    },
    # ... más preguntas
]

create_questionnaire(questions, deadline_days=30, link='mi-cuestionario')
```

**Importante**: El número de opciones debe ser igual al `poly_degree` (por defecto 8).

### Ajustar Parámetros de Seguridad

En `create_questionnaire.py`:

```python
degree = 16           # Mayor = más seguro pero más lento
plain_modulus = 257   # Debe ser primo
ciph_modulus = 2**60  # Mucho mayor para seguridad
```

## 📊 Visualización de Resultados

### Interfaz Web (Recomendado)

Accede a los resultados con gráficos interactivos:

```
http://localhost:5000/results.html?id=<link-del-cuestionario>
```

**Características:**
- 📊 Gráficos interactivos (barras, circular, dona)
- 📋 Vista de tabla con porcentajes detallados
- 📄 Exportar resultados a CSV
- 🖨️ Imprimir resultados
- 📱 Diseño responsive

**Tipos de visualización:**
1. **Gráfico de Barras**: Distribución clara de votos
2. **Gráfico Circular**: Proporciones visuales
3. **Gráfico de Dona**: Vista moderna de proporciones
4. **Tabla**: Datos precisos con barras de progreso

### Línea de Comandos

Alternativa para terminal:

```powershell
python view_results.py --link <link-del-cuestionario>
```

Muestra resultados en formato texto con barras ASCII.

## 📝 Notas de Seguridad

1. **Clave Secreta**: Mantén `secret_key` segura. Quien la tenga puede descifrar todas las respuestas.

2. **Tamaño de Parámetros**: Los parámetros actuales (`degree=8`) son para demostración. Para producción, usa `degree >= 2048`.

3. **HTTPS**: En producción, usa HTTPS para proteger la transmisión de claves públicas.

4. **Base de Datos**: En producción, usa PostgreSQL o MySQL en lugar de SQLite.

## 🐛 Troubleshooting

### Error: "No module named 'bfv'"

Asegúrate de que `py-fhe` está en `Backend/` y que los imports incluyen:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py-fhe'))
```

### Error: "Questionnaire not found"

Verifica que el link es correcto:
```powershell
python view_results.py --list
```

### Frontend no carga

Verifica que el servidor Flask está corriendo y que los archivos JS están en `Frontend/`.

## 📚 Referencias

- [BFV Scheme Paper](https://eprint.iacr.org/2012/144.pdf)
- [py-fhe Library](https://github.com/sarojaerabelli/py-fhe)
- [Homomorphic Encryption](https://en.wikipedia.org/wiki/Homomorphic_encryption)

## 📄 Licencia

Este proyecto es para uso educativo.
