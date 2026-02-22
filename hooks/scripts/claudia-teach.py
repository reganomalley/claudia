#!/usr/bin/env python3
"""
Claudia: claudia-teach.py
Stop hook that fires after every Claude response.
Scans for technology keywords and offers teaching moments for beginners.
Advisory only (exit 0 with additionalContext), never blocks.
Session-aware dedup to avoid repeating the same keyword tip.
"""

import json
import os
import re
import sys

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
    },
    "frameworks": {
        "Next.js": "a React framework for building full-stack web apps",
        "React": "a JavaScript library for building user interfaces",
        "Vue": "a progressive JavaScript framework for building UIs",
        "Svelte": "a compiler that turns components into efficient JavaScript",
        "Astro": "a framework for building content-focused websites",
        "Express": "a minimal Node.js web framework for building APIs",
        "FastAPI": "a modern Python web framework for building APIs",
    },
    "tools": {
        "Docker": "a tool for packaging apps into containers that run anywhere",
        "Kubernetes": "a system for managing containerized apps at scale",
        "Terraform": "infrastructure-as-code tool for provisioning cloud resources",
        "GitHub Actions": "CI/CD automation built into GitHub",
        "Webpack": "a module bundler for JavaScript applications",
        "Vite": "a fast build tool and dev server for modern web projects",
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


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_teach_state_{session_id}.json")


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_state(session_id, shown):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown), f)
    except IOError:
        pass


def load_config():
    """Load proactivity from ~/.claude/claudia.json, experience from claudia-context.json."""
    proactivity = "moderate"
    experience = "intermediate"

    config_path = os.path.expanduser("~/.claude/claudia.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
                proactivity = data.get("proactivity", proactivity)
        except (json.JSONDecodeError, IOError):
            pass

    context_path = os.path.expanduser("~/.claude/claudia-context.json")
    if os.path.exists(context_path):
        try:
            with open(context_path) as f:
                data = json.load(f)
                experience = data.get("experience", experience)
        except (json.JSONDecodeError, IOError):
            pass

    return proactivity, experience


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    message = input_data.get("last_assistant_message", "")

    if not message:
        sys.exit(0)

    # Check proactivity and experience
    proactivity, experience = load_config()

    # Only fire on moderate or high proactivity
    if proactivity == "low":
        sys.exit(0)

    is_beginner = experience == "beginner"

    # Non-beginners only get teaching on high proactivity
    if not is_beginner and proactivity != "high":
        sys.exit(0)

    shown = load_state(session_id)
    tips = []

    # Scan for technology keywords
    for category, keywords in KEYWORDS.items():
        for keyword, description in keywords.items():
            # Word-boundary match, case-insensitive
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, message, re.IGNORECASE):
                if keyword.lower() not in shown:
                    shown.add(keyword.lower())
                    tips.append(
                        f"I noticed we're talking about {keyword} ({description}). "
                        f"Want me to explain more? Just say `/claudia:explain {keyword.lower()}`"
                    )
                    # Only one keyword tip per response to avoid noise
                    break
        if tips:
            break

    # Scan for error patterns (only for beginners)
    if not tips and is_beginner:
        for pattern, description in ERROR_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                error_key = f"error-{description}"
                if error_key not in shown:
                    shown.add(error_key)
                    tips.append(
                        f"That looks like {description}. "
                        f"If you're not sure what it means, say `/claudia:explain` and paste the error."
                    )
                    break

    if tips:
        save_state(session_id, shown)
        tip_text = "\n".join(f"\U0001f4a1 Claudia: {tip}" for tip in tips)
        output = json.dumps({"additionalContext": tip_text})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
