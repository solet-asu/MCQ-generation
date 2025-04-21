# MCQ-generation
A workflow for automated MCQ generation using LLMs 

### Local Development Setup
The MCQ-generation workflow uses Python >=3.10.  

```shell
# 1. Clone the repository
git clone https://github.com/terryyutian/MCQ-generation.git

# 2. Move into the project
cd MCQ-generation

# 3. Install build environment tools
pip install --upgrade virtualenv

# 4. Create a virtual environment
python -m virtualenv .venv

# 5. Activate the virtual environment (Linux || Windows)
source .venv/bin/activate || source .venv/scripts/activate

# 6. Create an .env file.  Fill it in with the necessary values following this format: "OPENAI_API_KEY=XXXX"
touch .env

# 7. Install all the dependencies
pip install --editable .
```

# Run the demo app
1. put your directory to "./demo"
2. run this command in the terminal: `uvicorn app:app --reload`