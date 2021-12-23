from crontab import CronTab

with CronTab(user='aidan') as cron:
    job = cron.new(command='source ~/movie-booking-api/venv/bin/activate; $(which python3) ~/movie-booking-api/manage.py runscript heehaw.py')
    job.every(3).hours()

print('cron.write() was just executed')