import pygame
import game


def main():
    game.init(480, 400)

    # timer with id pygame.USEREVENT will tick every 10 milliseconds
    tick_id = pygame.USEREVENT
    tick_interval = 10
    pygame.time.set_timer(tick_id, tick_interval)

    # event loop
    running = True
    while running:
        # gets all events from the event queue
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == tick_id:
                # recalculates positions of game objects and redraws them
                game.tick(tick_interval / 1000)
                game.draw_objects()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.bird.flap()


if __name__ == "__main__":
    main()
