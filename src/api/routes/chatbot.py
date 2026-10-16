from flask import Blueprint, request, jsonify
from utils.ai_client import ask_ai, AIServiceError

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    """
    API để nhận câu hỏi từ frontend và trả về phản hồi từ hệ thống RAG/SQL Agent Langchain.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('message'), str) or not data['message'].strip() or len(data['message']) > 8000:
        return jsonify({"error": "No message provided"}), 400
        
    user_message = data['message']
    
    # Process with Langchain agent
    try:
        bot_response = ask_ai(user_message)
    except AIServiceError as exc:
        return jsonify(error=str(exc)), exc.status_code

    if bot_response == "OUT_OF_SCOPE":
        bot_response = "Xin lỗi, tôi không thể trả lời câu hỏi này."
    
    return jsonify({
        "response": bot_response
    }), 200
