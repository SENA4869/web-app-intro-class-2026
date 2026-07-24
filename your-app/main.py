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
# このappが、Webアプリ全体の本体になる
app = FastAPI(title="PAYMENT App")

# CORS設定: 別のアドレスで動くフロント（ブラウザの画面）からの通信を許可する
# allow_origins=["*"] は「どこからのアクセスでもOK」という意味（学習用の設定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- データベース設定 ---
# データを保存するファイルの名前。アプリと同じフォルダに payment.db が作られる
DATABASE = "payment.db"


def init_db():
    """データベースとテーブルを初期化する"""
    conn = sqlite3.connect(DATABASE)  # データベースに接続する
    cursor = conn.cursor()  # SQLを実行する係（カーソル）を用意する
    # payments テーブルがまだ無ければ作る（IF NOT EXISTS）
    #   id    : 自動で増える番号（主キー）
    #   title : PAYMENTの内容（空はNG）
    #   finished  : 完了したかどうか（0=未完了, 1=完了）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        payer TEXT NOT NULL,
        amount INTEGER NOT NULL
        )
    """)
    conn.commit()  # 変更を確定して保存する
    conn.close()  # 接続を閉じる


# --- Pydanticモデル ---
# APIが受け取るデータの「形」を決めるクラス。
# 形に合わないデータが送られてきたら、FastAPIが自動でエラーを返してくれる。


class PAYMENTCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)  
    payer: str = Field(min_length=1, max_length=50)   
    amount: int = Field(gt=0)                         


class PAYMENTUpdate(BaseModel):
    # PAYMENTを更新するときに受け取るデータ
    # finished は True / False（完了したかどうか）
    finished: bool


# --- APIエンドポイント ---
# @app.get / @app.post などの飾り（デコレータ）で、
# 「どのURLに、どの種類のリクエストが来たら、この関数を動かすか」を決める。


@app.get("/payments")  # GET /payments にアクセスされたら実行
def get_payments():
    """PAYMENT一覧を取得する"""
    conn = sqlite3.connect(DATABASE)  # 接続する
    cursor = conn.cursor()

    # payments テーブルの全データを id 順に取り出す
    cursor.execute("SELECT id, title, payer, amount FROM payments ORDER BY id")
    payments = cursor.fetchall()  # 取り出した全行をリストで受け取る

    conn.close()  # 接続を閉じる

    # 1行は (id, title, payer, amount) の順のタプルなので、番号で取り出す。
    # 取り出したデータを、ブラウザに返しやすい辞書のリストに作り変える。
    return [
        {
            "id": payment[0],    "title": payment[1], "payer": payment[2], "amount": payment[3]
        }
        for payment in payments
    ]


@app.post("/payments", status_code=201)  # POST /payments で新規作成 (201=作成成功)
def create_payment(payment: PAYMENTCreate):
    """新しいPAYMENTを作成する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 新しいPAYMENTを1件追加する
    cursor.execute(
        "INSERT INTO payments (title, payer, amount) VALUES (?, ?, ?)",
        (payment.title, payment.payer, payment.amount)
    )

    conn.commit()  # 追加を確定する
    id = cursor.lastrowid  # たった今追加した行の id を取得する

    conn.close()  # 接続を閉じる

    return {
        "id": id,  "title": payment.title, "payer": payment.payer,"amount": payment.amount
    }


@app.delete("/payments/{id}")
def delete_payment(id: int):
    # 中身の (payment_id,) や "id": payment_id もすべて id に書き換える
    """PAYMENTを削除する"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 削除する前に、その id のPAYMENTが存在するか確認する
    cursor.execute("SELECT id FROM payments WHERE id = ?", (payment_id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="PAYMENT not found")

    cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))  # 削除する
    conn.commit()  # 削除を確定する

    conn.close()
    return {"message": "PAYMENT deleted", "id": payment_id}


# --- 静的ファイル配信 ---
# static フォルダの中身（index.html など）をそのままブラウザに表示できるようにする
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# --- アプリ起動時にDBを初期化 ---
# プログラムが読み込まれたタイミングで、テーブルが無ければ作っておく
init_db()

# このファイルを直接 `python main.py` で実行したときだけ、サーバーを起動する
if __name__ == "__main__":
    # host="0.0.0.0" で外部からのアクセスも受け付ける。ポート8000で待ち受ける
    uvicorn.run(app, host="0.0.0.0", port=8000)