import os
import re
from git import Repo
from pathlib import Path
from matplotlib import patches
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.patches as mpatches
#print where we execute the script
cwd = os.getcwd()

# Let's declare a var for the path where we're going to download a repository
# Warning: this must end in /
CODE_ROOT_FOLDER="/{cwd}/Zeeguu-API/"

# If the file exists, it means we've already downloaded
if not os.path.exists(CODE_ROOT_FOLDER):
  Repo.clone_from("https://github.com/zeeguu/API", CODE_ROOT_FOLDER)

# helper function to get a file path w/o having to always provide the /content/Zeeguu-API/ prefix
def file_path(file_name):
    return CODE_ROOT_FOLDER+file_name

assert (file_path("zeeguu/core/model/user.py") == "/{cwd}/Zeeguu-API/zeeguu/core/model/user.py")

mapNames = {}
#DONE
# extracting a module name from a file name
def module_name_from_file_path(full_path):

    # e.g. ../core/model/user.py -> zeeguu.core.model.user
    # but also \core\model etc
    
    file_name = full_path[len(CODE_ROOT_FOLDER):]
    file_name = file_name.replace("/__init__.py","")
    file_name = file_name.replace("\__init__.py","")
    file_name = file_name.replace("/__main__.py","")
    file_name = file_name.replace("\__main__.py","")
    file_name = file_name.replace("/",".")
    file_name = file_name.replace("\\",".")
    file_name = file_name.replace(".py.example","")
    file_name = file_name.replace(".py","")
    mapNames[file_name] = full_path
    return file_name

assert 'zeeguu.core.model.user' == module_name_from_file_path(file_path('zeeguu/core/model/user.py'))

#lookinto this
#look at the files only from zeeguu folder
def include_module(module_name):
    return module_name.startswith("zeeguu") and not "test" in module_name and not "zeeguu.core.model" in module_name and not 'util' in module_name
#DONE
def import_from_line(line):
    try: 
        #find from and take everything 
        y = re.search("\bfrom\b\s*(.*)", line) 
        #find from and import
        x = re.search("from\s+(.*?)\s+import", line)
        #find import and take everything  before
        z = re.search("^.*?(?=\bimport\b)", line)
        #find after import
        c = y = re.search("^import (\S+)", line)
        if x:
            return x.group(1)
        if y:   
            return y.group(1)
        if z:   
            return z.group(1)
        if c:
            return c.group(1)
    except:
        return None

#DONE
# extracts all the imported modules from a file
# returns a module of the form zeeguu_core.model.bookmark, e.g.
def imports_from_file(file): 
    all_imports = []
    lines = [line for line in open(file)]
    for line in lines:
        imp = import_from_line(line)
        if imp:
            all_imports.append(imp)
    return all_imports


# extract dependencies from all files:
def dependencies_graph():
    files = Path(CODE_ROOT_FOLDER).rglob("*.py*")

    G = nx.Graph()

    for file in files:
        file_path = str(file)

        module_name = module_name_from_file_path(file_path)

        if module_name not in G.nodes:
            G.add_node(module_name)

        for each in imports_from_file(file_path):
            G.add_edge(module_name, each)

    return G


# use Mathplotlib also has support for drawing networks We do a simple drawing of all the files and their dependencies in our system

# a function to draw a graph
def draw_graph(H, size, **args):
    result = {word: '.'.join(word.split(".")[1:]) for word in H.nodes if len(word.split(".")) > 1}
    # only for api or core
    G = nx.relabel_nodes(H, result)
    pos = graphviz_layout(G, prog='neato')
    #pos = nx.spring_layout(G, k=0.01)

    plt.figure(figsize=size)
    if level > 2:
        nx.draw(G, pos, with_labels=True, **args)
        node_sizes = args.get('node_size', None)
        #label_pos = {}
        #count = 0
        #for node, (x, y) in pos.items():
        #    node_size = node_sizes[0]
        #    label_pos[node] = (x, y + node_size/1700 + 0.05) 
        #    count = count+1
        #nx.draw_networkx_labels(H, pos=label_pos)
    else:
        pos = graphviz_layout(G, prog='dot')
        nx.draw(G, pos=pos, **args)
        node_sizes = args.get('node_size', None)
        label_pos = {}
        count = 0
        for node, (x, y) in pos.items():
            node_size = node_sizes[0]
            label_pos[node] = (x, y) 
            count = count+1
        nx.draw_networkx_labels(G, pos=label_pos)
    plt.show()

#G = dependencies_graph()
#draw_graph(G, (12,10), with_labels=False)

def count_lines(target):
    total_sum = 0
    n_name = module_name_from_file_path(target)
    for key, value in mapNames.items():
        print(include_module(key))
        if include_module(key) and key.startswith(n_name):
            total_sum = total_sum + sum([1 for line in open(value)])
    return total_sum

# However, if we think a bit more about it, we realize tat a dependency graph 
# is a directed graph (e.g. module A depends on m)
# with any kinds of graph either directed (nx.DiGraph) or 
# non-directed (nx.Graph)
def dependencies_digraph():
    files = Path(CODE_ROOT_FOLDER).rglob("*.py*")

    G = nx.DiGraph()

    for file in files:
        file_path = str(file)

        source_module = module_name_from_file_path(file_path)
        if not include_module(source_module):
            continue
        
        if source_module not in G.nodes:
            G.add_node(source_module)

        for target_module in imports_from_file(file_path):
            if include_module(target_module):
                G.add_edge(source_module, target_module)
    return G

DG = dependencies_digraph()

def top_level_package(module_name, depth=1):
    components = module_name.split(".")
    return ".".join(components[:depth])

assert (top_level_package("zeeguu.core.model.utils") == "zeeguu")
assert (top_level_package("zeeguu.core.model.utils", 2) == "zeeguu.core")


def abstracted_to_top_level(G, depth=1):
    aG = nx.DiGraph()
    for each in G.edges():
        src = top_level_package(each[0], depth)
        dst = top_level_package(each[1], depth)

        if src != dst:
            aG.add_edge(src, dst)
    return aG
level = 3
ADG = abstracted_to_top_level(DG, level)
sizes = []
colors = []
for node in ADG.nodes:
    try:
        if count_lines(mapNames[node]) == 0:
            sizes.append(20)
            colors.append('lightgreen')
        else:
            sizes.append(count_lines(mapNames[node]))
            colors.append('lightblue')
    except KeyError:
        sizes.append(40)
        colors.append('b')
draw_graph(ADG, (10,10), node_size=sizes, node_color=colors, font_weight='bold')