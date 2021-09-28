reset
python3 webull.py crawl "$1"
./deploytgbot.sh "$2"
echo $(date) report started
python3 analyzer.py fullreport > latest_report
echo $(date) report created