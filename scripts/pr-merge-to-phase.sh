#!/bin/bash

PHASE=$1
FEATURE=$2

# Check if arguments are missing
if [ -z "$PHASE" ] || [ -z "$FEATURE" ]; then
    echo "Usage: ./pr-scratch-merge-to-phase.sh <PHASE> <FEATURE>"
    exit 1
fi

BASE_BRANCH="$PHASE/main"
HEAD_BRANCH="$PHASE/$FEATURE/main"

# Removed the '^' symbols for compatibility
PR_TITLE="$PHASE $FEATURE: $TASK → Main"
PR_BODY="Merge $HEAD_BRANCH into $BASE_BRANCH. This PR implements and tests all completed work for $FEATURE in $PHASE. Approved."

echo "Creating PR: $PR_TITLE"

gh pr create \
  --base "$BASE_BRANCH" \
  --head "$HEAD_BRANCH" \
  --title "$PR_TITLE" \
  --body "$PR_BODY"

# 2. Self-Approve (Note: This only works if your repo settings allow self-approval)
# gh pr review --approve

# 3. Merge (with a cleanup of the local/remote branch)
# gh pr merge --auto --squash --delete-branch
