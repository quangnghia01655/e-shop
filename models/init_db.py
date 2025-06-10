# init_db.py - Khởi tạo database và dữ liệu mẫu cho app
import sqlite3
import os
from werkzeug.security import generate_password_hash

def init_db():
    # Define the instance folder path
    instance_path = os.path.join(os.getcwd(), 'instance')
    os.makedirs(instance_path, exist_ok=True)  # Create instance folder if it doesn't exist
    db_path = os.path.join(instance_path, 'ecommerce.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Đọc file schema.sql từ thư mục sql
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    # Update admin user password
    admin_password = 'admin123'
    hashed_password = generate_password_hash(admin_password, method='sha256')
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, 'admin@black.com'))

    # Update buyer user password
    buyer_password = 'buyer123'
    hashed_password = generate_password_hash(buyer_password, method='sha256')
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, 'buyer@black.com'))

    # Tạo tài khoản admin nếu chưa có
    cursor.execute("SELECT id FROM users WHERE email = ?", ('admin@black.com',))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (name, email, password, is_seller, is_admin) VALUES (?, ?, ?, ?, ?)",
                       ('Admin', 'admin@black.com', hashed_password, 0, 1))
    # Tạo tài khoản buyer nếu chưa có
    cursor.execute("SELECT id FROM users WHERE email = ?", ('buyer@black.com',))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (name, email, password, is_seller, is_admin) VALUES (?, ?, ?, ?, ?)",
                       ('Buyer', 'buyer@black.com', hashed_password, 0, 0))
    # Đảm bảo admin đúng quyền admin
    cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", ('admin@black.com',))
    cursor.execute("UPDATE users SET is_admin = 0 WHERE email = ?", ('buyer@black.com',))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
