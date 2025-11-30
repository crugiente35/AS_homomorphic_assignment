/**
 * Plaintext and Ciphertext data structures
 */

class Plaintext {
    /**
     * A plaintext consisting of one polynomial.
     * 
     * @param {Polynomial} poly - Plaintext polynomial
     * @param {number} scalingFactor - Scaling factor (optional)
     */
    constructor(poly, scalingFactor = null) {
        this.poly = poly;
        this.scalingFactor = scalingFactor;
    }

    toString() {
        return `Plaintext(${this.poly.toString()})`;
    }

    /**
     * Serializes plaintext to JSON
     */
    toJSON() {
        return {
            poly: {
                ringDegree: this.poly.ringDegree,
                coeffs: this.poly.coeffs
            },
            scalingFactor: this.scalingFactor
        };
    }

    /**
     * Deserializes plaintext from JSON
     */
    static fromJSON(json) {
        // Support both snake_case (from Python) and camelCase
        const degree = json.poly.ringDegree || json.poly.ring_degree;
        const poly = new Polynomial(degree, json.poly.coeffs);
        return new Plaintext(poly, json.scalingFactor);
    }
}

class Ciphertext {
    /**
     * A ciphertext consisting of a pair of polynomials.
     * 
     * @param {Polynomial} c0 - First element of ciphertext
     * @param {Polynomial} c1 - Second element of ciphertext
     * @param {number} scalingFactor - Scaling factor (optional)
     * @param {number} modulus - Ciphertext modulus (optional)
     */
    constructor(c0, c1, scalingFactor = null, modulus = null) {
        this.c0 = c0;
        this.c1 = c1;
        this.scalingFactor = scalingFactor;
        this.modulus = modulus;
    }

    toString() {
        return `Ciphertext(c0: ${this.c0.toString()}, c1: ${this.c1.toString()})`;
    }

    /**
     * Serializes ciphertext to JSON for transmission
     */
    toJSON() {
        return {
            c0: {
                ringDegree: this.c0.ringDegree,
                coeffs: this.c0.coeffs
            },
            c1: {
                ringDegree: this.c1.ringDegree,
                coeffs: this.c1.coeffs
            },
            scalingFactor: this.scalingFactor,
            modulus: this.modulus
        };
    }

    /**
     * Deserializes ciphertext from JSON
     */
    static fromJSON(json) {
        // Support both snake_case (from Python) and camelCase
        const c0Degree = json.c0.ringDegree || json.c0.ring_degree;
        const c1Degree = json.c1.ringDegree || json.c1.ring_degree;
        
        const c0 = new Polynomial(c0Degree, json.c0.coeffs);
        const c1 = new Polynomial(c1Degree, json.c1.coeffs);
        return new Ciphertext(c0, c1, json.scalingFactor, json.modulus);
    }
}

class PublicKey {
    /**
     * A public key consisting of a pair of polynomials.
     * 
     * @param {Polynomial} p0 - First element of public key
     * @param {Polynomial} p1 - Second element of public key
     */
    constructor(p0, p1) {
        this.p0 = p0;
        this.p1 = p1;
    }

    toString() {
        return `PublicKey(p0: ${this.p0.toString()}, p1: ${this.p1.toString()})`;
    }

    /**
     * Serializes public key to JSON
     */
    toJSON() {
        return {
            p0: {
                ringDegree: this.p0.ringDegree,
                coeffs: this.p0.coeffs
            },
            p1: {
                ringDegree: this.p1.ringDegree,
                coeffs: this.p1.coeffs
            }
        };
    }

    /**
     * Deserializes public key from JSON
     */
    static fromJSON(json) {
        // Support both snake_case (from Python) and camelCase
        const p0Degree = json.p0.ringDegree || json.p0.ring_degree;
        const p1Degree = json.p1.ringDegree || json.p1.ring_degree;
        
        const p0 = new Polynomial(p0Degree, json.p0.coeffs);
        const p1 = new Polynomial(p1Degree, json.p1.coeffs);
        return new PublicKey(p0, p1);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Plaintext,
        Ciphertext,
        PublicKey
    };
}

if (typeof window !== 'undefined') {
    window.Plaintext = Plaintext;
    window.Ciphertext = Ciphertext;
    window.PublicKey = PublicKey;
}
