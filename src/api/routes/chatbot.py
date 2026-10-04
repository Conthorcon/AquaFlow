from flask import Blueprint, request, jsonify
from src.chatbot.src.txt2sql import generate_sql

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    """
    API để nhận câu hỏi từ frontend và trả về phản hồi từ hệ thống RAG/SQL Agent Langchain.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400
        
    user_message = data['message']
    
    # Process with Langchain agent
    bot_response = generate_sql(user_message)

    if bot_response == "OUT_OF_SCOPE":
        bot_response = "Xin lỗi, tôi không thể trả lời câu hỏi này."
    
    return jsonify({
        "response": bot_response
    }), 200
