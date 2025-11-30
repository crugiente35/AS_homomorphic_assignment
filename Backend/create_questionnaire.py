"""
Script to create a new encrypted questionnaire.
Generates keys, stores questionnaire in database, and provides a link.
"""

import sys
import os

# Add py-fhe to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py-fhe'))

from datetime import datetime, timedelta, timezone
import secrets
import json

from models import init_db, get_session, Questionnaire
from bfv.bfv_key_generator import BFVKeyGenerator
from bfv.bfv_parameters import BFVParameters
from util.polynomial import Polynomial


def serialize_polynomial(poly):
    """Serialize a Polynomial object to JSON."""
    return {
        'ring_degree': poly.ring_degree,
        'coeffs': poly.coeffs
    }


def create_questionnaire(questions, deadline_days=7, link=None):
    """
    Create a new questionnaire with BFV encryption.
    
    Args:
        questions: List of question dicts with 'text' and 'options'
        deadline_days: Number of days until deadline (default: 7)
        link: Custom link (optional, will be generated if not provided)
    
    Returns:
        Questionnaire object
    """
    session = get_session()
    
    try:
        # Generate unique link if not provided
        if link is None:
            link = secrets.token_urlsafe(16)
        
        # Set deadline
        deadline = datetime.now(timezone.utc) + timedelta(days=deadline_days)
        
        # BFV Parameters - adjust these based on security needs
        degree = 8  # Should be power of 2
        plain_modulus = 17  # Prime number
        ciph_modulus = 8000000000000  # Large prime
        
        params = BFVParameters(
            poly_degree=degree,
            plain_modulus=plain_modulus,
            ciph_modulus=ciph_modulus
        )
        
        print(f"Generating BFV keys with parameters:")
        params.print_parameters()
        
        # Generate keys
        key_generator = BFVKeyGenerator(params)
        public_key = key_generator.public_key
        secret_key = key_generator.secret_key
        print("Secret key generated", secret_key)
        # Serialize keys
        public_key_json = {
            'p0': serialize_polynomial(public_key.p0),
            'p1': serialize_polynomial(public_key.p1)
        }
        
        secret_key_json = {
            'coeffs': secret_key.s.coeffs,
            'ring_degree': secret_key.s.ring_degree
        }
        
        # Create questionnaire
        questionnaire = Questionnaire(
            link=link,
            deadline=deadline,
            questions_json=json.dumps(questions),
            poly_degree=degree,
            plain_modulus=plain_modulus,
            ciph_modulus=str(ciph_modulus),
            public_key_json=json.dumps(public_key_json),
            secret_key_json=json.dumps(secret_key_json),
            accumulated_responses_json=None,
            num_responses=0
        )
        
        session.add(questionnaire)
        session.commit()
        
        # Store data before closing session to avoid DetachedInstanceError
        questionnaire_data = {
            'id': questionnaire.id,
            'link': questionnaire.link,
            'deadline': questionnaire.deadline,
            'num_questions': len(questionnaire.get_questions())
        }
        
        print(f"\n✅ Questionnaire created successfully!")
        print(f"   Link: {link}")
        print(f"   Deadline: {deadline.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   URL: http://localhost:5000/questionnaire.html?id={link}")
        
        return questionnaire_data
        
    except Exception as e:
        session.rollback()
        print(f"Error creating questionnaire: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        session.close()


def example_questionnaire():
    """Create an example questionnaire."""
    questions = [
        {
            'text': '¿Cuál es tu lenguaje de programación favorito?',
            'options': ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust', 'TypeScript', 'Otro']
        },
        {
            'text': '¿Cuántos años de experiencia tienes programando?',
            'options': ['0-1 años', '1-3 años', '3-5 años', '5-10 años', '10+ años', 'N/A', 'N/A', 'N/A']
        },
        {
            'text': '¿Qué tipo de desarrollo prefieres?',
            'options': ['Frontend', 'Backend', 'Full Stack', 'Mobile', 'DevOps', 'Data Science', 'Machine Learning', 'Otro']
        },
        {
            'text': '¿Has usado cifrado homomórfico antes?',
            'options': ['Sí', 'No', 'No sé qué es', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']
        }
    ]
    
    return create_questionnaire(questions, deadline_days=30)


if __name__ == '__main__':
    print("=" * 60)
    print("Creating Example Questionnaire")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Create example questionnaire
    questionnaire = example_questionnaire()
    
    if questionnaire:
        print("\n" + "=" * 60)
        print("Questionnaire Details:")
        print("=" * 60)
        print(f"ID: {questionnaire['id']}")
        print(f"Link: {questionnaire['link']}")
        print(f"Questions: {questionnaire['num_questions']}")
        print(f"Deadline: {questionnaire['deadline']}")
        print("\nShare this URL with participants:")
        print(f"http://localhost:5000/questionnaire.html?id={questionnaire['link']}")
