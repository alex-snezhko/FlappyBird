"""
The auto-solver works on the principle of tracing a line between points to create a trajectory that the bird
must ideally pass through; it then attempts to follow that path by finding appropriate times when the bird must flap

"""

from game import Bird, Pipe
import math


# p1, p2: opening centers of pipes in question
def new_path_flap_times(bird, p1, p2) -> [float]:
    path_vector = p2 - p1

    # time in seconds it will take to get to end of path vector
    total_time = path_vector.x / Bird.FORWARD_VELOCITY

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
        b = y_vel - slope * Bird.FORWARD_VELOCITY
        c = y_pos - (p1.y - y_offset) - Bird.FORWARD_VELOCITY * slope * t_path

        sqrt_discriminant = math.sqrt(b**2 - 4 * a * c)
        plus = (-b + sqrt_discriminant) / (2 * a)
        minus = (-b - sqrt_discriminant) / (2 * a)
        delta_t = max(plus, minus)

        t_path = t_path + delta_t

        # break out of loop if the current time on the path has exceeded the total time spent on the path
        if t_path > total_time:
            break

        # update variables to be correct for next calculation
        y_pos += y_vel * delta_t + 0.5 * Bird.GRAVITY_ACCEL * delta_t**2 + 0.00001
        y_vel += Bird.GRAVITY_ACCEL * delta_t + Bird.FLAP_DELTA_V

        flap_times.append(t_path)

    return flap_times
