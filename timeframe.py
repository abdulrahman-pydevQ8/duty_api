import datetime
from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta

date = datetime.datetime.now()

class Tframe:
    def __init__(self, main_dic, main_keys,main_keys_days, week_end, month_name):
        global date
        self.date = date
        self.main_dic = main_dic
        self.main_keys = main_keys
        self.main_keys_days = main_keys_days
        self.week_end = week_end
        self.month_name = month_name

    #  fills the variables with the dates from the next month
    def next_nmonth(self, m):  # fills the dates of the next 30 days
        days_of_the_month = calendar.monthrange(self.date.year, self.date.month)[1]
        days_till_end_month = days_of_the_month - self.date.day
        self.date = self.date + timedelta(days=days_till_end_month + 1)
        self.date = datetime.datetime(self.date.year - 1, 12, 1)
        self.date = self.date + relativedelta(months=m)
        days_of_the_month = calendar.monthrange(self.date.year, self.date.month)[1]
        self.month_name = self.date.strftime('%B')
        days_name = []
        print('this is before the i loop')
        print(self.date)

        for i in range(days_of_the_month):
            new_d = self.date + timedelta(days=i)
            self.main_keys_days.append(new_d.strftime("%A"))
            if new_d.strftime("%A") == "Friday" or new_d.strftime("%A") == "Saturday":
                self.week_end.append(str(int(new_d.strftime("%d"))))
            days_name.append(new_d.strftime("%A"))
            new_d = str(int(new_d.strftime("%d")))
            new_d = f"{new_d}"
            self.main_dic.update({new_d: []})
            self.main_keys.append(new_d)
    def next_month(self):
        days_of_the_month = calendar.monthrange(self.date.year, self.date.month)[1]
        days_till_end_month = days_of_the_month - self.date.day
        self.date = self.date + timedelta(days=days_till_end_month + 1)
        days_of_the_month = calendar.monthrange(self.date.year, self.date.month)[1]
        self.month_name = self.date.strftime('%B')
        days_name = []

        for i in range(days_of_the_month):
            new_d = self.date + timedelta(days=i)
            self.main_keys_days.append(new_d.strftime("%A"))
            if new_d.strftime("%A") == "Friday" or new_d.strftime("%A") == "Saturday":
                self.week_end.append(str(int(new_d.strftime("%d"))))
            days_name.append(new_d.strftime("%A"))
            new_d = str(int(new_d.strftime("%d")))
            new_d = f"{new_d}"
            self.main_dic.update({new_d: []})
            self.main_keys.append(new_d)
