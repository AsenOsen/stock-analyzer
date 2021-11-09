SERVER="root@193.124.112.120"
HOME_DIR="/root/tgbot"
BOT_TOKEN=$1
SCRIPT_DIR=$(dirname "$(realpath -s "$0")")
# prepare clean system
ssh ${SERVER} "apt update && apt install -y python3.8 python3-pip rsync && mkdir -p ${HOME_DIR}"
# install bot in system
rsync -r ${SCRIPT_DIR}/* ${SERVER}:${HOME_DIR}
ssh ${SERVER} "pip3 install -r ${HOME_DIR}/requirements.txt"
ssh ${SERVER} "cat > /etc/systemd/system/tgbot.service <<- EOM
[Unit]
Description=Telegram StocksAnalyst
After=network.target

[Service]
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -u ${HOME_DIR}/bot.py ${BOT_TOKEN}
Restart=always

[Install]
WantedBy=default.target
EOM"
ssh ${SERVER} "systemctl daemon-reload && systemctl enable tgbot && systemctl restart tgbot"