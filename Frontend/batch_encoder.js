/**
 * Batch encoder for BFV scheme using CRT batching
 */

class BatchEncoder {
    /**
     * An encoder for several integers to polynomials using CRT batching.
     * 
     * @param {Object} params - Parameters including polynomial degree and plaintext modulus
     */
    constructor(params) {
        this.degree = params.polyDegree;
        this.plainModulus = params.plainModulus;
        this.ntt = new NTTContext(params.polyDegree, params.plainModulus);
    }

    /**
     * Encodes a list of integers into a polynomial.
     * 
     * @param {number[]} values - Integers to encode (must have length equal to polynomial degree)
     * @returns {Plaintext} A Plaintext object which represents the encoded value
     */
    encode(values) {
        if (values.length !== this.degree) {
            throw new Error(`Length of list (${values.length}) does not equal polynomial degree (${this.degree})`);
        }

        const coeffs = this.ntt.fttInv(values);
        return new Plaintext(new Polynomial(this.degree, coeffs));
    }

    /**
     * Decodes a plaintext polynomial back to a list of integers.
     * 
     * @param {Plaintext} plain - Plaintext to decode
     * @returns {number[]} A decoded list of integers
     */
    decode(plain) {
        const result = this.ntt.fttFwd(plain.poly.coeffs);
        return result.map(val => ((val % this.plainModulus) + this.plainModulus) % this.plainModulus);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BatchEncoder;
}

if (typeof window !== 'undefined') {
    window.BatchEncoder = BatchEncoder;
}
