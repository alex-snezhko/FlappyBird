import pygame
from random import random
from abc import ABC, abstractmethod
import math


# min and max heights that center of pipe openings are allowed to be at
MIN_OPENING_HEIGHT = 0.2
MAX_OPENING_HEIGHT = 1 - MIN_OPENING_HEIGHT

BACK_COLOR = (255, 255, 255)

SCREEN_W = 480
SCREEN_H = 400


# represents position of objects in game units [0-1] with (0, 0) at the bottom left
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y)

    # converts position to appropriate location on screen
    def to_screen_location(self) -> (int, int):
        screen_x = math.floor(self.x * SCREEN_W)
        screen_y = math.floor((1.0 - self.y) * SCREEN_H)
        return screen_x, screen_y


class AbstractGameObject(ABC):
    # updates game object's information after one game tick specified by parameter
    @abstractmethod
    def update(self, delta_t):
        pass

    # redraws game object based on current positions
    @abstractmethod
    def draw(self, screen):
        pass


class Bird(AbstractGameObject):
    # speed at which pipes move left towards bird (bird's x-position does not actually ever change)
    X_VELOCITY = 0.2
    # downward acceleration (game units/second^2)
    GRAVITY_ACCEL = -1.7

    # bird width and height in game units
    WIDTH = 0.06
    HEIGHT = 0.05
    # how much bird's velocity changes per flap
    FLAP_DELTA_V = 0.8

    def __init__(self):
        # bird stays at x-position of 0.25 the entire game
        self.pos = Position(0.25, 0.5)
        self.y_vel = 0
        self.image = pygame.image.load("resources/bird.png")

        width = math.floor(SCREEN_H / 10)
        height = math.floor(SCREEN_H / 12)
        self.image = pygame.transform.scale(self.image, (width, height))

    def flap(self):
        self.y_vel += self.FLAP_DELTA_V

    def update(self, delta_t):
        self.pos.y += self.y_vel * delta_t + 0.5 * self.GRAVITY_ACCEL * delta_t ** 2
        self.y_vel += self.GRAVITY_ACCEL * delta_t

    def draw(self, screen):
        # position of top-left point of image
        tl_pos = self.pos + Position(-self.WIDTH / 2, self.HEIGHT / 2)
        tl_pixel = tl_pos.to_screen_location()
        screen.blit(self.image, tl_pixel)


class Pipe(AbstractGameObject):
    # relevant pipe image dimensions (in game units)
    OPENING = 0.25  # size of opening between pair of pipes
    WIDTH = 0.125
    SINGLE_HEIGHT = MAX_OPENING_HEIGHT - OPENING / 2  # height of one of the pipes in a pair
    HEIGHT = SINGLE_HEIGHT * 2 + OPENING  # height of both pipes in pair combined

    # creates new pipe object with center of opening at specified height and optional x-offset if needed
    def __init__(self, center_height, x_offset=0):
        # position at center of opening
        self.center_pos = Position(1.0 + self.WIDTH - x_offset, center_height)

        img = pygame.image.load("resources/pipe.png")
        width_pix = math.floor(self.WIDTH * SCREEN_W)
        single_height_pix = math.floor(self.SINGLE_HEIGHT * SCREEN_H)
        combined_height_pix = math.floor(self.HEIGHT * SCREEN_H)

        # bottom pipe (scaled to appropriate size)
        single_pipe_image = pygame.transform.scale(img, (width_pix, single_height_pix))
        # top pipe
        mirror_image = pygame.transform.flip(single_pipe_image, False, True)

        # empty surface on which pipe images will be drawn
        both = pygame.Surface((width_pix, combined_height_pix))
        both.fill(BACK_COLOR)

        # draws pipe images onto surface
        both.blit(mirror_image, (0, 0))
        both.blit(single_pipe_image, (0, combined_height_pix - single_height_pix))

        self.image = both

    def update(self, delta_t):
        # move pipe leftward
        delta_x = -Bird.X_VELOCITY * delta_t
        self.center_pos.x += delta_x

    def draw(self, screen):
        # position of top-left point of image
        tl_pos = self.center_pos + Position(-self.WIDTH / 2, self.HEIGHT / 2)
        tl_pixel = tl_pos.to_screen_location()
        screen.blit(self.image, tl_pixel)


# main method that is called when game is run
def main():
    pygame.init()
    pygame.display.set_caption("Flappy Bird")

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    # --- set timer --- #

    # timer has id of pygame.USEREVENT
    tick = pygame.USEREVENT
    tick_interval = 10
    # tick time in seconds
    delta_t = tick_interval / 1000
    pygame.time.set_timer(tick, tick_interval)

    # initializes/resets positions of game objects
    def new_game(reset):
        # creates new game objects if game is being restarted
        if reset:
            nonlocal bird
            nonlocal pipes
            nonlocal score

            bird = Bird()
            pipes = []
            score = 0

        # length across which center of pipe opening is allowed to span
        pipe_y_range = MAX_OPENING_HEIGHT - MIN_OPENING_HEIGHT
        opening_y = random() * pipe_y_range + MIN_OPENING_HEIGHT
        pipes.append(Pipe(opening_y))

        if auto_solve:
            nonlocal flap_times_on_path
            nonlocal time_on_path

            flap_times_on_path = new_path_flap_times(bird.pos, pipes[0].center_pos)
            time_on_path = 0

    # switch between normal and auto-solve modes
    def set_game_mode(auto_solve_mode):
        nonlocal auto_solve
        auto_solve = auto_solve_mode

        new_game(reset=True)

        # --- changes gamemode buttons --- #

        selected_color = (170, 170, 170)
        unselected_color = (230, 230, 230)

        manual_button.fill(selected_color if not auto_solve else unselected_color)
        solver_button.fill(selected_color if auto_solve else unselected_color)

        normal_font = pygame.font.SysFont("Calibri", 12)
        bold_font = pygame.font.SysFont("Calibri", 12, True)

        manual_button_text_surface = (bold_font if not auto_solve else normal_font).render("Manual", False, (0, 0, 0))
        manual_button_text_x = manual_button.get_width() / 2 - manual_button_text_surface.get_width() / 2
        manual_button_text_y = manual_button.get_height() / 2 - manual_button_text_surface.get_height() / 2

        solver_button_text_surface = (bold_font if auto_solve else normal_font).render("Auto-solve", False, (0, 0, 0))
        solver_button_text_x = solver_button.get_width() / 2 - solver_button_text_surface.get_width() / 2
        solver_button_text_y = solver_button.get_height() / 2 - solver_button_text_surface.get_height() / 2

        manual_button.blit(manual_button_text_surface, (manual_button_text_x, manual_button_text_y))
        solver_button.blit(solver_button_text_surface, (solver_button_text_x, solver_button_text_y))

    # game mode buttons
    manual_button = pygame.Surface((SCREEN_W // 8, SCREEN_H // 15))
    solver_button = pygame.Surface((SCREEN_W // 8, SCREEN_H // 15))

    bird = Bird()
    pipes = []

    # how many pipes the bird has flown through
    score = 0

    # --- data relevent for the auto-solver --- #

    # The auto-solver works on the principle of creating an imaginary line which traces the path the bird must follow,
    #  and then forcing the bird to flap whenever it crosses that path to ensure it never falls below it

    # whether or not automatic solver mode is activated
    auto_solve = False
    # list of times on path when the bird will flap (when auto-solve enabled)
    flap_times_on_path = []
    # time which the bird has spent on this path (when auto-solve enabled)
    time_on_path = 0

    # p1, p2: opening centers of pipes in question
    def new_path_flap_times(p1, p2) -> [float]:
        path_vector = p2 - p1

        # time in seconds it will take to get to end of path vector
        total_time = path_vector.x / Bird.X_VELOCITY

        angle = math.atan2(path_vector.y, path_vector.x)
        # ensures bird doesnt run into edge of pipe
        remove_y = abs((Pipe.WIDTH / 2 + Bird.WIDTH / 2) * math.tan(angle))
        # magnitude of offset for imaginary line on which bird must flap
        y_offset = (Pipe.OPENING / 2 - Bird.HEIGHT / 2 - remove_y - 0.01) / 2

        # times on which the bird must flap to complete its path
        flap_times = []

        # variables used for calculation
        y_pos = bird.pos.y
        y_vel = bird.y_vel
        slope = path_vector.y / path_vector.x
        t_path = 0  # time passed along path vector
        while True:
            # --- find times at which bird crosses imaginary flap line --- #

            # equations used:
            # p2y = p1y + vy * dt + 0.5 * g * dt^2
            # p2y = (c1y - y_offset) + slope * vx * (t_path + dt)
            #
            # p1, p2: initial position of bird and then final position at which it must flap
            # vx, vy: bird's x and y velocities
            # dt: time that must pass before bird must flap (since the last time it has flapped)
            # c1: center of the first pipe

            # quadratic formula inputs
            a = 0.5 * Bird.GRAVITY_ACCEL
            b = y_vel - slope * Bird.X_VELOCITY
            c = y_pos - (p1.y - y_offset) - Bird.X_VELOCITY * slope * t_path

            sqrt_discriminant = math.sqrt(b ** 2 - 4 * a * c)
            plus = (-b + sqrt_discriminant) / (2 * a)
            minus = (-b - sqrt_discriminant) / (2 * a)
            dt = max(plus, minus)

            t_path = t_path + dt

            # break out of loop if the current time on the path has exceeded the total time spent on the path
            if t_path > total_time:
                break

            # update variables to be correct for next calculation
            y_pos += y_vel * dt + 0.5 * Bird.GRAVITY_ACCEL * dt ** 2 + 0.00001
            y_vel += Bird.GRAVITY_ACCEL * dt + Bird.FLAP_DELTA_V

            flap_times.append(t_path)

        return flap_times

    new_game(reset=False)
    set_game_mode(auto_solve_mode=False)

    # event loop
    running = True
    while running:
        # iterates through all events in the event queue
        for event in pygame.event.get():
            if event.type == tick:
                # --- recalculates positions of game objects --- #

                # flaps bird on auto-solve mode if needed
                if auto_solve and len(flap_times_on_path) > 0 and time_on_path + delta_t >= flap_times_on_path[0]:
                    # --- accurately calculates single-frame game object movement if there is a flap required --- #

                    # time since last tick at which bird must flap
                    t_since_last_tick = flap_times_on_path[0] - time_on_path
                    # time remaining in the frame after the bird has flapped
                    t_remaining = delta_t - t_since_last_tick

                    # updates game objects to time right before the bird must flap
                    bird.update(t_since_last_tick)
                    for pipe in pipes:
                        pipe.update(t_since_last_tick)

                    bird.flap()

                    # updates game objects to positions at the end of the frame
                    bird.update(t_remaining)
                    for pipe in pipes:
                        pipe.update(t_remaining)

                    # ensures that earliest flap time in list is at index 0 for next tick
                    flap_times_on_path.remove(flap_times_on_path[0])
                else:
                    # updates game object positions under normal circumstances
                    bird.update(delta_t)
                    for pipe in pipes:
                        pipe.update(delta_t)

                time_on_path += delta_t if auto_solve else 0

                # --- restarts game if bird collides with something --- #

                # initially assumed to be no collision
                collision = False

                # checks for collision with ground and ceiling
                if bird.pos.y < bird.HEIGHT / 2 or bird.pos.y > (1 - bird.HEIGHT / 2):
                    collision = True
                else:
                    # checks for collisions with pipe
                    for pipe in pipes:
                        x_dist = abs(pipe.center_pos.x - bird.pos.x)
                        # only checks collision with pipes within collision distance
                        if x_dist <= bird.WIDTH / 2 + pipe.WIDTH / 2:
                            coll_top = bird.pos.y + bird.HEIGHT / 2 >= pipe.center_pos.y + pipe.OPENING / 2
                            coll_bot = bird.pos.y - bird.HEIGHT / 2 <= pipe.center_pos.y - pipe.OPENING / 2
                            # resets game if collision detected
                            if coll_top or coll_bot:
                                collision = True
                                break

                if collision:
                    new_game(reset=True)
                    break

                # --- removes pipe if it has left the game area --- #

                # note: pipe at index 0 in list should be the one furthest to the left
                furthest_x = pipes[0].center_pos.x
                if furthest_x < -pipes[0].WIDTH / 2:
                    pipes.remove(pipes[0])

                # --- create new pipe if needed --- #

                # pipes are exactly 0.4 units away from each other
                min_allowed_x = 0.6 + Pipe.WIDTH / 2
                # x-position of pipe furthest to the right; last element in list of pipes should match this criteria
                closest_x = pipes[-1].center_pos.x
                # creates new pipe if rightmost pipe has travelled at least 0.4 game units
                if closest_x <= min_allowed_x:
                    opening_height = pipes[-1].center_pos.y
                    # adjacent pipes can vary in their opening y positions by at most 0.2 units
                    max_diff = 0.2

                    # select random number from (-max_diff to max_diff) for new y position
                    delta_y = (random() - 0.5) * max_diff * 2
                    # add favoritism to a higher new y if opening_height is close to MIN_OPENING_HEIGHT and vice versa
                    # (to prevent several pipes in a row from being very low or very high)
                    if opening_height < MIN_OPENING_HEIGHT + max_diff:
                        delta_y += MIN_OPENING_HEIGHT + max_diff - opening_height
                    elif opening_height > MAX_OPENING_HEIGHT - max_diff:
                        delta_y -= -MAX_OPENING_HEIGHT + max_diff + opening_height

                    new_opening_height = opening_height + delta_y
                    # add new pipe to pipes with appropriate x-offset to keep pipes exactly 0.4 units away
                    pipes.append(Pipe(new_opening_height, min_allowed_x - closest_x))

                # --- checks if bird has gone through a pipe during the course of this frame --- #

                for index, pipe in enumerate(pipes):
                    # pipe's x position as it was at the beginning of the frame
                    init_x_pos = pipe.center_pos.x + bird.X_VELOCITY * delta_t

                    # add to score and find new path if bird has passed this pipe
                    if init_x_pos >= bird.pos.x > pipe.center_pos.x:
                        score += 1

                        if auto_solve:
                            # initial and final points for bird's new path
                            pi = pipe.center_pos
                            pf = pipes[index + 1].center_pos

                            flap_times_on_path = new_path_flap_times(pi, pf)
                            time_on_path = 0

                # --- redraws game objects to their new positions --- #

                screen.fill(BACK_COLOR)

                for pipe in pipes:
                    pipe.draw(screen)
                bird.draw(screen)

                # --- draws score number --- #

                score_font = pygame.font.SysFont("Calibri", 40, True)
                score_text_surface = score_font.render(str(score), False, (0, 0, 0))
                score_text_x = screen.get_width() / 2 - score_text_surface.get_width() / 2
                score_text_y = screen.get_height() / 10

                screen.blit(score_text_surface, (score_text_x, score_text_y))

                # --- draws gamemode buttons --- #

                # solver button goes to top-right of screen, manual button touching solver button to the left
                screen.blit(manual_button, (screen.get_width() - manual_button.get_width() * 2, 0))
                screen.blit(solver_button, (screen.get_width() - solver_button.get_width(), 0))

                pygame.display.flip()

            elif event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not auto_solve:
                    bird.flap()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # --- switches game mode if mouseclick on one of game mode buttons --- #

                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_y < manual_button.get_height():
                    manual_button_left_x = screen.get_width() - manual_button.get_width() * 2
                    solver_button_left_x = manual_button_left_x + manual_button.get_width()

                    # switch game modes if mouse touching one of game mode buttons
                    if auto_solve and manual_button_left_x <= mouse_x < solver_button_left_x:
                        set_game_mode(auto_solve_mode=False)
                    elif not auto_solve and mouse_x >= solver_button_left_x:
                        set_game_mode(auto_solve_mode=True)


if __name__ == "__main__":
    main()
