reset
# collect data
python3 webull.py crawl "$1"
# create report
echo $(date) report started
python3 -u analyzer.py report > ./report
cp ./report $(printf './reports/report_%(%Y_%m_%d)T')
echo $(date) report created
# deploy bot with new data
python3 analyzer.py latestdata --to-file ./tgbot/data.json
./tgbot/deploy.sh "$2"