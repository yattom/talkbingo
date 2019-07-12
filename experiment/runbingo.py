#coding: utf-8

import random
import math
from collections import namedtuple

Cell = namedtuple('Cell', ['category', 'number', 'marked', 'shared_interests'], defaults=(False, None))

SHEET_CREATION_TRIAL = 40

class Sheet:
    CATEGORIES = ('STAR', 'CIRCLE', 'BOX', 'TRI')
    def __init__(self, sheet_number, cells):
        self._sheet_number = sheet_number
        self._cells = [Cell(c[0], c[1]) for c in cells]
        self._size = int(math.sqrt(len(self._cells)))

    def cells(self, loc):
        return self._cells[loc]

    def columns(self):
        return [[self._cells[r * self._size + c] for c in range(self._size)]
                for r in range(self._size)]

    def rows(self):
        return [[self._cells[r * self._size + c] for r in range(self._size)]
                for c in range(self._size)]


def create_sheet(sheet_number, size):
    numbers = [i + 1 for i in range(size * size) if i + 1 != sheet_number]
    random.shuffle(numbers)
    numbers = numbers[:int(size * size / 2)] + [sheet_number] + numbers[int(size * size / 2):]
    categories = shuffled_categories(size)
    cells = [Cell(categories.pop(0), numbers.pop(0), False, []) for i in range(size * size)]
    return Sheet(sheet_number, cells)


def shuffled_categories(size):
    categories = list(Sheet.CATEGORIES * int(size * size / len(Sheet.CATEGORIES) + 1))[:size * size]
    random.shuffle(categories)
    distributed = [None] * (size * size)
    for c in categories:
        available = [i for i in range(len(distributed)) if distributed[i] is None]
        trys = []
        for i in range(SHEET_CREATION_TRIAL):
            loc = random.choice(available)
            trial = distributed[:]
            trial[loc] = c
            trys.append((loc, eval_category_distribution_for_sheet(trial, size)))
        best_loc = sorted(trys, key=lambda v: v[1])[0][0]
        # print(f'best: {best_loc}, trys: {trys}, available: {available}')
        distributed[best_loc] = c
    return distributed


def mark_cell(sheet1, sheet2, category, shared_interests):
    candidates1 = []
    for n, c in enumerate(sheet1._cells):
        if c.number == sheet2._sheet_number and c.category == category:
            candidates1.append(n)
    assert len(candidates1) <= 1
    candidates2 = []
    for n, c in enumerate(sheet2._cells):
        if c.number == sheet1._sheet_number and c.category == category:
            candidates2.append(n)
    assert len(candidates2) <= 1
    if candidates1 and candidates2:
        sheet1._cells[candidates1[0]] = sheet1._cells[candidates1[0]]._replace(marked=True)
        sheet2._cells[candidates2[0]] = sheet2._cells[candidates2[0]]._replace(marked=True)

def eval_category_distribution_for_sheet(categories, size):
    columns = [[categories[r * size + c] for c in range(size)]
                for r in range(size)]
    rows = [[categories[r * size + c] for r in range(size)]
                for c in range(size)]
    val = sum([eval_category_distribution(line)
               for line in columns + rows])
    return val / (size * 2)

def eval_category_distribution(categories):
    LACKING_CATEGORY_WEIGHT = 10
    UNEVEN_CATEGORIES_WEIGHT = 1
    count = dict()
    for c in categories:
        if c is None: continue
        count[c] = count.get(c, 0) + 1
    if not count: return 0
    return ((len(Sheet.CATEGORIES) - len(count)) * LACKING_CATEGORY_WEIGHT +
            (max(count.values()) - min(count.values())) * UNEVEN_CATEGORIES_WEIGHT)

import pytest


@pytest.fixture
def sheet1():
    return Sheet(1, [('STAR', 9), ('STAR', 5)])

@pytest.fixture
def sheet2():
    return Sheet(9, [('STAR', 1), ('CIRCLE', 1)])

@pytest.fixture
def many_sheets():
    return [create_sheet(10, 7) for i in range(50)]


def is_category_distributed(cells):
    categories = dict()
    for c in cells:
        categories[c.category] = categories.get(c.category, 0) + 1
    evaluation = (len(categories) == 4 and
                  max(categories.values()) - min(categories.values()) <= 1)
    if not evaluation:
        print(f'uneven categories: {categories}')
    return evaluation


class TestSheet:
    class TestMark:
        def test_最初は埋まっていない(self, sheet1):
            assert not sheet1.cells(0).marked

        def test_2人で同じマスを埋める(self, sheet1, sheet2):
            mark_cell(sheet1, sheet2, 'STAR', ['共通点1', '共通点2'])
            assert sheet1.cells(0).marked
            assert sheet2.cells(0).marked

        def test_2人で同じマスを埋める_指定以OOは埋めない(self, sheet1, sheet2):
            mark_cell(sheet1, sheet2, 'STAR', ['共通点1', '共通点2'])
            assert not sheet1.cells(1).marked
            assert not sheet2.cells(1).marked

        def test_カテゴリが違うと埋められない(self, sheet1, sheet2):
            mark_cell(sheet1, sheet2, 'CIRCLE', ['共通点1', '共通点2'])
            assert not sheet1.cells(0).marked
            assert not sheet2.cells(0).marked

        def test_双方に一致しないと違うと埋められない(self, sheet1, sheet2):
            mark_cell(sheet1, sheet2, 'CIRCLE', ['共通点1', '共通点2'])
            assert not sheet1.cells(0).marked
            assert not sheet2.cells(0).marked

    class TestCreation:
        def test_7x7(self):
            sheet = create_sheet(10, 7)
            assert sheet._sheet_number == 10
            assert len(sheet._cells) == 7 * 7
            assert sheet._cells[3 * 7 + 3].number == sheet._sheet_number

        def test_カテゴリが分散する(self, many_sheets):
            for sheet in many_sheets:
                assert is_category_distributed(sheet._cells)

        def test_番号が分散する(self, many_sheets):
            number_positions = set()
            for sheet in many_sheets:
                for i, c in enumerate(sheet._cells):
                    number_positions.add((i, c.number))
            assert len(number_positions) >= (7 * 7) ** 2 * 0.5, '番号と登場箇所の組み合わせがほぼユニークになること'

        def test_行列ごとにカテゴリが分散する(self, many_sheets):
            invalid_count = 0
            for sheet in many_sheets:
                for line in sheet.columns() + sheet.rows():
                    if not is_category_distributed(line):
                        invalid_count += 1
                        break
            assert invalid_count < len(many_sheets) * 0.1

def test_shuffled_categories():
    sut = shuffled_categories(3)
