# Call Center Communication Analyzer Backend

## Setup Development Environment

1. Clone Repository<br/>
   `git clone git@github.com:erandasathsara/ICSMS-Call-Analyzer-Backend.git`
   <br/>
   <br/>
2. Checkout to dev branch<br/>
   `git checkout dev`
   <br/>
   <br/>
3. Create A Branch For You (If you don't have a branch)<br/>
   `git checkout -b YOUR_BRANCH_NAME`
   <br/>
   <br/>
4. Create A Virtual Environment<br/>
   `python -m venv venv`
   <br/>
   <br/>
5. Activate Environment<br/>
   `venv\Script\activate`
   <br/>
   <br/>
6. Install Dependencies.<br/>
   `pip intall -r requirements.txt`
   <br/>
   <br/>
7. Install FFMPEG<br/>
   `winget install "FFmpeg (Essentials Build)"`
   <br/>
   <br/>
8. Run Server<br/>
   `python main.py`
   <br/>
   <br/>
9. Run Docker Container (Optional)<br/>
   `docker build . -t call-analyzer-api `
   `docker run -p 8000:8000 --env-file .env call-analyzer-api`

<!-- https://stackoverflow.com/questions/68505216/modulenotfounderror-no-module-named-app-routes -->
<!-- uvicorn app.main:app --reload -->
