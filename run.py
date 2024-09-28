import re
import curses
import os

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return ''

def write_words(file_path, words):
    with open(file_path, 'w', encoding='utf-8') as file:
        for word in words:
            file.write(word + '\n')

def extract_words(text):
    return set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))

def select_file(stdscr, directory):
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select a file to open [q to quit]:", curses.color_pair(2))

        for idx in range(min(20, len(files))):
            file = files[idx]
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 1, 0, file)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, file)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(files) - 1:
            current_row += 1
        elif key == ord('\n'):
            return os.path.join(directory, files[current_row])
        elif key == ord('q'):
            return None

def curses_menu(stdscr, known_words, unknown_words, file_list):
    current_column = 0  # 0 = unknown words, 1 = known words, 2 = file selector
    current_row = 0
    scroll_offsets = [0, 0, 0]  # Offsets for scrolling each column

    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    max_height, max_width = stdscr.getmaxyx()
    max_displayable_items = max_height - 3

    while True:
        stdscr.clear()

        # Display Unknown Words
        stdscr.addstr(0, 0, f"Study [{len(unknown_words)}]:", curses.color_pair(2))
        for idx in range(scroll_offsets[0], min(scroll_offsets[0] + max_displayable_items // 1, len(unknown_words))):
            word = unknown_words[idx]
            if idx == current_row and current_column == 0:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx - scroll_offsets[0] + 1, 0, word)  # Adjust index for scrolling
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx - scroll_offsets[0] + 1, 0, word)

        # Display Known Words
        stdscr.addstr(0, 30, f"Known [{len(known_words)}]:", curses.color_pair(2))
        for idx in range(scroll_offsets[1], min(scroll_offsets[1] + max_displayable_items // 1, len(known_words))):
            word = known_words[idx]
            if idx == current_row and current_column == 1:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx - scroll_offsets[1] + 1, 30, word)  # Adjust index for scrolling
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx - scroll_offsets[1] + 1, 30, word)

        # Display File Selector
        stdscr.addstr(0, 60, "Add words:", curses.color_pair(2))
        for idx in range(scroll_offsets[2], min(scroll_offsets[2] + max_displayable_items // 3, len(file_list))):
            file_name = file_list[idx]
            if idx == current_row and current_column == 2:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx - scroll_offsets[2] + 1, 60, file_name)  # Adjust index for scrolling
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx - scroll_offsets[2] + 1, 60, file_name)

        # Instruction line
        instruction_line = "[TAB to switch columns, ENTER to select, Q to quit]"
        stdscr.addstr(max_displayable_items + 2, 0, instruction_line, curses.color_pair(2))

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP:
            if current_column == 0 and current_row > 0:
                current_row -= 1
            elif current_column == 1 and current_row > 0:
                current_row -= 1
            elif current_column == 2 and current_row > 0:
                current_row -= 1

        elif key == curses.KEY_DOWN:
            if current_column == 0 and current_row < len(unknown_words) - 1:
                current_row += 1
            elif current_column == 1 and current_row < len(known_words) - 1:
                current_row += 1
            elif current_column == 2 and current_row < len(file_list) - 1:
                current_row += 1

        elif key == ord('\t'):  # Change column
            current_column = (current_column + 1) % 3
            current_row = 0  # Reset row when switching columns

        elif key == ord('\n'):
            if current_column == 0 and current_row < len(unknown_words):
                selected_word = unknown_words[current_row]
                known_words.insert(0, selected_word)  # Insert at the top
                unknown_words.remove(selected_word)
                write_words('data/known_words.txt', known_words)
                write_words('data/unknown_words.txt', unknown_words)
                current_row = 0  # Reset row after selection
                scroll_offsets[0] = 0  # Reset scroll offset for unknown words

            elif current_column == 1 and current_row < len(known_words):
                selected_word = known_words[current_row]
                known_words.remove(selected_word)
                unknown_words.append(selected_word)
                write_words('data/known_words.txt', known_words)
                write_words('data/unknown_words.txt', unknown_words)
                current_row = 0  # Reset row after selection
                scroll_offsets[1] = 0  # Reset scroll offset for known words

            elif current_column == 2 and current_row < len(file_list):
                selected_file = os.path.join('learn', file_list[current_row])
                if not os.path.isfile(selected_file):
                    continue

                try:
                    with open(selected_file, 'r', encoding='utf-8') as file:
                        text = file.read()
                except Exception as e:
                    continue

                new_words = extract_words(text)
                write_words('data/current_file.txt', [text])

                all_unknown_words = set(unknown_words) | (new_words - set(known_words))
                write_words('data/unknown_words.txt', list(all_unknown_words))

                # Delete the selected file
                os.remove(selected_file)
                current_row = 0  # Reset row after processing a file
                scroll_offsets[2] = 0  # Reset scroll offset for file list

        elif key == ord('q'):
            break

        # Handle scrolling for each column
        if current_column == 0:
            if current_row < scroll_offsets[0]:
                scroll_offsets[0] = current_row
            elif current_row >= scroll_offsets[0] + (max_displayable_items // 3):
                scroll_offsets[0] = current_row - (max_displayable_items // 3) + 1

        elif current_column == 1:
            if current_row < scroll_offsets[1]:
                scroll_offsets[1] = current_row
            elif current_row >= scroll_offsets[1] + (max_displayable_items // 3):
                scroll_offsets[1] = current_row - (max_displayable_items // 3) + 1

        elif current_column == 2:
            if current_row < scroll_offsets[2]:
                scroll_offsets[2] = current_row
            elif current_row >= scroll_offsets[2] + (max_displayable_items // 3):
                scroll_offsets[2] = current_row - (max_displayable_items // 3) + 1


def main():
    known_words_file = 'data/known_words.txt'
    unknown_words_file = 'data/unknown_words.txt'
    learn_directory = 'learn'

    known_words = list(read_file(known_words_file).splitlines())
    unknown_words = list(read_file(unknown_words_file).splitlines())
    file_list = os.listdir(learn_directory)

    curses.wrapper(curses_menu, known_words, unknown_words, file_list)

if __name__ == "__main__":
    main()
