import unittest
import csv
import os

from firmware.taupunkt import taupunkt


class TestTaupunkt(unittest.TestCase):

    def test_upper_left(self):
        self.assertEqual(round(taupunkt(T=30, r=30), 1), 10.5)

    def test_lower_right(self):
        self.assertEqual(round(taupunkt(T=10, r=95), 1), 9.2)

    def test_taupunkt_table(self):
        this_dir = os.path.dirname(__file__)
        with open(f'{this_dir}/taupunkttabelle.csv', newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            csv_reader.__next__()  # skip first row (title stuff)
            r_row = csv_reader.__next__()[1:-1]  # read rows
            for row in csv_reader:
                temp = int(row[0])
                for r_i, result in enumerate(row[1:-1]):
                    r = int(r_row[r_i][:-2])
                    self.assertEqual(round(taupunkt(T=temp, r=r), 1), float(result.replace(',', '.')))
