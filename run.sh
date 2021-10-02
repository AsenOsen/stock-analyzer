# collect data
reset
python3 webull.py crawl "$1"
# deploy bot with new data
./deploytgbot.sh "$2"
# create actualreport
echo $(date) report started
python3 analyzer.py fullreport > latest_report
echo $(date) report created