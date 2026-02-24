
import os
import shutil
import asyncio
from sqlalchemy import create_engine, MetaData
from minio import Minio
from dotenv import load_dotenv
import redis.asyncio as redis

# 加载环境变量
load_dotenv()

# --- 配置 ---
SQLITE_DB_PATH = "test.db"
CHROMA_PERSIST_DIR = "data/chroma"
REDIS_URL = f"redis://:{os.getenv('REDIS_PASSWORD', '')}@{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/{os.getenv('REDIS_DB', 0)}"

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "resume-images")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

def clean_sqlite():
    print(f"Cleaning SQLite Database ({SQLITE_DB_PATH})...")
    if os.path.exists(SQLITE_DB_PATH):
        try:
            os.remove(SQLITE_DB_PATH)
            print("SQLite database removed.")
        except Exception as e:
            print(f"Error removing SQLite database: {e}")
    else:
        print("SQLite database does not exist.")

def clean_chroma():
    print(f"Cleaning ChromaDB ({CHROMA_PERSIST_DIR})...")
    if os.path.exists(CHROMA_PERSIST_DIR):
        try:
            shutil.rmtree(CHROMA_PERSIST_DIR)
            print("ChromaDB data removed.")
        except Exception as e:
            print(f"Error removing ChromaDB data: {e}")
    else:
        print("ChromaDB directory does not exist.")

async def clean_redis():
    print(f"Cleaning Redis ({REDIS_URL})...")
    try:
        r = redis.from_url(REDIS_URL)
        await r.flushdb()
        await r.aclose()
        print("Redis flushed.")
    except Exception as e:
        print(f"Error flushing Redis: {e}")

def clean_minio():
    print(f"Cleaning MinIO Bucket ({MINIO_BUCKET} @ {MINIO_ENDPOINT})...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        
        if client.bucket_exists(MINIO_BUCKET):
            # 删除桶内所有对象
            objects = client.list_objects(MINIO_BUCKET, recursive=True)
            for obj in objects:
                client.remove_object(MINIO_BUCKET, obj.object_name)
                print(f"Removed object: {obj.object_name}")
            
            # 删除桶本身（可选，或者保留空桶）
            # client.remove_bucket(MINIO_BUCKET)
            print(f"Bucket '{MINIO_BUCKET}' cleaned.")
        else:
            print(f"Bucket '{MINIO_BUCKET}' does not exist.")
            
    except Exception as e:
        print(f"Error cleaning MinIO: {e}")

async def main():
    print("Starting data cleanup...")
    clean_sqlite()
    clean_chroma()
    await clean_redis()
    clean_minio()
    print("Data cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())
