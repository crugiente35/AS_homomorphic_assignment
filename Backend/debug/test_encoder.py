"""
Test to compare Python BatchEncoder with JavaScript output
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bfv.batch_encoder import BatchEncoder
from bfv.bfv_parameters import BFVParameters

# Same parameters as in the system
degree = 8
plain_modulus = 17
ciph_modulus = 8000000000000

params = BFVParameters(
    poly_degree=degree,
    plain_modulus=plain_modulus,
    ciph_modulus=ciph_modulus
)

encoder = BatchEncoder(params)

# Test cases from the logs
test_cases = [
    [1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0],
]

print("="*80)
print("PYTHON BATCH ENCODER TEST")
print("="*80)

for i, values in enumerate(test_cases):
    print(f"\nTest {i+1}: {values}")
    plaintext = encoder.encode(values)
    coeffs = plaintext.poly.coeffs
    print(f"Encoded coeffs: {coeffs}")
    
    # Decode back
    decoded = encoder.decode(plaintext)
    print(f"Decoded: {decoded}")
    
    if decoded == values:
        print("✓ Round-trip OK")
    else:
        print("✗ Round-trip FAILED")

print("\n" + "="*80)
print("EXPECTED OUTPUT FOR JAVASCRIPT:")
print("="*80)
print("\nFor [1,0,0,0,0,0,0,0]:")
print(f"  Should encode to: {encoder.encode([1,0,0,0,0,0,0,0]).poly.coeffs}")
print("\nFor [0,1,0,0,0,0,0,0]:")
print(f"  Should encode to: {encoder.encode([0,1,0,0,0,0,0,0]).poly.coeffs}")
print("\n" + "="*80)
