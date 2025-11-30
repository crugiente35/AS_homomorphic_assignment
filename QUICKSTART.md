# 🚀 Inicio Rápido - Sistema de Cuestionarios con Cifrado Homomórfico

## Pasos para empezar en 5 minutos

### 1️⃣ Instalar dependencias

```powershell
cd Backend
pip install -r requirements.txt
```

### 2️⃣ Crear un cuestionario de ejemplo

```powershell
python create_questionnaire.py
```

**Salida esperada:**
```
✅ Questionnaire created successfully!
   Link: aB3dEf9HiJkLmN0pQr
   URL: http://localhost:5000/questionnaire.html?id=aB3dEf9HiJkLmN0pQr
```

### 3️⃣ Iniciar el servidor

```powershell
python app.py
```

**Salida esperada:**
```
Starting Flask server...
Server ready!
Access the application at: http://localhost:5000
* Running on http://0.0.0.0:5000
```

### 4️⃣ Abrir el cuestionario

Abre tu navegador en la URL generada:
```
http://localhost:5000/questionnaire.html?id=aB3dEf9HiJkLmN0pQr
```

### 5️⃣ Probar el cifrado (opcional)

Abre la página de test:
```
http://localhost:5000/test.html
```

Haz clic en "▶ Ejecutar Todos los Tests" para verificar que todo funciona.

### 6️⃣ Responder el cuestionario

1. Abre el cuestionario en el navegador
2. Responde todas las preguntas
3. Haz clic en "Enviar Respuestas Cifradas 🔐"
4. ¡Tus respuestas se cifran en el navegador y se envían al servidor!

### 7️⃣ Ver resultados descifrados

```powershell
# Listar todos los cuestionarios
python view_results.py --list

# Ver resultados de tu cuestionario
python view_results.py --link aB3dEf9HiJkLmN0pQr
```

**Salida esperada:**
```
================================================================================
RESULTS (Decrypted Accumulated Votes)
================================================================================

Question 1: ¿Cuál es tu lenguaje de programación favorito?
--------------------------------------------------------------------------------
  Python                         |   1 votes (100.0%) ██████████████████████████
```

---

## 🎯 Comandos Útiles

### Ver todos los cuestionarios
```powershell
python view_results.py --list
```

### Ver estadísticas sin descifrar
Abre en el navegador:
```
http://localhost:5000/api/questionnaire/<link>/stats
```

### Crear cuestionario personalizado

Edita `create_questionnaire.py` y modifica la función `example_questionnaire()`:

```python
questions = [
    {
        'text': '¿Tu pregunta aquí?',
        'options': ['Op1', 'Op2', 'Op3', 'Op4', 'Op5', 'Op6', 'Op7', 'Op8']
    }
]

create_questionnaire(questions, deadline_days=30, link='mi-encuesta')
```

Luego ejecuta:
```powershell
python create_questionnaire.py
```

---

## 📁 Estructura de Archivos

```
AS_assignment/
├── Frontend/
│   ├── questionnaire.html      # Página del cuestionario
│   ├── test.html               # Página de pruebas
│   └── *.js                    # Módulos de cifrado BFV
│
└── Backend/
    ├── app.py                  # Servidor Flask
    ├── models.py               # Base de datos SQLAlchemy
    ├── create_questionnaire.py # Crear cuestionarios
    ├── view_results.py         # Ver resultados
    └── py-fhe/                 # Librería de cifrado
```

---

## 🔒 ¿Qué hace cada componente?

### Frontend (JavaScript)
- **polynomial.js**: Aritmética de polinomios en anillos
- **ntt.js**: Transformada NTT para multiplicación rápida
- **batch_encoder.js**: Codifica vectores como polinomios (CRT)
- **bfv_encryptor.js**: Cifra polinomios con BFV
- **crypto_structures.js**: Clases Plaintext, Ciphertext, PublicKey

### Backend (Python)
- **models.py**: Define tabla SQL `questionnaires` con SQLAlchemy
- **app.py**: API Flask para servir cuestionarios y recibir respuestas
- **create_questionnaire.py**: Genera claves BFV y crea cuestionarios
- **view_results.py**: Descifra respuestas acumuladas con clave secreta

---

## 🔐 Flujo de Cifrado

```
Usuario → [Frontend]
   1. Responde: Opción 2
   2. Codifica: [0, 0, 1, 0, 0, 0, 0, 0]
   3. Cifra con clave pública
   4. Envía ciphertext

Servidor → [Backend]
   5. Recibe ciphertext
   6. Suma homomórficamente: accumulated += ciphertext
   7. Guarda en DB (cifrado)

Administrador → [Backend]
   8. Ejecuta view_results.py
   9. Descifra con clave secreta
   10. Ve totales: [5, 3, 8, 2, 1, 0, 0, 0]
```

**El servidor NUNCA ve las respuestas individuales en texto plano!** 🔒

---

## ⚠️ Solución de Problemas

### Error: ModuleNotFoundError: No module named 'flask'
```powershell
pip install -r requirements.txt
```

### Error: Questionnaire not found
Verifica el link:
```powershell
python view_results.py --list
```

### Frontend no carga archivos JS
Asegúrate de que el servidor Flask está corriendo:
```powershell
python app.py
```

Y accede vía `http://localhost:5000`, no abriendo el HTML directamente.

### Puerto 5000 ya en uso
Cambia el puerto en `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

---

## 📚 Más Información

Lee el [README.md](README.md) completo para:
- Explicación detallada de BFV
- Personalización avanzada
- Parámetros de seguridad
- API endpoints completos

---

## 🎓 Conceptos Clave

- **BFV**: Esquema de cifrado totalmente homomórfico
- **One-hot encoding**: Vector con un 1 y el resto 0s
- **Suma homomórfica**: Sumar ciphertexts sin descifrar
- **Clave pública**: Compartida con todos (frontend)
- **Clave secreta**: Solo para el servidor (descifrado)

---

¡Listo para empezar! 🚀
