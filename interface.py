import subprocess as std_subprocess 
import os 

import streamlit as st
import Derivation_Machine_INTERFACE
import uuid

import base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

if "derivation_ready" not in st.session_state:
    st.session_state.derivation_ready = False


st.title("Nanosyntax Derivation Machine")


st.write("Enter a functional sequence below.")


feature_input = st.text_input(
    "Functional sequence:",
    "SPI, Asp, Mood, Tense, Num, Person, Part, Sp"
)

st.divider()

st.header("Build Lexicon")

if "lexicon_entries" not in st.session_state:
    st.session_state.lexicon_entries = []

left, right = st.columns([3, 1])

with left:

    structure_input = st.text_area(
        "Lexical structure",
        height=180
    )

with right:

    phonological_input = st.text_input(
        "Phonological form"
    )

if st.button("Add to lexicon"):
    
    projection = Derivation_Machine_INTERFACE.latex_to_tree(
        structure_input
    ) 

    preview_image = Derivation_Machine_INTERFACE.create_preview(projection) 

    st.session_state.lexicon_entries.append(
    {
        "id" : str(uuid.uuid4()), 
        "tree_string": structure_input,
        "tree": projection,
        "phonology": phonological_input,
        "semantics" : None  
     }
    )

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

                preview_image = (
                    Derivation_Machine_INTERFACE.create_preview(
                        entry["tree"]
                    )
                )

                image_base64 = image_to_base64(preview_image)

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
                    if st.button("Edit", key=f"edit_{entry["id"]}"):
                        st.session_state.editing_entry = entry["id"]

                    if "editing_entry" in st.session_state:
                        entry = st.session_state.lexicon_entries[st.session_state.editing_entry]

                        latex_input = entry["tree_string"]
                        phonology_input = entry["phonology"]

                with col2:
                    if st.button("Delete", key=f"delete_{entry["id"]}"):
                        st.session_state.lexicon_entries.remove(entry)
                        st.rerun()              

st.divider()

if st.button("Build derivation"):

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
        lexicon
    )

    std_subprocess.run( 
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "derivations.tex"
        ],
        capture_output=True,
        text=True
    )

    st.session_state.derivation_ready = True

    st.success("Derivation complete!")

if st.session_state.derivation_ready:
    with open("derivations.tex", "rb") as file:

        st.download_button(
            label="Download LaTeX derivation",
            data=file,
            file_name="derivations.tex",
            mime="text/plain"
        )

if os.path.exists("derivations.pdf") and st.session_state.derivation_ready:
    with open("derivations.pdf", "rb") as file:
        st.download_button(
            label="Download PDF derivation",
            data=file,
            file_name="derivations.pdf",
            mime="application/pdf"
       )