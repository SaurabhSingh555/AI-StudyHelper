from flask import Flask, render_template, request, jsonify
import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)

# Set your OpenAI API Key and Base
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

llm = ChatOpenAI(
    temperature=0.7,
    model_name="gpt-3.5-turbo",
    openai_api_base=api_base,
    openai_api_key=api_key

)

# Prompt for explanation + questions
# Updated Prompt for explanation + questions
prompt_chatbot = PromptTemplate(
    input_variables=["exam", "topic", "difficulty"],
    template="""
You are an AI tutor for {exam} students.

Provide a detailed, comprehensive explanation of the topic "{topic}" at a {difficulty} level. Include every important aspect of the topic, including concepts, definitions, formulas, and key points that would help a student understand the topic thoroughly.

Then generate 7 MCQs for each difficulty level (Easy, Medium, Hard) related to the topic.

Format:

Explanation:
[Provide a detailed explanation with all important aspects and definitions]

Questions:
[Easy]
1. [Question Text]
a) Option 1
b) Option 2
c) Option 3
Answer: [Correct answer]

[Medium]
...

[Hard]
...
"""
)

chain_chatbot = LLMChain(prompt=prompt_chatbot, llm=llm)

# Prompt for self-assessment test
prompt_test = PromptTemplate(
    input_variables=["topic"],
    template="""
Generate 20 multiple-choice questions (MCQs) on the topic "{topic}" for self-assessment.
Each question should have 4 options and indicate the correct answer.
Return as a JSON list with keys: question, options (A-D), and correct.
"""
)
chain_test = LLMChain(prompt=prompt_test, llm=llm)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    topic = request.form.get("topic")
    exam = request.form.get("exam")
    difficulty = request.form.get("difficulty")

    if not topic or not exam or not difficulty:
        return jsonify({'response': 'Missing input.'})

    result = chain_chatbot.invoke({
        "exam": exam,
        "topic": topic,
        "difficulty": difficulty
    })

    return jsonify({'response': result['text']})

@app.route('/generate_test', methods=['POST'])
def generate_test():
    topic = request.form.get("topic")

    if not topic:
        return jsonify({'error': 'Missing topic'})

    result = chain_test.invoke({"topic": topic})

    import re, json
    # Extract JSON from response using regex
    try:
        json_str = re.search(r'\[.*\]', result['text'], re.DOTALL).group(0)
        questions = json.loads(json_str)
    except Exception as e:
        return jsonify({'error': 'Failed to parse questions', 'details': str(e)})

    return jsonify({"questions": questions})

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    data = request.get_json()
    questions = data.get("questions", [])
    user_answers = data.get("answers", {})

    score = 0
    feedback = []

    for idx, q in enumerate(questions):
        qid = str(idx)
        correct = q["correct"].strip().upper()
        user = user_answers.get(qid, "").strip().upper()
        is_correct = correct == user
        if is_correct:
            score += 1
        feedback.append({
            "question": q["question"],
            "your_answer": user,
            "correct_answer": correct,
            "is_correct": is_correct
        })

    return jsonify({
        "score": score,
        "total": len(questions),
        "feedback": feedback
    })

if __name__ == '__main__':
    app.run(debug=True)
