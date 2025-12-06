@echo off
if "%1"=="" (
    echo Usage: generate_certs.bat [client_name]
    echo Example: generate_certs.bat User1
    echo Example: generate_certs.bat Alice
    exit /b 1
)

set CLIENT_NAME=%1

echo Generating client certificate for %CLIENT_NAME%...
openssl genrsa -out %CLIENT_NAME%.key 2048
openssl req -new -key %CLIENT_NAME%.key -out %CLIENT_NAME%.csr -subj "/CN=%CLIENT_NAME%"
openssl x509 -req -days 365 -in %CLIENT_NAME%.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out %CLIENT_NAME%.crt -extfile client.ext
openssl pkcs12 -export -out %CLIENT_NAME%.p12 -inkey %CLIENT_NAME%.key -in %CLIENT_NAME%.crt -certfile ca.crt -passout pass:x

echo Done! Import %CLIENT_NAME%.p12 into your browser (password: x)
