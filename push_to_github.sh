#!/usr/bin/env bash
# Copyright 2026 Rishabh Ginotra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# One-Command Personal GitHub Push Script (Option B)
# Usage:
#   ./push_to_github.sh <github_repo_url_or_owner/repo> [personal_email]
# Example:
#   ./push_to_github.sh https://github.com/rishabhginotra/social-media-writer-agent.git

set -euo pipefail

TARGET_REPO="${1:-}"
PERSONAL_EMAIL="${2:-}"

if [[ -z "${TARGET_REPO}" ]]; then
  echo "Usage: ./push_to_github.sh <https://github.com/USERNAME/REPO.git | USERNAME/REPO> [personal_email]"
  exit 1
fi

if [[ -n "${PERSONAL_EMAIL}" ]]; then
  git config user.email "${PERSONAL_EMAIL}"
  git commit --amend --reset-author --no-edit >/dev/null 2>&1 || true
fi

echo "==> Running pre-push Unit Tests & Golden Evaluation Gate..."
python3 -m unittest discover -s tests/unit -v >/dev/null
python3 tests/eval/run_evaluation.py >/dev/null
echo "==> All unit tests and golden evaluation checks passed (100%)."

if [[ "${TARGET_REPO}" != http* && "${TARGET_REPO}" != git@* ]]; then
  if command -v gh >/dev/null 2>&1; then
    echo "==> Creating or verifying GitHub repository '${TARGET_REPO}' via GitHub CLI (gh)..."
    gh repo view "${TARGET_REPO}" >/dev/null 2>&1 || gh repo create "${TARGET_REPO}" --public --source=. --remote=origin
  fi
  REMOTE_URL="https://github.com/${TARGET_REPO%.git}.git"
else
  REMOTE_URL="${TARGET_REPO}"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "${REMOTE_URL}"
else
  git remote add origin "${REMOTE_URL}"
fi

echo "==> Pushing main branch to ${REMOTE_URL}..."
git branch -M main
git push -u origin main

echo "==> Successfully pushed social-media-writer-agent to ${REMOTE_URL}!"
