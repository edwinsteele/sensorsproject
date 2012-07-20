from django.http import HttpResponse

import datetime

def home(request):
        return HttpResponse("Hello, world. You're at the poll index.")


def year_detail(request, year):
        return HttpResponse("You're at the year detail for %s." % (year,))

def month_detail(request, year, month):
        return HttpResponse("You're at the month detail for %s/%s" % (month, year))

def day_detail(request, year, month, day):
        try:
            ymd = datetime.date(int(year), int(month), int(day))
        except ValueError:
            s = "Bad date format"
            ymd = None
        return HttpResponse("You're at the day detail for %s/%s/%s (%s)." % (day, month, year, ymd))
