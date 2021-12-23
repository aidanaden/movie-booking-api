from crontab import CronTab

with CronTab(user='aidan') as cron:
    job = cron.new(command='source /home/aidan/movie-booking-api/venv/bin/activate; $(which python3) /home/aidan/movie-booking-api/manage.py runscript /home/aidan/movie-booking-api/heehaw.py')
    job.every(3).hours()

print('cron.write() was just executed')