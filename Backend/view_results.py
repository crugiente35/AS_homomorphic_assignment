"""
Script to decrypt and view results from a questionnaire.
Only the server with the secret key can decrypt the accumulated responses.
"""

import sys
import os

# Add py-fhe to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py-fhe'))

from models import init_db, get_session, Questionnaire
from bfv.bfv_decryptor import BFVDecryptor
from bfv.bfv_parameters import BFVParameters
from bfv.batch_encoder import BatchEncoder
from util.ciphertext import Ciphertext
from util.polynomial import Polynomial
from util.secret_key import SecretKey
import json


def deserialize_polynomial(data):
    """Deserialize a Polynomial from JSON."""
    return Polynomial(data['ring_degree'], data['coeffs'])


def deserialize_ciphertext(data):
    """Deserialize a Ciphertext from JSON."""
    c0 = deserialize_polynomial(data['c0'])
    c1 = deserialize_polynomial(data['c1'])
    return Ciphertext(c0, c1, data.get('scaling_factor'), data.get('modulus'))


def view_results(link):
    """
    Decrypt and view results from a questionnaire.
    
    Args:
        link: Questionnaire link/ID
    """
    session = get_session()
    
    try:
        # Find questionnaire
        questionnaire = session.query(Questionnaire).filter_by(link=link).first()
        
        if not questionnaire:
            print(f"❌ Questionnaire with link '{link}' not found")
            return
        
        print("=" * 80)
        print(f"Questionnaire: {questionnaire.link}")
        print("=" * 80)
        print(f"Created: {questionnaire.created_at}")
        print(f"Deadline: {questionnaire.deadline}")
        print(f"Total Responses: {questionnaire.num_responses}")
        print(f"\n🌐 Ver resultados en el navegador:")
        print(f"   http://localhost:5000/results.html?id={questionnaire.link}")
        print()
        
        if questionnaire.num_responses == 0:
            print("⚠️  No responses yet!")
            return
        
        # Get parameters
        params = BFVParameters(
            poly_degree=questionnaire.poly_degree,
            plain_modulus=questionnaire.plain_modulus,
            ciph_modulus=int(questionnaire.ciph_modulus)
        )
        
        # Reconstruct secret key
        secret_key_data = questionnaire.get_secret_key()
        secret_key_poly = Polynomial(secret_key_data['ring_degree'], secret_key_data['coeffs'])
        secret_key = SecretKey(secret_key_poly)
        
        # Create decryptor and encoder
        decryptor = BFVDecryptor(params, secret_key)
        encoder = BatchEncoder(params)
        
        # Get accumulated responses
        accumulated = questionnaire.get_accumulated_responses()
        questions = questionnaire.get_questions()
        
        if not accumulated:
            print("⚠️  No accumulated responses found!")
            return
        
        print("=" * 80)
        print("RESULTS (Decrypted Accumulated Votes)")
        print("=" * 80)
        print()
        
        # Decrypt and display each question's results
        for i, (question, ciph_data) in enumerate(zip(questions, accumulated)):
            print(f"Question {i + 1}: {question['text']}")
            print("-" * 80)
            
            # Deserialize and decrypt
            ciphertext = deserialize_ciphertext(ciph_data)
            plaintext = decryptor.decrypt(ciphertext)
            decoded = encoder.decode(plaintext)
            
            # Display results for each option
            num_options = len(question['options'])
            for j in range(num_options):
                votes = decoded[j]
                option = question['options'][j]
                
                # Skip N/A options with 0 votes
                if option == 'N/A' and votes == 0:
                    continue
                
                # Calculate percentage
                percentage = (votes / questionnaire.num_responses * 100) if questionnaire.num_responses > 0 else 0
                
                # Create bar chart
                bar_length = int(percentage / 2)  # Scale to fit terminal
                bar = "█" * bar_length
                
                print(f"  {option:30s} | {votes:3d} votes ({percentage:5.1f}%) {bar}")
            
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error viewing results: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()


def list_questionnaires():
    """List all questionnaires in the database."""
    session = get_session()
    
    try:
        questionnaires = session.query(Questionnaire).all()
        
        if not questionnaires:
            print("No questionnaires found in database.")
            return
        
        print("=" * 80)
        print("All Questionnaires")
        print("=" * 80)
        
        for q in questionnaires:
            print(f"\nLink: {q.link}")
            print(f"  Created: {q.created_at}")
            print(f"  Deadline: {q.deadline}")
            print(f"  Responses: {q.num_responses}")
            print(f"  Questions: {len(q.get_questions())}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"Error listing questionnaires: {e}")
    
    finally:
        session.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='View encrypted questionnaire results')
    parser.add_argument('--link', type=str, help='Questionnaire link/ID to view')
    parser.add_argument('--list', action='store_true', help='List all questionnaires')
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    if args.list:
        list_questionnaires()
    elif args.link:
        view_results(args.link)
    else:
        print("Usage:")
        print("  python view_results.py --list                  # List all questionnaires")
        print("  python view_results.py --link <questionnaire_link>  # View results")
