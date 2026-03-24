#!/bin/bash

PHASE=$1
FEATURE=$2
TASK=$3

# Check if arguments are missing
if [ -z "$PHASE" ] || [ -z "$FEATURE" ] || [ -z "$TASK" ]; then
    echo "Usage: ./pr-scratch-merge-to-feature.sh <PHASE> <FEATURE> <TASK>"
    exit 1
fi

BASE_BRANCH="$PHASE/$FEATURE/main"
HEAD_BRANCH="$PHASE/$FEATURE/$TASK"

# Removed the '^' symbols for compatibility
PR_TITLE="$PHASE $FEATURE: $TASK → Main"
PR_BODY="Merge $HEAD_BRANCH into $BASE_BRANCH. This PR implements and tests the work for $TASK under $FEATURE in $PHASE."

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
