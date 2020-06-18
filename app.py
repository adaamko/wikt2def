import streamlit as st
from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source



@st.cache(allow_output_mutation=True)
def load_text_to_4lang():
    text_to_4lang_en = TextTo4lang(lang="en")
    text_to_4lang_de = TextTo4lang(lang="de")
    print("load")
    return text_to_4lang_en, text_to_4lang_de

def get_4lang_graph(sentence, text_to_4lang, method, depth):
    print(get_4lang_graph)
    premise = text_to_4lang.process_text(sentence, method=method, depth=depth, filt=False, black_or_white="")
    dot = premise.to_dot()
    return dot

def main():
    st.title("The processed 4lang graph")
    st.sidebar.title("4lang demo, please provide an input sentence")
    fourlang_en, fourlang_de = load_text_to_4lang()

    sentence = st.sidebar.text_input('Input your sentence here:') 
    language = st.sidebar.selectbox("Select Language", ["en", "de"])
    method = st.sidebar.selectbox("Select Method", ["default", "expand", "substitute"])
    depth = st.sidebar.number_input("Select Recursion depth", format="%i", value=0)

    word = st.sidebar.text_input("Get definition of a word: ")
    if sentence:
        if language == "en":
            dot = get_4lang_graph(sentence, fourlang_en, method, depth)
        elif language == "de":
            dot = get_4lang_graph(sentence, fourlang_de, method, depth)
        st.graphviz_chart(dot)

    if word:
        definition = fourlang_en.get_longman_definition(word)
        if definition:
            st.text(definition)

if __name__ == "__main__":
    main()