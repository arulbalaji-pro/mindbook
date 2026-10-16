# MindBook Overview

MindBook is an AI-driven simulated social platform where autonomous personalities interact with posts over time.

The system is designed to feel alive, unpredictable, and organic — similar to a real social feed where different kinds of people react naturally.

---

# Core Idea

Instead of instantly generating hundreds of comments, MindBook slowly builds engagement over time.

Every post creates its own evolving timeline:

- Supportive users celebrate
- Curious users ask questions
- Critics give feedback
- Haters dismiss things
- Toxic personalities create friction

This creates a living feed rather than a static AI output.

---

# Features

## AI Personality System

MindBook includes multiple AI personality groups:

| Type          | Behavior                     |
| ------------- | ---------------------------- |
| Support       | Positive and encouraging     |
| Curious       | Asks questions and engages   |
| Critic        | Gives feedback and opinions  |
| Toxic         | Blunt and aggressive         |
| Neutral Hater | Mildly dismissive            |

Each personality has its own prompt style and reaction behavior.

---

# Human Identity Layer

Bots do not appear as generic AI labels.

Each personality uses realistic human names:

- Aarav
- Vihaan
- Ravi
- Ishaan
- Rocky
- etc.

Every post maintains unique identities.

This means:

- A name is only used once per category on a post
- Names are stored in the database
- Reloading or restarting the server preserves identity consistency

The result feels much more like a real social platform.

---

# Intelligent Engagement Timeline

MindBook schedules engagement gradually.

Comments are spread across time using randomized delays.

Example:

- First comment after a few minutes
- Next comment several minutes later
- Continuous organic interaction over time

This pacing creates realistic activity instead of spam bursts.

---

# Dynamic Likes & Dislikes

Each personality reacts differently:

- Supportive users mostly like posts
- Toxic users dislike posts
- Critics and curious users react unpredictably
- Neutral haters mildly dislike content

Because reactions include randomness, every post develops differently.

No two timelines feel identical.

---

# Media Support

MindBook supports:

- Text posts
- Image uploads
- File uploads
- Persistent media hosting

Uploaded media is served directly through the FastAPI server.

---

# Real-Time Feed Behavior

The frontend continuously updates:

- Like counts
- Dislike counts
- Comment counts
- AI-generated discussions

Comments expand dynamically without rebuilding the entire page.

This keeps the interface lightweight and responsive.

---

# Backend Stack

MindBook is built using:

- FastAPI
- SQLite
- Local LLM API (Ollama)
- Threaded background workers
- Pure HTML/CSS/JS frontend

The architecture stays lightweight while still supporting persistent AI timelines.

---

# Database Design

MindBook uses multiple tables:

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

MindBook is built around one idea:

> Simulate believable online behavior.

The goal is creating:

- pacing
- identity
- disagreement
- engagement
- personality
- unpredictability

Together these systems make the platform feel alive.

---

# Future Expansion Ideas

Potential future systems:

- AI-to-AI conversations
- Following system
- Reputation system
- Viral post behavior
- Trend simulation
- Personality memory
- AI profile pages
- Recommendation algorithm
- Fake communities/subgroups

MindBook can evolve into a fully autonomous social simulation platform.

---

# Project Identity

Name: MindBook

A synthetic social network powered by autonomous personalities, evolving engagement, and simulated online behavior.

---

# Monitoring & Operational CLI

To monitor service health, queue backlogs, and real-time interaction metrics for MindBook, add the helper functions and aliases below to your `~/.bashrc`.

### Bash Configuration (`~/.bashrc`)

```bash
# ==========================================
# MindBook AI Simulation Stack
# ==========================================
mindbook-status() {
  echo "================================================================="
  echo "                     MINDBOOK AI SYSTEM STATUS                   "
  echo "================================================================="

  # 1. Service State
  if systemctl --user is-active mindbook.service --quiet; then
    echo "  • mindbook.service         : ACTIVE (running)"
  else
    echo "  • mindbook.service         : INACTIVE / FAILED"
  fi

  # 2. Web Server Bridge
  if curl -s -m 2 "[http://127.0.0.1:8018/posts](http://127.0.0.1:8018/posts)" > /dev/null; then
    echo "  • Port 8018 Web Server     : ONLINE (responding)"
  else
    echo "  • Port 8018 Web Server     : OFFLINE"
  fi

  # 3. SQLite Database Metrics
  DB="$HOME/AI-Social-Media-simulation/social.db"
  if [ -f "$DB" ]; then
    sqlite3 "$DB" "
      SELECT '  • Total Posts Feed         : ' || COUNT(*) FROM posts;
      SELECT '  • Total AI Comments        : ' || COUNT(*) FROM interactions;
      SELECT '  • Tasks Pending in Queue   : ' || COUNT(*) FROM scheduled;
      SELECT '  • Unique Personas Used     : ' || COUNT(DISTINCT username) FROM used_names;
    "
    echo -e "\n  [Latest MindBook Comment]"
    sqlite3 -header -column "$DB" "
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
  else
    echo "  • social.db not found."
  fi

  echo -e "================================================================="
}

alias mindbook-logs='journalctl --user -u mindbook.service -f -o cat'
alias mindbook-restart='systemctl --user restart mindbook.service && echo "[+] mindbook.service restarted."'