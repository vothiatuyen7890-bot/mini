#!/bin/bash

# Đặt tên file backup theo ngày giờ
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
DB_FILE="instance/site.db" # <--- ĐÃ SỬA: Chỉ đường dẫn đến file DB
BACKUP_DIR="backups"

# --- 1. Tạo thư mục backups nếu chưa tồn tại ---
mkdir -p $BACKUP_DIR

# --- 2. Sao chép file DB vào thư mục backups ---
# Lệnh này sẽ sao chép file từ 'instance/site.db' vào 'backups/backup_xxxx.db'
cp $DB_FILE $BACKUP_DIR/$BACKUP_FILE

echo "Database $DB_FILE đã được sao lưu thành $BACKUP_DIR/$BACKUP_FILE"

# --- 3. Giữ lại 5 bản sao lưu gần nhất (Tùy chọn dọn dẹp) ---
# Lệnh ls -t sắp xếp theo thời gian mới nhất
ls -t $BACKUP_DIR/*.db | awk 'NR>5' | xargs rm -f

# Quan trọng: Cấp quyền thực thi cho script (không cần thiết khi chạy bằng 'bash' nhưng vẫn nên giữ)
chmod +x $0