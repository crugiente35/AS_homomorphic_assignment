function sampleTriangle(size) {
    const samples = new Array(size);
    for (let i = 0; i < size; i++) {
        const sum = Math.random() + Math.random();
        if (sum < 0.5) samples[i] = -1;
        else if (sum < 1.5) samples[i] = 0;
        else samples[i] = 1;
    }
    return samples;
}

function reverseBits(num, bitLength) {
    let result = 0;
    for (let i = 0; i < bitLength; i++) {
        result = (result << 1) | (num & 1);
        num >>= 1;
    }
    return result;
}

function bitReverseArray(arr) {
    const n = arr.length;
    const logN = Math.log2(n);
    const result = new Array(n);
    for (let i = 0; i < n; i++) {
        result[reverseBits(i, logN)] = arr[i];
    }
    return result;
}

class Polynomial {
    constructor(degree, coeffs) {
        this.ringDegree = degree;
        this.coeffs = coeffs;
    }

    add(poly, coeffModulus = null) {
        const polySum = new Polynomial(this.ringDegree, this.coeffs.map((c, i) => c + poly.coeffs[i]));
        return coeffModulus ? polySum.mod(coeffModulus) : polySum;
    }

    multiply(poly, coeffModulus) {
        const result = new Array(2 * this.ringDegree - 1).fill(0);
        for (let i = 0; i < this.ringDegree; i++) {
            for (let j = 0; j < poly.ringDegree; j++) {
                result[i + j] += this.coeffs[i] * poly.coeffs[j];
            }
        }
        const reduced = new Array(this.ringDegree).fill(0);
        for (let i = 0; i < result.length; i++) {
            if (i < this.ringDegree) reduced[i] += result[i];
            else reduced[i - this.ringDegree] -= result[i];
        }
        return new Polynomial(this.ringDegree, reduced.map(c => ((c % coeffModulus) + coeffModulus) % coeffModulus));
    }

    scalarMultiply(scalar, coeffModulus = null) {
        const result = new Polynomial(this.ringDegree, this.coeffs.map(c => c * scalar));
        return coeffModulus ? result.mod(coeffModulus) : result;
    }

    mod(coeffModulus) {
        return new Polynomial(this.ringDegree, this.coeffs.map(c => {
            const mod = c % coeffModulus;
            return mod < 0 ? mod + coeffModulus : mod;
        }));
    }
}

class NTTContext {
    constructor(polyDegree, coeffModulus) {
        this.coeffModulus = coeffModulus;
        this.degree = polyDegree;
        this.rootOfUnity = this._findRootOfUnity(2 * polyDegree, coeffModulus);
        this.rootsOfUnity = this._computeRootsOfUnity();
        this.rootsOfUnityInv = this._computeRootsOfUnityInv();
    }

    _modPow(base, exp, mod) {
        if (mod === 1) return 0;
        let result = 1;
        base = base % mod;
        while (exp > 0) {
            if (exp % 2 === 1) result = (result * base) % mod;
            exp = Math.floor(exp / 2);
            base = (base * base) % mod;
        }
        return result;
    }

    _modInverse(a, m) {
        a = ((a % m) + m) % m;
        let [old_r, r] = [a, m];
        let [old_s, s] = [1, 0];
        while (r !== 0) {
            const q = Math.floor(old_r / r);
            [old_r, r] = [r, old_r - q * r];
            [old_s, s] = [s, old_s - q * s];
        }
        return ((old_s % m) + m) % m;
    }

    _findRootOfUnity(order, modulus) {
        for (let g = 2; g < modulus; g++) {
            const candidate = this._modPow(g, Math.floor((modulus - 1) / order), modulus);
            if (this._modPow(candidate, order, modulus) === 1) {
                let isPrimitive = true;
                for (let i = 1; i < order; i++) {
                    if (this._modPow(candidate, i, modulus) === 1) { isPrimitive = false; break; }
                }
                if (isPrimitive) return candidate;
            }
        }
        throw new Error("Root not found");
    }

    _computeRootsOfUnity() {
        const roots = new Array(this.degree);
        for (let i = 0; i < this.degree; i++) roots[i] = this._modPow(this.rootOfUnity, i, this.coeffModulus);
        return roots;
    }

    _computeRootsOfUnityInv() {
        const rootInv = this._modInverse(this.rootOfUnity, this.coeffModulus);
        const roots = new Array(this.degree);
        for (let i = 0; i < this.degree; i++) roots[i] = this._modPow(rootInv, i, this.coeffModulus);
        return roots;
    }

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

    nttInv(values) {
        const n = values.length;
        const result = bitReverseArray([...values]);
        for (let len = 2; len <= n; len *= 2) {
            const step = this.degree / (len / 2);
            for (let i = 0; i < n; i += len) {
                for (let j = 0; j < len / 2; j++) {
                    const u = result[i + j];
                    const v = (result[i + j + len / 2] * this.rootsOfUnityInv[j * step]) % this.coeffModulus;
                    result[i + j] = (u + v) % this.coeffModulus;
                    result[i + j + len / 2] = ((u - v) % this.coeffModulus + this.coeffModulus) % this.coeffModulus;
                }
            }
        }
        return result;
    }

    fttFwd(values) {
        const fttInput = values.map((val, i) => (val * this.rootsOfUnity[i]) % this.coeffModulus);
        return this.nttFwd(fttInput);
    }

    fttInv(values) {
        const toScaleDown = this.nttInv(values);
        const degreeInv = this._modInverse(this.degree, this.coeffModulus);
        return toScaleDown.map((val, i) => {
            const scaled = (val * this.rootsOfUnityInv[i]) % this.coeffModulus;
            return (scaled * degreeInv) % this.coeffModulus;
        });
    }
}

class Plaintext {
    constructor(poly) { this.poly = poly; }
}

class Ciphertext {
    constructor(c0, c1) { this.c0 = c0; this.c1 = c1; }
    toJSON() {
        return {
            c0: { ringDegree: this.c0.ringDegree, coeffs: this.c0.coeffs },
            c1: { ringDegree: this.c1.ringDegree, coeffs: this.c1.coeffs }
        };
    }
}

class PublicKey {
    constructor(p0, p1) { this.p0 = p0; this.p1 = p1; }
    static fromJSON(json) {
        const p0 = new Polynomial(json.p0.ringDegree || json.p0.ring_degree, json.p0.coeffs);
        const p1 = new Polynomial(json.p1.ringDegree || json.p1.ring_degree, json.p1.coeffs);
        return new PublicKey(p0, p1);
    }
}

class BatchEncoder {
    constructor(params) {
        this.degree = params.polyDegree;
        this.ntt = new NTTContext(params.polyDegree, params.plainModulus);
    }
    encode(values) {
        return new Plaintext(new Polynomial(this.degree, this.ntt.fttInv(values)));
    }
}

class BFVEncryptor {
    constructor(params, publicKey) {
        this.polyDegree = params.polyDegree;
        this.coeffModulus = params.ciphModulus;
        this.publicKey = publicKey;
        this.scalingFactor = Math.floor(params.ciphModulus / params.plainModulus);
    }
    encrypt(message) {
        const p0 = this.publicKey.p0;
        const p1 = this.publicKey.p1;
        const scaledMessage = message.poly.scalarMultiply(this.scalingFactor, this.coeffModulus);
        const randomVec = new Polynomial(this.polyDegree, sampleTriangle(this.polyDegree));
        const error1 = new Polynomial(this.polyDegree, sampleTriangle(this.polyDegree));
        const error2 = new Polynomial(this.polyDegree, sampleTriangle(this.polyDegree));
        const c0 = error1.add(p0.multiply(randomVec, this.coeffModulus), this.coeffModulus).add(scaledMessage, this.coeffModulus);
        const c1 = error2.add(p1.multiply(randomVec, this.coeffModulus), this.coeffModulus);
        return new Ciphertext(c0, c1);
    }
}

export { PublicKey, BatchEncoder, BFVEncryptor };
