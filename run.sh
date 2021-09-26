reset
python3 webull.py crawl $1
./deploy.sh
python3 analyzer.py fullreport > latest_report
