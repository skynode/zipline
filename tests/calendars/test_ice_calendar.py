from unittest import TestCase
import pandas as pd

from .test_trading_calendar import ExchangeCalendarTestBase
from zipline.utils.calendars.exchange_calendar_ice import ICEExchangeCalendar


class ICECalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = 'ice'
    calendar_class = ICEExchangeCalendar

    def test_hurricane_sandy_one_day(self):
        self.assertFalse(
            self.calendar.is_session(pd.Timestamp("2012-10-29", tz='UTC'))
        )

        # ICE wasn't closed on day 2 of hurricane sandy
        self.assertTrue(
            self.calendar.is_session(pd.Timestamp("2012-10-30", tz='UTC'))
        )

    def test_2016_holidays(self):
        # 2016 holidays:
        # new years: 2016-01-01
        # good friday: 2016-03-25
        # christmas (observed): 2016-12-26

        for date in ["2016-01-01", "2016-03-25", "2016-12-26"]:
            self.assertFalse(
                self.calendar.is_session(pd.Timestamp(date, tz='UTC'))
            )

    def test_2016_early_closes(self):
        # 2016 early closes
        # mlk: 2016-01-18
        # presidents: 2016-02-15
        # mem day: 2016-05-30
        # independence day: 2016-07-04
        # labor: 2016-09-05
        # thanksgiving: 2016-11-24
        for date in ["2016-01-18", "2016-02-15", "2016-05-30", "2016-07-04",
                     "2016-09-05", "2016-11-24"]:
            dt = pd.Timestamp(date, tz='UTC')
            self.assertTrue(dt in self.calendar.early_closes)

            market_close = self.calendar.schedule.loc[dt].market_close
            self.assertEqual(
                13,     # all ICE early closes are 1 pm local
                market_close.tz_localize("UTC").tz_convert(
                    self.calendar.tz
                ).hour
            )

    def test_daylight_savings(self):
        # 2004 daylight savings switches:
        # Sunday 2004-04-04 and Sunday 2004-10-31

        # make sure there's no weirdness around calculating the next day's
        # session's open time.
        for date_pair in [((2004, 4, 4), "2004-04-05"),
                          ((2004, 10, 31), "2004-11-01")]:
            next_day = pd.Timestamp(date_pair[1], tz='UTC')
            the_open = self.calendar.schedule.loc[next_day].market_open

            localized_open = the_open.tz_localize("UTC").tz_convert(
                self.calendar.tz
            )

            self.assertEqual(
                date_pair[0],
                (localized_open.year, localized_open.month, localized_open.day)
            )

    def test_sanity_check_session_lengths(self):
        # make sure that no session is longer than 22 hours
        for session in self.calendar.all_sessions:
            o, c = self.calendar.open_and_close_for_session(session)
            delta = c - o
            self.assertTrue((delta.seconds / 3600) <= 22)
