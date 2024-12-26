from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import os
import torch
from transformers import AutoTokenizer, AutoModel, pipeline, AutoModelForCausalLM, AutoTokenizer
import logging
import traceback
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import login  # Thêm import này
from poe_api_wrapper import AsyncPoeApi
import asyncio

tokens = {
    'p-b': 'UP0BVHX1gwILIgeTFYaMkA%3D%3D', 
    'p-lat': 'ESFGPES6yTdr%2FYgL3Bq5ai3pcZd%2B64NuT4tz3RbdSw%3D%3D',
}

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
app = Flask(__name__)

user_chat_history = {}

# model và tokenizer
model_path = "dangvantuan/vietnamese-embedding"
save_directory = "models/vietnamese_embedding"

# Tải model và tokenizer từ thư mục đã lưu (nếu có)
if os.path.exists(save_directory):
    tokenizer = AutoTokenizer.from_pretrained(save_directory)
    model = AutoModel.from_pretrained(save_directory)
else:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path)
    os.makedirs(save_directory, exist_ok=True)
    tokenizer.save_pretrained(save_directory)
    model.save_pretrained(save_directory)

model.eval()

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

#query chatbot
@app.route('/ask', methods=['POST'])
async def ask():
    print('request.json', request.json)
    user_query = request.json.get('query')
    user_id = request.json.get('user_id')
    chat_id = request.json.get('chatId')

    isNewChat = False

    if not user_query or not user_id:
        return jsonify({'error': 'Câu hỏi và ID người dùng không được để trống'}), 400

    logging.info(f"Received query: {user_query} from user: {user_id}")

    try:
        
        response = []

        response_text = ''

        #Create prompt
        prompt = (
            "<|im_start|>system\n"
            "Bạn là một trợ lý AI, bạn tên là ChatBotCSV hỗ trợ tìm kiếm sản phẩm và trả lời câu hỏi. Hãy trả lời dựa vào dữ liệu của tôi và các câu trả lời trước đó của bạn nếu có, bạn hạn chế trả lời câu hỏi ngoài dữ liệu của tôi nhé."
            "<|im_start|>user\n" + user_query + "\n"
            "<|im_start|>assistant\n"
        )
        
        print('response_text', response_text)

        client = await AsyncPoeApi(tokens=tokens).create()
        
        full_response = ""

        listData = [
            'data_extract/products_data_with_variants.csv',
            'data_extract/data_more.csv',
            'data_extract/faqs_data.csv',
        ]

        #haved chat
        if(chat_id != ''): 
            try: 
                async for chunk in client.send_message(bot="gpt4_o_mini", message=prompt, chatId=int(chat_id), file_path=listData):
                    full_response += chunk["response"]
            except Exception as e:
                print(f"Có lỗi xảy ra khi gửi tin nhắn: {e}, đã tạo lại hội thoại mới")
                async for chunk in client.send_message(bot="gpt4_o_mini", message=prompt):
                    full_response += chunk["response"]

                chat_id = chunk.get('chatId') 
                isNewChat = True
        #not
        else:
            async for chunk in client.send_message(bot="gpt4_o_mini", message=prompt, file_path=listData):
                full_response += chunk["response"]

            chat_id = chunk.get('chatId') 
            isNewChat = True

        return jsonify({'query': user_query, 'chatbot_response': full_response, 'userId': user_id, 'chatId': chat_id, 'isNewChat': isNewChat})

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500



#resummer
@app.route('/api/summarize', methods=['POST'])
async def summarize():
    data = request.json
    review = data.get('review', '')
    reviewId = data.get('reviewId', '')

    productId = data.get('productId', '')
    productVariantId = data.get('productVariantId', '')
    orderCode = data.get('orderCode', '')

    dataReSummarizeNegative = data.get('dataReSummarizeNegative', '')
    dataSummarizePositive = data.get('dataSummarizePositive', '')

    print('data', data)

    prompt = (
        "<|im_start|>system\n"
        "Bạn là một trợ lý AI. Tôi muốn bạn giúp tôi phân tích đánh giá sản phẩm của người dùng dưới đây.\n "
        "<|im_start|>user\n" + review + "\n"
        "<|im_start|>assistant\n"
        "Vui lòng chỉ ra đánh giá này là tốt hoặc tiêu cực, trả lời 'tích cực' hoặc 'tiêu cực'. \n"
        "Ví dụ: '- Đánh giá: Tiêu cực \n"
        "- Sau đó, bạn kết hợp các đánh giá tiêu cực khác: " + dataReSummarizeNegative + "\n"
        "- Và kết hợp đánh giá tích cực khác: " + dataSummarizePositive + "\n"
        "- Tôi muốn bạn đánh giá tổng quát gạch đầu dòng tích cực và tiêu cực như Tiki, phải kết hợp các đánh giá tiêu cực khác và đánh giá tích cực khác, không được phép ghi lại đánh giá của người dùng, đưa thêm xem đánh giá này là tích cực hay tiêu cực \n"
    )

    print('promp', prompt)

    client = await AsyncPoeApi(tokens=tokens).create()
    full_response = ""

    async for chunk in client.send_message(bot="capybara", message=prompt, chatId=int('782449387'), ):
        full_response += chunk["response"]

    return jsonify({"summary": full_response, 'productId': productId, 
    'reviewId': reviewId, 'productVariantId': productVariantId, 'orderCode': orderCode})

if __name__ == '__main__':
    app.run(debug=True)
