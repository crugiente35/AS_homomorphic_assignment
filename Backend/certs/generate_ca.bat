@echo off
echo Generating CA key and certificate...
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=QuestionnaireCA"

echo Generating server key and certificate...
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -extfile server.ext

echo CA and server certificates generated!
echo Now run: generate_client.bat [client_name]

