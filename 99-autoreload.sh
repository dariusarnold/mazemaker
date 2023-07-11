
#!/bin/sh

while :; do
    nginx -t && nginx -s reload
    sleep 6h
done &