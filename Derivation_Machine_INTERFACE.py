from pydoc import doc
import subprocess
import os 
import fitz

import shutil

PDFLATEX = shutil.which("pdflatex")

if PDFLATEX is None:
    raise RuntimeError(
        "pdflatex could not be found. Please install TeX Live (Windows/Linux) or MacTeX (macOS)."
    )


#____________________________________
# ------ definition of classes ------
#____________________________________

# the system is based upon tuples. A feature (F) and complement pair is represented as a tuple
## I used the new class Projection() to represent a labelled tuple containing a Feature() f and its complement, in syntactic terms, a phrase FP
### there are three possible complements: another Projection(), Base(), or an empty position that is a remnant of syntactic movement
#### Base() represents the bottom of the tree

#### Note: tuples are not ordered, which we may want to revisit from a theoretical standpoint later because of the right branching nature of Nano
#    But for now this is working surprisingly well

class Base: 
    def __repr__(self):
        return "⊥"

    def __eq__(self, other):
        return(
            isinstance(other, Base)
    )

    def __hash__(self):
        return hash("BASE")

class Feature: 
    def __init__(self, name): 
        self.name = name

    def __repr__(self): 
        return self.name

    def __eq__(self, other):
        return(
            isinstance(other, Feature) and 
            self.name == other.name 
        )

    def __hash__(self):
        return hash(self.name)

class Projection:
    def __init__(self, label, structure):
        self.label = label
        self.structure = structure

    def __repr__(self):
        return f"{self.label}{self.structure}"

    def __eq__(self, other):
        return (
            isinstance(other, Projection) and
            self.label == other.label and
            self.structure == other.structure
        )

    def __hash__(self):
        return hash((self.label, self.structure))

#_______________________________
# ------ Helper Functions ------
#_______________________________

# ------ Size Checker ------
def size_of_structure(tree):
    if isinstance(tree, Projection):
        return 1 + sum(size_of_structure(x) for x in tree.structure)
    elif isinstance(tree, tuple):
        return sum(size_of_structure(x) for x in tree)
    else:
        return 1

# ------ Subtree Checker ------
def contains_structure(tree, target):
    if tree == target:
        return True

    if isinstance(tree, Projection):
        for part in tree.structure:
            if contains_structure(part, target):
                return True
    return False

# ------ Basic Direct Match Function ------
def check_lexicon(state, lexicon):
    matches = []
    for key, value in lexicon.items():
        if contains_structure(key, state):
            matches.append((key, value))

    if not matches: 
        return None

    # ------ Elsewhere Condition: Choose Smallest Lexical Item ------
    best_key, best_value = min(
        matches,
        key=lambda kv: size_of_structure(kv[0])
    )

    return best_value 

# ------ Check for One-Place Tuples ------     -> Identifies remnant constituents
def one_place_checker(node):

    if isinstance(node, Projection): 
        if isinstance(node.structure, tuple) and len(node.structure) == 1: 
            return True 
        else: 
            for item in node.structure: 
                if isinstance(item, Feature):
                    continue
                if isinstance(item, Projection):
                    if one_place_checker(item): 
                        return True
    return False
                 
# ------ Check for One-Place Tuples ------     -> Identifies remnant constituents
def one_place_checker(node):
    
    if isinstance(node, Projection): 
        if isinstance(node.structure, tuple) and len(node.structure) == 1: 
            return True 
        else: 
            for item in node.structure: 
                if isinstance(item, Feature):
                    continue
                if isinstance(item, Projection):
                    if one_place_checker(item): 
                        return True
    return False

# ------ Collect Visible Nodes for Matching ------  -> You know what this works for now. I will fuck with it again later if needed 
def collect_visible_nodes(node,
                          dominated_by_label=False,
                          is_root=True): 

    if not isinstance(node, Projection):
        return []

    # invisible because dominated by a labelled node
    if dominated_by_label:
        return []

    visible = []

    # root node excluded
    if not is_root:
        visible.append(node)

    # labelled nodes stop visibility downward
    if node.label != "-":
        return visible

    # unlabeled nodes allow further visibility
    for part in node.structure:

        visible.extend(
            collect_visible_nodes(
                part,
                dominated_by_label=False,
                is_root=False
            )
        )

    return visible if visible else None   # -> returns the visible nodes, starting with the biggest unlabeled node first 


# ------ Check for the Base of the Tree ------
def base_checker(node):

    if isinstance(node, Projection): 
        if Base() in node.structure: 
            return True 
        else: 
            for item in node.structure: 
                if isinstance(item, Projection):
                    if base_checker(item): 
                        return True
    return False

# ------ Collect Target Nodes for Rescue Movement ------
def collect_target_nodes(tree): 

    targets = []

    if not isinstance(tree, Projection):
        return None

    # Locate start node
    def find_start(node):
        
        for item in node.structure: 
            if isinstance(item, Projection) and not one_place_checker(item): 
                return item
            elif isinstance(item, Projection): 
                found = find_start(item) 

                if found is not None: 
                    return found
                
    start_node = find_start(tree)

    # Collect nodes starting from the top down to start node 
    def check_and_collect(node): 
        for item in node.structure: 
            if isinstance(item, Projection) and base_checker(item) and item != start_node: 
                targets.append(item) 
                check_and_collect(item)
            else: 
                continue

    check_and_collect(tree) 
    if start_node is not None:
        targets.append(start_node)
    targets.reverse()           # it is important that the order of this list is reversed for its use later in rescue movement

    return targets

# ------ Basic Function for Removing a Constituent ------
def remove_subtree(tree, subtree):

    if tree == subtree:
        return None  # signals deletion upward

    if isinstance(tree, Projection):
        new_structure = []

        for part in tree.structure:

            if part == subtree:
                # skip entirely (true structural deletion)
                continue

            elif isinstance(part, Projection):
                updated = remove_subtree(part, subtree)

                if updated is not None:
                    new_structure.append(updated)

            else:
                new_structure.append(part)

        # collapse vacuous unlabeled node
        if tree.label == "-" and len(new_structure) == 1:
            return new_structure[0]

        return Projection(tree.label, tuple(new_structure))

    return tree

 # ------ Rescue Movement ------ 
def rescue_movement(tree): 

    spine = collect_target_nodes(tree)
    movement_possibilities = [tree]

    if spine is not None:
        for subtree in spine: 
            remnant = remove_subtree(tree, subtree)
            movement_result = Projection("-", (subtree, remnant))
            movement_possibilities.append(movement_result)

    return movement_possibilities

# ------ Generalized Visual Node Matching ------ 
def indirect_matching(tree, lexicon):

    visible_nodes = collect_visible_nodes(tree)

    def remove_items(list1, list2): 
        return [x for x in list1 if x not in list2]

    # first try spellout using spans 
    for node in visible_nodes: 
        if node.label == "-":
            parts = collect_visible_nodes(node)
            new_nodes = remove_items(visible_nodes, parts)
            new_nodes = [
                x for x in new_nodes
                if x.label != "-"
            ]    # -> if the largest unlabeled node can be spelled out, remove smaller unlabelled nodes from the spellout target list 
            
            matches = []
            matched_trees = []
            
            matches.append(check_lexicon(node, lexicon))
            matched_trees.append(node)
            
            for item in new_nodes: 
                matches.append(check_lexicon(item, lexicon))
            if len(matches) == (len(new_nodes) + 1) and None not in matches and len(matches)!=0:
                return matched_trees, matches

    # second, try exhaustive lexicalization 
    remove_me = []
    
    for node in visible_nodes: 
        if node.label == "-":
            remove_me.append(node)
            
    no_unlabeled = remove_items(visible_nodes, remove_me) 

    exhaustive_matches = []
    matched_trees = [] 

    for node in no_unlabeled: 
        exhaustive_matches.append(check_lexicon(node, lexicon))
        matched_trees.append(node)

    if len(exhaustive_matches) == len(no_unlabeled) and None not in exhaustive_matches and len(exhaustive_matches)!=0: 
        return matched_trees, exhaustive_matches
            
    return None 

#_______________________________________
#------ Managing Input and Output ------
#_______________________________________

def write_to_latex(tree):

    def recurse_and_write(node): 
        
        new_tree = ""

        if isinstance(node, Projection):
            if node.label == "-":
                new_tree += "[" + ""
            else: 
                new_tree += "[" + str(node.label) 

            for daughter in node.structure:
                new_tree += recurse_and_write(daughter) 

            new_tree += "]"

        if isinstance(node, Feature):
            new_tree += "[" + str(node.name) + "]"

        if isinstance(node, Base): 
            new_tree += "[$\\bot$]"
            
        return new_tree
                            
    latex_tree = recurse_and_write(tree) 
    
    with open("derivations.tex", "a", encoding="utf-8") as f: 
        f.write(
            "\n"
            "\\begin{frame}\n"
            "\t\\begin{center}\n"
            "\t\t\\begin{adjustbox}{max width=\\textwidth, max height=.9\\textheight}\n"
            "\t\t\t\\begin{forest}\n"
            f"\t\t\t{latex_tree}\n"
            "\t\t\t\\end{forest}\n"
            "\t\t\\end{adjustbox}\n"
            "\t\\end{center}\n"
            "\\end{frame}\n"
        )

def write_to_match(tree, match_dict):

    def recurse_and_write(node): 
        
        new_tree = ""

        if isinstance(node, Projection):
            if node in match_dict.keys():
                if node.label == "-":
                    new_tree += "[" + "" + ",tikz={\\node[draw,circle,inner sep=-1pt,fit to=tree,label=south:\emph{" + match_dict[node] + "}] {};}"
                else: 
                    new_tree += "[" + str(node.label) + ",tikz={\\node[draw,circle,inner sep=-1pt,fit to=tree,label=south:\emph{" + match_dict[node] + "}] {};}"
            elif node.label == "-":
                new_tree += "[" + ""
            else: 
                new_tree += "[" + str(node.label) 

            for daughter in node.structure:
                new_tree += recurse_and_write(daughter) 

            new_tree += "]"

        if isinstance(node, Feature):
            new_tree += "[" + str(node.name) + "]"

        if isinstance(node, Base): 
            new_tree += "[$\\bot$]"
            
        return new_tree
                            
    latex_tree = recurse_and_write(tree) 
    
    with open("derivations.tex", "a", encoding="utf-8") as f: 
        f.write(
            "\n"
            "\\begin{frame}\n"
            "\t\\begin{center}\n"
            "\t\t\\begin{adjustbox}{max width=\\textwidth, max height=.9\\textheight}\n"
            "\t\t\t\\begin{forest}\n"
            f"\t\t\t{latex_tree}\n"
            "\t\t\t\\end{forest}\n"
            "\t\t\\end{adjustbox}\n"
            "\t\\end{center}\n"
            "\\end{frame}\n"
        )


# ------ Write to LaTeX for Preview ------ 
def create_preview(tree):

    def recurse_and_write(node): 
        
        new_tree = ""

        if isinstance(node, Projection):
            if node.label == "-":
                new_tree += "[" + ""
            else: 
                new_tree += "[" + str(node.label) 

            for daughter in node.structure:
                new_tree += recurse_and_write(daughter) 

            new_tree += "]"

        if isinstance(node, Feature):
            new_tree += "[" + str(node.name) + "]"

        if isinstance(node, Base): 
            new_tree += "[$\\bot$]"
            
        return new_tree
                            
    latex_tree = recurse_and_write(tree) 
    
    with open("preview.tex", "w", encoding="utf-8") as f: 
        f.write(
            "\\documentclass{standalone}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage{adjustbox}\n"
            "\\usepackage[edges]{forest}\n"
            "\\useforestlibrary{linguistics}\n"
            "\\forestapplylibrarydefaults{linguistics}\n"
            "\\forestset{\n"
            "default preamble={for tree={s sep=10mm, inner sep=0, l=0}},\n"
            "\tfairly nice empty nodes/.style={\n"
            "\tdelay={where content={}{shape=coordinate,\n"
            "\tfor siblings={anchor=north}}{}},\n"
    		"\tfor tree={s sep=4mm}},\n"
            "}\n"
            "\\begin{document}\n"
            "\n"
            "\\begin{adjustbox}{max width=\\textwidth, max height=3cm}\n"
            "\t\\begin{forest}\n"
            f"\t\t{latex_tree}\n"
            "\t\\end{forest}\n"
            "\\end{adjustbox}\n"
            "\\end{document}\n"
        )

    subprocess.run(
        [
            "pdflatex",
            "preview.tex"
        ]
        check=True
    )

    doc = fitz.open("preview.pdf")

    page = doc.load_page(0)

    pix = page.get_pixmap(dpi=300)

    pix.save("_preview.png")

    doc.close()

    return "_preview.png"


# ------ Convert LaTeX Input to Recursive Projection() Class ------
def latex_to_tree(tree_string):

    index = 0

    def parse_node():

        nonlocal index

        while tree_string[index].isspace():
            index += 1

        if tree_string[index] != "[":
            raise ValueError("Expected [")

        index += 1

        content = ""

        while tree_string[index] not in [" ", "[", "]"]:
            content += tree_string[index]
            index += 1

        daughters = []

        while True:

            while tree_string[index].isspace():
                index += 1

            if tree_string[index] == "[":
                daughters.append(parse_node())

            elif tree_string[index] == "]":
                index += 1
                break

        # Convert to internal tree representation

        if content == "$\\bot$":
            return Base()

        if content == "" and daughters:
            return Projection("-", tuple(daughters))

        if len(daughters) == 0:
            return Feature(content)

        return Projection(content, tuple(daughters))

    return parse_node()

# ------ Creates a Lexicon From Two Parallel Input Lists ------
def create_lexicon(tree_strings, lexical_items):

    lexicon = {}

    for tree_string, lexical_item in zip(tree_strings, lexical_items):

        tree = latex_to_tree(tree_string)

        lexicon[tree] = lexical_item

    return lexicon

# ------ Create f_seq ------
def create_f_seq(feature_names):

    f_seq = []

    for feature_name in feature_names:
        feature = Feature(feature_name)
        f_seq.append(feature)

    return f_seq


#____________________________________________________________________________
# ------ The Main Clause Building Function Where it All Comes Together ------
#____________________________________________________________________________
def build_clause(f_seq, lexicon): 

# ------ Open LaTeX File and Define Preamble ------
    with open("derivations.tex", "w", encoding="utf-8") as f:
        f.write(
            "\\documentclass[12pt, aspectratio=169]{beamer}\n"
            "\\mode<presentation>\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage{tikz}\n"
            "\\def\\checkmark{\\tikz\\fill[scale=0.4](0,.35) -- (.25,0) -- (1,.7) -- (.25,.15) -- cycle;}\n" 
            "\\usetikzlibrary{calc}\n"
            "\\usepackage{expex}\n"
            "\\usepackage{adjustbox}\n"
            "\\usepackage{tabularx}\n"
            "\\usepackage{multirow}\n"
            "\\usepackage[table]{xcolor}\n"
            "\\usepackage[edges]{forest}\n"
            "\\useforestlibrary{linguistics}\n"
            "\\forestapplylibrarydefaults{linguistics}\n"
            "\\forestset{\n"
            "default preamble={for tree={s sep=10mm, inner sep=0, l=0}},\n"
            "\tfairly nice empty nodes/.style={\n"
            "\tdelay={where content={}{shape=coordinate,\n"
            "\tfor siblings={anchor=north}}{}},\n"
    		"\tfor tree={s sep=4mm}},\n"
            "}\n"
            "\n\\begin{document}\n"
        )

# ------ Main Derivation Variables ------
    final = Base() # initiates the derivation at the base of a tree
    counter = 0 # keeps track of derivation stage set at -1 in order to keep counter in step with the indices of f-seq
    
    interim_stages = {}          # keeps track of interim stages which will be important for integrating backtracking 
    remaining_movement_possibilities = {}  # includes stage counters as keys and a list of remaining movement possibilities for that stage as values
    remaining_f_seq = {-1 : f_seq}   # includes stage counters as keys and the remaining f-seq at that stage as values 

# ------ Main Clause-Building Function ------
    def build_and_match(f_seq, lexicon):

        nonlocal final, counter, interim_stages, remaining_movement_possibilities, remaining_f_seq

        print("Starting build_and_match")
        print("counter =", counter)
        for f in f_seq:
        
            f_seq_copy = remaining_f_seq[counter - 1][:]
            f_seq_copy.remove(f)
        
            remaining_f_seq[counter] = f_seq_copy
        
            counter += 1

            label = f"{f.name}P"
            first_try = Projection(label, (f, final))       # creates the new tree that results from Merge F: a labeled FP
            
            write_to_latex(first_try)

            lexicalization_possibilities = rescue_movement(first_try)
            print(lexicalization_possibilities)

# ------ Helper Function for Matching ------
            def matching(list1): 
        
                nonlocal final, counter, interim_stages, remaining_movement_possibilities, remaining_f_seq
        
                list2 = list1[:]

                for possibility in list1: 
        
        
                    direct_match = check_lexicon(possibility, lexicon) 
                    indirect_match = indirect_matching(possibility, lexicon)
                    list2.remove(possibility)
        
                    if direct_match is not None:
                        print("You found a match: " + direct_match)
                        final = possibility
                        remaining_movement_possibilities[counter] = list2
                        interim_stages[counter] = possibility

                        return [possibility], [direct_match]

                    if indirect_match is not None:
                        print("You found a match:", [str(item) for item in indirect_match])
                        final = possibility 
                        remaining_movement_possibilities[counter] = list2
                        interim_stages[counter] = possibility
        
                        return indirect_match
                print("MATCHING FAILED FOR:", [str(x) for x in list1])        
                return False

# ------ Back to main function body ------

            result = matching(lexicalization_possibilities)  
            
            if result is not False: 
                matched_trees, matches = result
                match_dict = dict(zip(matched_trees, matches))
                write_to_latex(final)
                write_to_match(final, match_dict)
                continue
            else: 
                print("No match found! Let's try backtracking")

            available_previous_cycles = list(range(counter - 1, -1, -1))

            for cycle in available_previous_cycles: 
                        
                counter = cycle

                if not remaining_movement_possibilities.get(cycle):
                    continue
                
                new_match = matching(remaining_movement_possibilities[cycle]) 

                if new_match:
                    return build_and_match(remaining_f_seq[cycle - 1], lexicon)
                        
            return False
                
        return True
    
    success = build_and_match(f_seq, lexicon)

    if success:
        print("Derivation successful! Woohoo!")
        with open("derivations.tex", "a", encoding="utf-8") as f:
            f.write(
            "\\end{document}" )      
    else:
        print("Derivation failed. No more possibilities :(") 
        with open("derivations.tex", "a", encoding="utf-8") as f:
            f.write(
            "\\end{document}" ) 
                    
if __name__ == "__main__":

    f_seq_verbal_1sg_pres = create_f_seq(
        ["SPI", "Asp", "Mood", "Tense", "Num", "Person", "Part", "Sp"]
    )

    lexicon = {}

    build_clause(
        f_seq_verbal_1sg_pres,
        lexicon
    )
