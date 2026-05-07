from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import sqlite3
import uuid
import time
import random
import os
import requests
import datetime
import threading

app = FastAPI()

# ----------------------------
# LOGGING
# ----------------------------
def log(tag, msg):
    colors = {
        "POST": "\033[94m",
        "SCHEDULER": "\033[93m",
        "WORKER": "\033[92m",
        "LLM": "\033[95m",
        "ERROR": "\033[91m",
        "DB": "\033[96m"
    }
    reset = "\033[0m"
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{colors.get(tag,'')}[{now}] [{tag}] {msg}{reset}", flush=True)


# ----------------------------
# CONFIG
# ----------------------------
DB_NAME = "social.db"
LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ----------------------------
# DB INIT
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        caption TEXT,
        media TEXT,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        created_at REAL
    )
    """)

    # NEW: added "username"
    c.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id TEXT PRIMARY KEY,
        post_id TEXT,
        ai_type TEXT,
        username TEXT,
        content TEXT,
        created_at REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS used_names (
        post_id TEXT,
        ai_type TEXT,
        username TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS scheduled (
        id TEXT PRIMARY KEY,
        post_id TEXT,
        ai_type TEXT,
        execute_at REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ----------------------------
# AI CONFIG
# ----------------------------
AI_GROUPS = [
    ("support", 12),
    ("curious", 10),
    ("critic", 10),
    ("toxic", 5),
    ("neutral_hater", 5)
]

PROMPTS = {
    "support": "You are supportive. Celebrate in 1 sentence.",
    "curious": "You are curious. Ask a short question.",
    "critic": "You are critical but fair. Give feedback in 1 sentence.",
    "toxic": "You are slightly toxic but not abusive. Be blunt.",
    "neutral_hater": "You dislike the post mildly. Be dismissive."
}

# ----------------------------
# NEW: HUMAN NAMES
# ----------------------------
AI_NAMES = {
    "support": ["Aarav", "Vihaan", "Arjun", "Reyansh", "Kabir"],
    "curious": ["Ishaan", "Advik", "Rohan", "Kiran", "Dev"],
    "critic": ["Ravi", "Siddharth", "Manoj", "Harish", "Nikhil"],
    "toxic": ["Rocky", "Vicky", "Max", "Jay", "Zane"],
    "neutral_hater": ["Amit", "Suresh", "Naresh", "Lokesh", "Dinesh"]
}


def get_ai_name(conn, post_id, ai_type):
    c = conn.cursor()

    rows = c.execute("""
        SELECT username FROM used_names
        WHERE post_id=? AND ai_type=?
    """, (post_id, ai_type)).fetchall()

    used = [r["username"] for r in rows]

    pool = AI_NAMES.get(ai_type, ["User"])

    available = [n for n in pool if n not in used]

    # NO names left
    if not available:
        return None

    name = random.choice(available)

    c.execute("""
        INSERT INTO used_names VALUES (?, ?, ?)
    """, (post_id, ai_type, name))

    return name


# ----------------------------
# DB CONNECTION
# ----------------------------
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# AI REACTIONS
# ----------------------------
def get_ai_reaction(ai_type):
    if ai_type == "support":
        return (1, 0)

    elif ai_type == "curious":
        return (random.choice([1, 0]), 0)

    elif ai_type == "critic":
        return (0, random.choice([1, 0]))

    elif ai_type == "toxic":
        return (0, 1)

    elif ai_type == "neutral_hater":
        return (0, random.choice([1, 0]))

    return (0, 0)


# ----------------------------
# POST CREATE
# ----------------------------
@app.post("/post")
async def create_post(caption: str = Form(...), file: UploadFile = File(None)):

    post_id = str(uuid.uuid4())

    filename = None

    if file:
        filename = f"{post_id}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as f:
            f.write(await file.read())

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO posts VALUES (?, ?, ?, 0, 0, ?)",
        (post_id, caption, filename, time.time())
    )

    conn.commit()
    conn.close()

    log("POST", f"Created {post_id}")

    schedule_ai(post_id)

    return {"post_id": post_id}


# ----------------------------
# SCHEDULER
# ----------------------------
def schedule_ai(post_id):

    log("SCHEDULER", f"Scheduling {post_id}")

    conn = get_db()
    c = conn.cursor()

    now = time.time()

    ai_queue = []

    for group, count in AI_GROUPS:
        ai_queue += [group] * count

    random.shuffle(ai_queue)

    current_time = now + 5

    for ai_type in ai_queue:

        current_time += random.randint(180, 420)

        c.execute(
            "INSERT INTO scheduled VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), post_id, ai_type, current_time)
        )

    conn.commit()
    conn.close()

    log("SCHEDULER", "Timeline created")


# ----------------------------
# LLM
# ----------------------------
def generate_comment(ai_type, caption):

    log("LLM", f"{ai_type} generating")

    payload = {
        "messages": [
            {"role": "system", "content": PROMPTS[ai_type]},
            {"role": "user", "content": caption}
        ],
        "temperature": 0.8,
        "max_tokens": 80
    }

    try:
        r = requests.post(LLAMA_URL, json=payload, timeout=30)

        return r.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        log("ERROR", str(e))
        return "..."


# ----------------------------
# WORKER
# ----------------------------
def worker():

    log("WORKER", "Started")

    while True:

        try:
            conn = get_db()
            c = conn.cursor()

            now = time.time()

            row = c.execute("""
                SELECT * FROM scheduled
                ORDER BY execute_at ASC
                LIMIT 1
            """).fetchone()

            if not row:
                conn.close()
                time.sleep(3)
                continue

            remaining = max(0, int(row["execute_at"] - now))

            log("WORKER", f"Next comment in {remaining} sec")

            if row["execute_at"] > now:
                conn.close()
                time.sleep(2)
                continue

            event_id = row["id"]
            post_id = row["post_id"]
            ai_type = row["ai_type"]

            post = c.execute(
                "SELECT caption FROM posts WHERE id=?",
                (post_id,)
            ).fetchone()

            if post:

                comment = generate_comment(ai_type, post["caption"])

                username = get_ai_name(conn, post_id, ai_type)

                # no unique names left
                if not username:

                    log("WORKER", f"No names left for {ai_type} on post {post_id}")

                    c.execute("DELETE FROM scheduled WHERE id=?", (event_id,))
                    conn.commit()
                    conn.close()

                    time.sleep(2)
                    continue

                likes_delta, dislikes_delta = get_ai_reaction(ai_type)

                c.execute("""
                    INSERT INTO interactions
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    post_id,
                    ai_type,
                    username,
                    comment,
                    time.time()
                ))

                c.execute("""
                    UPDATE posts
                    SET likes = likes + ?, dislikes = dislikes + ?
                    WHERE id = ?
                """, (
                    likes_delta,
                    dislikes_delta,
                    post_id
                ))

                log("DB", f"{username} ({ai_type})")

            c.execute("DELETE FROM scheduled WHERE id=?", (event_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            log("ERROR", str(e))

        time.sleep(2)


@app.on_event("startup")
def start_worker():
    threading.Thread(target=worker, daemon=True).start()
    log("WORKER", "Attached on startup")


# ----------------------------
# API
# ----------------------------
@app.get("/posts")
def get_posts():

    conn = get_db()
    c = conn.cursor()

    rows = c.execute("""
        SELECT *,
        (SELECT COUNT(*) FROM interactions WHERE post_id = posts.id) as comment_count
        FROM posts
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return {
        "posts": [dict(r) for r in rows]
    }


@app.get("/comments/{post_id}")
def get_comments(post_id: str):

    conn = get_db()
    c = conn.cursor()

    rows = c.execute("""
        SELECT username, ai_type, content
        FROM interactions
        WHERE post_id=?
        ORDER BY created_at ASC
    """, (post_id,)).fetchall()

    conn.close()

    return {
        "comments": [
            {
                "user": r["username"],
                "type": r["ai_type"],
                "text": r["content"]
            }
            for r in rows
        ]
    }


@app.delete("/post/{post_id}")
def delete_post(post_id: str):

    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    c.execute("DELETE FROM interactions WHERE post_id=?", (post_id,))
    c.execute("DELETE FROM scheduled WHERE post_id=?", (post_id,))
    c.execute("DELETE FROM used_names WHERE post_id=?", (post_id,))

    conn.commit()
    conn.close()

    return {"status": "deleted"}


@app.get("/")
def ui():
    return FileResponse("index.html")