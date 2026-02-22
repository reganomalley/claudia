#!/usr/bin/env bash
#
# Claudia: create-domain.sh
# Scaffolds a new knowledge domain for community contributors.
#
# Usage: ./scripts/create-domain.sh <domain-name>
# Example: ./scripts/create-domain.sh architecture
#
# Creates:
#   skills/claudia-<name>/SKILL.md
#   skills/claudia-<name>/references/   (empty directory with .gitkeep)

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <domain-name>"
    echo "Example: $0 architecture"
    echo ""
    echo "Creates a new Claudia knowledge domain with template files."
    exit 1
fi

DOMAIN_NAME="$1"
DOMAIN_DIR="skills/claudia-${DOMAIN_NAME}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/.claude-plugin/plugin.json" ]; then
    echo "Error: Run this from the claudia project root, or pass the domain name."
    echo "Expected to find .claude-plugin/plugin.json"
    exit 1
fi

# Check if domain already exists
if [ -d "$PROJECT_DIR/$DOMAIN_DIR" ]; then
    echo "Error: Domain '$DOMAIN_NAME' already exists at $DOMAIN_DIR/"
    exit 1
fi

echo "Creating domain: claudia-${DOMAIN_NAME}"

# Create directory structure
mkdir -p "$PROJECT_DIR/$DOMAIN_DIR/references"

# Create SKILL.md template
cat > "$PROJECT_DIR/$DOMAIN_DIR/SKILL.md" << SKILL_EOF
---
name: claudia-${DOMAIN_NAME}
description: >
  ${DOMAIN_NAME^} knowledge domain for Claudia. Use this skill when the user asks about
  [FILL IN: what topics this domain covers].
  Triggers on phrases like [FILL IN: "keyword1", "keyword2", "keyword3"].
version: 0.1.0
---

# Claudia ${DOMAIN_NAME^} Domain

## Overview

[FILL IN: 2-3 sentences. What does this domain help with? Be opinionated about the right defaults.]

## Decision Tree

[FILL IN: Primary decision tree for this domain. Use the tree format:]

\`\`\`
What are you trying to do?
├── Option A
│   └── Recommendation
├── Option B
│   └── Recommendation
└── Not sure
    └── Default recommendation
\`\`\`

## Quick Comparisons

| Need | First Choice | When to Upgrade |
|------|-------------|----------------|
| [situation] | [recommendation] | [when to move beyond it] |

## Common Mistakes

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| [mistake] | [consequence] | [solution] |

## Deep References

For detailed guidance, load:
- \`references/[topic].md\` -- [description]

## Response Format

When advising on ${DOMAIN_NAME}:
1. **Recommendation** (specific, concrete)
2. **Why** (reasoning, not just opinion)
3. **Trade-offs** (what you give up)
4. **Next step** (one action to take)
SKILL_EOF

# Create .gitkeep in references
touch "$PROJECT_DIR/$DOMAIN_DIR/references/.gitkeep"

# Create a reference template
cat > "$PROJECT_DIR/$DOMAIN_DIR/references/TEMPLATE.md" << REF_EOF
# [Reference Topic Title]

## Overview

[What does this reference cover? When should Claude load this file?]

## [Main Section]

[Deep content goes here. Be opinionated, use tables, use examples.]

## [Comparison Section]

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| [option] | [pros] | [cons] | [use case] |

## [Patterns / Anti-Patterns]

**Do:**
- [good practice]

**Don't:**
- [anti-pattern]: [why it's bad]

## [Decision Framework]

[When to choose each option. Be concrete.]
REF_EOF

echo ""
echo "Created:"
echo "  $DOMAIN_DIR/SKILL.md          (fill in the template)"
echo "  $DOMAIN_DIR/references/        (add reference .md files here)"
echo "  $DOMAIN_DIR/references/TEMPLATE.md  (reference file template)"
echo ""
echo "Next steps:"
echo "  1. Edit SKILL.md -- fill in description, triggers, decision trees"
echo "  2. Add reference files in references/"
echo "  3. Update skills/claudia-mentor/SKILL.md routing table"
echo "  4. Delete references/TEMPLATE.md when you have real references"
echo ""
echo "See existing domains (e.g., skills/claudia-databases/) for examples."
