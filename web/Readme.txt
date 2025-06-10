# Hướng dẫn chạy dự án E-Shop

## 1. Cài đặt môi trường
- Cài Python >= 3.8
- Cài các thư viện cần thiết:
  ```
  pip install -r requirements.txt
  ```

## 2. Khởi tạo database
- Đảm bảo file `sql/schema.sql` đã có dữ liệu mẫu.
- Chạy script khởi tạo database:
  ```
  python -m models.init_db
  ```
  (Script sẽ đọc file SQL từ `sql/schema.sql` và tạo file database tại `instance/ecommerce.db`)

## 3. Chạy ứng dụng Flask
- Chạy app bằng lệnh:
  ```
  python -m controllers.app
  ```
- Truy cập: http://127.0.0.1:5000

## 4. Cấu trúc thư mục
- `controllers/app.py`: code Flask chính
- `models/models.py`: các model SQLAlchemy
- `models/init_db.py`: script khởi tạo database
- `sql/schema.sql`: file SQL tạo bảng và dữ liệu mẫu
- `views/`: chứa các file template (thay cho templates/)
- `instance/ecommerce.db`: file database SQLite

## 5. Lưu ý
- Khi muốn reset database, xóa file `instance/ecommerce.db` rồi chạy lại bước 2.
- Khi đăng ký tài khoản, email phải hợp lệ (có ký tự `@`).


