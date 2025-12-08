#!/usr/bin/env python3
import os
import re
import sys

if os.path.exists(".git/MERGE_HEAD"):
    sys.exit(0)

with open(sys.argv[1]) as f:
    msg = f.read().strip()

pattern = (
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+"
)
if not re.match(pattern, msg):
    print("Error: Commit message must follow Conventional Commits format")
    print("Examples: feat: add new feature, fix(auth): resolve login bug, feat!: breaking change")
    sys.exit(1)
