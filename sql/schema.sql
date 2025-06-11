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
    total_purchased INTEGER DEFAULT 0, -- Số lượng đã mua/thêm vào giỏ
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
-- Danh mục Thời trang (1)
('Áo Thun Nam Cotton Cao Cấp', 150000, 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', 'Áo thun nam chất liệu cotton 100% thoáng mát, form dáng chuẩn Hàn Quốc, phù hợp mọi hoạt động hàng ngày.', 1, 1),
('Quần Jeans Nam Slim Fit', 450000, 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400', 'Quần jeans nam form slim fit, chất liệu denim cao cấp, bền đẹp và thời trang.', 1, 1),
('Áo Sơ Mi Nữ Công Sở', 280000, 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400', 'Áo sơ mi nữ thiết kế thanh lịch, phù hợp cho môi trường công sở và các buổi gặp gỡ quan trọng.', 1, 1),
('Váy Đầm Nữ Dự Tiệc', 680000, 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400', 'Váy đầm nữ thiết kế sang trọng, phù hợp cho các buổi tiệc tùng và sự kiện đặc biệt.', 1, 1),
('Áo Khoác Nam Thể Thao', 320000, 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400', 'Áo khoác nam thể thao chống gió, chống nước, thiết kế năng động và trẻ trung.', 1, 1),
('Chân Váy Nữ Xòe Vintage', 220000, 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400', 'Chân váy xòe phong cách vintage, chất liệu nhẹ nhàng, tôn dáng người mặc.', 1, 1),

-- Danh mục Mỹ phẩm (2)
('Kem Dưỡng Da Mặt Nhật Bản', 280000, 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=400', 'Kem dưỡng da mặt nhập khẩu Nhật Bản, chứa vitamin E và collagen giúp da mềm mịn tự nhiên.', 2, 1),
('Son Môi Lì Cao Cấp', 185000, 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400', 'Son môi lì màu đỏ cam tự nhiên, lâu trôi và không gây khô môi, phù hợp mọi loại da.', 2, 1),
('Phấn Phủ Kiểm Dầu Hàn Quốc', 220000, 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400', 'Phấn phủ kiểm dầu hiệu quả lên đến 12 giờ, cho lớp nền hoàn hảo và tự nhiên.', 2, 1),
('Sữa Rửa Mặt Trà Xanh', 95000, 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400', 'Sữa rửa mặt chiết xuất trà xanh, làm sạch sâu và kiểm soát dầu thừa hiệu quả.', 2, 1),
('Mascara Chuốt Mi Chống Nước', 160000, 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400', 'Mascara chống nước, giúp mi dài và cong tự nhiên, không lem không trôi suốt ngày dài.', 2, 1),
('Kem Chống Nắng SPF 50+', 150000, 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=400', 'Kem chống nắng SPF 50+ bảo vệ da toàn diện, không gây nhờn rít, phù hợp mọi loại da.', 2, 1),

-- Danh mục Thể thao (3)
('Giày Chạy Bộ Nike Air', 1850000, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', 'Giày chạy bộ Nike Air với công nghệ đệm khí tiên tiến, mang lại cảm giác êm ái và thoải mái.', 3, 1),
('Áo Thể Thao Nam Dry-Fit', 180000, 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400', 'Áo thể thao nam công nghệ Dry-Fit, thấm hút mồ hôi nhanh và khô thoáng khi vận động.', 3, 1),
('Bóng Đá Molten Chính Hãng', 450000, 'https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400', 'Bóng đá Molten chính hãng size 5, chất liệu da PU cao cấp, độ bền và độ nảy chuẩn FIFA.', 3, 1),
('Găng Tay Tập Gym', 120000, 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400', 'Găng tay tập gym chất liệu da tổng hợp, chống trượt và bảo vệ tay khi tập luyện.', 3, 1),
('Dây Nhảy Thể Thao', 85000, 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400', 'Dây nhảy thể thao có đếm số, tay cầm chống trượt, phù hợp tập luyện cardio tại nhà.', 3, 1),
('Bình Nước Thể Thao 750ml', 95000, 'https://images.unsplash.com/photo-1523362628745-0c100150b504?w=400', 'Bình nước thể thao 750ml, chất liệu nhựa an toàn, thiết kế tiện lợi cho các hoạt động thể thao.', 3, 1),

-- Danh mục Đồ gia dụng (4)
('Nồi Cơm Điện Sharp 1.8L', 1250000, 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400', 'Nồi cơm điện Sharp 1.8L công nghệ Nhật Bản, nấu cơm ngon và tiết kiệm điện năng.', 4, 1),
('Máy Xay Sinh Tố Philips', 850000, 'https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=400', 'Máy xay sinh tố Philips công suất 600W, dao xay sắc bén, cối xay dung tích 1.5L.', 4, 1),
('Bộ Dao Inox Cao Cấp', 320000, 'https://images.unsplash.com/photo-1593618998160-e34014e67546?w=400', 'Bộ dao inox cao cấp 5 món, thép không gỉ sắc bén, tay cầm chống trượt an toàn.', 4, 1),
('Chảo Chống Dính 28cm', 280000, 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400', 'Chảo chống dính đường kính 28cm, lớp phủ Ceramic cao cấp, tay cầm chịu nhiệt.', 4, 1),
('Máy Lọc Nước RO 9 Cấp', 4500000, 'https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=400', 'Máy lọc nước RO 9 cấp lọc, công nghệ Mỹ, cho nguồn nước sạch và an toàn cho gia đình.', 4, 1),
('Lò Vi Sóng Electrolux 23L', 2100000, 'https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=400', 'Lò vi sóng Electrolux 23L, nhiều chế độ nấu, thiết kế hiện đại và tiết kiệm không gian.', 4, 1),

-- Danh mục Sách (5)
('Sách Đắc Nhân Tâm', 85000, 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400', 'Cuốn sách kinh điển về nghệ thuật giao tiếp và ứng xử của Dale Carnegie, bản dịch tiếng Việt.', 5, 1),
('Sách Tư Duy Nhanh Và Chậm', 120000, 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400', 'Tác phẩm của Daniel Kahneman về tâm lý học và kinh tế học hành vi, giúp hiểu cách con người ra quyết định.', 5, 1),
('Sách Lập Trình Python', 180000, 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400', 'Sách học lập trình Python từ cơ bản đến nâng cao, phù hợp cho người mới bắt đầu.', 5, 1),
('Sách Tiếng Anh Giao Tiếp', 95000, 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400', 'Sách học tiếng Anh giao tiếp hàng ngày với 1000 mẫu câu thông dụng nhất.', 5, 1),
('Sách Lịch Sử Việt Nam', 140000, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400', 'Sách lịch sử Việt Nam từ thời nguyên thủy đến hiện đại, được viết bởi các sử gia uy tín.', 5, 1),
('Sách Triết Học Phương Đông', 110000, 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400', 'Tìm hiểu về triết học phương Đông qua các tư tưởng của Khổng Tử, Lão Tử và Phật giáo.', 5, 1),

-- Danh mục Điện tử (6)
('iPhone 15 Pro Max 256GB', 32990000, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400', 'iPhone 15 Pro Max 256GB, chip A17 Pro, camera 48MP, màn hình Super Retina XDR 6.7 inch.', 6, 1),
('Laptop Dell XPS 13', 25990000, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400', 'Laptop Dell XPS 13 inch, Intel Core i7 Gen 12, RAM 16GB, SSD 512GB, màn hình 4K touch.', 6, 1),
('Tai Nghe Sony WH-1000XM5', 8500000, 'https://images.unsplash.com/photo-1545127398-14699f92334b?w=400', 'Tai nghe Sony WH-1000XM5 chống ồn chủ động, âm thanh Hi-Res, pin 30 giờ.', 6, 1),
('Apple Watch Series 9', 9990000, 'https://images.unsplash.com/photo-1551816230-ef5deaed4a26?w=400', 'Apple Watch Series 9 GPS, chip S9, màn hình Always-On Retina, theo dõi sức khỏe toàn diện.', 6, 1),
('iPad Air 256GB WiFi', 17990000, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', 'iPad Air 256GB WiFi, chip M1, màn hình 10.9 inch Liquid Retina, hỗ trợ Apple Pencil.', 6, 1),
('Samsung Galaxy S24 Ultra', 30990000, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400', 'Samsung Galaxy S24 Ultra 512GB, chip Snapdragon 8 Gen 3, camera 200MP, S Pen tích hợp.', 6, 1),

-- Danh mục Mẹ và Bé (7)
('Sữa Bột Enfamil A+ 900g', 580000, 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400', 'Sữa bột Enfamil A+ 900g cho trẻ 0-12 tháng, bổ sung DHA và ARA hỗ trợ phát triển não bộ.', 7, 1),
('Tã Quần Pampers Newborn', 320000, 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=400', 'Tã quần Pampers Newborn size S, siêu thấm hút, mềm mại và an toàn cho làn da nhạy cảm của bé.', 7, 1),
('Xe Đẩy Em Bé Cao Cấp', 2850000, 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400', 'Xe đẩy em bé cao cấp 3 tư thế, khung nhôm nhẹ, bánh xe chống sốc, an toàn tuyệt đối.', 7, 1),
('Bình Sữa Pigeon 240ml', 180000, 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400', 'Bình sữa Pigeon 240ml, chất liệu PP an toàn, núm ty silicone mềm mại như ti mẹ.', 7, 1),
('Ghế Ăn Dặm Cho Bé', 1250000, 'https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=400', 'Ghế ăn dặm cho bé từ 6 tháng tuổi, chất liệu gỗ tự nhiên, thiết kế an toàn và tiện lợi.', 7, 1),
('Đồ Chơi Xúc Xắc Gỗ', 95000, 'https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=400', 'Đồ chơi xúc xắc gỗ tự nhiên, màu sắc tươi sáng, kích thích giác quan và trí não của bé.', 7, 1),

-- Danh mục Đồ dùng học tập (8)
('Bộ Bút Chì Staedtler 12 Cây', 45000, 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400', 'Bộ bút chì Staedtler 12 cây độ cứng HB, chất lượng Đức, viết mượt và không gãy ngòi.', 8, 1),
('Thước Kẻ Inox 30cm', 25000, 'https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?w=400', 'Thước kẻ inox 30cm, vạch chia chính xác, bền bỉ và không bị rỉ sét theo thời gian.', 8, 1),
('Cặp Sách Học Sinh', 280000, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400', 'Cặp sách học sinh chống thấm nước, thiết kế ergonomic, nhiều ngăn tiện lợi.', 8, 1),
('Máy Tính Casio FX-580VN X', 580000, 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=400', 'Máy tính Casio FX-580VN X, 552 chức năng, hiển thị tự nhiên, pin sử dụng lâu dài.', 8, 1),
('Bộ Compass Vẽ Hình Học', 85000, 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400', 'Bộ compass vẽ hình học 8 món, chất liệu kim loại cao cấp, vẽ chính xác và bền đẹp.', 8, 1),
('Giấy A4 Double A 500 Tờ', 120000, 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=400', 'Giấy A4 Double A 500 tờ, độ trắng 90%, mịn màng và phù hợp cho mọi loại máy in.', 8, 1);

-- Dữ liệu mẫu cho bảng giỏ hàng
INSERT INTO carts (user_id, created_at) VALUES
(2, '2025-05-30 10:00:00'); -- Giỏ hàng của Người Mua Thử

-- Dữ liệu mẫu cho bảng mặt hàng trong giỏ hàng
INSERT INTO cart_items (cart_id, product_id, quantity) VALUES
(1, 1, 2), -- 2 Áo Thun Nam Cotton Cao Cấp
(1, 3, 1); -- 1 Áo Sơ Mi Nữ Công Sở

-- Dữ liệu mẫu cho bảng đơn hàng
INSERT INTO orders (user_id, total_amount, status, payment_method, shipping_address, created_at) VALUES
(2, 580000, 'pending', 'cod', '123 Đường Lê Lợi, Quận 1, Thành phố Hồ Chí Minh', '2025-05-29 15:30:00'),
(2, 2200000, 'completed', 'bank_transfer', '456 Đường Nguyễn Huệ, Quận 1, Thành phố Hồ Chí Minh', '2025-05-28 09:00:00');

-- Dữ liệu mẫu cho bảng mặt hàng trong đơn hàng
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 2, 150000), -- 2 Áo Thun Nam Cotton Cao Cấp
(1, 7, 1, 280000), -- 1 Kem Dưỡng Da Mặt Nhật Bản
(2, 13, 1, 1850000), -- 1 Giày Chạy Bộ Nike Air
(2, 15, 1, 450000); -- 1 Bóng Đá Molten Chính Hãng
