TUNNEL_ID=$1
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: registry-dev.kinnoo.ai
    service: http://127.0.0.1:8000
  - service: http_status:404
EOF
