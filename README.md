# MAI Scheduler

An interactive class schedule generator for the Master in Artificial Intelligence (MAI) program, designed to help you create the optimal timetable for Q2 2025 based on preferences and constraints.

## Features

- **University Selection**: Choose courses from multiple universities participating in the MAI program.
- **Customizable Filters**:
  - **Mandatory Courses**: Ensure certain courses are included in your schedule.
  - **Excluded Courses**: Exclude courses you don't want to attend.
  - **ECTS Range**: Specify the minimum and maximum total ECTS credits.
  - **Maximum Class Days**: Limit the number of days you have classes each week.
- **Mental Health Options**:
  - **No Time Conflicts**: Automatically avoid overlapping classes.
  - **University Day Rule**: Option to prevent scheduling classes from different universities on the same day.
  - **Maximum Consecutive Hours**: Limit the number of consecutive class hours per day.
- **Penalty System**: Prioritize schedule preferences by assigning penalties to factors like:
  - Number of class days.
  - Total gap time between classes.
  - Maximum consecutive hours.
  - Earliest start time.
  - Latest end time.
- **Visual Schedule Representation**: Generate and view your schedule in a clear, graphical format.
- **Interactive Navigation**: Browse through all valid schedules that meet your criteria.

## Live Demo

Try out the MAI Scheduler online:

[MAI Scheduler Live App](https://mai-scheduler.streamlit.app)

*Hosted on Streamlit Community Cloud.*

## Running the App Locally

Follow these steps to run the MAI Scheduler on your local machine:

### 1. Clone the Repository

```bash
git clone https://github.com/oriolmirolf/MAI_Scheduler
cd MAI_Scheduler
```
### 2. Install Dependencies

Ensure you have Python 3.7 or higher installed. Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Prepare the Data

The app requires a data.json file containing the course schedules. Since the data is currently extracted manually and specific to Q2 2025, you have two options:
- Use Existing Data: If the data.json file is included in the repository, ensure it's placed in the same directory as the app script.
- Create Your Own Data: If you want to customize or update the data, create a data.json file with the following structure:
  ```json
  {
    "CourseCode1": {
      "University": "UniversityName",
      "ECTS": 5,
      "Schedule": {
        "Lecture": ["Monday 9-11", "Wednesday 9-11"],
        "Lab": ["Friday 14-16"]
      }
    },
    "CourseCode2": {
      "University": "AnotherUniversity",
      "ECTS": 5,
      "Schedule": {
        "Lecture": ["Tuesday 10-12"],
        "Seminar": ["Thursday 13-15"]
      }
    }
    // Add more courses as needed
  }
  ```

### 4. Run the App
Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

### 5. Access the App
Open your web browser and navigate to:
```
http://localhost:8501
```

## To-Do List
- **Automate Data Extraction:** Implement web scraping tools to automatically retrieve course schedules and details from university websites.
Ensure that the scraper adapts to different university websites and timetable formats.



## Contributing
Contributions are welcome! If you'd like to help improve the MAI Scheduler:

1. Fork the Repository: Create a personal copy of the repository on your GitHub account.
2. Create a Branch: Make a new branch for your feature or bug fix.
3. Commit Your Changes: Write clear and concise commit messages.
4. Submit a Pull Request: Explain your changes and await feedback.

Please ensure all new code follows the existing style and conventions.

## License
This project is licensed under the [MIT License](https://mit-license.org).

## Contact
For questions or suggestions, feel free to contact:

Email: mirolopezfeliuoriol@gmail.com
GitHub Issues: Issue Tracker
