/**
 * Number theory utilities for cryptographic operations.
 */

/**
 * Computes modular exponentiation: (base^exp) mod modulus
 * @param {number} base - Base number
 * @param {number} exp - Exponent
 * @param {number} modulus - Modulus
 * @returns {number} Result of (base^exp) mod modulus
 */
function modPow(base, exp, modulus) {
    if (modulus === 1) return 0;
    
    let result = 1;
    base = base % modulus;
    
    while (exp > 0) {
        if (exp % 2 === 1) {
            result = (result * base) % modulus;
        }
        exp = Math.floor(exp / 2);
        base = (base * base) % modulus;
    }
    
    return result;
}

/**
 * Computes modular multiplicative inverse using extended Euclidean algorithm
 * @param {number} a - Number to find inverse of
 * @param {number} m - Modulus
 * @returns {number} Modular inverse of a mod m
 */
function modInverse(a, m) {
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
 * Finds a primitive root of unity of given order modulo modulus
 * @param {number} order - Order of the root of unity
 * @param {number} modulus - Modulus
 * @returns {number} A primitive root of unity
 */
function rootOfUnity(order, modulus) {
    // Check if modulus - 1 is divisible by order
    if ((modulus - 1) % order !== 0) {
        throw new Error(`No ${order}-th root of unity exists mod ${modulus}`);
    }
    
    // Find a generator (primitive root)
    for (let g = 2; g < modulus; g++) {
        const candidate = modPow(g, Math.floor((modulus - 1) / order), modulus);
        
        // Check if this is a primitive order-th root of unity
        if (modPow(candidate, order, modulus) === 1) {
            // Verify it's primitive (not a root of smaller order)
            let isPrimitive = true;
            for (let i = 1; i < order; i++) {
                if (modPow(candidate, i, modulus) === 1) {
                    isPrimitive = false;
                    break;
                }
            }
            if (isPrimitive) {
                return candidate;
            }
        }
    }
    
    throw new Error(`Could not find ${order}-th root of unity mod ${modulus}`);
}

/**
 * Computes GCD of two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} GCD of a and b
 */
function gcd(a, b) {
    a = Math.abs(a);
    b = Math.abs(b);
    
    while (b !== 0) {
        [a, b] = [b, a % b];
    }
    
    return a;
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        modPow,
        modInverse,
        rootOfUnity,
        gcd
    };
}

if (typeof window !== 'undefined') {
    window.modPow = modPow;
    window.modInverse = modInverse;
    window.rootOfUnity = rootOfUnity;
    window.gcd = gcd;
}
