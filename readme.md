Sci-Facts Technical Overview

Tech Stack:

Backend Framework: The Sci-Facts app is built on the Flask web framework, a Python microframework for web development.
Frontend: The user interface is crafted using HTML and styled with CSS to ensure an engaging and responsive design.
Database: Postgres, a powerful open-source relational database, is employed to store and manage data, including quotes, facts, titles, and user information.
Server-side Logic: Python is used extensively for server-side scripting and business logic, integrating seamlessly with Flask.
Client-side Logic: JavaScript can be utilized for client-side interactions, such as dynamic content updates or form validation.
Key Features:

User Authentication: Users are required to authenticate to access certain features. Flask's built-in session management or token-based authentication can be implemented for this purpose.
Database Schema:
Tables: The database schema includes tables for users, titles (categorized as Books, TV, Movies, and Games), quotes, facts, and submission reviews.
Relations: Tables are connected through foreign key relationships, enabling efficient data retrieval and management.
User Roles:
User: Standard users can add quotes and facts to existing titles.
Admin: Admins have the authority to review and approve/deny submissions. Their access is restricted to the admin panel.
Content Submission:
Users can submit new titles, and these submissions are stored in a review queue for admin evaluation.
Adding quotes and facts involves interacting with forms and submitting data to the server for processing.
Admin Panel:
The admin panel provides tools to view, approve, or deny submissions.
Admins can also edit titles, quotes, and facts, ensuring data accuracy and quality.
