import pygame
import random
from abc import ABC, abstractmethod
from math import floor


# represents position of objects in game units [0-1] with (0, 0) at the bottom left
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y)


class AbstractGameObject(ABC):
    # updates game object's information after one game tick specified by parameter
    @abstractmethod
    def update(self, delta_t):
        pass

    # redraws game object based on current positions
    @abstractmethod
    def draw(self):
        pass


# min and max heights that center of pipe openings are allowed to be at
MIN_OPENING_HEIGHT = 0.2
MAX_OPENING_HEIGHT = 0.8


class Pipe(AbstractGameObject):
    # speed at which pipes move left towards bird; analagous to speed of bird (game units/second)
    SPEED = -0.2

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
        width_pix = floor(self.WIDTH * screen.get_width())
        single_height_pix = floor(self.SINGLE_HEIGHT * screen.get_height())
        combined_height_pix = floor(self.HEIGHT * screen.get_height())

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
        delta_x = self.SPEED * delta_t
        self.center_pos.x += delta_x

        # add to score if bird has passed this pipe
        left_of_bird = self.center_pos.x < BIRD_X
        was_right_of_bird = self.center_pos.x - delta_x >= BIRD_X
        if left_of_bird and was_right_of_bird:
            pipe_passed()

    def draw(self):
        tl_pos = self.center_pos + Position(-self.WIDTH / 2, self.HEIGHT / 2)
        tl_pixel = position_to_screen_location(tl_pos)
        screen.blit(self.image, tl_pixel)


# bird stays at x-position of 0.25 the entire game
BIRD_X = 0.25


class Bird(AbstractGameObject):
    # downward acceleration (game units/second^2)
    ACCELERATION = -1.7
    # bird width and height in game units
    WIDTH = 0.06
    HEIGHT = 0.05

    def __init__(self):
        self.pos = Position(BIRD_X, 0.5)
        self.y_vel = 0
        self.image = pygame.image.load("resources/bird.png")

        width = floor(screen.get_height() / 10)
        height = floor(screen.get_height() / 12)
        self.image = pygame.transform.scale(self.image, (width, height))

    def flap(self):
        self.y_vel += 0.8

    def update(self, delta_t):
        self.pos.y += self.y_vel * delta_t + 0.5 * self.ACCELERATION * delta_t ** 2
        self.y_vel += self.ACCELERATION * delta_t

    def draw(self):
        tl_position = self.pos + Position(-self.WIDTH / 2, self.HEIGHT / 2)
        tl_pixel = position_to_screen_location(tl_position)
        screen.blit(self.image, tl_pixel)


def init(screen_x, screen_y):
    global BACK_COLOR

    global screen
    global bird
    global pipes

    global score
    global font

    pygame.init()

    screen = pygame.display.set_mode((screen_x, screen_y))
    pygame.display.set_caption("Flappy Bird")

    BACK_COLOR = (255, 255, 255)

    bird = Bird()
    pipes = []
    # length across which center of pipe opening is allowed to span
    pipe_y_range = MAX_OPENING_HEIGHT - MIN_OPENING_HEIGHT
    opening_y = random.random() * pipe_y_range + MIN_OPENING_HEIGHT
    pipes.append(Pipe(opening_y))

    score = 0
    font = pygame.font.SysFont("Calibri", 40, True)


# delta_t: time passed since last tick
def tick(delta_t):
    bird.update(delta_t)
    for pipe in pipes:
        pipe.update(delta_t)

    # restarts game if bird collides with something
    if check_collision():
        init(screen.get_width(), screen.get_height())
        return

    # removes pipe if it has left the game area
    # note: pipe at index 0 in list should be the one furthest to the left
    furthest_x = pipes[0].center_pos.x
    if furthest_x < -pipes[0].WIDTH / 2:
        pipes.remove(pipes[0])

    # create new pipe if needed: pipes are exactly 0.4 units away from each other
    min_allowed_x = 0.6 + Pipe.WIDTH / 2
    # x-position of pipe furthest to the right; last element in list of pipes should match this criteria
    closest_x = pipes[-1].center_pos.x
    # creates new pipe if rightmost pipe has travelled at least 0.4 game units
    if closest_x <= min_allowed_x:
        opening_height = pipes[-1].center_pos.y
        # adjacent pipes can vary in their opening y positions by at most 0.2 units
        max_diff = 0.2

        # select random number from (-max_diff to max_diff) for new y position
        delta_y = (random.random() - 0.5) * max_diff * 2
        # add favoritism to a higher new y if opening_height is close to MIN_OPENING_HEIGHT and vice versa
        # (to prevent several pipes in a row from being very low or very high)
        if opening_height < MIN_OPENING_HEIGHT + max_diff:
            delta_y += MIN_OPENING_HEIGHT + max_diff - opening_height
        elif opening_height > MAX_OPENING_HEIGHT - max_diff:
            delta_y -= -MAX_OPENING_HEIGHT + max_diff + opening_height

        new_opening_height = opening_height + delta_y
        # add new pipe to pipes with appropriate x-offset to keep pipes exactly 0.4 units away
        pipes.append(Pipe(new_opening_height, min_allowed_x - closest_x))


def draw_objects():
    # erases all objects on the screen
    screen.fill(BACK_COLOR)

    # draws new objects
    for pipe in pipes:
        pipe.draw()
    bird.draw()

    text_surface = font.render(str(score), False, (0, 0, 0))
    text_x = screen.get_width() / 2 - text_surface.get_width() / 2
    text_y = screen.get_height() / 10
    screen.blit(text_surface, (text_x, text_y))

    pygame.display.flip()


# returns true if bird is involved in a collision
def check_collision() -> bool:
    # checks for collision with ground and ceiling
    if bird.pos.y < bird.HEIGHT / 2 or bird.pos.y > (1 - bird.HEIGHT / 2):
        return True

    # checks for collisions with pipe
    for pipe in pipes:
        x_dist = abs(pipe.center_pos.x - bird.pos.x)
        # only checks collision with pipes within collision distance
        if x_dist <= bird.WIDTH / 2 + pipe.WIDTH / 2:
            coll_top = bird.pos.y + bird.HEIGHT / 2 >= pipe.center_pos.y + pipe.OPENING / 2
            coll_bot = bird.pos.y - bird.HEIGHT / 2 <= pipe.center_pos.y - pipe.OPENING / 2
            # resets game if collision detected
            if coll_top or coll_bot:
                return True

    return False


def pipe_passed():
    global score
    score += 1


# converts float tuple of a game position [0-1] to appropriate location on screen
def position_to_screen_location(pos) -> (int, int):
    w = screen.get_width()
    h = screen.get_height()

    screen_x = floor(pos.x * w)
    screen_y = floor((1.0 - pos.y) * h)
    return screen_x, screen_y
