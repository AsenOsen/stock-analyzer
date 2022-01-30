reset
# collect data
echo $(date) crawling started
./crawler.py crawl "$1"
echo $(date) crawling finished
# create report
echo $(date) report started
./analyzer.py report > ./report
cp ./report $(printf './reports/report_%(%Y_%m_%d)T')
echo $(date) report created
# deploy bot with new data
./analyzer.py latestdata --to-file ./tgbot/data.json
./tgbot/deploy.sh "$2"