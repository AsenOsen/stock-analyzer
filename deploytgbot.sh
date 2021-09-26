SERVER="root@193.124.112.120"
HOME_DIR="/root/tgbot"
BOT_TOKEN=$1
# prepare clean system
ssh ${SERVER} "apt update && apt install -y mongodb python3.8 python3-pip rsync && mkdir -p ${HOME_DIR}"
# db transfer
latestCollection=$(mongo mongodb://localhost/webull --eval 'db.getCollectionNames()' | grep tickers | sort | tail -n1 | xargs)
mongodump -h=localhost -d=webull --collection=$latestCollection --out db
rsync -r ./db ${SERVER}:${HOME_DIR}
rm -rf db
ssh ${SERVER} "mongorestore ${HOME_DIR}/db && rm -rf ${HOME_DIR}/db"
# install bot in system
rsync -r ./analyzer.py ./tgbot.py ./tgbot ./requirements.txt ${SERVER}:${HOME_DIR}
ssh ${SERVER} "pip3 install -r ${HOME_DIR}/requirements.txt"
ssh ${SERVER} "cat > /etc/systemd/system/tgbot.service <<- EOM
[Unit]
Description=Telegram StocksAnalyst
After=network.target

[Service]
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -u ${HOME_DIR}/tgbot.py ${BOT_TOKEN}
Restart=always

[Install]
WantedBy=default.target
EOM"
ssh ${SERVER} "systemctl daemon-reload && systemctl enable tgbot && systemctl restart tgbot"