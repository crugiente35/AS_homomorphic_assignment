import {BatchEncoder, BFVEncryptor, PublicKey} from './crypto.js'

const params = {
    polyDegree: 8,
    plainModulus: 17,
    ciphModulus: 32768
}

const pkJson = {
    p0: {ringDegree: 8, coeffs: [1, 2, 3, 4, 5, 6, 7, 8]},
    p1: {ringDegree: 8, coeffs: [8, 7, 6, 5, 4, 3, 2, 1]}
}

const pk = PublicKey.fromJSON(pkJson)
const encoder = new BatchEncoder(params)
const encryptor = new BFVEncryptor(params, pk)

const vector = [1, 0, 0, 0, 0, 0, 0, 0]
const plaintext = encoder.encode(vector)
const ciphertext = encryptor.encrypt(plaintext)
const json = ciphertext.toJSON()

console.log('publicKey loaded:', pk.p0.coeffs.length === 8)
console.log('plaintext encoded:', plaintext.poly.coeffs.length === 8)
console.log('ciphertext c0 length:', json.c0.coeffs.length === 8)
console.log('ciphertext c1 length:', json.c1.coeffs.length === 8)

