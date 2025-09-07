# Event Reporting System
This is a simple and efficient platform that helps colleges manage events, student registrations, and generate reports. It’s designed to support multiple colleges and makes it easy to track attendance, collect feedback, and view analytics.

## What Can Done?
You can create, update, and manage events with ease. Students can register for events, and the system handles capacity limits automatically. It also allows you to mark attendance and collect feedback after events. With detailed reports, you can track participation, attendance rates, and see which students are the most active. The interface is clean and responsive.

## Tech Stack used:
On the backend, it uses FastAPI along with SQLAlchemy and SQLite for storing data. The frontend is built using HTML, CSS, Bootstrap 5, and JavaScript to keep it lightweight and fast. The database is structured to handle relationships between colleges, students, events, and feedback smoothly.

##  How to Get Started
clone the project to your machine. install the dependencies by running `pip install -r requirements.txt`. After that, you can start the application using `python main.py`. Once it’s running, you can access the web interface by going to `http://localhost:8000`.

## Sample Data Included
The system comes with sample data to help you test it easily. There are five colleges like MIT and Stanford, 18 students spread across those colleges, and 8 sample events like AI workshops and competitions. The data is realistic, with attendance and feedback rates.

## Reporting and Analytics
You’ll be able to see reports that show registration numbers, attendance rates, and feedback. It also highlights the top students and compares events across different colleges. The system handles cancellations and waitlists in a smooth and intuitive way.


## Handles Real-World Challenges
The system prevents duplicate registrations and ensures data is valid—for example, checking email uniqueness and ensuring event dates are correct. It handles errors gracefully, so users get clear messages when something goes wrong.


