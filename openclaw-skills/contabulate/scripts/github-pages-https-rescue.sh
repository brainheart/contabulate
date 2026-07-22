#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: github-pages-https-rescue.sh --repo brainheart/name --host sub.contabulate.org [options]

Diagnose and optionally rescue a stuck GitHub Pages HTTPS certificate for a
Contabulate subdomain. By default it only inspects. Add --reset to remove/re-add
Pages CNAME. Add --cloudflare-fallback to switch the Cloudflare DNS record to
proxied if GitHub remains stuck after watching.

Options:
  --repo OWNER/REPO              GitHub repo, e.g. brainheart/thucydides-contabulate
  --host HOST                    Custom domain, e.g. thucydides.contabulate.org
  --zone ZONE_ID                 Cloudflare zone id (default: contabulate.org zone)
  --watch-minutes N              Watch after reset before fallback (default: 30)
  --reset                        Remove/re-add GitHub Pages custom domain
  --cloudflare-fallback          If still stuck, proxy the Cloudflare DNS record
  --log PATH                     Log path (default: /tmp/<host>_https_rescue.log)
  --callback TEXT                Send OpenClaw system event on completion/failure
  --help                         Show help
EOF
}

REPO=""
HOST=""
ZONE="fc4b35b6a9eb82e69f58afeeca7987f5"
WATCH_MINUTES=30
DO_RESET=0
DO_CF_FALLBACK=0
LOG=""
CALLBACK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --zone) ZONE="$2"; shift 2 ;;
    --watch-minutes) WATCH_MINUTES="$2"; shift 2 ;;
    --reset) DO_RESET=1; shift ;;
    --cloudflare-fallback) DO_CF_FALLBACK=1; shift ;;
    --log) LOG="$2"; shift 2 ;;
    --callback) CALLBACK="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$REPO" || -z "$HOST" ]]; then
  usage >&2
  exit 2
fi

if [[ -z "$LOG" ]]; then
  safe_host=${HOST//[^A-Za-z0-9_.-]/_}
  LOG="/tmp/${safe_host}_https_rescue.log"
fi

touch "$LOG"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
notify() {
  local text="$1"
  [[ -z "$CALLBACK" ]] && return 0
  if command -v openclaw >/dev/null 2>&1; then
    openclaw system event --mode now --expect-final --text "$CALLBACK: $text" || true
  fi
}

require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 127; }; }
require gh
require curl
require openssl
require dig
require python3

cert_subject() {
  echo | openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null || true
}

pages_json() { gh api "repos/$REPO/pages"; }
cert_state() { pages_json | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("https_certificate") or {}).get("state") or "none")'; }

inspect_state() {
  log "== Pages =="
  pages_json | python3 -m json.tool | tee -a "$LOG"
  log "== DNS =="
  { dig +short CNAME "$HOST" @1.1.1.1; dig +short A "$HOST" @1.1.1.1; dig +short AAAA "$HOST" @1.1.1.1; dig +short CAA "$HOST" @1.1.1.1; } | tee -a "$LOG"
  log "== Cert =="
  cert_subject | tee -a "$LOG"
  log "== HTTPS headers =="
  curl -sSI --max-time 20 "https://$HOST" | sed -n '1,12p' | tee -a "$LOG" || true
}

wait_for_pages_built_no_cname() {
  for _ in {1..30}; do
    local pg_status cname
    pg_status=$(pages_json | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status") or "")')
    cname=$(pages_json | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cname") or "")')
    log "Pages after remove: status=${pg_status:-unknown} cname=${cname:-none}"
    [[ "$pg_status" == "built" && -z "$cname" ]] && return 0
    sleep 10
  done
  return 1
}

reset_cname() {
  log "Removing GitHub Pages custom domain for $REPO"
  gh api -X PUT "repos/$REPO/pages" -f cname='' >/dev/null
  wait_for_pages_built_no_cname || log "Timed out waiting for no-CNAME build; continuing cautiously"
  log "Re-adding custom domain $HOST"
  gh api -X PUT "repos/$REPO/pages" -f cname="$HOST" >/dev/null
}

watch_for_approval() {
  local iterations=$(( WATCH_MINUTES * 3 ))
  (( iterations < 1 )) && iterations=1
  for ((i=1; i<=iterations; i++)); do
    local state
    state=$(cert_state)
    local subject
    subject=$(echo | openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null | openssl x509 -noout -subject 2>/dev/null | sed 's/^subject=//' || true)
    log "watch $i/$iterations: state=$state cert=${subject:-none}"
    if [[ "$state" == "approved" ]]; then
      log "GitHub cert approved; enabling HTTPS enforcement"
      gh api -X PUT "repos/$REPO/pages" -f https_enforced=true >/dev/null
      notify "$HOST GitHub Pages certificate approved and HTTPS enforcement enabled"
      return 0
    fi
    sleep 20
  done
  return 1
}

cloudflare_fallback() {
  log "Switching Cloudflare DNS record to proxied fallback"
  python3 - "$ZONE" "$HOST" <<'PY' | tee -a "$LOG"
import json, os, sys, urllib.request
zone, host = sys.argv[1:3]
cred_path = os.path.expanduser('~/.config/cloudflare/credentials.json')
cred = json.load(open(cred_path))
token = cred.get('api_token') or cred.get('token') or cred.get('key') or next(iter(cred.values()))
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
def req(method, url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)
base = f'https://api.cloudflare.com/client/v4/zones/{zone}/dns_records'
records = req('GET', f'{base}?name={host}')['result']
if len(records) != 1:
    raise SystemExit(f'expected 1 DNS record for {host}, got {len(records)}')
rec = records[0]
payload = {k: rec[k] for k in ['type', 'name', 'content', 'ttl']}
payload['proxied'] = True
out = req('PUT', f'{base}/{rec["id"]}', payload)['result']
print(json.dumps({k: out.get(k) for k in ['type','name','content','proxied','ttl']}, indent=2))
PY
  sleep 30
  local code
  code=$(curl -skI --max-time 20 "https://$HOST" | awk 'NR==1{print $2}')
  local subject
  subject=$(echo | openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null | openssl x509 -noout -subject 2>/dev/null | sed 's/^subject=//' || true)
  log "Cloudflare fallback verify: http=${code:-none} cert=${subject:-none}"
  if [[ "$code" =~ ^(200|301|302)$ ]]; then
    notify "$HOST HTTPS works through Cloudflare proxied fallback; GitHub certificate remains $(cert_state)"
    return 0
  fi
  notify "$HOST Cloudflare fallback attempted but verification failed; inspect $LOG"
  return 1
}

log "Starting HTTPS rescue for repo=$REPO host=$HOST log=$LOG"
inspect_state
if [[ "$DO_RESET" -eq 1 ]]; then
  reset_cname
  inspect_state
  if watch_for_approval; then exit 0; fi
fi

state=$(cert_state)
if [[ "$state" == "approved" ]]; then
  log "Cert already approved; enabling HTTPS enforcement"
  gh api -X PUT "repos/$REPO/pages" -f https_enforced=true >/dev/null
  notify "$HOST certificate already approved; HTTPS enforcement enabled"
  exit 0
fi

if [[ "$DO_CF_FALLBACK" -eq 1 ]]; then
  cloudflare_fallback
else
  log "GitHub certificate state is $state; no fallback requested"
  notify "$HOST HTTPS rescue ended with GitHub certificate state=$state; no fallback requested"
fi
