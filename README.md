<div align="center">
#Schedulify

![](https://i.ibb.co/Df3sf4b/logo-removebg-preview-removebg-preview-1.png)

Created by Corey Hudson, Damian Tucker,<br> Hunter Gulledge, Jax Pendergrass and Luke Bergren

<div align="left">
<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Schedulify is developed by a team of senior computer science students from the University of Alabama at Birmingham with solid experience in software development and web technologies, including past collaborations on academic and web-based projects.

  

### About Schedulify

Schedulify is a fully web-based calendar app designed to help users, particularly students and individuals with ADHD, manage their weekly tasks and boost productivity. Using our “Productivity Funnel” approach, users categorize tasks (e.g., “School,” “Work,” “Home”), assign them to specific days, and then organize them into an hourly schedule for optimal time management. This step-by-step process helps users achieve both personal and professional balance.

## Requirements
Latest version of Python

## Installation
To run the application, clone the repository into your chosen directory using:<br>
<br>`git clone https://github.com/HunterGulledge4/calendar-web-app.git`<br>
<br>then access the directory with:<br><br>
`cd calendar-web-app`<br><br>

#### For Windows
*Make sure that running scripts is enabled.*<br><br>
In powershell, run: <br><br>
`./run_flask.bat`
<br><br>or<br><br>
`run_flask.bat`<br><br>
in the command prompt.<br><br>

#### For MAC/Linux
Run <br><br>`./run_flask.sh` <br><br>or<br><br> `run_flask.sh`<br><br> in the terminal.<br><br>

The program will then open in your default browser.<br><br>

## Features

### 1. Task-Funneling System  
Schedulify’s core feature is its **task-funneling system**, designed to help users organize their week efficiently:  
1. **List tasks abstractly:** Start by listing the categories for the tasks for the week.  
2. **Assign tasks to days:** Distribute tasks across the days of the week in which you wish to complete them.  
3. **Schedule tasks:** Allocate specific times for each task within the day.  

This step-by-step process provides a structured approach to planning and ensures tasks are manageable and prioritized.  

---

### 2. Week-to-Week Navigation
Navigate through weeks easily using intuitive arrow buttons located at the top of the page. Clicking the left arrow will take you to the previous week and the right arrow to the next week. The application makes backend calls that updates and refreshes the page to the data given for the previous or next week instead of taking the user to a new page.  

This feature focuses on delivering a functional and seamless calendar experience to the user. 

---

### 3. Light/Dark Mode   
A quality-of-life enhancement for user comfort:  
**Toggle switch:** Located at the top-right and will easily switch between light and dark modes.    
The dark mode helps to increase the comfort of the user by reducing the eye strain caused by viewing white light over an extened period of time. 
