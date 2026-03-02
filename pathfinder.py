import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import math
import random
import time

color_empty = "white"
color_wall = "black"
color_start = "green"
color_goal = "red"
color_frontier = "yellow"
color_visited = "lightblue"
color_path = "lime"
color_agent = "purple"

class PathfinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Informed Search & Dynamic Pathfinding")
        
        #default Grid Settings
        self.rows = 10
        self.cols = 10
        self.cell_size = 30
        self.grid = []
        self.rects = {}
        self.start_node = None
        self.goal_node = None
        self.is_running = False
        self.current_path = []
        self.covered_cells = set()  # Track cells already traversed by agent
        self.setup_ui()
        self.initialize_grid()

    def setup_ui(self):
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack()
        
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_click)

        control_frame = tk.Frame(self.root, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        #grid sizing
        tk.Label(control_frame, text="Rows:").pack()
        self.entry_rows = tk.Entry(control_frame)
        self.entry_rows.insert(0, str(self.rows))
        self.entry_rows.pack()
        
        tk.Label(control_frame, text="Cols:").pack()
        self.entry_cols = tk.Entry(control_frame)
        self.entry_cols.insert(0, str(self.cols))
        self.entry_cols.pack()
        
        tk.Button(control_frame, text="Update Grid Size", command=self.update_grid_size).pack(pady=5)

        tk.Label(control_frame, text="Drawing Mode:").pack(pady=(10, 0))
        self.draw_mode = tk.StringVar(value="Wall")
        tk.Radiobutton(control_frame, text="Start Node", variable=self.draw_mode, value="Start").pack(anchor=tk.W)
        tk.Radiobutton(control_frame, text="Goal Node", variable=self.draw_mode, value="Goal").pack(anchor=tk.W)
        tk.Radiobutton(control_frame, text="Wall / Obstacle", variable=self.draw_mode, value="Wall").pack(anchor=tk.W)
        tk.Radiobutton(control_frame, text="Eraser", variable=self.draw_mode, value="Eraser").pack(anchor=tk.W)
        
        tk.Button(control_frame, text="Generate Random Maze (30%)", command=self.generate_maze).pack(pady=5)
        
        #algorithm & heuristic
        tk.Label(control_frame, text="Algorithm:").pack(pady=(10, 0))
        self.algo_var = tk.StringVar(value="A* Search")
        ttk.Combobox(control_frame, textvariable=self.algo_var, values=["A* Search", "Greedy Best-First"]).pack()
        
        tk.Label(control_frame, text="Heuristic:").pack(pady=(5, 0))
        self.heuristic_var = tk.StringVar(value="Manhattan")
        ttk.Combobox(control_frame, textvariable=self.heuristic_var, values=["Manhattan", "Euclidean"]).pack()
        
        #dynamic mode
        self.dynamic_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="Enable Dynamic Obstacles", variable=self.dynamic_mode).pack(pady=10)
        
        #run button
        tk.Button(control_frame, text="RUN PATHFINDER", bg="black", fg="white", command=self.start_agent).pack(pady=10, fill=tk.X)
        tk.Button(control_frame, text="Clear Visuals", command=self.clear_visuals).pack(fill=tk.X)

        tk.Label(control_frame, text="--- Metrics Dashboard ---", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        self.lbl_visited = tk.Label(control_frame, text="Nodes Visited: 0")
        self.lbl_visited.pack(anchor=tk.W)  
        self.lbl_cost = tk.Label(control_frame, text="Path Cost: 0")
        self.lbl_cost.pack(anchor=tk.W)
        self.lbl_time = tk.Label(control_frame, text="Execution Time: 0 ms")
        self.lbl_time.pack(anchor=tk.W)

    def update_grid_size(self):
        try:
            self.rows = int(self.entry_rows.get())
            self.cols = int(self.entry_cols.get())
            self.initialize_grid()
        except ValueError:
            messagebox.showerror("Error", "Rows and Cols must be integers.")

    def initialize_grid(self):
        self.canvas.delete("all")
        self.canvas.config(width=self.cols * self.cell_size, height=self.rows * self.cell_size)
        
        #0 = Empty, 1 = Wall
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.rects = {}
        self.start_node = None
        self.goal_node = None
        self.covered_cells = set()  # Reset covered cells on grid reset
        
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color_empty, outline="gray")
                self.rects[(r, c)] = rect

    def color_cell(self, r, c, color):
        self.canvas.itemconfig(self.rects[(r, c)], fill=color)

    def handle_click(self, event):
        if self.is_running:
            return
            
        c = event.x // self.cell_size
        r = event.y // self.cell_size
        
        if 0 <= r < self.rows and 0 <= c < self.cols:
            mode = self.draw_mode.get()
            
            if mode == "Start":
                if self.start_node:
                    self.color_cell(self.start_node[0], self.start_node[1], color_empty)
                self.start_node = (r, c)
                self.grid[r][c] = 0 #ensure it's not a wall
                self.color_cell(r, c, color_start)
                
            elif mode == "Goal":
                if self.goal_node:
                    self.color_cell(self.goal_node[0], self.goal_node[1], color_empty)
                self.goal_node = (r, c)
                self.grid[r][c] = 0
                self.color_cell(r, c, color_goal)
                
            elif mode == "Wall":
                if (r, c) != self.start_node and (r, c) != self.goal_node:
                    self.grid[r][c] = 1
                    self.color_cell(r, c, color_wall)
                    
            elif mode == "Eraser":
                if (r, c) == self.start_node: self.start_node = None
                if (r, c) == self.goal_node: self.goal_node = None
                self.grid[r][c] = 0
                self.color_cell(r, c, color_empty)

    def generate_maze(self):
        self.clear_visuals()
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) != self.start_node and (r, c) != self.goal_node:
                    if random.random() < 0.30: # 30% wall coverage
                        self.grid[r][c] = 1
                        self.color_cell(r, c, color_wall)
                    else:
                        self.grid[r][c] = 0
                        self.color_cell(r, c, color_empty)

    def clear_visuals(self):
        # Clears the path/visited nodes but keeps the walls, start, and goal
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 1:
                    self.color_cell(r, c, color_wall)
                elif (r, c) == self.start_node:
                    self.color_cell(r, c, color_start)
                elif (r, c) == self.goal_node:
                    self.color_cell(r, c, color_goal)
                else:
                    self.color_cell(r, c, color_empty)

    def calculate_heuristic(self, r1, c1, r2, c2):
        if self.heuristic_var.get() == "Manhattan":
            return abs(r1 - r2) + abs(c1 - c2)
        elif self.heuristic_var.get() == "Euclidean":
            return math.sqrt((r1 - r2)**2 + (c1 - c2)**2)
        return 0

    def get_neighbors(self, r, c):
        neighbors = []
        #Up, Down, Left, Right 
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] == 0: # If not an obstacle
                    neighbors.append((nr, nc))
        return neighbors

    def find_path(self, start_pos):
        algorithm = self.algo_var.get()

        start_time = time.time()
        nodes_visited = 0
        open_set = []
        tie_breaker = 0 
        heapq.heappush(open_set, (0, tie_breaker, start_pos))
        
        #dictionaries to track path costs and paths
        came_from = {}
        g_score = {start_pos: 0}
        
        #track what is in the open_set for quick lookup
        open_set_hash = {start_pos}
        
        while len(open_set) > 0:
            current_f, _, current_node = heapq.heappop(open_set)
            open_set_hash.remove(current_node)
            
            #If we reached the goal, reconstruct the path
            if current_node == self.goal_node:
                end_time = time.time()
                self.update_metrics(nodes_visited, g_score[current_node], end_time - start_time)
                return self.reconstruct_path(came_from, current_node)
            
            nodes_visited += 1
            
            #visualize visited node
            if current_node != self.start_node and current_node != self.goal_node:
                self.color_cell(current_node[0], current_node[1], color_visited)
                self.root.update()
                time.sleep(0.01) #small delay for animation
                
            #check all valid neighbors
            for neighbor in self.get_neighbors(current_node[0], current_node[1]):
                #assume cost between adjacent nodes is 1
                tentative_g = g_score[current_node] + 1
                
                #If we found a cheaper path to this neighbor
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current_node #mark parent for path reconstruction
                    g_score[neighbor] = tentative_g #update g_score for this neighbor
                    
                    h = self.calculate_heuristic(neighbor[0], neighbor[1], self.goal_node[0], self.goal_node[1])

                    if algorithm == "A* Search":
                        f_score = tentative_g + h
                    elif algorithm == "Greedy Best-First":
                        f_score = h 
                    
                    if neighbor not in open_set_hash:
                        tie_breaker += 1
                        heapq.heappush(open_set, (f_score, tie_breaker, neighbor))
                        open_set_hash.add(neighbor)
                        
                        #visualize frontier node
                        if neighbor != self.goal_node:
                            self.color_cell(neighbor[0], neighbor[1], color_frontier)
                            
        #If loop finishes and goal is not found
        messagebox.showinfo("Result", "No path exists to the Goal!")
        return []

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        
        path.reverse() 
        for r, c in path:
            if (r, c) != self.start_node and (r, c) != self.goal_node:
                self.color_cell(r, c, color_path)
        return path

    def update_metrics(self, visited, cost, exec_time):
        self.lbl_visited.config(text=f"Nodes Visited: {visited}")
        self.lbl_cost.config(text=f"Path Cost: {cost}")
        self.lbl_time.config(text=f"Execution Time: {int(exec_time * 1000)} ms")

    def start_agent(self):
        if not self.start_node or not self.goal_node:
            messagebox.showwarning("Warning", "Please set both Start and Goal nodes.")
            return
            
        self.is_running = True
        self.covered_cells = set()  # Reset covered cells at start
        self.clear_visuals()
        
        #initial search
        self.current_path = self.find_path(self.start_node)
        
        if not self.current_path:
            self.is_running = False
            return
            
        #moving along the path
        self.transit_agent(0)

    def transit_agent(self, step_index):
        if not self.is_running:
            return
            
        #check if reached goal
        if step_index >= len(self.current_path):
            self.is_running = False
            messagebox.showinfo("Success", "Agent reached the Goal!")
            return
            
        current_pos = self.current_path[step_index]
        
        #mark current position as covered
        self.covered_cells.add(current_pos)
        
        #color the agent's current position
        if current_pos != self.start_node and current_pos != self.goal_node:
            self.color_cell(current_pos[0], current_pos[1], color_agent)
            
        self.root.update()
        time.sleep(0.1) #transit speed
        
        #dynamic obstacles
        if self.dynamic_mode.get():
            #5% chance to spawn a random wall every step while moving
            if random.random() < 0.05:
                #find an empty spot to spawn wall, excluding covered cells
                empty_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 0 and (r, c) != self.start_node and (r, c) != self.goal_node and (r, c) != current_pos and (r, c) not in self.covered_cells]
                
                if empty_cells:
                    spawn_r, spawn_c = random.choice(empty_cells)
                    self.grid[spawn_r][spawn_c] = 1 #make it an obstacle
                    self.color_cell(spawn_r, spawn_c, color_wall)
                    
                    #only re-calculate if obstacle spawned on our remaining path
                    remaining_path = self.current_path[step_index + 1:]
                    if (spawn_r, spawn_c) in remaining_path:
                        print("Path blocked! Re-calculating...")
                        self.clear_visuals()
                        #re-color covered cells to preserve path visualization
                        for covered_r, covered_c in self.covered_cells:
                            if (covered_r, covered_c) != self.start_node and (covered_r, covered_c) != self.goal_node:
                                self.color_cell(covered_r, covered_c, color_path)

                        new_path = self.find_path(current_pos)
                        
                        if new_path:
                            self.current_path = new_path
                            #resume moving from the beginning of the new path
                            self.root.after(100, lambda: self.transit_agent(0))
                            return
                        else:
                            self.is_running = False
                            return

        #move to next step
        self.root.after(100, lambda: self.transit_agent(step_index + 1))

if __name__ == "__main__":
    root = tk.Tk()
    app = PathfinderApp(root)
    root.mainloop()