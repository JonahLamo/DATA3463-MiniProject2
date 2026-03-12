import os
from podium import Podium
from athletes import Athletes
from countries import Countries

if os.path.exists('DATA3463-MiniProject2\out\podium.csv'):
    Podium()
if os.path.exists('DATA3463-MiniProject2\out\athletes.csv'):
    Athletes()
if os.path.exists('DATA3463-MiniProject2\out\athletes.csv'):
    Countries()
