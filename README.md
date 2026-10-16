# GhostNet Overview

GhostNet is an AI-driven simulated social platform where autonomous personalities interact with posts over time.

The system is designed to feel alive, unpredictable, and organic — similar to a real social feed where different kinds of people react naturally.

---

# Core Idea

Instead of instantly generating hundreds of comments, GhostNet slowly builds engagement over time.

Every post creates its own evolving timeline:

* Supportive users celebrate
* Curious users ask questions
* Critics give feedback
* Haters dismiss things
* Toxic personalities create friction

This creates a living feed rather than a static AI output.

---

# Features

## AI Personality System

GhostNet includes multiple AI personality groups:

| Type          | Behavior                    |
| ------------- | --------------------------- |
| Support       | Positive and encouraging    |
| Curious       | Asks questions and engages  |
| Critic        | Gives feedback and opinions |
| Toxic         | Blunt and aggressive        |
| Neutral Hater | Mildly dismissive           |

Each personality has its own prompt style and reaction behavior.

---

# Human Identity Layer

Bots do not appear as generic AI labels.

Each personality uses realistic human names:

* Aarav
* Vihaan
* Ravi
* Ishaan
* Rocky
* etc.

Every post maintains unique identities.

This means:

* A name is only used once per category on a post
* Names are stored in the database
* Reloading or restarting the server preserves identity consistency

The result feels much more like a real social platform.

---

# Intelligent Engagement Timeline

GhostNet schedules engagement gradually.

Comments are spread across time using randomized delays.

Example:

* First comment after a few minutes
* Next comment several minutes later
* Continuous organic interaction over time

This pacing creates realistic activity instead of spam bursts.

---

# Dynamic Likes & Dislikes

Each personality reacts differently:

* Supportive users mostly like posts
* Toxic users dislike posts
* Critics and curious users react unpredictably
* Neutral haters mildly dislike content

Because reactions include randomness, every post develops differently.

No two timelines feel identical.

---

# Media Support

GhostNet supports:

* Text posts
* Image uploads
* File uploads
* Persistent media hosting

Uploaded media is served directly through the FastAPI server.

---

# Real-Time Feed Behavior

The frontend continuously updates:

* Like counts
* Dislike counts
* Comment counts
* AI-generated discussions

Comments expand dynamically without rebuilding the entire page.

This keeps the interface lightweight and responsive.

---

# Backend Stack

GhostNet is built using:

* FastAPI
* SQLite
* Local LLM API
* Threaded background workers
* Pure HTML/CSS/JS frontend

The architecture stays lightweight while still supporting persistent AI timelines.

---

# Database Design

GhostNet uses multiple tables:

| Table        | Purpose                    |
| ------------ | -------------------------- |
| posts        | Stores posts and reactions |
| interactions | Stores AI comments         |
| scheduled    | Stores future AI events    |
| used_names   | Tracks identities per post |

This separation keeps the system scalable and organized.

---

# Worker Engine

A background worker continuously:

1. Checks scheduled events
2. Generates AI responses
3. Applies reactions
4. Stores comments
5. Updates engagement

This creates the illusion of an active network operating on its own.

---

# Design Philosophy

GhostNet is built around one idea:

> Simulate believable online behavior.

The goal is creating:

* pacing
* identity
* disagreement
* engagement
* personality
* unpredictability

Together these systems make the platform feel alive.

---

# Future Expansion Ideas

Potential future systems:

* AI-to-AI conversations
* Following system
* Reputation system
* Viral post behavior
* Trend simulation
* Personality memory
* AI profile pages
* Recommendation algorithm
* Fake communities/subgroups

GhostNet can evolve into a fully autonomous social simulation platform.

---

# Project Identity

Name: GhostNet

A synthetic social network powered by autonomous personalities, evolving engagement, and simulated online behavior.


## Monitoring & Operational CLI

To monitor service health and database metrics for both MindBook and RetroTube, run `ai-worker-status`.

### Bash Configuration (`~/.bashrc`)

```bash
# RetroTube & Simulated Social AI Stack
ai-worker-status() {
  echo "================================================================="
  echo "              SIMULATED SOCIAL AI SYSTEMS STATUS                 "
  echo "================================================================="

  # --- RETROTUBE SECTION ---
  echo -e "
[1] RETROTUBE (Port 7004 & 5055):"
  systemctl --user is-active retrotube-worker.service --quiet &&     echo "  • retrotube-worker.service : ACTIVE (running)" ||     echo "  • retrotube-worker.service : INACTIVE / FAILED"

  curl -s -m 2 "http://127.0.0.1:5055/comments?id=ping" > /dev/null &&     echo "  • Port 5055 Bridge          : ONLINE (responding)" ||     echo "  • Port 5055 Bridge          : OFFLINE"

  docker ps --filter "name=retro-tube" --format "  • {{.Names}} : {{.Status}} ({{.Ports}})"

  if [ -f "$HOME/retro-tube/retrotube.db" ]; then
    sqlite3 "$HOME/retro-tube/retrotube.db" "
      SELECT '  • Total Comments Posted    : ' || COUNT(*) FROM comments;
      SELECT '  • Tasks Pending Exec       : ' || COUNT(*) FROM scheduled_tasks WHERE executed = 0;
      SELECT '  • Average Rating Given     : ' || ROUND(AVG(stars), 2) || ' / 5.0' FROM comments;
    "
    echo -e "
  [Upcoming Scheduled Tasks in Queue]"
    sqlite3 -header -column "$HOME/retro-tube/retrotube.db" "
      SELECT 
        id, 
        substr(prompt, 1, 24) AS video_title, 
        username, 
        ai_type, 
        stars || '★' AS rating, 
        datetime(scheduled_time, 'unixepoch', 'localtime') AS due_at
      FROM scheduled_tasks 
      WHERE executed = 0 
      ORDER BY scheduled_time ASC 
      LIMIT 3;
    "
  fi

  # --- MINDBOOK SECTION ---
  echo -e "
[2] MINDBOOK (FastAPI / Port 8018):"
  systemctl --user is-active mindbook.service --quiet &&     echo "  • mindbook.service         : ACTIVE (running)" ||     echo "  • mindbook.service         : INACTIVE / FAILED"

  curl -s -m 2 "http://127.0.0.1:8018/posts" > /dev/null &&     echo "  • Port 8018 Web Server     : ONLINE (responding)" ||     echo "  • Port 8018 Web Server     : OFFLINE"

  if [ -f "$HOME/AI-Social-Media-simulation/social.db" ]; then
    sqlite3 "$HOME/AI-Social-Media-simulation/social.db" "
      SELECT '  • Total Posts Feed         : ' || COUNT(*) FROM posts;
      SELECT '  • Total AI Comments        : ' || COUNT(*) FROM interactions;
      SELECT '  • Tasks Pending in Queue   : ' || COUNT(*) FROM scheduled;
      SELECT '  • Unique Personas Used     : ' || COUNT(DISTINCT username) FROM used_names;
    "
    echo -e "
  [Latest MindBook Comment]"
    sqlite3 -header -column "$HOME/AI-Social-Media-simulation/social.db" "
      SELECT 
        substr(id, 1, 8) AS id, 
        substr(post_id, 1, 8) AS post_id, 
        username, 
        ai_type, 
        substr(content, 1, 35) AS comment 
      FROM interactions 
      ORDER BY created_at DESC 
      LIMIT 1;
    "
  fi

  echo -e "
================================================================="
}

alias sim-social-logs='journalctl --user -u retrotube-worker.service -f'
alias mindbook-logs='journalctl --user -u mindbook.service -f -o cat'
alias sim-social-restart='systemctl --user restart retrotube-worker.service && docker compose -f ~/retro-tube/docker-compose.yml restart && echo "[+] AI worker and RetroTube container restarted."'
```

| Command | Purpose |
| :--- | :--- |
| `ai-worker-status` | Health & SQLite metrics dashboard for MindBook and RetroTube |
| `mindbook-logs` | Live unbuffered logs for MindBook worker & Ollama |
| `sim-social-logs` | Live task execution and queue countdowns for RetroTube |
| `sim-social-restart` | Restart RetroTube worker and Docker container |
