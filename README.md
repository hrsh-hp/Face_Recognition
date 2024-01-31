# Face Recognition Project for Design Engineering

## Project overview:

The Facial Recognition System with Django is a versatile application designed for real-time identification and personalized interactions. Using Python, the system employs facial recognition technology to greet individuals, enhance security, and elevate event experiences. This project showcases its adaptability in entrances, security setups, and event management, offering personalized greetings, access control, and attendee engagement tracking.

## Features:

- **Real-time Facial Recognition:** Utilizes Python to identify individuals in real-time, providing a seamless and efficient identification process.

- **Personalized Greetings:** Greets individuals by name at entrances, offering a personalized and welcoming experience.

- **Security Integration:** Enhances security by identifying authorized personnel and preventing unauthorized access.

- **Event Engagement Tracking:** Tracks attendee engagement at events, providing tailored interactions and streamlining attendance management.

- **Continuous Frame Capture:** Captures frames at regular intervals and sends them to the backend.

## Technologies:

- **Webcam Access:** Utilizes the `getUserMedia` API to access the user's webcam.
- **Face Recognition:** Recognizes faces in the captured frames using face recognition libraries.
- **Django Backend:** Django (Python web framework) for server-side development.Which Handles image data from the frontend, performs face recognition, and provides responses.


## Setting Up the Project on Windows

### Prerequisites
- Ensure that Python is installed on your system. If not, download and install Python from [python.org](https://www.python.org/).

### Setting Up Virtual Environment

1. Install virtualenv:
    ```bash
    pip install virtualenv
    ```

2. Create a new virtual environment:
    ```bash
    python -m venv venv
    ```

3. Activate the virtual environment:
    ```bash
    .\venv\Scripts\activate
    ```

### Initializing Dependencies and Running the Server

4. Install Django in the virtual environment:
    ```bash
    pip install Django
    ```

5. Fork the main repository and Clone your forked repository:
    ```bash
    git clone https://github.com/<your username>/Face_Recognition.git
    ```

6. Navigate to the project directory:
    ```bash
    cd Face_Recognition
    ```

8. Install project dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    
9.  Make changes in database using makemigrations:
    ```bash
    python manage.py makemigrations
    ```

10. Update the actual database:
    ```bash
    python manage.py migrate
    ```

11. Create Superuser to access admin panel
    ```bash
    python manage.py createsuperuser
    ```

12. Try running the server:
    ```bash
    python manage.py runserver
    ```


#### There's a need for initializing SECRET_KEY and .env.

1. Generate SECRET_KEY in python shell:
    ```bash
    from django.core.management.utils import get_random_secret_key
    print('SECRET_KEY=',get_random_secret_key())
    ```

2. Add SECRET_KEY in .env :
    
    ```bash
    SECRET_KEY= <YOUR GENERATED SECRET_KEY>
    EMAIL_HOST_USER = "<Your email Id>"
    EMAIL_HOST_PASSWORD = "<You email app password>" 
    ```
