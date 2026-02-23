#!/usr/bin/env python3
"""
Claudia: claudia-teach.py
Stop hook that fires after every Claude response.
Scans for technology keywords and offers teaching moments for beginners.
Also reveals commands contextually for beginners (progressive reveal).
Advisory only (exit 0 with additionalContext), never blocks.
Session-aware dedup to avoid repeating the same keyword tip.
"""

import json
import os
import re
import sys
import time

# Technology keywords by category
KEYWORDS = {
    "hosting": {
        "Vercel": "a platform for deploying frontend apps and serverless functions",
        "Netlify": "a platform for deploying static sites and serverless functions",
        "Railway": "a platform for deploying apps and databases with minimal config",
        "Fly.io": "a platform for running apps close to users globally",
        "Render": "a cloud platform for deploying web services and databases",
        "Heroku": "a cloud platform for deploying apps (one of the originals)",
        "AWS": "Amazon Web Services — the biggest cloud provider",
        "GCP": "Google Cloud Platform — Google's cloud infrastructure",
        "Azure": "Microsoft's cloud platform",
    },
    "databases": {
        "Postgres": "a powerful open-source relational database",
        "PostgreSQL": "a powerful open-source relational database",
        "MongoDB": "a document database that stores data as JSON-like objects",
        "Redis": "an in-memory data store, often used for caching",
        "SQLite": "a lightweight database that lives in a single file",
        "Supabase": "an open-source Firebase alternative built on Postgres",
        "PlanetScale": "a serverless MySQL platform with branching",
        "Prisma": "a TypeScript ORM that generates type-safe database queries",
        "Drizzle": "a lightweight TypeScript ORM with SQL-like syntax",
        "Turso": "an edge-hosted SQLite database",
        "Neon": "serverless Postgres with branching and autoscaling",
        "Pinecone": "a vector database for AI/ML similarity search",
        "DynamoDB": "AWS's serverless NoSQL database",
        "Firestore": "Google's serverless document database (part of Firebase)",
    },
    "frameworks": {
        "Next.js": "a React framework for building full-stack web apps",
        "React": "a JavaScript library for building user interfaces",
        "Vue": "a progressive JavaScript framework for building UIs",
        "Svelte": "a compiler that turns components into efficient JavaScript",
        "SvelteKit": "a full-stack framework built on Svelte",
        "Astro": "a framework for building content-focused websites",
        "Express": "a minimal Node.js web framework for building APIs",
        "FastAPI": "a modern Python web framework for building APIs",
        "Django": "a batteries-included Python web framework",
        "Flask": "a lightweight Python web framework",
        "Remix": "a full-stack React framework focused on web standards",
        "Nuxt": "a full-stack Vue framework (like Next.js but for Vue)",
        "Hono": "an ultrafast web framework that runs anywhere (Cloudflare, Deno, Bun)",
        "tRPC": "end-to-end typesafe APIs without code generation",
    },
    "tools": {
        "Docker": "a tool for packaging apps into containers that run anywhere",
        "Kubernetes": "a system for managing containerized apps at scale",
        "Terraform": "infrastructure-as-code tool for provisioning cloud resources",
        "GitHub Actions": "CI/CD automation built into GitHub",
        "Webpack": "a module bundler for JavaScript applications",
        "Vite": "a fast build tool and dev server for modern web projects",
        "Bun": "an all-in-one JavaScript runtime, bundler, and package manager",
        "Deno": "a secure JavaScript/TypeScript runtime by Node's creator",
        "pnpm": "a fast, disk-efficient package manager for Node.js",
        "Turborepo": "a build system for JavaScript/TypeScript monorepos",
        "ESLint": "a tool for finding and fixing problems in JavaScript code",
        "Prettier": "an opinionated code formatter",
        "Tailwind": "a utility-first CSS framework",
        "Playwright": "a browser automation and testing framework",
        "Vitest": "a fast unit testing framework powered by Vite",
    },
    "concepts": {
        "API": "Application Programming Interface — how programs talk to each other",
        "REST": "a common pattern for designing web APIs using HTTP methods",
        "GraphQL": "a query language for APIs that lets you ask for exactly what you need",
        "WebSocket": "a protocol for real-time two-way communication between client and server",
        "OAuth": "a standard for letting apps access your data without your password",
        "JWT": "JSON Web Token — a compact way to securely transmit info between parties",
        "CI/CD": "Continuous Integration/Delivery — automating testing and deployment",
        "SSR": "Server-Side Rendering — generating HTML on the server for each request",
        "SSG": "Static Site Generation — pre-building HTML pages at build time",
        "ISR": "Incremental Static Regeneration — rebuilding static pages on demand",
        "ORM": "Object-Relational Mapping — lets you query databases using code instead of SQL",
        "CORS": "Cross-Origin Resource Sharing — controls which sites can call your API",
        "CSP": "Content Security Policy — tells browsers what resources your page can load",
        "CSRF": "Cross-Site Request Forgery — an attack that tricks users into unwanted actions",
        "XSS": "Cross-Site Scripting — an attack that injects malicious scripts into web pages",
        "CDN": "Content Delivery Network — serves your files from servers close to users",
        "DNS": "Domain Name System — translates domain names to IP addresses",
        "TLS": "Transport Layer Security — encrypts data in transit (the S in HTTPS)",
        "WASM": "WebAssembly — lets you run compiled code in the browser at near-native speed",
        "Edge Functions": "serverless functions that run close to users at CDN edge locations",
        "Middleware": "code that runs between a request and response, often for auth or logging",
        "Monorepo": "a single repository containing multiple projects or packages",
        "Microservices": "an architecture where an app is split into small, independent services",
    },
}

# Error patterns to detect
ERROR_PATTERNS = [
    (r'\berror\b.*\b(ENOENT|EACCES|EPERM|ECONNREFUSED)\b', "a system error"),
    (r'\bundefined is not a function\b', "a common JavaScript type error"),
    (r'\bCannot read propert(?:y|ies) of (undefined|null)\b', "a null reference error"),
    (r'\bModule not found\b', "a missing dependency error"),
    (r'\bSyntaxError\b', "a syntax error"),
    (r'\bTypeError\b', "a type error"),
    (r'\bReferenceError\b', "a reference error — usually a typo or missing variable"),
]

def stop_lock_acquire(session_id):
    """Try to acquire the per-turn Stop hook lock. Returns True if acquired."""
    lock_file = os.path.expanduser(f"~/.claude/claudia_stop_lock_{session_id}.tmp")
    now = time.time()
    try:
        if os.path.exists(lock_file):
            with open(lock_file) as f:
                ts = float(f.read().strip())
            if now - ts < 2.0:
                return False
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        with open(lock_file, "w") as f:
            f.write(str(now))
        return True
    except (IOError, ValueError):
        return True


# Contextual command reveals for beginners
COMMAND_REVEALS = {
    "file_written": {
        "patterns": [
            r"(?:I've |I have )?(?:created|wrote|written|saved|generated)\s+[`'\"]?\S+\.\w+",
            r"(?:new file|writing to|saved to)\s+[`'\"]?\S+\.\w+",
        ],
        "command": "/claudia:explain",
        "tip": "Want to understand what I just wrote? Try `/claudia:explain [filename]`",
    },
    "error_appeared": {
        "patterns": [
            r'\b(?:error|Error|ERROR)\b',
            r'\b(?:failed|Failed|FAILED)\b',
            r'\btraceback\b',
        ],
        "command": "/claudia:wtf",
        "tip": "Got an error you don't understand? Try `/claudia:wtf` and I'll break it down",
    },
    "git_activity": {
        "patterns": [
            r'\bgit (?:commit|push|pull|merge|rebase)\b',
            r'\b(?:committed|pushed|merged)\b',
            r'\bpull request\b',
        ],
        "command": "/claudia:review",
        "tip": "Want me to check your changes before committing? Try `/claudia:review`",
    },
    "multiple_files": {
        "patterns": [
            r'(?:created|wrote|updated)\s+\d+\s+files',
            r'(?:src|lib|components)/',
        ],
        "command": "/claudia:where",
        "tip": "Losing track of your project? Try `/claudia:where` for a guided tour",
    },
    "tech_question": {
        "patterns": [
            r'\bshould (?:I|we) use\b',
            r'\bwhich (?:database|framework|library|tool)\b',
            r'\bwhat\'?s the (?:best|right) way\b',
        ],
        "command": "/claudia:ask",
        "tip": "Got a tech question? Try `/claudia:ask` for architecture advice",
    },
    "project_growing": {
        "patterns": [
            r'\bpackage\.json\b.*\bdependenc',
            r'\b(?:npm|yarn|pnpm) install\b',
            r'\bnode_modules\b',
        ],
        "command": "/claudia:health",
        "tip": "Project growing? Try `/claudia:health` for a full checkup",
    },
    "shortcuts_mentioned": {
        "patterns": [
            r'\bshortcut',
            r'\bhotkey',
            r'\bkeybind',
            r'\bkeyboard\b',
        ],
        "command": "/claudia:shortcuts",
        "tip": "Want the full list of keyboard shortcuts? Try `/claudia:shortcuts`",
    },
}


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_teach_state_{session_id}.json")


def load_state(session_id):
    """Load state with backward-compatible migration from flat set to dict."""
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                data = json.load(f)
                # Migration: old format was a flat list (set of shown keywords)
                if isinstance(data, list):
                    return {
                        "shown_keywords": data,
                        "revealed_commands": [],
                    }
                # New format: dict with shown_keywords and revealed_commands
                if isinstance(data, dict):
                    data.setdefault("shown_keywords", [])
                    data.setdefault("revealed_commands", [])
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return {"shown_keywords": [], "revealed_commands": []}


def save_state(session_id, state):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f)
    except IOError:
        pass


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config, dismiss_hint


def load_config():
    return load_user_config()


def check(input_data, proactivity, experience):
    """Run teach logic. Returns output dict or None."""
    session_id = input_data.get("session_id", "default")
    message = input_data.get("last_assistant_message", "")

    if not message:
        return None

    if proactivity == "low":
        return None

    is_beginner = experience == "beginner"

    if not is_beginner and proactivity != "high":
        return None

    state = load_state(session_id)
    shown_keywords = set(state["shown_keywords"])
    revealed_commands = set(state["revealed_commands"])
    tips = []

    # Build suppressed topics set (case-insensitive)
    suppress_topics = input_data.get("suppress_topics", [])
    suppressed = {t.lower() for t in suppress_topics if isinstance(t, str)}

    # Scan for technology keywords
    for category, keywords in KEYWORDS.items():
        if category.lower() in suppressed:
            continue
        for keyword, description in keywords.items():
            if keyword.lower() in suppressed:
                continue
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, message, re.IGNORECASE):
                if keyword.lower() not in shown_keywords:
                    shown_keywords.add(keyword.lower())
                    tips.append(
                        f"I noticed we're talking about {keyword} ({description}). "
                        f"Want me to explain more? Just say `/claudia:explain {keyword.lower()}`\n"
                        f"(Say \"stop tips about {keyword}\" to silence this)"
                    )
                    break
        if tips:
            break

    # Scan for error patterns (only for beginners)
    if not tips and is_beginner:
        for pattern, description in ERROR_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                error_key = f"error-{description}"
                if error_key not in shown_keywords:
                    shown_keywords.add(error_key)
                    tips.append(
                        f"That looks like {description}. "
                        f"If you're not sure what it means, say `/claudia:explain` and paste the error."
                    )
                    break

    # Progressive command reveals (beginners only, max 1 per response)
    if is_beginner:
        for reveal_key, reveal in COMMAND_REVEALS.items():
            command = reveal["command"]
            if command in revealed_commands:
                continue
            for pattern in reveal["patterns"]:
                if re.search(pattern, message, re.IGNORECASE):
                    revealed_commands.add(command)
                    tips.append(reveal["tip"])
                    break
            if len(tips) > (1 if tips else 0):
                break

    if tips:
        state["shown_keywords"] = list(shown_keywords)
        state["revealed_commands"] = list(revealed_commands)
        save_state(session_id, state)
        tip_text = "\n".join(f"Claudia: {tip}" for tip in tips)
        system_text = tip_text
        context = tip_text + (
            "\nIf the user asks to stop tips about a keyword or category, "
            "add it to the \"suppress_topics\" list in ~/.claude/claudia.json "
            "(create the file/key if missing)."
        )
        if len(shown_keywords) % 3 == 0:
            user_hint, claude_hint = dismiss_hint("teach")
            system_text += "\n" + user_hint
            context += "\n" + claude_hint
        colored = "\n".join(f"\033[38;5;160m{line}\033[0m" for line in system_text.split("\n"))
        return {"additionalContext": context, "systemMessage": colored}

    if shown_keywords != set(state["shown_keywords"]) or revealed_commands != set(state["revealed_commands"]):
        state["shown_keywords"] = list(shown_keywords)
        state["revealed_commands"] = list(revealed_commands)
        save_state(session_id, state)

    return None


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    proactivity, experience = load_config()
    session_id = input_data.get("session_id", "default")
    result = check(input_data, proactivity, experience)
    if result and stop_lock_acquire(session_id):
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
