/**
 * Number Theoretic Transform (NTT) and Fermat Theoretic Transform (FTT) implementation.
 */

/**
 * Reverses the bits of a number
 * @param {number} num - Number to reverse
 * @param {number} bitLength - Number of bits to consider
 * @returns {number} Bit-reversed number
 */
function reverseBits(num, bitLength) {
    let result = 0;
    for (let i = 0; i < bitLength; i++) {
        result = (result << 1) | (num & 1);
        num >>= 1;
    }
    return result;
}

/**
 * Bit-reverses an array
 * @param {number[]} arr - Array to bit-reverse
 * @returns {number[]} Bit-reversed array
 */
function bitReverseArray(arr) {
    const n = arr.length;
    const logN = Math.log2(n);
    const result = new Array(n);
    
    for (let i = 0; i < n; i++) {
        result[reverseBits(i, logN)] = arr[i];
    }
    
    return result;
}

class NTTContext {
    /**
     * Number/Fermat Theoretic Transform parameters.
     * 
     * @param {number} polyDegree - Degree of the polynomial ring.
     * @param {number} coeffModulus - Modulus for coefficients of the polynomial.
     * @param {number} rootOfUnity - Root of unity (optional).
     */
    constructor(polyDegree, coeffModulus, rootOfUnity = null) {
        // Check if degree is power of 2
        if ((polyDegree & (polyDegree - 1)) !== 0) {
            throw new Error(`Polynomial degree must be a power of 2. d = ${polyDegree} is not.`);
        }
        
        this.coeffModulus = coeffModulus;
        this.degree = polyDegree;
        
        if (!rootOfUnity) {
            // Find a (2d)-th root of unity
            rootOfUnity = this._findRootOfUnity(2 * polyDegree, coeffModulus);
        }
        
        this.rootOfUnity = rootOfUnity;
        
        // Precompute roots of unity
        this.rootsOfUnity = this._computeRootsOfUnity();
        this.rootsOfUnityInv = this._computeRootsOfUnityInv();
        
        // Precompute scaled inverse roots for inverse transform
        const nInv = this._modInverse(polyDegree, coeffModulus);
        this.scaledRouInv = this.rootsOfUnityInv.map(r => (r * nInv) % coeffModulus);
    }

    /**
     * Finds a primitive root of unity
     */
    _findRootOfUnity(order, modulus) {
        if ((modulus - 1) % order !== 0) {
            throw new Error(`No ${order}-th root of unity exists mod ${modulus}`);
        }
        
        for (let g = 2; g < modulus; g++) {
            const candidate = this._modPow(g, Math.floor((modulus - 1) / order), modulus);
            
            if (this._modPow(candidate, order, modulus) === 1) {
                let isPrimitive = true;
                for (let i = 1; i < order; i++) {
                    if (this._modPow(candidate, i, modulus) === 1) {
                        isPrimitive = false;
                        break;
                    }
                }
                if (isPrimitive) return candidate;
            }
        }
        
        throw new Error(`Could not find ${order}-th root of unity mod ${modulus}`);
    }

    /**
     * Modular exponentiation
     */
    _modPow(base, exp, mod) {
        if (mod === 1) return 0;
        let result = 1;
        base = base % mod;
        
        while (exp > 0) {
            if (exp % 2 === 1) {
                result = (result * base) % mod;
            }
            exp = Math.floor(exp / 2);
            base = (base * base) % mod;
        }
        
        return result;
    }

    /**
     * Modular multiplicative inverse
     */
    _modInverse(a, m) {
        a = ((a % m) + m) % m;
        let [old_r, r] = [a, m];
        let [old_s, s] = [1, 0];
        
        while (r !== 0) {
            const quotient = Math.floor(old_r / r);
            [old_r, r] = [r, old_r - quotient * r];
            [old_s, s] = [s, old_s - quotient * s];
        }
        
        if (old_r > 1) {
            throw new Error(`${a} is not invertible mod ${m}`);
        }
        
        return ((old_s % m) + m) % m;
    }

    /**
     * Precompute roots of unity
     */
    _computeRootsOfUnity() {
        const roots = new Array(this.degree);
        for (let i = 0; i < this.degree; i++) {
            roots[i] = this._modPow(this.rootOfUnity, i, this.coeffModulus);
        }
        return roots;
    }

    /**
     * Precompute inverse roots of unity
     */
    _computeRootsOfUnityInv() {
        const rootInv = this._modInverse(this.rootOfUnity, this.coeffModulus);
        const roots = new Array(this.degree);
        for (let i = 0; i < this.degree; i++) {
            roots[i] = this._modPow(rootInv, i, this.coeffModulus);
        }
        return roots;
    }

    /**
     * Forward NTT transform
     * @param {number[]} values - Input values
     * @returns {number[]} Transformed values
     */
    nttFwd(values) {
        const n = values.length;
        const result = bitReverseArray([...values]);
        
        for (let len = 2; len <= n; len *= 2) {
            const step = this.degree / (len / 2);
            for (let i = 0; i < n; i += len) {
                for (let j = 0; j < len / 2; j++) {
                    const u = result[i + j];
                    const v = (result[i + j + len / 2] * this.rootsOfUnity[j * step]) % this.coeffModulus;
                    result[i + j] = (u + v) % this.coeffModulus;
                    result[i + j + len / 2] = ((u - v) % this.coeffModulus + this.coeffModulus) % this.coeffModulus;
                }
            }
        }
        
        return result;
    }

    /**
     * Inverse NTT transform
     * @param {number[]} values - Transformed values
     * @returns {number[]} Original values
     */
    nttInv(values) {
        const n = values.length;
        const result = bitReverseArray([...values]);
        
        for (let len = 2; len <= n; len *= 2) {
            const step = this.degree / (len / 2);
            for (let i = 0; i < n; i += len) {
                for (let j = 0; j < len / 2; j++) {
                    const u = result[i + j];
                    const v = (result[i + j + len / 2] * this.scaledRouInv[j * step]) % this.coeffModulus;
                    result[i + j] = (u + v) % this.coeffModulus;
                    result[i + j + len / 2] = ((u - v) % this.coeffModulus + this.coeffModulus) % this.coeffModulus;
                }
            }
        }
        
        return result;
    }

    /**
     * Forward FTT (Fermat Theoretic Transform)
     * @param {number[]} values - Input values
     * @returns {number[]} Transformed values
     */
    fttFwd(values) {
        return this.nttFwd(values);
    }

    /**
     * Inverse FTT
     * @param {number[]} values - Transformed values
     * @returns {number[]} Original values
     */
    fttInv(values) {
        return this.nttInv(values);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NTTContext, bitReverseArray, reverseBits };
}

if (typeof window !== 'undefined') {
    window.NTTContext = NTTContext;
    window.bitReverseArray = bitReverseArray;
    window.reverseBits = reverseBits;
}
