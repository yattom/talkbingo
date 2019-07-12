#coding: utf-8

import random
import math
from collections import namedtuple

Cell = namedtuple('Cell', ['category', 'number', 'marked', 'shared_interests'], defaults=(False, None))


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

    def dump(self):
        out = []
        for r in range(self._size):
            out.append(' '.join([c.category[0] + f'{c.number:02}' for c in self._cells[r * self._size : (r + 1) * self._size]]))
        return '\n'.join(out)

def create_sheet(sheet_number, size):
    while True:
        numbers = [i + 1 for i in range(size * size) if i + 1 != sheet_number]
        random.shuffle(numbers)
        numbers = numbers[:int(size * size / 2)] + [sheet_number] + numbers[int(size * size / 2):]

        categories = shuffled_categories(size)
        cells = [Cell(categories.pop(0), numbers.pop(0), False, []) for i in range(size * size)]

        candidate = Sheet(sheet_number, cells)
        if all([is_category_distributed(line) for line in candidate.columns() + candidate.rows()]):
            return candidate

def shuffled_categories(size):
    # return shuffled_categories_by_weight(size)
    # return shuffled_categories_by_random(size)
    return shuffled_categories_by_placing(size)


def shuffled_categories_by_random(size):
    categories = list(Sheet.CATEGORIES * int(size * size / len(Sheet.CATEGORIES) + 1))[:size * size]
    random.shuffle(categories)
    return categories


def shuffled_categories_by_weight(size):
    SHEET_CREATION_TRIAL = 10
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


def shuffled_categories_by_placing(size):
    '''
    各カテゴリを各列と行に1個ずつ置いた上で
    あとを詰めていく
    '''
    distributed = [None] * (size * size)
    for category in Sheet.CATEGORIES:
        cols = list(range(size))
        random.shuffle(cols)
        for r in range(size):
            c = cols[r]
            if distributed[r * size + c]:
                available = [cc for cc in range(size) if distributed[r * size + cc] is None]
                if not available:
                    break
                c = random.choice(available)
            distributed[r * size + c] = category

    open_cells = len([c for c in distributed if c is None])
    filling_categories = list(Sheet.CATEGORIES * int(open_cells / len(Sheet.CATEGORIES) + 1))[:open_cells]
    random.shuffle(filling_categories)
    for i in range(len(distributed)):
        if distributed[i] is None:
            distributed[i] = filling_categories.pop(0)
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


def is_category_distributed(cells):
    categories = dict()
    for c in cells:
        categories[c.category] = categories.get(c.category, 0) + 1
    # evaluation = (len(categories) == len(Sheet.CATEGORIES) and
    #               max(categories.values()) - min(categories.values()) <= 1)
    evaluation = len(categories) == len(Sheet.CATEGORIES)
    # if not evaluation:
    #     print(f'uneven categories: {categories}')
    return evaluation


import pytest


@pytest.fixture
def sheet1():
    return Sheet(1, [('STAR', 9), ('STAR', 5)])

@pytest.fixture
def sheet2():
    return Sheet(9, [('STAR', 1), ('CIRCLE', 1)])

@pytest.fixture
def many_sheets():
    return [create_sheet(i + 1, 7) for i in range(50)]


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

        def test_カテゴリがランダムに配置される(self, many_sheets):
            category_positions = set()
            for sheet in many_sheets:
                for i, c in enumerate(sheet._cells):
                    category_positions.add((i, c.category))
            assert len(category_positions) >= (7 * 7) * len(Sheet.CATEGORIES) * 0.9, 'カテゴリと登場箇所の組み合わせがほぼユニークになること'

        def test_番号がランダムに配置される(self, many_sheets):
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
                        print(sheet.dump())
                        invalid_count += 1
                        break
            assert invalid_count == 0

