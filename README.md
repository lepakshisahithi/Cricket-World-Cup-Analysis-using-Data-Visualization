# Historical Performance Analysis of the Indian Cricket Team in ICC World Cups Using Python
## 👥 Project Team

This is a group project developed as part of our Data Visualization coursework.

| S.No. | Team Member Name | Roll Number |
| 1 | L.Sahithi | 24FH1A3110 |
| 2 | B.Deepika | 24FH1A3103 |
| 3 | P.Rajitha | 24FH1A3112  |


##  Project Guide

Guide Name: Dr.B.Mahesh

## Department

Computer Science and Engineering (Artificial Intelligence)

## Project overview
This Data Visualization project explores World Cup match records and India's performance using Python, Pandas, and Matplotlib.

## Visualizations
1. Number of matches by year
2. India's match outcomes (wins, losses, and other/no-result records)
3. India's wins by year
4. Top 10 teams by average runs per match
5. India's average runs per match by year
6. Pie chart of India's match outcomes
7. Scatter plot comparing Team 1 and Team 2 scores
8. Histogram of team-score distribution
9. Box plot comparing team-score distributions

The program also saves summary tables as CSV files.

## Dataset
The project uses `world_cup_score.csv`, supplied with the project. The source data contains over-by-over rows, so the script reduces it to one record per match before creating match-level charts.

## Requirements
- Python 3.9 or newer
- pandas
- matplotlib

Install dependencies:
```bash
pip install -r requirements.txt
```

## How to run
1. Download or clone this repository.
2. Make sure `world_cup_score.csv` and `cricket_analysis.py` are in the same folder.
3. Install the dependencies.
4. Run:
```bash
python cricket_analysis.py
```

The charts and summary CSV files are saved in the `output_graphs` folder.

## Important data note
The dataset contains multiple World Cup years and may include different tournament formats. Check the tournament metadata and source documentation before making claims that all years represent the same format. This is an exploratory analysis and should be interpreted in light of the dataset's coverage and quality.
