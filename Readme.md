## Demo Video 🎥

Watch the demo video of the AI Lead Qualification Automation system here:  
[Demo Video on Google Drive](https://drive.google.com/file/d/1Gt_YvaD6boPFL_2DzJVtImDuZoTMs2aU/view?usp=sharing)

# AI-Powered Lead Qualification Automation

Welcome to the AI-Powered Lead Qualification Automation repository! 
This project demonstrates a Python-based automation system that uses AI to analyze and qualify inbound leads from marketing campaigns or website forms. Designed as a portfolio project, it highlights automation, AI integration, and data management best practices for sales and business development teams.

---

## Project Architecture

The system is designed to automate the end-to-end lead qualification process:

- **Input Layer:** Leads are provided via a CSV file containing Name, Email, Company, Job Title, and Message.
- **AI Analysis Layer:** Each lead is processed by a Large Language Model (Groq API) to generate structured insights.
- **Output Layer:** Results are stored in Airtable and saved locally as CSV and JSON for easy access and reporting.

**Workflow:**

```text
New Lead (CSV) → AI Analysis → Lead Scoring → Priority Classification → Store Results (Airtable & Local Files)
