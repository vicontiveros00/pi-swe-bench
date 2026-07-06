import sys
import traceback

import solution


def run():
    assert solution.roman_to_int("III") == 3
    assert solution.roman_to_int("IV") == 4
    assert solution.roman_to_int("IX") == 9
    assert solution.roman_to_int("LVIII") == 58
    assert solution.roman_to_int("MCMXCIV") == 1994


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
