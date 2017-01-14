"""Render tabular output.

This is designed for screen or text-file output, using a fixed-width font.

"""

from collections import defaultdict

class Column_spec(object):
    """Details of a table column.

    Public attributes:
      align         -- 'left' or 'right'
      right_padding -- int

    """
    def __init__(self, align='left', right_padding=1):
        self.align = align
        self.right_padding = right_padding

    def render(self, s, width):
        if self.align == 'left':
            s = s.ljust(width)
        elif self.align == 'right':
            s = s.rjust(width)
        return s + " " * self.right_padding

class Table(object):
    """Render tabular output.

    Normal use:

      tbl = Table(row_count=3)
      tbl.add_heading('foo')
      i = tbl.add_column(align='left', right_padding=3)
      tbl.set_column_values(i, ['a', 'b'])
      [...]
      print '\n'.join(tbl.render())

    """
    def __init__(self, row_count=None):
        self.col_count = 0
        self.row_count = row_count
        self.headings = []
        self.columns = []
        self.cells = defaultdict(str)

    def set_row_count(self, row_count):
        """Change the table's row count."""
        self.row_count = row_count

    def add_heading(self, heading, span=1):
        """Specify a column or column group heading.

        To leave a column with no heading, pass the empty string.

        To allow a heading to cover multiple columns, pass the 'span' parameter
        and don't add headings for the rest of the covered columns.

        """
        self.headings.append((heading, span))

    def add_column(self, **kwargs):
        """Add a column to the table.

        align         -- 'left' (default) or 'right'
        right_padding -- int (default 1)

        Returns the column id

        Right padding is the number of spaces to leave between this column and
        the next.

        (The last column should have right padding 1, so that the heading can
        use the full width if necessary.)

        """
        column = Column_spec(**kwargs)
        self.columns.append(column)
        column_id = self.col_count
        self.col_count += 1
        return column_id

    def get_column(self, column_id):
        """Retrieve a column object given its id.

        You can use this to change the column's attributes after adding it.

        """
        return self.columns[column_id]

    def set_column_values(self, column_id, values):
        """Specify the values for a column.

        column_id -- as returned by add_column()
        values    -- iterable

        str() is called on the values.

        If values are not supplied for all rows, the remaining rows are left
        blank. If too many values are supplied, the excess values are ignored.

        """
        for row, value in enumerate(values):
            self.cells[row, column_id] = str(value)

    def render(self):
        """Render the table.

        Returns a list of strings.

        Each line has no trailing whitespace.

        Lines which would be wholly blank are omitted.

        """
        def column_values(col):
            return [self.cells[row, col] for row in xrange(self.row_count)]

        result = []

        cells = self.cells
        widths = [max(map(len, column_values(i)))
                  for i in xrange(self.col_count)]
        col = 0
        heading_line = []
        for heading, span in self.headings:
            # width available for the heading
            width = (sum(widths[col:col+span]) +
                     sum(self.columns[i].right_padding
                         for i in range(col, col+span)) - 1)
            shortfall = len(heading) - width
            if shortfall > 0:
                width += shortfall
                # Make the leftmost column in the span wider to fit the heading
                widths[col] += shortfall
            heading_line.append(heading.ljust(width))
            col += span
        result.append(" ".join(heading_line).rstrip())

        for row in xrange(self.row_count):
            l = []
            for col, (column, width) in enumerate(zip(self.columns, widths)):
                l.append(column.render(cells[row, col], width))
            line = "".join(l).rstrip()
            if line:
                result.append(line)
        return result

