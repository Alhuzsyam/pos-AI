#!/bin/bash
set -e

echo "Waiting for database..."
until python -c "
import pymysql, os, sys, time
host = os.environ.get('DB_HOST', 'db')
for i in range(30):
    try:
        conn = pymysql.connect(host=host, user=os.environ.get('DB_USER','root'), password=os.environ.get('DB_PASSWORD','password'), db=os.environ.get('DB_NAME','posai'))
        conn.close()
        print('DB ready!')
        sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1}/30: {e}')
        time.sleep(2)
sys.exit(1)
"; do
  sleep 1
done

echo "Running migrations..."
python -c "
from app.database import Base, engine
from app import models
Base.metadata.create_all(bind=engine)
print('Tables created.')
"

echo "Seeding superadmin..."
python -c "
import os
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

db = SessionLocal()
existing = db.query(User).filter(User.username == 'superadmin').first()
if not existing:
    superadmin = User(
        tenant_id=None,
        username='superadmin',
        full_name='Super Admin',
        email='admin@posai.com',
        password_hash=hash_password(os.environ.get('SUPERADMIN_PASSWORD', 'superadmin123')),
        role=UserRole.SUPERADMIN.value,
    )
    db.add(superadmin)
    db.commit()
    print('Superadmin created.')
else:
    print('Superadmin already exists.')
db.close()
"

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
