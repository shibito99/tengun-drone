import sqlite3
import hashlib
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── 設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="メモ帳",
    page_icon="📝",
    layout="centered",
)

DB_PATH   = Path(__file__).parent / "data.db"
TITLE_MAX = 100
MEMO_MAX  = 500

# ユーザー名: パスワードのSHA-256ハッシュ
# 追加方法: python -c "import hashlib; print(hashlib.sha256('パスワード'.encode()).hexdigest())"
USERS = {
    "admin":   hashlib.sha256("password123".encode()).hexdigest(),
    "alice":   hashlib.sha256("alice123".encode()).hexdigest(),
    "bob":     hashlib.sha256("bob456".encode()).hexdigest(),
    "charlie": hashlib.sha256("charlie789".encode()).hexdigest(),
    "diana":   hashlib.sha256("diana000".encode()).hexdigest(),
}


# ── DB ──────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        with get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    title   TEXT NOT NULL,
                    memo    TEXT,
                    created TEXT NOT NULL,
                    owner   TEXT NOT NULL DEFAULT ''
                )
            """)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(items)").fetchall()]
            if "owner" not in cols:
                conn.execute("ALTER TABLE items ADD COLUMN owner TEXT NOT NULL DEFAULT ''")
    except sqlite3.Error as e:
        st.error(f"DB初期化エラー: {e}")
        st.stop()


def sanitize(text, max_len: int) -> str:
    return (text or "").strip()[:max_len]


def save_item(title: str, memo: str, owner: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO items (title, memo, created, owner) VALUES (?, ?, ?, ?)",
            (title, memo, datetime.now().strftime("%Y-%m-%d %H:%M"), owner),
        )


def fetch_all(owner: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE owner=? ORDER BY id DESC", (owner,)
        ).fetchall()


def update_item(item_id: int, title: str, memo: str, owner: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET title=?, memo=? WHERE id=? AND owner=?",
            (title, memo, item_id, owner),
        )


def delete_item(item_id: int, owner: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM items WHERE id=? AND owner=?", (item_id, owner))


def check_login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    return USERS.get(username) == hashlib.sha256(password.encode()).hexdigest()


# ── セッション初期化 ─────────────────────────────────────
init_db()

for key, default in [("logged_in", False), ("editing_id", None),
                     ("username", ""), ("confirm_delete_id", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── ログイン画面 ─────────────────────────────────────────
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("## 📝 メモ帳")
        st.caption("ログインしてください")
        with st.form("login_form"):
            username  = st.text_input("ユーザー名", placeholder="admin")
            password  = st.text_input("パスワード", type="password")
            login_btn = st.form_submit_button("ログイン", use_container_width=True)

        if login_btn:
            if not username.strip() or not password:
                st.error("ユーザー名とパスワードを入力してください。")
            elif check_login(username.strip(), password):
                st.session_state.logged_in = True
                st.session_state.username  = username.strip()
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが違います。")
    st.stop()

# ── ここから下はログイン済みのみ ─────────────────────────
me = st.session_state.username
if not me:
    st.session_state.logged_in = False
    st.rerun()

# ヘッダー
col_title, col_user, col_logout = st.columns([5, 3, 1])
col_title.markdown("## 📝 メモ帳")
col_user.caption(f"ログイン中: **{me}**")
if col_logout.button("ログアウト"):
    for key in ("logged_in", "editing_id", "username", "confirm_delete_id"):
        st.session_state[key] = False if key == "logged_in" else (None if key != "username" else "")
    st.rerun()

st.divider()

# ── 新規入力 ─────────────────────────────────────────────
with st.expander("➕ 新規入力", expanded=True):
    with st.form("input_form", clear_on_submit=True):
        title = st.text_input(
            f"タイトル（必須・{TITLE_MAX}文字以内）",
            max_chars=TITLE_MAX,
            placeholder="タイトルを入力",
        )
        memo = st.text_area(
            f"メモ（{MEMO_MAX}文字以内）",
            max_chars=MEMO_MAX,
            placeholder="メモを入力（任意）",
            height=120,
        )
        submitted = st.form_submit_button("💾 保存する", use_container_width=True)

    if submitted:
        clean_title = sanitize(title, TITLE_MAX)
        clean_memo  = sanitize(memo,  MEMO_MAX)
        if not clean_title:
            st.error("タイトルは必須です。空白のみは使えません。")
        else:
            try:
                save_item(clean_title, clean_memo, me)
                st.success(f"「{clean_title}」を保存しました。")
                st.session_state.confirm_delete_id = None
            except sqlite3.Error as e:
                st.error(f"保存に失敗しました: {e}")

st.divider()

# ── 一覧 ─────────────────────────────────────────────────
try:
    items = fetch_all(me)
except sqlite3.Error as e:
    st.error(f"データの読み込みに失敗しました: {e}")
    items = []

count = len(items)
st.markdown(f"### 一覧　`{count}件`")

if not items:
    st.info("まだデータがありません。上のフォームから入力してください。")
else:
    for row in items:
        # 編集モード
        if st.session_state.editing_id == row["id"]:
            with st.container(border=True):
                st.caption(f"編集中　／　登録日時: {row['created']}")
                with st.form(f"edit_form_{row['id']}"):
                    new_title = st.text_input(
                        f"タイトル（必須・{TITLE_MAX}文字以内）",
                        value=row["title"] or "",
                        max_chars=TITLE_MAX,
                    )
                    new_memo = st.text_area(
                        f"メモ（{MEMO_MAX}文字以内）",
                        value=row["memo"] or "",
                        max_chars=MEMO_MAX,
                        height=120,
                    )
                    col_save, col_cancel = st.columns(2)
                    save_clicked   = col_save.form_submit_button("💾 保存", use_container_width=True)
                    cancel_clicked = col_cancel.form_submit_button("キャンセル", use_container_width=True)

                if save_clicked:
                    clean_title = sanitize(new_title, TITLE_MAX)
                    clean_memo  = sanitize(new_memo,  MEMO_MAX)
                    if not clean_title:
                        st.error("タイトルは必須です。")
                    else:
                        try:
                            update_item(row["id"], clean_title, clean_memo, me)
                            st.session_state.editing_id = None
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"更新に失敗しました: {e}")
                if cancel_clicked:
                    st.session_state.editing_id = None
                    st.rerun()

        # 削除確認モード
        elif st.session_state.confirm_delete_id == row["id"]:
            with st.container(border=True):
                st.warning(f"「{row['title']}」を削除しますか？この操作は元に戻せません。")
                col_yes, col_no = st.columns(2)
                if col_yes.button("削除する", key=f"confirm_yes_{row['id']}", use_container_width=True):
                    try:
                        delete_item(row["id"], me)
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"削除に失敗しました: {e}")
                if col_no.button("キャンセル", key=f"confirm_no_{row['id']}", use_container_width=True):
                    st.session_state.confirm_delete_id = None
                    st.rerun()

        # 通常表示
        else:
            with st.container(border=True):
                col_info, col_edit, col_del = st.columns([6, 1, 1])
                col_info.markdown(f"**{row['title'] or '（タイトルなし）'}**")
                col_info.caption(f"{row['memo'] or '（メモなし）'}　／　{row['created'] or ''}")

                if col_edit.button("✏️", key=f"edit_{row['id']}", help="編集"):
                    st.session_state.editing_id        = row["id"]
                    st.session_state.confirm_delete_id = None
                    st.rerun()

                if col_del.button("🗑️", key=f"del_{row['id']}", help="削除"):
                    st.session_state.confirm_delete_id = row["id"]
                    st.session_state.editing_id        = None
                    st.rerun()
