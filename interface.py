# Nanosyntax Derivation Machine
# Copyright 2026 Fryske Akademy & Meg Smith
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess as std_subprocess 
import os 
import tempfile 

import streamlit as st
import Derivation_Machine_INTERFACE
import uuid

import base64
import shutil
import time 

def cleanup_old_sessions(max_age_hours=24):

    temp_dir = tempfile.gettempdir()
    current_time = time.time()

    for name in os.listdir(temp_dir):

        if not name.startswith("nanosyntax_"):
            continue

        path = os.path.join(temp_dir, name)

        if not os.path.isdir(path):
            continue

        age_seconds = current_time - os.path.getmtime(path)

        if age_seconds > max_age_hours * 60 * 60:
            shutil.rmtree(path, ignore_errors=True)

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

if "derivation_ready" not in st.session_state:
    st.session_state.derivation_ready = False

if "session_dir" not in st.session_state: 

    cleanup_old_sessions()

    st.session_state.session_dir = tempfile.mkdtemp(
        prefix="nanosyntax_" 
    )

    st.session_state.preview_dir = os.path.join(

        st.session_state.session_dir,
        "previews"
    )

    st.session_state.derivations_dir = os.path.join(

        st.session_state.session_dir,
        "derivations"
    )

    os.makedirs(st.session_state.preview_dir)
    os.makedirs(st.session_state.derivations_dir)

derivations_path = os.path.join(
    st.session_state.derivations_dir,
    "derivations.tex"
)

derivations_pdf_path = os.path.join(
    st.session_state.derivations_dir,
    "derivations.pdf"
)

st.header("Nanosyntax Derivation Machine")

st.write("Enter a functional sequence below.")
st.write("Separate features with commas. For example: `SPI, Asp, Mood, Tense, Num, Person, Part, Sp`")

feature_input = st.text_input(
    "Functional sequence:",
    "SPI, Asp, Mood, Tense, Num, Person, Part, Sp", 
    disabled=st.session_state.derivation_ready
)

st.divider()

st.header("Build Lexicon")

st.write(r"use `$\bot$` for the bottom of the tree")  
st.write("avoid [..., roof] notation")

if "lexicon_entries" not in st.session_state:
    st.session_state.lexicon_entries = []

if "structure_input" not in st.session_state:
    st.session_state.structure_input = ""

if "load_entry" not in st.session_state:
    st.session_state.load_entry = None

if "phonology_input" not in st.session_state:
    st.session_state.phonology_input = ""

if "clear_inputs" not in st.session_state:
    st.session_state.clear_inputs = False

if "show_derivation_controls" not in st.session_state:
    st.session_state.show_derivation_controls = False

if st.session_state.clear_inputs:
    st.session_state.structure_input = ""
    st.session_state.phonology_input = ""
    st.session_state.clear_inputs = False

if st.session_state.load_entry is not None:
    st.session_state.structure_input = st.session_state.load_entry["tree_string"]
    st.session_state.phonology_input = st.session_state.load_entry["phonology"]
    st.session_state.load_entry = None

left, right = st.columns([3, 1])

with left:

    structure_input = st.text_area(
        "Lexical structure",
        height=180,
        key="structure_input", 
        disabled=st.session_state.derivation_ready
    )

with right:

    phonological_input = st.text_input(
        "Phonological form",
        key="phonology_input", 
        disabled=st.session_state.derivation_ready
    )

if "editing_entry" in st.session_state:
    button_label = "Save changes" 
else: 
    button_label = "Add to lexicon"

if st.button(button_label, disabled=st.session_state.derivation_ready):
    if "[..., roof]" in structure_input:
        st.error(
            "Please do not use [..., roof] notation. "
            "Replace with $\bot$ if this is the base of your tree, "
            "or simply remove [..., roof] from your lexical item."
        )
        st.stop() 
    
    try:
        projection = Derivation_Machine_INTERFACE.latex_to_tree(
            structure_input
        )

    except Exception:
        st.error(
        "Could not compile tree. Please input a valid forest structure."
        )
        st.stop() 

    duplicate = False

    for entry in st.session_state.lexicon_entries:
        if (
            (
            entry["tree"] == projection
            or entry["phonology"] == phonological_input
            )
            and entry["id"] != st.session_state.get("editing_entry")
        ):
            duplicate = True
            break
    if duplicate:
        st.error(
            "This item conflicts with an existing lexical entry."
            "Trees and phonological forms must be unique."
        )
        st.stop()

    if "editing_entry" in st.session_state: 

        for entry in st.session_state.lexicon_entries:
            if entry["id"] == st.session_state.editing_entry:

                entry["tree_string"] = structure_input
                entry["tree"] = projection
                entry["phonology"] = phonological_input

                Derivation_Machine_INTERFACE.delete_preview(entry["preview"])

                preview_path = Derivation_Machine_INTERFACE.create_preview(
                    projection, 
                    filename=os.path.join(
                        st.session_state.preview_dir,
                        f"preview_{uuid.uuid4()}"
                    )
                )   

                entry["preview"] = preview_path 
                entry["preview_base64"] = image_to_base64(preview_path) 

                break

        del st.session_state.editing_entry

    else: 
        preview_path = Derivation_Machine_INTERFACE.create_preview(
            projection,
            filename=os.path.join(
                st.session_state.preview_dir,
                f"preview_{uuid.uuid4()}"
            )
        )

        preview_base64 = image_to_base64(preview_path)

        st.session_state.lexicon_entries.append(
            {
                "id": str(uuid.uuid4()),
                "tree_string": structure_input,
                "tree": projection,
                "phonology": phonological_input,
                "preview": preview_path, 
                "preview_base64": preview_base64, 
                "semantics": None
            }
        )

    st.session_state.clear_inputs = True

    st.rerun() 

st.divider()

st.header("Lexicon")

cards_per_row = 3

entries = st.session_state.lexicon_entries

for i in range(0, len(entries), cards_per_row):

    cols = st.columns(cards_per_row)

    for col, entry in zip(cols, entries[i:i + cards_per_row]):

        with col:

            with st.container(border=True, height=350):

                st.subheader(entry["phonology"])

                image_base64 = entry["preview_base64"]

                st.markdown(
                    f"""
                    <div style="
                        width: 100%;
                        height: 150px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        overflow: hidden;
                    ">
                        <img src="data:image/png;base64,{image_base64}"
                            style="
                            max-width: 100%; 
                            max-height: 100%;
                            object-fit: contain">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("LaTeX source"):
                    st.code(entry["tree_string"], language="latex") 

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "Edit", 
                        key=f"edit_{entry["id"]}", 
                        disabled=st.session_state.derivation_ready 
                    ):
                        st.session_state.editing_entry = entry["id"]

                        st.session_state.load_entry = entry

                        st.rerun()


                with col2:
                    if st.button(
                        "Delete", 
                        key=f"delete_{entry["id"]}",
                        disabled=st.session_state.derivation_ready
                    ):

                        Derivation_Machine_INTERFACE.delete_preview(entry["preview"])

                        st.session_state.lexicon_entries.remove(entry)
                        st.rerun()              

st.divider()

if not st.session_state.derivation_ready:

    if st.button("Build derivation", use_container_width=True):

        # Convert user input into a Python list
        feature_names = [
            x.strip()
            for x in feature_input.split(",")
        ]

        # Create Feature() objects
        f_seq = Derivation_Machine_INTERFACE.create_f_seq(feature_names)

        st.write("Building derivation...")

        lexicon = {
            entry["tree"]: entry["phonology"]
            for entry in st.session_state.lexicon_entries
        }

        Derivation_Machine_INTERFACE.build_clause(
            f_seq,
            lexicon, 
            st.session_state.derivations_dir
        )

        if shutil.which("pdflatex") is None:
            st.error(
                "LaTeX compiler not found. Please install TeX Live or MacTeX."
            )
            st.stop()

        derivation_filename = os.path.basename(derivations_path)

        result = std_subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                derivation_filename
            ],
            cwd=st.session_state.derivations_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            st.error("Could not compile PDF derivation.")
            st.code(result.stdout + "\n" + result.stderr)
            st.stop()

        if not os.path.exists(derivations_pdf_path):
            st.error("Could not compile pdf derivation.")
            st.stop()

        for ext in [".aux", ".log", ".nav", ".out", ".snm", ".toc"]:
            path = os.path.join(
                st.session_state.derivations_dir, 
                f"derivations{ext}"
                )       
            if os.path.exists(path):
                os.remove(path)

        st.session_state.derivation_ready = True
        st.session_state.show_derivation_controls = True

        st.rerun()

        st.success("Derivation complete!")

if st.session_state.show_derivation_controls: 

    col1, col2 = st.columns(2)

    with col1:
        continue_editing = st.button(
            "Continue editing",
            use_container_width=True
        )

    with col2:
        new_derivation = st.button(
            "New derivation",
            use_container_width=True
        )

    if continue_editing:

        st.session_state.show_derivation_controls = False
        st.session_state.derivation_ready = False

        st.rerun()

    if new_derivation:
        st.session_state.show_derivation_controls = False
        st.session_state.derivation_ready = False

        # Delete lexical-entry preview files
        for entry in st.session_state.lexicon_entries:
            Derivation_Machine_INTERFACE.delete_preview(entry["preview"])

        # Clear the lexicon
        st.session_state.lexicon_entries = []

        # Clear lexical-entry input fields
        st.session_state.clear_inputs = True

        # Clear the derivations directory
        for filename in os.listdir(st.session_state.derivations_dir):
            path = os.path.join(
                st.session_state.derivations_dir,
                filename
            )
            if os.path.isfile(path):
                os.remove(path)

        # Clear the previews directory
        for filename in os.listdir(st.session_state.preview_dir):
            path = os.path.join(
                st.session_state.preview_dir,
                filename
            )
            if os.path.isfile(path):
                os.remove(path)

        st.rerun()

if st.session_state.derivation_ready:

    st.subheader("Derivation")

    if os.path.exists(derivations_pdf_path):

        with open(derivations_pdf_path, "rb") as file: 
            pdf_data = file.read()

            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

            st.markdown(
                f"""
                <iframe
                src="data:application/pdf;base64,{pdf_base64}"
                width="100%"
                height="425"
                style="border: none;">
                </iframe>
                """,
                unsafe_allow_html=True
            )

            st.write("")
            st.write("")

            col1, col2 = st.columns(2)

            with col1: 
                with open(derivations_path, "rb") as file:

                    st.download_button(
                        label="Download LaTeX derivation",
                        data=file,
                        file_name="derivations.tex",
                        mime="text/plain", 
                        use_container_width=True
                    )

            with col2: 
                with open(derivations_pdf_path, "rb") as file:
                    st.download_button(
                    label="Download PDF derivation",
                    data=file,
                    file_name="derivations.pdf",
                    mime="application/pdf", 
                    use_container_width=True    
                )