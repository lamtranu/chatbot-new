import csv
from pymongo import MongoClient
from bson import ObjectId

# Hàm chuyển ObjectId thành chuỗi
def mongo_to_dict(obj):
    if isinstance(obj, ObjectId):
        return str(obj)  # Chuyển ObjectId thành chuỗi
    elif isinstance(obj, dict):
        return {key: mongo_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [mongo_to_dict(item) for item in obj]
    else:
        return obj

# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Market_Student"]
collection = db["faqs"]

# Lấy tất cả bài viết faq
faqs_data = list(collection.find())

# Chuyển đổi dữ liệu thành dạng dễ sử dụng
formatted_data = []
for faq in faqs_data:
    if(faq.get("status") == "active"):
        faq_info = {
            "faq_id": mongo_to_dict(faq.get("_id")),  # Chuyển ObjectId thành chuỗi
            "question": faq.get("question"),
            "answer": faq.get("answer"), 
        }
        formatted_data.append(faq_info)

# Lưu dữ liệu vào file CSV
csv_file_path = 'D:/DATN/LLM/data_extract/faqs_data.csv'

# Đảm bảo file CSV được ghi đúng định dạng
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(file, fieldnames=["faq_id", "question", "answer"])
    writer.writeheader()  # Ghi tiêu đề cột
    writer.writerows(formatted_data)  # Ghi dữ liệu

print(f"Dữ liệu đã faq được xuất thành công ra file {csv_file_path}")
