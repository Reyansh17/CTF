import time,datetime

now = datetime.datetime.now()
ttl = (now.hour + 2) * 60 * 60 + (now.minute + 25) * 60 + now.second

print(ttl)