"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller.
Parts of this code were originally based on the gtp module 
in the Deep-Go project by Isaac Henrion and Amos Storkey 
at the University of Edinburgh.
"""
import traceback
import numpy as np
import re
from sys import stdin, stdout, stderr
from typing import Any, Callable, Dict, List, Tuple

from board_base import (
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    GO_COLOR,
    GO_POINT,
    PASS,
    MAXSIZE,
    coord_to_point,
    opponent,
)
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine


class GtpConnection:
    def __init__(
        self, go_engine: GoEngine, board: GoBoard, debug_mode: bool = True
    ) -> None:
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board:
            Represents the current board state.
        """
        self._debug_mode: bool = debug_mode
        self.go_engine = go_engine
        self.board: GoBoard = board
        self.game_status = "playing"
        self.commands: Dict[str, Callable[[List[str]], None]] = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-rules_captured_count": self.gogui_rules_captured_count_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
        }

        # argmap is used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap: Dict[str, Tuple[int, str]] = {
            "boardsize": (1, "Usage: boardsize INT"),
            "komi": (1, "Usage: komi FLOAT"),
            "known_command": (1, "Usage: known_command CMD_NAME"),
            "genmove": (1, "Usage: genmove {w,b}"),
            "play": (2, "Usage: play {b,w} MOVE"),
            "legal_moves": (1, "Usage: legal_moves {w,b}"),
        }

    def write(self, data: str) -> None:
        stdout.write(data)

    def flush(self) -> None:
        stdout.flush()

    def start_connection(self) -> None:
        """
        Start a GTP connection.
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command: str) -> None:
        """
        Parse command string and execute it
        """
        if len(command.strip(" \r\t")) == 0:
            return
        if command[0] == "#":
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements: List[str] = command.split()
        if not elements:
            return
        command_name: str = elements[0]
        args: List[str] = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error("Unknown command")
            stdout.flush()

    def has_arg_error(self, cmd: str, argnum: int) -> bool:
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg: str) -> None:
        """Write msg to the debug stream"""
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg: str) -> None:
        """Send error msg to stdout"""
        stdout.write("? {}\n\n".format(error_msg))
        stdout.flush()

    def respond(self, response: str = "") -> None:
        """Send response to stdout"""
        stdout.write("= {}\n\n".format(response))
        stdout.flush()

    def reset(self, size: int) -> None:
        """
        Reset the board to empty board of given size
        """
        self.game_status = "playing"
        self.board.reset(size)

    def board2d(self) -> str:
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args: List[str]) -> None:
        """Return the GTP protocol version being used (always 2)"""
        self.respond("2")

    def quit_cmd(self, args: List[str]) -> None:
        """Quit game and exit the GTP interface"""
        self.respond()
        exit()

    def name_cmd(self, args: List[str]) -> None:
        """Return the name of the Go engine"""
        self.respond(self.go_engine.name)

    def version_cmd(self, args: List[str]) -> None:
        """Return the version of the  Go engine"""
        self.respond(str(self.go_engine.version))

    def clear_board_cmd(self, args: List[str]) -> None:
        """clear the board"""
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args: List[str]) -> None:
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args: List[str]) -> None:
        self.respond("\n" + self.board2d())

    def komi_cmd(self, args: List[str]) -> None:
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args: List[str]) -> None:
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args: List[str]) -> None:
        """list all supported GTP commands"""
        self.respond(" ".join(list(self.commands.keys())))

    def legal_moves_cmd(self, args: List[str]) -> None:
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color: str = args[0].lower()
        color: GO_COLOR = color_to_int(board_color)
        moves: List[GO_POINT] = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves: List[str] = []
        for move in moves:
            coords: Tuple[int, int] = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = " ".join(sorted(gtp_moves))
        self.respond(sorted_moves)

    """
    ==========================================================================
    Assignment 1 - game-specific commands start here
    ==========================================================================
    """
    """
    ==========================================================================
    Assignment 1 - commands we already implemented for you
    ==========================================================================
    """

    def gogui_analyze_cmd(self, args: List[str]) -> None:
        """We already implemented this function for Assignment 1"""
        self.respond(
            "pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
            "pstring/Side to Play/gogui-rules_side_to_move\n"
            "pstring/Final Result/gogui-rules_final_result\n"
            "pstring/Board Size/gogui-rules_board_size\n"
            "pstring/Rules GameID/gogui-rules_game_id\n"
            "pstring/Show Board/gogui-rules_board\n"
        )

    def gogui_rules_game_id_cmd(self, args: List[str]) -> None:
        """We already implemented this function for Assignment 1"""
        self.respond("Ninuki")

    def gogui_rules_board_size_cmd(self, args: List[str]) -> None:
        """We already implemented this function for Assignment 1"""
        self.respond(str(self.board.size))

    def gogui_rules_side_to_move_cmd(self, args: List[str]) -> None:
        """We already implemented this function for Assignment 1"""
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args: List[str]) -> None:
        """We already implemented this function for Assignment 1"""
        size = self.board.size
        str = ""
        for row in range(size - 1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                # str += '.'
                point = self.board.board[start + i]
                if point == BLACK:
                    str += "X"
                elif point == WHITE:
                    str += "O"
                elif point == EMPTY:
                    str += "."
                else:
                    assert False
            str += "\n"
        self.respond(str)

    """
    ==========================================================================
    Assignment 1 - game-specific commands you have to implement or modify
    ==========================================================================
    """

    def check_point_is_win(self, point: GO_POINT) -> GO_COLOR or bool:
        """Function to check is a point have 5 connected point"""
        self.debug_msg(format_point(point_to_coord(point, self.board.size)))
        bord2D = GoBoardUtil.get_twoD_board(self.board)
        num_rows, num_cols = bord2D.shape

        def is_within_board(coord):
            return 0 <= coord[0] < num_rows and 0 <= coord[1] < num_cols

        current_coord = point_to_coord(point, self.board.size)
        current_coord = (
            ((self.board.size - 1) - (current_coord[0] - 1)),
            current_coord[1] - 1,
        )
        current_color = bord2D[current_coord]

        def int_to_color(num):
            if num == 1:
                return "black"
            elif num == 2:
                return "white"
            else:
                return "ERROR"

        count = 1
        UP = True
        DOWN = True
        # Up and Down
        for i in range(1, 6):
            up_coord = (current_coord[0], current_coord[1] + i)
            if is_within_board(up_coord) and current_color == bord2D[up_coord] and UP:
                count += 1
            else:
                UP = False

            down_coord = (current_coord[0], current_coord[1] - i)
            if (
                is_within_board(down_coord)
                and current_color == bord2D[down_coord]
                and DOWN
            ):
                count += 1
            else:
                DOWN = False

            if count >= 5:
                return int_to_color(current_color)

        count = 1
        # L and R
        L = True
        R = True
        for i in range(1, 6):
            right_coord = (current_coord[0] + i, current_coord[1])
            left_coord = (current_coord[0] - i, current_coord[1])

            if (
                is_within_board(right_coord)
                and current_color == bord2D[right_coord]
                and R
            ):
                count += 1
            else:
                R = False

            if (
                is_within_board(left_coord)
                and current_color == bord2D[left_coord]
                and L
            ):
                count += 1
            else:
                R = False

            if count >= 5:
                return int_to_color(current_color)

        count = 1
        # Diag 1
        L = True
        R = True
        for i in range(1, 6):
            right_coord = (current_coord[0] + i, current_coord[1] + i)
            left_coord = (current_coord[0] - i, current_coord[1] - i)

            if (
                is_within_board(right_coord)
                and current_color == bord2D[right_coord]
                and R
            ):
                count += 1
            else:
                R = False

            if (
                is_within_board(left_coord)
                and current_color == bord2D[left_coord]
                and L
            ):
                count += 1
            else:
                R = False
            if count >= 5:
                return int_to_color(current_color)

        count = 1
        L = True
        R = True
        # Diag 2
        for i in range(1, 6):
            right_coord = (current_coord[0] + i, current_coord[1] - i)
            left_coord = (current_coord[0] - i, current_coord[1] + i)

            if (
                is_within_board(right_coord)
                and current_color == bord2D[right_coord]
                and R
            ):
                count += 1
            else:
                R = False

            if (
                is_within_board(left_coord)
                and current_color == bord2D[left_coord]
                and L
            ):
                count += 1
            else:
                R = False

            if count >= 5:
                return int_to_color(current_color)

        return False

    def cap_process(self, point: GO_POINT) -> None:
        """
        Function to process a point move and check if any stones are captured.
        """

        bord2D = GoBoardUtil.get_twoD_board(self.board)
        current_coord = point_to_coord(point, self.board.size)
        current_coord = (
            ((self.board.size - 1) - (current_coord[0] - 1)),
            current_coord[1] - 1,
        )
        current_color = bord2D[current_coord]

        num_rows, num_cols = bord2D.shape

        def is_within_board(coord):
            return 0 <= coord[0] < num_rows and 0 <= coord[1] < num_cols

        u_nighbors = []  # up
        d_nighbors = []  # down
        l_nighbors = []  # L
        r_nighbors = []
        ul_nighbors = []
        ur_nighbors = []
        dl_nighbors = []
        dr_nighbors = []

        # up and down

        for i in range(1, 4):
            up_coord = (current_coord[0], current_coord[1] + i)
            down_coord = (current_coord[0], current_coord[1] - i)
            right_coord = (current_coord[0] + i, current_coord[1])
            left_coord = (current_coord[0] - i, current_coord[1])
            up_right_coord = (current_coord[0] + i, current_coord[1] + i)
            down_left_coord = (current_coord[0] - i, current_coord[1] - i)
            down_right_coord = (current_coord[0] + i, current_coord[1] - i)
            up_left_coord = (current_coord[0] - i, current_coord[1] + i)

            if is_within_board(up_coord):
                u_nighbors.append(up_coord)
            if is_within_board(down_coord):
                d_nighbors.append(down_coord)
            if is_within_board(right_coord):
                r_nighbors.append(right_coord)
            if is_within_board(left_coord):
                l_nighbors.append(left_coord)
            if is_within_board(up_right_coord):
                ur_nighbors.append(up_right_coord)
            if is_within_board(down_left_coord):
                dl_nighbors.append(down_left_coord)
            if is_within_board(down_right_coord):
                dr_nighbors.append(down_right_coord)
            if is_within_board(up_left_coord):
                ul_nighbors.append(up_left_coord)

        # UP
        if (
            len(u_nighbors) == 3
            and bord2D[u_nighbors[0]]
            == bord2D[u_nighbors[1]]
            == opponent(current_color)
            and bord2D[u_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    u_nighbors[0][0] + 1, u_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    u_nighbors[1][0] + 1, u_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # DOWN
        if (
            len(d_nighbors) == 3
            and bord2D[d_nighbors[0]]
            == bord2D[d_nighbors[1]]
            == opponent(current_color)
            and bord2D[d_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    d_nighbors[0][0] + 1, d_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    d_nighbors[1][0] + 1, d_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # R
        if (
            len(r_nighbors) == 3
            and bord2D[r_nighbors[0]]
            == bord2D[r_nighbors[1]]
            == opponent(current_color)
            and bord2D[r_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    r_nighbors[0][0] + 1, r_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    r_nighbors[1][0] + 1, r_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # L
        if (
            len(l_nighbors) == 3
            and bord2D[l_nighbors[0]]
            == bord2D[l_nighbors[1]]
            == opponent(current_color)
            and bord2D[l_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    l_nighbors[0][0] + 1, l_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    l_nighbors[1][0] + 1, l_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # UR
        if (
            len(ur_nighbors) == 3
            and bord2D[ur_nighbors[0]]
            == bord2D[ur_nighbors[1]]
            == opponent(current_color)
            and bord2D[ur_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    ur_nighbors[0][0] + 1, ur_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    ur_nighbors[1][0] + 1, ur_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # UL
        if (
            len(ul_nighbors) == 3
            and bord2D[ul_nighbors[0]]
            == bord2D[ul_nighbors[1]]
            == opponent(current_color)
            and bord2D[ul_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    ul_nighbors[0][0] + 1, ul_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    ul_nighbors[1][0] + 1, ul_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # DR
        if (
            len(dr_nighbors) == 3
            and bord2D[dr_nighbors[0]]
            == bord2D[dr_nighbors[1]]
            == opponent(current_color)
            and bord2D[dr_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    dr_nighbors[0][0] + 1, dr_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    dr_nighbors[1][0] + 1, dr_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # DL
        if (
            len(dl_nighbors) == 3
            and bord2D[dl_nighbors[0]]
            == bord2D[dl_nighbors[1]]
            == opponent(current_color)
            and bord2D[dl_nighbors[2]] == current_color
        ):
            self.board.board[
                coord_to_point(
                    dl_nighbors[0][0] + 1, dl_nighbors[0][1] + 1, self.board.size
                )
            ] = EMPTY
            self.board.board[
                coord_to_point(
                    dl_nighbors[1][0] + 1, dl_nighbors[1][1] + 1, self.board.size
                )
            ] = EMPTY

            if current_color == 1:
                self.board.black_cap += 2
            elif current_color == 2:
                self.board.white_cap += 2

        # Define the four adjacent neighbors
        # neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        # for neighbor in neighbors:
        #     neighbor_coord = (current_coord[0] + neighbor[0], current_coord[1] + neighbor[1])

        #     # Check if the neighbor is within the board boundaries
        #     if 0 <= neighbor_coord[0] < self.board.size and 0 <= neighbor_coord[1] < self.board.size:
        #         neighbor_color = bord2D[neighbor_coord]

        #         # Check if the neighbor has a different color
        #         if neighbor_color != current_color:
        #             # Perform a depth-first search to check for captured stones
        #             if not self.is_group_alive(neighbor_coord, neighbor_color):
        #                 # If the group is not alive, remove the stones from the board
        #                 self.remove_group(neighbor_coord, neighbor_color)

    def is_group_alive(self, group_coord, group_color):
        """
        Check if a group of stones of a specific color is alive using a depth-first search.
        """
        visited = set()
        stack = [group_coord]

        while stack:
            coord = stack.pop()
            if coord in visited:
                continue
            visited.add(coord)

            for neighbor in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_coord = (coord[0] + neighbor[0], coord[1] + neighbor[1])

                if (
                    0 <= neighbor_coord[0] < self.board.size
                    and 0 <= neighbor_coord[1] < self.board.size
                ):
                    neighbor_color = self.board.board[
                        coord_to_point(
                            neighbor_coord[0] + 1,
                            neighbor_coord[1] + 1,
                            self.board.size,
                        )
                    ]
                    if neighbor_color == EMPTY:
                        return True
                    elif neighbor_color == group_color:
                        stack.append(neighbor_coord)

        return False

    def remove_group(self, group_coord, group_color):
        """
        Remove a group of stones of a specific color from the board.
        """
        visited = set()
        stack = [group_coord]

        while stack:
            coord = stack.pop()
            if coord in visited:
                continue
            visited.add(coord)

            self.board.board[
                coord_to_point(coord[0] + 1, coord[1] + 1, self.board.size)
            ] = EMPTY

            for neighbor in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_coord = (coord[0] + neighbor[0], coord[1] + neighbor[1])

                if (
                    0 <= neighbor_coord[0] < self.board.size
                    and 0 <= neighbor_coord[1] < self.board.size
                ):
                    neighbor_color = self.board.board[
                        coord_to_point(
                            neighbor_coord[0] + 1,
                            neighbor_coord[1] + 1,
                            self.board.size,
                        )
                    ]
                    if neighbor_color == group_color:
                        stack.append(neighbor_coord)

    def gogui_rules_final_result_cmd(self, args: List[str]) -> None:
        """Implement this function for Assignment 1"""
        if self.board.last_move != -1:
            last_check = self.check_point_is_win(self.board.last_move)
            if last_check != False:
                self.game_status = last_check
                self.respond(last_check)
                return
        if self.board.black_cap >= 10:
            self.game_status = "black"
            self.respond("black")
            return
        if self.board.white_cap >= 10:
            self.game_status = "white"
            self.respond("white")
            return
        # is Draw?
        elif len(self.board.get_empty_points()) == 0:
            self.game_status = "draw"
            self.respond("draw")
            return
        self.respond("unknown")
        return

    def gogui_rules_legal_moves_cmd(self, args: List[str]) -> None:
        """Implement this function for Assignment 1"""
        if self.game_status == "playing":
            list_res = [
                format_point(point_to_coord(x, self.board.size))
                for x in self.board.get_empty_points()
            ]
            if self.board.ko_recapture != -1:
                ko = format_point(
                    point_to_coord(self.board.ko_recapture, self.board.size)
                )
                if ko in list_res:
                    list_res.remove(ko)
            res = " ".join(list_res)
            self.respond(res)
        else:
            self.respond()

    def play_cmd(self, args: List[str]) -> None:
        """
        Modify this function for Assignment 1.
        play a move args[1] for given color args[0] in {'b','w'}.
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]

            if board_color != "b" and board_color != "w":
                self.respond('illegal move: "{}" wrong color'.format(board_color))
                return

            color = color_to_int(board_color)
            if args[1].lower() == "pass":
                # self.board.play_move(PASS, color)
                self.board.current_player = opponent(color)
                self.respond()
                return

            try:
                coord = move_to_coord(args[1], self.board.size)
            except (IndexError, ValueError):
                self.respond('illegal move: "{}" wrong coordinate'.format(board_move))
                return

            move = coord_to_point(coord[0], coord[1], self.board.size)
            if self.board.current_player != color:
                self.respond(f"illegal move: {args} wrong color")
                return
            # is legal move
            if self.board.board[move] != EMPTY:
                self.respond(f"illegal move: {args} occupied")
                return
            else:
                self.board.board[move] = color
                self.cap_process(move)
                self.board.last_move = move
                self.board.current_player = opponent(color=color)
                self.debug_msg(
                    "Move: {}\nBoard:\n{}\n".format(board_move, self.board2d())
                )
            self.respond()
            return
        except Exception as e:
            self.respond("Error: {}".format(str(e)))
            raise e

    def genmove_cmd(self, args):
        """Modify this function for Assignment 1"""
        """ generate a move for color args[0] in {'b','w'} """
        board_color = args[0].lower()
        color = color_to_int(board_color)

        # Check if the game is already decided (opponent has won)
        # opponent = "black" if color == WHITE else "white"
        # if self.board.result() == opponent:
        #     self.respond("resign")
        #     return
        if (
            self.board.last_move != -1
            and self.check_point_is_win(self.board.last_move) != False
        ):
            self.respond("resign")
            return

        # # Generate a move using your game engine
        # move = self.go_engine.get_move(self.board, color)

        list_res = [x for x in self.board.get_empty_points()]
        if self.board.ko_recapture != -1:
            ko = self.board.ko_recapture
            if ko in list_res:
                list_res.remove(ko)

        # If your game engine returns None, it means full, no empty
        if len(list_res) == 0:
            self.respond("pass")
            return

        move = np.random.choice(list_res)
        self.board.board[move] = color
        self.board.current_player = opponent(color)
        self.board.last_move = move
        self.cap_process(move)
        move_as_string = format_point(point_to_coord(move, self.board.size))
        self.respond(move_as_string)

    def gogui_rules_captured_count_cmd(self, args: List[str]) -> None:
        """
        Modify this function for Assignment 1.
        Respond with the score for white, an space, and the score for black.
        """

        self.respond(f"{self.board.white_cap} {self.board.black_cap}")

    """
    ==========================================================================
    Assignment 1 - game-specific commands end here
    ==========================================================================
    """


def point_to_coord(point: GO_POINT, boardsize: int) -> Tuple[int, int]:
    """
    Transform point given as board array index
    to (row, col) coordinate representation.
    Special case: PASS is transformed to (PASS,PASS)
    """
    if point == PASS:
        return (PASS, PASS)
    else:
        NS = boardsize + 1
        return divmod(point, NS)


def format_point(move: Tuple[int, int]) -> str:
    """
    Return move coordinates as a string such as 'A1', or 'PASS'.
    """
    assert MAXSIZE <= 25
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    if move[0] == PASS:
        return "PASS"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def move_to_coord(point_str: str, board_size: int) -> Tuple[int, int]:
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return (PASS, PASS)
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("invalid point: '{}'".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("point off board: '{}'".format(s))
    return row, col


def color_to_int(c: str) -> int:
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK, "w": WHITE, "e": EMPTY, "BORDER": BORDER}
    return color_to_int[c]
