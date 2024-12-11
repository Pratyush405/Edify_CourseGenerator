# prompts/course_generator.py
from typing import Dict, List, Optional

class CourseGenerator:
    def __init__(self):
        self.course_context = {}
        
    def generate_tabler_prompt(self, topic: str, num_modules: int) -> str:
        return f"""You are Tabler, creating a course outline for: {topic}.
        
Requirements:
1. Create exactly {num_modules} modules
2. Each module must have 3-5 lessons
3. Follow this exact format:

Course Title: [title]
Duration: [duration]
Modules: {num_modules}

Overview:
[2-3 sentences maximum]

Learning Outcomes:
[5-7 bullet points]

Curriculum:
Module 1: [Module Title]
- Lesson 1.1: [Lesson Title]
- Lesson 1.2: [Lesson Title]
[continue for all modules]
"""

    def generate_dictator_prompt(self, course_outline: str) -> str:
        return f"""Convert this course outline to a Python dictionary:

{course_outline}

Rules:
1. Keys must be full module titles (e.g., "Module 1: Introduction")
2. Values must be lists of lesson titles
3. Maintain the exact naming and numbering
4. Return only the Python dictionary, no explanation
"""

    def generate_coursify_prompt(self, lesson_name: str, module_name: str, course_name: str, previous_context: Optional[Dict] = None) -> str:
        context = f"Previous lessons covered: {previous_context}\n" if previous_context else ""
        
        return f"""Generate educational content for:
Course: {course_name}
Module: {module_name}
Lesson: {lesson_name}

{context}

Requirements:
1. Start with clear prerequisites and objectives
2. Cover only the specific lesson topic
3. Include practical examples
4. End with a summary of key points
5. Maximum length: 1500 words
"""

    def generate_quizzy_prompt(self, module_content: str, module_name: str) -> str:
        return f"""Create a quiz for module: {module_name}

Content to reference:
{module_content}

Requirements:
1. Exactly 30 multiple-choice questions
2. Each question must directly relate to the module content
3. No theoretical questions not covered in the content
4. Include exactly 4 options per question
5. Provide answer key at the end
6. Format: Q1, Q2, etc. with options a, b, c, d

Quiz Questions:
[Your questions here]

Answer Key:
[Answers here]
"""

    def process_course_generation(self, topic: str, num_modules: int = 4) -> Dict:
        outline_prompt = self.generate_tabler_prompt(topic, num_modules)
        course_outline = "AI_RESPONSE_HERE"
        
        dict_prompt = self.generate_dictator_prompt(course_outline)
        course_structure = "AI_RESPONSE_HERE"
        
        self.course_context = {
            'topic': topic,
            'outline': course_outline,
            'structure': course_structure,
            'generated_content': {}
        }
        
        return self.course_context

    def generate_lesson_content(self, lesson_name: str, module_name: str, course_name: str) -> str:
        previous_content = self.course_context.get('generated_content', {})
        prompt = self.generate_coursify_prompt(lesson_name, module_name, course_name, previous_content)
        content = "AI_RESPONSE_HERE"
        
        if module_name not in self.course_context['generated_content']:
            self.course_context['generated_content'][module_name] = {}
        self.course_context['generated_content'][module_name][lesson_name] = content
        
        return content