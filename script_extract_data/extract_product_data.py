import csv
from pymongo import MongoClient
from bson import ObjectId

# Hàm chuyển ObjectId và các cấu trúc phức tạp thành chuỗi hoặc kiểu đơn giản
def mongo_to_dict(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: mongo_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [mongo_to_dict(item) for item in obj]
    return obj

# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Market_Student"]
products_collection = db["products"]
variants_collection = db["variantproducts"]
discounts_collection = db["discountproducts"]

# Lấy tất cả sản phẩm đã được phê duyệt (Approved)
products_data = products_collection.find({"status": "Approved"})

# Chuyển đổi dữ liệu sản phẩm sang định dạng mong muốn
formatted_data = []
for product in products_data:
    # Lấy và giới hạn mô tả sản phẩm (description)
    full_description = product.get("productDescription", "")  # Lấy mô tả, mặc định là chuỗi rỗng
    limited_description = " ".join(full_description.split()[:100])  # Giới hạn 100 từ đầu tiên
    product_info = {
        "product_id": mongo_to_dict(product.get("_id")),
        "name": product.get("productName"),
        "price": product.get("productPrice"),
        "quantity": product.get("productQuantity"),
        "sold_count": product.get("productSoldQuantity"),
        "description": limited_description,
        "variants": [],
        "product_discount": None  # Giảm giá cho sản phẩm gốc
    }

    # Lấy thông tin các biến thể
    has_valid_variants = False
    for variant_id in product.get("productVariants", []):
        variant = variants_collection.find_one({"_id": ObjectId(variant_id), "variantStatus": {"$ne": "Deleted"}})
        if variant and variant.get("variantStatus") == "Approved":
            has_valid_variants = True
            variant_info = {
                "variant_name": variant.get("variantName"),
                "variant_price": variant.get("variantPrice"),
                "variant_quantity": variant.get("variantQuantity"),
                "variant_sold_quantity": variant.get("variantSoldQuantity"),
                "variant_discounts": []
            }

            # Lấy thông tin giảm giá cho biến thể
            for discount_id in variant.get("variantDiscounts", []):
                discount = discounts_collection.find_one({"_id": ObjectId(discount_id), "discountStatus": True})
                if discount:
                    variant_info["variant_discounts"].append({
                        "discount_price": discount.get("discountPrices"),
                        "discount_quantity": discount.get("discountQuantitys"),
                    })

            product_info["variants"].append(variant_info)

    # Nếu không có biến thể hợp lệ, lấy thông tin giảm giá từ sản phẩm gốc
    if not has_valid_variants:
        for discount_id in product.get("productDiscounts", []):
            discount = discounts_collection.find_one({"_id": ObjectId(discount_id), "discountStatus": True})
            if discount:
                product_info["product_discount"] = {
                    "discount_price": discount.get("discountPrices"),
                    "discount_quantity": discount.get("discountQuantitys"),
                }

    formatted_data.append(product_info)

# Lưu dữ liệu vào file CSV
csv_file_path = 'D:/DATN/CHATBOT-NEW/data_extract/products_data_with_variants.csv'

#Ghi file CSV
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as file:
    # Ghi các cột vào CSV
    writer = csv.DictWriter(file, fieldnames=["product_id", "name", "price", "quantity", "sold_count", "description", "variants", "product_discount"])
    writer.writeheader()

    for data in formatted_data:
        data["variants"] = str(data["variants"])  # Chuyển danh sách variants thành chuỗi
        data["product_discount"] = str(data["product_discount"])  # Chuyển giảm giá thành chuỗi
        writer.writerow(data)

print(f"Dữ liệu đã được xuất thành công ra file {csv_file_path}")
