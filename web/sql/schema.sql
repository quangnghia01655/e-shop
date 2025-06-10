-- schema.sql: Cấu trúc và dữ liệu mẫu cho database
-- Copy toàn bộ nội dung từ ecommerce_schema_with_data.sql vào đây

-- Dữ liệu và cấu trúc cho website thương mại điện tử

-- Bảng người dùng
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- Họ và tên người dùng
    email TEXT UNIQUE NOT NULL, -- Địa chỉ email
    password TEXT NOT NULL, -- Mật khẩu đã mã hóa
    is_seller BOOLEAN DEFAULT 0, -- Trạng thái người bán (1: là người bán, 0: không phải)
    is_admin BOOLEAN DEFAULT 0 -- Trạng thái quản trị viên (1: là admin, 0: không phải)
);

-- Bảng người bán
CREATE TABLE sellers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- ID người dùng liên kết
    shop_name TEXT NOT NULL, -- Tên cửa hàng
    phone TEXT, -- Số điện thoại
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng danh mục sản phẩm
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- Tên danh mục
);

-- Bảng sản phẩm
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- Tên sản phẩm
    price REAL NOT NULL, -- Giá sản phẩm
    image_url TEXT, -- URL hình ảnh sản phẩm
    description TEXT, -- Mô tả sản phẩm
    category_id INTEGER, -- ID danh mục
    seller_id INTEGER, -- ID người bán
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (seller_id) REFERENCES sellers(id)
);

-- Bảng giỏ hàng
CREATE TABLE carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- ID người dùng
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Thời gian tạo
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng mặt hàng trong giỏ hàng
CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL, -- ID giỏ hàng
    product_id INTEGER NOT NULL, -- ID sản phẩm
    quantity INTEGER DEFAULT 1, -- Số lượng
    FOREIGN KEY (cart_id) REFERENCES carts(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Bảng đơn hàng
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- ID người dùng
    total_amount REAL NOT NULL, -- Tổng số tiền
    status TEXT DEFAULT 'pending', -- Trạng thái đơn hàng (pending, completed, cancelled)
    payment_method TEXT, -- Phương thức thanh toán
    shipping_address TEXT, -- Địa chỉ giao hàng
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Thời gian tạo
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng mặt hàng trong đơn hàng
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL, -- ID đơn hàng
    product_id INTEGER NOT NULL, -- ID sản phẩm
    quantity INTEGER NOT NULL, -- Số lượng
    price REAL NOT NULL, -- Giá tại thời điểm đặt
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Bảng thông báo người dùng
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- View đếm tổng số lượng đã bán của từng sản phẩm
CREATE VIEW IF NOT EXISTS product_sales_count AS
SELECT 
    p.id AS product_id,
    p.name AS product_name,
    SUM(oi.quantity) AS total_sold
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name;

-- Dữ liệu mẫu cho bảng người dùng
INSERT INTO users (name, email, password, is_seller) VALUES
('Quản Trị Viên', 'admin@black.com', 'hashed_password_placeholder', 1),
('Người Mua Thử', 'buyer@black.com', 'hashed_password_placeholder', 0);

-- Dữ liệu mẫu cho bảng người bán
INSERT INTO sellers (user_id, shop_name, phone) VALUES
(1, 'Cửa Hàng Quản Trị', '0123456789');

-- Dữ liệu mẫu cho bảng danh mục
INSERT OR IGNORE INTO categories (name) VALUES
('Thời trang'),
('Mỹ phẩm'),
('Thể thao'),
('Đồ gia dụng'),
('Sách'),
('Điện tử'),
('Mẹ và Bé'),
('Đồ dùng học tập');

-- Dữ liệu mẫu cho bảng sản phẩm
INSERT INTO products (name, price, image_url, description, category_id, seller_id) VALUES
('Len Milk Cotton 50g', 9000, 'https://down-vn.img.susercontent.com/file/vn-11134201-7r98o-lq00szybju47c4.webp', 'Len Milk Cotton 50g mềm mại, phù hợp để đan áo len, khăn choàng.', 1, 1),
('Len Milk Bò 50g', 8000, 'https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lzoi1sk7ozvl0b@resize_w900_nl.webp', 'Len Milk Bò 50g với độ bền cao, màu sắc tươi sáng.', 1, 1),
('Phấn Nền Carslan Soft Mist', 246560, 'https://down-vn.img.susercontent.com/file/cn-11134207-7ras8-m1zcphdc86do71@resize_w900_nl.webp', 'Phấn nền kiểm dầu Carslan Soft Mist 24h.', 2, 1),
('Smoothie Tẩy Tế Bào Chết Dove', 139000, 'https://down-vn.img.susercontent.com/file/vn-11134207-7ra0g-m9s6d94kjqzy0f_tn', 'Tẩy tế bào chết Body Dove giúp da sáng mịn.', 2, 1),
('Giày Chạy Bộ Adidas', 1200000, 'https://down-vn.img.susercontent.com/file/sg-11134201-7repk-m8d799gvych35c.webp', 'Giày chạy bộ Adidas chuyên nghiệp.', 3, 1),
('Bóng Rổ Spalding', 300000, 'https://www.shutterstock.com/image-vector/simple-sports-equipment-sticker-single-600w-2357166703.jpg', 'Bóng rổ Spalding chất lượng cao.', 3, 1),
('Nước Giặt Joykity Lavender', 288500, 'https://down-vn.img.susercontent.com/file/vn-11134258-7ra0g-m9o6vh861tsqdb', 'Nước giặt Joykity hương lavender dịu nhẹ.', 4, 1),
('Sách Self-Help', 150000, 'https://thumbs.dreamstime.com/b/simple-book-sticker-logo-white-background-simple-book-sticker-logo-129305111.jpg', 'Sách self-help giúp phát triển bản thân.', 5, 1),
('Bàn Phím Cơ AULA WIN68', 435000, 'https://down-vn.img.susercontent.com/file/vn-11134207-7ras8-m4u5m87em4s84e.webp', 'Bàn phím cơ AULA WIN68, Led RGB.', 6, 1),
('Quạt Mini GOOJODQ', 276600, 'https://down-vn.img.susercontent.com/file/cn-11134207-7ras8-m8zn1jzagnw231.webp', 'Quạt mini GOOJODQ với tốc độ cao.', 6, 1),
('Sữa Enfagrow A+ Neuropro 4', 1068000, 'https://down-vn.img.susercontent.com/file/vn-11134207-7ra0g-m9tjq2suj2u23c@resize_w900_nl.webp', 'Sữa hỗ trợ phát triển trí não cho trẻ.', 7, 1),
('Bút Chì Cao Cấp', 10000, 'https://png.pngtree.com/png-vector/20240628/ourmid/pngtree-crayons-sticker-cartoon-style-with-pencils-ruler-bold-outline-png-image_12735710.png', 'Bút chì cao cấp cho học sinh.', 8, 1),
('Áo Thun Nam Cotton', 150000, 'https://example.com/ao-thun-nam.jpg', 'Áo thun nam chất liệu cotton thoáng mát.', 1, 1),
('Sữa Rửa Mặt Hàn Quốc', 120000, 'https://example.com/sua-rua-mat.jpg', 'Sữa rửa mặt dịu nhẹ nhập khẩu Hàn Quốc.', 2, 1),
('Giày Thể Thao Nữ', 350000, 'https://example.com/giay-nu.jpg', 'Giày thể thao nữ phong cách trẻ trung.', 3, 1),
('Bình Nước Giữ Nhiệt', 90000, 'https://example.com/binh-giu-nhiet.jpg', 'Bình nước giữ nhiệt inox cao cấp.', 4, 1),
('Sách Luyện Thi Đại Học', 200000, 'https://example.com/sach-luyen-thi.jpg', 'Sách luyện thi đại học môn Toán.', 5, 1);

-- Dữ liệu mẫu cho bảng giỏ hàng
INSERT INTO carts (user_id, created_at) VALUES
(2, '2025-05-30 10:00:00'); -- Giỏ hàng của Người Mua Thử

-- Dữ liệu mẫu cho bảng mặt hàng trong giỏ hàng
INSERT INTO cart_items (cart_id, product_id, quantity) VALUES
(1, 1, 2), -- 2 Len Milk Cotton 50g
(1, 3, 1); -- 1 Phấn Nền Carslan Soft Mist

-- Dữ liệu mẫu cho bảng đơn hàng
INSERT INTO orders (user_id, total_amount, status, payment_method, shipping_address, created_at) VALUES
(2, 255560, 'pending', 'cod', '123 Đường Lê Lợi, Quận 1, TP. Hồ Chí Minh', '2025-05-29 15:30:00'),
(2, 1500000, 'completed', 'bank_transfer', '456 Đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh', '2025-05-28 09:00:00');

-- Dữ liệu mẫu cho bảng mặt hàng trong đơn hàng
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 9000), -- Len Milk Cotton 50g
(1, 3, 1, 246560), -- Phấn Nền Carslan Soft Mist
(2, 5, 1, 1200000), -- Giày Chạy Bộ Adidas
(2, 6, 1, 300000); -- Bóng Rổ Spalding
