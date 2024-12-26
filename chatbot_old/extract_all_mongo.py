import subprocess

# Đường dẫn đến thư mục lưu trữ xuất file
output_path = "D:/DATN/DB_Market_Student"

# Thông tin kết nối MongoDB
host = "127.0.0.1"  # Hoặc "localhost"
port = 27017        # Cổng mặc định của MongoDB
db_name = "Market_Student"  # Tên cơ sở dữ liệu bạn muốn xuất

# Lệnh mongodump
command = [
    "mongodump",
    "--host", host,
    "--port", str(port),
    "--db", db_name,
    "--out", output_path
]

# Thực thi lệnh mongodump
try:
    subprocess.run(command, check=True)
    print(f"Export database '{db_name}' to {output_path} successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error during export: {e}")
