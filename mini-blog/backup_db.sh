#!/bin/bash

# Đặt tên file backup theo ngày giờ
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
DB_FILE="site.db"
BACKUP_DIR="backups"

# --- 1. Tạo thư mục backups nếu chưa tồn tại ---
mkdir -p $BACKUP_DIR

# --- 2. Sao chép file DB vào thư mục backups ---
cp $DB_FILE $BACKUP_DIR/$BACKUP_FILE

echo "Database $DB_FILE đã được sao lưu thành $BACKUP_DIR/$BACKUP_FILE"

# --- 3. Giữ lại 5 bản sao lưu gần nhất (Tùy chọn dọn dẹp) ---
# Lệnh ls -t sắp xếp theo thời gian mới nhất
# awk 'NR>5' chọn ra những file từ dòng thứ 6 trở đi
# xargs rm -f xóa các file đó
ls -t $BACKUP_DIR/*.db | awk 'NR>5' | xargs rm -f

# Quan trọng: Cấp quyền thực thi cho script
chmod +x $0