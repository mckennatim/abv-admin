#!/bin/bash
#sed -i 's/\r$//' restart-abv.sh convert line endings
# restart-abv.sh
cd /home/abv/public_html/abv-admin/song-app/server
pkill -f "python app.py"
sleep 2
nohup python app.py &
echo "ABV server restarted in $FLASK_ENV mode"