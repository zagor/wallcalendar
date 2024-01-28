import datetime
import subprocess

from PIL import ImageFont, ImageDraw
import color
import config
import namn


class Calendar:
    class CalendarEntry:
        def __init__(self, line: str):
            sdate, stime, edate, etime, self.event, self.calendar = line.strip().split('\t')
            self.start_time = datetime.datetime.fromisoformat(f'{sdate}T{stime}:00')
            self.end_time = datetime.datetime.fromisoformat(f'{edate}T{etime}:00')
            self.days: int = (self.end_time - self.start_time).days
            self.allday: bool = (self.end_time - self.start_time).total_seconds() > 86300
            self.config = config.Config().get("Calendar")
            self.color = self.config['calendars'].get(self.calendar, color.black)

        def __lt__(self, other) -> bool:
            # sort long multi-day events highest
            if self.days > other.days:
                return True

            # sort early events before later
            if self.start_time < other.start_time:
                return True

    def __init__(self, draw: ImageDraw, xsize: int, ysize: int):
        self.draw = draw
        self.xsize = xsize
        self.ysize = ysize
        self.day_width = round(xsize / 7)
        self.day_height = round(ysize / 5)
        self.font = '/usr/share/fonts/truetype/msttcorefonts/verdana.ttf'
        self.boldfont = '/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf'
        self.config = config.Config().get("Calendar")
        self.fetch_calendars()

    def fetch_calendars(self):
        cal_args = []
        for c in self.config['calendars'].keys():
            cal_args.append('--calendar')
            cal_args.append(f'"{c}"')

        today = datetime.date.today()
        first_day = today - datetime.timedelta(days=today.weekday())
        last_day = first_day + datetime.timedelta(days=28)
        command = ['gcalcli', '--nocache', *cal_args, 'agenda',
                   '--tsv', '--nocolor', '--details', 'calendar',
                   first_day.isoformat(), last_day.isoformat()]
        with open("cal.tsv", "w") as file:
            subprocess.run(command, stdout=file)

    def draw_background(self):
        ##############
        # dagens datum
        ##############
        today = datetime.date.today()
        firstmonday = today - datetime.timedelta(days=today.weekday())
        string = today.strftime('%A %e %B').capitalize()
        f = ImageFont.truetype(self.boldfont, 65)
        _, _, w, h = f.getbbox(string)
        xpos = self.xsize/2 - w/2
        self.draw.text((xpos, -15), string, font=f, fill=color.black)

        #############
        # dagens namn
        #############
        names = namn.namnsdag.get(today.strftime('%m%d'), 'Inget namn!')
        string = ', '.join(names)
        f = ImageFont.truetype(self.boldfont, 35)
        w = f.getlength(string)
        xpos = self.xsize/2 - w/2
        self.draw.text((xpos, h), string, font=f, fill=color.dgray)

        ################
        # rita kalendern
        ################

        # veckodagar
        self.draw.rectangle((0, self.day_height - 20, self.xsize - 1, self.day_height), fill=color.mblue)
        t = firstmonday
        f = ImageFont.truetype(self.boldfont, 18)
        for x in range(0, self.xsize, self.day_width):
            self.draw.text((x + 60, self.day_height - 22), t.strftime('%A'), font=f, fill=color.black)
            t += datetime.timedelta(days=1)

        # gör idag gul
        t = today.weekday()
        self.draw.rectangle((t * self.day_width + 1, self.day_height + 16,
                            (t + 1) * self.day_width - 1, self.day_height * 2 - 1),
                            fill=color.yellow)

        # dagnummer
        f = ImageFont.truetype(self.boldfont, 70)
        t = firstmonday
        for w in range(1, 5):
            y = w * self.day_height
            #self.draw.rectangle((0, y, self.xsize - 1, y + 15), outline=color.mblue, fill=color.lblue)
            self.draw.line((0, y, self.xsize - 1, y), fill=color.mblue)
            for d in range(0, 7):
                string = t.strftime('%e')
                if int(string) == today.day:
                    c = color.dyellow
                else:
                    c = color.lgray
                #self.draw.text((self.day_width * d + self.day_width - 20, y), string, font=f, fill=color.black)
                self.draw.text((self.day_width * d + 40, y + 40), string, font=f, fill=c)
                t += datetime.timedelta(days=1)

        # verikala dagavgränsare
        for x in range(self.day_width, self.xsize, self.day_width):
            self.draw.line((x, self.day_height - 20, x, self.ysize), fill=color.mblue)

        # veckonummer
        f = ImageFont.truetype(self.font, 11)
        t = firstmonday
        for w in range(1, 5):
            y = w * self.day_height
            self.draw.text((2, y), t.strftime('%V'), font=f, fill=color.blue)
            t += datetime.timedelta(weeks=1)

    def fit_string(self, string: str, f: ImageFont, days=1):
        while f.getbbox(string)[2] > self.day_width * days:
            string = string[:-1]
        return string

    def draw_events(self):
        with open('cal.tsv') as f:
            elist = [self.CalendarEntry(line) for line in f]
        events = sorted(elist)
        events_per_day = {}
        today = datetime.date.today()
        firstmonday = today - datetime.timedelta(days=today.weekday())
        f = ImageFont.truetype(self.boldfont, 12)
        for e in events:
            days_ahead = (e.start_time.date() - firstmonday).days
            row = int(days_ahead / 7) + 1
            column = days_ahead % 7
            x = column * self.day_width
            y = row * self.day_height
            y += events_per_day.get(days_ahead, 0) * 18
            events_per_day[days_ahead] = events_per_day.get(days_ahead, 0) + 1
            for day in range(1, e.days):
                day += days_ahead
                events_per_day[day] = events_per_day.get(day, 0) + 1
            #print(f'Rendering event {e.start_time} {e.event} {days_ahead}')
            if e.days == 0:
                string = f'{e.start_time.strftime("%H:%M")} {e.event}'
                string = self.fit_string(string, f)
                self.draw.text((x+3, y+16), string, font=f, fill=e.color)
            while e.days > 0:
                box = (x + 2, y + 16, x + e.days * self.day_width - 7, y + 32)
                self.draw.rectangle(box, fill=e.color)
                string = self.fit_string(e.event, f, e.days)
                self.draw.text((x+3, y+16), string, font=f, fill=color.white)
                drawn_days = 7 - e.start_time.weekday()
                if e.start_time.weekday() + e.days > 6:
                    # we have a wrap
                    e.start_time += datetime.timedelta(days=drawn_days)
                    row += 1
                    column = 0
                    x = column * self.day_width
                    y = row * self.day_height
                e.days -= drawn_days

    def render(self):
        self.draw_background()
        self.draw_events()
