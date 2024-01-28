import datetime
import math
import re

from PIL import ImageDraw, ImageFont

import color
import homeassistant
from config import Config


class Outdoor:
    def __init__(self, draw: ImageDraw):
        self.draw: ImageDraw = draw
        self.config = Config().get(__class__.__name__)
        self.font = '/usr/share/fonts/truetype/msttcorefonts/verdana.ttf'
        self.boldfont = '/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf'
        self.xpos = 1080
        self.ypos = 30
        self.width = 200
        self.height = 80
        self.pixels_per_second = 0.0
        self.pixels_per_degree = 0.0
        self.min_temp = 1000.0
        self.max_temp = -1000.0

    def load_foreca(self):
        # ort:Taby-kyrka time:1706446800 cloud:3 precip:0 snow:0 temp:5 wind:5 humidity: tid:01-28T14:00
        result = []
        with open("foreca.txt") as f:
            for line in f.readlines():
                m = re.search(r'time:(\d+).+precip:(\d+).+snow:(\d+) temp:(-?\d+)', line)
                if m:
                    timestamp, _, _, temp = m.groups()
                    timestring = datetime.datetime.fromtimestamp(int(timestamp)).astimezone().isoformat()
                    result.append({'state': temp,
                                   'last_changed': timestring})
        return result

    def find_range(self, data: dict) -> (int, int):
        for entity in data:
            for entry in entity:
                state: str = entry['state']
                if state.startswith('u'):  # unknown or unavailable
                    continue
                temp = float(state)
                if temp > self.max_temp:
                    self.max_temp = temp
                if temp < self.min_temp:
                    self.min_temp = temp

    def background(self, start_time: datetime.datetime, end_time: datetime.datetime):
        x = self.xpos
        y = self.ypos
        w = self.width
        h = self.height
        self.draw.line((x, y, x, y + h), fill=color.mgray, width=1)
        self.draw.line((x, y + h, x + w, y + h), fill=color.mgray, width=1)
        f = ImageFont.truetype(self.font, 11)
        s = str(self.max_temp)
        _, _, string_width, string_height = f.getbbox(s)
        self.draw.text((x - string_width - 2, y - string_height / 2), s, font=f, fill=color.dgray)
        s = str(self.min_temp)
        _, _, string_width, string_height = f.getbbox(s)
        self.draw.text((x - string_width - 2, y + h - string_height / 2), f'{self.min_temp}', font=f, fill=color.dgray)
        for t in range(math.floor(self.min_temp), math.ceil(self.max_temp)):
            if t % 5:
                continue
            if self.min_temp < t < self.max_temp:
                temp_offset = (t - self.min_temp) * self.pixels_per_degree
                self.draw.line((x, y + h - temp_offset, x + w, y + h - temp_offset), fill=color.lred, width=1)
        # vertical 6-hour lines
        vertical = start_time.astimezone()
        vertical = vertical.replace(second=0, minute=0, hour=vertical.hour - (vertical.hour % 6))
        vertical += datetime.timedelta(hours=6)
        f = ImageFont.truetype(self.font, 11)
        text_width = f.getlength('00')
        while vertical < end_time.astimezone():
            time_offset = (vertical - start_time).total_seconds() * self.pixels_per_second
            self.draw.line((x + time_offset, y, x + time_offset, y + h), fill=color.lgray, width=1)
            self.draw.text((x + time_offset - text_width/2, y + h), f'{vertical.hour:02d}', font=f, fill=color.dgray)
            vertical += datetime.timedelta(hours=6)
        # now line
        now = datetime.datetime.now().astimezone()
        time_offset = (now - start_time).total_seconds() * self.pixels_per_second
        self.draw.line((x + time_offset, y, x + time_offset, y + h), fill=color.mgray, width=1)

    def render(self):
        data = homeassistant.get_history([self.config['entity'],])
        data.append(self.load_foreca())
        self.find_range(data)
        now_time = datetime.datetime.now(datetime.timezone.utc)
        end_time = now_time + datetime.timedelta(days=1)
        start_time = now_time - datetime.timedelta(days=1)
        self.pixels_per_second = self.width / (86400 * 2)
        self.pixels_per_degree = self.height / (self.max_temp - self.min_temp)
        self.background(start_time, end_time)
        last_time = start_time
        seconds_per_point = (86400 * 2) / self.width * 2
        for entity in data:
            coordinates = []
            for entry in entity:
                state: str = entry['state']
                if state.startswith('u'):  # unknown or unavailable
                    continue
                change_time = datetime.datetime.fromisoformat(entry['last_changed'])
                if (change_time - last_time).total_seconds() < seconds_per_point:
                    continue
                last_time = change_time
                temp = float(state)
                if not temp:
                    continue
                x = (change_time - start_time).total_seconds() * self.pixels_per_second
                y = self.height - ((temp - self.min_temp) * self.pixels_per_degree)
                coordinates.append((x + self.xpos, y + self.ypos))
            self.draw.line(coordinates, fill=color.red, width=1)

        current_temp = float(data[0][-1]['state'])
        f = ImageFont.truetype(self.boldfont, 28)
        text = f'{current_temp:.1f}°C'
        text_width = f.getlength(text)
        left_margin = (self.width - text_width) / 2
        self.draw.text((self.xpos + left_margin, -6), text, font=f, fill=color.dgray)
