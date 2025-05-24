import pygame
import random
import time
from collections import defaultdict

TILE_SIZE = 12
GRID_SIZE = 50
WINDOW_SIZE = TILE_SIZE * GRID_SIZE
FPS = 10

TILE_PERCENTAGE_RANGES = {
    'G': (15, 25),  # Трава
    'W': (15, 25),  # Вода
    'D': (10, 20),  # Земля
    'F': (10, 20),  # Лес
    'M': (10, 20),  # Низкие горы
    'H': (0, 5),  # Высокие горы
    'R': (0, 5),  # Дорога
}

tile_adjacency = {
    'G': ['G', 'W', 'D', 'F', 'M', 'R'],
    'W': ['W', 'G', 'F'],
    'D': ['D', 'G', 'R'],
    'F': ['F', 'G', 'M', 'W'],
    'M': ['M', 'F', 'G', 'H'],
    'H': ['H', 'M'],
    'R': ['R', 'D', 'G'],
}

tile_colors = {
    'G': (0, 200, 0),  # трава
    'W': (0, 150, 255),  # вода
    'D': (139, 69, 19),  # земля
    'F': (34, 139, 34),  # лес
    'M': (120, 120, 120),  # низкие горы
    'H': (70, 70, 70),  # высокие горы
    'R': (255, 215, 0),  # дорога
    'S': (237, 201, 175),  # песок
    '?': (180, 180, 180)  # неопределённая клетка
}

# Исключаем песок из начальных возможных тайлов
tile_types = ['G', 'W', 'D', 'F', 'M', 'H', 'R']
grid = [[tile_types.copy() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
total_cells = GRID_SIZE * GRID_SIZE

tile_counts = defaultdict(int)


def is_collapsed(cell):
    return len(cell) == 1


def update_tile_counts(x, y, new_tile, old_tiles):
    #Обновляет счетчик тайлов при коллапсе клетки
    if is_collapsed(old_tiles):
        old_tile = old_tiles[0]
        tile_counts[old_tile] -= 1

    tile_counts[new_tile] += 1


def check_percentage_limits(tile_type):
    #Проверяет, не превышены ли процентные ограничения для данного типа тайла
    if tile_type not in TILE_PERCENTAGE_RANGES:
        return True

    current_percent = (tile_counts[tile_type] / total_cells) * 100
    min_p, max_p = TILE_PERCENTAGE_RANGES[tile_type]

    return current_percent < max_p


def get_available_tiles(x, y):
    # доступные тайлы для клетки с учетом процентных ограничений
    options = grid[y][x]

    # Если клетка уже занята, возвращаем её текущий тайл
    if is_collapsed(options):
        return options

    # Если это не часть заранее сгенерированной дороги, убираем дорогу из вариантов
    if (x, y) not in road_path_coords:
        options = [tile for tile in options if tile != 'R']

    # те тайлы, которые не превысили свои процентные ограничения
    available_tiles = [tile for tile in options if check_percentage_limits(tile)]

    # Если все тайлы превысили лимит, возвращаем все варианты, чтобы избежать тупика
    if not available_tiles:
        return options

    return available_tiles


def convert_to_high_mountains():
    # Преобразует низкие горы в высокие, если они окружены горами или краем карты
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if is_collapsed(grid[y][x]) and grid[y][x][0] == 'M':
                # Проверяем 4 направления
                surrounded = True
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if not is_collapsed(grid[ny][nx]) or grid[ny][nx][0] not in ['M', 'H']:
                            surrounded = False
                            break

                if surrounded:
                    grid[y][x] = ['H']
                    tile_counts['M'] -= 1
                    tile_counts['H'] += 1


def convert_water_to_sand():
    # Преобразует воду в песок, если она граничит с дорогой и выполняется условие:
    # Клетка воды не единственная (есть соседние клетки воды)
    water_to_sand = []

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if is_collapsed(grid[y][x]) and grid[y][x][0] == 'W':
                # Проверяем, есть ли соседи-дороги
                has_road_neighbor = False
                road_positions = []

                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'R':
                            has_road_neighbor = True
                            road_positions.append((nx, ny))

                if has_road_neighbor:
                    # Проверяем условие: есть ли соседние клетки воды
                    has_water_neighbor = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'W':
                                has_water_neighbor = True
                                break

                    # Если условие выполняются, добавляем в список на замену
                    if has_water_neighbor:
                        water_to_sand.append((x, y))

    # Заменяем отмеченные клетки воды на песок
    for x, y in water_to_sand:
        grid[y][x] = ['S']
        tile_counts['W'] -= 1
        tile_counts['S'] += 1


def collapse_cell(x, y):
    if is_collapsed(grid[y][x]):
        return

    options = get_available_tiles(x, y)

    # Убираем дорогу, если она бы образовала перекресток
    if 'R' in options and too_many_road_neighbors(x, y):
        options = [opt for opt in options if opt != 'R']

    if not options:
        options = ['G']  # fallback

    chosen_tile = random.choice(options)
    old_tiles = grid[y][x].copy()
    grid[y][x] = [chosen_tile]
    update_tile_counts(x, y, chosen_tile, old_tiles)


def get_neighbors(x, y):
    neighbors = []
    if x > 0: neighbors.append((x - 1, y))
    if x < GRID_SIZE - 1: neighbors.append((x + 1, y))
    if y > 0: neighbors.append((x, y - 1))
    if y < GRID_SIZE - 1: neighbors.append((x, y + 1))
    return neighbors


def propagate(x, y):
    stack = [(x, y)]
    while stack:
        # берём клетку из стека
        cx, cy = stack.pop()
        current_options = grid[cy][cx]

        # проверяем всех её соседей
        for nx, ny in get_neighbors(cx, cy):
            neighbor_options = grid[ny][nx]

            # пропускаем уже коллапсированные клетки
            if is_collapsed(neighbor_options):
                continue

            # собираем ВСЕ возможные тайлы, которые могут быть у соседа
            valid_neighbor_tiles = set()

            for neighbor_tile in neighbor_options:
                # Проверяем, есть ли хотя бы один тайл в current_options,
                # который допускает neighbor_tile как соседа
                compatible = any(
                    neighbor_tile in tile_adjacency.get(option, []) for option in current_options
                )
                if compatible:
                    valid_neighbor_tiles.add(neighbor_tile)

            # если список допустимых тайлов изменился — обновляем соседа
            if valid_neighbor_tiles and valid_neighbor_tiles != set(neighbor_options):
                grid[ny][nx] = list(valid_neighbor_tiles)
                stack.append((nx, ny)) # добавляем в стек для дальнейшего распространения


def generate_road_path():
    start = (random.randint(0, GRID_SIZE - 1), 0)  # Верхняя граница
    end = (random.randint(0, GRID_SIZE - 1), GRID_SIZE - 1)  # Нижняя граница

    path = [start]

    x, y = start
    while (x, y) != end:
        # Выбираем направление движения: вниз, влево или вправо, чтобы приблизиться к end
        moves = []
        if y < end[1]:
            moves.append((x, y + 1))  # вниз
        if x > end[0]:
            moves.append((x - 1, y))  # влево
        if x < end[0]:
            moves.append((x + 1, y))  # вправо

        next_cell = random.choice(moves)
        if next_cell not in path:
            path.append(next_cell)
            x, y = next_cell
        else:
            break  # чтобы не зациклиться

    return path


road_path_coords = set()


def place_road(path):
    global road_path_coords
    road_path_coords = set(path)  # Сохраняем координаты дороги для проверки
    for (x, y) in path:
        grid[y][x] = ['R']
        tile_counts['R'] += 1


def too_many_road_neighbors(x, y):
    # Проверяет, не делает ли дорога перекресток или квадрат
    count = 0
    for nx, ny in get_neighbors(x, y):
        if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'R':
            count += 1
    return count >= 2


def find_lowest_entropy_cell():
    min_entropy = float('inf')
    candidates = []

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            options = grid[y][x]
            if not is_collapsed(options):
                entropy = len(options)
                if entropy < min_entropy:
                    min_entropy = entropy
                    candidates = [(x, y)]
                elif entropy == min_entropy:
                    candidates.append((x, y))

    return random.choice(candidates) if candidates else None


def draw_grid(screen):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = grid[y][x]
            if len(cell) == 1:
                color = tile_colors[cell[0]]
            else:
                color = tile_colors['?']
            pygame.draw.rect(screen, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, (50, 50, 50), (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)


def print_tile_percentages():
    # Выводит текущее процентное соотношение тайлов
    print("\nCurrent tile percentages:")
    for tile in TILE_PERCENTAGE_RANGES:
        percent = (tile_counts[tile] / total_cells) * 100
        print(f"{tile}: {percent:.1f}%")
    print()


def run_wfc_step():
    cell = find_lowest_entropy_cell()
    if cell:
        x, y = cell
        collapse_cell(x, y)
        propagate(x, y)
        return True
    return False

def save_map_to_file(filename="generated_map.txt"):
    with open(filename, 'w') as f:
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Берём элемент из списка тайлов клетки
                tile = grid[y][x][0] if grid[y][x] else '?'
                f.write(tile)
            f.write('\n')  # Переход на новую строку для каждой строки сетки
    print(f"Карта успешно сохранена в файл {filename}")

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Wave Function Collapse with Sand Beaches")
    clock = pygame.time.Clock()
    running = True
    finished_generation = False

    # 1) Генерируем путь дороги
    road_path = generate_road_path()
    place_road(road_path)

    # 2) Запускаем WFC для остальных клеток
    map_saved = False  # Добавьте флаг вне цикла

    while running:
        screen.fill((0, 0, 0))
        draw_grid(screen)
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    print_tile_percentages()

        if not finished_generation:
            finished_generation = not run_wfc_step()
        elif finished_generation and not map_saved:
            convert_to_high_mountains()
            convert_water_to_sand()
            save_map_to_file()
            map_saved = True  # Чтобы больше не сохранялось
            finished_generation = False  # Чтобы не вызывать функцию каждый кадр

    # После завершения выводим итоговые проценты
    print_tile_percentages()
    pygame.quit()


if __name__ == "__main__":
    main()