from graphviz import Digraph

# Create a directed graph with left-to-right layout
dot = Digraph(comment="Website Process Flow", format="png")
dot.attr(rankdir="LR", size="10,5")

# Define nodes (pages & actions)
pages = {
    "Login": "🔑 Login",
    "Dashboard": "📊 Dashboard",
    "Pending": "⏳ Pending Clients",
    "Add": "➕ Add Client",
    "Update": "✏️ Update Client",
    "Download": "⬇️ Download Data",
    "View": "🔍 View Clients",
    "Redeemed": "🎟️ Redeemed",
    "Tasks": "📝 To-Do / Tasks",
    "Statistics": "📈 Statistics",
    "Logs": "📜 Audit Logs",
    "UserMgmt": "👥 User Management",
    "Logout": "🚪 Logout"
}

# Add nodes to graph
for key, label in pages.items():
    dot.node(key, label, shape="box", style="rounded,filled", color="lightblue", fontname="Arial")

# Define edges (flows)
edges = [
    ("Login", "Dashboard"),
    ("Dashboard", "Pending"),
    ("Dashboard", "Add"),
    ("Dashboard", "Update"),
    ("Dashboard", "Download"),
    ("Dashboard", "View"),
    ("Dashboard", "Redeemed"),
    ("Dashboard", "Tasks"),
    ("Dashboard", "Statistics"),
    ("Dashboard", "Logs"),
    ("Dashboard", "UserMgmt"),
    ("Dashboard", "Logout"),
]

# Add edges to graph
for src, dst in edges:
    dot.edge(src, dst)

# Save and render
output_path = "/mnt/data/website_process_flow_lr"
dot.render(output_path, cleanup=True)

output_path + ".png"