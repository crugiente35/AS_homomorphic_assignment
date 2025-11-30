"""
Test to simulate the full questionnaire flow:
1. Generate keys (backend)
2. Encrypt responses (simulating frontend)
3. Accumulate (backend)
4. Decrypt (backend)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py-fhe'))

from bfv.batch_encoder import BatchEncoder
from bfv.bfv_decryptor import BFVDecryptor
from bfv.bfv_encryptor import BFVEncryptor
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_key_generator import BFVKeyGenerator
from bfv.bfv_parameters import BFVParameters
import json

print("="*80)
print("SIMULATING QUESTIONNAIRE FLOW")
print("="*80)

# 1. BACKEND: Generate keys
print("\n1. Backend: Generating keys...")
degree = 8
plain_modulus = 17
ciph_modulus = 8000000000000

params = BFVParameters(
    poly_degree=degree,
    plain_modulus=plain_modulus,
    ciph_modulus=ciph_modulus
)

key_generator = BFVKeyGenerator(params)
public_key = key_generator.public_key
secret_key = key_generator.secret_key

encoder = BatchEncoder(params)
encryptor = BFVEncryptor(params, public_key)
decryptor = BFVDecryptor(params, secret_key)
evaluator = BFVEvaluator(params)

print(f"✓ Keys generated")
print(f"  poly_degree: {degree}")
print(f"  plain_modulus: {plain_modulus}")
print(f"  ciph_modulus: {ciph_modulus}")

# 2. FRONTEND: Simulate 3 users responding to 2 questions
print("\n2. Frontend: Simulating user responses...")

# Question 1 responses (expected sum: [1,1,0,1,0,0,0,0])
q1_response1 = [1,0,0,0,0,0,0,0]  # Option 0
q1_response2 = [0,1,0,0,0,0,0,0]  # Option 1
q1_response3 = [0,0,0,1,0,0,0,0]  # Option 3

# Question 2 responses (expected sum: [0,2,0,1,0,0,0,0])
q2_response1 = [0,1,0,0,0,0,0,0]  # Option 1
q2_response2 = [0,1,0,0,0,0,0,0]  # Option 1
q2_response3 = [0,0,0,1,0,0,0,0]  # Option 3

print(f"  User 1 Q1: {q1_response1}")
print(f"  User 2 Q1: {q1_response2}")
print(f"  User 3 Q1: {q1_response3}")
print(f"  Expected Q1 sum: [1,1,0,1,0,0,0,0]")

print(f"\n  User 1 Q2: {q2_response1}")
print(f"  User 2 Q2: {q2_response2}")
print(f"  User 3 Q2: {q2_response3}")
print(f"  Expected Q2 sum: [0,2,0,1,0,0,0,0]")

# Encrypt responses (simulating what frontend does)
print("\n3. Frontend: Encrypting responses...")

# User 1
q1_r1_encoded = encoder.encode(q1_response1)
q1_r1_encrypted = encryptor.encrypt(q1_r1_encoded)
q2_r1_encoded = encoder.encode(q2_response1)
q2_r1_encrypted = encryptor.encrypt(q2_r1_encoded)

# User 2
q1_r2_encoded = encoder.encode(q1_response2)
q1_r2_encrypted = encryptor.encrypt(q1_r2_encoded)
q2_r2_encoded = encoder.encode(q2_response2)
q2_r2_encrypted = encryptor.encrypt(q2_r2_encoded)

# User 3
q1_r3_encoded = encoder.encode(q1_response3)
q1_r3_encrypted = encryptor.encrypt(q1_r3_encoded)
q2_r3_encoded = encoder.encode(q2_response3)
q2_r3_encrypted = encryptor.encrypt(q2_r3_encoded)

print(f"✓ All responses encrypted")

# 4. BACKEND: Accumulate responses (simulating submit_answers endpoint)
print("\n4. Backend: Accumulating responses...")

# Initialize with first user's responses
q1_accumulated = q1_r1_encrypted
q2_accumulated = q2_r1_encrypted

print(f"  After user 1: initialized")

# Add user 2
q1_accumulated = evaluator.add(q1_accumulated, q1_r2_encrypted)
q2_accumulated = evaluator.add(q2_accumulated, q2_r2_encrypted)

print(f"  After user 2: accumulated")

# Add user 3
q1_accumulated = evaluator.add(q1_accumulated, q1_r3_encrypted)
q2_accumulated = evaluator.add(q2_accumulated, q2_r3_encrypted)

print(f"  After user 3: accumulated")
print(f"✓ All responses accumulated")

# 5. BACKEND: Decrypt results (simulating decrypt_questionnaire function)
print("\n5. Backend: Decrypting accumulated results...")

# Question 1
q1_plaintext = decryptor.decrypt(q1_accumulated)
q1_decoded = encoder.decode(q1_plaintext)

print(f"\nQuestion 1:")
print(f"  Decrypted plaintext coeffs: {q1_plaintext.poly.coeffs}")
print(f"  Decoded values: {q1_decoded}")
print(f"  Expected:       [1, 1, 0, 1, 0, 0, 0, 0]")
if q1_decoded == [1, 1, 0, 1, 0, 0, 0, 0]:
    print(f"  ✓ MATCH!")
else:
    print(f"  ✗ MISMATCH!")

# Question 2
q2_plaintext = decryptor.decrypt(q2_accumulated)
q2_decoded = encoder.decode(q2_plaintext)

print(f"\nQuestion 2:")
print(f"  Decrypted plaintext coeffs: {q2_plaintext.poly.coeffs}")
print(f"  Decoded values: {q2_decoded}")
print(f"  Expected:       [0, 2, 0, 1, 0, 0, 0, 0]")
if q2_decoded == [0, 2, 0, 1, 0, 0, 0, 0]:
    print(f"  ✓ MATCH!")
else:
    print(f"  ✗ MISMATCH!")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
