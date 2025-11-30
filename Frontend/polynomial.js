/**
 * A module to handle polynomial arithmetic in the quotient ring Z_a[x]/f(x).
 */

class Polynomial {
    /**
     * A polynomial in the ring R_a.
     * R is the quotient ring Z[x]/f(x), where f(x) = x^d + 1.
     * 
     * @param {number} degree - Degree of quotient polynomial for ring R_a.
     * @param {number[]} coeffs - Array of integers representing coefficients of polynomial.
     */
    constructor(degree, coeffs) {
        this.ringDegree = degree;
        
        if (coeffs.length !== degree) {
            throw new Error(`Size of polynomial array ${coeffs.length} is not equal to degree ${degree} of ring`);
        }
        
        this.coeffs = coeffs;
    }

    /**
     * Adds two polynomials in the ring.
     * 
     * @param {Polynomial} poly - Polynomial to be added to the current polynomial.
     * @param {number} coeffModulus - Modulus a of coefficients of polynomial ring R_a.
     * @returns {Polynomial} A Polynomial which is the sum of the two polynomials.
     */
    add(poly, coeffModulus = null) {
        if (!(poly instanceof Polynomial)) {
            throw new Error('Argument must be a Polynomial');
        }

        const polySum = new Polynomial(
            this.ringDegree,
            this.coeffs.map((coeff, i) => coeff + poly.coeffs[i])
        );

        if (coeffModulus) {
            return polySum.mod(coeffModulus);
        }
        return polySum;
    }

    /**
     * Subtracts second polynomial from first polynomial in the ring.
     * 
     * @param {Polynomial} poly - Polynomial to be subtracted.
     * @param {number} coeffModulus - Modulus a of coefficients.
     * @returns {Polynomial} Difference between the two polynomials.
     */
    subtract(poly, coeffModulus = null) {
        if (!(poly instanceof Polynomial)) {
            throw new Error('Argument must be a Polynomial');
        }

        const polyDiff = new Polynomial(
            this.ringDegree,
            this.coeffs.map((coeff, i) => coeff - poly.coeffs[i])
        );

        if (coeffModulus) {
            return polyDiff.mod(coeffModulus);
        }
        return polyDiff;
    }

    /**
     * Multiplies two polynomials in the ring using NTT.
     * 
     * @param {Polynomial} poly - Polynomial to be multiplied.
     * @param {number} coeffModulus - Modulus a of coefficients.
     * @param {NTTContext} ntt - NTTContext object for multiplication.
     * @returns {Polynomial} Product of the two polynomials.
     */
    multiply(poly, coeffModulus, ntt = null) {
        if (!(poly instanceof Polynomial)) {
            throw new Error('Argument must be a Polynomial');
        }

        if (ntt) {
            // Transform both polynomials to NTT representation
            const nttSelf = ntt.nttFwd(this.coeffs);
            const nttPoly = ntt.nttFwd(poly.coeffs);
            
            // Component-wise multiplication
            const nttProd = nttSelf.map((val, i) => (val * nttPoly[i]) % coeffModulus);
            
            // Transform back
            const coeffs = ntt.nttInv(nttProd);
            return new Polynomial(this.ringDegree, coeffs);
        }

        // Naive multiplication O(n^2) - fallback
        const result = new Array(2 * this.ringDegree - 1).fill(0);
        
        for (let i = 0; i < this.ringDegree; i++) {
            for (let j = 0; j < poly.ringDegree; j++) {
                result[i + j] += this.coeffs[i] * poly.coeffs[j];
            }
        }

        // Reduce modulo x^d + 1
        const reduced = new Array(this.ringDegree).fill(0);
        for (let i = 0; i < result.length; i++) {
            if (i < this.ringDegree) {
                reduced[i] += result[i];
            } else {
                reduced[i - this.ringDegree] -= result[i];
            }
        }

        return new Polynomial(this.ringDegree, reduced.map(c => ((c % coeffModulus) + coeffModulus) % coeffModulus));
    }

    /**
     * Multiplies polynomial by a scalar.
     * 
     * @param {number} scalar - Scalar to multiply.
     * @param {number} coeffModulus - Modulus for coefficients.
     * @returns {Polynomial} Scaled polynomial.
     */
    scalarMultiply(scalar, coeffModulus = null) {
        const scaledCoeffs = this.coeffs.map(c => c * scalar);
        const result = new Polynomial(this.ringDegree, scaledCoeffs);
        
        if (coeffModulus) {
            return result.mod(coeffModulus);
        }
        return result;
    }

    /**
     * Applies modulus to all coefficients.
     * 
     * @param {number} coeffModulus - Modulus to apply.
     * @returns {Polynomial} Polynomial with coefficients mod coeffModulus.
     */
    mod(coeffModulus) {
        const modCoeffs = this.coeffs.map(c => {
            const mod = c % coeffModulus;
            return mod < 0 ? mod + coeffModulus : mod;
        });
        return new Polynomial(this.ringDegree, modCoeffs);
    }

    /**
     * Returns string representation of the polynomial.
     * @returns {string} String representation.
     */
    toString() {
        return `Polynomial(degree=${this.ringDegree}, coeffs=[${this.coeffs.join(', ')}])`;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Polynomial;
}

if (typeof window !== 'undefined') {
    window.Polynomial = Polynomial;
}
