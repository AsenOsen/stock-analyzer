reset
# collect data
echo $(date) crawling started
python3 webull.py crawl "$1"
echo $(date) crawling finished
# create report
echo $(date) report started
python3 -u analyzer.py report > ./report
cp ./report $(printf './reports/report_%(%Y_%m_%d)T')
echo $(date) report created
# deploy bot with new data
python3 analyzer.py latestdata --to-file ./tgbot/data.json
./tgbot/deploy.sh "$2"