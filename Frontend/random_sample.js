/**
 * Random sampling utilities for FHE
 */

/**
 * Samples from a triangular distribution centered at 0
 * Used for error sampling in BFV encryption
 * 
 * @param {number} size - Number of samples to generate
 * @returns {number[]} Array of sampled values
 */
function sampleTriangle(size) {
    const samples = new Array(size);
    
    for (let i = 0; i < size; i++) {
        // Triangular distribution: sum of two uniform random variables
        // This gives values mostly concentrated around 0
        const u1 = Math.random();
        const u2 = Math.random();
        
        // Map to {-1, 0, 1} with triangular distribution
        const sum = u1 + u2;
        
        if (sum < 0.5) {
            samples[i] = -1;
        } else if (sum < 1.5) {
            samples[i] = 0;
        } else {
            samples[i] = 1;
        }
    }
    
    return samples;
}

/**
 * Samples uniformly from {0, 1, ..., max-1}
 * 
 * @param {number} size - Number of samples
 * @param {number} max - Maximum value (exclusive)
 * @returns {number[]} Array of random values
 */
function sampleUniform(size, max) {
    const samples = new Array(size);
    
    for (let i = 0; i < size; i++) {
        samples[i] = Math.floor(Math.random() * max);
    }
    
    return samples;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sampleTriangle,
        sampleUniform
    };
}

if (typeof window !== 'undefined') {
    window.sampleTriangle = sampleTriangle;
    window.sampleUniform = sampleUniform;
}
