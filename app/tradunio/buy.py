#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import date as dt
import re
import requests


def players_onsale(user_id):
    """
    Returns the football players currently on sale
    @return: [[name, team, min_price, market_price, points, date, owner, position]]
    :param community_id:
    """
    # get from database