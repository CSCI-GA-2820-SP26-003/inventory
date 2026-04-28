#!/usr/bin/env bash

# This script is used for a manual deploy to production by triggering the tekton cd pipeline. Normally a deploy is triggered from the Webhook after a merge to the master branch. 
set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
die()     { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }

# ── preflight checks ─────────────────────────────────────────────────────────
header "=== Inventory Manual Deploy ==="

command -v oc  &>/dev/null || die "'oc' not found. Install the OpenShift CLI and re-run."
command -v tkn &>/dev/null || die "'tkn' not found. Install the Tekton CLI and re-run."

info "Checking OpenShift authentication..."
OC_USER=$(oc whoami 2>/dev/null) \
  || die "Not logged in to OpenShift. Run 'oc login <cluster-url>' and re-run."
OC_PROJECT=$(oc project -q 2>/dev/null) \
  || die "Could not determine current project. Run 'oc project <name>' and re-run."

success "Logged in as '${OC_USER}' — project '${OC_PROJECT}'"

# ── apply manifests ───────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

header "── Applying PostgreSQL manifests ──"
oc apply -f "${REPO_ROOT}/k8s/postgres/"
success "PostgreSQL manifests applied."

header "── Applying Tekton pipeline manifests ──"
# Apply workspace, tasks, and pipeline (files directly in .tekton/)
oc apply -f "${REPO_ROOT}/.tekton/workspace.yaml"
oc apply -f "${REPO_ROOT}/.tekton/tasks.yaml"
oc apply -f "${REPO_ROOT}/.tekton/pipeline.yaml"
success "Tekton pipeline manifests applied."

header "── Applying Tekton event listener / triggers ──"
oc apply -f "${REPO_ROOT}/.tekton/events/"
success "Event listener manifests applied."

header "── Applying application routes ──"
oc apply -f "${REPO_ROOT}/k8s/route.yaml"
success "Routes applied."

# ── wait for postgres to be ready ────────────────────────────────────────────
header "── Waiting for PostgreSQL to be ready ──"
info "Waiting up to 120 s for postgres StatefulSet rollout..."
oc rollout status statefulset/postgres --timeout=120s \
  && success "PostgreSQL is ready." \
  || warn "PostgreSQL rollout did not finish in time — continuing anyway."

# ── select git ref ───────────────────────────────────────────────────────────
header "── Git ref ──"
read -rp "Branch or commit SHA to deploy (press Enter to use default: master): " GIT_REF
GIT_REF="${GIT_REF:-master}"
info "Deploying ref: '${GIT_REF}'"

# ── trigger pipeline ──────────────────────────────────────────────────────────
header "── Triggering inventory-cd-pipeline ──"
info "Starting pipeline run (logs will stream below)..."
echo ""

tkn pipeline start inventory-cd-pipeline \
  --use-param-defaults \
  -p GIT_REF="${GIT_REF}" \
  -w name=pipeline-workspace,claimName=pipeline-pvc \
  --showlog

echo ""

# ── post-run status ───────────────────────────────────────────────────────────
header "── Pipeline run summary ──"
LAST_RUN=$(tkn pipelinerun list --limit 1 -o name 2>/dev/null | head -1)

if [[ -n "${LAST_RUN}" ]]; then
  tkn pipelinerun describe "${LAST_RUN#*/}"
  STATUS=$(tkn pipelinerun describe "${LAST_RUN#*/}" --output jsonpath='{.status.conditions[0].reason}' 2>/dev/null || true)
  if [[ "${STATUS}" == "Succeeded" ]]; then
    success "Pipeline completed successfully."
  else
    die "Pipeline finished with status: ${STATUS}. Check 'tkn pipelinerun logs ${LAST_RUN#*/}' for details."
  fi
else
  warn "Could not retrieve pipeline run status."
fi
