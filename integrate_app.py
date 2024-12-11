from openai import OpenAI, OpenAIError
import streamlit as st
import os
import json
import shelve
import unicodedata
from fpdf import FPDF
import base64
import time
import requests
from streamlit.runtime.scriptrunner import get_script_run_ctx
import pandas as pd
from br import BookRecommender

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename, 'F')
    return pdf


st.set_page_config(
    page_title="Course Generator & Book Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


if "page" not in st.session_state:
    st.session_state.page = "course_generator"


TABLER_PROMPT = """Create a detailed course outline for:
Course Name: {course_name}
Education Level: {edu_level}
Difficulty: {difficulty}
Number of Modules: {num_modules}
Duration: {duration}
Credits: {credits}

Follow this exact format:

Course Title: [The course name]

Course Details:
- Duration: [duration]
- Credits: [credits]
- Level: [edu_level]
- Difficulty: [difficulty]

Course Overview:
[2-3 sentences about what students will learn]

Learning Outcomes:
1. [specific outcome]
2. [specific outcome]
3. [specific outcome]
4. [specific outcome]
5. [specific outcome]

Course Structure:
[Generate exactly {num_modules} modules with 3 lessons each]

Module 1: [Specific module name]
- Lesson 1.1: [Specific lesson name]
- Lesson 1.2: [Specific lesson name]
- Lesson 1.3: [Specific lesson name]

[Continue for all modules]"""

DICTATOR_PROMPT = """Convert this course outline into a Python dictionary. Follow this exact format:
{
    "Module 1: Title": [
        "Lesson 1.1: Title",
        "Lesson 1.2: Title",
        "Lesson 1.3: Title"
    ]
}
Include only the dictionary, no other text."""

COURSIFY_PROMPT = """Create focused lesson content for:
Lesson: {lesson_name}
Module: {module_name}
Course: {course_name}

Follow this structure:
1. Learning Objectives (2-3 bullet points)
2. Key Concepts (list main terms and definitions)
3. Detailed Content (clear explanation with examples)
4. Practice Activities (2-3 exercises)
5. Summary (key takeaways)

Keep content clear and practical."""

QUIZZY_PROMPT = """Create a quiz for the module: {module_name}
Create exactly 10 multiple-choice questions based on this content:
{module_content}

Format:
Q1. [Clear question]
a) [Option]
b) [Option]
c) [Option]
d) [Option]

[Repeat for all 10 questions]

Answer Key:
1. [letter]
[Continue for all questions]"""


try:
    api_key = "ollama"
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key=api_key
    )
except OpenAIError as e:
    st.error(f"API Error: {str(e)}")


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "llama3.2:1b"
if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Feature", ["Course Generator", "Book Recommender"])
    st.session_state.page = page.lower().replace(" ", "_")
    
    if st.button("🗑️ Clear All"):
        st.session_state.clear()
        st.experimental_rerun()


def show_course_generator():
    st.title("📚 Smart Course Generator")
    
    col1, col_divider, col2 = st.columns([3.0, 0.1, 7.0])

    with col1:
        st.header("Course Details 📋")
        
      
        course_name = st.text_input("Course Name", key="course_name")
        target_audience_edu_level = st.selectbox(
            "Education Level",
            ["Primary", "High School", "Diploma", "Bachelors", "Masters"],
            key="edu_level"
        )
        difficulty_level = st.selectbox(
            "Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            key="difficulty"
        )
        num_modules = st.slider(
            "Number of Modules",
            min_value=1, max_value=10, value=4,
            key="num_modules"
        )
        course_duration = st.text_input("Course Duration (e.g., 12 weeks)", key="duration")
        course_credit = st.text_input("Course Credits (e.g., 3 credits)", key="credits")

       
        generate_button = st.button("🚀 Generate Course", use_container_width=True)

    with col2:
        st.header("Generated Content 📝")
        
        if generate_button and "pdf" not in st.session_state:
           
            if not all([course_name, target_audience_edu_level, difficulty_level, course_duration, course_credit]):
                st.warning("Please fill in all required fields")
            else:
                
                try:
                    with st.spinner("Generating course outline..."):
                        formatted_prompt = TABLER_PROMPT.format(
                            course_name=course_name,
                            edu_level=target_audience_edu_level,
                            difficulty=difficulty_level,
                            num_modules=num_modules,
                            duration=course_duration,
                            credits=course_credit
                        )
                        
                        response = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": "system", "content": "You are a helpful course creation assistant."},
                                {"role": "user", "content": formatted_prompt}
                            ],
                            temperature=0.3
                        )
                        
                        course_outline = response.choices[0].message.content
                        st.session_state['course_outline'] = course_outline
                        st.success("✅ Course outline generated!")
                        
                        with st.expander("View Course Outline", expanded=True):
                            st.write(course_outline)
                        
                        
                        
                        if st.button("📚 Generate Complete Course"):
                            try:
                                
                                dict_response = client.chat.completions.create(
                                    model=st.session_state["openai_model"],
                                    messages=[
                                        {"role": "system", "content": "Convert the outline to a dictionary format."},
                                        {"role": "user", "content": DICTATOR_PROMPT + "\n\n" + course_outline}
                                    ]
                                )
                                
                                module_lessons = json.loads(dict_response.choices[0].message.content)
                                
                               
                                complete_course_content = ""
                                for module_name, lessons in module_lessons.items():
                                    st.write(f"### {module_name}")
                                    module_content = ""
                                    
                                    
                                    for lesson_name in lessons:
                                        with st.spinner(f"Generating content for {lesson_name}..."):
                                            lesson_prompt = COURSIFY_PROMPT.format(
                                                lesson_name=lesson_name,
                                                module_name=module_name,
                                                course_name=course_name
                                            )
                                            
                                            lesson_response = client.chat.completions.create(
                                                model=st.session_state["openai_model"],
                                                messages=[
                                                    {"role": "system", "content": "Create focused lesson content."},
                                                    {"role": "user", "content": lesson_prompt}
                                                ]
                                            )
                                            
                                            lesson_content = lesson_response.choices[0].message.content
                                            module_content += f"\n\n{lesson_content}"
                                            
                                            with st.expander(f"📖 {lesson_name}"):
                                                st.write(lesson_content)
                                    
                                    
                                    with st.spinner(f"Generating quiz for {module_name}..."):
                                        quiz_prompt = QUIZZY_PROMPT.format(
                                            module_name=module_name,
                                            module_content=module_content
                                        )
                                        
                                        quiz_response = client.chat.completions.create(
                                            model=st.session_state["openai_model"],
                                            messages=[
                                                {"role": "system", "content": "Create module quiz questions."},
                                                {"role": "user", "content": quiz_prompt}
                                            ]
                                        )
                                        
                                        quiz_content = quiz_response.choices[0].message.content
                                        with st.expander(f"📝 Quiz - {module_name}"):
                                            st.write(quiz_content)
                                        
                                        complete_course_content += f"\n\n{module_content}\n\n{quiz_content}"
                                
                                
                                if "pdf" not in st.session_state:
                                    st.session_state.pdf = generate_pdf(complete_course_content, "course.pdf")
                                    pdf_data = base64.b64encode(st.session_state.pdf.output(dest="S").encode('latin1')).decode()
                                    
                                    st.success("🎉 Course generation complete!")
                                    st.download_button(
                                        label="⬇️ Download Course PDF",
                                        data=pdf_data,
                                        file_name="course.pdf",
                                        mime="application/pdf"
                                    )
                                    
                            except Exception as e:
                                st.error(f"Error generating course content: {str(e)}")
                                
                except Exception as e:
                    st.error(f"Error generating course outline: {str(e)}")
                    
        else:
            st.info("👈 Fill in the course details and click 'Generate Course' to start")


def initialize_recommender():
    try:
        df = pd.read_csv('./book1.csv')
        data = df.to_dict('records')
        return BookRecommender(data)
    except Exception as e:
        st.error(f"Error initializing book recommender: {str(e)}")
        return None


if 'recommender' not in st.session_state:
    st.session_state.recommender = initialize_recommender()

def show_book_recommender():
    st.title("📚 Course Book Recommender")
    

    course_name = st.session_state.get('course_name', '')
    edu_level = st.session_state.get('edu_level', '')
    
    with st.container():
        st.write("### Search for Related Books")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            
            search_query = st.text_input("Search Query", 
                value=course_name if course_name else "",
                placeholder="Enter keywords to search books...")
        
        with col2:
            min_rating = st.slider("Minimum Rating", 0.0, 5.0, 4.0, 0.1)
        
        col3, col4 = st.columns(2)
        
        with col3:
            min_year = st.number_input("From Year", 1900, 2024, 2000)
        
        with col4:
            max_year = st.number_input("To Year", 1900, 2024, 2024)
        
        if st.button("Search Books", use_container_width=True):
            if search_query:
                try:
                    if st.session_state.recommender:
                        # Get recommendations using BookRecommender
                        all_recommendations = st.session_state.recommender.get_recommendations(
                            search_query, 
                            num_recommendations=10
                        )
                        
          
                        filtered_results = []
                        for book in all_recommendations:
                            if (book['PublishYear'] >= min_year and 
                                book['PublishYear'] <= max_year and 
                                book['Rating'] >= min_rating):
                                
                                book['similarity_score'] = float(book['Similarity Score'])
                                filtered_results.append(book)
                        
                        if filtered_results:
                            st.success(f"Found {len(filtered_results)} relevant books!")
                            
                            for book in filtered_results:
                                with st.expander(f"📖 {book['Name']} ({book['PublishYear']})"):
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        st.markdown(f"**Authors:** {book['Authors']}")
                                        st.write(book['Description'])
                                    
                                    with col2:
                                        st.metric("Rating", f"{book['Rating']:.1f}/5.0")
                                        st.progress(book['similarity_score'])
                                        st.caption("Relevance Score")
                        else:
                            st.warning("No books found matching your criteria.")
                    else:
                        st.error("Book recommender not properly initialized.")
                        
                except Exception as e:
                    st.error(f"Error searching books: {str(e)}")
            else:
                st.warning("Please enter a search query.")


if st.session_state.page == "course_generator":
    show_course_generator()
elif st.session_state.page == "book_recommender":
    show_book_recommender()