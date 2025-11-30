/**
 * BFV Encryptor for encrypting messages with a public key
 */

class BFVEncryptor {
    /**
     * An object that can encrypt data using BFV given a public key.
     * 
     * @param {Object} params - Parameters including polynomial degree and ciphertext modulus
     * @param {PublicKey} publicKey - Public key used for encryption
     */
    constructor(params, publicKey) {
        this.polyDegree = params.polyDegree;
        this.coeffModulus = params.ciphModulus;
        this.publicKey = publicKey;
        this.scalingFactor = Math.floor(params.scalingFactor);
    }

    /**
     * Encrypts a message.
     * 
     * @param {Plaintext} message - Plaintext to be encrypted
     * @returns {Ciphertext} A ciphertext consisting of a pair of polynomials
     */
    encrypt(message) {
        const p0 = this.publicKey.p0;
        const p1 = this.publicKey.p1;
        
        // Scale the message
        const scaledMessage = message.poly.scalarMultiply(this.scalingFactor, this.coeffModulus);

        // Sample random polynomial and errors
        const randomVec = new Polynomial(
            this.polyDegree,
            sampleTriangle(this.polyDegree)
        );
        
        // For security, we should use triangle distribution for errors
        // But for deterministic testing, we can use zeros
        let error1 = new Polynomial(
            this.polyDegree,
            sampleTriangle(this.polyDegree)
        );
        
        // Uncomment below for zero errors (testing only!)
        // error1 = new Polynomial(this.polyDegree, new Array(this.polyDegree).fill(0));
        
        let error2 = new Polynomial(
            this.polyDegree,
            sampleTriangle(this.polyDegree)
        );
        
        // Uncomment below for zero errors (testing only!)
        // error2 = new Polynomial(this.polyDegree, new Array(this.polyDegree).fill(0));

        // Compute ciphertext components
        // c0 = error1 + p0 * randomVec + scaledMessage
        const c0 = error1
            .add(p0.multiply(randomVec, this.coeffModulus), this.coeffModulus)
            .add(scaledMessage, this.coeffModulus);
        
        // c1 = error2 + p1 * randomVec
        const c1 = error2.add(
            p1.multiply(randomVec, this.coeffModulus),
            this.coeffModulus
        );

        return new Ciphertext(c0, c1);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BFVEncryptor;
}

if (typeof window !== 'undefined') {
    window.BFVEncryptor = BFVEncryptor;
}
