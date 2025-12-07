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
import ssl

from models import init_db, get_session, Questionnaire, SubmissionRecord
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_parameters import BFVParameters
from bfv.bfv_decryptor import BFVDecryptor
from bfv.batch_encoder import BatchEncoder
from util.ciphertext import Ciphertext
from util.polynomial import Polynomial
from util.secret_key import SecretKey
import threading
import time

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


def decrypt_questionnaire(questionnaire):
    """Decrypt accumulated responses for a questionnaire."""
    try:
        # Check if already decrypted
        if questionnaire.is_decrypted:
            print(f"Questionnaire {questionnaire.link} already decrypted")
            return True
        
        # Check if has responses
        if questionnaire.num_responses == 0:
            print(f"Questionnaire {questionnaire.link} has no responses to decrypt")
            return False
        
        print(f"Decrypting questionnaire {questionnaire.link}...")
        
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
            print(f"Questionnaire {questionnaire.link} has no accumulated responses")
            return False
        
        # Decrypt and format results
        results = []
        print(f"\n{'='*40}")
        print(f"🔓 DESCIFRANDO RESULTADOS")
        print(f"{'='*40}")
        
        for i, (question, ciph_data) in enumerate(zip(questions, accumulated)):
            print(f"\n--- Pregunta {i+1}: {question['text']} ---")
            
            # Deserialize and decrypt
            ciphertext = deserialize_ciphertext(ciph_data)
            print(f"Ciphertext: c0.ring_degree={ciphertext.c0.ring_degree}")
            
            plaintext = decryptor.decrypt(ciphertext)
            print(f"Plaintext descifrado (coeffs): {plaintext.poly.coeffs}")
            
            decoded = encoder.decode(plaintext)
            print(f"Valores decodificados: {decoded}")
            
            # Filter out N/A options
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
            
            print(f"Resultados finales pregunta {i+1}:")
            for opt_result in options_results:
                print(f"  {opt_result['option']}: {opt_result['votes']} votos ({opt_result['percentage']}%)")
        
        # Store decrypted results
        questionnaire.set_decrypted_results(results)
        
        print(f"\n{'='*40}")
        print(f"✓ Questionnaire {questionnaire.link} decrypted successfully")
        print(f"{'='*40}\n")
        return True
        
    except Exception as e:
        print(f"✗ Error decrypting questionnaire {questionnaire.link}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_expired_questionnaires():
    """Background task to check and decrypt expired questionnaires."""
    print("\n🔍 Starting automatic decryption service...")
    
    while True:
        try:
            time.sleep(60)  # Check every 60 seconds
            
            session = get_session(DB_URL)
            
            try:
                # Find expired questionnaires that haven't been decrypted yet
                now = datetime.now(timezone.utc)
                questionnaires = session.query(Questionnaire).filter(
                    Questionnaire.is_decrypted == 0,
                    Questionnaire.num_responses > 0
                ).all()
                
                for q in questionnaires:
                    # Make deadline timezone-aware if needed
                    deadline = q.deadline
                    if deadline.tzinfo is None:
                        deadline = deadline.replace(tzinfo=timezone.utc)
                    
                    # Check if expired
                    if now > deadline:
                        print(f"\n⏰ Questionnaire {q.link} has expired. Decrypting...")
                        
                        if decrypt_questionnaire(q):
                            session.commit()
                            print(f"✓ Results saved to database for {q.link}")
                        else:
                            session.rollback()
                
            except Exception as e:
                print(f"Error in expiration check: {e}")
                session.rollback()
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error in background task: {e}")
            time.sleep(60)


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('../Frontend/dist', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from Frontend directory."""
    try:
        return send_from_directory('../Frontend/dist', filename)
    except:
        return send_from_directory('../Frontend/dist', 'index.html')


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
        
        # Return deadline in ISO format with Z to indicate UTC
        deadline_iso = deadline.isoformat()
        if not deadline_iso.endswith('Z') and not '+' in deadline_iso:
            deadline_iso += 'Z'

        response_data = {
            'id': questionnaire.id,
            'link': questionnaire.link,
            'deadline': deadline_iso,
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


@app.route('/api/cert-info', methods=['GET'])
def get_cert_info():
    peercert = request.environ.get('peercert')
    fingerprint = request.environ.get('peercert_fingerprint')
    if not peercert or not fingerprint:
        return jsonify({'error': 'No client certificate'}), 401
    cn = dict(x[0] for x in peercert.get('subject', ()))['commonName']
    return jsonify({'fingerprint': fingerprint, 'cn': cn}), 200


@app.route('/api/submit-answers', methods=['POST'])
def submit_answers():
    session = get_session(DB_URL)
    
    try:
        data = request.get_json()
        
        questionnaire_id = data.get('questionnaire_id')
        encrypted_answers = data.get('encrypted_answers')

        cert_fingerprint = request.environ.get('peercert_fingerprint')
        if not cert_fingerprint:
            return jsonify({'error': 'Client certificate required'}), 401


        if not questionnaire_id or not encrypted_answers:
            return jsonify({'error': 'Missing required fields'}), 400
        
        questionnaire = session.query(Questionnaire).filter_by(link=questionnaire_id).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) > deadline:
            return jsonify({'error': 'Questionnaire has expired'}), 410
        
        existing = session.query(SubmissionRecord).filter_by(
            questionnaire_id=questionnaire.id,
            cert_fingerprint=cert_fingerprint
        ).first()
        if existing:
            return jsonify({'error': 'Already submitted'}), 409

        params = BFVParameters(
            poly_degree=questionnaire.poly_degree,
            plain_modulus=questionnaire.plain_modulus,
            ciph_modulus=int(questionnaire.ciph_modulus)
        )
        
        evaluator = BFVEvaluator(params)
        new_ciphertexts = [deserialize_ciphertext(ciph_data) for ciph_data in encrypted_answers]
        
        accumulated = questionnaire.get_accumulated_responses()
        
        if accumulated is None:
            accumulated = [serialize_ciphertext(ciph) for ciph in new_ciphertexts]
        else:
            accumulated_ciphertexts = [deserialize_ciphertext(ciph_data) for ciph_data in accumulated]
            for i in range(len(new_ciphertexts)):
                accumulated_ciphertexts[i] = evaluator.add(accumulated_ciphertexts[i], new_ciphertexts[i])
            accumulated = [serialize_ciphertext(ciph) for ciph in accumulated_ciphertexts]

        questionnaire.set_accumulated_responses(accumulated)
        questionnaire.num_responses += 1
        
        submission_record = SubmissionRecord(
            questionnaire_id=questionnaire.id,
            cert_fingerprint=cert_fingerprint
        )
        session.add(submission_record)

        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Answers submitted successfully',
            'total_responses': questionnaire.num_responses
        }), 200

    except Exception as e:
        session.rollback()
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
        hide_results_until_deadline = data.get('hide_results_until_deadline', True)

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
            num_responses=0,
            hide_results_until_deadline=hide_results_until_deadline
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
    Return decrypted results from a questionnaire.
    """
    session = get_session(DB_URL)
    
    try:
        questionnaire = session.query(Questionnaire).filter_by(link=link).first()
        
        if not questionnaire:
            return jsonify({'error': 'Questionnaire not found'}), 404
        
        deadline = questionnaire.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        is_expired = datetime.now(timezone.utc) > deadline

        if questionnaire.hide_results_until_deadline and not is_expired:
            return jsonify({
                'error': 'Results are hidden until the deadline',
                'deadline': deadline.isoformat()
            }), 403

        if questionnaire.num_responses == 0:
            return jsonify({
                'error': 'No responses yet',
                'num_responses': 0
            }), 404
        
        questionnaire.is_decrypted = False
        if decrypt_questionnaire(questionnaire):
            session.commit()
        else:
            return jsonify({
                'error': 'Failed to decrypt results',
            }), 500

        results = questionnaire.get_decrypted_results()
        
        if not results:
            return jsonify({'error': 'Results not available'}), 404

        return jsonify({
            'link': questionnaire.link,
            'created_at': questionnaire.created_at.isoformat(),
            'deadline': deadline.isoformat(),
            'num_responses': questionnaire.num_responses,
            'is_expired': is_expired,
            'results': results
        }), 200
        
    except Exception as e:
        print(f"Error getting results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


def get_client_cert_fingerprint():
    cert_pem = request.environ.get('SSL_CLIENT_CERT', '')
    if not cert_pem:
        return None
    import hashlib
    from OpenSSL import crypto
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem)
    fingerprint = cert.digest('sha256').decode().replace(':', '').lower()
    return fingerprint


if __name__ == '__main__':
    print("Starting Flask server with mTLS...")
    print("Database URL:", DB_URL)

    init_db(DB_URL)
    
    decryption_thread = threading.Thread(target=check_expired_questionnaires, daemon=True)
    decryption_thread.start()
    print("✓ Automatic decryption service started")
    
    from werkzeug.serving import run_simple

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain('certs/server.crt', 'certs/server.key')
    context.load_verify_locations('certs/ca.crt')

    class PeerCertWSGIRequestHandler:
        def __init__(self, app):
            self.app = app
        def __call__(self, environ, start_response):
            sock = environ.get('werkzeug.socket') or environ.get('gunicorn.socket')
            if sock:
                cert = sock.getpeercert(binary_form=True)
                if cert:
                    import hashlib
                    environ['peercert_fingerprint'] = hashlib.sha256(cert).hexdigest()
                    environ['peercert'] = sock.getpeercert()
            return self.app(environ, start_response)

    wrapped_app = PeerCertWSGIRequestHandler(app)

    print("Server ready!")
    print("Access the application at: https://localhost:5000")

    run_simple('0.0.0.0', 5000, wrapped_app, ssl_context=context, use_reloader=False, use_debugger=True, threaded=True)
