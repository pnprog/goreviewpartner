"""Standard layout of fixed handicap stones.

This follows the rules from the GTP spec.

"""

def max_free_handicap_for_board_size(board_size):
    """Return the maximum number of stones for place_free_handicap command."""
    return board_size * board_size - 1

def max_fixed_handicap_for_board_size(board_size):
    """Return the maximum number of stones for fixed_handicap command."""
    if board_size <= 7:
        return 0
    if board_size > 25:
        raise ValueError
    if board_size % 2 == 0 or board_size == 7:
        return 4
    else:
        return 9

handicap_pattern = [
    ['00', '22'],
    ['00', '22', '20'],
    ['00', '22', '20', '02'],
    ['00', '22', '20', '02', '11'],
    ['00', '22', '20', '02', '10', '12'],
    ['00', '22', '20', '02', '10', '12', '11'],
    ['00', '22', '20', '02', '10', '12', '01', '21'],
    ['00', '22', '20', '02', '10', '12', '01', '21', '11'],
]

def handicap_points(number_of_stones, board_size):
    """Return the handicap points for a given number of stones and board size.

    Returns a list of pairs (row, col), length 'number_of_stones'.

    Raises ValueError if there isn't a placement pattern for the specified
    number of handicap stones and board size.

    """
    if number_of_stones > max_fixed_handicap_for_board_size(board_size):
        raise ValueError
    if number_of_stones < 2:
        raise ValueError
    if board_size < 13:
        altitude = 2
    else:
        altitude = 3
    pos = {'0' : altitude,
           '1' : (board_size - 1) / 2,
           '2' : board_size - altitude - 1}
    return [(pos[s[0]], pos[s[1]])
            for s in handicap_pattern[number_of_stones-2]]
