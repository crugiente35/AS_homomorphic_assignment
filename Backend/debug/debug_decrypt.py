"""
Debug script to test decryption manually
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import json
from bfv.bfv_parameters import BFVParameters
from bfv.bfv_decryptor import BFVDecryptor
from bfv.batch_encoder import BatchEncoder
from util.ciphertext import Ciphertext
from util.polynomial import Polynomial
from util.secret_key import SecretKey

# Connect to database (in parent directory)
db_path = os.path.join(os.path.dirname(__file__), '..', 'questionnaires.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List available questionnaires
cursor.execute("""
    SELECT link, num_responses, deadline
    FROM questionnaires
    ORDER BY created_at DESC
""")

questionnaires = cursor.fetchall()

if not questionnaires:
    print("No questionnaires found in database!")
    conn.close()
    sys.exit(1)

print("Available questionnaires:")
for i, (link, num_resp, deadline) in enumerate(questionnaires):
    print(f"  {i+1}. {link} ({num_resp} responses, deadline: {deadline})")

# Use the first questionnaire with responses, or just the first one
selected_link = None
for link, num_resp, deadline in questionnaires:
    if num_resp > 0:
        selected_link = link
        break

if not selected_link:
    selected_link = questionnaires[0][0]
    print(f"\nNo questionnaires with responses found. Using first one: {selected_link}")
else:
    print(f"\nUsing questionnaire: {selected_link}")

# Get questionnaire details
cursor.execute("""
    SELECT poly_degree, plain_modulus, ciph_modulus,
           secret_key_json, accumulated_responses_json, num_responses
    FROM questionnaires
    WHERE link = ?
""", (selected_link,))

result = cursor.fetchone()
conn.close()

if not result:
    print("Error: Could not retrieve questionnaire details!")
    sys.exit(1)

poly_degree, plain_modulus, ciph_modulus, secret_key_json, accumulated_json, num_responses = result

print("="*80)
print("DEBUGGING DECRYPTION")
print("="*80)

print(f"\nParametros BFV:")
print(f"  poly_degree: {poly_degree}")
print(f"  plain_modulus: {plain_modulus}")
print(f"  ciph_modulus: {ciph_modulus}")

# Create parameters
params = BFVParameters(
    poly_degree=poly_degree,
    plain_modulus=plain_modulus,
    ciph_modulus=int(ciph_modulus)
)

print(f"\nBFVParameters created")
print(f"  scaling_factor: {params.scaling_factor}")

# Reconstruct secret key
secret_key_data = json.loads(secret_key_json)
print(f"\nSecret key data:")
print(f"  ring_degree: {secret_key_data['ring_degree']}")
print(f"  coeffs (first 8): {secret_key_data['coeffs'][:8]}")

secret_key_poly = Polynomial(secret_key_data['ring_degree'], secret_key_data['coeffs'])
secret_key = SecretKey(secret_key_poly)

print(f"\nSecret key reconstructed")

# Create decryptor and encoder
decryptor = BFVDecryptor(params, secret_key)
encoder = BatchEncoder(params)

print(f"\nDecryptor and Encoder created")

# Get accumulated responses
accumulated = json.loads(accumulated_json)

print(f"\n{'='*80}")
print(f"DECRYPTING {len(accumulated)} QUESTIONS")
print(f"{'='*80}")

for i, ciph_data in enumerate(accumulated):
    print(f"\n--- Pregunta {i+1} ---")
    
    # Reconstruct ciphertext
    c0 = Polynomial(ciph_data['c0']['ring_degree'], ciph_data['c0']['coeffs'])
    c1 = Polynomial(ciph_data['c1']['ring_degree'], ciph_data['c1']['coeffs'])
    
    scaling_factor = ciph_data.get('scaling_factor')
    modulus = ciph_data.get('modulus')
    
    ciphertext = Ciphertext(c0, c1, scaling_factor, modulus)
    
    print(f"Ciphertext reconstructed:")
    print(f"  c0.ring_degree: {ciphertext.c0.ring_degree}")
    print(f"  c1.ring_degree: {ciphertext.c1.ring_degree}")
    print(f"  scaling_factor: {ciphertext.scaling_factor}")
    print(f"  modulus: {ciphertext.modulus}")
    
    # Decrypt
    print(f"\nDecrypting...")
    plaintext = decryptor.decrypt(ciphertext)
    
    print(f"Plaintext decrypted:")
    print(f"  poly.ring_degree: {plaintext.poly.ring_degree}")
    print(f"  poly.coeffs: {plaintext.poly.coeffs}")
    
    # Decode
    print(f"\nDecoding...")
    decoded = encoder.decode(plaintext)
    
    print(f"Decoded values: {decoded}")
    
    # Show results
    print(f"\nResults for question {i+1}:")
    for j, votes in enumerate(decoded):
        if votes > 0:
            print(f"  Option {j}: {votes} votes")

print(f"\n{'='*80}")
print(f"DECRYPTION TEST COMPLETE")
print(f"{'='*80}")
