"""
Flask API for encrypted questionnaire system.
Handles questionnaire retrieval and encrypted answer submission.
"""

import sys
import os

# Add py-fhe to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py-fhe'))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone
import json

from models import init_db, get_session, Questionnaire, Response
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_parameters import BFVParameters
from util.ciphertext import Ciphertext
from util.polynomial import Polynomial

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize database
DB_URL = 'sqlite:///questionnaires.db'
engine, Session = init_db(DB_URL)


def serialize_polynomial(poly):
    """Serialize a Polynomial object to JSON."""
    return {
        'ring_degree': poly.ring_degree,
        'coeffs': poly.coeffs
    }


def deserialize_polynomial(data):
    """Deserialize a Polynomial from JSON."""
    # Support both camelCase (from JS) and snake_case
    ring_degree = data.get('ring_degree') or data.get('ringDegree')
    return Polynomial(ring_degree, data['coeffs'])


def serialize_ciphertext(ciph):
    """Serialize a Ciphertext object to JSON."""
    return {
        'c0': serialize_polynomial(ciph.c0),
        'c1': serialize_polynomial(ciph.c1),
        'scaling_factor': ciph.scaling_factor,
        'modulus': ciph.modulus
    }
def deserialize_ciphertext(data):
    """Deserialize a Ciphertext from JSON."""
    c0 = deserialize_polynomial(data['c0'])
    c1 = deserialize_polynomial(data['c1'])
    # Support both camelCase and snake_case
    scaling_factor = data.get('scaling_factor') or data.get('scalingFactor')
    return Ciphertext(c0, c1, scaling_factor, data.get('modulus'))


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('../Frontend', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from Frontend directory."""
    return send_from_directory('../Frontend', filename)


@app.route('/api/questionnaire/<string:link>', methods=['GET'])
def get_questionnaire(link):
    """
    Get questionnaire details including public key.
    
    Returns:
        JSON with questionnaire data, questions, public key, and parameters
    """
    session = get_session(DB_URL)
    
    try:
        questionnaire = session.query(Questionnaire).filter_by(link=link).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        # Check if expired
        # Make deadline timezone-aware if it's naive
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) > deadline:
            return jsonify({
                'error': 'Questionnaire has expired',
                'deadline': questionnaire.deadline.isoformat()
            }), 410
        
        response_data = {
            'id': questionnaire.id,
            'link': questionnaire.link,
            'deadline': questionnaire.deadline.isoformat(),
            'questions': questionnaire.get_questions(),
            'public_key': questionnaire.get_public_key(),
            'params': questionnaire.get_params()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error retrieving questionnaire: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/submit-answers', methods=['POST'])
def submit_answers():
    """
    Receive encrypted answers and accumulate them.
    
    Expected JSON:
    {
        'questionnaire_id': 'link-or-id',
        'encrypted_answers': [ciphertext1, ciphertext2, ...]
    }
    """
    session = get_session(DB_URL)
    
    try:
        data = request.get_json()
        
        questionnaire_id = data.get('questionnaire_id')
        encrypted_answers = data.get('encrypted_answers')
        
        if not questionnaire_id or not encrypted_answers:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Find questionnaire
        questionnaire = session.query(Questionnaire).filter_by(link=questionnaire_id).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        # Check if expired
        # Make deadline timezone-aware if it's naive
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) > deadline:
            return jsonify({'error': 'Questionnaire has expired'}), 410
        
        # Get BFV parameters
        params = BFVParameters(
            poly_degree=questionnaire.poly_degree,
            plain_modulus=questionnaire.plain_modulus,
            ciph_modulus=int(questionnaire.ciph_modulus)
        )
        
        evaluator = BFVEvaluator(params)
        
        # Deserialize incoming ciphertexts
        new_ciphertexts = [deserialize_ciphertext(ciph_data) for ciph_data in encrypted_answers]
        
        # Get existing accumulated responses
        accumulated = questionnaire.get_accumulated_responses()
        
        if accumulated is None:
            # First response - just store the ciphertexts
            accumulated = [serialize_ciphertext(ciph) for ciph in new_ciphertexts]
        else:
            # Add new ciphertexts to accumulated ones
            accumulated_ciphertexts = [deserialize_ciphertext(ciph_data) for ciph_data in accumulated]
            
            # Homomorphic addition for each question
            for i in range(len(new_ciphertexts)):
                accumulated_ciphertexts[i] = evaluator.add(accumulated_ciphertexts[i], new_ciphertexts[i])
            
            # Serialize back
            accumulated = [serialize_ciphertext(ciph) for ciph in accumulated_ciphertexts]
        
        # Update questionnaire
        questionnaire.set_accumulated_responses(accumulated)
        questionnaire.num_responses += 1
        
        # Create response record
        response = Response(questionnaire_id=questionnaire.id)
        session.add(response)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Answers submitted successfully',
            'total_responses': questionnaire.num_responses
        }), 200
        
    except Exception as e:
        session.rollback()
        print(f"Error submitting answers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/questionnaire/<string:link>/stats', methods=['GET'])
def get_stats(link):
    """
    Get basic statistics about a questionnaire (without decrypting).
    """
    session = get_session(DB_URL)
    
    try:
        questionnaire = session.query(Questionnaire).filter_by(link=link).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        # Make deadline timezone-aware if it's naive
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        return jsonify({
            'link': questionnaire.link,
            'num_responses': questionnaire.num_responses,
            'deadline': questionnaire.deadline.isoformat(),
            'created_at': questionnaire.created_at.isoformat(),
            'is_expired': datetime.now(timezone.utc) > deadline
        }), 200
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()}), 200


@app.route('/api/questionnaires', methods=['GET'])
def list_questionnaires():
    """
    Get list of all questionnaires with basic info.
    """
    session = get_session(DB_URL)
    
    try:
        questionnaires = session.query(Questionnaire).order_by(Questionnaire.created_at.desc()).all()
        
        result = []
        for q in questionnaires:
            # Make deadline timezone-aware if it's naive
            deadline = q.deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            
            result.append({
                'id': q.id,
                'link': q.link,
                'created_at': q.created_at.isoformat(),
                'deadline': deadline.isoformat(),
                'num_responses': q.num_responses,
                'num_questions': len(q.get_questions()),
                'is_expired': datetime.now(timezone.utc) > deadline
            })
        
        return jsonify({'questionnaires': result}), 200
        
    except Exception as e:
        print(f"Error listing questionnaires: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/create-questionnaire', methods=['POST'])
def create_questionnaire_api():
    """
    Create a new questionnaire via API.
    
    Expected JSON:
    {
        'questions': [{'text': '...', 'options': [...]}],
        'deadline_datetime': '2025-12-31T23:59',
        'link': 'optional-custom-link'
    }
    """
    from bfv.bfv_key_generator import BFVKeyGenerator
    from util.secret_key import SecretKey
    import secrets as secrets_module
    
    session = get_session(DB_URL)
    
    try:
        data = request.get_json()
        
        questions = data.get('questions')
        deadline_datetime = data.get('deadline_datetime')
        custom_link = data.get('link')
        
        if not questions or len(questions) == 0:
            return jsonify({'error': 'No questions provided'}), 400
        
        if not deadline_datetime:
            return jsonify({'error': 'deadline_datetime is required'}), 400
        
        # Validate questions
        for i, q in enumerate(questions):
            if 'text' not in q or 'options' not in q:
                return jsonify({'error': f'Question {i+1} missing text or options'}), 400
            if len(q['options']) != 8:
                return jsonify({'error': f'Question {i+1} must have exactly 8 options'}), 400
        
        # Generate unique link if not provided
        if custom_link:
            # Check if link already exists
            existing = session.query(Questionnaire).filter_by(link=custom_link).first()
            if existing:
                return jsonify({'error': 'Link already exists'}), 400
            link = custom_link
        else:
            link = secrets_module.token_urlsafe(16)
        
        # Parse deadline datetime
        try:
            # The datetime comes as 'YYYY-MM-DDTHH:MM' from datetime-local input
            deadline = datetime.fromisoformat(deadline_datetime)
            # Make it timezone-aware (assume local time, convert to UTC)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            
            # Validate deadline is in the future
            if deadline <= datetime.now(timezone.utc):
                return jsonify({'error': 'Deadline must be in the future'}), 400
        except ValueError as e:
            return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
        
        # BFV Parameters
        degree = 8
        plain_modulus = 17
        ciph_modulus = 8000000000000
        
        params = BFVParameters(
            poly_degree=degree,
            plain_modulus=plain_modulus,
            ciph_modulus=ciph_modulus
        )
        
        # Generate keys
        key_generator = BFVKeyGenerator(params)
        public_key = key_generator.public_key
        secret_key = key_generator.secret_key
        
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
        
        return jsonify({
            'success': True,
            'link': link,
            'deadline': deadline.isoformat(),
            'url': f'/questionnaire.html?id={link}'
        }), 200
        
    except Exception as e:
        session.rollback()
        print(f"Error creating questionnaire: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/questionnaire/<string:link>/results', methods=['GET'])
def get_results(link):
    """
    Decrypt and return results from a questionnaire.
    Only works after deadline has passed.
    """
    from bfv.bfv_decryptor import BFVDecryptor
    from bfv.batch_encoder import BatchEncoder
    from util.secret_key import SecretKey
    
    session = get_session(DB_URL)
    
    try:
        questionnaire = session.query(Questionnaire).filter_by(link=link).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        # Make deadline timezone-aware if it's naive
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        # Check if questionnaire is still active (not expired)
        if datetime.now(timezone.utc) <= deadline:
            return jsonify({
                'error': 'Questionnaire is still active. Results will be available after the deadline.',
                'deadline': deadline.isoformat(),
                'is_active': True
            }), 403
        
        # Check if has responses
        if questionnaire.num_responses == 0:
            return jsonify({
                'error': 'No responses yet',
                'num_responses': 0
            }), 404
        
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
            return jsonify({'error': 'No accumulated responses found'}), 404
        
        # Decrypt and format results
        results = []
        for i, (question, ciph_data) in enumerate(zip(questions, accumulated)):
            # Deserialize and decrypt
            ciphertext = deserialize_ciphertext(ciph_data)
            plaintext = decryptor.decrypt(ciphertext)
            decoded = encoder.decode(plaintext)
            
            # Filter out N/A options with 0 votes
            options_results = []
            for j, option in enumerate(question['options']):
                votes = int(decoded[j])
                
                # Skip N/A options completely
                if option.strip().upper() == 'N/A':
                    continue
                
                percentage = (votes / questionnaire.num_responses * 100) if questionnaire.num_responses > 0 else 0
                options_results.append({
                    'option': option,
                    'votes': votes,
                    'percentage': round(percentage, 2)
                })
            
            results.append({
                'question': question['text'],
                'results': options_results
            })
        
        # Make deadline timezone-aware if it's naive
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        return jsonify({
            'link': questionnaire.link,
            'created_at': questionnaire.created_at.isoformat(),
            'deadline': deadline.isoformat(),
            'num_responses': questionnaire.num_responses,
            'is_expired': datetime.now(timezone.utc) > deadline,
            'results': results
        }), 200
        
    except Exception as e:
        print(f"Error getting results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


if __name__ == '__main__':
    print("Starting Flask server...")
    print("Database URL:", DB_URL)
    print("Initializing database...")
    
    # Initialize database
    init_db(DB_URL)
    
    print("Server ready!")
    print("Access the application at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
