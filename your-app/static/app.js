// バックエンド（main.py）のAPIエンドポイント
const API_URL = "/payments";

// ============================================================
// データ通信処理（CRUD）
// ============================================================

/**
 * 1. 支払い一覧を取得して画面に表示する（リロード時にも動く）
 */
async function loadPayments() {
  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      const error = await response.json();
      showError(error.detail || "データの取得に失敗しました");
      return;
    }

    const payments = await response.json();
    renderPayments(payments); // 画面を描画
  } catch (error) {
    showError("通信エラーが発生しました。サーバー（main.py）が起動しているか確認してください。");
  }
}

/**
 * 2. 新しい支払いをデータベースに追加する
 */
async function addPayment() {
  // index.html の入力欄（id）から値を取り出す
  const titleInput = document.getElementById("title-input");
  const payerInput = document.getElementById("payer-input");
  const amountInput = document.getElementById("amount-input");

  const title = titleInput.value.trim();
  const payer = payerInput.value.trim();
  const amount = parseInt(amountInput.value, 10);

  // 送信前の入力チェック（バリデーション）
  if (title === "") {
    showError("内容を入力してください");
    return;
  }
  if (payer === "") {
    showError("支払った人の名前を入力してください");
    return;
  }
  if (isNaN(amount) || amount <= 0) {
    showError("正しい金額を入力してください");
    return;
  }

  try {
    // バックエンド（FastAPI）へ POST リクエストを送信してDBに保存
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        payer: payer,
        amount: amount,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      showError(error.detail || "追加に失敗しました");
      return;
    }

    // 登録成功後、入力欄を空にする
    titleInput.value = "";
    payerInput.value = "";
    amountInput.value = "";

    // 最新のリストを取り直して画面を更新（これで保存されたことが確認できる）
    await loadPayments();
  } catch (error) {
    showError("通信エラーが発生しました");
  }
}

/**
 * 3. 指定したデータを削除する
 */
async function deletePayment(id) {
  try {
    const response = await fetch(`${API_URL}/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      showError(error.detail || "削除に失敗しました");
      return;
    }

    // 削除後にリストを更新
    await loadPayments();
  } catch (error) {
    showError("通信エラーが発生しました");
  }
}

// ============================================================
// 画面描画処理
// ============================================================

/**
 * 取得した支払いデータをHTML要素に変換して表示する
 */
function renderPayments(payments) {
  const list = document.getElementById("payment-list");
  list.innerHTML = ""; // 表示を一度リセット

  payments.forEach((payment) => {
    // <li> 要素の作成
    const li = document.createElement("li");
    li.className = "todo-item";

    // 情報（テキスト）表示エリア
    const infoDiv = document.createElement("div");
    infoDiv.className = "todo-info";

    const titleSpan = document.createElement("span");
    titleSpan.className = "todo-title";
    titleSpan.textContent = payment.title;

    const detailsSpan = document.createElement("span");
    detailsSpan.className = "todo-details";
    // 金額を 3,000円 のようにカンマ区切りにする
    const formattedAmount = Number(payment.amount).toLocaleString();
    detailsSpan.textContent = `支払者: ${payment.payer} / 金額: ${formattedAmount}円`;

    infoDiv.appendChild(titleSpan);
    infoDiv.appendChild(detailsSpan);

    // 削除ボタンの作成
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-button";
    deleteBtn.textContent = "削除";
    deleteBtn.addEventListener("click", () => deletePayment(payment.id));

    // <li> にまとめる
    li.appendChild(infoDiv);
    li.appendChild(deleteBtn);

    // <ul>（payment-list）に追加
    list.appendChild(li);
  });
}

// ============================================================
// エラーメッセージ表示
// ============================================================

function showError(message) {
  const errorDiv = document.getElementById("error-message");
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
    setTimeout(() => {
      errorDiv.style.display = "none";
    }, 5000);
  }
}

// ============================================================
// イベント登録 & 初回読み込み
// ============================================================

// フォーム送信（追加ボタン押下 or Enter）時のイベント設定
const paymentForm = document.getElementById("payment-form");
if (paymentForm) {
  paymentForm.addEventListener("submit", function (e) {
    e.preventDefault(); // 画面の再読み込み（デフォルト挙動）を止める
    addPayment();
  });
}

// ページが開かれた（リロードされた）タイミングで自動的にデータベースからデータを取得
loadPayments();