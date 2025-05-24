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
    'G': (30, 50),  # Трава (основной биом)
    'W': (20, 30),  # Вода
    'M': (20, 30),   # Низкие горы
}

tile_adjacency = {
    'G': ['G', 'W', 'M'],  # Трава граничит с водой и горами
    'W': ['W', 'G'],       # Вода - только с травой и водой
    'M': ['M', 'G'],       # Горы - с травой и другими горами
}

tile_types = ['G', 'W', 'M']
grid = [[tile_types.copy() for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
total_cells = GRID_WIDTH * GRID_HEIGHT

tile_counts = defaultdict(int)

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
    available_tiles = [tile for tile in options if check_percentage_limits(tile)]
    return available_tiles if available_tiles else options

def collapse_cell(x, y):
    if is_collapsed(grid[y][x]):
        return
    options = get_available_tiles(x, y)
    chosen_tile = random.choice(options) if options else 'G'
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
            valid_neighbor_tiles = [
                t for t in neighbor_options
                if any(t in tile_adjacency.get(opt, []) for opt in current_options)
            ]
            if valid_neighbor_tiles and set(valid_neighbor_tiles) != set(neighbor_options):
                grid[ny][nx] = valid_neighbor_tiles
                stack.append((nx, ny))

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

def save_map_to_file(filename="generated_map_2.txt"):
    with open(filename, 'w') as f:
        for y in range(GRID_HEIGHT):
            line = ''.join(grid[y][x][0] for x in range(GRID_WIDTH))
            f.write(line + '\n')
    print(f"Карта сохранена в {filename}")

def print_tile_percentages():
    print("\nРаспределение тайлов:")
    for tile, (min_p, max_p) in TILE_PERCENTAGE_RANGES.items():
        percent = (tile_counts[tile] / total_cells) * 100
        print(f"{tile}: {percent:.1f}% (допустимо: {min_p}%-{max_p}%)")

def main():
    print(f"Генерация карты {GRID_WIDTH}x{GRID_HEIGHT}...")
    while run_wfc_step():
        pass
    save_map_to_file()
    print_tile_percentages()

if __name__ == "__main__":
    main()