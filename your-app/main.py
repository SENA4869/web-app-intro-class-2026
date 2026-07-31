"""
PAYMENTアプリ バックエンド - 完成版
第8回: セキュリティの基礎 & 総仕上げ
"""

import sqlite3  # Python標準のデータベース（SQLite）を使うためのライブラリ
import uvicorn  # FastAPIアプリを動かすためのWebサーバー

from fastapi import FastAPI, HTTPException  # Webアプリ本体とエラー応答用
from fastapi.middleware.cors import CORSMiddleware  # ブラウザからのアクセスを許可する設定
from fastapi.staticfiles import StaticFiles  # HTML/CSS/JSなどのファイルを配信する機能
from pydantic import BaseModel, Field  # 受け取るデータの形をチェックする道具

# --- FastAPIアプリ ---
app = FastAPI(title="PAYMENT App")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- データベース設定 ---
DATABASE = "payment.db"


def init_db():
    """データベースとテーブルを初期化する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        payer TEXT NOT NULL,
        amount INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# --- Pydanticモデル ---
class PAYMENTCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)  
    payer: str = Field(min_length=1, max_length=50)   
    amount: int = Field(gt=0)                         


# --- APIエンドポイント ---

@app.get("/payments")
def get_payments():
    """PAYMENT一覧を取得する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, payer, amount FROM payments ORDER BY id")
    payments = cursor.fetchall()

    conn.close()

    return [
        {
            "id": payment[0], "title": payment[1], "payer": payment[2], "amount": payment[3]
        }
        for payment in payments
    ]


@app.post("/payments", status_code=201)
def create_payment(payment: PAYMENTCreate):
    """新しいPAYMENTを作成する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO payments (title, payer, amount) VALUES (?, ?, ?)",
        (payment.title, payment.payer, payment.amount)
    )

    conn.commit()
    id = cursor.lastrowid

    conn.close()

    return {
        "id": id, "title": payment.title, "payer": payment.payer, "amount": payment.amount
    }


@app.delete("/payments/{id}")
def delete_payment(id: int):
    """PAYMENTを削除する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM payments WHERE id = ?", (id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="PAYMENT not found")

    cursor.execute("DELETE FROM payments WHERE id = ?", (id,))
    conn.commit()

    conn.close()
    return {"message": "PAYMENT deleted", "id": id}


# --- 静的ファイル配信 ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# --- アプリ起動時にDBを初期化 ---
init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)