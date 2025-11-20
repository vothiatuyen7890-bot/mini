#!/bin/bash
# Đặt tên file backup theo ngày giờ
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
DB_FILE="site.db"
BACKUP_DIR="backups"

# Tạo thư mục backups nếu chưa tồn tại
mkdir -p $BACKUP_DIR

# Sao chép file DB
cp $DB_FILE $BACKUP_DIR/$BACKUP_FILE

echo "Database $DB_FILE đã được sao lưu thành $BACKUP_DIR/$BACKUP_FILE"

# Giữ lại 5 bản sao lưu gần nhất (tùy chọn)
ls -t $BACKUP_DIR/*.db | awk 'NR>5' | xargs rm -f