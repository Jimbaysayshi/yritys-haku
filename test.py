import os
import time
path = 'C:\\Users\\fitaptoiv-jt\\AppData\\Local\\Projects\\yritys-api\\uploads'
file = '4969d85f1b52498d8368c7a398c136f2.xls'

now = time.time()
for f in os.listdir(path):
    real_path = os.path.join(path, f)
    if os.stat(real_path).st_mtime < now - 10 * 60 * 1000:
        os.remove(real_path)
