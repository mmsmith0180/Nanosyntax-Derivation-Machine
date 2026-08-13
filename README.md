## Live Demo

A hosted version of the application is available at:

https://nanosyntax-derivation-machine.onrender.com

The hosted version is intended for testing and demonstration purposes.

# Nanosyntax Derivation Machine

The Nanosyntax Derivation Machine is an open-source computational tool for constructing and exploring nanosyntactic derivations. It supports user-defined functional sequences and lexicon building by automatically performing feature-by-feature Merge, lexicalization, movement operations, and derivation visualization.

The interface allows users to enter lexical items as bracketed tree structures, build a lexicon, generate derivations, view derivations, and download the corresponding LaTeX code and PDF files. During the lexicon building phase, each lexical entry is rendered as a preview tree within the interface for visual verification before derivation.

## Theoretical Considerations 

This derivation machine implements the Nanosyntactic theory (Starke 2009, 2011; Baunaz et al. 2018; Caha 2009; De Clercq et al. 2025). It is an initial computational implementation of the Lexicalization Algorithm within a single workspace (Starke 2014, 2018). Any mistakes in interpretation or implementation of the theory are my own. 

Full references for the theoretical works cited above are available in REFERENCES.md.

### Current Functionality  
The Derivation Machine implements the following functions: 

* Lexicon Building through the interface
* f-seq input through the interface
* Recursive tree building by Merge-F
* Matching mediated by a user-created lexicon
* Rescue movement
* Subextraction 
* Recursive backcycling after failed lexicalization 

The program automatically scales trees, circles matches, and adjusts the s-sep of most small, successfully matched trees. 

### Algorithmic Definitions 
* Subextraction is defined such that the program searches for and extracts the closest labelled non-remnant constituent rather than the bottom of the tree. 
* Backcycling looks for the most recent cycle for which another movement possibility yields a match. The derivation then proceeds forwards from that point. It does not override the elsewhere condition to check for other possible, non-ideal matches at each stage, although this could be implemented later if it proves necessary. 

### Current Limitations and Future directions

The current implementation provides a single active workspace per user session. It does not yet implement multiple independent workspaces within the interface (Starke 2025, Nanoseminar Spring 2025, Morphopalooza 2026). Multiple workspaces are a planned future direction.

For some larger trees, s-sep must be adjusted manaully in the output .tex file in order to avoid overlap between circles for use in a formal presentation.

In order to use the LaTeX code in a presentation, users must open and modify the code in their local TeX environment or copy-paste the code into an online editor like Overleaf. Direct visualization or editing of TeX code is not supported in the interface.



## Requirements

### Software

* Python 3.12 or newer
* A LaTeX distribution with `pdflatex`:

  * TeX Live (Windows/Linux)
  * MacTeX (macOS)

### Python packages

Install the required Python packages:

```
pip install -r requirements.txt
```

The required packages are:

* `streamlit`
* `PyMuPDF`

## Running the Application

After installing the requirements:

```
streamlit run interface.py
```

The application will open in a browser window, most likely in your set default browser.

## Using the Derivation Machine

### 1. Enter a functional sequence

Enter the desired functional sequence as a comma-separated list.

Example:

```
SPI, Asp, Mood, Tense, Num, Person, Part, Sp
```

The program will convert these feature names into the internal feature representation used for derivation building.

### 2. Build the lexicon

Lexical entries are entered as forest-style bracketed structures.

Example:

```
[KP[K][NP[N][$\bot$]]]
```

The phonological form is entered separately.

The program will generate a preview of each lexical item and display it in the lexicon.

### 3. Build a derivation

After entering the lexical inventory and checking the previewed trees, select:

```
Build derivation
```


The program will attempt to construct a derivation from the functional sequence and lexicon.

Once a derivation has been successfully generated, the derivation is displayed as a PDF within the interface. The lexical entries, functional sequence, and input fields are temporarily locked while the derivation is reviewed.

Two options are then available:

* **Continue editing** — returns the interface to editing mode while keeping the current lexical inventory and derivation available for comparison.
* **New derivation** — clears the current lexical inventory, previews, derivation files, and input fields so that a new derivation can be constructed.

Generated derivation outputs can also be downloaded as:

* LaTeX source (`.tex`)
* PDF derivation (`.pdf`)

## Lexicon Input Conventions

### Tree format

Lexical structures must use forest-style bracket notation.

Example:

```
[ProcP[Proc]]
```

### Base nodes

The base of the tree must be represented as:

```
$\bot$
```

Example:

```
[NP[N][$\bot$]]
```

### Phrase Notation 

Every phrase label should end in an uppercase `P`.

Example:

```
TenseP
```

Avoid:

```
Tensep
```


### Homophonous morphemes 

Lexical entries with identical phonological forms should be numbered to distinguish separate morphemes.

Example:

```
e1
e2
```

This prevents ambiguity between genuinely distinct homophonous morphemes and accidental duplication.

### Duplicate entries

The lexicon does not permit:

* identical structural entries
* identical phonological forms

These restrictions help identify potential errors in lexical specification and derivation output.

## Citation

If you use the Nanosyntax Derivation Machine in research, please cite the software using the citation information provided in the `CITATION.cff` file included in this repository.

GitHub will automatically generate citations in several formats via the repository's **Cite this repository** feature.

## License

This project is licensed under the Apache License, Version 2.0.

A copy of the license is included in the `LICENSE` file.
