#!/bin/bash
# restart-abv.sh
cd /home/tryit/public_html/abv/server
pkill -f "python app.py"
sleep 2
nohup python app.py &
echo "ABV server restarted"