# MAI Scheduler

An interactive class schedule generator for the [Master in Artificial Intelligence (MAI)](https://www.fib.upc.edu/en/studies/masters/master-artificial-intelligence) program (UPC, UB, URV), designed to help you create the optimal timetable for Q2 2025 based on preferences, constraints, and personal scheduling preferences.

## Live Demo

Try out the **MAI Scheduler** online:

[**MAI Scheduler Live App**](https://mai-scheduler.streamlit.app)

*(Hosted on Streamlit Community Cloud.)*

---

## Features

- **Multi-Page Layout**  
  - **Home Page**: Filter courses, generate schedules, and visually explore different combinations.  
  - **Saved Schedules Page**: Log in to see and manage previously saved schedules.

- **Optional Login & Registration**  
  - **Auto-Login on Registration**: Once you register, you’re instantly logged in—no extra steps needed.  
  - **Logout**: End your session at any time.

- **University Selection**  
  Choose courses from multiple universities (UPC, UB, URV) that participate in the MAI program.

- **Customizable Filters**  
  - **Mandatory Courses**: Force specific courses to appear in your generated schedule.
  - **Excluded Courses**: Keep out courses you don’t want to attend.
  - **ECTS Range**: Specify minimum and maximum total ECTS credits.
  - **Max Class Days**: Limit the number of days you have classes each week.

- **Mental Health Options**  
  - **No Time Conflicts**: Avoid overlapping classes automatically.
  - **University Day Rule**: Prevent classes from different universities on the same day.
  - **Maximum 6 Consecutive Hours**: Cap the maximum consecutive class hours per day.

- **Penalty System**  
  Prioritize schedule preferences by assigning penalties to:
  - Number of class days
  - Total gap time between classes
  - Maximum consecutive hours
  - Earliest start time
  - Latest end time

- **Visual Schedule Representation**  
  Generate and view your schedule in a clear, graphical timetable.

- **Interactive Navigation**  
  Browse valid schedules with **Previous**/**Next** buttons, or **Save** a schedule (if logged in).

- **Saved Schedules**  
  - **Persist Schedules**: When logged in, save schedules to revisit later.
  - **View & Re-Plot**: The dedicated “Saved Schedules” page re-displays your timetable and details.

- **Clickable Syllabus Links**  
  Each course listing includes a direct link to its [syllabus](https://www.fib.upc.edu/en/studies/masters/master-artificial-intelligence/curriculum/syllabus/MBM-CODE).

---

## Security

- **Password Storage**:  
  All user passwords are **hashed** using a secure algorithm (bcrypt via Passlib) and stored in a cloud-based PostgreSQL database. This means plain-text passwords are never saved.
  
- **Data Handling**:  
  - **User Data**: When you register or log in, only your username and hashed password are stored.  
  - **Schedules**: Any schedules you save are stored in the database attached to your user ID, but do not contain sensitive information beyond course codes and schedule details.
  
- **Deployment**:  
  - The live app uses **Streamlit Community Cloud**.  
  - The database is hosted remotely (e.g., **Neon** or another cloud PostgreSQL provider).  
  - Always ensure you use SSL/HTTPS when sharing your login credentials.

---

## Running the App Locally

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/oriolmirolf/MAI_Scheduler
   cd MAI_Scheduler
   ```

2. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```  
   Make sure Python 3.7+ is installed.

3. **Prepare the Data**  
   - Use the existing `data.json` or create your own with the required structure:
     ```json
     {
       "CourseCode1": {
         "University": "UniversityName",
         "ECTS": 5,
         "Schedule": {
           "Lecture": ["Monday 9-11", "Wednesday 9-11"],
           "Lab": ["Friday 14-16"]
         }
       }
       ...
     }
     ```

4. **Run the App**  
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Access the App**  
   Open your browser at:
   ```
   http://localhost:8501
   ```

---

## To-Do List

- **Automate Data Extraction**  
  Implement web scraping for real-time retrieval of university timetables.
  
- **Enhance Schedule Customization**  
  Integrate additional advanced constraints, e.g., building locations or travel times.

---

## Contributing

Contributions are welcome!

1. **Fork** the repo on GitHub.  
2. **Create a Branch** for your feature or bug fix.  
3. **Commit** your changes with clear, concise messages.  
4. **Open a Pull Request** and await feedback.

---

## License

This project is licensed under the [MIT License](https://mit-license.org).

---

## Contact

For questions or suggestions, you can reach:

- **Email**: mirolopezfeliuoriol@gmail.com  
- **GitHub Issues**: [MAI_Scheduler Issues](https://github.com/oriolmirolf/MAI_Scheduler/issues)
