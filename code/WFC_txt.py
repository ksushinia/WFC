import random
from collections import defaultdict

def get_user_input():
    while True:
        try:
            width = int(input("Введите ширину карты (например, 80): "))
            height = int(input("Введите высоту карты (например, 40): "))
            if width <= 0 or height <= 0:
                print("Ошибка: размеры должны быть положительными числами.")
                continue
            return width, height
        except ValueError:
            print("Ошибка: введите целое число.")

GRID_WIDTH, GRID_HEIGHT = get_user_input()

TILE_PERCENTAGE_RANGES = {
    'G': (15, 25),  # Трава
    'W': (15, 25),  # Вода
    'D': (10, 20),  # Земля
    'F': (10, 20),  # Лес
    'M': (10, 20),  # Низкие горы
    'H': (0, 5),    # Высокие горы
    'R': (0, 5),    # Дорога
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

tile_types = ['G', 'W', 'D', 'F', 'M', 'H', 'R']
grid = [[tile_types.copy() for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
total_cells = GRID_WIDTH * GRID_HEIGHT

tile_counts = defaultdict(int)
road_path_coords = set()


def is_collapsed(cell):
    return len(cell) == 1


def update_tile_counts(x, y, new_tile, old_tiles):
    if is_collapsed(old_tiles):
        old_tile = old_tiles[0]
        tile_counts[old_tile] -= 1
    tile_counts[new_tile] += 1


def check_percentage_limits(tile_type):
    if tile_type not in TILE_PERCENTAGE_RANGES:
        return True

    current_percent = (tile_counts[tile_type] / total_cells) * 100
    min_p, max_p = TILE_PERCENTAGE_RANGES[tile_type]

    return current_percent < max_p


def get_available_tiles(x, y):
    options = grid[y][x]

    if is_collapsed(options):
        return options

    if (x, y) not in road_path_coords:
        options = [tile for tile in options if tile != 'R']

    available_tiles = [tile for tile in options if check_percentage_limits(tile)]

    if not available_tiles:
        return options

    return available_tiles


def convert_to_high_mountains():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if is_collapsed(grid[y][x]) and grid[y][x][0] == 'M':
                surrounded = True
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        if not is_collapsed(grid[ny][nx]) or grid[ny][nx][0] not in ['M', 'H']:
                            surrounded = False
                            break

                if surrounded:
                    grid[y][x] = ['H']
                    tile_counts['M'] -= 1
                    tile_counts['H'] += 1


def convert_water_to_sand():
    water_to_sand = []

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if is_collapsed(grid[y][x]) and grid[y][x][0] == 'W':
                has_road_neighbor = False
                road_positions = []

                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'R':
                            has_road_neighbor = True
                            road_positions.append((nx, ny))

                if has_road_neighbor:
                    has_water_neighbor = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                            if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'W':
                                has_water_neighbor = True
                                break

                    if has_water_neighbor:
                        water_to_sand.append((x, y))

    for x, y in water_to_sand:
        grid[y][x] = ['S']
        tile_counts['W'] -= 1
        tile_counts['S'] += 1


def collapse_cell(x, y):
    if is_collapsed(grid[y][x]):
        return

    options = get_available_tiles(x, y)

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
    if x < GRID_WIDTH - 1: neighbors.append((x + 1, y))
    if y > 0: neighbors.append((x, y - 1))
    if y < GRID_HEIGHT - 1: neighbors.append((x, y + 1))
    return neighbors


def propagate(x, y):
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        current_options = grid[cy][cx]

        for nx, ny in get_neighbors(cx, cy):
            neighbor_options = grid[ny][nx]

            if is_collapsed(neighbor_options):
                continue

            valid_neighbor_tiles = set()
            for neighbor_tile in neighbor_options:
                compatible = any(
                    neighbor_tile in tile_adjacency.get(option, []) for option in current_options
                )
                if compatible:
                    valid_neighbor_tiles.add(neighbor_tile)

            if valid_neighbor_tiles and valid_neighbor_tiles != set(neighbor_options):
                grid[ny][nx] = list(valid_neighbor_tiles)
                stack.append((nx, ny))


def generate_road_path():
    start = (random.randint(0, GRID_WIDTH - 1), 0)
    end = (random.randint(0, GRID_WIDTH - 1), GRID_HEIGHT - 1)

    path = [start]
    x, y = start

    while (x, y) != end:
        moves = []
        if y < end[1]:
            moves.append((x, y + 1))
        if x > end[0]:
            moves.append((x - 1, y))
        if x < end[0]:
            moves.append((x + 1, y))

        next_cell = random.choice(moves)
        if next_cell not in path:
            path.append(next_cell)
            x, y = next_cell
        else:
            break

    return path


def place_road(path):
    global road_path_coords
    road_path_coords = set(path)
    for (x, y) in path:
        grid[y][x] = ['R']
        tile_counts['R'] += 1


def too_many_road_neighbors(x, y):
    count = 0
    for nx, ny in get_neighbors(x, y):
        if is_collapsed(grid[ny][nx]) and grid[ny][nx][0] == 'R':
            count += 1
    return count >= 2


def find_lowest_entropy_cell():
    min_entropy = float('inf')
    candidates = []

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            options = grid[y][x]
            if not is_collapsed(options):
                entropy = len(options)
                if entropy < min_entropy:
                    min_entropy = entropy
                    candidates = [(x, y)]
                elif entropy == min_entropy:
                    candidates.append((x, y))

    return random.choice(candidates) if candidates else None


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
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                tile = grid[y][x][0] if grid[y][x] else '?'
                f.write(tile)
            f.write('\n')
    print(f"Карта успешно сохранена в файл {filename}")


def print_tile_percentages():
    print("\nCurrent tile percentages:")
    for tile in TILE_PERCENTAGE_RANGES:
        percent = (tile_counts[tile] / total_cells) * 100
        print(f"{tile}: {percent:.1f}%")
    print()


def main():
    print(f"Генерация карты размером {GRID_WIDTH}x{GRID_HEIGHT}...")
    road_path = generate_road_path()
    place_road(road_path)

    while True:
        if not run_wfc_step():
            break

    convert_to_high_mountains()
    convert_water_to_sand()
    save_map_to_file()
    print_tile_percentages()


if __name__ == "__main__":
    main()